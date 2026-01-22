"""
Management command to run monitoring checks without Celery.
This can be scheduled using Windows Task Scheduler.
"""
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.inventory.models import Device
from apps.monitoring.tasks import check_device

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run monitoring checks for all enabled devices (alternative to Celery)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--device-id',
            type=int,
            help='Check a specific device by ID',
        )
        parser.add_argument(
            '--device-name',
            type=str,
            help='Check a specific device by name',
        )

    def handle(self, *args, **options):
        device_id = options.get('device_id')
        device_name = options.get('device_name')

        if device_id:
            # Check specific device by ID
            try:
                device = Device.objects.get(id=device_id, enabled=True)
                self.stdout.write(f"Checking device: {device.name}")
                check_device(device.id)
                self.stdout.write(self.style.SUCCESS(f"✓ Check completed for {device.name}"))
            except Device.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Device with ID {device_id} not found or disabled"))
                return

        elif device_name:
            # Check specific device by name
            try:
                device = Device.objects.get(name=device_name, enabled=True)
                self.stdout.write(f"Checking device: {device.name}")
                check_device(device.id)
                self.stdout.write(self.style.SUCCESS(f"✓ Check completed for {device.name}"))
            except Device.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Device '{device_name}' not found or disabled"))
                return

        else:
            # Check all enabled devices
            devices = Device.objects.filter(enabled=True)
            
            if not devices.exists():
                self.stdout.write(self.style.WARNING("No enabled devices found"))
                return

            self.stdout.write(f"Found {devices.count()} enabled devices")
            
            for device in devices:
                # Check if enough time has passed since last check
                if device.last_check_at:
                    time_since_last_check = (timezone.now() - device.last_check_at).total_seconds()
                    if time_since_last_check < device.check_interval_seconds:
                        self.stdout.write(
                            f"⊘ Skipping {device.name}: checked {time_since_last_check:.1f}s ago"
                        )
                        continue

                self.stdout.write(f"→ Checking {device.name} ({device.ip_address})...")
                try:
                    check_device(device.id)
                    self.stdout.write(self.style.SUCCESS(f"  ✓ {device.name}: {device.last_status}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  ✗ Error checking {device.name}: {e}"))
                    logger.error(f"Error checking {device.name}: {e}", exc_info=True)

            self.stdout.write(self.style.SUCCESS("\nMonitoring check cycle completed"))
