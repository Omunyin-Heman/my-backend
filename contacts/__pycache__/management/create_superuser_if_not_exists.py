from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings

class Command(BaseCommand):
    help = "Creates a superuser if it does not already exist."

    def handle(self, *args, **options):
        User = get_user_model()
        username = "administrator"
        email = "admin@example.com"
        password = "admin123"

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f"✅ Superuser '{username}' created successfully."))
        else:
            self.stdout.write(self.style.WARNING(f"⚠️ Superuser '{username}' already exists."))
