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
from django.db.models import Q

def run_diag():
    print("--- Digital Twin Deep Diagnostic ---")
    
    # 1. Departments
    depts = models.Department.objects.all()
    print(f"Total Departments: {depts.count()}")
    for d in depts:
        print(f"  ID: {d.id}, Name: {d.name}")
        
    # 2. Files
    files = models.File.objects.filter(delete_flag=0)
    print(f"Total Active Files: {files.count()}")
    
    # 3. Borrows
    borrows = models.Borrow.objects.filter(status='0')
    print(f"Total Active Borrows (Status 'Issued'): {borrows.count()}")
    for b in borrows:
        try:
            dept = b.borrower.department if b.borrower else "No Borrower"
            print(f"  Borrow ID: {b.id}, File: {b.file_doc}, Borrower Dept: {dept}")
        except Exception as e:
            print(f"  Borrow ID: {b.id} Error: {e}")

    # 4. Check query logic used in View
    for dept in depts:
        f_count = models.File.objects.filter(
            Q(current_department=dept) | Q(file_doc_id_fk__borrower__department=dept, file_doc_id_fk__status='0'),
            delete_flag=0
        ).distinct().count()
        print(f"  Department '{dept.name}' calculated file count: {f_count}")

    # 5. Recent Logs (for flows)
    recent_limit = timezone.now() - timedelta(minutes=60) # broadened for check
    logs = models.CustodyLog.objects.filter(timestamp__gt=recent_limit)
    print(f"Recent Custody Logs (last 60m): {logs.count()}")

if __name__ == "__main__":
    run_diag()
