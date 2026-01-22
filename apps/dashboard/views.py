"""
Views for the dashboard app.
"""
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from apps.inventory.models import Device, APIToken, Unit
from apps.monitoring.models import CheckResult, AgentReport, StatusChangeHistory

logger = logging.getLogger(__name__)


@login_required
def dashboard_view(request):
    """
    Main dashboard showing all devices with their current status.
    """
    # Get filter parameters
    device_type = request.GET.get('device_type', '')
    status = request.GET.get('status', '')
    location = request.GET.get('location', '')
    unit_id = request.GET.get('unit', '')
    search = request.GET.get('search', '')
    enabled_filter = request.GET.get('enabled', 'all')

    # Start with all devices
    devices = Device.objects.all()

    # Apply filters
    if device_type:
        devices = devices.filter(device_type=device_type)
    
    if status:
        devices = devices.filter(last_status=status)
    
    if location:
        devices = devices.filter(location__icontains=location)
    
    if search:
        devices = devices.filter(
            Q(name__icontains=search) | Q(ip_address__icontains=search)
        )

    if unit_id:
        devices = devices.filter(unit_id=unit_id)
    
    if enabled_filter == 'enabled':
        devices = devices.filter(enabled=True)
    elif enabled_filter == 'disabled':
        devices = devices.filter(enabled=False)

    # Get status counts for summary
    status_counts = Device.objects.filter(enabled=True).values('last_status').annotate(
        count=Count('id')
    )
    status_summary = {item['last_status']: item['count'] for item in status_counts}

    # Get distinct locations for filter dropdown
    locations = Device.objects.values_list('location', flat=True).distinct().order_by('location')
    locations = [loc for loc in locations if loc]  # Filter out empty strings
    units = Unit.objects.order_by('name')

    context = {
        'devices': devices.order_by('name'),
        'status_summary': status_summary,
        'locations': locations,
        'filters': {
            'device_type': device_type,
            'status': status,
            'location': location,
            'search': search,
            'unit': unit_id,
            'enabled': enabled_filter,
        },
        'device_types': Device.DEVICE_TYPE_CHOICES,
        'statuses': Device.STATUS_CHOICES,
        'units': units,
    }

    return render(request, 'dashboard/index.html', context)


@login_required
def device_detail_view(request, device_id):
    """
    Detailed view for a single device showing recent check history.
    """
    device = get_object_or_404(Device, id=device_id)
    
    # Get recent check results (last 24 hours by default)
    hours = int(request.GET.get('hours', 24))
    since = timezone.now() - timedelta(hours=hours)
    
    recent_results = CheckResult.objects.filter(
        device=device,
        created_at__gte=since
    ).order_by('-created_at')

    # Calculate statistics
    total_checks = recent_results.count()
    if total_checks > 0:
        up_count = recent_results.filter(overall_status='UP').count()
        degraded_count = recent_results.filter(overall_status='DEGRADED').count()
        down_count = recent_results.filter(overall_status='DOWN').count()
        
        uptime_percentage = (up_count / total_checks) * 100 if total_checks > 0 else 0
        
        # Average response times
        ping_results = recent_results.filter(ping_ok=True, ping_ms__isnull=False)
        avg_ping = sum(r.ping_ms for r in ping_results) / len(ping_results) if ping_results else None
    else:
        up_count = degraded_count = down_count = 0
        uptime_percentage = 0
        avg_ping = None

    statistics = {
        'total_checks': total_checks,
        'up_count': up_count,
        'degraded_count': degraded_count,
        'down_count': down_count,
        'uptime_percentage': uptime_percentage,
        'avg_ping_ms': avg_ping,
    }

    # Get latest result for quick status and limit to 100 most recent
    latest_result = recent_results[:100].first()
    
    # Get latest agent report for system metrics
    latest_agent_report = device.agent_reports.first()
    
    # Get status change history (last 10 changes)
    status_changes = device.status_history.all()[:10]

    context = {
        'device': device,
        'recent_results': recent_results,
        'latest_result': latest_result,
        'latest_agent_report': latest_agent_report,
        'statistics': statistics,
        'hours': hours,
        'status_changes': status_changes,
    }

    return render(request, 'dashboard/device_detail.html', context)


