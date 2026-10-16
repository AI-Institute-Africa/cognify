import os
import django
import sys
import zipfile
import io
from django.test import RequestFactory
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'land_registry.settings')
django.setup()

from registry.models import Project, ProjectPhase, ProjectTask, Department, UserSecurity, SubCategory, File, TaskAttachment
from registry.views import download_phase_deliverables, manage_task, executive_governance

def verify_fixes():
    print("--- Starting Final Verification ---")
    
    # Setup
    owner = User.objects.first()
    dept = Department.objects.first()
    factory = RequestFactory()
    subcat = SubCategory.objects.first() or SubCategory.objects.create(name="Governance")

    # 1. Verify Zip Download Logic
    print("Testing Zip Download Logic...")
    project = Project.objects.create(name="Zip Test", department=dept, owner=owner)
    phase = ProjectPhase.objects.create(project=project, name="Phase 1", sequence=1, status='Done')
    task = ProjectTask.objects.create(phase=phase, title="Task 1", owner=owner, is_deliverable=True)
    
    # Add task attachment
    TaskAttachment.objects.create(task=task, filename="task_file.txt", file=io.BytesIO(b"Task content"))
    
    # Add phase required document
    doc = File.objects.create(title="Phase Doc", sub_category=subcat, ref_num="P-DOC")
    doc.file_attachment.save("phase_doc.txt", io.BytesIO(b"Phase content"))
    phase.required_documents.add(doc)
    
    request = factory.get(f'/download-phase-deliverables/{phase.pk}/')
    request.user = owner
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    
    response = download_phase_deliverables(request, phase.pk)
    
    if response.status_code == 200:
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            file_list = zf.namelist()
            print(f"Zip Content: {file_list}")
            has_task_file = any("task_file.txt" in f for f in file_list)
            has_phase_doc = any("phase_doc.txt" in f for f in file_list)
            if has_task_file and has_phase_doc:
                print("SUCCESS: Zip includes both task and phase files.")
            else:
                print(f"FAILED: Zip missing files. Task file: {has_task_file}, Phase doc: {has_phase_doc}")
    else:
        print(f"FAILED: Zip download returned status {response.status_code}")

    # 2. Verify Task Creation Fields
    print("\nTesting Task Creation Fields...")
    # Create a team member user
    tm_user = User.objects.create_user(username="tm_user", password="password")
    UserSecurity.objects.create(user=tm_user, role='Team Member')
    
    request = factory.post(f'/manage-task/{phase.pk}/', {
        'title': 'Self Task',
        'description': 'Description',
        'owner': tm_user.id,
        'priority': 'Medium',
        'due_date': '2026-12-31'
    })
    request.user = tm_user
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    
    manage_task(request, phase.pk)
    
    new_task = ProjectTask.objects.filter(title='Self Task').first()
    if new_task:
        print(f"Task Created: {new_task.title}, Self-assigned: {new_task.self_assigned}, Assigned By: {new_task.assigned_by}")
        if new_task.self_assigned == True and new_task.assigned_by == tm_user:
            print("SUCCESS: Task correctly marked as self-assigned.")
        else:
            print("FAILED: Task fields not correctly populated.")
    else:
        print("FAILED: Task not created.")

    # 3. Verify Executive Dashboard Access
    print("\nTesting Dashboard Access...")
    hod_user = User.objects.create_user(username="hod_user", password="password")
    UserSecurity.objects.get_or_create(user=hod_user, defaults={'role': 'HOD'})
    
    request = factory.get('/executive-governance/')
    request.user = hod_user
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    
    response = executive_governance(request)
    if response.status_code == 200:
        print("SUCCESS: HOD can access executive dashboard.")
    else:
        print(f"FAILED: HOD denied access to dashboard (status {response.status_code}).")

    # Cleanup
    project.delete()
    tm_user.delete()
    hod_user.delete()
    print("\n--- Verification COMPLETED ---")

if __name__ == "__main__":
    verify_fixes()
