import os
import django
import sys

sys.path.append(r"c:\Users\USER 2\Downloads\project1\project1\land_registry")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'land_registry.settings')
django.setup()

from registry import models
from registry.services.custody import CustodyService
from django.contrib.auth.models import User

with open("transfer_test_results.txt", "w") as f:
    try:
        f.write("--- Transfer Simulation ---\n")

        # Get a file and department from the DB
        file_obj = models.File.objects.filter(delete_flag=0).first()
        depts = models.Department.objects.all()
        user = User.objects.filter(is_superuser=True).first()

        if not file_obj:
            f.write("ERROR: No active files found!\n")
        elif not depts.exists():
            f.write("ERROR: No departments found!\n")
        elif not user:
            f.write("ERROR: No superuser found!\n")
        else:
            # Pick a target dept different from current
            target_dept = depts.exclude(id=file_obj.current_department_id).first()
            if not target_dept:
                target_dept = depts.first()

            f.write(f"File: {file_obj.ref_num} | Current Dept: {file_obj.current_department}\n")
            f.write(f"Target Dept: {target_dept.name}\n")
            f.write(f"User: {user.username}\n")

            # Simulate location
            location = models.FileLocation.objects.create(
                building="Test Building",
                floor="1",
                office="Office A",
                cabinet="Cabinet 1",
                shelf="Shelf 1"
            )
            f.write(f"Location created: {location}\n")

            # Try the transfer
            log = CustodyService.transfer(file_obj, user, target_dept, "Test transfer reason", location=location)
            f.write(f"SUCCESS! CustodyLog ID: {log.id}, from: {log.from_department}, to: {log.to_department}\n")

            # Clean up test data
            location.delete()
            log.delete()
            f.write("Cleanup done.\n")

    except Exception as e:
        import traceback
        f.write(f"EXCEPTION: {str(e)}\n")
        f.write(traceback.format_exc())
