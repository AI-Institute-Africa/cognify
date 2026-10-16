import os
import django
import secrets
import io
import zipfile

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'land_registry.settings')
django.setup()

from django.contrib.auth.models import User
from registry.models import UserSecurity, ProjectPhase, ProjectTask

def list_users():
    print(f"{'Username':<20} | {'Role':<20} | {'Status':<10} | {'Superuser':<10}")
    print("-" * 70)
    for u in User.objects.all().order_by('username'):
        sec = UserSecurity.objects.filter(user=u).first()
        role = sec.role if sec else 'None'
        status = 'Approved' if (sec and sec.is_role_approved) else 'Pending'
        print(f"{u.username:<20} | {role:<20} | {status:<10} | {str(u.is_superuser):<10}")

def list_phases():
    print(f"\n{'Project':<30} | {'Phase Name':<20} | {'Status':<20}")
    print("-" * 75)
    for phase in ProjectPhase.objects.all().order_by('project__name', 'sequence'):
        print(f"{phase.project.name[:30]:<30} | {phase.name:<20} | {phase.status:<20}")

if __name__ == "__main__":
    list_users()
    list_phases()
