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
from apps.monitoring.models import AgentReport, StatusChangeHistory

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
        report.agent_healthy = report.determine_health()
        report.save()
        
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
