import os
import django
import sys

# Set up Django environment
sys.path.append(r'c:\Users\USER 2\Downloads\project1\project1\land_registry')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'land_registry.settings')
django.setup()

from registry.models import Organization, FederationLink, File, Department, CustodyLog
from registry.services.federation import FederationService
from registry.services.custody import CustodyService
from django.contrib.auth.models import User
from django.utils import timezone

def test_federation():
    print("Starting Federation Mode Test...")
    
    # 1. Setup Organizations
    local_org = FederationService.get_or_create_local_org()
    print(f"Local Org: {local_org.name} ({local_org.code})")
    
    remote_org, created = Organization.objects.get_or_create(
        name="University of Zimbabwe",
        code="UZ_FED",
        api_endpoint="https://uz.edu.zw/api/rifts-x",
        is_local=False
    )
    print(f"Remote Org: {remote_org.name} created: {created}")
    
    # 2. Setup Federation Link
    link, created = FederationLink.objects.get_or_create(
        source_org=local_org,
        target_org=remote_org,
        defaults={'link_status': 'Active'}
    )
    if not created:
        link.link_status = 'Active'
        link.save()
    print(f"Federation Link status: {link.link_status}")
    
    # 3. Setup Test File and User
    user = User.objects.first()
    dept = Department.objects.first()
    file_obj, created = File.objects.get_or_create(
        ref_num="TEST-FED-001",
        defaults={
            'title': "Federated Test Document",
            'sub_category_id': 1, # Assuming 1 exists
            'f_status': 'available'
        }
    )
    print(f"Test File: {file_obj.ref_num}")
    
    # 4. Perform Federated Transfer
    print("Initiating federated transfer...")
    try:
        CustodyService.federated_transfer(
            file_obj=file_obj,
            current_user=user,
            target_org=remote_org,
            target_dept_name="Legal Department",
            reason="Inter-institutional review"
        )
        print("Federated transfer COMPLETED.")
        
        # 5. Verify Logs
        last_log = CustodyLog.objects.filter(file_doc=file_obj).order_by('-timestamp').first()
        print(f"Last Log Action: {last_log.action}")
        print(f"From Org: {last_log.from_organization.name if last_log.from_organization else 'N/A'}")
        print(f"To Org: {last_log.to_organization.name}")
        
        # 6. Verify File Status
        file_obj.refresh_from_db()
        print(f"File Current Status: {file_obj.f_status}")
        
        if file_obj.f_status == 'external' and last_log.to_organization == remote_org:
            print("\nVERIFICATION SUCCESSFUL: Federation mode logic is sound.")
        else:
            print("\nVERIFICATION FAILED: Status or organization mismatch.")
            
    except Exception as e:
        print(f"TEST ERROR: {str(e)}")

if __name__ == "__main__":
    test_federation()
