import os
import django
import sys

# Setup Django environment
sys.path.append(r"c:\Users\USER 2\Downloads\project1\project1\land_registry")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'land_registry.settings')
django.setup()

from registry import models

print("--- Recent Custody Logs ---")
logs = models.CustodyLog.objects.all().order_by('-timestamp')[:10]
for log in logs:
    print(f"Time: {log.timestamp}, Action: {log.action}, File: {log.file_doc.ref_num}")
    print(f"  From Dept: {log.from_department.name if log.from_department else 'NONE'}")
    print(f"  To Dept: {log.to_department.name if log.to_department else 'NONE'}")
    print(f"  Reason: {log.reason}")
    print(f"  Acknowledged: {log.acknowledged}")
    print("-" * 20)
