"""
Models for agent-reported status.
"""
from django.db import models
from django.utils import timezone
from apps.inventory.models import Device


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
    disk_percent = models.FloatField(null=True, blank=True)
    
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
        Determine if all monitored services/processes are healthy.
        """
        # Check services
        for service_name, service_info in self.services_status.items():
            if not service_info.get('running', False):
                return False
        
        # Check processes
        for process_name, process_info in self.processes_status.items():
            if not process_info.get('running', False):
                return False
        
        return True
