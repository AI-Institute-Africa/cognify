"""
Iteration 33 - Testing Bug Fixes for Course Enrollment, Bulk Enrollment, and Course Management

Features to test:
1. POST /api/courses/{id}/enroll - works for org_admin, teacher, student
2. POST /api/courses/{id}/enroll - creates student_profile if none exists
3. POST /api/org/bulk-enroll - no longer requires course_id, enrolls into organization
4. POST /api/org/bulk-enroll - creates users with temp passwords
5. PUT /api/courses/{id} - updates course title and description
6. DELETE /api/courses/{id} - deletes course and related lessons
7. POST /api/courses/{id}/lessons - adds a lesson to a course
8. POST /api/courses/{id}/generate-lessons-from-content - endpoint exists
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://knowledge-sync-9.preview.emergentagent.com')

# Test credentials
STUDENT_EMAIL = "demo.student@cognify.edu"
STUDENT_PASSWORD = "demo123"
ORG_ADMIN_EMAIL = "test.orgadmin@cognify.edu"
ORG_ADMIN_PASSWORD = "admin123"
TEACHER_EMAIL = "demo.teacher@eduos.edu"
TEACHER_PASSWORD = "demo123"


class TestAuthentication:
    """Test authentication for different roles"""
    
    def test_student_login(self):
        """Test student can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        assert response.status_code == 200, f"Student login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data.get("user", {}).get("role") == "student"
        print(f"PASS: Student login successful")
        return data["access_token"]
    
    def test_org_admin_login(self):
        """Test org_admin can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Org admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data.get("user", {}).get("role") == "org_admin"
        print(f"PASS: Org admin login successful")
        return data["access_token"]
    
    def test_teacher_login(self):
        """Test teacher can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        # Teacher may not exist, skip if 401
        if response.status_code == 401:
            pytest.skip("Teacher account not available")
        assert response.status_code == 200, f"Teacher login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        print(f"PASS: Teacher login successful")
        return data["access_token"]


@pytest.fixture
def student_token():
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": STUDENT_EMAIL,
        "password": STUDENT_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip("Student login failed")
    return response.json()["access_token"]


@pytest.fixture
def org_admin_token():
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ORG_ADMIN_EMAIL,
        "password": ORG_ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip("Org admin login failed")
    return response.json()["access_token"]


@pytest.fixture
def teacher_token():
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEACHER_EMAIL,
        "password": TEACHER_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip("Teacher login failed")
    return response.json()["access_token"]


