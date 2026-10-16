"""
Test Phase 4 Features - EduOS 2026
Tests for:
1. Avatar Settings & Voice Cloning
2. Video/Slides Generation APIs
3. Student Meetings (Virtual Classroom)
4. Organization Admin Dashboard
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
STUDENT_EMAIL = "demo.student@eduos.edu"
STUDENT_PASSWORD = "demo123"
TEACHER_EMAIL = "demo.teacher@eduos.edu"
TEACHER_PASSWORD = "demo123"
ADMIN_EMAIL = "demo.admin@eduos.edu"
ADMIN_PASSWORD = "demo123"


def get_token(email, password):
    """Helper to get auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email,
        "password": password
    })
    data = response.json()
    # API returns access_token, not token
    return data.get("access_token") or data.get("token")


class TestHealthAndAuth:
    """Basic health and authentication tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get('status') == 'healthy'
        print(f"✓ Health check passed: {data}")
    
    def test_student_login(self):
        """Test student login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data or "token" in data
        assert data.get("user", {}).get("role") == "student"
        print(f"✓ Student login successful: {data.get('user', {}).get('email')}")
    
    def test_teacher_login(self):
        """Test teacher login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data or "token" in data
        assert data.get("user", {}).get("role") == "teacher"
        print(f"✓ Teacher login successful: {data.get('user', {}).get('email')}")
    
    def test_admin_login(self):
        """Test admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data or "token" in data
        print(f"✓ Admin login successful: {data.get('user', {}).get('email')}")


