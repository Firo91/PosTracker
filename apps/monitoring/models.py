"""
Models for storing monitoring check results.
"""
from django.db import models
from django.utils import timezone
from apps.inventory.models import Device
from typing import Optional


class StatusChangeHistory(models.Model):
    """
    Track when device status changes.
    Useful for identifying when issues occur and recovery times.
    """
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    
    old_status = models.CharField(
        max_length=10,
        choices=[('UP', 'Up'), ('DEGRADED', 'Degraded'), ('DOWN', 'Down'), ('UNKNOWN', 'Unknown')]
    )
    new_status = models.CharField(
        max_length=10,
        choices=[('UP', 'Up'), ('DEGRADED', 'Degraded'), ('DOWN', 'Down'), ('UNKNOWN', 'Unknown')]
    )
    
    changed_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the status change occurred"
    )
    
    reason = models.CharField(
        max_length=255,
        blank=True,
        help_text="Why the status changed (e.g., ping failed, service down)"
    )
    
    class Meta:
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['device', '-changed_at']),
        ]
    
    def __str__(self):
        return f"{self.device.name}: {self.old_status} → {self.new_status} at {self.changed_at}"


class AgentStatusHistory(models.Model):
    """
    Track when agent health status changes.
    Useful for identifying when the agent or monitored services go down/up.
    """
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='agent_status_history'
    )
    
    old_status = models.BooleanField(
        null=True,
        blank=True,
        help_text="Previous agent health status (True=healthy, False=unhealthy, None=no contact)"
    )
    new_status = models.BooleanField(
        null=True,
        blank=True,
        help_text="New agent health status (True=healthy, False=unhealthy, None=no contact)"
    )
    
    changed_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When the agent status change occurred"
    )
    
    reason = models.CharField(
        max_length=255,
        blank=True,
        help_text="Why the agent status changed (e.g., service stopped, agent recovered)"
    )
    
    class Meta:
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['device', '-changed_at']),
        ]
        verbose_name_plural = "Agent status histories"
    
    def __str__(self):
        old_text = "No contact" if self.old_status is None else "Healthy" if self.old_status else "Unhealthy"
        new_text = "No contact" if self.new_status is None else "Healthy" if self.new_status else "Unhealthy"
        return f"{self.device.name} Agent: {old_text} → {new_text} at {self.changed_at}"


class AgentReport(models.Model):
    """Store status reports from agents running on devices."""
    
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='agent_reports'
    )
    
    # Timestamp
    reported_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When the agent sent this report"
    )
    
    # System info
    hostname = models.CharField(max_length=255, blank=True)
    cpu_percent = models.FloatField(null=True, blank=True)
    memory_percent = models.FloatField(null=True, blank=True)
    memory_used_gb = models.FloatField(null=True, blank=True)
    memory_total_gb = models.FloatField(null=True, blank=True)
    disk_percent = models.FloatField(null=True, blank=True)
    disk_used_gb = models.FloatField(null=True, blank=True)
    disk_free_gb = models.FloatField(null=True, blank=True)
    disk_total_gb = models.FloatField(null=True, blank=True)
    uptime_hours = models.FloatField(null=True, blank=True)
    process_count = models.IntegerField(null=True, blank=True)
    
    # Service/Process status (JSON field for flexibility)
    services_status = models.JSONField(
        default=dict,
        help_text="Dictionary of service statuses"
    )
    processes_status = models.JSONField(
        default=dict,
        help_text="Dictionary of process statuses"
    )
    
    # Overall agent status
    agent_healthy = models.BooleanField(
        default=True,
        help_text="True if all monitored services/processes are running"
    )
    
    # Raw data
    raw_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Full agent report data"
    )
    
    class Meta:
        ordering = ['-reported_at']
        indexes = [
            models.Index(fields=['device', '-reported_at']),
        ]
    
    def __str__(self):
        return f"{self.device.name} - {self.reported_at}"
    
    def determine_health(self) -> bool:
        """
        Determine if monitored services/processes are healthy.

        Rules:
        - Ignore services explicitly marked as not found (found=False)
        - For services without a 'found' key, use 'running' if present
        - Any found service that is not running => unhealthy
        - Any process with 'running' False => unhealthy
        - If no evaluable checks exist, default to True (agent up but nothing monitored)
        """
        evaluable = False

        # Services: only count those that are found (or no 'found' key provided)
        for service_info in self.services_status.values():
            found = service_info.get('found')
            running = service_info.get('running', False)

            if found is False:
                # Misnamed or not installed service; ignore for health calculation
                continue

            evaluable = True
            if not running:
                return False

        # Processes: use 'running' directly
        for process_info in self.processes_status.values():
            evaluable = True
            if not process_info.get('running', False):
                return False

        # If nothing evaluable, consider agent healthy (no monitored items)
        return True


class CheckResult(models.Model):
    """
    Stores the result of a monitoring check for a device.
    """
    STATUS_CHOICES = [
        ('UP', 'Up'),
        ('DOWN', 'Down'),
    ]

    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='check_results',
        help_text="The device this check was performed on"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When this check was performed"
    )

    # Ping check results
    ping_ok = models.BooleanField(
        default=False,
        help_text="Whether ping was successful"
    )
    ping_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Ping response time in milliseconds"
    )

    # Overall status
    overall_status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='DOWN',
        help_text="Overall device status"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error messages from failed checks"
    )

    # Consecutive failure tracking
    consecutive_failures = models.PositiveIntegerField(
        default=0,
        help_text="Number of consecutive failures at the time of this check"
    )

    # Check duration
    check_duration_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Total duration of the check in milliseconds"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Check Result'
        verbose_name_plural = 'Check Results'
        indexes = [
            models.Index(fields=['device', '-created_at']),
            models.Index(fields=['overall_status']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self) -> str:
        return f"{self.device.name} - {self.overall_status} at {self.created_at}"

    def determine_overall_status(self) -> str:
        """
        Determine overall device status based on ping check.
        
        Logic:
        - If ping OK => UP
        - If ping failed => DOWN
        """
        return 'UP' if self.ping_ok else 'DOWN'


class AlertLog(models.Model):
    """
    Tracks sent alerts to prevent spam and provide audit trail.
    """
    ALERT_TYPE_CHOICES = [
        ('STATUS_CHANGE', 'Status Change'),
        ('DOWN_ALERT', 'Device Down'),
        ('UP_ALERT', 'Device Up'),
        ('DEGRADED_ALERT', 'Service Degraded'),
    ]

    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='alert_logs',
        help_text="The device this alert is about"
    )
    alert_type = models.CharField(
        max_length=20,
        choices=ALERT_TYPE_CHOICES,
        help_text="Type of alert"
    )
    old_status = models.CharField(
        max_length=10,
        blank=True,
        help_text="Previous status"
    )
    new_status = models.CharField(
        max_length=10,
        help_text="New status"
    )
    message = models.TextField(
        help_text="Alert message content"
    )
    sent_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the alert was sent"
    )
    recipients = models.TextField(
        help_text="Comma-separated list of recipients"
    )
    success = models.BooleanField(
        default=True,
        help_text="Whether the alert was sent successfully"
    )
    error = models.TextField(
        blank=True,
        help_text="Error message if sending failed"
    )

    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Alert Log'
        verbose_name_plural = 'Alert Logs'
        indexes = [
            models.Index(fields=['device', '-sent_at']),
            models.Index(fields=['-sent_at']),
        ]

    def __str__(self) -> str:
        return f"{self.alert_type} for {self.device.name} at {self.sent_at}"
