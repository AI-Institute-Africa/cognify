"""
EduOS 2026 - P0/P1 Feature Tests
Testing: Login flows, Parent portal, Settings, Virtual classroom, Study groups, Course view
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://school-hub-128.preview.emergentagent.com').rstrip('/')

# Test credentials
STUDENT_CREDS = {"email": "demo.student@eduos.edu", "password": "demo123"}
TEACHER_CREDS = {"email": "demo.teacher@eduos.edu", "password": "demo123"}
PARENT_CREDS = {"email": "demo.parent@eduos.edu", "password": "demo123"}
ADMIN_CREDS = {"email": "demo.admin@eduos.edu", "password": "demo123"}


def get_token(creds):
    """Helper to get auth token from login response"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=creds)
    if response.status_code == 200:
        data = response.json()
        # API returns access_token, not token
        return data.get("access_token") or data.get("token")
    return None


class TestHealthAndBasics:
    """Basic health and connectivity tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ Health check passed: {data}")


class TestStudentLogin:
    """Student login and dashboard tests"""
    
    def test_student_login_success(self):
        """Test student can login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=STUDENT_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data or "token" in data
        assert "user" in data
        assert data["user"]["role"] == "student"
        assert data["user"]["email"] == STUDENT_CREDS["email"]
        print(f"✓ Student login successful: {data['user']['full_name']}")
    
    def test_student_dashboard_stats(self):
        """Test student can access dashboard stats"""
        token = get_token(STUDENT_CREDS)
        assert token is not None, "Failed to get student token"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Student dashboard stats: {data}")
    
    def test_student_courses(self):
        """Test student can view courses"""
        token = get_token(STUDENT_CREDS)
        assert token is not None
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Student can view {len(data)} courses")


class TestTeacherLogin:
    """Teacher login and dashboard tests"""
    
    def test_teacher_login_success(self):
        """Test teacher can login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data or "token" in data
        assert data["user"]["role"] == "teacher"
        print(f"✓ Teacher login successful: {data['user']['full_name']}")
    
    def test_teacher_dashboard_stats(self):
        """Test teacher can access dashboard stats"""
        token = get_token(TEACHER_CREDS)
        assert token is not None
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        assert response.status_code == 200
        print(f"✓ Teacher dashboard stats retrieved")


class TestParentLogin:
    """Parent login and children listing tests"""
    
    def test_parent_login_success(self):
        """Test parent can login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=PARENT_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data or "token" in data
        assert data["user"]["role"] == "parent"
        print(f"✓ Parent login successful: {data['user']['full_name']}")
    
    def test_parent_children_endpoint(self):
        """Test parent can access /api/parents/children endpoint"""
        token = get_token(PARENT_CREDS)
        assert token is not None
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/parents/children", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Parent children endpoint works: {len(data)} children linked")
        return data


class TestUserSettings:
    """User settings page tests"""
    
    def test_get_user_settings(self):
        """Test user can get their settings"""
        token = get_token(STUDENT_CREDS)
        assert token is not None
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/user/settings", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ User settings retrieved: {data}")
    
    def test_update_user_profile(self):
        """Test user can update their profile"""
        token = get_token(STUDENT_CREDS)
        assert token is not None
        headers = {"Authorization": f"Bearer {token}"}
        
        # Update profile
        response = requests.put(
            f"{BASE_URL}/api/user/profile?full_name=Demo%20Student%20Updated",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Profile updated: {data}")
        
        # Revert back
        requests.put(
            f"{BASE_URL}/api/user/profile?full_name=Demo%20Student",
            headers=headers
        )
    
    def test_update_notification_settings(self):
        """Test user can update notification settings"""
        token = get_token(STUDENT_CREDS)
        assert token is not None
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.put(
            f"{BASE_URL}/api/user/notifications?email_notifications=true&push_notifications=true",
            headers=headers
        )
        assert response.status_code == 200
        print(f"✓ Notification settings updated")
    
    def test_change_password(self):
        """Test password change functionality"""
        token = get_token(STUDENT_CREDS)
        assert token is not None
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to change password (should work with correct current password)
        response = requests.put(
            f"{BASE_URL}/api/user/password?current_password=demo123&new_password=demo123",
            headers=headers
        )
        # Should succeed (same password is allowed)
        assert response.status_code == 200
        print(f"✓ Password change endpoint works")


class TestVirtualClassroom:
    """Virtual classroom tests for students"""
    
    def test_student_meetings_endpoint(self):
        """Test student can access their meetings"""
        token = get_token(STUDENT_CREDS)
        assert token is not None
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/zoom/student-meetings", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Student meetings endpoint works: {len(data)} meetings")
    
    def test_teacher_zoom_meetings(self):
        """Test teacher can access zoom meetings"""
        token = get_token(TEACHER_CREDS)
        assert token is not None
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/zoom/meetings", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Teacher zoom meetings endpoint works: {len(data)} meetings")


class TestStudyGroups:
    """Study groups tests"""
    
    def test_get_all_study_groups(self):
        """Test student can see all public study groups"""
        token = get_token(STUDENT_CREDS)
        assert token is not None
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/study-groups/all", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ All study groups endpoint works: {len(data)} groups")
    
    def test_get_my_study_groups(self):
        """Test student can see their study groups"""
        token = get_token(STUDENT_CREDS)
        assert token is not None
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/study-groups/my-groups", headers=headers)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ My study groups endpoint works")


class TestCourseView:
    """Course view page tests"""
    
    def test_get_courses(self):
        """Test getting list of courses"""
        token = get_token(STUDENT_CREDS)
        assert token is not None
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"✓ Courses list retrieved: {len(data)} courses")
        return data
    
    def test_get_single_course(self):
        """Test getting a single course"""
        token = get_token(STUDENT_CREDS)
        assert token is not None
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get courses first
        courses_resp = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        courses = courses_resp.json()
        
        if len(courses) > 0:
            course_id = courses[0]["id"]
            response = requests.get(f"{BASE_URL}/api/courses/{course_id}", headers=headers)
            assert response.status_code == 200
            data = response.json()
            print(f"✓ Single course retrieved: {data.get('name', data.get('title'))}")
    
    def test_get_course_content(self):
        """Test getting course content (video/slides)"""
        token = get_token(STUDENT_CREDS)
        assert token is not None
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get courses first
        courses_resp = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        courses = courses_resp.json()
        
        if len(courses) > 0:
            course_id = courses[0]["id"]
            response = requests.get(f"{BASE_URL}/api/content/course/{course_id}/content", headers=headers)
            assert response.status_code == 200
            data = response.json()
            print(f"✓ Course content retrieved: {len(data)} items")


class TestInvalidCredentials:
    """Test invalid login attempts"""
    
    def test_invalid_password(self):
        """Test login fails with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo.student@eduos.edu",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print(f"✓ Invalid password correctly rejected")
    
    def test_invalid_email(self):
        """Test login fails with non-existent email"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "nonexistent@eduos.edu",
            "password": "demo123"
        })
        assert response.status_code == 401
        print(f"✓ Invalid email correctly rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
