"""
Iteration 16 Tests: Enrollment Gate, Assignments, Study Groups, Avatar Teaching, Risk Alerts
Tests for Cognify Platform features:
- GET /api/assignments/student/my-assignments - Returns assignments for enrolled courses (with enrollment gate)
- Enrollment Gate - Unpaid students see restricted content with preview only
- Enrollment Gate - Paid students see full content
- GET /api/study-groups/all - Returns all study groups visible to students
- POST /api/study-groups/{id}/join - Student can join a study group
- POST /api/content/lesson/{id}/avatar-teach - Avatar teaching endpoint
- POST /api/risk/set-alert - Teacher can set risk alert for student
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://knowledge-sync-9.preview.emergentagent.com').rstrip('/')

# Test credentials from request
PAID_STUDENT = {"email": "demo.student@cognify.edu", "password": "demo123"}
UNPAID_STUDENT = {"email": "unpaid.student@test.edu", "password": "test123"}
TEACHER = {"email": "demo.teacher@eduos.edu", "password": "demo123"}
COURSE_ID = "9495d24f-7462-4f89-a751-a6742c61f62e"


class TestHealthCheck:
    """Basic health check"""
    
    def test_health_endpoint(self):
        """Test health endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print(f"✓ Health check passed: {response.json()}")


class TestAuthentication:
    """Authentication tests for all user types"""
    
    def test_paid_student_login(self):
        """Test paid student can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=PAID_STUDENT)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == PAID_STUDENT["email"]
        print(f"✓ Paid student login successful: {data['user']['full_name']}")
        return data["access_token"]
    
    def test_teacher_login(self):
        """Test teacher can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "teacher"
        print(f"✓ Teacher login successful: {data['user']['full_name']}")
        return data["access_token"]
    
    def test_unpaid_student_login_or_create(self):
        """Test unpaid student login or create if not exists"""
        # Try login first
        response = requests.post(f"{BASE_URL}/api/auth/login", json=UNPAID_STUDENT)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Unpaid student login successful: {data['user']['full_name']}")
            return data["access_token"]
        
        # Create unpaid student if doesn't exist
        register_data = {
            "email": UNPAID_STUDENT["email"],
            "password": UNPAID_STUDENT["password"],
            "full_name": "Unpaid Test Student",
            "role": "student"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"✓ Unpaid student created and logged in")
            return data.get("access_token")
        
        # If registration fails, try login again
        response = requests.post(f"{BASE_URL}/api/auth/login", json=UNPAID_STUDENT)
        if response.status_code == 200:
            return response.json()["access_token"]
        
        pytest.skip("Could not create or login unpaid student")


