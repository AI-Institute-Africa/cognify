"""
Management command: enable_riftsx_mfa
--------------------------------------
Backfills mfa_enabled = True for all existing RIFTS-X Master platform
users so that they are required to complete email-based MFA on login,
matching the same security posture as Governance platform users.

Usage (run on PythonAnywhere Bash console):
    python manage.py enable_riftsx_mfa
"""

from django.core.management.base import BaseCommand
from registry.models import UserSecurity


class Command(BaseCommand):
    help = "Enable MFA for all existing RIFTS-X Master platform users."

    def handle(self, *args, **kwargs):
        qs = UserSecurity.objects.filter(platform='RIFTS-X', mfa_enabled=False)
        count = qs.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS(
                "All RIFTS-X users already have MFA enabled. Nothing to do."
            ))
            return

        updated = qs.update(mfa_enabled=True)
        self.stdout.write(self.style.SUCCESS(
            f"SUCCESS: Enabled MFA for {updated} RIFTS-X Master user(s)."
        ))

        # List the affected users for transparency
        for profile in UserSecurity.objects.filter(platform='RIFTS-X', mfa_enabled=True).select_related('user'):
            self.stdout.write(f"  - {profile.user.username}  ({profile.user.email})  role={profile.role}")
