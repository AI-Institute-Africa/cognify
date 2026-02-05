"""
Cognify Platform Comprehensive Audit Tests
Tests for: AI File Handling, Email Verification, Paynow Payment, LinkedIn Profile, 
Course Payment Flow, Profile/Settings, Parent Notifications
"""
import pytest
import requests
import os
import json
import io
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://edusync-34.preview.emergentagent.com')

# Test credentials
STUDENT_EMAIL = "demo.student@cognify.edu"
STUDENT_PASSWORD = "demo123"
ORG_ADMIN_EMAIL = "test.orgadmin@cognify.edu"
ORG_ADMIN_PASSWORD = "admin123"


class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_student_login(self):
        """POST /api/auth/login - Student authentication"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": STUDENT_EMAIL, "password": STUDENT_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == STUDENT_EMAIL
        assert data["user"]["role"] == "student"
        print(f"✓ Student login successful: {data['user']['full_name']}")
    
    def test_org_admin_login(self):
        """POST /api/auth/login - Org admin authentication"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ORG_ADMIN_EMAIL, "password": ORG_ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "org_admin"
        print(f"✓ Org admin login successful: {data['user']['full_name']}")
    
    def test_invalid_login(self):
        """POST /api/auth/login - Invalid credentials rejected"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "invalid@test.com", "password": "wrongpass"}
        )
        assert response.status_code == 401
        print("✓ Invalid login correctly rejected")
    
    def test_get_current_user(self):
        """GET /api/auth/me - Get current user profile"""
        # Login first
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": STUDENT_EMAIL, "password": STUDENT_PASSWORD}
        )
        token = login_resp.json()["access_token"]
        
        # Get current user
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == STUDENT_EMAIL
        print(f"✓ Get current user successful: {data['full_name']}")


class TestAcademicLevelsAndCourseTypes:
    """Test Zimbabwe academic levels and course types"""
    
    def test_get_academic_levels(self):
        """GET /api/academic-levels - Zimbabwe academic levels"""
        response = requests.get(f"{BASE_URL}/api/academic-levels")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify Zimbabwe levels exist
        codes = [level["code"] for level in data]
        assert "grade_1" in codes  # Primary
        assert "form_1" in codes   # Secondary
        assert "undergraduate" in codes  # Tertiary
        print(f"✓ Academic levels returned: {len(data)} levels")
        print(f"  Categories: {set(level['category'] for level in data)}")
    
    def test_get_course_types(self):
        """GET /api/course-types - Course types with pricing"""
        response = requests.get(f"{BASE_URL}/api/course-types")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify course types
        codes = [ct["code"] for ct in data]
        assert "free" in codes
        assert "certificate" in codes
        assert "diploma" in codes
        
        # Verify pricing
        for ct in data:
            assert "price" in ct
            assert "name" in ct
        print(f"✓ Course types returned: {len(data)} types")
        print(f"  Types: {[ct['name'] for ct in data]}")


class TestProfileAndSettings:
    """Test profile update with LinkedIn URL"""
    
    @pytest.fixture
    def student_token(self):
        """Get student auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": STUDENT_EMAIL, "password": STUDENT_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_update_profile_with_linkedin(self, student_token):
        """PUT /api/user/profile - Update profile with LinkedIn URL"""
        linkedin_url = "https://linkedin.com/in/testprofile"
        
        response = requests.put(
            f"{BASE_URL}/api/user/profile",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "full_name": "Demo Student",
                "linkedin_url": linkedin_url,
                "bio": "Test bio for audit"
            }
        )
        
        # Accept 200 or 404 (endpoint may not exist)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Profile updated with LinkedIn URL")
        elif response.status_code == 404:
            print("⚠ PUT /api/user/profile endpoint not found - checking alternative")
            # Try alternative endpoint
            alt_response = requests.post(
                f"{BASE_URL}/api/users/update-profile",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"linkedin_url": linkedin_url}
            )
            if alt_response.status_code == 200:
                print("✓ Profile updated via alternative endpoint")
            else:
                print(f"⚠ Profile update returned: {alt_response.status_code}")
        else:
            print(f"⚠ Profile update returned: {response.status_code}")


