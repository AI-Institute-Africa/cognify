import os
import django
import sys

# Setup Django environment
sys.path.append(r"c:\Users\USER 2\Downloads\project1\project1\land_registry")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'land_registry.settings')
django.setup()

from registry import models
from django.contrib.auth.models import User

def check_logs():
    print("--- Custody Log Debug ---")
    logs = models.CustodyLog.objects.all().order_by('-timestamp')[:5]
    print(f"Total Logs: {models.CustodyLog.objects.count()}")
    for l in logs:
        print(f"ID: {l.id} | File: {l.file_doc.ref_num} | Action: {l.action} | From: {l.from_department} | To: {l.to_department} | Time: {l.timestamp}")
        print(f"  Reason: {l.reason}")
        print(f"  File Current Dept: {l.file_doc.current_department}")

if __name__ == "__main__":
    check_logs()
