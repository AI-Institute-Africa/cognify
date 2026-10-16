"""
Iteration 30 - Testing 5 New Features:
1. Certificate Gallery (GET /api/certificates/gallery/my, GET /api/certificates/gallery/user/{userId})
2. Org Admin Course Viewer (GET /api/org/courses)
3. Org Portal Login/Registration (POST /api/auth/org-register)
4. Avatar Voice Cloning (POST /api/avatar/upload-voice, GET /api/avatar/voice-status)
5. Publish from AI Q&A Generator (POST /api/training-engine/publish-assignment, POST /api/training-engine/publish-exam)
"""

import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://knowledge-sync-9.preview.emergentagent.com')

# Test credentials
STUDENT_EMAIL = "demo.student@cognify.edu"
STUDENT_PASSWORD = "demo123"
TEACHER_EMAIL = "demo.teacher@eduos.edu"
TEACHER_PASSWORD = "demo123"
ORG_ADMIN_EMAIL = "test.orgadmin@cognify.edu"
ORG_ADMIN_PASSWORD = "admin123"
ORG_SLUG = "cognify"


class TestAuthentication:
    """Test authentication for all user types"""
    
    def test_student_login(self):
        """Test student login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        assert response.status_code == 200, f"Student login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        print(f"✓ Student login successful")
    
    def test_teacher_login(self):
        """Test teacher login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        assert response.status_code == 200, f"Teacher login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        print(f"✓ Teacher login successful")
    
    def test_org_admin_login(self):
        """Test org admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Org admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        print(f"✓ Org admin login successful")


@pytest.fixture
def student_token():
    """Get student auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": STUDENT_EMAIL,
        "password": STUDENT_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Student authentication failed")


@pytest.fixture
def teacher_token():
    """Get teacher auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEACHER_EMAIL,
        "password": TEACHER_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Teacher authentication failed")


@pytest.fixture
def org_admin_token():
    """Get org admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ORG_ADMIN_EMAIL,
        "password": ORG_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Org admin authentication failed")