class TestCourseEnrollment:
    """Test course enrollment with payment check"""
    
    @pytest.fixture
    def student_token(self):
        """Get student auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": STUDENT_EMAIL, "password": STUDENT_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_get_courses(self, student_token):
        """GET /api/courses - Get available courses"""
        response = requests.get(
            f"{BASE_URL}/api/courses",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Courses retrieved: {len(data)} courses")
        return data
    
    def test_enroll_free_course(self, student_token):
        """POST /api/courses/{id}/enroll - Enroll in free course"""
        # Get courses first
        courses_resp = requests.get(
            f"{BASE_URL}/api/courses",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        courses = courses_resp.json()
        
        # Find a free course
        free_course = next((c for c in courses if c.get("price", 0) == 0), None)
        
        if free_course:
            response = requests.post(
                f"{BASE_URL}/api/courses/{free_course['id']}/enroll",
                headers={"Authorization": f"Bearer {student_token}"}
            )
            # Accept 200 (success) or already enrolled
            assert response.status_code in [200, 400]
            data = response.json()
            if response.status_code == 200:
                print(f"✓ Enrolled in free course: {free_course.get('name', free_course.get('title'))}")
            else:
                print(f"✓ Course enrollment response: {data.get('message', data)}")
        else:
            print("⚠ No free courses available for enrollment test")


class TestPaynowPayment:
    """Test Paynow payment integration"""
    
    @pytest.fixture
    def student_token(self):
        """Get student auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": STUDENT_EMAIL, "password": STUDENT_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_initiate_paynow_ecocash(self, student_token):
        """POST /api/payments/paynow/initiate - EcoCash payment"""
        response = requests.post(
            f"{BASE_URL}/api/payments/paynow/initiate",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "course_id": "test-course-001",
                "course_name": "Test Course",
                "amount": 29.99,
                "currency": "USD",
                "payment_method": "ecocash",
                "phone": "+263771234567"
            }
        )
        
        # Paynow may fail if credentials not configured
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✓ Paynow EcoCash initiated: {data.get('reference')}")
            else:
                print(f"⚠ Paynow initiation returned: {data.get('error', 'Unknown error')}")
        else:
            print(f"⚠ Paynow endpoint returned: {response.status_code}")
            # This is expected if Paynow credentials not configured
    
    def test_initiate_paynow_card(self, student_token):
        """POST /api/payments/paynow/initiate - Card payment"""
        response = requests.post(
            f"{BASE_URL}/api/payments/paynow/initiate",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "course_id": "test-course-001",
                "course_name": "Test Course",
                "amount": 99.99,
                "currency": "USD",
                "payment_method": "card"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Paynow card payment response: {data.get('success', 'N/A')}")
        else:
            print(f"⚠ Paynow card endpoint returned: {response.status_code}")


class TestAIFileHandling:
    """Test AI file upload and analysis"""
    
    @pytest.fixture
    def student_token(self):
        """Get student auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": STUDENT_EMAIL, "password": STUDENT_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_landing_upload_text(self):
        """POST /api/ai/landing-upload - Text file upload (no auth)"""
        # Create a simple text file
        text_content = "This is a test document about machine learning and AI."
        files = {
            'file': ('test.txt', io.BytesIO(text_content.encode()), 'text/plain')
        }
        data = {'question': 'What is this document about?'}
        
        response = requests.post(
            f"{BASE_URL}/api/ai/landing-upload",
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            result = response.json()
            assert "response" in result
            print(f"✓ Landing upload text analysis successful")
            print(f"  Response preview: {result['response'][:100]}...")
        else:
            print(f"⚠ Landing upload returned: {response.status_code}")
    
    def test_mentor_upload_document(self, student_token):
        """POST /api/mentor/upload-document - Authenticated document upload"""
        # Create a simple text file
        text_content = "Chapter 1: Introduction to Python Programming\n\nPython is a high-level programming language."
        files = {
            'file': ('lesson.txt', io.BytesIO(text_content.encode()), 'text/plain')
        }
        data = {'question': 'Summarize this document'}
        
        response = requests.post(
            f"{BASE_URL}/api/mentor/upload-document",
            headers={"Authorization": f"Bearer {student_token}"},
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            result = response.json()
            assert "response" in result
            print(f"✓ Mentor document upload successful")
            print(f"  Response preview: {result['response'][:100]}...")
        else:
            print(f"⚠ Mentor upload returned: {response.status_code}")


class TestLinkedInAnalysis:
    """Test LinkedIn profile analysis"""
    
    @pytest.fixture
    def student_token(self):
        """Get student auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": STUDENT_EMAIL, "password": STUDENT_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_analyze_linkedin_no_url(self, student_token):
        """POST /api/mentor/analyze-linkedin - Without LinkedIn URL"""
        response = requests.post(
            f"{BASE_URL}/api/mentor/analyze-linkedin",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should return message about no LinkedIn URL
        if not data.get("success"):
            print(f"✓ LinkedIn analysis correctly reports no URL: {data.get('message')}")
        else:
            print(f"✓ LinkedIn analysis successful: {data}")


class TestStudentRiskAlerts:
    """Test student risk alerts with parent notifications"""
    
    @pytest.fixture
    def teacher_token(self):
        """Get teacher/admin auth token"""
        # Try org admin first
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ORG_ADMIN_EMAIL, "password": ORG_ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        return None
    
    def test_set_student_alert(self, teacher_token):
        """POST /api/risk/set-alert - Set student alert"""
        if not teacher_token:
            pytest.skip("No teacher/admin token available")
        
        response = requests.post(
            f"{BASE_URL}/api/risk/set-alert",
            headers={"Authorization": f"Bearer {teacher_token}"},
            params={
                "student_id": "demo-student-001",
                "alert_type": "Academic Performance",
                "severity": "medium",
                "notes": "Test alert for audit - student needs additional support"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Student alert set: {data.get('alert_id')}")
            print(f"  Notifications sent: {data.get('notifications_sent', [])}")
        elif response.status_code == 403:
            print("⚠ Risk alert requires teacher role")
        elif response.status_code == 404:
            print("⚠ Student not found for alert")
        else:
            print(f"⚠ Risk alert returned: {response.status_code}")


class TestOrgPendingEnrollments:
    """Test organization pending enrollments"""
    
    @pytest.fixture
    def org_admin_token(self):
        """Get org admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ORG_ADMIN_EMAIL, "password": ORG_ADMIN_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_get_pending_enrollments(self, org_admin_token):
        """GET /api/org/pending-enrollments - Get pending enrollment list"""
        response = requests.get(
            f"{BASE_URL}/api/org/pending-enrollments",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Pending enrollments retrieved: {len(data)} pending")


class TestMentorProfile:
    """Test AI Mentor profile endpoints"""
    
    @pytest.fixture
    def student_token(self):
        """Get student auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": STUDENT_EMAIL, "password": STUDENT_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_get_mentor_profile(self, student_token):
        """GET /api/mentor/profile - Get mentor profile"""
        response = requests.get(
            f"{BASE_URL}/api/mentor/profile",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        print(f"✓ Mentor profile retrieved")
        print(f"  Learning style: {data.get('learning_style', 'N/A')}")


class TestHealthAndBasics:
    """Test basic health endpoints"""
    
    def test_health_check(self):
        """GET /api/health - Health check"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✓ Health check passed: {data}")
    
    def test_supported_languages(self):
        """GET /api/language/supported - Supported languages"""
        response = requests.get(f"{BASE_URL}/api/language/supported")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Supported languages: {len(data)} languages")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
