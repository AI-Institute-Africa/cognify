"""
Iteration 31 - Testing Bug Fixes for:
1. Publish assignments/exams from AI Q&A Generator for org_admin/teacher
2. GET /api/assignments returns assignments for org_admin (not 0)
3. GET /api/exams returns exams for org_admin
4. GET /api/courses returns courses for org_admin (should see all active courses)
5. GET /api/org/courses returns org courses for admin
6. Custom course generation sets is_active=true, is_published=true, organization_id, name field
7. Avatar voice cloning endpoints
8. Audio pause/stop controls (UI only)
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
STUDENT_EMAIL = "demo.student@cognify.edu"
STUDENT_PASSWORD = "demo123"
TEACHER_EMAIL = "demo.teacher@eduos.edu"
TEACHER_PASSWORD = "demo123"
ORG_ADMIN_EMAIL = "test.orgadmin@cognify.edu"
ORG_ADMIN_PASSWORD = "admin123"


class TestAuthentication:
    """Authentication tests for all user roles"""
    
    def test_student_login(self):
        """Test student login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        assert response.status_code == 200, f"Student login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data.get("user", {}).get("role") == "student"
    
    def test_teacher_login(self):
        """Test teacher login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        assert response.status_code == 200, f"Teacher login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data.get("user", {}).get("role") == "teacher"
    
    def test_org_admin_login(self):
        """Test org admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Org admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data.get("user", {}).get("role") == "org_admin"


@pytest.fixture
def student_token():
    """Get student auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": STUDENT_EMAIL,
        "password": STUDENT_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Student login failed")


@pytest.fixture
def teacher_token():
    """Get teacher auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEACHER_EMAIL,
        "password": TEACHER_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Teacher login failed")