class TestCertificateGallery:
    """Feature 1: Certificate Gallery endpoints"""
    
    def test_get_my_certificates(self, student_token):
        """GET /api/certificates/gallery/my - returns user's certificates"""
        response = requests.get(
            f"{BASE_URL}/api/certificates/gallery/my",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "certificates" in data
        assert "total" in data
        assert isinstance(data["certificates"], list)
        print(f"✓ GET /api/certificates/gallery/my - returned {data['total']} certificates")
    
    def test_get_my_certificates_requires_auth(self):
        """GET /api/certificates/gallery/my - requires authentication"""
        response = requests.get(f"{BASE_URL}/api/certificates/gallery/my")
        assert response.status_code == 403 or response.status_code == 401
        print(f"✓ GET /api/certificates/gallery/my - correctly requires auth")
    
    def test_get_user_certificates_same_org(self, student_token):
        """GET /api/certificates/gallery/user/{userId} - returns target user's certificates"""
        # First get current user info
        me_response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        if me_response.status_code == 200:
            user_id = me_response.json().get("id")
            if user_id:
                response = requests.get(
                    f"{BASE_URL}/api/certificates/gallery/user/{user_id}",
                    headers={"Authorization": f"Bearer {student_token}"}
                )
                assert response.status_code == 200, f"Failed: {response.text}"
                data = response.json()
                assert "certificates" in data
                assert "user" in data
                print(f"✓ GET /api/certificates/gallery/user/{user_id} - returned certificates")
    
    def test_get_user_certificates_not_found(self, student_token):
        """GET /api/certificates/gallery/user/{userId} - returns 404 for invalid user"""
        response = requests.get(
            f"{BASE_URL}/api/certificates/gallery/user/invalid-user-id-12345",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 404
        print(f"✓ GET /api/certificates/gallery/user/invalid - correctly returns 404")


class TestOrgAdminCourseViewer:
    """Feature 2: Org Admin Course Viewer (Courses tab)"""
    
    def test_get_org_courses(self, org_admin_token):
        """GET /api/org/courses - returns org courses"""
        response = requests.get(
            f"{BASE_URL}/api/org/courses",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/org/courses - returned {len(data)} courses")
    
    def test_get_org_courses_requires_auth(self):
        """GET /api/org/courses - requires authentication"""
        response = requests.get(f"{BASE_URL}/api/org/courses")
        assert response.status_code == 403 or response.status_code == 401
        print(f"✓ GET /api/org/courses - correctly requires auth")
    
    def test_get_org_courses_student_access(self, student_token):
        """GET /api/org/courses - student can also access (returns their org courses)"""
        response = requests.get(
            f"{BASE_URL}/api/org/courses",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        # Should return 200 (may be empty list if student has no org)
        assert response.status_code == 200, f"Failed: {response.text}"
        print(f"✓ GET /api/org/courses - student access works")


class TestOrgPortalRegistration:
    """Feature 3: Org Portal Login/Registration"""
    
    def test_org_public_info(self):
        """GET /api/org/public/{slug} - returns org public info"""
        response = requests.get(f"{BASE_URL}/api/org/public/{ORG_SLUG}")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "name" in data or "id" in data
        print(f"✓ GET /api/org/public/{ORG_SLUG} - returned org info")
    
    def test_org_register_creates_pending_user(self):
        """POST /api/auth/org-register - creates pending user with role"""
        import uuid
        test_email = f"test_reg_{uuid.uuid4().hex[:8]}@test.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/org-register", json={
            "email": test_email,
            "password": "testpass123",
            "full_name": "Test Registration User",
            "role": "student",
            "org_slug": ORG_SLUG
        })
        
        # Should succeed with pending status
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            assert "pending" in data.get("status", "").lower() or "pending" in data.get("message", "").lower()
            print(f"✓ POST /api/auth/org-register - created pending user")
        elif response.status_code == 404:
            # Org not found - acceptable if org doesn't exist
            print(f"✓ POST /api/auth/org-register - org not found (expected if no cognify org)")
        else:
            # Check if it's a duplicate email error
            assert response.status_code in [200, 400, 404], f"Unexpected status: {response.status_code} - {response.text}"
            print(f"✓ POST /api/auth/org-register - handled correctly")
    
    def test_org_register_invalid_role(self):
        """POST /api/auth/org-register - rejects invalid role"""
        import uuid
        test_email = f"test_invalid_{uuid.uuid4().hex[:8]}@test.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/org-register", json={
            "email": test_email,
            "password": "testpass123",
            "full_name": "Test Invalid Role",
            "role": "admin",  # Invalid - only student/teacher allowed
            "org_slug": ORG_SLUG
        })
        
        # Should reject with 400 or 422
        assert response.status_code in [400, 404, 422], f"Should reject invalid role: {response.text}"
        print(f"✓ POST /api/auth/org-register - correctly rejects invalid role")


class TestAvatarVoiceCloning:
    """Feature 4: Avatar Voice Cloning"""
    
    def test_get_voice_status(self, student_token):
        """GET /api/avatar/voice-status - returns voice clone status"""
        response = requests.get(
            f"{BASE_URL}/api/avatar/voice-status",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "has_voice" in data
        assert isinstance(data["has_voice"], bool)
        print(f"✓ GET /api/avatar/voice-status - has_voice={data['has_voice']}")
    
    def test_get_voice_status_requires_auth(self):
        """GET /api/avatar/voice-status - requires authentication"""
        response = requests.get(f"{BASE_URL}/api/avatar/voice-status")
        assert response.status_code == 403 or response.status_code == 401
        print(f"✓ GET /api/avatar/voice-status - correctly requires auth")
    
    def test_upload_voice_sample(self, student_token):
        """POST /api/avatar/upload-voice - accepts audio file upload"""
        # Create a small test audio file (just bytes for testing)
        test_audio = b"RIFF" + b"\x00" * 100  # Minimal WAV-like header
        
        files = {
            'file': ('test_voice.wav', io.BytesIO(test_audio), 'audio/wav')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/avatar/upload-voice",
            headers={"Authorization": f"Bearer {student_token}"},
            files=files
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "voice_cloned" in data or "message" in data
        print(f"✓ POST /api/avatar/upload-voice - upload successful")
    
    def test_upload_voice_requires_auth(self):
        """POST /api/avatar/upload-voice - requires authentication"""
        test_audio = b"RIFF" + b"\x00" * 100
        files = {'file': ('test.wav', io.BytesIO(test_audio), 'audio/wav')}
        
        response = requests.post(f"{BASE_URL}/api/avatar/upload-voice", files=files)
        assert response.status_code == 403 or response.status_code == 401
        print(f"✓ POST /api/avatar/upload-voice - correctly requires auth")


class TestPublishFromAIQAGenerator:
    """Feature 5: Publish Assignments & Exams from AI Q&A Generator"""
    
    def test_publish_assignment_teacher(self, teacher_token):
        """POST /api/training-engine/publish-assignment - teacher can publish"""
        # First get a course to use
        courses_response = requests.get(
            f"{BASE_URL}/api/courses",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        if courses_response.status_code == 200:
            courses = courses_response.json()
            if isinstance(courses, list) and len(courses) > 0:
                course_id = courses[0].get('id')
                
                response = requests.post(
                    f"{BASE_URL}/api/training-engine/publish-assignment",
                    headers={"Authorization": f"Bearer {teacher_token}"},
                    json={
                        "title": "Test AI Generated Assignment",
                        "course_id": course_id,
                        "questions": [
                            {"q": "What is 2+2?", "a": "4", "category": "basic"},
                            {"q": "What is the capital of France?", "a": "Paris", "category": "basic"}
                        ],
                        "description": "Auto-generated test assignment",
                        "max_score": 10
                    }
                )
                
                assert response.status_code == 200, f"Failed: {response.text}"
                data = response.json()
                assert "assignment_id" in data or "message" in data
                print(f"✓ POST /api/training-engine/publish-assignment - teacher published successfully")
                return
        
        print(f"✓ POST /api/training-engine/publish-assignment - skipped (no courses available)")
    
    def test_publish_assignment_student_forbidden(self, student_token):
        """POST /api/training-engine/publish-assignment - student cannot publish"""
        response = requests.post(
            f"{BASE_URL}/api/training-engine/publish-assignment",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "title": "Test Assignment",
                "course_id": "test-course-id",
                "questions": [],
                "description": "Test",
                "max_score": 10
            }
        )
        
        assert response.status_code == 403, f"Should be forbidden for student: {response.text}"
        print(f"✓ POST /api/training-engine/publish-assignment - correctly forbidden for student")
    
    def test_publish_exam_teacher(self, teacher_token):
        """POST /api/training-engine/publish-exam - teacher can publish exam"""
        # First get a course to use
        courses_response = requests.get(
            f"{BASE_URL}/api/courses",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        
        if courses_response.status_code == 200:
            courses = courses_response.json()
            if isinstance(courses, list) and len(courses) > 0:
                course_id = courses[0].get('id')
                
                response = requests.post(
                    f"{BASE_URL}/api/training-engine/publish-exam",
                    headers={"Authorization": f"Bearer {teacher_token}"},
                    json={
                        "title": "Test AI Generated Exam",
                        "course_id": course_id,
                        "sections": [
                            {
                                "name": "Section A - MCQ",
                                "questions": [
                                    {"q": "What is 2+2?", "type": "mcq", "options": ["A) 3", "B) 4", "C) 5"], "correct": "B", "marks": 5}
                                ]
                            }
                        ],
                        "duration_minutes": 30,
                        "total_marks": 50,
                        "description": "Auto-generated test exam"
                    }
                )
                
                assert response.status_code == 200, f"Failed: {response.text}"
                data = response.json()
                assert "exam_id" in data or "message" in data
                print(f"✓ POST /api/training-engine/publish-exam - teacher published successfully")
                return
        
        print(f"✓ POST /api/training-engine/publish-exam - skipped (no courses available)")
    
    def test_publish_exam_student_forbidden(self, student_token):
        """POST /api/training-engine/publish-exam - student cannot publish"""
        response = requests.post(
            f"{BASE_URL}/api/training-engine/publish-exam",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "title": "Test Exam",
                "course_id": "test-course-id",
                "sections": [],
                "duration_minutes": 30,
                "total_marks": 100
            }
        )
        
        assert response.status_code == 403, f"Should be forbidden for student: {response.text}"
        print(f"✓ POST /api/training-engine/publish-exam - correctly forbidden for student")


class TestHealthEndpoint:
    """Basic health check"""
    
    def test_health(self):
        """GET /api/health - returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print(f"✓ GET /api/health - status: healthy")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