@login_required
def add_device_view(request):
    """
    Create a new device via form submission.
    """
    if request.method == 'POST':
        # Validate required fields
        name = request.POST.get('name', '').strip()
        ip_address = request.POST.get('ip_address', '').strip()
        device_type = request.POST.get('device_type', '').strip()
        location = request.POST.get('location', '').strip()
        notes = request.POST.get('notes', '').strip()
        enabled = request.POST.get('enabled') == 'on'
        unit_id = request.POST.get('unit', '').strip()
        new_unit_name = request.POST.get('new_unit_name', '').strip()
        
        errors = {}

        # Validate name
        if not name:
            errors['name'] = 'Device name is required.'
        
        # Validate IP address
        if not ip_address:
            errors['ip_address'] = 'IP address is required.'
        else:
            # Simple IP validation
            import re
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
            if not re.match(ip_pattern, ip_address):
                errors['ip_address'] = 'Invalid IP address format.'
            else:
                parts = [int(p) for p in ip_address.split('.')]
                if any(p > 255 for p in parts):
                    errors['ip_address'] = 'IP address octets must be 0-255.'
        
        # Validate device type
        valid_types = [choice[0] for choice in Device.DEVICE_TYPE_CHOICES]
        if not device_type:
            errors['device_type'] = 'Device type is required.'
        elif device_type not in valid_types:
            errors['device_type'] = 'Invalid device type selected.'
        
        # Handle unit assignment or creation
        unit = None
        if new_unit_name:
            # Create new unit
            if Unit.objects.filter(name__iexact=new_unit_name).exists():
                errors['new_unit_name'] = 'A unit with this name already exists.'
            else:
                unit = Unit.objects.create(
                    name=new_unit_name,
                    location=location  # Use same location as device
                )
        elif unit_id:
            # Use existing unit
            try:
                unit = Unit.objects.get(id=unit_id)
            except Unit.DoesNotExist:
                errors['unit'] = 'Selected unit not found.'
        
        # If no errors, create device
        if not errors:
            device = Device.objects.create(
                name=name,
                ip_address=ip_address,
                device_type=device_type,
                location=location,
                notes=notes,
                enabled=enabled,
                ping_enabled=True,
                unit=unit,
            )
            logger.info(f'Device created: {device.name} ({device.ip_address}) in unit {unit.name if unit else "None"} by user {request.user}')
            
            # Redirect to device detail or success page
            context = {
                'success': True,
                'device': device,
                'device_id': device.id,
            }
            return render(request, 'dashboard/add_device.html', context)
        
        # If errors, return form with errors
        context = {
            'errors': errors,
            'form_data': {
                'name': name,
                'ip_address': ip_address,
                'device_type': device_type,
                'location': location,
                'notes': notes,
                'enabled': enabled,
                'unit': unit_id,
                'new_unit_name': new_unit_name,
            },
            'device_types': Device.DEVICE_TYPE_CHOICES,
            'units': Unit.objects.order_by('name'),
        }
        return render(request, 'dashboard/add_device.html', context)
    
    # GET request - show empty form
    context = {
        'device_types': Device.DEVICE_TYPE_CHOICES,
        'units': Unit.objects.order_by('name'),
    }
    return render(request, 'dashboard/add_device.html', context)


@login_required
def manage_api_tokens(request):
    """
    Manage API tokens for agents.
    """
    devices = Device.objects.all()
    tokens = APIToken.objects.all().order_by('-created_at')
    
    context = {
        'devices': devices,
        'tokens': tokens,
    }
    return render(request, 'dashboard/manage_tokens.html', context)


@login_required
@require_http_methods(["POST"])
def create_api_token(request):
    """
    Create a new API token for a device.
    """
    device_id = request.POST.get('device_id')
    token_name = request.POST.get('token_name', '').strip()
    
    if not device_id or not token_name:
        return JsonResponse({'error': 'Device and token name required'}, status=400)
    
    try:
        device = Device.objects.get(id=device_id)
    except Device.DoesNotExist:
        return JsonResponse({'error': 'Device not found'}, status=404)
    
    # Delete old token if exists
    if hasattr(device, 'api_token') and device.api_token:
        device.api_token.delete()
    
    # Create new token
    token_string = APIToken.generate_token()
    token = APIToken.objects.create(
        device=device,
        token=token_string,
        name=token_name,
        enabled=True
    )
    
    logger.info(f"Created API token '{token_name}' for device {device.name}")
    
    return JsonResponse({
        'success': True,
        'token': token_string,
        'device_name': device.name,
        'token_name': token_name,
    })


@login_required
@require_http_methods(["POST"])
def delete_api_token(request, token_id):
    """
    Delete an API token.
    """
    try:
        token = APIToken.objects.get(id=token_id)
        device_name = token.device.name if token.device else 'Generic'
        token_name = token.name
        token.delete()
        
        logger.info(f"Deleted API token '{token_name}' for device {device_name}")
        
        return JsonResponse({'success': True})
    except APIToken.DoesNotExist:
        return JsonResponse({'error': 'Token not found'}, status=404)


@login_required
@require_http_methods(["POST"])
def toggle_api_token(request, token_id):
    """
    Enable/disable an API token.
    """
    try:
        token = APIToken.objects.get(id=token_id)
        token.enabled = not token.enabled
        token.save()
        
        logger.info(f"Token '{token.name}' set to {'enabled' if token.enabled else 'disabled'}")
        
        return JsonResponse({
            'success': True,
            'enabled': token.enabled
        })
    except APIToken.DoesNotExist:
        return JsonResponse({'error': 'Token not found'}, status=404)