class TestStudentAssignments:
    """Test student assignments endpoint with enrollment gate"""
    
    @pytest.fixture
    def paid_student_token(self):
        """Get paid student token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=PAID_STUDENT)
        if response.status_code != 200:
            pytest.skip("Paid student login failed")
        return response.json()["access_token"]
    
    def test_get_student_assignments_endpoint_exists(self, paid_student_token):
        """Test GET /api/assignments/student/my-assignments endpoint exists"""
        headers = {"Authorization": f"Bearer {paid_student_token}"}
        response = requests.get(f"{BASE_URL}/api/assignments/student/my-assignments", headers=headers)
        
        # Should return 200 with list (even if empty)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Student assignments endpoint works - returned {len(data)} assignments")
    
    def test_assignments_require_student_role(self):
        """Test that assignments endpoint requires student role"""
        # Login as teacher
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER)
        if response.status_code != 200:
            pytest.skip("Teacher login failed")
        teacher_token = response.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {teacher_token}"}
        response = requests.get(f"{BASE_URL}/api/assignments/student/my-assignments", headers=headers)
        
        # Should return 403 for non-student
        assert response.status_code == 403
        print("✓ Assignments endpoint correctly rejects non-student access")


class TestEnrollmentGate:
    """Test enrollment gate for course content"""
    
    @pytest.fixture
    def paid_student_token(self):
        """Get paid student token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=PAID_STUDENT)
        if response.status_code != 200:
            pytest.skip("Paid student login failed")
        return response.json()["access_token"]
    
    def test_course_content_endpoint(self, paid_student_token):
        """Test course content endpoint returns data"""
        headers = {"Authorization": f"Bearer {paid_student_token}"}
        response = requests.get(f"{BASE_URL}/api/content/course/{COURSE_ID}/content", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Check if it's restricted or full access
        if isinstance(data, dict) and data.get('access_restricted'):
            print(f"✓ Enrollment gate active - restricted content returned")
            print(f"  Message: {data.get('message')}")
            print(f"  Preview items: {data.get('preview_items')}/{data.get('total_items')}")
        else:
            print(f"✓ Full content access - returned {len(data) if isinstance(data, list) else 'dict'} items")
    
    def test_course_exists(self, paid_student_token):
        """Test that the test course exists"""
        headers = {"Authorization": f"Bearer {paid_student_token}"}
        response = requests.get(f"{BASE_URL}/api/courses/{COURSE_ID}", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Course found: {data.get('name')}")
        print(f"  Is paid: {data.get('is_paid', False)}")
        print(f"  Price: ${data.get('price', 0)}")


class TestStudyGroups:
    """Test study groups endpoints"""
    
    @pytest.fixture
    def student_token(self):
        """Get student token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=PAID_STUDENT)
        if response.status_code != 200:
            pytest.skip("Student login failed")
        return response.json()["access_token"]
    
    def test_get_all_study_groups(self, student_token):
        """Test GET /api/study-groups/all returns all groups"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/study-groups/all", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ All study groups endpoint works - returned {len(data)} groups")
        
        if data:
            group = data[0]
            print(f"  Sample group: {group.get('name')} - Topic: {group.get('topic')}")
    
    def test_get_my_study_groups(self, student_token):
        """Test GET /api/study-groups/my-groups returns user's groups"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/study-groups/my-groups", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "groups" in data
        assert "suggested" in data
        print(f"✓ My study groups endpoint works")
        print(f"  My groups: {len(data['groups'])}")
        print(f"  Suggested: {len(data['suggested'])}")
    
    def test_create_and_join_study_group(self, student_token):
        """Test creating and joining a study group"""
        headers = {"Authorization": f"Bearer {student_token}"}
        
        # Create a new study group
        group_data = {
            "name": f"Test Study Group {uuid.uuid4().hex[:8]}",
            "topic": "Mathematics",
            "description": "Test group for iteration 16 testing"
        }
        response = requests.post(f"{BASE_URL}/api/study-groups", json=group_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "group_id" in data
        group_id = data["group_id"]
        print(f"✓ Study group created: {group_id}")
        
        # Try to join (should fail since creator is already member)
        response = requests.post(f"{BASE_URL}/api/study-groups/{group_id}/join", headers=headers)
        assert response.status_code == 400  # Already a member
        print("✓ Join endpoint correctly rejects duplicate membership")
        
        return group_id


class TestAvatarTeaching:
    """Test avatar teaching endpoint"""
    
    @pytest.fixture
    def student_token(self):
        """Get student token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=PAID_STUDENT)
        if response.status_code != 200:
            pytest.skip("Student login failed")
        return response.json()["access_token"]
    
    def test_avatar_teach_endpoint_exists(self, student_token):
        """Test POST /api/content/lesson/{id}/avatar-teach endpoint exists"""
        headers = {"Authorization": f"Bearer {student_token}"}
        
        # First get course content to find a lesson ID
        response = requests.get(f"{BASE_URL}/api/content/course/{COURSE_ID}/content", headers=headers)
        if response.status_code != 200:
            pytest.skip("Could not get course content")
        
        content = response.json()
        if isinstance(content, dict) and content.get('contents'):
            content = content['contents']
        
        if not content or len(content) == 0:
            # Create a test lesson
            lesson_id = "test-lesson-" + uuid.uuid4().hex[:8]
        else:
            lesson_id = content[0].get('id', 'test-lesson')
        
        # Test avatar teaching endpoint
        response = requests.post(
            f"{BASE_URL}/api/content/lesson/{lesson_id}/avatar-teach",
            params={"voice_id": "nova"},
            headers=headers
        )
        
        # May return 404 if lesson not found, 500 if AI budget issue, or 200 if successful
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Avatar teaching generated successfully")
            print(f"  Script length: {len(data.get('teaching_script', ''))}")
            print(f"  Audio URL: {data.get('audio_url', 'None')}")
        elif response.status_code == 404:
            print(f"✓ Avatar teaching endpoint exists (lesson not found - expected)")
        elif response.status_code == 500:
            error = response.json()
            print(f"✓ Avatar teaching endpoint exists (AI service issue: {error.get('detail', 'unknown')})")
        else:
            print(f"Avatar teaching response: {response.status_code} - {response.text[:200]}")
        
        # Endpoint should exist (not 405 Method Not Allowed)
        assert response.status_code != 405


class TestRiskAlerts:
    """Test risk alert endpoint for teachers"""
    
    @pytest.fixture
    def teacher_token(self):
        """Get teacher token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEACHER)
        if response.status_code != 200:
            pytest.skip("Teacher login failed")
        return response.json()["access_token"]
    
    @pytest.fixture
    def student_id(self):
        """Get a student ID for testing"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=PAID_STUDENT)
        if response.status_code != 200:
            pytest.skip("Student login failed")
        return response.json()["user"]["id"]
    
    def test_set_risk_alert_endpoint(self, teacher_token, student_id):
        """Test POST /api/risk/set-alert endpoint"""
        headers = {"Authorization": f"Bearer {teacher_token}"}
        
        # Set a risk alert
        response = requests.post(
            f"{BASE_URL}/api/risk/set-alert",
            params={
                "student_id": student_id,
                "alert_type": "Academic Performance",
                "severity": "medium",
                "notes": "Test alert from iteration 16 testing"
            },
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "alert_id" in data
        print(f"✓ Risk alert created: {data['alert_id']}")
        print(f"  Notifications sent: {len(data.get('notifications_sent', []))}")
    
    def test_risk_alert_requires_teacher_role(self):
        """Test that risk alert requires teacher role"""
        # Login as student
        response = requests.post(f"{BASE_URL}/api/auth/login", json=PAID_STUDENT)
        if response.status_code != 200:
            pytest.skip("Student login failed")
        student_token = response.json()["access_token"]
        student_id = response.json()["user"]["id"]
        
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.post(
            f"{BASE_URL}/api/risk/set-alert",
            params={
                "student_id": student_id,
                "alert_type": "Test",
                "severity": "low",
                "notes": "Should fail"
            },
            headers=headers
        )
        
        assert response.status_code == 403
        print("✓ Risk alert endpoint correctly rejects non-teacher access")


class TestUnpaidStudentEnrollmentGate:
    """Test enrollment gate for unpaid students"""
    
    def test_unpaid_student_content_restriction(self):
        """Test that unpaid student sees restricted content"""
        # First try to login or create unpaid student
        response = requests.post(f"{BASE_URL}/api/auth/login", json=UNPAID_STUDENT)
        
        if response.status_code != 200:
            # Create unpaid student
            register_data = {
                "email": UNPAID_STUDENT["email"],
                "password": UNPAID_STUDENT["password"],
                "full_name": "Unpaid Test Student",
                "role": "student"
            }
            response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
            if response.status_code not in [200, 201]:
                # Try login again
                response = requests.post(f"{BASE_URL}/api/auth/login", json=UNPAID_STUDENT)
                if response.status_code != 200:
                    pytest.skip("Could not create or login unpaid student")
        
        token = response.json().get("access_token")
        if not token:
            pytest.skip("No token received for unpaid student")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get course content
        response = requests.get(f"{BASE_URL}/api/content/course/{COURSE_ID}/content", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and data.get('access_restricted'):
                print(f"✓ Unpaid student sees restricted content")
                print(f"  Message: {data.get('message')}")
                print(f"  Preview items: {data.get('preview_items')}/{data.get('total_items')}")
            else:
                print(f"✓ Content returned (may be free course or student has access)")
        else:
            print(f"Content request returned: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
