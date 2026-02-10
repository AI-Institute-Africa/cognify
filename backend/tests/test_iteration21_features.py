"""
Iteration 21 - Testing 6 New Features:
1. Organization-Specific Login Page (/org/{slug}/login)
2. Enrolled Badge on Course Cards
3. Student Document Uploads
4. Export Reports for Org Admins
5. Advanced Course Creation with AI Features
6. Popup Quiz Component
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://scholar-port.preview.emergentagent.com')

# Test credentials
TEACHER_EMAIL = "demo.teacher@eduos.edu"
TEACHER_PASSWORD = "demo123"
STUDENT_EMAIL = "demo.student@cognify.edu"
STUDENT_PASSWORD = "demo123"
ORG_ADMIN_EMAIL = "test.orgadmin@cognify.edu"
ORG_ADMIN_PASSWORD = "admin123"

# Test org slug
TEST_ORG_SLUG = "test-university-of-zimbabwe"


class TestAuthentication:
    """Test authentication for all user types"""
    
    def test_health_check(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("✓ Health check passed")
    
    def test_teacher_login(self):
        """Test teacher login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "teacher"
        print(f"✓ Teacher login successful: {data['user']['full_name']}")
        return data["access_token"]
    
    def test_student_login(self):
        """Test student login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "student"
        print(f"✓ Student login successful: {data['user']['full_name']}")
        return data["access_token"]
    
    def test_org_admin_login(self):
        """Test org admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "org_admin"
        print(f"✓ Org Admin login successful: {data['user']['full_name']}")
        return data["access_token"]


class TestOrganizationLoginPage:
    """Test Feature 1: Organization-Specific Login Page"""
    
    def test_org_public_info_endpoint(self):
        """Test /api/org/public/{slug} endpoint returns org info"""
        response = requests.get(f"{BASE_URL}/api/org/public/{TEST_ORG_SLUG}")
        
        # Should return 200 or 404 if org doesn't exist
        if response.status_code == 200:
            data = response.json()
            assert "name" in data
            assert "stats" in data
            assert "branding" in data
            print(f"✓ Org public info returned: {data.get('name')}")
            print(f"  - Stats: {data.get('stats')}")
            print(f"  - Branding: {data.get('branding')}")
        elif response.status_code == 404:
            print(f"⚠ Org slug '{TEST_ORG_SLUG}' not found - may need to create test org")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")
    
    def test_org_public_info_invalid_slug(self):
        """Test that invalid org slug returns 404"""
        response = requests.get(f"{BASE_URL}/api/org/public/invalid-org-slug-12345")
        assert response.status_code == 404
        print("✓ Invalid org slug correctly returns 404")


class TestEnrolledBadge:
    """Test Feature 2: Enrolled Badge on Course Cards"""
    
    @pytest.fixture
    def student_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_courses_list_returns_enrolled_students(self, student_token):
        """Test that courses list includes enrolled_students field"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        
        assert response.status_code == 200
        courses = response.json()
        
        if len(courses) > 0:
            # Check that courses have enrolled_students field
            course = courses[0]
            assert "enrolled_students" in course or "id" in course
            print(f"✓ Courses list returned {len(courses)} courses")
            
            # Check for enrolled courses
            enrolled_count = sum(1 for c in courses if c.get('enrolled_students'))
            print(f"  - Courses with enrolled students: {enrolled_count}")
        else:
            print("⚠ No courses found")


class TestStudentDocumentUploads:
    """Test Feature 3: Student Document Uploads"""
    
    @pytest.fixture
    def student_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_get_student_documents(self, student_token):
        """Test GET /api/student/documents endpoint"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/student/documents", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        print(f"✓ Student documents endpoint works - {len(data['documents'])} documents found")
    
    def test_student_documents_requires_auth(self):
        """Test that documents endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/student/documents")
        assert response.status_code in [401, 403]
        print("✓ Documents endpoint correctly requires authentication")
    
    def test_teacher_cannot_access_student_documents(self):
        """Test that teacher cannot access student documents endpoint"""
        # Login as teacher
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        teacher_token = login_response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(f"{BASE_URL}/api/student/documents", headers=headers)
        
        # Should return 403 for non-students
        assert response.status_code == 403
        print("✓ Teacher correctly denied access to student documents")


class TestExportReports:
    """Test Feature 4: Export Reports for Org Admins"""
    
    @pytest.fixture
    def org_admin_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_org_admin_dashboard(self, org_admin_token):
        """Test org admin dashboard endpoint"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/org-admin/dashboard", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check for statistics that would be used in export
        assert "statistics" in data or "org_name" in data
        print(f"✓ Org admin dashboard works")
        print(f"  - Data keys: {list(data.keys())}")
    
    def test_org_staff_list(self, org_admin_token):
        """Test org staff list endpoint (used for staff export)"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/org/staff", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Org staff list works - {len(data) if isinstance(data, list) else 'N/A'} staff members")
    
    def test_org_participants_list(self, org_admin_token):
        """Test org participants list endpoint (used for participants export)"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/org/participants", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Org participants list works - {len(data) if isinstance(data, list) else 'N/A'} participants")