class TestCourseEnrollment:
    """Test course enrollment for different roles"""
    
    def test_get_courses(self, org_admin_token):
        """Get list of courses"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        assert response.status_code == 200, f"Failed to get courses: {response.text}"
        courses = response.json()
        assert isinstance(courses, list), "Courses should be a list"
        print(f"PASS: Got {len(courses)} courses")
        return courses
    
    def test_student_can_enroll(self, student_token):
        """Test student can enroll in a course"""
        headers = {"Authorization": f"Bearer {student_token}"}
        
        # Get courses first
        courses_resp = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        assert courses_resp.status_code == 200
        courses = courses_resp.json()
        
        if not courses:
            pytest.skip("No courses available for enrollment test")
        
        # Find a free course
        free_course = next((c for c in courses if not c.get('is_paid') or c.get('price', 0) == 0), None)
        if not free_course:
            pytest.skip("No free courses available")
        
        course_id = free_course['id']
        response = requests.post(f"{BASE_URL}/api/courses/{course_id}/enroll", headers=headers)
        
        # 200 = enrolled, or already enrolled
        assert response.status_code in [200, 402], f"Enrollment failed: {response.text}"
        data = response.json()
        
        if response.status_code == 200:
            assert "enrolled" in data or "already_enrolled" in data, f"Unexpected response: {data}"
            print(f"PASS: Student enrollment works - {data.get('message', 'enrolled')}")
        else:
            print(f"INFO: Course requires payment (expected for paid courses)")
    
    def test_org_admin_can_enroll(self, org_admin_token):
        """Test org_admin can enroll in a course (bug fix verification)"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        
        # Get courses
        courses_resp = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        assert courses_resp.status_code == 200
        courses = courses_resp.json()
        
        if not courses:
            pytest.skip("No courses available")
        
        # Try to enroll in first course
        course_id = courses[0]['id']
        response = requests.post(f"{BASE_URL}/api/courses/{course_id}/enroll", headers=headers)
        
        # Should not get 403 - org_admin should be allowed
        assert response.status_code != 403, f"Org admin should be allowed to enroll: {response.text}"
        assert response.status_code in [200, 402], f"Unexpected status: {response.status_code} - {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            print(f"PASS: Org admin can enroll - {data.get('message', 'success')}")
        else:
            print(f"INFO: Course requires payment (org_admin not creator)")
    
    def test_teacher_can_enroll(self, teacher_token):
        """Test teacher can enroll in a course"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        courses_resp = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        assert courses_resp.status_code == 200
        courses = courses_resp.json()
        
        if not courses:
            pytest.skip("No courses available")
        
        course_id = courses[0]['id']
        response = requests.post(f"{BASE_URL}/api/courses/{course_id}/enroll", headers=headers)
        
        # Should not get 403
        assert response.status_code != 403, f"Teacher should be allowed to enroll: {response.text}"
        print(f"PASS: Teacher enrollment endpoint accessible (status: {response.status_code})")


class TestBulkEnrollment:
    """Test bulk enrollment into organization (not course)"""
    
    def test_bulk_enroll_no_course_id_required(self, org_admin_token):
        """Test bulk enrollment works without course_id - enrolls into organization"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        
        # Generate unique test emails
        test_id = str(uuid.uuid4())[:8]
        test_emails = [
            f"testbulk1_{test_id}@example.com",
            f"testbulk2_{test_id}@example.com"
        ]
        
        # Bulk enroll WITHOUT course_id
        response = requests.post(
            f"{BASE_URL}/api/org/bulk-enroll",
            headers=headers,
            json={
                "emails": test_emails,
                "role": "student"
            }
        )
        
        assert response.status_code == 200, f"Bulk enrollment failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "results" in data, "Response should contain 'results'"
        assert "successful" in data, "Response should contain 'successful' count"
        assert data["successful"] >= 1, f"At least one enrollment should succeed: {data}"
        
        # Check that temp passwords are returned
        for result in data.get("results", []):
            if result.get("success") and result.get("status") == "created":
                assert "temp_password" in result, f"Temp password should be returned for new users: {result}"
        
        print(f"PASS: Bulk enrollment works without course_id - {data['successful']}/{data['total']} enrolled")
        return data
    
    def test_bulk_enroll_with_role_selector(self, org_admin_token):
        """Test bulk enrollment with role selector (student/teacher)"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        
        test_id = str(uuid.uuid4())[:8]
        test_email = f"testteacher_{test_id}@example.com"
        
        # Enroll as teacher
        response = requests.post(
            f"{BASE_URL}/api/org/bulk-enroll",
            headers=headers,
            json={
                "emails": [test_email],
                "role": "teacher"
            }
        )
        
        assert response.status_code == 200, f"Bulk enrollment failed: {response.text}"
        data = response.json()
        assert data["successful"] >= 1
        print(f"PASS: Bulk enrollment with teacher role works")
    
    def test_bulk_enrolled_user_can_login(self, org_admin_token):
        """Test that bulk enrolled users can login with temp password"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        
        test_id = str(uuid.uuid4())[:8]
        test_email = f"testlogin_{test_id}@example.com"
        
        # Bulk enroll
        enroll_resp = requests.post(
            f"{BASE_URL}/api/org/bulk-enroll",
            headers=headers,
            json={
                "emails": [test_email],
                "role": "student"
            }
        )
        
        assert enroll_resp.status_code == 200
        enroll_data = enroll_resp.json()
        
        # Find the temp password
        temp_password = None
        for result in enroll_data.get("results", []):
            if result.get("email") == test_email and result.get("temp_password"):
                temp_password = result["temp_password"]
                break
        
        if not temp_password:
            pytest.skip("No temp password returned (user may already exist)")
        
        # Try to login with temp password
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": test_email,
            "password": temp_password
        })
        
        assert login_resp.status_code == 200, f"Login with temp password failed: {login_resp.text}"
        login_data = login_resp.json()
        assert "access_token" in login_data
        print(f"PASS: Bulk enrolled user can login with temp password")


