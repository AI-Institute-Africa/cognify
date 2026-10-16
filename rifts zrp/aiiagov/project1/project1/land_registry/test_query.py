import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'land_registry.settings')
django.setup()

from registry.models import Department, CloudFolder
from django.contrib.auth.models import User

try:
    d = Department.objects.first()
    print(f"Department found: {d.name}")
    print(f"Testing reverse relation 'cloud_folders':")
    print(list(d.cloud_folders.all()))
    
    print("\nTesting CloudFolder creation:")
    u = User.objects.first()
    cf, created = CloudFolder.objects.get_or_create(
        name="Test Folder",
        department=d,
        parent=None,
        defaults={'created_by': u}
    )
    print(f"CloudFolder: {cf}, Created: {created}")

except Exception as e:
    import traceback
    traceback.print_exc()