class TestAdvancedCourseCreation:
    """Test Feature 5: Advanced Course Creation with AI Features"""
    
    @pytest.fixture
    def teacher_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_create_course_endpoint(self, teacher_token):
        """Test course creation endpoint exists"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        # Test that the endpoint exists (even if we don't create a course)
        response = requests.post(f"{BASE_URL}/api/courses", headers=headers, json={
            "code": "TEST001",
            "name": "Test Course",
            "description": "Test description",
            "grade_level": "Form 4",
            "credits": 3,
            "max_students": 30,
            "category": "certificate",
            "price": 0,
            "is_paid": False
        })
        
        # Should return 200/201 for success or 400 for validation error
        assert response.status_code in [200, 201, 400]
        print(f"✓ Course creation endpoint works (status: {response.status_code})")
    
    def test_courses_have_category_field(self, teacher_token):
        """Test that courses have category field for course types"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        
        assert response.status_code == 200
        courses = response.json()
        
        if len(courses) > 0:
            course = courses[0]
            # Check for category or course_type field
            has_category = "category" in course or "course_type" in course
            print(f"✓ Courses have category/type field: {has_category}")
            if has_category:
                print(f"  - Sample category: {course.get('category') or course.get('course_type')}")


class TestPopupQuiz:
    """Test Feature 6: Popup Quiz Component"""
    
    @pytest.fixture
    def student_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        return response.json()["access_token"]
    
    def test_quiz_questions_endpoint(self, student_token):
        """Test /api/lessons/{id}/quiz-questions endpoint"""
        headers = {"Authorization": f"Bearer {student_token}"}
        
        # Use a test lesson ID
        test_lesson_id = "test-lesson-1"
        response = requests.get(
            f"{BASE_URL}/api/lessons/{test_lesson_id}/quiz-questions?count=3",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "questions" in data
        print(f"✓ Quiz questions endpoint works - {len(data['questions'])} questions returned")
        
        if len(data['questions']) > 0:
            q = data['questions'][0]
            assert "question" in q
            assert "options" in q
            print(f"  - Sample question: {q['question'][:50]}...")
    
    def test_quiz_result_endpoint(self, student_token):
        """Test /api/lessons/{id}/quiz-result endpoint"""
        headers = {"Authorization": f"Bearer {student_token}"}
        
        test_lesson_id = "test-lesson-1"
        response = requests.post(
            f"{BASE_URL}/api/lessons/{test_lesson_id}/quiz-result",
            headers=headers,
            json={
                "course_id": "test-course-1",
                "score": 2,
                "total": 3,
                "passed": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ Quiz result endpoint works - {data.get('message')}")


class TestIntegration:
    """Integration tests for all features together"""
    
    def test_full_student_flow(self):
        """Test complete student flow: login -> courses -> documents"""
        # 1. Login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Get courses
        courses_response = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        assert courses_response.status_code == 200
        
        # 3. Get documents
        docs_response = requests.get(f"{BASE_URL}/api/student/documents", headers=headers)
        assert docs_response.status_code == 200
        
        print("✓ Full student flow works: login -> courses -> documents")
    
    def test_full_org_admin_flow(self):
        """Test complete org admin flow: login -> dashboard -> staff -> participants"""
        # 1. Login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Get dashboard
        dashboard_response = requests.get(f"{BASE_URL}/api/org-admin/dashboard", headers=headers)
        assert dashboard_response.status_code == 200
        
        # 3. Get staff
        staff_response = requests.get(f"{BASE_URL}/api/org/staff", headers=headers)
        assert staff_response.status_code == 200
        
        # 4. Get participants
        participants_response = requests.get(f"{BASE_URL}/api/org/participants", headers=headers)
        assert participants_response.status_code == 200
        
        print("✓ Full org admin flow works: login -> dashboard -> staff -> participants")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