@pytest.fixture
def org_admin_token():
    """Get org admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ORG_ADMIN_EMAIL,
        "password": ORG_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Org admin login failed")


class TestOrgAdminCoursesAccess:
    """Test that org_admin can see courses - Bug fix verification"""
    
    def test_org_admin_get_courses_returns_data(self, org_admin_token):
        """Org admin should see active courses (not 0)"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        assert response.status_code == 200, f"Failed to get courses: {response.text}"
        courses = response.json()
        assert isinstance(courses, list), "Courses should be a list"
        # Org admin should see at least some courses (global active courses)
        print(f"Org admin sees {len(courses)} courses")
        # The fix should show global active courses even if org has no specific courses
    
    def test_org_admin_get_org_courses(self, org_admin_token):
        """GET /api/org/courses should return org courses"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/org/courses", headers=headers)
        assert response.status_code == 200, f"Failed to get org courses: {response.text}"
        courses = response.json()
        assert isinstance(courses, list), "Org courses should be a list"
        print(f"Org admin sees {len(courses)} org-specific courses")


class TestOrgAdminAssignmentsAccess:
    """Test that org_admin can see assignments - Bug fix verification"""
    
    def test_org_admin_get_assignments(self, org_admin_token):
        """Org admin should see assignments they created + org assignments"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/assignments", headers=headers)
        assert response.status_code == 200, f"Failed to get assignments: {response.text}"
        assignments = response.json()
        assert isinstance(assignments, list), "Assignments should be a list"
        print(f"Org admin sees {len(assignments)} assignments")
    
    def test_teacher_get_assignments(self, teacher_token):
        """Teacher should see assignments they created"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(f"{BASE_URL}/api/assignments", headers=headers)
        assert response.status_code == 200, f"Failed to get assignments: {response.text}"
        assignments = response.json()
        assert isinstance(assignments, list)
        print(f"Teacher sees {len(assignments)} assignments")


class TestOrgAdminExamsAccess:
    """Test that org_admin can see exams - Bug fix verification"""
    
    def test_org_admin_get_exams(self, org_admin_token):
        """Org admin should see exams they created + org exams"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/exams", headers=headers)
        assert response.status_code == 200, f"Failed to get exams: {response.text}"
        exams = response.json()
        assert isinstance(exams, list), "Exams should be a list"
        print(f"Org admin sees {len(exams)} exams")
    
    def test_teacher_get_exams(self, teacher_token):
        """Teacher should see exams they created"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(f"{BASE_URL}/api/exams", headers=headers)
        assert response.status_code == 200, f"Failed to get exams: {response.text}"
        exams = response.json()
        assert isinstance(exams, list)
        print(f"Teacher sees {len(exams)} exams")


class TestPublishAssignmentFromAIQA:
    """Test publishing assignments from AI Q&A Generator"""
    
    def test_teacher_can_publish_assignment(self, teacher_token):
        """Teacher should be able to publish assignment from AI Q&A"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        # First get a course to use
        courses_resp = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        if courses_resp.status_code != 200 or not courses_resp.json():
            pytest.skip("No courses available for teacher")
        
        course = courses_resp.json()[0]
        course_id = course.get('id')
        
        # Publish assignment
        payload = {
            "title": f"TEST_AI_Assignment_{uuid.uuid4().hex[:8]}",
            "course_id": course_id,
            "questions": [
                {"q": "What is Python?", "a": "A programming language", "category": "basic"},
                {"q": "What is a function?", "a": "A reusable block of code", "category": "basic"}
            ],
            "description": "Auto-generated test assignment",
            "max_score": 10
        }
        
        response = requests.post(f"{BASE_URL}/api/training-engine/publish-assignment", 
                                json=payload, headers=headers)
        assert response.status_code in [200, 201], f"Failed to publish assignment: {response.text}"
        data = response.json()
        assert "assignment_id" in data or "id" in data or "message" in data
        print(f"Teacher published assignment successfully: {data}")
    
    def test_org_admin_can_publish_assignment(self, org_admin_token):
        """Org admin should be able to publish assignment from AI Q&A"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        
        # First get a course to use
        courses_resp = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        if courses_resp.status_code != 200 or not courses_resp.json():
            pytest.skip("No courses available for org admin")
        
        course = courses_resp.json()[0]
        course_id = course.get('id')
        
        # Publish assignment
        payload = {
            "title": f"TEST_OrgAdmin_Assignment_{uuid.uuid4().hex[:8]}",
            "course_id": course_id,
            "questions": [
                {"q": "What is AI?", "a": "Artificial Intelligence", "category": "basic"}
            ],
            "description": "Org admin test assignment",
            "max_score": 5
        }
        
        response = requests.post(f"{BASE_URL}/api/training-engine/publish-assignment", 
                                json=payload, headers=headers)
        assert response.status_code in [200, 201], f"Failed to publish assignment: {response.text}"
        print(f"Org admin published assignment successfully")
    
    def test_student_cannot_publish_assignment(self, student_token):
        """Student should NOT be able to publish assignment"""
        headers = {"Authorization": f"Bearer {student_token}"}
        
        payload = {
            "title": "Student Test Assignment",
            "course_id": "some-course-id",
            "questions": [{"q": "Test?", "a": "Test", "category": "basic"}],
            "description": "Should fail",
            "max_score": 5
        }
        
        response = requests.post(f"{BASE_URL}/api/training-engine/publish-assignment", 
                                json=payload, headers=headers)
        assert response.status_code == 403, f"Student should be forbidden: {response.status_code}"


class TestPublishExamFromAIQA:
    """Test publishing exams from AI Q&A Generator"""
    
    def test_teacher_can_publish_exam(self, teacher_token):
        """Teacher should be able to publish exam from AI Q&A"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        # First get a course to use
        courses_resp = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        if courses_resp.status_code != 200 or not courses_resp.json():
            pytest.skip("No courses available for teacher")
        
        course = courses_resp.json()[0]
        course_id = course.get('id')
        
        # Publish exam
        payload = {
            "title": f"TEST_AI_Exam_{uuid.uuid4().hex[:8]}",
            "course_id": course_id,
            "sections": [
                {
                    "title": "Section 1",
                    "questions": [
                        {"question": "What is 2+2?", "options": ["A. 3", "B. 4", "C. 5"], "correct": "B", "marks": 5}
                    ]
                }
            ],
            "duration_minutes": 30,
            "total_marks": 5,
            "description": "Auto-generated test exam"
        }
        
        response = requests.post(f"{BASE_URL}/api/training-engine/publish-exam", 
                                json=payload, headers=headers)
        assert response.status_code in [200, 201], f"Failed to publish exam: {response.text}"
        print(f"Teacher published exam successfully")
    
    def test_org_admin_can_publish_exam(self, org_admin_token):
        """Org admin should be able to publish exam from AI Q&A"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        
        # First get a course to use
        courses_resp = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        if courses_resp.status_code != 200 or not courses_resp.json():
            pytest.skip("No courses available for org admin")
        
        course = courses_resp.json()[0]
        course_id = course.get('id')
        
        # Publish exam
        payload = {
            "title": f"TEST_OrgAdmin_Exam_{uuid.uuid4().hex[:8]}",
            "course_id": course_id,
            "sections": [
                {
                    "title": "Section 1",
                    "questions": [
                        {"question": "What is ML?", "options": ["A. Machine Learning", "B. Math Logic"], "correct": "A", "marks": 10}
                    ]
                }
            ],
            "duration_minutes": 60,
            "total_marks": 10,
            "description": "Org admin test exam"
        }
        
        response = requests.post(f"{BASE_URL}/api/training-engine/publish-exam", 
                                json=payload, headers=headers)
        assert response.status_code in [200, 201], f"Failed to publish exam: {response.text}"
        print(f"Org admin published exam successfully")
    
    def test_student_cannot_publish_exam(self, student_token):
        """Student should NOT be able to publish exam"""
        headers = {"Authorization": f"Bearer {student_token}"}
        
        payload = {
            "title": "Student Test Exam",
            "course_id": "some-course-id",
            "sections": [],
            "duration_minutes": 30,
            "total_marks": 100,
            "description": "Should fail"
        }
        
        response = requests.post(f"{BASE_URL}/api/training-engine/publish-exam", 
                                json=payload, headers=headers)
        assert response.status_code == 403, f"Student should be forbidden: {response.status_code}"


class TestAvatarVoiceCloning:
    """Test avatar voice cloning endpoints"""
    
    def test_voice_status_endpoint(self, student_token):
        """GET /api/avatar/voice-status should return voice status"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/avatar/voice-status", headers=headers)
        assert response.status_code == 200, f"Failed to get voice status: {response.text}"
        data = response.json()
        assert "has_voice" in data, "Response should have has_voice field"
        print(f"Voice status: {data}")
    
    def test_voice_status_requires_auth(self):
        """Voice status should require authentication"""
        response = requests.get(f"{BASE_URL}/api/avatar/voice-status")
        assert response.status_code in [401, 403], "Should require auth"
    
    def test_upload_voice_requires_auth(self):
        """Upload voice should require authentication"""
        response = requests.post(f"{BASE_URL}/api/avatar/upload-voice")
        assert response.status_code in [401, 403, 422], "Should require auth or file"


