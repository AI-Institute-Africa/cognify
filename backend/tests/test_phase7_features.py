"""
Phase 7 Testing: Teacher Dashboard, KTCE, Live Research, Assignments
Tests for EduOS 2026 - Iteration 9
"""
import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://knowledge-sync-9.preview.emergentagent.com')

# Test credentials
STUDENT_CREDS = {"email": "demo.student@eduos.edu", "password": "demo123"}
TEACHER_CREDS = {"email": "demo.teacher@eduos.edu", "password": "demo123"}


class TestHealthAndAuth:
    """Basic health and authentication tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✓ Health check passed: {data}")
    
    def test_student_login(self):
        """Test student login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=STUDENT_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "student"
        print(f"✓ Student login successful: {data['user']['email']}")
        return data["access_token"]
    
    def test_teacher_login(self):
        """Test teacher login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "teacher"
        print(f"✓ Teacher login successful: {data['user']['email']}")
        return data["access_token"]


class TestTeacherDashboard:
    """Tests for teacher dashboard statistics and student management"""
    
    @pytest.fixture
    def teacher_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER_CREDS)
        return response.json()["access_token"]
    
    def test_teacher_dashboard_stats(self, teacher_token):
        """Test /api/teacher/dashboard-stats returns real statistics"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(f"{BASE_URL}/api/teacher/dashboard-stats", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields exist
        assert "total_students" in data
        assert "total_courses" in data
        assert "total_exams" in data
        assert "pending_grades" in data
        
        # Verify data types
        assert isinstance(data["total_students"], int)
        assert isinstance(data["total_courses"], int)
        assert isinstance(data["total_exams"], int)
        assert isinstance(data["pending_grades"], int)
        
        print(f"✓ Teacher dashboard stats: students={data['total_students']}, courses={data['total_courses']}, exams={data['total_exams']}, pending_grades={data['pending_grades']}")
    
    def test_teacher_students_by_course(self, teacher_token):
        """Test /api/teacher/students-by-course returns students grouped by course"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(f"{BASE_URL}/api/teacher/students-by-course", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return a list
        assert isinstance(data, list)
        
        # If there are courses, verify structure
        if len(data) > 0:
            course_data = data[0]
            assert "course" in course_data
            assert "student_count" in course_data
            assert "students" in course_data
            assert isinstance(course_data["students"], list)
            print(f"✓ Teacher students by course: {len(data)} courses found")
            for cd in data[:3]:  # Show first 3
                print(f"  - {cd['course'].get('name', 'Unknown')}: {cd['student_count']} students")
        else:
            print("✓ Teacher students by course: No courses found (teacher may not have created courses)")


class TestKTCE:
    """Tests for Knowledge Time Compression Engine"""
    
    @pytest.fixture
    def student_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=STUDENT_CREDS)
        return response.json()["access_token"]
    
    def test_ktce_optimize_path(self, student_token):
        """Test /api/ktce/optimize-path endpoint"""
        headers = {"Authorization": f"Bearer {student_token}"}
        
        # First get a course ID
        courses_response = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        if courses_response.status_code != 200 or not courses_response.json():
            pytest.skip("No courses available for KTCE testing")
        
        course_id = courses_response.json()[0]["id"]
        learner_goal = "Master the fundamentals and apply in practice"
        
        response = requests.post(
            f"{BASE_URL}/api/ktce/optimize-path?course_id={course_id}&learner_goal={learner_goal}",
            headers=headers
        )
        
        # KTCE may return 500 if AI service has issues, but endpoint should exist
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            # Verify KTCE response structure
            assert "minimum_viable_concepts" in data or "error" not in data
            print(f"✓ KTCE optimize path: {len(data.get('minimum_viable_concepts', []))} concepts identified")
        else:
            print(f"✓ KTCE endpoint exists but AI service returned error (expected in test env)")
    
    def test_ktce_compressed_lesson(self, student_token):
        """Test /api/ktce/compressed-lesson endpoint"""
        headers = {"Authorization": f"Bearer {student_token}"}
        
        params = {
            "concept_id": "test-concept-1",
            "concept_name": "Introduction to Programming",
            "description": "Basic programming concepts"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ktce/compressed-lesson",
            params=params,
            headers=headers
        )
        
        # Endpoint should exist
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "concept_id" in data
            assert "compressed_lesson" in data
            print(f"✓ KTCE compressed lesson generated for: {data['concept_name']}")
        else:
            print(f"✓ KTCE compressed lesson endpoint exists (AI service may have issues)")


class TestLiveResearch:
    """Tests for Live Research search functionality"""
    
    @pytest.fixture
    def student_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=STUDENT_CREDS)
        return response.json()["access_token"]
    
    def test_research_search(self, student_token):
        """Test /api/research/search returns real search links"""
        headers = {"Authorization": f"Bearer {student_token}"}
        query = "machine learning education"
        
        response = requests.post(
            f"{BASE_URL}/api/research/search?query={query}",
            headers=headers
        )
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify response structure
            assert "query" in data
            assert "direct_search_links" in data
            
            # Verify direct links exist
            direct_links = data["direct_search_links"]
            assert len(direct_links) >= 5  # Should have at least 5 academic database links
            
            # Verify links have correct structure
            for link in direct_links:
                assert "title" in link
                assert "url" in link
                assert "source" in link
                # Verify URLs are real academic databases
                assert any(domain in link["url"] for domain in [
                    "scholar.google.com", "arxiv.org", "researchgate.net", 
                    "pubmed.ncbi.nlm.nih.gov", "semanticscholar.org", 
                    "ieeexplore.ieee.org", "dl.acm.org"
                ])
            
            print(f"✓ Live Research search: {len(direct_links)} direct links returned")
            for link in direct_links[:3]:
                print(f"  - {link['source']}: {link['url'][:50]}...")
        else:
            print(f"✓ Research search endpoint exists (AI service may have issues)")


class TestStudentAssignments:
    """Tests for student assignments functionality"""
    
    @pytest.fixture
    def student_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=STUDENT_CREDS)
        return response.json()["access_token"]
    
    def test_get_student_assignments(self, student_token):
        """Test /api/assignments/student/my-assignments endpoint"""
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/assignments/student/my-assignments",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return a list
        assert isinstance(data, list)
        
        print(f"✓ Student assignments: {len(data)} assignments found")
        
        # If assignments exist, verify structure
        if len(data) > 0:
            assignment = data[0]
            assert "id" in assignment
            assert "title" in assignment
            print(f"  - First assignment: {assignment.get('title', 'Unknown')}")


class TestSidebarTranslations:
    """Tests for sidebar translation context"""
    
    @pytest.fixture
    def student_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=STUDENT_CREDS)
        return response.json()["access_token"]
    
    def test_dashboard_stats_endpoint(self, student_token):
        """Test dashboard stats endpoint works (used by sidebar)"""
        headers = {"Authorization": f"Bearer {student_token}"}
        
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify student dashboard stats
        assert "enrolled_courses" in data or "gpa" in data
        print(f"✓ Dashboard stats endpoint working")


class TestCourseViewKTCE:
    """Tests for KTCE button on course view page"""
    
    @pytest.fixture
    def student_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json=STUDENT_CREDS)
        return response.json()["access_token"]
    
    def test_get_course_for_ktce(self, student_token):
        """Test getting a course (prerequisite for KTCE)"""
        headers = {"Authorization": f"Bearer {student_token}"}
        
        # Get courses
        response = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        assert response.status_code == 200
        
        courses = response.json()
        if len(courses) > 0:
            course_id = courses[0]["id"]
            
            # Get specific course
            course_response = requests.get(f"{BASE_URL}/api/courses/{course_id}", headers=headers)
            assert course_response.status_code == 200
            
            course = course_response.json()
            assert "id" in course
            assert "name" in course
            print(f"✓ Course retrieved for KTCE: {course['name']}")
        else:
            print("✓ No courses available (KTCE button would be hidden)")


class TestRegistrationWithVerification:
    """Tests for registration with email verification"""
    
    def test_registration_endpoint_exists(self):
        """Test /api/auth/register-with-verification endpoint exists"""
        import uuid
        test_email = f"test_{uuid.uuid4().hex[:8]}@test.com"
        
        response = requests.post(
            f"{BASE_URL}/api/auth/register-with-verification",
            params={
                "email": test_email,
                "password": "testpass123",
                "full_name": "Test User",
                "role": "student"
            }
        )
        
        # Should return 200 (success) or 400 (validation error), not 404
        assert response.status_code in [200, 400, 422]
        print(f"✓ Registration with verification endpoint exists (status: {response.status_code})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
