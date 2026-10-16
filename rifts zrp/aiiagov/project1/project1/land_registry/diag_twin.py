import os
import django
import sys

# Setup Django environment
sys.path.append(r"c:\Users\USER 2\Downloads\project1\project1\land_registry")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'land_registry.settings')
django.setup()

from registry import models
from django.utils import timezone
from datetime import timedelta

with open("diag_results.txt", "w") as f:
    f.write("--- Digital Twin Data Diagnostic ---\n")

    # Check Departments
    depts = models.Department.objects.all()
    f.write(f"Total Departments: {depts.count()}\n")

    # Check Files
    total_files = models.File.objects.filter(delete_flag=0).count()
    files_with_dept = models.File.objects.filter(delete_flag=0, current_department__isnull=False).count()
    f.write(f"Total Active Files: {total_files}\n")
    f.write(f"Files with Department assigned: {files_with_dept}\n")

    # Check Overdue
    now = timezone.now()
    overdue_borrows = models.Borrow.objects.filter(status='0', return_date__lt=now.date())
    f.write(f"Total Overdue Borrows (status='0', return_date < {now.date()}): {overdue_borrows.count()}\n")

    # Check ALL active borrows
    active_borrows = models.Borrow.objects.filter(status='0')
    f.write(f"Total Active Borrows (status='0'): {active_borrows.count()}\n")
    for b in active_borrows:
        f.write(f"  - Borrow ID: {b.id}, File: {b.file_doc}, Return Date: {b.return_date}, Borrow Date: {b.borrowing_date}\n")

    # Check recent logs for flow
    recent_limit = now - timedelta(minutes=5)
    recent_logs = models.CustodyLog.objects.filter(timestamp__gt=recent_limit)
    f.write(f"Recent Custody Logs (last 5m): {recent_logs.count()}\n")

    # Sample file to see fields
    if total_files > 0:
        sample = models.File.objects.filter(delete_flag=0).first()
        f.write(f"Sample File: {sample.ref_num}, Dept: {sample.current_department}, Location: {sample.current_location}\n")
