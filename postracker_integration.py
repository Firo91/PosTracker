"""
PosTracker + ChatWarning Integration Module

Provides easy API to send alerts from PosTracker monitoring to ChatWarning
for real-time alert notifications.
"""
import os
import logging
import json
import requests
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ChatWarningIntegration:
    """
    Integration with ChatWarning for sending alerts.
    
    Requires environment variables:
    - ALERT_CHAT_BASE_URL: Base URL of ChatWarning (e.g., https://chatwarning.herokuapp.com)
    - ALERT_CHAT_USER: Admin username
    - ALERT_CHAT_PASS: Admin password
    """
    
    def __init__(self):
        self.base_url = os.getenv('ALERT_CHAT_BASE_URL', '').rstrip('/')
        self.username = os.getenv('ALERT_CHAT_USER', '')
        self.password = os.getenv('ALERT_CHAT_PASS', '')
        self.timeout = 10  # seconds
        
        # Log credentials status for debugging
        logger.info(f"DEBUG: ChatWarning init - base_url={self.base_url}")
        logger.info(f"DEBUG: ChatWarning init - username={self.username}")
        logger.info(f"DEBUG: ChatWarning init - password_set={bool(self.password)}")
        
        # JWT token cache
        self._access_token = None
        self._token_expiry = None
        
        # Channel cache
        self._channel_cache = {}
        
        if not all([self.base_url, self.username, self.password]):
            logger.warning(
                "ChatWarning integration not configured. "
                "Set ALERT_CHAT_BASE_URL, ALERT_CHAT_USER, ALERT_CHAT_PASS environment variables."
            )
    
    def is_configured(self) -> bool:
        """Check if integration is properly configured."""
        return bool(self.base_url and self.username and self.password)
    
    def _get_token(self) -> Optional[str]:
        """Get JWT access token, using cache if valid."""
        # Check if cached token is still valid
        if self._access_token and self._token_expiry and datetime.now() < self._token_expiry:
            return self._access_token
        
        # Get new token
        try:
            logger.info(f"DEBUG: Requesting JWT token from {self.base_url}/api/token/")
            response = requests.post(
                f"{self.base_url}/api/token/",
                json={"username": self.username, "password": self.password},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            self._access_token = data.get('access')
            # Token valid for 24 hours, cache for 23 hours to be safe
            self._token_expiry = datetime.now() + timedelta(hours=23)
            
            logger.info("DEBUG: JWT token obtained successfully")
            return self._access_token
            
        except Exception as e:
            logger.error(f"Failed to get JWT token from ChatWarning: {e}")
            return None
    
    def send_alert(
        self,
        device_name: str,
        status: str,
        alert_type: str,
        message: str,
        channel_name: str = 'alerts',
        previous_status: Optional[str] = None,
        severity: str = 'info',
        unit_name: Optional[str] = None
    ) -> bool:
        """
        Send an alert to ChatWarning.
        
        Args:
            device_name: Name of the device
            status: Current status (UP, DOWN, DEGRADED, WARNING)
            alert_type: Type of alert (STATUS_CHANGE, PROCESS_DOWN, CPU_HIGH, RAM_HIGH, STORAGE_HIGH, UPTIME_LONG)
            message: Detailed alert message
            channel_name: Target channel in ChatWarning (default: 'alerts')
            previous_status: Previous status (for status changes)
            severity: Alert severity (info, warning, critical)
            
        Returns:
            True if alert sent successfully, False otherwise
        """
        if not self.is_configured():
            logger.warning("ChatWarning not configured. Alert not sent.")
            return False
        
        try:
            # Get JWT token
            token = self._get_token()
            if not token:
                logger.error("Failed to obtain JWT token")
                return False
            
            # Headers with Bearer token
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # First, get the channel ID by querying /api/chat/channels/
            try:
                logger.info(f"DEBUG: Fetching channels from {self.base_url}/api/chat/channels/")
                channels_response = requests.get(
                    f"{self.base_url}/api/chat/channels/",
                    headers=headers,
                    timeout=self.timeout
                )
                channels_response.raise_for_status()
                channels = channels_response.json()
                
                # Find channel by name
                channel_id = None
                for ch in channels:
                    if ch['name'] == channel_name:
                        channel_id = ch['id']
                        break
                
                if not channel_id:
                    logger.error(f"Channel '{channel_name}' not found in ChatWarning")
                    return False
                    
            except Exception as e:
                logger.error(f"Failed to fetch channels from ChatWarning: {e}")
                return False
            
            # Build alert title - show status transition if applicable
            if unit_name:
                device_label = f"{device_name} ({unit_name})"
            else:
                device_label = device_name
            
            if previous_status and previous_status != status:
                title = f"{device_label}: {previous_status} → {status}"
            else:
                title = f"{device_label}: {status}"
            
            # Prepare alert payload for ChatWarning API
            alert_payload = {
                'channel': channel_id,
                'app_name': 'postracker',
                'severity': severity,
                'title': title,
                'description': message
            }
            
            # Send to ChatWarning alerts endpoint
            endpoint = f"{self.base_url}/api/chat/alerts/"
            
            response = requests.post(
                endpoint,
                json=alert_payload,
                headers=headers,
                timeout=self.timeout
            )
            
            # Check response
            if response.status_code in [200, 201]:
                logger.info(
                    f"Alert sent to ChatWarning: {device_name} - {alert_type} "
                    f"(channel: {channel_name})"
                )
                return True
            else:
                logger.error(
                    f"Failed to send alert to ChatWarning. "
                    f"Status: {response.status_code}, Response: {response.text}"
                )
                return False
        
        except requests.exceptions.Timeout:
            logger.error(
                f"Timeout connecting to ChatWarning ({self.base_url}). "
                f"Alert not sent for {device_name}"
            )
            return False
        except requests.exceptions.ConnectionError as e:
            logger.error(
                f"Connection error to ChatWarning ({self.base_url}): {e}. "
                f"Alert not sent for {device_name}"
            )
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error sending alert to ChatWarning: {e}",
                exc_info=True
            )
            return False


