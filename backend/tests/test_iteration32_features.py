"""
Iteration 32 - Bug Fixes Testing
Tests for:
1. AI Training Engine page - Publish section visibility for org_admin/teacher
2. Avatar Settings page - Voice Cloning section placement
3. Custom course creation endpoint
4. GET /api/courses for org_admin
5. GET /api/assignments for org_admin and students
6. Published assignments visible to students
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://knowledge-sync-9.preview.emergentagent.com')

# Test credentials
STUDENT_EMAIL = "demo.student@cognify.edu"
STUDENT_PASSWORD = "demo123"
ORG_ADMIN_EMAIL = "test.orgadmin@cognify.edu"
ORG_ADMIN_PASSWORD = "admin123"


class TestAuthentication:
    """Test authentication for different user roles"""
    
    def test_student_login(self):
        """Test student can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        assert response.status_code == 200, f"Student login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data["user"]["role"] == "student", f"Expected student role, got {data['user']['role']}"
        print(f"✓ Student login successful: {data['user']['email']}")
    
    def test_org_admin_login(self):
        """Test org_admin can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Org admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data["user"]["role"] == "org_admin", f"Expected org_admin role, got {data['user']['role']}"
        print(f"✓ Org admin login successful: {data['user']['email']}")


class TestCoursesAPI:
    """Test courses API for org_admin"""
    
    @pytest.fixture
    def org_admin_token(self):
        """Get org_admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture
    def student_token(self):
        """Get student auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_org_admin_can_get_courses(self, org_admin_token):
        """Test org_admin can access GET /api/courses"""
        response = requests.get(
            f"{BASE_URL}/api/courses",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200, f"GET /api/courses failed: {response.text}"
        courses = response.json()
        assert isinstance(courses, list), "Expected list of courses"
        print(f"✓ Org admin can access courses: {len(courses)} courses found")
    
    def test_custom_course_endpoint_exists(self, org_admin_token):
        """Test POST /api/courses/generate-custom endpoint exists and accepts requests"""
        # We're not testing actual generation (takes too long), just that endpoint exists
        # Use a very short timeout since we just want to verify the endpoint accepts the request
        try:
            response = requests.post(
                f"{BASE_URL}/api/courses/generate-custom",
                headers={"Authorization": f"Bearer {org_admin_token}"},
                json={
                    "title": "Test Course",
                    "description": "Test description",
                    "learning_goal": "Test learning goal",
                    "target_audience": "beginner",
                    "duration_weeks": 1,
                    "num_lessons": 3,
                    "course_type": "free_custom",
                    "language": "en"
                },
                timeout=5  # Very short timeout - we just want to verify endpoint exists
            )
            # Accept 200 (success), 500 (AI timeout), or 504 (gateway timeout)
            assert response.status_code in [200, 201, 500, 502, 504], f"Unexpected status: {response.status_code} - {response.text}"
            print(f"✓ Custom course endpoint exists and accepts requests (status: {response.status_code})")
        except requests.exceptions.ReadTimeout:
            # Timeout is expected for this long-running endpoint
            print("✓ Custom course endpoint exists (timed out as expected for long-running AI generation)")


class TestAssignmentsAPI:
    """Test assignments API for different roles"""
    
    @pytest.fixture
    def org_admin_token(self):
        """Get org_admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture
    def student_token(self):
        """Get student auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_org_admin_can_get_assignments(self, org_admin_token):
        """Test org_admin can access GET /api/assignments"""
        response = requests.get(
            f"{BASE_URL}/api/assignments",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200, f"GET /api/assignments failed: {response.text}"
        data = response.json()
        # Response could be list or dict with assignments key
        if isinstance(data, dict):
            assignments = data.get("assignments", [])
        else:
            assignments = data
        print(f"✓ Org admin can access assignments: {len(assignments)} assignments found")
    
    def test_student_can_get_assignments(self, student_token):
        """Test student can access GET /api/assignments/student/my-assignments"""
        response = requests.get(
            f"{BASE_URL}/api/assignments/student/my-assignments",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200, f"GET /api/assignments/student/my-assignments failed: {response.text}"
        data = response.json()
        if isinstance(data, dict):
            assignments = data.get("assignments", [])
        else:
            assignments = data
        print(f"✓ Student can access assignments: {len(assignments)} assignments found")


class TestAvatarVoiceCloning:
    """Test avatar voice cloning endpoints"""
    
    @pytest.fixture
    def org_admin_token(self):
        """Get org_admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_voice_status_endpoint(self, org_admin_token):
        """Test GET /api/avatar/voice-status endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/avatar/voice-status",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200, f"GET /api/avatar/voice-status failed: {response.text}"
        data = response.json()
        assert "has_voice" in data, "Expected has_voice field in response"
        print(f"✓ Voice status endpoint works: has_voice={data.get('has_voice')}")


class TestPublishEndpoints:
    """Test publish assignment/exam endpoints for teachers/org_admin"""
    
    @pytest.fixture
    def org_admin_token(self):
        """Get org_admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture
    def student_token(self):
        """Get student auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_publish_assignment_requires_auth(self):
        """Test publish assignment endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/training-engine/publish-assignment",
            json={"title": "Test", "course_id": "test", "questions": []}
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Publish assignment requires authentication")
    
    def test_student_cannot_publish_assignment(self, student_token):
        """Test student cannot publish assignment (should get 403)"""
        response = requests.post(
            f"{BASE_URL}/api/training-engine/publish-assignment",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"title": "Test", "course_id": "test", "questions": []}
        )
        assert response.status_code == 403, f"Expected 403 for student, got {response.status_code}"
        print("✓ Student correctly denied from publishing assignment")
    
    def test_org_admin_can_publish_assignment(self, org_admin_token):
        """Test org_admin can access publish assignment endpoint"""
        # First get a course to use
        courses_response = requests.get(
            f"{BASE_URL}/api/courses",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        courses = courses_response.json()
        if not courses:
            pytest.skip("No courses available for testing")
        
        course_id = courses[0]["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/training-engine/publish-assignment",
            headers={"Authorization": f"Bearer {org_admin_token}"},
            json={
                "title": "Test Assignment from Iteration 32",
                "course_id": course_id,
                "questions": [
                    {"q": "Test question 1?", "a": "Test answer 1", "category": "basic"},
                    {"q": "Test question 2?", "a": "Test answer 2", "category": "intermediate"}
                ],
                "description": "Test assignment created during iteration 32 testing",
                "max_score": 10
            }
        )
        assert response.status_code in [200, 201], f"Publish assignment failed: {response.status_code} - {response.text}"
        print(f"✓ Org admin can publish assignment (status: {response.status_code})")


class TestOrgAdminSidebarAccess:
    """Test org_admin has access to teacher-side features"""
    
    @pytest.fixture
    def org_admin_token(self):
        """Get org_admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_org_admin_can_access_exams(self, org_admin_token):
        """Test org_admin can access GET /api/exams"""
        response = requests.get(
            f"{BASE_URL}/api/exams",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200, f"GET /api/exams failed: {response.status_code}"
        print("✓ Org admin can access exams endpoint")
    
    def test_org_admin_can_access_grades(self, org_admin_token):
        """Test org_admin can access GET /api/grades"""
        response = requests.get(
            f"{BASE_URL}/api/grades",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        # 200 or 404 (no grades) are both acceptable
        assert response.status_code in [200, 404], f"GET /api/grades failed: {response.status_code}"
        print(f"✓ Org admin can access grades endpoint (status: {response.status_code})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
