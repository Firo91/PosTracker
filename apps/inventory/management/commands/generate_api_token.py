"""
Management command to generate API tokens for devices.
Usage: python manage.py generate_api_token <device_id> [--name "Token Name"]
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.inventory.models import Device, APIToken


class Command(BaseCommand):
    help = 'Generate an API token for a device'

    def add_arguments(self, parser):
        parser.add_argument('device_id', type=int, help='Device ID')
        parser.add_argument(
            '--name',
            default='',
            help='Descriptive name for the token'
        )

    def handle(self, *args, **options):
        device_id = options['device_id']
        name = options.get('name', '')

        try:
            device = Device.objects.get(id=device_id)
        except Device.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Device with ID {device_id} not found')
            )
            return

        # Delete existing token if present
        if hasattr(device, 'api_token') and device.api_token:
            old_token = device.api_token
            old_token.delete()
            self.stdout.write(
                self.style.WARNING(f'Deleted previous token for {device.name}')
            )

        # Generate new token
        token_string = APIToken.generate_token()
        token_name = name or f'{device.name} API Token'

        token = APIToken.objects.create(
            device=device,
            token=token_string,
            name=token_name,
            enabled=True
        )

        self.stdout.write(
            self.style.SUCCESS(f'✓ Generated API token for {device.name}')
        )
        self.stdout.write(f'\nToken: {token_string}')
        self.stdout.write(
            f'\nAdd this to agent_config.json:\n'
            f'  "api_key": "{token_string}"\n'
        )
