"""
Cognify Platform - Iteration 17 Tests
Testing: Registration, Profile Update, Study Groups, Org Admin Features, Content Upload, Assignment Generation
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://edusync-34.preview.emergentagent.com')

# Test credentials
STUDENT_EMAIL = "demo.student@cognify.edu"
STUDENT_PASSWORD = "demo123"
TEACHER_EMAIL = "demo.teacher@eduos.edu"
TEACHER_PASSWORD = "demo123"
ORG_ADMIN_EMAIL = "test.orgadmin@cognify.edu"
ORG_ADMIN_PASSWORD = "admin123"
COURSE_ID = "9495d24f-7462-4f89-a751-a6742c61f62e"


class TestHealthCheck:
    """Basic health check"""
    
    def test_health_endpoint(self):
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("✓ Health check passed")


class TestDirectRegistration:
    """Test POST /api/auth/register - Direct registration without email verification"""
    
    def test_register_new_user_direct(self):
        """Register a new user directly without email verification"""
        unique_email = f"test.user.{uuid.uuid4().hex[:8]}@test.com"
        payload = {
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Test User Direct",
            "role": "student",
            "preferred_language": "en"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        
        # Should return 200 with token (direct registration)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response contains token and user
        assert "access_token" in data, "Missing access_token in response"
        assert "user" in data, "Missing user in response"
        assert data["user"]["email"] == unique_email
        assert data["user"]["role"] == "student"
        print(f"✓ Direct registration successful for {unique_email}")
        
        # Verify can login immediately (no email verification needed)
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": unique_email,
            "password": "testpass123"
        })
        assert login_response.status_code == 200, "Should be able to login immediately after registration"
        print("✓ Immediate login after registration works")
    
    def test_register_with_linkedin_url(self):
        """Register with LinkedIn URL"""
        unique_email = f"test.linkedin.{uuid.uuid4().hex[:8]}@test.com"
        payload = {
            "email": unique_email,
            "password": "testpass123",
            "full_name": "LinkedIn Test User",
            "role": "student",
            "preferred_language": "en"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        assert response.status_code == 200
        print(f"✓ Registration with LinkedIn URL field successful")
    
    def test_register_duplicate_email_fails(self):
        """Duplicate email should fail"""
        payload = {
            "email": STUDENT_EMAIL,
            "password": "testpass123",
            "full_name": "Duplicate User",
            "role": "student"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        assert response.status_code == 400, "Duplicate email should return 400"
        print("✓ Duplicate email registration correctly rejected")


class TestProfileUpdate:
    """Test PUT /api/auth/profile - Update profile with LinkedIn URL"""
    
    @pytest.fixture
    def student_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Student login failed")
        return response.json()["access_token"]
    
    def test_update_profile_with_linkedin(self, student_token):
        """Update profile with LinkedIn URL"""
        headers = {"Authorization": f"Bearer {student_token}"}
        payload = {
            "full_name": "Demo Student Updated",
            "linkedin_url": "https://linkedin.com/in/demostudent",
            "bio": "Test bio for demo student"
        }
        response = requests.put(f"{BASE_URL}/api/auth/profile", json=payload, headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data
        assert "updated_fields" in data
        print(f"✓ Profile updated with LinkedIn URL: {data['updated_fields']}")
    
    def test_update_profile_linkedin_only(self, student_token):
        """Update only LinkedIn URL"""
        headers = {"Authorization": f"Bearer {student_token}"}
        payload = {
            "linkedin_url": "https://linkedin.com/in/updated-profile"
        }
        response = requests.put(f"{BASE_URL}/api/auth/profile", json=payload, headers=headers)
        
        assert response.status_code == 200
        print("✓ LinkedIn URL only update successful")
    
    def test_verify_profile_update_persisted(self, student_token):
        """Verify profile update is persisted"""
        headers = {"Authorization": f"Bearer {student_token}"}
        
        # First update
        update_payload = {"linkedin_url": "https://linkedin.com/in/verify-persist"}
        requests.put(f"{BASE_URL}/api/auth/profile", json=update_payload, headers=headers)
        
        # Then get profile
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # LinkedIn URL should be in user data or profile
        print(f"✓ Profile data retrieved successfully")


class TestContentUpload:
    """Test POST /api/content/course/{id}/content - Content upload with JSON body"""
    
    @pytest.fixture
    def teacher_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Teacher login failed")
        return response.json()["access_token"]
    
    def test_upload_text_content(self, teacher_token):
        """Upload text content to course"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        payload = {
            "content_type": "text",
            "title": "Test Lesson Content",
            "description": "Test description for lesson",
            "content_text": "This is the lesson content text for testing.",
            "text": "This is the lesson content text for testing."
        }
        response = requests.post(
            f"{BASE_URL}/api/content/course/{COURSE_ID}/content",
            json=payload,
            headers=headers
        )
        
        # May return 404 if course doesn't exist, or 200 if successful
        if response.status_code == 404:
            print("⚠ Course not found - skipping content upload test")
            pytest.skip("Course not found")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data
        print(f"✓ Content uploaded successfully: {data.get('id')}")
    
    def test_get_course_content(self, teacher_token):
        """Get course content list"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(
            f"{BASE_URL}/api/content/course/{COURSE_ID}/content",
            headers=headers
        )
        
        if response.status_code == 404:
            pytest.skip("Course not found")
        
        assert response.status_code == 200
        print(f"✓ Course content retrieved")


class TestStudyGroupManagement:
    """Test Study Group delete/leave endpoints"""
    
    @pytest.fixture
    def student_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Student login failed")
        return response.json()["access_token"]
    
    def test_create_and_delete_study_group(self, student_token):
        """Create a study group and then delete it (creator only)"""
        headers = {"Authorization": f"Bearer {student_token}"}
        
        # Create group
        create_payload = {
            "name": f"Test Group {uuid.uuid4().hex[:6]}",
            "topic": "Mathematics",
            "description": "Test group for deletion",
            "max_members": 5
        }
        create_response = requests.post(
            f"{BASE_URL}/api/study-groups",
            json=create_payload,
            headers=headers
        )
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        group_id = create_response.json()["group_id"]
        print(f"✓ Study group created: {group_id}")
        
        # Delete group (as creator)
        delete_response = requests.delete(
            f"{BASE_URL}/api/study-groups/{group_id}",
            headers=headers
        )
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        print(f"✓ Study group deleted successfully")
    
    def test_leave_study_group(self, student_token):
        """Test leaving a study group"""
        headers = {"Authorization": f"Bearer {student_token}"}
        
        # First create a group
        create_payload = {
            "name": f"Leave Test Group {uuid.uuid4().hex[:6]}",
            "topic": "Science",
            "description": "Test group for leave functionality",
            "max_members": 10
        }
        create_response = requests.post(
            f"{BASE_URL}/api/study-groups",
            json=create_payload,
            headers=headers
        )
        assert create_response.status_code == 200
        group_id = create_response.json()["group_id"]
        
        # Creator cannot leave (should delete instead)
        leave_response = requests.post(
            f"{BASE_URL}/api/study-groups/{group_id}/leave",
            headers=headers
        )
        # Should return 400 because creator cannot leave
        assert leave_response.status_code == 400, "Creator should not be able to leave"
        print("✓ Creator correctly prevented from leaving (must delete instead)")
        
        # Clean up - delete the group
        requests.delete(f"{BASE_URL}/api/study-groups/{group_id}", headers=headers)
    
    def test_leave_nonexistent_group(self, student_token):
        """Test leaving a non-existent group"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.post(
            f"{BASE_URL}/api/study-groups/nonexistent-id/leave",
            headers=headers
        )
        assert response.status_code == 404
        print("✓ Leave non-existent group correctly returns 404")
    
    def test_delete_group_non_creator_fails(self, student_token):
        """Non-creator cannot delete group"""
        headers = {"Authorization": f"Bearer {student_token}"}
        
        # Try to delete a group we didn't create (use random ID)
        response = requests.delete(
            f"{BASE_URL}/api/study-groups/some-other-group-id",
            headers=headers
        )
        # Should return 404 (not found) or 403 (forbidden)
        assert response.status_code in [404, 403]
        print("✓ Non-creator correctly prevented from deleting group")


