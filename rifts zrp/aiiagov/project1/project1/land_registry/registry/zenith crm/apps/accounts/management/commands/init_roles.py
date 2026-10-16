from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from apps.accounts.constants import DEFAULT_ROLES


class Command(BaseCommand):
    help = "Create default role groups for Confluence Nexus"

    def handle(self, *args, **options):
        self.stdout.write("Initializing default user roles...")
        for role in DEFAULT_ROLES:
            group, created = Group.objects.get_or_create(name=role)
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created group: {role}"))
            else:
                self.stdout.write(self.style.WARNING(f"Group already exists: {role}"))
        self.stdout.write(self.style.SUCCESS("Default roles are initialized."))