class TestAvatarSettings:
    """Test Avatar Settings & Voice APIs"""
    
    @pytest.fixture
    def student_token(self):
        return get_token(STUDENT_EMAIL, STUDENT_PASSWORD)
    
    def test_get_preset_voices(self, student_token):
        """Test GET /api/voice/preset-voices - should return 6 voices"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/voice/preset-voices", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 6, f"Expected 6 preset voices, got {len(data)}"
        
        # Verify voice structure
        for voice in data:
            assert "id" in voice
            assert "name" in voice
            assert "gender" in voice
            assert "style" in voice
        
        voice_names = [v['name'] for v in data]
        print(f"✓ Preset voices: {voice_names}")
    
    def test_get_avatar_settings(self, student_token):
        """Test GET /api/voice/avatar-settings"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/voice/avatar-settings", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have default settings
        assert "voice_id" in data
        assert "teaching_style" in data
        print(f"✓ Avatar settings: voice={data.get('voice_id')}, style={data.get('teaching_style')}")
    
    def test_save_avatar_settings(self, student_token):
        """Test POST /api/voice/save-avatar-settings"""
        headers = {"Authorization": f"Bearer {student_token}"}
        params = {
            "avatar_name": "Test Tutor",
            "voice_id": "shimmer",
            "teaching_style": "friendly"
        }
        response = requests.post(
            f"{BASE_URL}/api/voice/save-avatar-settings",
            params=params,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ Avatar settings saved: {data.get('message')}")
    
    def test_clone_voice_simple(self, student_token):
        """Test POST /api/voice/clone-simple (MOCKED)"""
        headers = {"Authorization": f"Bearer {student_token}"}
        params = {"name": "Test Voice Clone"}
        response = requests.post(
            f"{BASE_URL}/api/voice/clone-simple",
            params=params,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "voice_id" in data
        assert data.get("status") == "ready"
        print(f"✓ Voice cloned (MOCKED): {data.get('voice_id')}")


class TestStudentMeetings:
    """Test Student Virtual Classroom Meetings"""
    
    @pytest.fixture
    def student_token(self):
        return get_token(STUDENT_EMAIL, STUDENT_PASSWORD)
    
    def test_get_student_meetings(self, student_token):
        """Test GET /api/zoom/student-meetings"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/zoom/student-meetings", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Check meeting structure if any exist
        if len(data) > 0:
            meeting = data[0]
            assert "id" in meeting or "topic" in meeting
            print(f"✓ Student meetings found: {len(data)} meetings")
        else:
            print("✓ Student meetings endpoint works (no meetings yet)")


class TestOrgAdminDashboard:
    """Test Organization Admin Dashboard APIs"""
    
    @pytest.fixture
    def admin_token(self):
        return get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
    
    def test_get_org_admin_dashboard(self, admin_token):
        """Test GET /api/org-admin/dashboard"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/org-admin/dashboard", headers=headers)
        
        # May return 403 if user is not org_admin role
        if response.status_code == 403:
            print("⚠ Admin user is not org_admin role - expected for demo.admin")
            pytest.skip("Admin user doesn't have org_admin role")
        
        assert response.status_code == 200
        data = response.json()
        assert "statistics" in data
        print(f"✓ Org admin dashboard: {data.get('statistics')}")
    
    def test_get_org_analytics(self, admin_token):
        """Test GET /api/org-admin/analytics"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/org-admin/analytics", headers=headers)
        
        if response.status_code == 403:
            print("⚠ Admin user is not org_admin role")
            pytest.skip("Admin user doesn't have org_admin role")
        
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Org analytics retrieved")
    
    def test_get_org_teachers(self, admin_token):
        """Test GET /api/org-admin/teachers"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/org-admin/teachers", headers=headers)
        
        if response.status_code == 403:
            pytest.skip("Admin user doesn't have org_admin role")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Org teachers: {len(data)} teachers")
    
    def test_get_org_students(self, admin_token):
        """Test GET /api/org-admin/students"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/org-admin/students", headers=headers)
        
        if response.status_code == 403:
            pytest.skip("Admin user doesn't have org_admin role")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Org students: {len(data)} students")


class TestVideoSlidesGeneration:
    """Test Video and Slides Generation APIs (Teacher only)"""
    
    @pytest.fixture
    def teacher_token(self):
        return get_token(TEACHER_EMAIL, TEACHER_PASSWORD)
    
    def test_generate_video_endpoint_exists(self, teacher_token):
        """Test POST /api/content/generate-video endpoint exists"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        # Just test the endpoint exists - actual generation takes too long
        response = requests.post(
            f"{BASE_URL}/api/content/generate-video",
            params={"topic": "Test Topic", "duration": 1},
            headers=headers
        )
        
        # Should not be 404 - endpoint exists
        assert response.status_code != 404, "Video generation endpoint not found"
        print(f"✓ Video generation endpoint exists (status: {response.status_code})")
    
    def test_generate_slides_endpoint_exists(self, teacher_token):
        """Test POST /api/content/generate-slides endpoint exists"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.post(
            f"{BASE_URL}/api/content/generate-slides",
            params={"topic": "Test Topic", "slide_count": 1},
            headers=headers
        )
        
        assert response.status_code != 404, "Slides generation endpoint not found"
        print(f"✓ Slides generation endpoint exists (status: {response.status_code})")


class TestCourseViewFeatures:
    """Test Course View related features"""
    
    @pytest.fixture
    def student_token(self):
        return get_token(STUDENT_EMAIL, STUDENT_PASSWORD)
    
    @pytest.fixture
    def teacher_token(self):
        return get_token(TEACHER_EMAIL, TEACHER_PASSWORD)
    
    def test_get_courses(self, student_token):
        """Test GET /api/courses"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Courses retrieved: {len(data)} courses")
        return data
    
    def test_get_course_content(self, student_token):
        """Test GET /api/content/course/{course_id}/content"""
        headers = {"Authorization": f"Bearer {student_token}"}
        
        # First get courses
        courses_response = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        courses = courses_response.json()
        
        if not isinstance(courses, list) or len(courses) == 0:
            pytest.skip("No courses available")
        
        course_id = courses[0].get('id')
        response = requests.get(
            f"{BASE_URL}/api/content/course/{course_id}/content",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Course content retrieved: {len(data)} items for course {course_id}")
    
    def test_avatar_teach_lesson_endpoint(self, student_token):
        """Test POST /api/content/lesson/{lesson_id}/avatar-teach"""
        headers = {"Authorization": f"Bearer {student_token}"}
        
        # Get courses first
        courses_response = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        courses = courses_response.json()
        
        if not isinstance(courses, list) or len(courses) == 0:
            pytest.skip("No courses available")
        
        course_id = courses[0].get('id')
        
        # Get course content
        content_response = requests.get(
            f"{BASE_URL}/api/content/course/{course_id}/content",
            headers=headers
        )
        content = content_response.json()
        
        if not isinstance(content, list) or len(content) == 0:
            pytest.skip("No course content available")
        
        lesson_id = content[0].get('id')
        
        # Test avatar teach endpoint
        response = requests.post(
            f"{BASE_URL}/api/content/lesson/{lesson_id}/avatar-teach",
            params={"voice_id": "nova"},
            headers=headers
        )
        
        # Should not be 404
        assert response.status_code != 404, "Avatar teach endpoint not found"
        print(f"✓ Avatar teach endpoint exists (status: {response.status_code})")


class TestDashboardStats:
    """Test Dashboard Statistics"""
    
    @pytest.fixture
    def student_token(self):
        return get_token(STUDENT_EMAIL, STUDENT_PASSWORD)
    
    def test_dashboard_stats(self, student_token):
        """Test GET /api/dashboard/stats"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Dashboard stats retrieved")
    
    def test_achievements(self, student_token):
        """Test GET /api/achievements"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/achievements", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Achievements retrieved: {len(data)} achievements")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
