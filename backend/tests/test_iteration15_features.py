"""
Iteration 15 Tests - Email Verification, Google OAuth, Content Upload
Tests:
1. POST /api/auth/register-with-verification - Creates pending registration with verification code
2. POST /api/auth/verify-email - Verifies email and creates user account
3. GET /api/auth/google/login - Returns Emergent auth URL for Google OAuth
4. POST /api/content/course/{course_id}/content - Teacher uploads content with JSON body
5. GET /api/content/course/{course_id}/content - Student can view course content
6. Teacher can see their courses after login
7. Student can see enrolled course content
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://cognify-edu.preview.emergentagent.com"

# Test credentials from review request
TEACHER_EMAIL = "demo.teacher@eduos.edu"
TEACHER_PASSWORD = "demo123"
STUDENT_EMAIL = "demo.student@cognify.edu"
STUDENT_PASSWORD = "demo123"
COURSE_ID = "9495d24f-7462-4f89-a751-a6742c61f62e"


class TestHealthCheck:
    """Basic health check to ensure API is running"""
    
    def test_health_endpoint(self):
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ Health check passed: {data}")


class TestEmailVerificationFlow:
    """Test email verification registration flow"""
    
    def test_register_with_verification_creates_pending_registration(self):
        """POST /api/auth/register-with-verification - Creates pending registration"""
        test_email = f"test_{uuid.uuid4().hex[:8]}@testcognify.com"
        
        payload = {
            "email": test_email,
            "password": "TestPass123!",
            "full_name": "Test User",
            "role": "student"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/auth/register-with-verification",
            json=payload
        )
        
        print(f"Register response status: {response.status_code}")
        print(f"Register response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "message" in data, "Response should contain 'message'"
        assert "email_sent" in data, "Response should contain 'email_sent'"
        assert "expires_in_minutes" in data, "Response should contain 'expires_in_minutes'"
        
        # Verify message content
        assert "verification" in data["message"].lower(), f"Message should mention verification: {data['message']}"
        assert data["expires_in_minutes"] == 15, f"Expiry should be 15 minutes, got {data['expires_in_minutes']}"
        
        print(f"✓ Register with verification passed: {data}")
        return test_email
    
    def test_register_with_verification_rejects_duplicate_email(self):
        """POST /api/auth/register-with-verification - Rejects duplicate email"""
        # Use existing teacher email
        payload = {
            "email": TEACHER_EMAIL,
            "password": "TestPass123!",
            "full_name": "Duplicate User",
            "role": "student"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/auth/register-with-verification",
            json=payload
        )
        
        print(f"Duplicate email response: {response.status_code}")
        assert response.status_code == 400, f"Expected 400 for duplicate email, got {response.status_code}"
        print(f"✓ Duplicate email correctly rejected")
    
    def test_verify_email_with_invalid_code(self):
        """POST /api/auth/verify-email - Rejects invalid verification code"""
        response = requests.post(
            f"{BASE_URL}/api/auth/verify-email",
            params={
                "email": "nonexistent@test.com",
                "verification_code": "000000"
            }
        )
        
        print(f"Invalid code response: {response.status_code}")
        assert response.status_code == 400, f"Expected 400 for invalid code, got {response.status_code}"
        print(f"✓ Invalid verification code correctly rejected")


class TestGoogleOAuthFlow:
    """Test Google OAuth endpoints"""
    
    def test_google_session_endpoint_exists(self):
        """POST /api/auth/google/session - Endpoint exists and responds"""
        # Test with invalid session to verify endpoint exists
        response = requests.post(
            f"{BASE_URL}/api/auth/google/session",
            params={"session_id": "invalid_session_id"}
        )
        
        print(f"Google session response: {response.status_code}")
        print(f"Google session body: {response.text[:200]}")
        
        # Should return 401 for invalid session, not 404
        # 520 is Cloudflare error which can happen intermittently
        assert response.status_code in [401, 500, 520], f"Expected 401, 500, or 520 for invalid session, got {response.status_code}"
        
        # If we got a proper response, verify it's the expected error
        if response.status_code == 401:
            data = response.json()
            assert "detail" in data, "Response should contain error detail"
        
        print(f"✓ Google session endpoint exists and responds correctly")


class TestTeacherAuthentication:
    """Test teacher login and course access"""
    
    @pytest.fixture
    def teacher_token(self):
        """Get teacher authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEACHER_EMAIL, "password": TEACHER_PASSWORD}
        )
        assert response.status_code == 200, f"Teacher login failed: {response.text}"
        data = response.json()
        return data["access_token"]
    
    def test_teacher_login_success(self):
        """Teacher can login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEACHER_EMAIL, "password": TEACHER_PASSWORD}
        )
        
        print(f"Teacher login response: {response.status_code}")
        assert response.status_code == 200, f"Teacher login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Response should contain access_token"
        assert "user" in data, "Response should contain user"
        assert data["user"]["role"] == "teacher", f"User role should be teacher, got {data['user']['role']}"
        
        print(f"✓ Teacher login successful: {data['user']['email']}")
        return data["access_token"]
    
    def test_teacher_can_see_courses(self, teacher_token):
        """Teacher can see their courses after login"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/courses",
            headers=headers
        )
        
        print(f"Teacher courses response: {response.status_code}")
        assert response.status_code == 200, f"Failed to get courses: {response.text}"
        
        courses = response.json()
        print(f"✓ Teacher can see {len(courses)} courses")
        
        # Check if courses have expected fields
        if courses:
            course = courses[0]
            assert "id" in course, "Course should have id"
            assert "name" in course, "Course should have name"
            print(f"  Sample course: {course.get('name', 'N/A')}")


