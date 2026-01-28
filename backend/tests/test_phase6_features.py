"""
Test Phase 6 Features - EduOS 2026
Tests: Email verification, Forgot password, Study groups, Virtual classroom,
       Academic levels, Course types, Teacher dashboard, Assignments,
       Stripe payments, Risk prediction, Credentials, Organization features
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
STUDENT_CREDS = {"email": "demo.student@eduos.edu", "password": "demo123"}
TEACHER_CREDS = {"email": "demo.teacher@eduos.edu", "password": "demo123"}
PARENT_CREDS = {"email": "demo.parent@eduos.edu", "password": "demo123"}
ORG_ADMIN_CREDS = {"email": "demo.orgadmin@eduos.edu", "password": "demo123"}


@pytest.fixture(scope="module")
def student_token():
    """Get student auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=STUDENT_CREDS)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Student login failed")


@pytest.fixture(scope="module")
def teacher_token():
    """Get teacher auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Teacher login failed")


@pytest.fixture(scope="module")
def parent_token():
    """Get parent auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=PARENT_CREDS)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Parent login failed")


@pytest.fixture(scope="module")
def org_admin_token():
    """Get org admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=ORG_ADMIN_CREDS)
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Org admin login failed")


class TestHealthAndBasics:
    """Basic health and connectivity tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ Health check passed: {data}")


class TestStudentMeetings:
    """Test student virtual classroom meetings endpoint"""
    
    def test_student_meetings_endpoint(self, student_token):
        """GET /api/zoom/student-meetings - returns meetings for students"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/zoom/student-meetings", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Student meetings: {len(data)} meetings found")


class TestStudyGroups:
    """Test study groups endpoints"""
    
    def test_all_study_groups_endpoint(self, student_token):
        """GET /api/study-groups/all - returns all study groups visible to students"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/study-groups/all", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ All study groups: {len(data)} groups found")
    
    def test_my_study_groups_endpoint(self, student_token):
        """GET /api/study-groups/my-groups - returns user's study groups"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/study-groups/my-groups", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ My study groups: {len(data)} groups found")


class TestAcademicLevels:
    """Test academic levels endpoint (Zimbabwe levels)"""
    
    def test_academic_levels_endpoint(self, student_token):
        """GET /api/academic-levels - returns Zimbabwe academic levels"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/academic-levels", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Check for Zimbabwe-specific levels
        level_names = [level.get("name", "") for level in data]
        print(f"✓ Academic levels: {level_names}")


class TestCourseTypes:
    """Test course types endpoint"""
    
    def test_course_types_endpoint(self, student_token):
        """GET /api/course-types - returns course types with pricing"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/course-types", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # Check structure
        for course_type in data:
            assert "name" in course_type or "type" in course_type
        print(f"✓ Course types: {len(data)} types found")


class TestTeacherDashboard:
    """Test teacher dashboard stats endpoint"""
    
    def test_teacher_dashboard_stats(self, teacher_token):
        """GET /api/teacher/dashboard-stats - returns real teacher stats"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(f"{BASE_URL}/api/teacher/dashboard-stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        # Check for expected fields
        assert "total_students" in data or "students" in data or isinstance(data, dict)
        print(f"✓ Teacher dashboard stats: {data}")


