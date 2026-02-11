"""
Models for device inventory and credential management.
"""
from datetime import timedelta
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from typing import Optional
import secrets


class Unit(models.Model):
    """
    Logical grouping for devices (e.g., store/brand/region).
    """
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Unit/brand/store name"
    )
    country_code = models.CharField(
        max_length=2,
        blank=True,
        help_text="ISO 2-letter country code (e.g., NO, IS)"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description for this unit"
    )
    location = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional location/region"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Unit'
        verbose_name_plural = 'Units'

    def __str__(self) -> str:
        return self.name


class APIToken(models.Model):
    """
    API authentication token for secure agent-to-server communication.
    """
    device = models.OneToOneField(
        'Device',
        on_delete=models.CASCADE,
        related_name='api_token',
        null=True,
        blank=True,
        help_text="Device this token is for (optional, can be generic)"
    )
    token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Unique authentication token"
    )
    name = models.CharField(
        max_length=100,
        help_text="Descriptive name for this token"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this token was created"
    )
    last_used = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this token was last used"
    )
    enabled = models.BooleanField(
        default=True,
        help_text="Whether this token is active"
    )

    class Meta:
        verbose_name = "API Token"
        verbose_name_plural = "API Tokens"

    def __str__(self):
        return f"{self.name} ({self.token[:8]}...)"

    @staticmethod
    def generate_token():
        """Generate a secure random token."""
        return secrets.token_urlsafe(48)

    def record_usage(self):
        """Update last_used timestamp."""
        self.last_used = timezone.now()
        self.save(update_fields=['last_used'])


class Device(models.Model):
    """
    Represents a Windows POS terminal or server to be monitored.
    """
    DEVICE_TYPE_CHOICES = [
        ('POS', 'POS Terminal'),
        ('SERVER', 'Server'),
    ]

    STATUS_CHOICES = [
        ('UP', 'Up'),
        ('DEGRADED', 'Degraded'),
        ('DOWN', 'Down'),
        ('UNKNOWN', 'Unknown'),
    ]

    # Basic device information
    unit = models.ForeignKey(
        Unit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='devices',
        help_text="Unit/brand grouping for this device"
    )
    name = models.CharField(
        max_length=255,
        help_text="Friendly name for the device"
    )
    ip_address = models.GenericIPAddressField(
        protocol='IPv4',
        help_text="Static IP address of the device"
    )
    device_type = models.CharField(
        max_length=10,
        choices=DEVICE_TYPE_CHOICES,
        default='POS'
    )
    location = models.CharField(
        max_length=255,
        blank=True,
        help_text="Physical location or description"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about the device"
    )
    enabled = models.BooleanField(
        default=True,
        help_text="Whether monitoring is enabled for this device"
    )

    # Monitoring settings - ping only
    ping_enabled = models.BooleanField(
        default=True,
        help_text="Enable ping checks"
    )

    # Check parameters
    check_interval_seconds = models.PositiveIntegerField(
        default=60,
        validators=[MinValueValidator(10)],
        help_text="Interval between checks in seconds"
    )
    timeout_ms = models.PositiveIntegerField(
        default=1200,
        validators=[MinValueValidator(100), MaxValueValidator(30000)],
        help_text="Timeout for individual checks in milliseconds"
    )
    retries = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Number of retries on failure"
    )
    failure_threshold = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(1)],
        help_text="Consecutive failures before marking as DOWN"
    )
    success_threshold = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Consecutive successes to recover from DOWN"
    )

    # Current status (cached for performance)
    last_status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='UNKNOWN',
        help_text="Last known status"
    )
    last_status_change = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the status last changed"
    )
    last_check_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the last check was performed"
    )
    consecutive_failures = models.PositiveIntegerField(
        default=0,
        help_text="Current count of consecutive failures"
    )
    consecutive_successes = models.PositiveIntegerField(
        default=0,
        help_text="Current count of consecutive successes"
    )
    
    # Agent reporting
    last_agent_report = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the agent last reported status"
    )
    
    # Separate state tracking for independent alerts
    last_ping_state = models.BooleanField(
        null=True,
        blank=True,
        help_text="Last known ping state (True=UP/OK, False=DOWN/Failed)"
    )
    last_agent_state = models.BooleanField(
        null=True,
        blank=True,
        help_text="Last known agent state (True=Healthy, False=Unhealthy/None)"
    )
    last_down_services = models.JSONField(
        default=list,
        blank=True,
        help_text="Last known set of down services/processes for deduplication"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Device'
        verbose_name_plural = 'Devices'
        indexes = [
            models.Index(fields=['enabled', 'last_status']),
            models.Index(fields=['device_type']),
            models.Index(fields=['ip_address']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['unit', 'name'],
                name='unique_device_name_per_unit'
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.ip_address})"

    def update_status(self, new_status: str) -> None:
        """
        Update device status and track status changes.
        """
        if self.last_status != new_status:
            self.last_status = new_status
            self.last_status_change = timezone.now()
            self.save(update_fields=['last_status', 'last_status_change'])

    def get_status_display_color(self) -> str:
        """
        Return Bootstrap color class for the current status.
        """
        color_map = {
            'UP': 'success',
            'DEGRADED': 'warning',
            'DOWN': 'danger',
            'UNKNOWN': 'secondary',
        }
        return color_map.get(self.last_status, 'secondary')

    def compute_overall_status(self) -> str:
        """
        Compute overall device status considering both ping and agent health.
        Returns: 'UP', 'DEGRADED', 'DOWN', or 'UNKNOWN'
        """
        from apps.monitoring.models import CheckResult, AgentReport
        freshness_minutes = getattr(settings, 'AGENT_FRESH_MINUTES', 10)
        freshness_cutoff = timezone.now() - timedelta(minutes=freshness_minutes)
        
        # Get latest check result (ping)
        latest_check = self.check_results.first()
        ping_ok = latest_check.ping_ok if latest_check else None
        
        # Get latest agent report
        latest_agent = self.agent_reports.first()
        agent_healthy = latest_agent.agent_healthy if latest_agent else None
        agent_fresh = bool(latest_agent and latest_agent.reported_at >= freshness_cutoff)
        
        # Logic:
        # - If ping fails but agent recently reports → treat as reachable (UP/DEGRADED)
        # - If ping fails and no fresh agent → DOWN
        # - If ping OK but agent unhealthy → DEGRADED (reachable but services down)
        # - If ping OK and agent healthy → UP
        # - If no data → UNKNOWN/agent-driven status
        
        if ping_ok is False:
            if agent_fresh:
                if agent_healthy is False:
                    return 'DOWN'
                if agent_healthy is True:
                    return 'DEGRADED'
                return 'DOWN'
            return 'DOWN'

        if ping_ok is True:
            if agent_healthy is False:
                return 'DEGRADED'
            if agent_healthy is True:
                return 'UP'
            # Ping OK but no agent data yet
            return 'UP'

        # No ping data
        if agent_fresh:
            return 'DEGRADED' if agent_healthy is False else 'UP'
        return 'UNKNOWN'
