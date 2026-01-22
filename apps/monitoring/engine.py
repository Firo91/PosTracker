"""
Monitoring engine for performing device checks.

This module contains the core monitoring logic for ping checks using Windows ping command.
"""
import subprocess
import re
import logging
import time
from typing import Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CheckResult:
    """Result of a monitoring check."""
    ok: bool
    duration_ms: Optional[int] = None
    error: Optional[str] = None


def run_ping(ip_address: str, timeout_ms: int = 1200) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Perform a ping check using Windows ping command.
    
    Args:
        ip_address: IP address to ping
        timeout_ms: Timeout in milliseconds
        
    Returns:
        Tuple of (success, response_time_ms, error_message)
    """
    try:
        # Windows ping command: ping -n 1 -w <timeout_ms> <ip>
        # -n 1: Send only 1 echo request
        # -w <timeout>: Timeout in milliseconds
        cmd = ['ping', '-n', '1', '-w', str(timeout_ms), ip_address]
        
        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_ms / 1000 + 1  # Add 1 second buffer for subprocess timeout
        )
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Parse ping output
        # Look for "Reply from" or "time=" in output
        if result.returncode == 0 and 'Reply from' in result.stdout:
            # Extract time from output
            # Example: "Reply from 192.168.1.1: bytes=32 time=1ms TTL=64"
            time_match = re.search(r'time[=<](\d+)ms', result.stdout)
            if time_match:
                ping_time = int(time_match.group(1))
            else:
                # If time is <1ms, it might show as "time<1ms"
                if 'time<1ms' in result.stdout:
                    ping_time = 0
                else:
                    ping_time = duration_ms
            
            logger.debug(f"Ping to {ip_address} successful: {ping_time}ms")
            return True, ping_time, None
        else:
            error_msg = result.stdout.strip() if result.stdout else "No response"
            logger.warning(f"Ping to {ip_address} failed: {error_msg}")
            return False, None, error_msg
            
    except subprocess.TimeoutExpired:
        error_msg = f"Ping timeout after {timeout_ms}ms"
        logger.warning(f"Ping to {ip_address} timed out")
        return False, None, error_msg
    except Exception as e:
        error_msg = f"Ping error: {str(e)}"
        logger.error(f"Ping to {ip_address} error: {e}", exc_info=True)
        return False, None, error_msg