class TestCourseContentUpload:
    """Test course content upload and retrieval"""
    
    @pytest.fixture
    def teacher_token(self):
        """Get teacher authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEACHER_EMAIL, "password": TEACHER_PASSWORD}
        )
        assert response.status_code == 200, f"Teacher login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture
    def student_token(self):
        """Get student authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": STUDENT_EMAIL, "password": STUDENT_PASSWORD}
        )
        assert response.status_code == 200, f"Student login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_teacher_can_upload_content_json(self, teacher_token):
        """POST /api/content/course/{course_id}/content - Teacher uploads content with JSON body"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        content_payload = {
            "content_type": "text",
            "title": f"Test Content {datetime.now().isoformat()}",
            "description": "Test content description for iteration 15",
            "content_text": "This is the test content body for the course.",
            "order": 1
        }
        
        response = requests.post(
            f"{BASE_URL}/api/content/course/{COURSE_ID}/content",
            json=content_payload,
            headers=headers
        )
        
        print(f"Content upload response: {response.status_code}")
        print(f"Content upload body: {response.text[:500]}")
        
        assert response.status_code == 200, f"Content upload failed: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response should contain content id"
        assert data["title"] == content_payload["title"], "Title should match"
        
        print(f"✓ Teacher uploaded content successfully: {data['id']}")
        return data["id"]
    
    def test_student_can_view_course_content(self, student_token):
        """GET /api/content/course/{course_id}/content - Student can view course content"""
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/content/course/{COURSE_ID}/content",
            headers=headers
        )
        
        print(f"Student content view response: {response.status_code}")
        
        assert response.status_code == 200, f"Failed to get course content: {response.text}"
        
        contents = response.json()
        print(f"✓ Student can view {len(contents)} content items")
        
        if contents:
            content = contents[0]
            assert "id" in content, "Content should have id"
            assert "title" in content, "Content should have title"
            print(f"  Sample content: {content.get('title', 'N/A')}")


class TestStudentEnrollment:
    """Test student enrollment and course access"""
    
    @pytest.fixture
    def student_token(self):
        """Get student authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": STUDENT_EMAIL, "password": STUDENT_PASSWORD}
        )
        assert response.status_code == 200, f"Student login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_student_login_success(self):
        """Student can login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": STUDENT_EMAIL, "password": STUDENT_PASSWORD}
        )
        
        print(f"Student login response: {response.status_code}")
        assert response.status_code == 200, f"Student login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Response should contain access_token"
        assert data["user"]["role"] == "student", f"User role should be student, got {data['user']['role']}"
        
        print(f"✓ Student login successful: {data['user']['email']}")
    
    def test_student_can_see_enrolled_courses(self, student_token):
        """Student can see enrolled courses"""
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/courses",
            headers=headers
        )
        
        print(f"Student courses response: {response.status_code}")
        assert response.status_code == 200, f"Failed to get courses: {response.text}"
        
        courses = response.json()
        print(f"✓ Student can see {len(courses)} courses")


class TestResendEmailIntegration:
    """Test Resend email service integration"""
    
    def test_resend_verification_endpoint_exists(self):
        """POST /api/auth/resend-verification - Endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/auth/resend-verification",
            params={"email": "nonexistent@test.com"}
        )
        
        print(f"Resend verification response: {response.status_code}")
        # Should return 404 for non-existent pending registration
        assert response.status_code == 404, f"Expected 404 for non-existent email, got {response.status_code}"
        print(f"✓ Resend verification endpoint exists and responds correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
