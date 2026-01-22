import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Create an initial superuser if it does not exist (idempotent)."

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.getenv("ADMIN_USERNAME", "admin")
        email = os.getenv("ADMIN_EMAIL", "admin@example.com")
        password = os.getenv("ADMIN_PASSWORD")

        if not password:
            self.stdout.write(self.style.WARNING(
                "ADMIN_PASSWORD not set; skipping initial admin creation."
            ))
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.SUCCESS(
                f"Admin user '{username}' already exists; nothing to do."
            ))
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(
            f"Created initial superuser '{username}'"
        ))
