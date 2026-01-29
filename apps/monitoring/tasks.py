"""
Celery tasks for monitoring devices.
"""
import logging
import time
from datetime import timedelta
from typing import Optional
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from django.db.models import Q

from apps.inventory.models import Device
from apps.monitoring.models import CheckResult
from apps.monitoring.engine import run_ping

logger = logging.getLogger(__name__)


@shared_task(bind=True, ignore_result=True)
def run_all_monitoring_checks(self):
    """
    Run monitoring checks for all enabled devices.
    This task is called periodically by Celery Beat.
    """
    enabled_devices = Device.objects.filter(enabled=True)
    logger.info(f"Starting monitoring checks for {enabled_devices.count()} enabled devices")
    
    for device in enabled_devices:
        try:
            # Check if enough time has passed since last check
            if device.last_check_at:
                time_since_last_check = (timezone.now() - device.last_check_at).total_seconds()
                if time_since_last_check < device.check_interval_seconds:
                    logger.debug(f"Skipping {device.name}: checked {time_since_last_check:.1f}s ago")
                    continue
            
            # Run the check for this device
            check_device.delay(device.id)
            
        except Exception as e:
            logger.error(f"Error scheduling check for {device.name}: {e}", exc_info=True)
    
    logger.info("Finished scheduling monitoring checks")


@shared_task(bind=True, max_retries=3)
def check_device(self, device_id: int):
    """
    Perform a complete monitoring check for a single device.
    
    Args:
        device_id: ID of the device to check
    """
    try:
        device = Device.objects.get(id=device_id)
    except Device.DoesNotExist:
        logger.error(f"Device {device_id} not found")
        return
    
    if not device.enabled:
        logger.debug(f"Device {device.name} is disabled, skipping check")
        return
    
    logger.info(f"Checking device: {device.name} ({device.ip_address})")
    
    start_time = time.time()
    errors = []
    freshness_minutes = getattr(settings, 'AGENT_FRESH_MINUTES', 10)
    freshness_cutoff = timezone.now() - timedelta(minutes=freshness_minutes)
    latest_agent = device.agent_reports.first()
    agent_healthy = latest_agent.agent_healthy if latest_agent else None
    agent_fresh = bool(latest_agent and latest_agent.reported_at >= freshness_cutoff)
    
    # Initialize check result
    check_result = CheckResult(device=device)
    
    # Ping check
    if device.ping_enabled:
        ping_ok, ping_ms, ping_error = run_ping(
            device.ip_address,
            timeout_ms=device.timeout_ms
        )
        check_result.ping_ok = ping_ok
        check_result.ping_ms = ping_ms
        if ping_error:
            errors.append(f"Ping: {ping_error}")
    else:
        check_result.ping_ok = False
        check_result.ping_ms = None
    
    # Determine overall status (UP if ping OK, DOWN if ping failed)
    check_result.overall_status = check_result.determine_overall_status()
    check_result.error_message = '\n'.join(errors) if errors else ''
    
    # Calculate total check duration
    check_result.check_duration_ms = int((time.time() - start_time) * 1000)
    
    # Save check result
    check_result.save()
    
    # Check for alerts and send to ChatWarning
    _check_and_send_alerts(device, latest_agent)
    
    # Update device status if thresholds are met
    old_status = device.last_status
    
    # Update device
    device.last_check_at = timezone.now()
    
    # Compute overall status considering ping and agent health
    new_status = device.compute_overall_status()
    
    if new_status != old_status:
        device.last_status = new_status
        device.last_status_change = timezone.now()
        device.save(update_fields=['last_status', 'last_status_change', 'last_check_at'])
        
        # Record status change in history
        from apps.monitoring.models import StatusChangeHistory
        if check_result.ping_ok is False:
            if agent_fresh:
                reason = "Ping failed but agent reporting; treating as reachable"
            else:
                reason = "Ping failed"
        elif check_result.ping_ok is True:
            if agent_healthy is False:
                reason = "Agent reported unhealthy services/processes"
            elif agent_healthy is True:
                reason = "Ping OK and agent healthy"
            else:
                reason = "Ping OK"
        else:
            reason = "Using latest agent report" if agent_fresh else "No recent data"
        StatusChangeHistory.objects.create(
            device=device,
            old_status=old_status,
            new_status=new_status,
            reason=reason
        )
        
        logger.info(f"Device {device.name} status changed: {old_status} → {new_status}")

        # Send status change alert to ChatWarning
        _send_status_change_alert(device, old_status, new_status, reason)
    else:
        device.save(update_fields=['last_check_at'])
    
    # Check for metric-based alerts and send to ChatWarning
    _check_and_send_alerts(device, latest_agent)

    logger.info(
        f"Check complete for {device.name}: {new_status} "
        f"(ping: {check_result.ping_ok}, {check_result.ping_ms}ms)"
    )


@shared_task(bind=True, ignore_result=True)
def cleanup_old_check_results(self, keep_count: int = 500):
    """
    Clean up old check results, keeping only the most recent N per device.
    
    Args:
        keep_count: Number of recent results to keep per device
    """
    logger.info(f"Starting cleanup of old check results (keeping {keep_count} per device)")
    
    devices = Device.objects.all()
    total_deleted = 0
    
    for device in devices:
        # Get IDs of results to keep
        keep_ids = list(
            CheckResult.objects.filter(device=device)
            .order_by('-created_at')
            .values_list('id', flat=True)[:keep_count]
        )
        
        # Delete older results
        deleted_count, _ = CheckResult.objects.filter(
            device=device
        ).exclude(id__in=keep_ids).delete()
        
        if deleted_count > 0:
            total_deleted += deleted_count
            logger.debug(f"Deleted {deleted_count} old results for {device.name}")
    
    logger.info(f"Cleanup complete: deleted {total_deleted} old check results")


