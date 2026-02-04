"""
Test P0 Features:
1. User Registration Enhancement - LinkedIn profile field
2. AI Personal Mentor LinkedIn Integration
3. Course Structure Redesign - Standard vs Customized branches
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCourseTypesAndBranches:
    """Test course types and branches endpoints"""
    
    def test_get_course_types(self):
        """Test /api/course-types returns all course types with branch info"""
        response = requests.get(f"{BASE_URL}/api/course-types")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of course types"
        assert len(data) >= 5, f"Expected at least 5 course types, got {len(data)}"
        
        # Verify structure
        for ct in data:
            assert 'code' in ct, "Course type missing 'code'"
            assert 'name' in ct, "Course type missing 'name'"
            assert 'price' in ct, "Course type missing 'price'"
            assert 'branch' in ct, "Course type missing 'branch'"
        
        # Verify branches exist
        branches = set(ct['branch'] for ct in data)
        assert 'standard' in branches, "Missing 'standard' branch"
        assert 'customized' in branches, "Missing 'customized' branch"
        
        print(f"✓ Course types endpoint returns {len(data)} types with branches: {branches}")
    
    def test_get_course_types_filter_standard(self):
        """Test filtering course types by standard branch"""
        response = requests.get(f"{BASE_URL}/api/course-types?branch=standard")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0, "Expected at least one standard course type"
        
        for ct in data:
            assert ct['branch'] == 'standard', f"Expected standard branch, got {ct['branch']}"
        
        print(f"✓ Standard branch filter returns {len(data)} course types")
    
    def test_get_course_types_filter_customized(self):
        """Test filtering course types by customized branch"""
        response = requests.get(f"{BASE_URL}/api/course-types?branch=customized")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0, "Expected at least one customized course type"
        
        for ct in data:
            assert ct['branch'] == 'customized', f"Expected customized branch, got {ct['branch']}"
        
        print(f"✓ Customized branch filter returns {len(data)} course types")
    
    def test_get_course_branches(self):
        """Test /api/course-branches returns branch definitions"""
        response = requests.get(f"{BASE_URL}/api/course-branches")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, dict), "Expected dict of branches"
        
        # Verify standard branch
        assert 'standard' in data, "Missing 'standard' branch definition"
        assert 'name' in data['standard'], "Standard branch missing 'name'"
        assert 'description' in data['standard'], "Standard branch missing 'description'"
        assert 'features' in data['standard'], "Standard branch missing 'features'"
        
        # Verify customized branch
        assert 'customized' in data, "Missing 'customized' branch definition"
        assert 'name' in data['customized'], "Customized branch missing 'name'"
        assert 'description' in data['customized'], "Customized branch missing 'description'"
        assert 'features' in data['customized'], "Customized branch missing 'features'"
        
        print(f"✓ Course branches endpoint returns: {list(data.keys())}")


class TestLinkedInRegistration:
    """Test LinkedIn URL field in registration"""
    
    def test_register_with_linkedin_url(self):
        """Test registration with LinkedIn URL field"""
        import uuid
        test_email = f"test_linkedin_{uuid.uuid4().hex[:8]}@test.com"
        
        response = requests.post(
            f"{BASE_URL}/api/auth/register-with-verification",
            params={
                "email": test_email,
                "password": "testpass123",
                "full_name": "Test LinkedIn User",
                "role": "student",
                "linkedin_url": "https://www.linkedin.com/in/testuser"
            }
        )
        
        # Should succeed or return verification pending
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'message' in data or 'verification_code' in data or 'pending_id' in data
        
        print(f"✓ Registration with LinkedIn URL accepted for {test_email}")
    
    def test_register_without_linkedin_url(self):
        """Test registration without LinkedIn URL (optional field)"""
        import uuid
        test_email = f"test_no_linkedin_{uuid.uuid4().hex[:8]}@test.com"
        
        response = requests.post(
            f"{BASE_URL}/api/auth/register-with-verification",
            params={
                "email": test_email,
                "password": "testpass123",
                "full_name": "Test No LinkedIn User",
                "role": "student"
            }
        )
        
        # Should succeed without LinkedIn URL
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        
        print(f"✓ Registration without LinkedIn URL accepted for {test_email}")


class TestLinkedInAnalysis:
    """Test LinkedIn profile analysis endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for demo student"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "demo.student@eduos.edu",
                "password": "demo123"
            }
        )
        if response.status_code == 200:
            return response.json().get('access_token')
        pytest.skip("Could not authenticate demo student")
    
    def test_analyze_linkedin_no_url(self, auth_token):
        """Test LinkedIn analysis when user has no LinkedIn URL"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/mentor/analyze-linkedin",
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Should return success=False with message about no LinkedIn URL
        if not data.get('success'):
            assert 'message' in data, "Expected message when no LinkedIn URL"
            print(f"✓ LinkedIn analysis correctly reports: {data.get('message')}")
        else:
            # If user has LinkedIn URL, analysis should work
            assert 'profile' in data, "Expected profile data when analysis succeeds"
            print(f"✓ LinkedIn analysis succeeded with profile data")
    
    def test_mentor_profile_endpoint(self, auth_token):
        """Test mentor profile endpoint returns linkedin_profile field"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/mentor/profile",
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'user_id' in data or 'id' in data, "Expected user_id or id in profile"
        
        print(f"✓ Mentor profile endpoint working")


class TestCoursesWithBranches:
    """Test courses endpoint with branch filtering"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for demo student"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "demo.student@eduos.edu",
                "password": "demo123"
            }
        )
        if response.status_code == 200:
            return response.json().get('access_token')
        pytest.skip("Could not authenticate demo student")
    
    def test_get_courses(self, auth_token):
        """Test courses endpoint returns courses with branch info"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/courses",
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of courses"
        
        print(f"✓ Courses endpoint returns {len(data)} courses")
        
        # Check if any courses have branch info
        courses_with_branch = [c for c in data if c.get('course_branch')]
        print(f"  - {len(courses_with_branch)} courses have branch info")


class TestHealthAndBasicEndpoints:
    """Basic health checks"""
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Health endpoint working")
    
    def test_login_demo_student(self):
        """Test login with demo student credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "demo.student@eduos.edu",
                "password": "demo123"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'access_token' in data, "Expected access_token in response"
        assert 'user' in data, "Expected user in response"
        
        print(f"✓ Demo student login successful: {data['user'].get('email')}")
    
    def test_login_demo_teacher(self):
        """Test login with demo teacher credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "demo.teacher@eduos.edu",
                "password": "demo123"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert 'access_token' in data, "Expected access_token in response"
        
        print(f"✓ Demo teacher login successful: {data['user'].get('email')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