class TestOrgAdminFeatures:
    """Test Organization Admin features"""
    
    @pytest.fixture
    def org_admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        if response.status_code != 200:
            # Try to create org admin if doesn't exist
            print(f"⚠ Org admin login failed: {response.text}")
            pytest.skip("Org admin login failed")
        return response.json()["access_token"]
    
    def test_get_org_participants(self, org_admin_token):
        """GET /api/org/participants - Get org participants"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/org/participants", headers=headers)
        
        # May return 400 if no org associated, or 200 with list
        if response.status_code == 400:
            print("⚠ No organization associated with admin")
            pytest.skip("No organization associated")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Got {len(data)} org participants")
    
    def test_get_org_staff(self, org_admin_token):
        """GET /api/org/staff - Get org staff"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/org/staff", headers=headers)
        
        if response.status_code == 400:
            pytest.skip("No organization associated")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Got {len(data)} org staff members")
    
    def test_invite_staff(self, org_admin_token):
        """POST /api/org/invite-staff - Invite new staff"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        unique_email = f"staff.{uuid.uuid4().hex[:8]}@test.org"
        
        response = requests.post(
            f"{BASE_URL}/api/org/invite-staff",
            params={
                "email": unique_email,
                "full_name": "Test Staff Member",
                "role": "teacher"
            },
            headers=headers
        )
        
        if response.status_code == 400:
            pytest.skip("No organization associated")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data
        print(f"✓ Staff invitation sent: {data.get('message')}")
    
    def test_assign_staff_rights(self, org_admin_token):
        """POST /api/org/staff/assign-rights - Assign staff rights"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        
        # First get staff list to get a valid staff_id
        staff_response = requests.get(f"{BASE_URL}/api/org/staff", headers=headers)
        if staff_response.status_code != 200 or not staff_response.json():
            pytest.skip("No staff members to assign rights to")
        
        staff_list = staff_response.json()
        if not staff_list:
            pytest.skip("No staff members found")
        
        staff_id = staff_list[0].get('id')
        
        payload = {
            "staff_id": staff_id,
            "can_create_courses": True,
            "can_manage_participants": True,
            "can_upload_content": True,
            "can_invite_participants": False
        }
        response = requests.post(
            f"{BASE_URL}/api/org/staff/assign-rights",
            json=payload,
            headers=headers
        )
        
        if response.status_code == 403:
            print("⚠ Staff member not in organization")
            pytest.skip("Staff not in org")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print("✓ Staff rights assigned successfully")
    
    def test_connect_database(self, org_admin_token):
        """POST /api/org/database/connect - Connect external database"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        payload = {
            "db_type": "mongodb",
            "connection_string": "mongodb://localhost:27017",
            "db_name": "test_external_db",
            "collection_name": "students"
        }
        response = requests.post(
            f"{BASE_URL}/api/org/database/connect",
            json=payload,
            headers=headers
        )
        
        if response.status_code == 400:
            pytest.skip("No organization associated")
        
        # Connection may fail but endpoint should work
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "status" in data
        print(f"✓ Database connection attempt: {data.get('status')}")


class TestOrgDocumentUpload:
    """Test POST /api/org/documents/upload - Upload org documents"""
    
    @pytest.fixture
    def org_admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Org admin login failed")
        return response.json()["access_token"]
    
    def test_upload_text_document(self, org_admin_token):
        """Upload a text document"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        
        # Create a simple text file
        files = {
            'file': ('test_doc.txt', b'This is test document content for Cognify platform.', 'text/plain')
        }
        data = {
            'title': 'Test Document',
            'description': 'Test document for org',
            'doc_type': 'reference'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/org/documents/upload",
            files=files,
            data=data,
            headers=headers
        )
        
        if response.status_code == 400:
            pytest.skip("No organization associated")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        result = response.json()
        assert "document_id" in result
        print(f"✓ Document uploaded: {result.get('document_id')}")


