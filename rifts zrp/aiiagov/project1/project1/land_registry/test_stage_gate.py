import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'land_registry.settings')
django.setup()

from registry.models import Project, ProjectPhase, ProjectTask, Department
from registry.services.governance import GovernanceService
from django.contrib.auth.models import User

def test_stage_gate():
    print("--- Starting Stage-Gate Verification ---")
    
    # 1. Setup
    owner = User.objects.first()
    dept = Department.objects.first()
    
    # 2. Project Creation & Auto-initialization
    print("Testing Project Initialization...")
    project = Project.objects.create(
        name="Stage-Gate Test Project",
        description="Testing the gate control logic.",
        department=dept,
        owner=owner,
        end_date="2026-12-31",
        status='Active'
    )
    
    GovernanceService.initialize_stage_gates(project)
    
    phases = project.phases.all().order_by('sequence')
    if phases.count() != 5:
        print(f"FAILED: Expected 5 phases, found {phases.count()}")
        return
    
    print(f"SUCCESS: Created 5 phases: {[p.name for p in phases]}")
    
    # 3. Test Phase 1 Advancement
    phase1 = phases[0]
    phase2 = phases[1]
    
    print(f"Testing Phase 1 ('{phase1.name}') Advancement...")
    
    # Create a pending task in Phase 1
    ProjectTask.objects.create(
        phase=phase1,
        title="Initial Task",
        owner=owner,
        due_date="2026-03-31",
        status='Pending'
    )
    
    # Try to advance with pending tasks
    success, msg = GovernanceService.advance_phase(phase1, owner)
    if success:
        print(f"FAILED: Should not advance with pending tasks. Msg: {msg}")
        return
    print(f"SUCCESS: Blocked advancement due to pending tasks. Msg: {msg}")
    
    # Complete the task
    task = phase1.tasks.first()
    task.status = 'Done'
    task.save()
    
    # Add a required document (Stage-Gate compliance)
    from registry.models import File, SubCategory
    subcat = SubCategory.objects.first()
    doc = File.objects.create(title="Evidence", sub_category=subcat, ref_num="TEST-DOC")
    phase1.required_documents.add(doc)
    
    # Advance again
    success, msg = GovernanceService.advance_phase(phase1, owner)
    if not success:
        print(f"FAILED: Should advance after tasks completed. Error: {msg}")
        return
    
    phase1.refresh_from_db()
    if phase1.status != 'Review':
        print(f"FAILED: Phase 1 status should be 'Review', found '{phase1.status}'")
        return
    print(f"SUCCESS: Phase 1 is now '{phase1.status}'")
    
    # 4. Test Gate Approval (Non-PM)
    print("Testing Gate Approval (Non-PM)...")
    other_user = User.objects.create_user(username="other_user", password="password")
    success, msg = GovernanceService.approve_phase(phase1, other_user, 'Approved')
    if success:
        print("FAILED: Other user should not be able to approve gate.")
        return
    print(f"SUCCESS: Correctly blocked unauthorized approval. Msg: {msg}")
    
    # 5. Test Gate Approval (PM/Owner)
    print("Testing Gate Approval (Authorized)...")
    success, msg = GovernanceService.approve_phase(phase1, owner, 'Approved')
    if not success:
        print(f"FAILED: PM should be able to approve gate. Error: {msg}")
        return
    
    phase1.refresh_from_db()
    phase2.refresh_from_db()
    
    if phase1.status != 'Completed' or phase2.status != 'Active':
        print(f"FAILED: Transition logic failed. P1: {phase1.status}, P2: {phase2.status}")
        return
    
    print(f"SUCCESS: Gate cleared! P1: {phase1.status}, P2: {phase2.status}")
    
    # Cleanup
    project.delete()
    other_user.delete()
    print("--- Stage-Gate Verification COMPLETED ---")

if __name__ == "__main__":
    test_stage_gate()