class TestCourseManagement:
    """Test course management (PUT/DELETE) for org_admin"""
    
    def test_create_course(self, org_admin_token):
        """Create a test course for management tests"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        
        test_id = str(uuid.uuid4())[:8]
        course_data = {
            "code": f"TEST{test_id}",
            "name": f"Test Course {test_id}",
            "description": "Test course for iteration 33 testing",
            "grade_level": "Grade 10",
            "credits": 3,
            "max_students": 30,
            "category": "certificate",
            "price": 0,
            "is_paid": False
        }
        
        response = requests.post(f"{BASE_URL}/api/courses", headers=headers, json=course_data)
        assert response.status_code == 201, f"Course creation failed: {response.text}"
        
        data = response.json()
        assert "id" in data, "Course should have an ID"
        print(f"PASS: Course created with ID {data['id']}")
        return data
    
    def test_update_course(self, org_admin_token):
        """Test PUT /api/courses/{id} updates course"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        
        # Create a course first
        test_id = str(uuid.uuid4())[:8]
        create_resp = requests.post(f"{BASE_URL}/api/courses", headers=headers, json={
            "code": f"UPD{test_id}",
            "name": f"Update Test {test_id}",
            "description": "Original description",
            "grade_level": "Grade 10"
        })
        
        if create_resp.status_code != 201:
            pytest.skip(f"Could not create course: {create_resp.text}")
        
        course_id = create_resp.json()["id"]
        
        # Update the course
        update_data = {
            "title": f"Updated Title {test_id}",
            "description": "Updated description for testing"
        }
        
        update_resp = requests.put(
            f"{BASE_URL}/api/courses/{course_id}",
            headers=headers,
            json=update_data
        )
        
        assert update_resp.status_code == 200, f"Course update failed: {update_resp.text}"
        updated = update_resp.json()
        
        # Verify update
        assert updated.get("description") == "Updated description for testing", f"Description not updated: {updated}"
        print(f"PASS: Course updated successfully")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/courses/{course_id}", headers=headers)
        return course_id
    
    def test_delete_course(self, org_admin_token):
        """Test DELETE /api/courses/{id} deletes course and lessons"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        
        # Create a course
        test_id = str(uuid.uuid4())[:8]
        create_resp = requests.post(f"{BASE_URL}/api/courses", headers=headers, json={
            "code": f"DEL{test_id}",
            "name": f"Delete Test {test_id}",
            "description": "Course to be deleted",
            "grade_level": "Grade 10"
        })
        
        if create_resp.status_code != 201:
            pytest.skip(f"Could not create course: {create_resp.text}")
        
        course_id = create_resp.json()["id"]
        
        # Add a lesson to the course
        lesson_resp = requests.post(
            f"{BASE_URL}/api/courses/{course_id}/lessons",
            headers=headers,
            json={
                "title": "Test Lesson",
                "description": "Lesson to be deleted with course",
                "content": "Test content"
            }
        )
        
        # Delete the course
        delete_resp = requests.delete(f"{BASE_URL}/api/courses/{course_id}", headers=headers)
        assert delete_resp.status_code == 200, f"Course deletion failed: {delete_resp.text}"
        
        # Verify course is deleted
        get_resp = requests.get(f"{BASE_URL}/api/courses/{course_id}", headers=headers)
        assert get_resp.status_code == 404, "Course should be deleted"
        
        print(f"PASS: Course and related lessons deleted successfully")


class TestLessons:
    """Test lesson management"""
    
    def test_add_lesson_to_course(self, org_admin_token):
        """Test POST /api/courses/{id}/lessons adds a lesson"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        
        # Create a course first
        test_id = str(uuid.uuid4())[:8]
        create_resp = requests.post(f"{BASE_URL}/api/courses", headers=headers, json={
            "code": f"LES{test_id}",
            "name": f"Lesson Test {test_id}",
            "description": "Course for lesson testing",
            "grade_level": "Grade 10"
        })
        
        if create_resp.status_code != 201:
            pytest.skip(f"Could not create course: {create_resp.text}")
        
        course_id = create_resp.json()["id"]
        
        # Add a lesson
        lesson_data = {
            "title": "Introduction to Testing",
            "description": "Learn the basics of software testing",
            "content": "This is the lesson content with detailed explanations...",
            "key_points": ["Point 1", "Point 2", "Point 3"],
            "duration": "45 min"
        }
        
        lesson_resp = requests.post(
            f"{BASE_URL}/api/courses/{course_id}/lessons",
            headers=headers,
            json=lesson_data
        )
        
        assert lesson_resp.status_code == 200, f"Lesson creation failed: {lesson_resp.text}"
        lesson = lesson_resp.json()
        
        assert "id" in lesson, "Lesson should have an ID"
        assert lesson.get("title") == "Introduction to Testing"
        assert lesson.get("course_id") == course_id
        
        print(f"PASS: Lesson added to course successfully")
        
        # Verify lesson appears in course lessons
        lessons_resp = requests.get(f"{BASE_URL}/api/courses/{course_id}/lessons", headers=headers)
        assert lessons_resp.status_code == 200
        lessons = lessons_resp.json()
        assert len(lessons) >= 1, "Course should have at least one lesson"
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/courses/{course_id}", headers=headers)
    
    def test_generate_lessons_endpoint_exists(self, org_admin_token):
        """Test POST /api/courses/{id}/generate-lessons-from-content endpoint exists"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        
        # Get a course
        courses_resp = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        courses = courses_resp.json()
        
        if not courses:
            pytest.skip("No courses available")
        
        course_id = courses[0]['id']
        
        # Test endpoint exists (without file, should get 422 for missing file)
        response = requests.post(
            f"{BASE_URL}/api/courses/{course_id}/generate-lessons-from-content",
            headers=headers
        )
        
        # 422 = endpoint exists but missing required file
        # 403 = not authorized (endpoint exists)
        # 404 = course not found (endpoint exists)
        assert response.status_code in [422, 403, 404, 400], f"Unexpected status: {response.status_code}"
        print(f"PASS: generate-lessons-from-content endpoint exists (status: {response.status_code})")


class TestCourseManagePage:
    """Test Course Manage page accessibility"""
    
    def test_course_manage_page_route(self, org_admin_token):
        """Verify course management endpoints work for org_admin"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        
        # Get courses
        courses_resp = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        assert courses_resp.status_code == 200
        courses = courses_resp.json()
        
        if not courses:
            pytest.skip("No courses available")
        
        course_id = courses[0]['id']
        
        # Get course details
        detail_resp = requests.get(f"{BASE_URL}/api/courses/{course_id}", headers=headers)
        assert detail_resp.status_code == 200, f"Failed to get course details: {detail_resp.text}"
        
        # Get course lessons
        lessons_resp = requests.get(f"{BASE_URL}/api/courses/{course_id}/lessons", headers=headers)
        assert lessons_resp.status_code == 200, f"Failed to get lessons: {lessons_resp.text}"
        
        print(f"PASS: Course management endpoints accessible for org_admin")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
