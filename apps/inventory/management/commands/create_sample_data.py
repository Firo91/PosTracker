"""
Management command to create sample test data.
Run with: python manage.py create_sample_data
"""
from django.core.management.base import BaseCommand
from apps.inventory.models import Device


class Command(BaseCommand):
    help = 'Create sample devices for testing'

    def handle(self, *args, **options):
        self.stdout.write("Creating sample data...")
        
        # Sample devices
        sample_devices = [
            {
                'name': 'POS-Terminal-01',
                'ip_address': '192.168.1.101',
                'device_type': 'POS',
                'location': 'Front Counter',
                'ping_enabled': True,
                'rdp_check_enabled': True,
                'simphony_check_mode': 'WINDOWS_SERVICE',
                'simphony_service_name': 'SimphonyService',
            },
            {
                'name': 'POS-Terminal-02',
                'ip_address': '192.168.1.102',
                'device_type': 'POS',
                'location': 'Drive-Through',
                'ping_enabled': True,
            },
            {
                'name': 'Server-Main',
                'ip_address': '192.168.1.10',
                'device_type': 'SERVER',
                'location': 'Server Room',
                'ping_enabled': True,
            },
            {
                'name': 'Test-Localhost',
                'ip_address': '127.0.0.1',
                'device_type': 'SERVER',
                'location': 'Local Testing',
                'ping_enabled': True,
                'notes': 'Localhost for testing ping functionality',
            },
        ]
        
        created_count = 0
        for device_data in sample_devices:
            device, created = Device.objects.get_or_create(
                name=device_data['name'],
                defaults=device_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Created device: {device.name} ({device.ip_address})")
                )
            else:
                self.stdout.write(f"  Device already exists: {device.name}")
        
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Sample data creation complete! Created {created_count} new devices."
        ))
        self.stdout.write("")
        self.stdout.write("Next steps:")
        self.stdout.write("1. Update device IP addresses to match your network")
        self.stdout.write("2. Run monitoring: python manage.py run_monitoring")
