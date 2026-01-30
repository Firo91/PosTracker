"""
API views for receiving agent reports.
"""
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json

from apps.inventory.models import Device, APIToken
from apps.monitoring.models import AgentReport, StatusChangeHistory, AgentStatusHistory

logger = logging.getLogger(__name__)


def validate_api_token(request):
    """
    Validate API token from request headers.
    Returns APIToken object or None.
    """
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    
    if not auth_header.startswith('Bearer '):
        return None
    
    token_string = auth_header[7:]  # Remove "Bearer " prefix
    
    try:
        token = APIToken.objects.get(token=token_string, enabled=True)
        token.record_usage()
        return token
    except APIToken.DoesNotExist:
        return None


@csrf_exempt
@require_http_methods(["POST"])
def agent_report(request):
    """
    Receive status report from an agent.
    Requires: Authorization header with Bearer token
    
    Expected JSON format:
    {
        "device_id": 1,
        "timestamp": "2026-01-08T12:00:00Z",
        "system_info": {
            "hostname": "POS-01",
            "cpu_percent": 25.5,
            "memory_percent": 60.2,
            "disk_percent": 45.0
        },
        "processes": {
            "ServiceHost (POS Program)": {
                "running": true,
                "count": 1,
                "instances": [{"pid": 1234, "memory_mb": 125.5, "cpu": 5.2}]
            }
        }
    }
    """
    try:
        # Validate API token
        api_token = validate_api_token(request)
        if not api_token:
            return JsonResponse({'error': 'Invalid or missing API token'}, status=401)
        
        # Parse request body
        data = json.loads(request.body)
        
        # Get device
        device_id = data.get('device_id')
        if not device_id:
            return JsonResponse({'error': 'device_id is required'}, status=400)
        
        try:
            device = Device.objects.get(id=device_id)
        except Device.DoesNotExist:
            return JsonResponse({'error': f'Device {device_id} not found'}, status=404)
        
        # Extract data
        system_info = data.get('system_info', {})
        processes = data.get('processes', {})
        
        # Create agent report
        report = AgentReport.objects.create(
            device=device,
            reported_at=timezone.now(),
            hostname=system_info.get('hostname', ''),
            cpu_percent=system_info.get('cpu_percent'),
            memory_percent=system_info.get('memory_percent'),
            memory_used_gb=system_info.get('memory_used_gb'),
            memory_total_gb=system_info.get('memory_total_gb'),
            disk_percent=system_info.get('disk_percent'),
            disk_used_gb=system_info.get('disk_used_gb'),
            disk_free_gb=system_info.get('disk_free_gb'),
            disk_total_gb=system_info.get('disk_total_gb'),
            uptime_hours=system_info.get('uptime_hours'),
            process_count=system_info.get('process_count'),
            processes_status=processes,
            raw_data=data
        )
        
        # Determine health (check all processes running)
        old_agent_status = None
        
        # Get the previous agent status from the most recent report
        previous_report = device.agent_reports.exclude(id=report.id).first()
        if previous_report:
            old_agent_status = previous_report.agent_healthy
        
        report.agent_healthy = report.determine_health()
        report.save()
        
        # Track agent status changes
        if old_agent_status is not None and old_agent_status != report.agent_healthy:
            # Build reason string based on what changed
            reason = "Agent health status changed"
            if not report.agent_healthy:
                # Agent became unhealthy - list what failed
                failed_items = []
                for name, status in report.processes_status.items():
                    if status.get('found', True) and not status.get('running', False):
                        failed_items.append(name)
                if failed_items:
                    reason = f"Services/processes not running: {', '.join(failed_items)}"
            else:
                # Agent recovered
                reason = "All monitored services/processes recovered"
            
            AgentStatusHistory.objects.create(
                device=device,
                old_status=old_agent_status,
                new_status=report.agent_healthy,
                reason=reason
            )
            logger.info(f"Agent status changed for {device.name}: {old_agent_status} -> {report.agent_healthy}")
        
        # Update device last agent report time
        device.last_agent_report = timezone.now()
        device.save(update_fields=['last_agent_report'])

        # Update device status immediately using fresh agent data
        old_status = device.last_status
        new_status = device.compute_overall_status()
        if new_status != old_status:
            device.last_status = new_status
            device.last_status_change = timezone.now()
            device.save(update_fields=['last_status', 'last_status_change'])

            StatusChangeHistory.objects.create(
                device=device,
                old_status=old_status,
                new_status=new_status,
                reason="Agent report updated status"
            )
        
        logger.info(f"Agent report received from {device.name} (ID: {device_id}) - Token: {api_token.name}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Report received',
            'report_id': report.id,
            'agent_healthy': report.agent_healthy
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error processing agent report: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def device_status(request):
    """
    Get current status for one or more devices.
    Requires: Authorization header with Bearer token
    
    Query parameters:
    - devices: comma-separated device names or IDs (e.g., ?devices=Caps,10.18.70.36 or ?devices=1,2,3)
    - unit: unit name to get all devices in that unit (e.g., ?unit=Store1)
    
    Returns latest AgentReport metrics for each device.
    """
    try:
        # Validate API token
        api_token = validate_api_token(request)
        if not api_token:
            return JsonResponse({'error': 'Invalid or missing API token'}, status=401)
        
        # Get query parameters
        devices_param = request.GET.get('devices', '')
        unit_param = request.GET.get('unit', '')
        
        if not devices_param and not unit_param:
            return JsonResponse({
                'error': 'Either "devices" or "unit" parameter is required',
                'usage': {
                    'by_devices': '/api/device-status/?devices=Caps,ServerA',
                    'by_unit': '/api/device-status/?unit=Store1'
                }
            }, status=400)
        
        # Find devices
        devices = []
        
        if unit_param:
            # Get all devices in the unit
            from apps.inventory.models import Unit
            try:
                unit = Unit.objects.get(name__iexact=unit_param)
                devices = list(Device.objects.filter(unit=unit, enabled=True))
            except Unit.DoesNotExist:
                return JsonResponse({'error': f'Unit "{unit_param}" not found'}, status=404)
        
        elif devices_param:
            # Parse comma-separated device identifiers
            device_identifiers = [d.strip() for d in devices_param.split(',') if d.strip()]
            
            for identifier in device_identifiers:
                # Try to find by ID (if numeric)
                if identifier.isdigit():
                    try:
                        device = Device.objects.get(id=int(identifier))
                        devices.append(device)
                        continue
                    except Device.DoesNotExist:
                        pass
                
                # Try to find by name
                try:
                    device = Device.objects.get(name__iexact=identifier)
                    devices.append(device)
                    continue
                except Device.DoesNotExist:
                    pass
                
                # Try to find by IP address
                try:
                    device = Device.objects.get(ip_address=identifier)
                    devices.append(device)
                    continue
                except Device.DoesNotExist:
                    pass
        
        if not devices:
            return JsonResponse({
                'error': 'No devices found',
                'searched': devices_param or f'unit: {unit_param}'
            }, status=404)
        
        # Build response with latest agent data for each device
        results = []
        
        for device in devices:
            latest_agent = device.agent_reports.first()
            
            device_data = {
                'device_id': device.id,
                'device_name': device.name,
                'ip_address': device.ip_address,
                'device_type': device.device_type,
                'unit': device.unit.name if device.unit else None,
                'location': device.location,
                'enabled': device.enabled,
                'status': device.last_status,
            }
            
            if latest_agent:
                device_data.update({
                    'agent_healthy': latest_agent.agent_healthy,
                    'reported_at': latest_agent.reported_at.isoformat(),
                    'uptime_hours': latest_agent.uptime_hours,
                    'uptime_days': round(latest_agent.uptime_hours / 24, 1) if latest_agent.uptime_hours else None,
                    'cpu_percent': latest_agent.cpu_percent,
                    'memory_percent': latest_agent.memory_percent,
                    'memory_used_gb': latest_agent.memory_used_gb,
                    'memory_total_gb': latest_agent.memory_total_gb,
                    'disk_percent': latest_agent.disk_percent,
                    'disk_used_gb': latest_agent.disk_used_gb,
                    'disk_free_gb': latest_agent.disk_free_gb,
                    'disk_total_gb': latest_agent.disk_total_gb,
                    'processes_status': latest_agent.processes_status,
                })
            else:
                device_data['agent_healthy'] = None
                device_data['reported_at'] = None
                device_data['message'] = 'No agent reports yet'
            
            results.append(device_data)
        
        return JsonResponse({
            'status': 'success',
            'count': len(results),
            'devices': results
        })
        
    except Exception as e:
        logger.error(f"Error getting device status: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)
