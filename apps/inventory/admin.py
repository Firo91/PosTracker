"""
Admin interface for inventory app.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Device, APIToken, Unit


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'unit',
        'ip_address',
        'device_type',
        'location',
        'status_badge',
        'enabled',
        'last_check_at',
    ]
    list_filter = [
        'enabled',
        'device_type',
        'last_status',
        'unit',
    ]
    search_fields = ['name', 'ip_address', 'location', 'unit__name']
    readonly_fields = [
        'last_status',
        'last_status_change',
        'last_check_at',
        'consecutive_failures',
        'consecutive_successes',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Device Information', {
            'fields': (
                'unit',
                'name',
                'ip_address',
                'device_type',
                'location',
                'notes',
                'enabled',
            )
        }),
        ('Network Checks', {
            'fields': (
                'ping_enabled',
            )
        }),
        ('Check Parameters', {
            'fields': (
                'check_interval_seconds',
                'timeout_ms',
                'retries',
                'failure_threshold',
                'success_threshold',
            ),
            'classes': ('collapse',)
        }),
        ('Status Information', {
            'fields': (
                'last_status',
                'last_status_change',
                'last_check_at',
                'consecutive_failures',
                'consecutive_successes',
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        color = obj.get_status_display_color()
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.get_last_status_display()
        )
    status_badge.short_description = 'Status'

    class Media:
        css = {
            'all': ('https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',)
        }


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'description', 'created_at')
    search_fields = ('name', 'location', 'description')


@admin.register(APIToken)
class APITokenAdmin(admin.ModelAdmin):
    list_display = ('name', 'device', 'short_token', 'enabled', 'created_at', 'last_used')
    list_filter = ('enabled', 'created_at', 'device')
    search_fields = ('name', 'token', 'device__name')
    readonly_fields = ('token', 'created_at', 'last_used')
    
    fieldsets = (
        ('Token Information', {
            'fields': ('name', 'device', 'token', 'enabled'),
            'description': 'Leave Device blank for a generic token (can query all devices), or select a specific device to limit access.'
        }),
        ('Metadata', {
            'fields': ('created_at', 'last_used'),
            'classes': ('collapse',)
        }),
    )
    
    def short_token(self, obj):
        """Display shortened token for security."""
        return f"{obj.token[:12]}...{obj.token[-12:]}"
    short_token.short_description = 'Token (masked)'
    
    def get_readonly_fields(self, request, obj=None):
        """Make token and device read-only after creation."""
        if obj:  # Editing existing object
            return self.readonly_fields + ['device']
        return self.readonly_fields