@login_required
def edit_device(request, device_id):
    """
    Edit device information (IP address, name, settings).
    """
    device = get_object_or_404(Device, id=device_id)
    
    if request.method == 'POST':
        # Update device fields
        device.name = request.POST.get('name', device.name).strip()
        device.ip_address = request.POST.get('ip_address', device.ip_address).strip()
        device.device_type = request.POST.get('device_type', device.device_type)
        device.location = request.POST.get('location', '').strip()
        device.notes = request.POST.get('notes', '').strip()
        device.enabled = request.POST.get('enabled') == 'on'
        device.ping_enabled = request.POST.get('ping_enabled') == 'on'
        device.check_interval_seconds = int(request.POST.get('check_interval_seconds', 60))
        
        # Handle unit assignment or creation
        unit_id = request.POST.get('unit', '').strip()
        new_unit_name = request.POST.get('new_unit_name', '').strip()
        
        if new_unit_name:
            # Create new unit
            unit, created = Unit.objects.get_or_create(
                name__iexact=new_unit_name,
                defaults={'name': new_unit_name, 'location': device.location}
            )
            if not created:
                unit = Unit.objects.get(name__iexact=new_unit_name)
            device.unit = unit
        elif unit_id:
            # Use existing unit
            try:
                device.unit = Unit.objects.get(id=unit_id)
            except Unit.DoesNotExist:
                pass
        else:
            # Clear unit if none selected
            device.unit = None
        
        try:
            device.save()
            messages.success(request, f"Device '{device.name}' updated successfully")
            logger.info(f"Device {device.id} updated by {request.user.username}")
            return redirect('dashboard:device_detail', device_id=device.id)
        except Exception as e:
            messages.error(request, f"Error updating device: {str(e)}")
            logger.error(f"Error updating device {device.id}: {str(e)}")
    
    context = {
        'device': device,
        'device_types': Device.DEVICE_TYPE_CHOICES,
        'units': Unit.objects.order_by('name'),
    }
    return render(request, 'dashboard/edit_device.html', context)


@login_required
def unit_list(request):
    """List all units with device counts and status summary."""
    units = Unit.objects.annotate(device_count=Count('devices'))
    # Precompute status counts per unit
    unit_status = (
        Device.objects
        .values('unit_id', 'last_status')
        .annotate(count=Count('id'))
    )
    status_map = {}
    for row in unit_status:
        status_map.setdefault(row['unit_id'], {})[row['last_status']] = row['count']

    # Attach status summary to each unit
    unit_data = []
    for unit in units:
        summary = status_map.get(unit.id, {})
        unit_data.append({
            'unit': unit,
            'device_count': unit.device_count,
            'status_summary': summary,
        })

    return render(request, 'dashboard/unit_list.html', {'unit_data': unit_data})


@login_required
def unit_detail(request, unit_id):
    """Detail view showing all devices within a unit."""
    unit = get_object_or_404(Unit, id=unit_id)
    devices = unit.devices.all().order_by('name')

    # Status summary for this unit
    status_counts = (
        devices
        .values('last_status')
        .annotate(count=Count('id'))
    )
    status_summary = {row['last_status']: row['count'] for row in status_counts}

    return render(request, 'dashboard/unit_detail.html', {
        'unit': unit,
        'devices': devices,
        'status_summary': status_summary,
    })


@login_required
def manage_units(request):
    """Create units and assign devices to them from a single page."""
    devices = Device.objects.order_by('name')
    units = Unit.objects.annotate(device_count=Count('devices')).order_by('name')

    errors = {}
    form_data = {
        'name': '',
        'location': '',
        'description': '',
        'devices': [],
    }

    if request.method == 'POST':
        form_data['name'] = request.POST.get('name', '').strip()
        form_data['location'] = request.POST.get('location', '').strip()
        form_data['description'] = request.POST.get('description', '').strip()
        form_data['devices'] = request.POST.getlist('devices')

        # Validate inputs
        if not form_data['name']:
            errors['name'] = 'Unit name is required.'
        elif Unit.objects.filter(name__iexact=form_data['name']).exists():
            errors['name'] = 'A unit with this name already exists.'

        if not errors:
            unit = Unit.objects.create(
                name=form_data['name'],
                location=form_data['location'],
                description=form_data['description'],
            )

            if form_data['devices']:
                Device.objects.filter(id__in=form_data['devices']).update(unit=unit)

            messages.success(request, f"Unit '{unit.name}' created and devices assigned.")
            return redirect('dashboard:manage_units')
        else:
            messages.error(request, 'Please fix the errors below.')

    context = {
        'devices': devices,
        'units': units,
        'errors': errors,
        'form_data': form_data,
    }
    return render(request, 'dashboard/manage_units.html', context)
