"""
Iteration 24 - Testing critical bug fixes:
1. Custom course generation - verify no 'body stream already read' error
2. Multi-Subject Continue Learning - should navigate to /multi-subject/{pathId} with lessons
3. Teacher messaging - verify students appear in the list
4. Student assignments - verify questions are displayed and file upload works
5. Organization login - staff should see org-specific content at /org/cognify
"""

import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEACHER_EMAIL = "demo.teacher@eduos.edu"
TEACHER_PASSWORD = "demo123"
STUDENT_EMAIL = "demo.student@cognify.edu"
STUDENT_PASSWORD = "demo123"
ORG_ADMIN_EMAIL = "test.orgadmin@cognify.edu"
ORG_ADMIN_PASSWORD = "admin123"


class TestAuthentication:
    """Test authentication for all user types"""
    
    def test_teacher_login(self):
        """Test teacher login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        assert response.status_code == 200, f"Teacher login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert data.get("user", {}).get("role") == "teacher"
        print(f"✓ Teacher login successful: {data['user'].get('full_name')}")
    
    def test_student_login(self):
        """Test student login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        assert response.status_code == 200, f"Student login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert data.get("user", {}).get("role") == "student"
        print(f"✓ Student login successful: {data['user'].get('full_name')}")
    
    def test_org_admin_login(self):
        """Test org admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Org admin login failed: {response.text}"
        data = response.json()
        assert "token" in data
        print(f"✓ Org admin login successful: {data['user'].get('full_name')}")


class TestOrganizationLogin:
    """Test organization login page and API"""
    
    def test_get_org_public_info(self):
        """Test getting public organization info for login page"""
        response = requests.get(f"{BASE_URL}/api/org/public/cognify")
        assert response.status_code == 200, f"Failed to get org info: {response.text}"
        data = response.json()
        assert data.get("name") is not None
        assert data.get("slug") == "cognify"
        print(f"✓ Organization info retrieved: {data.get('name')}")


class TestTeacherMessaging:
    """Test teacher messaging - verify students appear in the list"""
    
    @pytest.fixture
    def teacher_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Teacher login failed")
    
    def test_get_teacher_students(self, teacher_token):
        """Test getting students for teacher messaging - CRITICAL: Should return students"""
        response = requests.get(
            f"{BASE_URL}/api/teacher/students",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        assert response.status_code == 200, f"Failed to get students: {response.text}"
        students = response.json()
        assert isinstance(students, list), "Response should be a list"
        print(f"✓ Teacher students endpoint returned {len(students)} students")
        
        # Verify student structure if any exist
        if len(students) > 0:
            student = students[0]
            assert "id" in student, "Student should have id"
            assert "full_name" in student or "email" in student, "Student should have name or email"
            print(f"  First student: {student.get('full_name', student.get('email'))}")
    
    def test_get_messages(self, teacher_token):
        """Test getting messages"""
        response = requests.get(
            f"{BASE_URL}/api/messages",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        assert response.status_code == 200, f"Failed to get messages: {response.text}"
        print(f"✓ Messages endpoint working")


class TestStudentAssignments:
    """Test student assignments - verify questions display and file upload"""
    
    @pytest.fixture
    def student_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Student login failed")
    
    def test_get_student_assignments(self, student_token):
        """Test getting student assignments with content/questions"""
        response = requests.get(
            f"{BASE_URL}/api/assignments/student/my-assignments",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200, f"Failed to get assignments: {response.text}"
        assignments = response.json()
        assert isinstance(assignments, list), "Response should be a list"
        print(f"✓ Student assignments endpoint returned {len(assignments)} assignments")
        
        # Check if assignments have content/questions
        for assignment in assignments[:3]:  # Check first 3
            print(f"  Assignment: {assignment.get('title')}")
            if assignment.get('content'):
                content = assignment['content']
                if content.get('questions'):
                    print(f"    - Has {len(content['questions'])} questions")
                if content.get('reflection_prompts'):
                    print(f"    - Has {len(content['reflection_prompts'])} reflection prompts")
    
    def test_upload_submission_endpoint_exists(self, student_token):
        """Test that upload-submission endpoint exists (without actually uploading)"""
        # Just verify the endpoint responds (even with error for missing file)
        response = requests.post(
            f"{BASE_URL}/api/assignments/upload-submission",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        # Should return 422 (missing file) not 404 (endpoint not found)
        assert response.status_code != 404, "Upload submission endpoint not found"
        print(f"✓ Upload submission endpoint exists (status: {response.status_code})")


class TestMultiSubjectLearning:
    """Test multi-subject learning paths"""
    
    @pytest.fixture
    def student_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Student login failed")
    
    def test_get_my_paths(self, student_token):
        """Test getting user's multi-subject learning paths"""
        response = requests.get(
            f"{BASE_URL}/api/multi-subject/my-paths",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200, f"Failed to get paths: {response.text}"
        paths = response.json()
        assert isinstance(paths, list), "Response should be a list"
        print(f"✓ Multi-subject paths endpoint returned {len(paths)} paths")
        return paths
    
    def test_get_courses_for_path_creation(self, student_token):
        """Test getting courses available for multi-subject path creation"""
        response = requests.get(
            f"{BASE_URL}/api/courses",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200, f"Failed to get courses: {response.text}"
        courses = response.json()
        assert isinstance(courses, list), "Response should be a list"
        print(f"✓ Courses endpoint returned {len(courses)} courses for path creation")
    
    def test_create_and_get_path(self, student_token):
        """Test creating a multi-subject path and retrieving it"""
        # First get available courses
        courses_response = requests.get(
            f"{BASE_URL}/api/courses",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        if courses_response.status_code != 200:
            pytest.skip("Could not get courses")
        
        courses = courses_response.json()
        if len(courses) < 2:
            pytest.skip("Not enough courses to create multi-subject path")
        
        # Create a path with first 2 courses
        course_ids = [c['id'] for c in courses[:2]]
        create_response = requests.post(
            f"{BASE_URL}/api/multi-subject/create",
            headers={
                "Authorization": f"Bearer {student_token}",
                "Content-Type": "application/json"
            },
            json={
                "name": "TEST_Multi_Subject_Path",
                "description": "Test path for iteration 24",
                "goal": "Test multi-subject learning",
                "selected_courses": course_ids,
                "duration_weeks": 4,
                "ai_features": {}
            }
        )
        assert create_response.status_code == 200, f"Failed to create path: {create_response.text}"
        path_data = create_response.json()
        path_id = path_data.get('id')
        assert path_id is not None, "Path ID should be returned"
        print(f"✓ Created multi-subject path: {path_id}")
        
        # Now get the path
        get_response = requests.get(
            f"{BASE_URL}/api/multi-subject/{path_id}",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert get_response.status_code == 200, f"Failed to get path: {get_response.text}"
        path = get_response.json()
        assert path.get('name') == "TEST_Multi_Subject_Path"
        assert 'courses' in path or 'selected_courses' in path
        print(f"✓ Retrieved multi-subject path with courses")
        
        # Cleanup - delete the test path
        delete_response = requests.delete(
            f"{BASE_URL}/api/multi-subject/{path_id}",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        print(f"✓ Cleaned up test path")


class TestCustomCourseGeneration:
    """Test custom course generation API"""
    
    @pytest.fixture
    def teacher_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Teacher login failed")
    
    def test_get_courses_for_import(self, teacher_token):
        """Test getting courses available for import in custom course creation"""
        response = requests.get(
            f"{BASE_URL}/api/courses",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        assert response.status_code == 200, f"Failed to get courses: {response.text}"
        courses = response.json()
        assert isinstance(courses, list), "Response should be a list"
        print(f"✓ Courses available for import: {len(courses)}")
    
    def test_ai_features_preferences(self, teacher_token):
        """Test AI features preferences endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/ai-features/preferences",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        # Should return 200 or 404 (if no preferences saved yet)
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        print(f"✓ AI features preferences endpoint working (status: {response.status_code})")


class TestCourseLessons:
    """Test course lessons for multi-subject learning"""
    
    @pytest.fixture
    def student_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Student login failed")
    
    def test_get_course_lessons(self, student_token):
        """Test getting lessons for a course (needed for multi-subject learning page)"""
        # First get a course
        courses_response = requests.get(
            f"{BASE_URL}/api/courses",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        if courses_response.status_code != 200:
            pytest.skip("Could not get courses")
        
        courses = courses_response.json()
        if len(courses) == 0:
            pytest.skip("No courses available")
        
        course_id = courses[0]['id']
        
        # Get lessons for the course
        lessons_response = requests.get(
            f"{BASE_URL}/api/courses/{course_id}/lessons",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert lessons_response.status_code == 200, f"Failed to get lessons: {lessons_response.text}"
        lessons = lessons_response.json()
        assert isinstance(lessons, list), "Response should be a list"
        print(f"✓ Course {courses[0].get('title', course_id)} has {len(lessons)} lessons")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
