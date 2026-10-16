import os
import django
import sys

# Setup Django environment
sys.path.append(r"c:\Users\USER 2\Downloads\project1\project1\land_registry")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'land_registry.settings')
django.setup()

from registry.models import File, Department, CloudFolder, CustodyLog, FileApproval, FileLocation
from registry.services.custody import CustodyService
from django.contrib.auth.models import User

def verify():
    print("--- RIFTS-X Physical-Digital Twin Verification ---")
    
    # 1. Setup
    user = User.objects.filter(is_superuser=True).first()
    dept = Department.objects.first()
    if not user or not dept:
        print("Error: Need at least one superuser and one department for testing.")
        return

    ref_num = f"TWIN-TEST-{os.urandom(2).hex().upper()}"
    print(f"Testing with File Ref: {ref_num}")

    # 2. Test File Creation & Auto-Provisioning
    print("\n[Test 1] Auto-Provisioning...")
    from registry.models import SubCategory
    subcat = SubCategory.objects.first()
    if not subcat:
        print("Error: Need at least one sub-category for testing.")
        return

    loc = FileLocation.objects.create(building="Test B", floor="1", cabinet="A", shelf="1")
    file_obj = File.objects.create(
        ref_num=ref_num,
        title=f"Test Twin File {ref_num}",
        sub_category=subcat,
        current_department=dept,
        current_location=loc
    )
    
    # Trigger custody and cloud (simulating save_file_doc logic)
    from registry.services.cloud import CloudService
    CustodyService.record_creation(file_obj, user, loc)
    CloudService.get_or_create_folder(file_obj.ref_num, dept, user=user)
    
    # Verify Cloud Folder
    folder = CloudFolder.objects.filter(name=ref_num, department=dept).first()
    if folder:
        print(f"SUCCESS: Digital Twin Folder created for {ref_num}")
    else:
        print(f"FAILED: Digital Twin Folder NOT found for {ref_num}")

    # 3. Test Loss Workflow
    print("\n[Test 2] Property Loss Workflow...")
    CustodyService.mark_lost(file_obj, user, "Testing displacement resilience.")
    file_obj.refresh_from_db()
    
    if file_obj.is_lost:
        print("SUCCESS: File status marked as LOST.")
        last_log = CustodyLog.objects.filter(file_doc=file_obj, action='LOST').first()
        if last_log:
            print(f"SUCCESS: Custody log entry created: {last_log.reason}")
    else:
        print("FAILED: File status NOT updated to LOST.")

    # 4. Test Recovery Workflow
    print("\n[Test 3] Recovery Workflow...")
    new_loc = FileLocation.objects.create(building="Recovered B", floor="G", cabinet="X", shelf="9")
    CustodyService.mark_found(file_obj, user, new_loc, "Found in archive basement.")
    file_obj.refresh_from_db()
    
    if not file_obj.is_lost and file_obj.current_location == new_loc:
        print("SUCCESS: File status RESTORED and location updated.")
    else:
        print("FAILED: Recovery workflow did not update status/location correctly.")

    # 5. Test Approval Trigger
    print("\n[Test 4] Approval System...")
    app = CustodyService.request_approval(file_obj, user, 'Digitization', "Requesting high-res scan clearance.")
    if app:
        print(f"SUCCESS: Approval request created: {app.action_type} ({app.status})")
    else:
        print("FAILED: Approval request creation failed.")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    verify()
