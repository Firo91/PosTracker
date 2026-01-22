"""
Unit tests for monitoring engine.
"""
import unittest
from unittest.mock import patch, MagicMock
from apps.monitoring.engine import run_ping, run_tcp_check


class TestPingCheck(unittest.TestCase):
    """Tests for ping functionality."""
    
    @patch('subprocess.run')
    def test_successful_ping(self, mock_run):
        """Test successful ping response."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='Reply from 192.168.1.1: bytes=32 time=5ms TTL=64'
        )
        
        ok, ms, error = run_ping('192.168.1.1', timeout_ms=1000)
        
        self.assertTrue(ok)
        self.assertEqual(ms, 5)
        self.assertIsNone(error)
    
    @patch('subprocess.run')
    def test_failed_ping(self, mock_run):
        """Test failed ping response."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout='Request timed out.'
        )
        
        ok, ms, error = run_ping('192.168.1.1', timeout_ms=1000)
        
        self.assertFalse(ok)
        self.assertIsNone(ms)
        self.assertIsNotNone(error)


class TestTCPCheck(unittest.TestCase):
    """Tests for TCP connectivity checks."""
    
    @patch('socket.socket')
    def test_successful_tcp_connect(self, mock_socket):
        """Test successful TCP connection."""
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0
        mock_socket.return_value = mock_sock
        
        ok, ms, error = run_tcp_check('192.168.1.1', 3389, timeout_ms=1000)
        
        self.assertTrue(ok)
        self.assertIsNotNone(ms)
        self.assertIsNone(error)
    
    @patch('socket.socket')
    def test_failed_tcp_connect(self, mock_socket):
        """Test failed TCP connection."""
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 1
        mock_socket.return_value = mock_sock
        
        ok, ms, error = run_tcp_check('192.168.1.1', 3389, timeout_ms=1000)
        
        self.assertFalse(ok)
        self.assertIsNone(ms)
        self.assertIsNotNone(error)


if __name__ == '__main__':
    unittest.main()
