"""
Simple test script to verify basic monitoring functionality.
Run with: python test_monitoring.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'netwatch.settings')
django.setup()

from apps.monitoring.engine import run_ping, run_tcp_check

def test_ping():
    """Test ping functionality."""
    print("Testing Ping Check...")
    print("-" * 50)
    
    # Test localhost
    ok, ms, error = run_ping('127.0.0.1', timeout_ms=1000)
    print(f"Ping 127.0.0.1: {'✓ OK' if ok else '✗ Failed'}")
    if ok:
        print(f"  Response time: {ms}ms")
    else:
        print(f"  Error: {error}")
    print()

def test_tcp():
    """Test TCP connectivity."""
    print("Testing TCP Check...")
    print("-" * 50)
    
    # Test a port that should be closed
    ok, ms, error = run_tcp_check('127.0.0.1', 9999, timeout_ms=1000)
    print(f"TCP 127.0.0.1:9999: {'✓ Connected' if ok else '✗ Failed'}")
    if ok:
        print(f"  Connection time: {ms}ms")
    else:
        print(f"  Error: {error}")
    print()

def main():
    """Run all tests."""
    print("\n" + "=" * 50)
    print("NetWatch Monitoring Engine Test")
    print("=" * 50 + "\n")
    
    test_ping()
    test_tcp()
    
    print("=" * 50)
    print("Tests completed!")
    print("=" * 50)

if __name__ == '__main__':
    main()
