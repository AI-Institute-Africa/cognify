import os
import django
import sys

# Setup Django environment
sys.path.append(r"c:\Users\USER 2\Downloads\project1\project1\land_registry")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'land_registry.settings')
django.setup()

from registry import models

print("--- Borrower-Department Mapping ---")
borrowers = models.Borrower.objects.all()
for b in borrowers:
    print(f"Borrower: {b.code} - {b.first_name} {b.last_name}, Dept: {b.department.name if b.department else 'NONE'}")

print("\n--- Department File Counts (Direct) ---")
depts = models.Department.objects.all()
for d in depts:
    count = models.File.objects.filter(current_department=d, delete_flag=0).count()
    print(f"Dept: {d.name}, Direct File Count: {count}")

print("\n--- Active Borrows ---")
borrows = models.Borrow.objects.filter(status='0')
for b in borrows:
    print(f"Borrower: {b.borrower.code}, File: {b.file_doc.ref_num}, Borrower Dept: {b.borrower.department.name if b.borrower.department else 'NONE'}")
