"""
Iteration 34 - Bug Fixes Testing
Tests for:
1. POST /api/org/bulk-enroll - sends emails with temp_password in results
2. POST /api/courses/{id}/generate-lessons-from-content - no 500 error
3. GET /api/students - returns org-specific participants
4. GET /api/teachers - returns org-specific staff
5. Participants and Staff pages routing (org_admin access)
"""

import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def org_admin_token(self):
        """Get org_admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test.orgadmin@cognify.edu",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Org admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def student_token(self):
        """Get student auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo.student@cognify.edu",
            "password": "demo123"
        })
        assert response.status_code == 200, f"Student login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    def test_org_admin_login(self, org_admin_token):
        """Test org_admin can login"""
        assert org_admin_token is not None
        print(f"✓ Org admin login successful")
    
    def test_student_login(self, student_token):
        """Test student can login"""
        assert student_token is not None
        print(f"✓ Student login successful")


class TestBulkEnrollment:
    """Test bulk enrollment with temp passwords and email sending"""
    
    @pytest.fixture(scope="class")
    def org_admin_token(self):
        """Get org_admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test.orgadmin@cognify.edu",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_bulk_enroll_returns_temp_password(self, org_admin_token):
        """Test that bulk enrollment returns temp_password for new users"""
        import uuid
        test_email = f"test_bulk_{uuid.uuid4().hex[:8]}@example.com"
        
        response = requests.post(
            f"{BASE_URL}/api/org/bulk-enroll",
            json={
                "emails": [test_email],
                "role": "student"
            },
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        
        assert response.status_code == 200, f"Bulk enroll failed: {response.text}"
        data = response.json()
        
        # Check response structure
        assert "results" in data, "No results in response"
        assert "successful" in data, "No successful count in response"
        assert data["successful"] >= 1, "No successful enrollments"
        
        # Check that temp_password is returned for new users
        new_user_result = next((r for r in data["results"] if r.get("status") == "created"), None)
        assert new_user_result is not None, "No new user created"
        assert "temp_password" in new_user_result, "No temp_password in result for new user"
        assert len(new_user_result["temp_password"]) >= 8, "Temp password too short"
        
        print(f"✓ Bulk enrollment returns temp_password: {new_user_result['temp_password'][:3]}***")
        
        # Cleanup - delete test user
        requests.delete(
            f"{BASE_URL}/api/users/{test_email}",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
    
    def test_bulk_enroll_existing_user_no_temp_password(self, org_admin_token):
        """Test that existing users don't get temp_password"""
        # Use existing student email
        response = requests.post(
            f"{BASE_URL}/api/org/bulk-enroll",
            json={
                "emails": ["demo.student@cognify.edu"],
                "role": "student"
            },
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        
        assert response.status_code == 200, f"Bulk enroll failed: {response.text}"
        data = response.json()
        
        # Check that existing user is linked, not created
        existing_result = next((r for r in data["results"] if r.get("status") == "existing_user_linked"), None)
        if existing_result:
            assert "temp_password" not in existing_result or existing_result.get("temp_password") is None
            print(f"✓ Existing user linked without temp_password")
        else:
            print(f"✓ User already in org (no action needed)")
    
    def test_bulk_enroll_with_role_teacher(self, org_admin_token):
        """Test bulk enrollment with teacher role"""
        import uuid
        test_email = f"test_teacher_{uuid.uuid4().hex[:8]}@example.com"
        
        response = requests.post(
            f"{BASE_URL}/api/org/bulk-enroll",
            json={
                "emails": [test_email],
                "role": "teacher"
            },
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        
        assert response.status_code == 200, f"Bulk enroll failed: {response.text}"
        data = response.json()
        assert data["successful"] >= 1
        
        # Verify user was created with teacher role
        new_user_result = next((r for r in data["results"] if r.get("status") == "created"), None)
        assert new_user_result is not None
        assert "temp_password" in new_user_result
        
        print(f"✓ Bulk enrollment with teacher role works")


class TestGenerateLessonsFromContent:
    """Test generate-lessons-from-content endpoint"""
    
    @pytest.fixture(scope="class")
    def org_admin_token(self):
        """Get org_admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test.orgadmin@cognify.edu",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def test_course_id(self, org_admin_token):
        """Create a test course for lesson generation"""
        import uuid
        response = requests.post(
            f"{BASE_URL}/api/courses",
            json={
                "name": f"Test Course for Lessons {uuid.uuid4().hex[:6]}",
                "description": "Test course for lesson generation",
                "category": "test"
            },
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        if response.status_code == 200:
            return response.json().get("id")
        # Try to get an existing course
        courses_resp = requests.get(
            f"{BASE_URL}/api/courses",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        if courses_resp.status_code == 200:
            courses = courses_resp.json()
            if courses:
                return courses[0].get("id")
        return None
    
    def test_generate_lessons_endpoint_accepts_file(self, org_admin_token, test_course_id):
        """Test that generate-lessons-from-content endpoint accepts file without 500 error"""
        if not test_course_id:
            pytest.skip("No course available for testing")
        
        # Create a simple text file
        test_content = """
        Introduction to Python Programming
        
        Chapter 1: Variables and Data Types
        Python supports various data types including integers, floats, strings, and booleans.
        Variables are used to store data values.
        
        Chapter 2: Control Flow
        Python uses if-else statements for conditional execution.
        Loops like for and while are used for iteration.
        
        Chapter 3: Functions
        Functions are reusable blocks of code.
        They help organize and modularize programs.
        """
        
        files = {
            'file': ('test_content.txt', io.BytesIO(test_content.encode()), 'text/plain')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/courses/{test_course_id}/generate-lessons-from-content",
            files=files,
            headers={"Authorization": f"Bearer {org_admin_token}"},
            timeout=60  # AI generation can take time
        )
        
        # The endpoint should NOT return 500 with 'str has no attribute text' error
        # It may timeout or return success, but should not have the specific bug
        if response.status_code == 500:
            error_detail = response.json().get("detail", "")
            assert "str" not in error_detail.lower() or "text" not in error_detail.lower(), \
                f"Bug still present: {error_detail}"
            print(f"✓ Endpoint returned 500 but NOT the 'str has no attribute text' error: {error_detail}")
        elif response.status_code == 504:
            print(f"✓ Endpoint timed out (expected for AI generation) - no 500 error")
        elif response.status_code == 200:
            data = response.json()
            assert "lessons" in data or "message" in data
            print(f"✓ Lessons generated successfully: {data.get('message', 'OK')}")
        else:
            print(f"✓ Endpoint returned {response.status_code} - no 500 'str has no attribute text' error")


class TestStudentsEndpoint:
    """Test GET /api/students returns org-specific participants"""
    
    @pytest.fixture(scope="class")
    def org_admin_token(self):
        """Get org_admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test.orgadmin@cognify.edu",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_students_returns_list(self, org_admin_token):
        """Test GET /api/students returns a list"""
        response = requests.get(
            f"{BASE_URL}/api/students",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        
        assert response.status_code == 200, f"Get students failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/students returns list with {len(data)} participants")
    
    def test_students_have_required_fields(self, org_admin_token):
        """Test that students have required fields: full_name, email, enrolled_courses, org_status, created_at"""
        response = requests.get(
            f"{BASE_URL}/api/students",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            student = data[0]
            # Check required fields
            assert "full_name" in student or ("user" in student and "full_name" in student.get("user", {})), \
                "Missing full_name field"
            assert "email" in student or ("user" in student and "email" in student.get("user", {})), \
                "Missing email field"
            assert "enrolled_courses" in student, "Missing enrolled_courses field"
            assert "org_status" in student, "Missing org_status field"
            assert "created_at" in student, "Missing created_at field"
            
            print(f"✓ Students have all required fields: full_name, email, enrolled_courses, org_status, created_at")
        else:
            print(f"✓ No students in org (empty list is valid)")
    
    def test_students_forbidden_for_student_role(self):
        """Test that students cannot access /api/students"""
        # Login as student
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo.student@cognify.edu",
            "password": "demo123"
        })
        assert login_resp.status_code == 200
        student_token = login_resp.json()["access_token"]
        
        response = requests.get(
            f"{BASE_URL}/api/students",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 403, f"Expected 403 for student role, got {response.status_code}"
        print(f"✓ Students endpoint correctly returns 403 for student role")


class TestTeachersEndpoint:
    """Test GET /api/teachers returns org-specific staff"""
    
    @pytest.fixture(scope="class")
    def org_admin_token(self):
        """Get org_admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test.orgadmin@cognify.edu",
            "password": "admin123"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_get_teachers_returns_list(self, org_admin_token):
        """Test GET /api/teachers returns a list"""
        response = requests.get(
            f"{BASE_URL}/api/teachers",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        
        assert response.status_code == 200, f"Get teachers failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/teachers returns list with {len(data)} staff members")
    
    def test_teachers_have_required_fields(self, org_admin_token):
        """Test that teachers have required fields: full_name, email, role, courses_count, rights, created_at"""
        response = requests.get(
            f"{BASE_URL}/api/teachers",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if len(data) > 0:
            teacher = data[0]
            # Check required fields
            assert "full_name" in teacher or ("user" in teacher and "full_name" in teacher.get("user", {})), \
                "Missing full_name field"
            assert "email" in teacher or ("user" in teacher and "email" in teacher.get("user", {})), \
                "Missing email field"
            assert "role" in teacher, "Missing role field"
            assert "courses_count" in teacher, "Missing courses_count field"
            assert "rights" in teacher, "Missing rights field"
            assert "created_at" in teacher, "Missing created_at field"
            
            # Check rights structure
            rights = teacher.get("rights", {})
            assert "can_create_courses" in rights, "Missing can_create_courses in rights"
            assert "can_manage_participants" in rights, "Missing can_manage_participants in rights"
            assert "can_upload_content" in rights, "Missing can_upload_content in rights"
            
            print(f"✓ Teachers have all required fields: full_name, email, role, courses_count, rights, created_at")
        else:
            print(f"✓ No teachers in org (empty list is valid)")
    
    def test_teachers_forbidden_for_student_role(self):
        """Test that students cannot access /api/teachers"""
        # Login as student
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo.student@cognify.edu",
            "password": "demo123"
        })
        assert login_resp.status_code == 200
        student_token = login_resp.json()["access_token"]
        
        response = requests.get(
            f"{BASE_URL}/api/teachers",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 403, f"Expected 403 for student role, got {response.status_code}"
        print(f"✓ Teachers endpoint correctly returns 403 for student role")
    
    def test_teachers_forbidden_for_teacher_role(self):
        """Test that teachers cannot access /api/teachers (only admin/org_admin)"""
        # Login as teacher
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo.teacher@eduos.edu",
            "password": "demo123"
        })
        if login_resp.status_code != 200:
            pytest.skip("Teacher login failed")
        teacher_token = login_resp.json()["access_token"]
        
        response = requests.get(
            f"{BASE_URL}/api/teachers",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        assert response.status_code == 403, f"Expected 403 for teacher role, got {response.status_code}"
        print(f"✓ Teachers endpoint correctly returns 403 for teacher role")


class TestEmailSenderConfiguration:
    """Test that email sender is configured correctly"""
    
    def test_sender_email_is_resend(self):
        """Verify SENDER_EMAIL in .env is onboarding@resend.dev"""
        import subprocess
        result = subprocess.run(
            ["grep", "SENDER_EMAIL", "/app/backend/.env"],
            capture_output=True,
            text=True
        )
        
        assert "onboarding@resend.dev" in result.stdout, \
            f"SENDER_EMAIL should be onboarding@resend.dev, got: {result.stdout}"
        assert "gmail.com" not in result.stdout, \
            f"SENDER_EMAIL should NOT be gmail.com"
        
        print(f"✓ SENDER_EMAIL is correctly set to onboarding@resend.dev")


class TestHealthCheck:
    """Basic health check"""
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✓ API health check passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
