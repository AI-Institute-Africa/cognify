import os
import django
import sys

# Setup Django
sys.path.append(r'c:\Users\USER 2\Downloads\project1\project1\land_registry')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'land_registry.settings')
django.setup()

from django.contrib.auth.models import User
from registry.models import ProjectPhase, Project
from registry.services.governance import GovernanceService

def verify():
    # 1. Get Project Leader user
    try:
        pl_user = User.objects.get(username='chacks')
        print(f"Found PL user: {pl_user.username}")
    except User.DoesNotExist:
        print("PL user 'chacks' not found")
        return

    # 2. Get an Active phase where 'chacks' is PM
    phase = ProjectPhase.objects.filter(pm=pl_user, status='Active').first()
    if not phase:
        print("No Active phase found for chacks")
        return
    
    print(f"Testing with phase: {phase.name} (Current Status: {phase.status})")

    # 3. Attempt Level 1 submission (PL acting as Team Member or advancing)
    print("Attempting Level 1 submission as PL...")
    success, message = GovernanceService.team_member_submit_to_pl(
        phase, 
        pl_user, 
        comments="Verification Level 1"
    )
    
    if success:
        print(f"SUCCESS: {message}")
        phase.refresh_from_db()
        print(f"New Status: {phase.status}")
        
        if phase.status == 'Awaiting Project Leader Approval':
            # 4. Attempt Level 2 approval (PL approving)
            print("Attempting Level 2 approval as PL...")
            success2, message2 = GovernanceService.pl_submit_to_pmt(
                phase,
                pl_user,
                comments="Verification Level 2"
            )
            if success2:
                print(f"SUCCESS: {message2}")
                phase.refresh_from_db()
                print(f"Final Status: {phase.status}")
                if phase.status == 'Awaiting PMT Approval':
                    print("VERIFICATION COMPLETE: PL can now submit and review.")
                else:
                    print(f"FAILED: Expected 'Awaiting PMT Approval', got '{phase.status}'")
            else:
                print(f"FAILED Level 2: {message2}")
        else:
            print(f"FAILED: Expected 'Awaiting Project Leader Approval', got '{phase.status}'")
    else:
        print(f"FAILED Level 1: {message}")

if __name__ == "__main__":
    verify()
