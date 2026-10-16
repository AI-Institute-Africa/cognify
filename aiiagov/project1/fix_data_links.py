import os
import django
import sys

# Setup Django environment
sys.path.append(r"c:\Users\USER 2\Downloads\project1\project1\land_registry")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'land_registry.settings')
django.setup()

from registry import models

print("--- Data Repair Utility ---")

# 1. Fetch departments
legal_dept = models.Department.objects.filter(name='Legal Affairs').first()
records_dept = models.Department.objects.filter(name='Records Management').first()

if not legal_dept or not records_dept:
    print("Error: Required departments not found.")
    sys.exit(1)

# 2. Update Borrowers
print("Updating Borrowers...")
b1 = models.Borrower.objects.filter(code='62-3378997x34').first()
if b1:
    b1.department = legal_dept
    b1.save()
    print(f"Updated {b1.name()} to {legal_dept.name}")

b2 = models.Borrower.objects.filter(code='62-3378997L34').first()
if b2:
    b2.department = legal_dept
    b2.save()
    print(f"Updated {b2.name()} to {legal_dept.name}")

b3 = models.Borrower.objects.filter(code='65-86736635L65').first()
if b3:
    b3.department = records_dept
    b3.save()
    print(f"Updated {b3.name()} to {records_dept.name}")

# 3. Update File real-time departments if missing
print("\nRepairing File-Department links...")
active_files = models.File.objects.filter(delete_flag=0)
for f in active_files:
    if not f.current_department:
        # Check if it's currently borrowed
        borrow = models.Borrow.objects.filter(file_doc=f, status='0').first()
        if borrow and borrow.borrower.department:
            f.current_department = borrow.borrower.department
            f.save()
            print(f"Linked File {f.ref_num} to {f.current_department.name} (via Borrower)")

print("\n--- Repair Complete ---")