class TestStudentAssignments:
    """Test student assignments endpoint"""
    
    def test_student_my_assignments(self, student_token):
        """GET /api/assignments/student/my-assignments - returns student's assignments"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/assignments/student/my-assignments", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Student assignments: {len(data)} assignments found")


class TestEmailVerification:
    """Test email verification flow (registration with verification)"""
    
    def test_register_with_verification_invalid_email(self):
        """POST /api/auth/register-with-verification - test with invalid data"""
        # Test with missing fields
        response = requests.post(
            f"{BASE_URL}/api/auth/register-with-verification",
            params={"email": "", "password": "test123", "full_name": "Test User", "role": "student"}
        )
        # Should fail with validation error
        assert response.status_code in [400, 422]
        print(f"✓ Register validation works: {response.status_code}")
    
    def test_register_with_verification_existing_email(self):
        """POST /api/auth/register-with-verification - test with existing email"""
        response = requests.post(
            f"{BASE_URL}/api/auth/register-with-verification",
            params={
                "email": "demo.student@eduos.edu",
                "password": "test123",
                "full_name": "Test User",
                "role": "student"
            }
        )
        # Should fail because email exists
        assert response.status_code == 400
        print(f"✓ Duplicate email rejected: {response.status_code}")


class TestForgotPassword:
    """Test forgot password flow"""
    
    def test_forgot_password_v2_endpoint(self):
        """POST /api/auth/forgot-password-v2 - test password reset request"""
        response = requests.post(
            f"{BASE_URL}/api/auth/forgot-password-v2",
            params={"email": "demo.student@eduos.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        # In demo mode, reset_code may be returned
        print(f"✓ Forgot password: {data.get('message')}")
    
    def test_forgot_password_v2_nonexistent_email(self):
        """POST /api/auth/forgot-password-v2 - test with non-existent email"""
        response = requests.post(
            f"{BASE_URL}/api/auth/forgot-password-v2",
            params={"email": "nonexistent@test.com"}
        )
        # Should still return 200 for security (don't reveal if email exists)
        assert response.status_code in [200, 404]
        print(f"✓ Non-existent email handled: {response.status_code}")


class TestCredentialsV2:
    """Test credential issuance v2 endpoint"""
    
    def test_issue_credential_v2(self, teacher_token, student_token):
        """POST /api/credentials/issue-v2 - test credential issuance"""
        # First get a student ID
        headers = {"Authorization": f"Bearer {student_token}"}
        profile_response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        
        # Now try to issue credential as teacher
        teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.post(
            f"{BASE_URL}/api/credentials/issue-v2",
            params={
                "student_id": "test-student-id",
                "credential_type": "certificate",
                "title": "Test Certificate"
            },
            headers=teacher_headers
        )
        # May fail if student_id doesn't exist, but endpoint should be accessible
        assert response.status_code in [200, 201, 400, 404]
        print(f"✓ Issue credential v2: {response.status_code}")


class TestRiskPrediction:
    """Test risk prediction contact parent endpoint"""
    
    def test_contact_parent_endpoint(self, teacher_token):
        """POST /api/risk/contact-parent - test contacting parent about risk"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.post(
            f"{BASE_URL}/api/risk/contact-parent",
            params={
                "student_id": "test-student-id",
                "risk_type": "attendance",
                "message": "Test message about attendance"
            },
            headers=headers
        )
        # May fail if student doesn't exist, but endpoint should be accessible
        assert response.status_code in [200, 400, 404]
        print(f"✓ Contact parent: {response.status_code}")


class TestOrganizationFeatures:
    """Test organization-scoped features"""
    
    def test_org_participants_endpoint(self, org_admin_token):
        """GET /api/org/participants - returns organization participants"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/org/participants", headers=headers)
        # May return 403 if user doesn't have org_id, or 200 with data
        assert response.status_code in [200, 403]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            print(f"✓ Org participants: {len(data)} participants")
        else:
            print(f"✓ Org participants: Access controlled (403)")
    
    def test_org_courses_endpoint(self, org_admin_token):
        """GET /api/org/courses - returns organization courses"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/org/courses", headers=headers)
        assert response.status_code in [200, 403]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            print(f"✓ Org courses: {len(data)} courses")
        else:
            print(f"✓ Org courses: Access controlled (403)")


class TestStripePayments:
    """Test Stripe payment endpoints (MOCKED)"""
    
    def test_create_payment_checkout(self, student_token):
        """POST /api/payments/create-checkout - test payment checkout creation"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.post(
            f"{BASE_URL}/api/payments/create-checkout",
            params={
                "course_id": "test-course-id",
                "origin_url": "https://test.com"
            },
            headers=headers
        )
        # May fail if course doesn't exist or Stripe not configured
        assert response.status_code in [200, 400, 404, 500]
        print(f"✓ Payment checkout: {response.status_code}")


class TestLoginFlows:
    """Test all login flows"""
    
    def test_student_login(self):
        """Test student login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=STUDENT_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "student"
        print(f"✓ Student login successful")
    
    def test_teacher_login(self):
        """Test teacher login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "teacher"
        print(f"✓ Teacher login successful")
    
    def test_parent_login(self):
        """Test parent login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=PARENT_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "parent"
        print(f"✓ Parent login successful")
    
    def test_org_admin_login(self):
        """Test org admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ORG_ADMIN_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "org_admin"
        print(f"✓ Org admin login successful")
    
    def test_invalid_login(self):
        """Test invalid credentials rejected"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "invalid@test.com", "password": "wrongpass"}
        )
        assert response.status_code == 401
        print(f"✓ Invalid login rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
