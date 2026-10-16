import os
import sys
import django

# Add workspace directory to path
sys.path.append(r"c:\Users\USER 2\Desktop\nbsz (4)\aiiagov\project1\project1\land_registry")

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'land_registry.settings')
django.setup()

from django.contrib.auth.models import User
from registry import models
from django.test import RequestFactory
from registry.views import cloud_create_folder, cloud_delete_folder, cloud_download_folder
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.storage.fallback import FallbackStorage
from django.urls import reverse

def run_test():
    print("Starting folder permissions system test...")

    # Create users
    superuser, _ = User.objects.get_or_create(username="test_super", is_superuser=True, is_staff=True)
    regular_user, _ = User.objects.get_or_create(username="test_regular", is_superuser=False, is_staff=False)
    
    # Test 1: Superuser bypass
    print("Checking superuser bypass...")
    assert models.InstitutionalFolderPermission.user_can(superuser, 'can_create_folder') is True
    assert models.InstitutionalFolderPermission.user_can(superuser, 'can_delete_folder') is True
    assert models.InstitutionalFolderPermission.user_can(superuser, 'can_download_folder') is True
    assert models.InstitutionalFolderPermission.user_can(superuser, 'can_view_all_folders') is True

    # Test 2: Regular user default (no permission object)
    print("Checking regular user default (no permissions record)...")
    if hasattr(regular_user, 'folder_permission'):
        regular_user.folder_permission.delete()
    regular_user.refresh_from_db()
    assert models.InstitutionalFolderPermission.user_can(regular_user, 'can_create_folder') is False
    assert models.InstitutionalFolderPermission.user_can(regular_user, 'can_delete_folder') is False
    assert models.InstitutionalFolderPermission.user_can(regular_user, 'can_download_folder') is False
    assert models.InstitutionalFolderPermission.user_can(regular_user, 'can_view_all_folders') is False

    # Test 3: Grant permissions
    print("Granting specific permission to regular user...")
    perm = models.InstitutionalFolderPermission.objects.create(
        user=regular_user,
        can_create_folder=True,
        can_delete_folder=False,
        can_download_folder=True,
        can_view_all_folders=True
    )
    assert models.InstitutionalFolderPermission.user_can(regular_user, 'can_create_folder') is True
    assert models.InstitutionalFolderPermission.user_can(regular_user, 'can_delete_folder') is False
    assert models.InstitutionalFolderPermission.user_can(regular_user, 'can_download_folder') is True
    assert models.InstitutionalFolderPermission.user_can(regular_user, 'can_view_all_folders') is True

    # Test 4: View level permission enforcement
    print("Checking view guards...")
    factory = RequestFactory()

    # Prepare mock request helpers
    def prepare_request(request, user):
        request.user = user
        middleware = SessionMiddleware(lambda r: None)
        middleware.process_request(request)
        request.session.save()
        request._messages = FallbackStorage(request)

    # 4a: Create folder with regular user who has can_create_folder=True
    dept, _ = models.Department.objects.get_or_create(name="Test Dept")
    request = factory.post('/cloud/create-folder/', {
        'name': 'Allowed Folder',
        'department_id': dept.pk
    })
    prepare_request(request, regular_user)
    response = cloud_create_folder(request)
    print(f"  Create folder (Authorized): response status {response.status_code}")
    # Should redirect with success message (or at least not error page)
    assert response.status_code == 302
    assert models.CloudFolder.objects.filter(name='Allowed Folder').exists()

    # 4b: Delete folder with regular user who has can_delete_folder=False
    folder = models.CloudFolder.objects.get(name='Allowed Folder')
    request = factory.post(f'/cloud/delete-folder/{folder.pk}/')
    prepare_request(request, regular_user)
    response = cloud_delete_folder(request, folder.pk)
    print(f"  Delete folder (Unauthorized): response status {response.status_code}")
    # Folder should still exist (not marked is_deleted)
    folder.refresh_from_db()
    assert folder.is_deleted is False

    # 4c: Delete folder with superuser (Authorized)
    request = factory.post(f'/cloud/delete-folder/{folder.pk}/')
    prepare_request(request, superuser)
    response = cloud_delete_folder(request, folder.pk)
    print(f"  Delete folder (Superuser): response status {response.status_code}")
    folder.refresh_from_db()
    assert folder.is_deleted is True

    # Cleanup test records
    perm.delete()
    folder.delete()
    regular_user.delete()
    superuser.delete()

    print("SUCCESS: Folder permissions verified perfectly!")

if __name__ == '__main__':
    run_test()
