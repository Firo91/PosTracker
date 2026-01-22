"""
Alert system for sending email notifications on device status changes.
"""
import logging
from typing import Optional
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta

from apps.inventory.models import Device
from apps.monitoring.models import CheckResult, AlertLog

logger = logging.getLogger(__name__)

# Minimum time between alerts for the same device (seconds)
ALERT_THROTTLE_SECONDS = 600  # 10 minutes


def should_send_alert(device: Device, new_status: str) -> bool:
    """
    Determine if an alert should be sent based on throttling rules.
    
    Args:
        device: The device to check
        new_status: The new status
        
    Returns:
        True if alert should be sent, False otherwise
    """
    # Check if alerts are configured
    if not settings.ALERT_EMAIL_RECIPIENTS or not settings.ALERT_EMAIL_RECIPIENTS[0]:
        logger.debug("Alert email recipients not configured, skipping alert")
        return False
    
    # Check last alert time for this device
    last_alert = AlertLog.objects.filter(device=device).order_by('-sent_at').first()
    
    if last_alert:
        time_since_last_alert = (timezone.now() - last_alert.sent_at).total_seconds()
        if time_since_last_alert < ALERT_THROTTLE_SECONDS:
            logger.debug(
                f"Alert throttled for {device.name}: last alert {time_since_last_alert:.0f}s ago"
            )
            return False
    
    return True


def send_status_change_alert(
    device: Device,
    old_status: str,
    new_status: str,
    check_result: Optional[CheckResult] = None
) -> bool:
    """
    Send an email alert about a device status change.
    
    Args:
        device: The device that changed status
        old_status: Previous status
        new_status: New status
        check_result: Optional check result with details
        
    Returns:
        True if alert was sent successfully, False otherwise
    """
    # Check if we should send the alert
    if not should_send_alert(device, new_status):
        return False
    
    # Determine alert type
    if new_status == 'DOWN':
        alert_type = 'DOWN_ALERT'
        subject_prefix = '🔴 DOWN'
    elif new_status == 'UP' and old_status in ['DOWN', 'DEGRADED']:
        alert_type = 'UP_ALERT'
        subject_prefix = '🟢 UP'
    elif new_status == 'DEGRADED':
        alert_type = 'DEGRADED_ALERT'
        subject_prefix = '🟡 DEGRADED'
    else:
        alert_type = 'STATUS_CHANGE'
        subject_prefix = 'Status Change'
    
    # Build email subject
    subject = f"[NetWatch] {subject_prefix}: {device.name}"
    
    # Build email message
    message_lines = [
        f"Device Status Change Alert",
        f"=" * 50,
        f"",
        f"Device Name: {device.name}",
        f"IP Address: {device.ip_address}",
        f"Device Type: {device.get_device_type_display()}",
        f"Location: {device.location or 'Not specified'}",
        f"",
        f"Status Change: {old_status} → {new_status}",
        f"",
    ]
    
    # Add check details if available
    if check_result:
        message_lines.extend([
            f"Check Details:",
            f"  Ping: {'✓ OK' if check_result.ping_ok else '✗ Failed'}" + 
                (f" ({check_result.ping_ms}ms)" if check_result.ping_ms else ""),
            f"  RDP: {'✓ OK' if check_result.rdp_ok else '✗ Failed'}" + 
                (f" ({check_result.rdp_ms}ms)" if check_result.rdp_ms else ""),
        ])
        
        if device.needs_simphony_check():
            simphony_status = '✓ Running' if check_result.simphony_ok else f'✗ {check_result.simphony_status}'
            message_lines.append(f"  Simphony: {simphony_status}")
        
        if check_result.error_message:
            message_lines.extend([
                f"",
                f"Errors:",
                f"{check_result.error_message}",
            ])
    
    message_lines.extend([
        f"",
        f"Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"",
        f"--",
        f"NetWatch Device Monitoring System",
    ])
    
    message = "\n".join(message_lines)
    
    # Get recipients
    recipients = [r.strip() for r in settings.ALERT_EMAIL_RECIPIENTS if r.strip()]
    
    if not recipients:
        logger.warning("No alert recipients configured")
        return False
    
    # Send email
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False,
        )
        
        # Log successful alert
        AlertLog.objects.create(
            device=device,
            alert_type=alert_type,
            old_status=old_status,
            new_status=new_status,
            message=message,
            recipients=', '.join(recipients),
            success=True,
        )
        
        logger.info(f"Alert sent for {device.name}: {old_status} → {new_status}")
        return True
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to send alert for {device.name}: {e}", exc_info=True)
        
        # Log failed alert
        AlertLog.objects.create(
            device=device,
            alert_type=alert_type,
            old_status=old_status,
            new_status=new_status,
            message=message,
            recipients=', '.join(recipients),
            success=False,
            error=error_msg,
        )
        
        return False


def test_alert_configuration() -> bool:
    """
    Test the alert configuration by sending a test email.
    
    Returns:
        True if test email was sent successfully, False otherwise
    """
    recipients = [r.strip() for r in settings.ALERT_EMAIL_RECIPIENTS if r.strip()]
    
    if not recipients:
        logger.error("No alert recipients configured")
        return False
    
    subject = "[NetWatch] Test Alert"
    message = """
This is a test alert from NetWatch Device Monitoring System.

If you receive this email, your alert configuration is working correctly.

Configured recipients: {}

--
NetWatch Device Monitoring System
    """.format(', '.join(recipients))
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False,
        )
        logger.info(f"Test alert sent successfully to {len(recipients)} recipients")
        return True
    except Exception as e:
        logger.error(f"Failed to send test alert: {e}", exc_info=True)
        return False