# Global integration instance
_integration = ChatWarningIntegration()


def send_device_alert(
    device_name: str,
    status: str,
    alert_type: str,
    message: str,
    channel_name: str = 'alerts',
    previous_status: Optional[str] = None,
    severity: str = 'info',
    unit_name: Optional[str] = None
) -> bool:
    """
    Send a device alert to ChatWarning.
    
    Convenience function wrapping ChatWarningIntegration.send_alert()
    
    Args:
        device_name: Name of the device
        status: Current status (UP, DOWN, DEGRADED, WARNING)
        alert_type: Type of alert (STATUS_CHANGE, PROCESS_DOWN, CPU_HIGH, RAM_HIGH, STORAGE_HIGH, UPTIME_LONG)
        message: Detailed alert message
        channel_name: Target channel in ChatWarning (default: 'alerts')
        previous_status: Previous status (for status changes)
        severity: Alert severity (info, warning, critical)
        unit_name: Unit name (optional, added to title if provided)
        
    Returns:
        True if alert sent successfully, False otherwise
    """
    return _integration.send_alert(
        device_name=device_name,
        status=status,
        alert_type=alert_type,
        message=message,
        channel_name=channel_name,
        previous_status=previous_status,
        severity=severity,
        unit_name=unit_name
    )


def send_process_alert(
    device_name: str,
    process_name: str,
    channel_name: str = 'alerts'
) -> bool:
    """
    Send a process down alert.
    
    Args:
        device_name: Name of the device
        process_name: Name of the process that went down
        channel_name: Target channel
        
    Returns:
        True if alert sent successfully
    """
    return send_device_alert(
        device_name=device_name,
        status='DOWN',
        alert_type='PROCESS_DOWN',
        message=f'Process "{process_name}" is not running',
        channel_name=channel_name,
        severity='critical'
    )


