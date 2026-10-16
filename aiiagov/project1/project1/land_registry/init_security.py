import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'land_registry.settings')
django.setup()

from django.contrib.auth.models import User
from registry.models import UserSecurity

def init_security():
    users = User.objects.all()
    count = 0
    for user in users:
        if not hasattr(user, 'security_profile'):
            UserSecurity.objects.get_or_create(user=user)
            count += 1
    print(f"Initialized {count} security profiles.")

if __name__ == "__main__":
    init_security()