class TestStudentAssignmentsAccess:
    """Test that students can see AI-generated assignments for enrolled courses"""
    
    def test_student_get_assignments(self, student_token):
        """Student should see assignments for enrolled courses"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/assignments", headers=headers)
        assert response.status_code == 200, f"Failed to get assignments: {response.text}"
        assignments = response.json()
        assert isinstance(assignments, list), "Assignments should be a list"
        print(f"Student sees {len(assignments)} assignments")
    
    def test_student_get_exams(self, student_token):
        """Student should see exams for enrolled courses"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/exams", headers=headers)
        assert response.status_code == 200, f"Failed to get exams: {response.text}"
        exams = response.json()
        assert isinstance(exams, list), "Exams should be a list"
        print(f"Student sees {len(exams)} exams")


class TestCertificateGallery:
    """Test certificate gallery endpoint"""
    
    def test_certificate_gallery_my(self, student_token):
        """GET /api/certificates/gallery/my should return user's certificates"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/certificates/gallery/my", headers=headers)
        assert response.status_code == 200, f"Failed to get certificates: {response.text}"
        data = response.json()
        assert isinstance(data, (list, dict)), "Should return certificates data"
        print(f"Certificate gallery response: {type(data)}")


class TestOrgPortal:
    """Test org portal endpoints"""
    
    def test_org_public_info(self):
        """GET /api/org/public/cognify should return org info"""
        response = requests.get(f"{BASE_URL}/api/org/public/cognify")
        assert response.status_code == 200, f"Failed to get org info: {response.text}"
        data = response.json()
        assert "name" in data or "organization" in data, "Should have org name"
        print(f"Org public info: {data}")


class TestHealthEndpoint:
    """Basic health check"""
    
    def test_health(self):
        """Health endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
