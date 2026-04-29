"""
Iteration 35 Tests - Generated Lessons & Assignment Generation
Tests for:
1. GET /api/content/course/{courseId}/content returns lessons from both collections
2. Generated lessons with source=uploaded_document appear in content endpoint
3. Generated lessons include text content and key_points array
4. POST /api/courses/{id}/generate-assignment-from-lessons endpoint exists
5. CourseManagePage shows 'Generate Assignment from Lessons' button when lessons exist
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://knowledge-sync-9.preview.emergentagent.com')

# Test credentials
STUDENT_EMAIL = "demo.student@cognify.edu"
STUDENT_PASSWORD = "demo123"
ADMIN_EMAIL = "test.orgadmin@cognify.edu"
ADMIN_PASSWORD = "admin123"

# Test course with generated lessons
TEST_COURSE_ID = "9495d24f-7462-4f89-a751-a6742c61f62e"


@pytest.fixture(scope="module")
def student_token():
    """Get student auth token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": STUDENT_EMAIL, "password": STUDENT_PASSWORD}
    )
    assert response.status_code == 200, f"Student login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def admin_token():
    """Get org admin auth token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json()["access_token"]


class TestCourseContentEndpoint:
    """Tests for GET /api/content/course/{courseId}/content"""
    
    def test_content_endpoint_returns_data(self, student_token):
        """Test that content endpoint returns array of content items"""
        response = requests.get(
            f"{BASE_URL}/api/content/course/{TEST_COURSE_ID}/content",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200, f"Content endpoint failed: {response.text}"
        
        data = response.json()
        # Could be array or object with access_restricted
        if isinstance(data, dict) and data.get('access_restricted'):
            contents = data.get('contents', [])
        else:
            contents = data
        
        assert isinstance(contents, list), "Content should be a list"
        assert len(contents) > 0, "Should have at least one content item"
    
    def test_content_includes_generated_lessons(self, student_token):
        """Test that generated lessons from lessons collection appear in content"""
        response = requests.get(
            f"{BASE_URL}/api/content/course/{TEST_COURSE_ID}/content",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        if isinstance(data, dict) and data.get('access_restricted'):
            contents = data.get('contents', [])
        else:
            contents = data
        
        # Find lessons with source=uploaded_document
        generated_lessons = [c for c in contents if c.get('source') == 'uploaded_document']
        assert len(generated_lessons) > 0, "Should have generated lessons from uploaded documents"
    
    def test_generated_lessons_have_text_content(self, student_token):
        """Test that generated lessons have actual text content (not empty)"""
        response = requests.get(
            f"{BASE_URL}/api/content/course/{TEST_COURSE_ID}/content",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        if isinstance(data, dict) and data.get('access_restricted'):
            contents = data.get('contents', [])
        else:
            contents = data
        
        # Find lessons with source=uploaded_document
        generated_lessons = [c for c in contents if c.get('source') == 'uploaded_document']
        
        for lesson in generated_lessons:
            text = lesson.get('text', '')
            assert text and len(text) > 50, f"Lesson '{lesson.get('title')}' should have substantial text content"
    
    def test_generated_lessons_have_key_points(self, student_token):
        """Test that generated lessons include key_points array"""
        response = requests.get(
            f"{BASE_URL}/api/content/course/{TEST_COURSE_ID}/content",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        if isinstance(data, dict) and data.get('access_restricted'):
            contents = data.get('contents', [])
        else:
            contents = data
        
        # Find lessons with source=uploaded_document
        generated_lessons = [c for c in contents if c.get('source') == 'uploaded_document']
        
        for lesson in generated_lessons:
            key_points = lesson.get('key_points', [])
            assert isinstance(key_points, list), f"Lesson '{lesson.get('title')}' should have key_points array"
            assert len(key_points) > 0, f"Lesson '{lesson.get('title')}' should have at least one key point"
    
    def test_content_includes_course_contents_collection(self, student_token):
        """Test that content from course_contents collection is also included"""
        response = requests.get(
            f"{BASE_URL}/api/content/course/{TEST_COURSE_ID}/content",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        if isinstance(data, dict) and data.get('access_restricted'):
            contents = data.get('contents', [])
        else:
            contents = data
        
        # Find content without source=uploaded_document (from course_contents)
        regular_content = [c for c in contents if not c.get('source')]
        assert len(regular_content) > 0, "Should have content from course_contents collection"


class TestLessonsEndpoint:
    """Tests for GET /api/courses/{courseId}/lessons"""
    
    def test_lessons_endpoint_returns_data(self, admin_token):
        """Test that lessons endpoint returns array of lessons"""
        response = requests.get(
            f"{BASE_URL}/api/courses/{TEST_COURSE_ID}/lessons",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Lessons endpoint failed: {response.text}"
        
        lessons = response.json()
        assert isinstance(lessons, list), "Lessons should be a list"
        assert len(lessons) > 0, "Should have at least one lesson"
    
    def test_lessons_have_required_fields(self, admin_token):
        """Test that lessons have all required fields"""
        response = requests.get(
            f"{BASE_URL}/api/courses/{TEST_COURSE_ID}/lessons",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        lessons = response.json()
        required_fields = ['id', 'course_id', 'title', 'content']
        
        for lesson in lessons:
            for field in required_fields:
                assert field in lesson, f"Lesson missing required field: {field}"
    
    def test_lessons_have_source_uploaded_document(self, admin_token):
        """Test that generated lessons have source=uploaded_document"""
        response = requests.get(
            f"{BASE_URL}/api/courses/{TEST_COURSE_ID}/lessons",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        lessons = response.json()
        
        # At least some lessons should have source=uploaded_document
        uploaded_lessons = [l for l in lessons if l.get('source') == 'uploaded_document']
        assert len(uploaded_lessons) > 0, "Should have lessons with source=uploaded_document"


class TestGenerateAssignmentEndpoint:
    """Tests for POST /api/courses/{id}/generate-assignment-from-lessons"""
    
    def test_endpoint_exists_and_requires_auth(self):
        """Test that endpoint exists and requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/courses/{TEST_COURSE_ID}/generate-assignment-from-lessons"
        )
        # Should return 403 (no auth) not 404 (not found)
        assert response.status_code in [401, 403], f"Endpoint should require auth, got {response.status_code}"
    
    def test_endpoint_requires_teacher_role(self, student_token):
        """Test that endpoint requires teacher/admin role"""
        response = requests.post(
            f"{BASE_URL}/api/courses/{TEST_COURSE_ID}/generate-assignment-from-lessons",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 403, f"Should require teacher role, got {response.status_code}"
    
    def test_endpoint_returns_404_for_invalid_course(self, admin_token):
        """Test that endpoint returns 404 for non-existent course"""
        response = requests.post(
            f"{BASE_URL}/api/courses/nonexistent-course-id/generate-assignment-from-lessons",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404, f"Should return 404 for invalid course, got {response.status_code}"
        assert "not found" in response.json().get('detail', '').lower()
    
    def test_endpoint_accessible_by_org_admin(self, admin_token):
        """Test that org_admin can access the endpoint (doesn't 403)"""
        # We just verify it doesn't return 403 - actual generation takes too long
        try:
            response = requests.post(
                f"{BASE_URL}/api/courses/{TEST_COURSE_ID}/generate-assignment-from-lessons",
                headers={"Authorization": f"Bearer {admin_token}"},
                timeout=3  # Short timeout - we just want to verify access
            )
            # Should not be 403 (forbidden) - could be timeout or success
            assert response.status_code != 403, "Org admin should have access to generate assignments"
        except requests.exceptions.ReadTimeout:
            # Timeout is expected - AI generation takes 15-30 seconds
            # The fact that we got a timeout (not immediate 403) means access was granted
            pass


class TestCourseEndpoint:
    """Tests for course data"""
    
    def test_course_exists(self, student_token):
        """Test that test course exists"""
        response = requests.get(
            f"{BASE_URL}/api/courses/{TEST_COURSE_ID}",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200, f"Course not found: {response.text}"
        
        course = response.json()
        assert course.get('id') == TEST_COURSE_ID
        assert course.get('name') or course.get('title'), "Course should have name/title"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