@shared_task(ignore_result=True)
def cleanup_old_data():
    """
    Remove old check results and agent reports (data retention policy).
    Keeps last 7 days of data, or last 1000 results per device.
    Run this task daily via Celery Beat.
    """
    from datetime import timedelta
    from apps.monitoring.models import AgentReport
    
    cutoff_date = timezone.now() - timedelta(days=7)
    
    # Delete old CheckResults
    check_results_deleted, _ = CheckResult.objects.filter(
        created_at__lt=cutoff_date
    ).delete()
    
    # Delete old AgentReports
    agent_reports_deleted, _ = AgentReport.objects.filter(
        reported_at__lt=cutoff_date
    ).delete()
    
    if check_results_deleted > 0 or agent_reports_deleted > 0:
        logger.info(
            f"Data retention: deleted {check_results_deleted} check results "
            f"and {agent_reports_deleted} agent reports older than {cutoff_date}"
        )

def _check_and_send_alerts(device: Device, agent_report=None):
    """
    Check device metrics against thresholds and send alerts to ChatWarning if needed.
    
    Alerts for:
    - Process down (monitored services/processes not running)
    - CPU usage too high
    - Memory usage too high
    - Disk usage too high
    - Device uptime exceeds threshold (recommends reboot)
    
    Args:
        device: Device object to check
        agent_report: Latest AgentReport for the device (optional)
    """
    # Skip if no agent report or alert integration not configured
    if not agent_report:
        return
    
    # Try to import integration, silently fail if requests not available
    try:
        from postracker_integration import (
            send_process_alert,
            send_cpu_alert,
            send_memory_alert,
            send_storage_alert,
            send_uptime_alert
        )
    except ImportError:
        logger.warning("postracker_integration not available. Install requests package.")
        return
    
    alert_cpu_threshold = getattr(settings, 'ALERT_CPU_THRESHOLD', 85)
    alert_memory_threshold = getattr(settings, 'ALERT_MEMORY_THRESHOLD', 85)
    alert_disk_threshold = getattr(settings, 'ALERT_DISK_THRESHOLD', 90)
    alert_uptime_threshold_days = getattr(settings, 'ALERT_UPTIME_THRESHOLD_DAYS', 30)
    alert_uptime_threshold_hours = alert_uptime_threshold_days * 24
    
    try:
        # Check for process/service alerts
        if not agent_report.agent_healthy:
            # Device has unhealthy services/processes
            for service_name, service_info in agent_report.services_status.items():
                if service_info.get('found', True) and not service_info.get('running', False):
                    logger.warning(f"Sending process alert for {device.name}: {service_name} down")
                    send_process_alert(
                        device_name=device.name,
                        process_name=service_name,
                        channel_name='alerts'
                    )
            
            for process_name, process_info in agent_report.processes_status.items():
                if not process_info.get('running', False):
                    logger.warning(f"Sending process alert for {device.name}: {process_name} down")
                    send_process_alert(
                        device_name=device.name,
                        process_name=process_name,
                        channel_name='alerts'
                    )
        
        # Check CPU usage
        if agent_report.cpu_percent and agent_report.cpu_percent > alert_cpu_threshold:
            logger.warning(f"Sending CPU alert for {device.name}: {agent_report.cpu_percent}%")
            send_cpu_alert(
                device_name=device.name,
                cpu_percent=agent_report.cpu_percent,
                threshold=alert_cpu_threshold,
                channel_name='alerts'
            )
        
        # Check memory usage
        if agent_report.memory_percent and agent_report.memory_percent > alert_memory_threshold:
            logger.warning(f"Sending memory alert for {device.name}: {agent_report.memory_percent}%")
            send_memory_alert(
                device_name=device.name,
                memory_percent=agent_report.memory_percent,
                threshold=alert_memory_threshold,
                channel_name='alerts'
            )
        
        # Check disk usage
        if agent_report.disk_percent and agent_report.disk_percent > alert_disk_threshold:
            logger.warning(f"Sending disk alert for {device.name}: {agent_report.disk_percent}%")
            send_storage_alert(
                device_name=device.name,
                disk_percent=agent_report.disk_percent,
                threshold=alert_disk_threshold,
                channel_name='alerts'
            )
        
        # Check uptime (recommend reboot after N days)
        if agent_report.uptime_hours and agent_report.uptime_hours > alert_uptime_threshold_hours:
            logger.info(f"Sending uptime alert for {device.name}: {agent_report.uptime_hours / 24:.1f} days")
            send_uptime_alert(
                device_name=device.name,
                uptime_hours=agent_report.uptime_hours,
                threshold_days=alert_uptime_threshold_days,
                channel_name='alerts'
            )
    
    except Exception as e:
        logger.error(f"Error checking/sending alerts for {device.name}: {e}", exc_info=True)


def _send_status_change_alert(device: Device, old_status: str, new_status: str, reason: str) -> None:
    """
    Send a status change alert to ChatWarning if integration is configured.
    """
    try:
        from postracker_integration import send_status_change_alert
    except ImportError:
        logger.warning("postracker_integration not available. Install requests package.")
        return

    try:
        send_status_change_alert(
            device_name=device.name,
            old_status=old_status,
            new_status=new_status,
            reason=reason,
            channel_name='alerts'
        )
    except Exception as exc:
        logger.error(
            f"Error sending status change alert for {device.name}: {exc}",
            exc_info=True
        )