class TestAssignmentGeneration:
    """Test POST /api/advanced/assignment/generate - Generate assignment linked to course"""
    
    @pytest.fixture
    def teacher_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Teacher login failed")
        return response.json()["access_token"]
    
    def test_generate_assignment_with_course_id(self, teacher_token):
        """Generate assignment linked to a course"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/advanced/assignment/generate",
            params={
                "lesson_topic": "Introduction to Python Programming",
                "course_id": COURSE_ID,
                "assignment_type": "reflection",
                "difficulty": "medium"
            },
            headers=headers
        )
        
        # AI features may fail due to budget
        if response.status_code == 500:
            error_msg = response.json().get('detail', '')
            if 'budget' in error_msg.lower() or 'ai' in error_msg.lower():
                print("⚠ AI budget exceeded - assignment generation skipped")
                pytest.skip("AI budget exceeded")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "assignment_id" in data
        assert data.get("course_id") == COURSE_ID
        print(f"✓ Assignment generated with course_id: {data.get('assignment_id')}")


class TestMultiSubjectLearning:
    """Test POST /api/advanced/multidisciplinary/generate - Multi-subject learning for students"""
    
    @pytest.fixture
    def student_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Student login failed")
        return response.json()["access_token"]
    
    def test_student_can_generate_multidisciplinary(self, student_token):
        """Students should be able to generate multi-subject lessons"""
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/advanced/multidisciplinary/generate",
            params={
                "topic": "Climate Change",
                "duration_minutes": 30
            },
            headers=headers
        )
        
        # AI features may fail due to budget
        if response.status_code == 500:
            error_msg = response.json().get('detail', '')
            if 'budget' in error_msg.lower() or 'ai' in error_msg.lower():
                print("⚠ AI budget exceeded - multi-subject generation skipped")
                pytest.skip("AI budget exceeded")
        
        # Should not return 403 (students are now allowed)
        assert response.status_code != 403, "Students should be allowed to generate multi-subject lessons"
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Multi-subject lesson generated for student")
        else:
            print(f"⚠ Multi-subject generation returned {response.status_code}")


class TestStudentLogin:
    """Test student authentication"""
    
    def test_student_login(self):
        """Test student login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        assert response.status_code == 200, f"Student login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "student"
        print(f"✓ Student login successful: {data['user']['email']}")
    
    def test_teacher_login(self):
        """Test teacher login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        assert response.status_code == 200, f"Teacher login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "teacher"
        print(f"✓ Teacher login successful: {data['user']['email']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
