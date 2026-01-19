"""
EduOS 2026 API Tests
Tests for authentication, courses, at-risk students, and dashboard endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://eduos-platform-2.preview.emergentagent.com')

# Test credentials
TEACHER_CREDS = {"email": "demo.teacher@eduos.edu", "password": "demo123"}
STUDENT_CREDS = {"email": "demo.student@eduos.edu", "password": "demo123"}
ADMIN_CREDS = {"email": "demo.admin@eduos.edu", "password": "demo123"}


class TestHealthCheck:
    """Health check endpoint tests"""
    
    def test_health_endpoint(self):
        """Test that health endpoint returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ Health check passed: {data}")


class TestAuthentication:
    """Authentication endpoint tests"""
    
    def test_teacher_login_success(self):
        """Test teacher login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == TEACHER_CREDS["email"]
        assert data["user"]["role"] == "teacher"
        print(f"✓ Teacher login successful: {data['user']['full_name']}")
        return data["access_token"]
    
    def test_student_login_success(self):
        """Test student login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=STUDENT_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == STUDENT_CREDS["email"]
        assert data["user"]["role"] == "student"
        print(f"✓ Student login successful: {data['user']['full_name']}")
        return data["access_token"]
    
    def test_admin_login_success(self):
        """Test admin login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_CREDS["email"]
        assert data["user"]["role"] == "admin"
        print(f"✓ Admin login successful: {data['user']['full_name']}")
        return data["access_token"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials returns 401"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid credentials correctly rejected with 401")


class TestDashboard:
    """Dashboard endpoint tests"""
    
    @pytest.fixture
    def teacher_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
        return response.json()["access_token"]
    
    @pytest.fixture
    def student_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=STUDENT_CREDS)
        return response.json()["access_token"]
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        return response.json()["access_token"]
    
    def test_dashboard_stats_teacher(self, teacher_token):
        """Test dashboard stats for teacher"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_students" in data or "active_courses" in data
        print(f"✓ Teacher dashboard stats: {data}")
    
    def test_dashboard_stats_student(self, student_token):
        """Test dashboard stats for student"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Student dashboard stats: {data}")
    
    def test_dashboard_stats_admin(self, admin_token):
        """Test dashboard stats for admin"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Admin dashboard stats: {data}")


class TestCourses:
    """Course endpoint tests"""
    
    @pytest.fixture
    def teacher_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
        return response.json()["access_token"]
    
    @pytest.fixture
    def student_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=STUDENT_CREDS)
        return response.json()["access_token"]
    
    def test_get_courses_teacher(self, teacher_token):
        """Test getting courses as teacher"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Teacher can view {len(data)} courses")
        return data
    
    def test_get_courses_student(self, student_token):
        """Test getting courses as student"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Student can view {len(data)} courses")
    
    def test_create_course_teacher(self, teacher_token):
        """Test creating a course as teacher"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        course_data = {
            "code": "TEST101",
            "name": "Test Course for API Testing",
            "description": "This is a test course created by automated tests",
            "grade_level": "Grade 10",
            "credits": 3,
            "max_students": 30
        }
        response = requests.post(f"{BASE_URL}/api/courses", json=course_data, headers=headers)
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == course_data["code"]
        assert data["name"] == course_data["name"]
        assert "id" in data
        print(f"✓ Teacher created course: {data['name']} (ID: {data['id']})")
        return data
    
    def test_create_course_student_forbidden(self, student_token):
        """Test that students cannot create courses"""
        headers = {"Authorization": f"Bearer {student_token}"}
        course_data = {
            "code": "FAIL101",
            "name": "Should Fail",
            "description": "Students should not be able to create courses",
            "grade_level": "Grade 10",
            "credits": 3,
            "max_students": 30
        }
        response = requests.post(f"{BASE_URL}/api/courses", json=course_data, headers=headers)
        assert response.status_code == 403
        print("✓ Student correctly forbidden from creating courses (403)")


class TestAtRiskStudents:
    """At-risk students endpoint tests"""
    
    @pytest.fixture
    def teacher_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
        return response.json()["access_token"]
    
    @pytest.fixture
    def student_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=STUDENT_CREDS)
        return response.json()["access_token"]
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        return response.json()["access_token"]
    
    def test_at_risk_students_teacher(self, teacher_token):
        """Test at-risk students endpoint as teacher"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(f"{BASE_URL}/api/students/at-risk", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Teacher can access at-risk students: {len(data)} students found")
        if data:
            # Validate structure of at-risk student data
            student = data[0]
            assert "id" in student
            assert "name" in student
            assert "risk_score" in student
            assert "risk_level" in student
            assert "factors" in student
            print(f"  - First at-risk student: {student['name']} (Risk: {student['risk_score']})")
        return data
    
    def test_at_risk_students_admin(self, admin_token):
        """Test at-risk students endpoint as admin"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/students/at-risk", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Admin can access at-risk students: {len(data)} students found")
        return data
    
    def test_at_risk_students_student_forbidden(self, student_token):
        """Test that students cannot access at-risk endpoint"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/students/at-risk", headers=headers)
        assert response.status_code == 403
        print("✓ Student correctly forbidden from at-risk endpoint (403)")


class TestStudents:
    """Students endpoint tests"""
    
    @pytest.fixture
    def teacher_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
        return response.json()["access_token"]
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDS)
        return response.json()["access_token"]
    
    def test_get_students_teacher(self, teacher_token):
        """Test getting students list as teacher"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(f"{BASE_URL}/api/students", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Teacher can view {len(data)} students")
    
    def test_get_students_admin(self, admin_token):
        """Test getting students list as admin"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/students", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Admin can view {len(data)} students")


class TestAuthMe:
    """Auth /me endpoint tests"""
    
    @pytest.fixture
    def teacher_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
        return response.json()["access_token"]
    
    def test_auth_me(self, teacher_token):
        """Test /auth/me endpoint returns current user"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEACHER_CREDS["email"]
        assert data["role"] == "teacher"
        print(f"✓ Auth /me returns correct user: {data['full_name']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
