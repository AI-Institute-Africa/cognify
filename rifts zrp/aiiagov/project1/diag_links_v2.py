import os
import django
import sys

# Setup Django environment
sys.path.append(r"c:\Users\USER 2\Downloads\project1\project1\land_registry")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'land_registry.settings')
django.setup()

from registry import models

print("--- All Files ---")
files = models.File.objects.filter(delete_flag=0)
for f in files:
    print(f"File: {f.ref_num}, Title: {f.title}, Dept: {f.current_department.name if f.current_department else 'NONE'}, Status: {f.f_status}")

print("\n--- Borrowers ---")
borrowers = models.Borrower.objects.all()
for b in borrowers:
    print(f"Borrower: {b.code}, Name: {b.first_name} {b.last_name}, Dept: {b.department.name if b.department else 'NONE'}")

print("\n--- Departments ---")
depts = models.Department.objects.all()
for d in depts:
    print(f"Dept: {d.name}")