def send_process_recovery_alert(
    device_name: str,
    process_name: str,
    channel_name: str = 'alerts'
) -> bool:
    """
    Send a process recovery alert.
    
    Args:
        device_name: Name of the device
        process_name: Name of the process that recovered
        channel_name: Target channel
        
    Returns:
        True if alert sent successfully
    """
    return send_device_alert(
        device_name=device_name,
        status='UP',
        alert_type='PROCESS_RECOVERED',
        message=f'Process "{process_name}" is running again',
        channel_name=channel_name,
        severity='info'
    )


def send_cpu_alert(
    device_name: str,
    cpu_percent: float,
    threshold: float = 80.0,
    channel_name: str = 'alerts'
) -> bool:
    """
    Send a high CPU alert.
    
    Args:
        device_name: Name of the device
        cpu_percent: Current CPU percentage
        threshold: CPU threshold that was exceeded
        channel_name: Target channel
        
    Returns:
        True if alert sent successfully
    """
    return send_device_alert(
        device_name=device_name,
        status='WARNING',
        alert_type='CPU_HIGH',
        message=f'CPU usage is {cpu_percent:.1f}% (threshold: {threshold:.1f}%)',
        channel_name=channel_name,
        severity='warning'
    )


def send_memory_alert(
    device_name: str,
    memory_percent: float,
    threshold: float = 80.0,
    channel_name: str = 'alerts'
) -> bool:
    """
    Send a high memory/RAM alert.
    
    Args:
        device_name: Name of the device
        memory_percent: Current memory percentage
        threshold: Memory threshold that was exceeded
        channel_name: Target channel
        
    Returns:
        True if alert sent successfully
    """
    return send_device_alert(
        device_name=device_name,
        status='WARNING',
        alert_type='RAM_HIGH',
        message=f'Memory usage is {memory_percent:.1f}% (threshold: {threshold:.1f}%)',
        channel_name=channel_name,
        severity='warning'
    )


def send_storage_alert(
    device_name: str,
    disk_percent: float,
    threshold: float = 90.0,
    channel_name: str = 'alerts'
) -> bool:
    """
    Send a high storage/disk alert.
    
    Args:
        device_name: Name of the device
        disk_percent: Current disk usage percentage
        threshold: Disk threshold that was exceeded
        channel_name: Target channel
        
    Returns:
        True if alert sent successfully
    """
    return send_device_alert(
        device_name=device_name,
        status='WARNING',
        alert_type='STORAGE_HIGH',
        message=f'Storage usage is {disk_percent:.1f}% (threshold: {threshold:.1f}%)',
        channel_name=channel_name,
        severity='warning'
    )


def send_uptime_alert(
    device_name: str,
    uptime_hours: float,
    threshold_days: int = 30,
    channel_name: str = 'alerts'
) -> bool:
    """
    Send an alert for device running longer than threshold.
    
    Args:
        device_name: Name of the device
        uptime_hours: Current uptime in hours
        threshold_days: Uptime threshold in days
        channel_name: Target channel
        
    Returns:
        True if alert sent successfully
    """
    uptime_days = uptime_hours / 24
    return send_device_alert(
        device_name=device_name,
        status='WARNING',
        alert_type='UPTIME_LONG',
        message=f'Device has been running for {uptime_days:.1f} days (threshold: {threshold_days} days). Consider reboot.',
        channel_name=channel_name,
        severity='info'
    )


def send_status_change_alert(
    device_name: str,
    old_status: str,
    new_status: str,
    reason: str = '',
    channel_name: str = 'server-monitoring'
) -> bool:
    """
    Send a device status change alert.
    
    Args:
        device_name: Name of the device
        old_status: Previous status
        new_status: New status
        reason: Reason for status change
        channel_name: Target channel
        
    Returns:
        True if alert sent successfully
    """
    # Determine severity based on new status
    if new_status == 'DOWN':
        severity = 'critical'
    elif new_status == 'DEGRADED':
        severity = 'warning'
    else:  # UP
        severity = 'info'
    
    message = f"Device status changed from {old_status} to {new_status}"
    if reason:
        message += f". Reason: {reason}"
    
    return send_device_alert(
        device_name=device_name,
        status=new_status,
        alert_type='STATUS_CHANGE',
        message=message,
        channel_name=channel_name,
        previous_status=old_status,
        severity=severity
    )
