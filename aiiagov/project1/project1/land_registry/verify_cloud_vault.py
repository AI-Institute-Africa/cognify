import os
import django
import sys
from django.utils import timezone
from django.core.files.base import ContentFile

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'land_registry.settings')
django.setup()

from registry.models import Department, CloudFolder, CloudFile, CloudFileVersion, FileAccessLog, CloudShare
from django.contrib.auth.models import User
from registry.services.cloud import CloudService

def run_verification():
    print("--- RIFTS Document Cloud Verification ---")
    
    # 0. Cleanup
    CloudFile.objects.all().delete()
    CloudFolder.objects.filter(name='Confidential Contracts').delete()

    # 1. Setup Test Data
    print("[1/5] Setting up test governance context...")
    admin_user, _ = User.objects.get_or_create(username='cloud_admin', is_staff=True)
    dept, _ = Department.objects.get_or_create(name='Legal Affairs')
    
    root_folder = CloudService.get_or_create_folder(
        name='Confidential Contracts',
        department=dept,
        user=admin_user,
        project_context='PROJ-DEED-2024'
    )
    print(f"      Governance Folder created: {root_folder}")

    # 2. Test File Upload & Versioning
    print("[2/5] Testing file ingestion & versioning...")
    dummy_file = ContentFile(b"Initial content for deed agreement v1", name="land_title_deed.pdf")
    
    cloud_file = CloudService.upload_file(
        folder=root_folder,
        uploaded_file=dummy_file,
        user=admin_user,
        commit_message="Initial legal draft"
    )
    print(f"      File uploaded: {cloud_file.name} (v{cloud_file.latest_version.version_number})")
    
    # Upload v2
    dummy_file_v2 = ContentFile(b"Updated content with witness signatures", name="land_title_deed.pdf")
    CloudService.upload_file(
        folder=root_folder,
        uploaded_file=dummy_file_v2,
        user=admin_user,
        commit_message="Witness signatures added"
    )
    
    cloud_file.refresh_from_db()
    v_count = cloud_file.latest_version.version_number
    print(f"      Version incremented: {cloud_file.name} (v{v_count})")
    assert v_count == 2, f"Expected v2, got v{v_count}"

    # 3. Test Rollback
    print("[3/5] Testing institutional rollback...")
    success = CloudService.rollback(cloud_file, 1, admin_user)
    print(f"      Rollback successful: {success}")
    cloud_file.refresh_from_db()
    v_count_after = cloud_file.latest_version.version_number
    print(f"      New version after rollback: v{v_count_after} (Message: {cloud_file.latest_version.commit_message})")
    assert v_count_after == 3, f"Expected v3, got v{v_count_after}"
    assert "Rollback to v1" in cloud_file.latest_version.commit_message

    # Test View Log
    CloudService.log_access(admin_user, cloud_file, 'VIEW', version=cloud_file.latest_version)

    # 4. Test Audit Logging
    print("[4/5] Verifying institutional audit trail...")
    logs = FileAccessLog.objects.filter(cloud_file=cloud_file)
    l_count = logs.count()
    print(f"      Total audit events recorded: {l_count}")
    for log in logs:
        print(f"      - {log.timestamp.strftime('%H:%M:%S')}: {log.action} by {log.user.username}")
    assert l_count >= 4, f"Expected at least 4 logs, got {l_count}"

    # 5. Test Secure Sharing
    print("[5/5] Testing expiry-based secure sharing...")
    share = CloudService.create_share(cloud_file, admin_user, expiry_days=1)
    print(f"      Secure Link Generated: /cloud/s/{share.access_token}")
    print(f"      Expiry Valid: {share.is_valid()}")
    assert share.is_valid() == True
    
    print("\n--- Verification COMPLETE: All Governance Rules Satisfied ---")

if __name__ == "__main__":
    run_verification()
