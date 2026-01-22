"""
Management command to test alert configuration.
"""
from django.core.management.base import BaseCommand
from apps.monitoring.alerts import test_alert_configuration


class Command(BaseCommand):
    help = 'Send a test alert email to verify configuration'

    def handle(self, *args, **options):
        self.stdout.write("Sending test alert...")
        
        success = test_alert_configuration()
        
        if success:
            self.stdout.write(self.style.SUCCESS("✓ Test alert sent successfully!"))
            self.stdout.write("Check the configured email addresses for the test message.")
        else:
            self.stdout.write(self.style.ERROR("✗ Failed to send test alert."))
            self.stdout.write("Check the logs for error details.")
