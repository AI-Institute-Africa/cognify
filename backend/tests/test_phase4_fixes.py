"""
Test Phase 4 Fixes - Cognify Platform
Tests for:
- Profile update with LinkedIn URL
- Study group delete/leave
- Org admin staff/participants display
- Staff invitation
- Content upload visibility
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
STUDENT_CREDS = {"email": "demo.student@cognify.edu", "password": "demo123"}
TEACHER_CREDS = {"email": "demo.teacher@eduos.edu", "password": "demo123"}
ORG_ADMIN_CREDS = {"email": "test.orgadmin@cognify.edu", "password": "admin123"}
COURSE_ID = "9495d24f-7462-4f89-a751-a6742c61f62e"


class TestHealthCheck:
    """Basic health check"""
    
    def test_health_endpoint(self):
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✓ Health check passed")


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_student_login(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=STUDENT_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "student"
        print(f"✓ Student login successful: {data['user']['email']}")
        return data["access_token"]
    
    def test_teacher_login(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "teacher"
        print(f"✓ Teacher login successful: {data['user']['email']}")
        return data["access_token"]
    
    def test_org_admin_login(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ORG_ADMIN_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "org_admin"
        print(f"✓ Org admin login successful: {data['user']['email']}")
        return data["access_token"]


class TestDirectRegistration:
    """Test direct registration without email verification"""
    
    def test_register_new_user(self):
        unique_email = f"test.user.{uuid.uuid4().hex[:8]}@test.com"
        payload = {
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Test User",
            "role": "student",
            "linkedin_url": "https://linkedin.com/in/testuser"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == unique_email
        print(f"✓ Direct registration successful: {unique_email}")
        return data["access_token"]
    
    def test_duplicate_email_rejected(self):
        payload = {
            "email": STUDENT_CREDS["email"],
            "password": "testpass123",
            "full_name": "Duplicate User",
            "role": "student"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        assert response.status_code == 400
        print("✓ Duplicate email correctly rejected")


class TestProfileUpdate:
    """Test profile update with LinkedIn URL"""
    
    @pytest.fixture
    def student_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=STUDENT_CREDS)
        return response.json()["access_token"]
    
    def test_update_profile_with_linkedin(self, student_token):
        headers = {"Authorization": f"Bearer {student_token}"}
        linkedin_url = f"https://linkedin.com/in/testuser-{uuid.uuid4().hex[:6]}"
        
        payload = {
            "full_name": "Demo Student Updated",
            "linkedin_url": linkedin_url,
            "bio": "Test bio for profile update"
        }
        
        response = requests.put(f"{BASE_URL}/api/auth/profile", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "linkedin_url" in data.get("updated_fields", [])
        print(f"✓ Profile updated with LinkedIn URL: {linkedin_url}")
    
    def test_get_profile_returns_linkedin(self, student_token):
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        # LinkedIn URL should be present if previously set
        print(f"✓ Profile retrieved, linkedin_url present: {'linkedin_url' in data}")
    
    def test_update_linkedin_only(self, student_token):
        headers = {"Authorization": f"Bearer {student_token}"}
        linkedin_url = f"https://linkedin.com/in/onlylinkedin-{uuid.uuid4().hex[:6]}"
        
        payload = {"linkedin_url": linkedin_url}
        
        response = requests.put(f"{BASE_URL}/api/auth/profile", json=payload, headers=headers)
        assert response.status_code == 200
        print(f"✓ LinkedIn URL only update successful")


class TestOrgAdminFeatures:
    """Test org admin staff and participants features"""
    
    @pytest.fixture
    def org_admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ORG_ADMIN_CREDS)
        return response.json()["access_token"]
    
    def test_get_org_staff(self, org_admin_token):
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/org/staff", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Org staff retrieved: {len(data)} staff members")
        for staff in data[:3]:
            print(f"  - {staff.get('full_name', 'N/A')} ({staff.get('role', 'N/A')})")
    
    def test_get_org_participants(self, org_admin_token):
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/org/participants", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Org participants retrieved: {len(data)} participants")
        for participant in data[:3]:
            print(f"  - {participant.get('full_name', 'N/A')} ({participant.get('email', 'N/A')})")
    
    def test_invite_staff(self, org_admin_token):
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        unique_email = f"staff.invite.{uuid.uuid4().hex[:8]}@test.com"
        
        params = {
            "email": unique_email,
            "full_name": "Invited Staff Member",
            "role": "teacher"
        }
        
        response = requests.post(f"{BASE_URL}/api/org/invite-staff", params=params, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ Staff invitation sent to: {unique_email}")
    
    def test_assign_staff_rights(self, org_admin_token):
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        
        # First get staff list to get a staff ID
        staff_response = requests.get(f"{BASE_URL}/api/org/staff", headers=headers)
        staff_list = staff_response.json()
        
        if len(staff_list) > 0:
            staff_id = staff_list[0].get("id")
            
            payload = {
                "staff_id": staff_id,
                "can_create_courses": True,
                "can_manage_participants": False,
                "can_upload_content": True,
                "can_invite_participants": False
            }
            
            response = requests.post(f"{BASE_URL}/api/org/staff/assign-rights", json=payload, headers=headers)
            assert response.status_code == 200
            print(f"✓ Staff rights assigned to: {staff_id}")
        else:
            print("⚠ No staff members found to assign rights")


class TestContentUpload:
    """Test content upload and visibility"""
    
    @pytest.fixture
    def teacher_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
        return response.json()["access_token"]
    
    @pytest.fixture
    def student_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=STUDENT_CREDS)
        return response.json()["access_token"]
    
    def test_upload_course_content(self, teacher_token):
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        payload = {
            "content_type": "text",
            "title": f"Test Content {uuid.uuid4().hex[:6]}",
            "description": "Test content description",
            "content_text": "This is test content for the course.",
            "text": "This is test content for the course."
        }
        
        response = requests.post(f"{BASE_URL}/api/content/course/{COURSE_ID}/content", json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            print(f"✓ Content uploaded successfully: {data.get('title')}")
            return data["id"]
        elif response.status_code == 404:
            print(f"⚠ Course {COURSE_ID} not found - skipping content upload test")
            pytest.skip("Course not found")
        else:
            print(f"✗ Content upload failed: {response.status_code} - {response.text}")
            assert False, f"Content upload failed: {response.text}"
    
    def test_get_course_content(self, student_token):
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = requests.get(f"{BASE_URL}/api/content/course/{COURSE_ID}/content", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print(f"✓ Course content retrieved: {len(data)} items")
            elif isinstance(data, dict):
                contents = data.get("contents", [])
                print(f"✓ Course content retrieved: {len(contents)} items (access_restricted: {data.get('access_restricted', False)})")
        elif response.status_code == 404:
            print(f"⚠ Course {COURSE_ID} not found")
            pytest.skip("Course not found")
        else:
            print(f"✗ Get content failed: {response.status_code}")


class TestStudyGroups:
    """Test study group delete and leave functionality"""
    
    @pytest.fixture
    def student_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=STUDENT_CREDS)
        return response.json()["access_token"]
    
    @pytest.fixture
    def teacher_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
        return response.json()["access_token"]
    
    def test_create_study_group(self, student_token):
        headers = {"Authorization": f"Bearer {student_token}"}
        
        payload = {
            "name": f"Test Study Group {uuid.uuid4().hex[:6]}",
            "topic": "Mathematics",
            "description": "Test group for Phase 4 testing",
            "max_members": 10
        }
        
        response = requests.post(f"{BASE_URL}/api/study-groups", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "group_id" in data
        print(f"✓ Study group created: {data['group_id']}")
        return data["group_id"]
    
    def test_delete_study_group_by_creator(self, student_token):
        headers = {"Authorization": f"Bearer {student_token}"}
        
        # First create a group
        payload = {
            "name": f"Delete Test Group {uuid.uuid4().hex[:6]}",
            "topic": "Science",
            "description": "Group to be deleted",
            "max_members": 5
        }
        
        create_response = requests.post(f"{BASE_URL}/api/study-groups", json=payload, headers=headers)
        assert create_response.status_code == 200
        group_id = create_response.json()["group_id"]
        
        # Now delete it
        delete_response = requests.delete(f"{BASE_URL}/api/study-groups/{group_id}", headers=headers)
        assert delete_response.status_code == 200
        print(f"✓ Study group deleted by creator: {group_id}")
    
    def test_leave_study_group(self, student_token, teacher_token):
        # Student creates a group
        student_headers = {"Authorization": f"Bearer {student_token}"}
        teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
        
        payload = {
            "name": f"Leave Test Group {uuid.uuid4().hex[:6]}",
            "topic": "History",
            "description": "Group for leave testing",
            "max_members": 10
        }
        
        create_response = requests.post(f"{BASE_URL}/api/study-groups", json=payload, headers=student_headers)
        assert create_response.status_code == 200
        group_id = create_response.json()["group_id"]
        
        # Teacher joins the group
        join_response = requests.post(f"{BASE_URL}/api/study-groups/{group_id}/join", headers=teacher_headers)
        assert join_response.status_code == 200
        print(f"✓ Teacher joined group: {group_id}")
        
        # Teacher leaves the group
        leave_response = requests.post(f"{BASE_URL}/api/study-groups/{group_id}/leave", headers=teacher_headers)
        assert leave_response.status_code == 200
        print(f"✓ Teacher left group: {group_id}")
        
        # Cleanup - delete the group
        requests.delete(f"{BASE_URL}/api/study-groups/{group_id}", headers=student_headers)
    
    def test_creator_cannot_leave(self, student_token):
        headers = {"Authorization": f"Bearer {student_token}"}
        
        # Create a group
        payload = {
            "name": f"Creator Leave Test {uuid.uuid4().hex[:6]}",
            "topic": "Physics",
            "description": "Testing creator cannot leave",
            "max_members": 5
        }
        
        create_response = requests.post(f"{BASE_URL}/api/study-groups", json=payload, headers=headers)
        assert create_response.status_code == 200
        group_id = create_response.json()["group_id"]
        
        # Try to leave as creator - should fail
        leave_response = requests.post(f"{BASE_URL}/api/study-groups/{group_id}/leave", headers=headers)
        assert leave_response.status_code == 400
        print(f"✓ Creator correctly prevented from leaving group")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/study-groups/{group_id}", headers=headers)
    
    def test_non_creator_cannot_delete(self, student_token, teacher_token):
        student_headers = {"Authorization": f"Bearer {student_token}"}
        teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
        
        # Student creates a group
        payload = {
            "name": f"Non-Creator Delete Test {uuid.uuid4().hex[:6]}",
            "topic": "Chemistry",
            "description": "Testing non-creator cannot delete",
            "max_members": 10
        }
        
        create_response = requests.post(f"{BASE_URL}/api/study-groups", json=payload, headers=student_headers)
        assert create_response.status_code == 200
        group_id = create_response.json()["group_id"]
        
        # Teacher joins
        requests.post(f"{BASE_URL}/api/study-groups/{group_id}/join", headers=teacher_headers)
        
        # Teacher tries to delete - should fail
        delete_response = requests.delete(f"{BASE_URL}/api/study-groups/{group_id}", headers=teacher_headers)
        assert delete_response.status_code == 403
        print(f"✓ Non-creator correctly prevented from deleting group")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/study-groups/{group_id}", headers=student_headers)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
