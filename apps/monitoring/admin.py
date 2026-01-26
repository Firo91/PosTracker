"""
Admin interface for monitoring app.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import CheckResult, AlertLog, StatusChangeHistory, AgentStatusHistory


@admin.register(CheckResult)
class CheckResultAdmin(admin.ModelAdmin):
    list_display = [
        'device',
        'created_at',
        'overall_status_badge',
        'ping_indicator',
        'check_duration_ms',
    ]
    list_filter = [
        'overall_status',
        'ping_ok',
        'created_at',
    ]
    search_fields = ['device__name', 'device__ip_address', 'error_message']
    readonly_fields = [
        'device',
        'created_at',
        'ping_ok',
        'ping_ms',
        'overall_status',
        'error_message',
        'consecutive_failures',
        'check_duration_ms',
    ]
    date_hierarchy = 'created_at'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

    def overall_status_badge(self, obj):
        color_map = {
            'UP': 'success',
            'DOWN': 'danger',
        }
        color = color_map.get(obj.overall_status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color,
            obj.overall_status
        )
    overall_status_badge.short_description = 'Status'

    def ping_indicator(self, obj):
        if obj.ping_ok:
            return format_html(
                '<span style="color: green;">✓ {}ms</span>',
                obj.ping_ms or 0
            )
        return format_html('<span style="color: red;">✗</span>')
    ping_indicator.short_description = 'Ping'

    class Media:
        css = {
            'all': ('https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',)
        }


@admin.register(AlertLog)
class AlertLogAdmin(admin.ModelAdmin):
    list_display = [
        'device',
        'alert_type',
        'status_change',
        'sent_at',
        'success_indicator',
    ]
    list_filter = [
        'alert_type',
        'success',
        'sent_at',
    ]
    search_fields = ['device__name', 'message', 'recipients']
    readonly_fields = [
        'device',
        'alert_type',
        'old_status',
        'new_status',
        'message',
        'sent_at',
        'recipients',
        'success',
        'error',
    ]
    date_hierarchy = 'sent_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def status_change(self, obj):
        if obj.old_status:
            return f"{obj.old_status} → {obj.new_status}"
        return obj.new_status
    status_change.short_description = 'Status Change'

    def success_indicator(self, obj):
        if obj.success:
            return format_html('<span style="color: green;">✓ Sent</span>')
        return format_html('<span style="color: red;">✗ Failed</span>')
    success_indicator.short_description = 'Delivery'

    class Media:
        css = {
            'all': ('https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',)
        }


@admin.register(StatusChangeHistory)
class StatusChangeHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'device',
        'changed_at',
        'status_change_display',
        'reason',
    ]
    list_filter = [
        'old_status',
        'new_status',
        'changed_at',
    ]
    search_fields = ['device__name', 'reason']
    readonly_fields = [
        'device',
        'old_status',
        'new_status',
        'changed_at',
        'reason',
    ]
    date_hierarchy = 'changed_at'
    ordering = ['-changed_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def status_change_display(self, obj):
        old_color = {
            'UP': 'success',
            'DEGRADED': 'warning',
            'DOWN': 'danger',
            'UNKNOWN': 'secondary'
        }.get(obj.old_status, 'secondary')
        
        new_color = {
            'UP': 'success',
            'DEGRADED': 'warning',
            'DOWN': 'danger',
            'UNKNOWN': 'secondary'
        }.get(obj.new_status, 'secondary')
        
        return format_html(
            '<span class="badge bg-{}">{}</span> → <span class="badge bg-{}">{}</span>',
            old_color, obj.old_status, new_color, obj.new_status
        )
    status_change_display.short_description = 'Status Change'

    class Media:
        css = {
            'all': ('https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',)
        }


@admin.register(AgentStatusHistory)
class AgentStatusHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'device',
        'changed_at',
        'status_change_display',
        'reason',
    ]
    list_filter = [
        'old_status',
        'new_status',
        'changed_at',
    ]
    search_fields = ['device__name', 'reason']
    readonly_fields = [
        'device',
        'old_status',
        'new_status',
        'changed_at',
        'reason',
    ]
    date_hierarchy = 'changed_at'
    ordering = ['-changed_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def status_change_display(self, obj):
        old_color = 'success' if obj.old_status else 'danger'
        old_text = 'Healthy' if obj.old_status else 'Unhealthy'
        new_color = 'success' if obj.new_status else 'danger'
        new_text = 'Healthy' if obj.new_status else 'Unhealthy'
        
        return format_html(
            '<span class="badge bg-{}">{}</span> → <span class="badge bg-{}">{}</span>',
            old_color, old_text, new_color, new_text
        )
    status_change_display.short_description = 'Agent Status Change'

    class Media:
        css = {
            'all': ('https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',)
        }
