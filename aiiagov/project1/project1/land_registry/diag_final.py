import os
import django
import sys

# Setup Django environment
sys.path.append(r"c:\Users\USER 2\Downloads\project1\project1\land_registry")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'land_registry.settings')
django.setup()

from registry import models
from django.db.models import Q

with open("diag_final_results.txt", "w") as f:
    f.write("--- Digital Twin Data Diagnostic ---\n")
    
    # 1. Departments
    depts = models.Department.objects.all()
    f.write(f"Total Departments: {depts.count()}\n")
    for d in depts:
        f.write(f"  ID: {d.id}, Name: {d.name}\n")
        
    # 2. Files
    files = models.File.objects.filter(delete_flag=0)
    f.write(f"Total Active Files: {files.count()}\n")
    
    # 3. Borrows
    borrows = models.Borrow.objects.filter(status='0')
    f.write(f"Total Active Borrows (status='0'): {borrows.count()}\n")
    for b in borrows:
        f.write(f"  Borrow ID: {b.id}, File: {b.file_doc}, Borrower: {b.borrower}\n")
        if b.borrower:
            f.write(f"    Borrower Dept: {b.borrower.department}\n")
            
    # 4. Check query consistency
    for dept in depts:
        # This is the exact query from views.py
        file_count = models.File.objects.filter(
            Q(current_department=dept) | Q(file_doc_id_fk__borrower__department=dept, file_doc_id_fk__status='0'),
            delete_flag=0
        ).distinct().count()
        f.write(f"  Dept '{dept.name}' (ID: {dept.id}) -> Calculated File Count: {file_count}\n")

    # 5. Check DigitalShare (if used)
    # The view also counts DigitalShare status='active'? 
    # No, get_digital_twin_updates only uses File and Borrow (via backref).
