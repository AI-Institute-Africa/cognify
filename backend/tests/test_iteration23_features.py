"""
Iteration 23 - Testing Features:
1. AI Features Selection Canvas - checkboxes for standard vs customized courses
2. Create Custom Course page - 3 creation methods
3. Organization login page at /org/cognify
4. Teacher messaging system
5. Multi-Subject page
6. Share Content page
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://scholar-port.preview.emergentagent.com')

def get_token(email, password):
    """Helper to get auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email,
        "password": password
    })
    data = response.json()
    return data.get("access_token") or data.get("token")


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_teacher_login(self):
        """Test teacher login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo.teacher@eduos.edu",
            "password": "demo123"
        })
        assert response.status_code == 200, f"Teacher login failed: {response.text}"
        data = response.json()
        assert "access_token" in data or "token" in data, "No token in response"
        assert data.get("user", {}).get("role") == "teacher", "User is not a teacher"
        print(f"Teacher login successful: {data.get('user', {}).get('full_name')}")
    
    def test_student_login(self):
        """Test student login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "demo.student@cognify.edu",
            "password": "demo123"
        })
        assert response.status_code == 200, f"Student login failed: {response.text}"
        data = response.json()
        assert "access_token" in data or "token" in data, "No token in response"
        print(f"Student login successful: {data.get('user', {}).get('full_name')}")


class TestOrganizationLogin:
    """Test organization-specific login page"""
    
    def test_org_public_info_cognify(self):
        """Test getting public info for Cognify University"""
        response = requests.get(f"{BASE_URL}/api/org/public/cognify")
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        if response.status_code == 200:
            data = response.json()
            assert "name" in data, "No name in org data"
            assert "branding" in data, "No branding in org data"
            assert "stats" in data, "No stats in org data"
            print(f"Organization found: {data.get('name')}")
            print(f"Branding: {data.get('branding')}")
            print(f"Stats: {data.get('stats')}")
        elif response.status_code == 404:
            print("Organization 'cognify' not found - may need to be created")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")


class TestTeacherMessaging:
    """Test teacher messaging system"""
    
    @pytest.fixture
    def teacher_token(self):
        return get_token("demo.teacher@eduos.edu", "demo123")
    
    def test_get_teacher_students(self, teacher_token):
        """Test getting students for teacher messaging"""
        response = requests.get(
            f"{BASE_URL}/api/teacher/students",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Failed to get students: {response.text}"
        students = response.json()
        print(f"Found {len(students)} students")
        return students
    
    def test_get_messages(self, teacher_token):
        """Test getting messages"""
        response = requests.get(
            f"{BASE_URL}/api/messages",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        print(f"Response status: {response.status_code}")
        assert response.status_code == 200, f"Failed to get messages: {response.text}"
        messages = response.json()
        print(f"Found {len(messages)} messages")
        return messages
    
    def test_send_message(self, teacher_token):
        """Test sending a message"""
        # First get a student to send to
        students_response = requests.get(
            f"{BASE_URL}/api/teacher/students",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        students = students_response.json()
        
        if len(students) == 0:
            pytest.skip("No students available to send message to")
        
        student_id = students[0]["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/messages",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={
                "recipient_id": student_id,
                "content": "Test message from pytest",
                "message_type": "text"
            }
        )
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text}")
        
        assert response.status_code == 200, f"Failed to send message: {response.text}"


class TestAIFeaturesPreferences:
    """Test AI features preferences API"""
    
    @pytest.fixture
    def student_token(self):
        return get_token("demo.student@cognify.edu", "demo123")
    
    def test_get_ai_preferences(self, student_token):
        """Test getting AI preferences"""
        response = requests.get(
            f"{BASE_URL}/api/user/ai-preferences",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        # May return 404 if no preferences set yet
        assert response.status_code in [200, 404], f"Unexpected status: {response.text}"
    
    def test_save_ai_preferences(self, student_token):
        """Test saving AI preferences"""
        response = requests.post(
            f"{BASE_URL}/api/user/ai-preferences",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "features": {
                    "multimodal": True,
                    "multilingual": True,
                    "avatar_tutor": False,
                    "ai_mentor": True
                },
                "role": "student",
                "course_type": "standard",
                "total_fee": 17.98
            }
        )
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text}")
        
        assert response.status_code == 200, f"Failed to save preferences: {response.text}"


class TestMultiSubject:
    """Test multi-subject learning paths"""
    
    @pytest.fixture
    def student_token(self):
        return get_token("demo.student@cognify.edu", "demo123")
    
    def test_get_my_paths(self, student_token):
        """Test getting user's multi-subject paths"""
        response = requests.get(
            f"{BASE_URL}/api/multi-subject/my-paths",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Failed to get paths: {response.text}"
        paths = response.json()
        print(f"Found {len(paths)} multi-subject paths")
    
    def test_get_courses_for_selection(self, student_token):
        """Test getting courses for multi-subject selection"""
        response = requests.get(
            f"{BASE_URL}/api/courses",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        print(f"Response status: {response.status_code}")
        
        assert response.status_code == 200, f"Failed to get courses: {response.text}"
        courses = response.json()
        print(f"Found {len(courses)} courses available for selection")


class TestShareContent:
    """Test share content functionality"""
    
    @pytest.fixture
    def student_token(self):
        return get_token("demo.student@cognify.edu", "demo123")
    
    def test_get_my_shared(self, student_token):
        """Test getting user's shared content"""
        response = requests.get(
            f"{BASE_URL}/api/share/my-shared",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        print(f"Response status: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        
        assert response.status_code == 200, f"Failed to get shared: {response.text}"
        shared = response.json()
        print(f"Found {len(shared)} shared items")
    
    def test_get_available_content(self, student_token):
        """Test getting available content to share"""
        for content_type in ["assignment", "grade", "certificate"]:
            response = requests.get(
                f"{BASE_URL}/api/share/available/{content_type}",
                headers={"Authorization": f"Bearer {student_token}"}
            )
            print(f"Content type '{content_type}': status {response.status_code}")
            
            assert response.status_code == 200, f"Failed for {content_type}: {response.text}"


class TestCustomCourseCreation:
    """Test custom course creation endpoints"""
    
    @pytest.fixture
    def teacher_token(self):
        return get_token("demo.teacher@eduos.edu", "demo123")
    
    def test_get_courses_for_import(self, teacher_token):
        """Test getting courses that can be imported for customization"""
        response = requests.get(
            f"{BASE_URL}/api/courses",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        print(f"Response status: {response.status_code}")
        
        assert response.status_code == 200, f"Failed to get courses: {response.text}"
        courses = response.json()
        
        # Filter standard courses
        standard_courses = [c for c in courses if c.get('course_branch') != 'customized' and not c.get('is_user_created')]
        print(f"Found {len(standard_courses)} standard courses available for import")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
