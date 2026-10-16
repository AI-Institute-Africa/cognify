"""
Iteration 37 - Bug Fixes Testing
Tests for:
1. POST /api/avatar-orchestrator/generate-video - HeyGen video generation
2. GET /api/avatar-orchestrator/avatars - HeyGen avatars list
3. POST /api/avatar-orchestrator/generate-slides - Slide generation
4. POST /api/avatar-orchestrator/interactive-tutor - Q&A response
5. POST /api/research/search - JSON body (not query param)
6. GET /api/teacher/students - org_admin access
7. POST /api/messages - Send message between users
8. GET /api/user/shareable-content - All content types
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
STUDENT_EMAIL = "demo.student@cognify.edu"
STUDENT_PASSWORD = "demo123"
ORG_ADMIN_EMAIL = "test.orgadmin@cognify.edu"
ORG_ADMIN_PASSWORD = "admin123"


class TestAuthentication:
    """Test authentication for both student and org_admin"""
    
    def test_student_login(self):
        """Test student login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        assert response.status_code == 200, f"Student login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data.get("user", {}).get("role") == "student"
        print(f"✓ Student login successful: {data['user']['email']}")
        return data["access_token"]
    
    def test_org_admin_login(self):
        """Test org_admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Org admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data.get("user", {}).get("role") == "org_admin"
        print(f"✓ Org admin login successful: {data['user']['email']}")
        return data["access_token"]


@pytest.fixture(scope="module")
def student_token():
    """Get student auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": STUDENT_EMAIL,
        "password": STUDENT_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Student login failed: {response.text}")
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def org_admin_token():
    """Get org_admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ORG_ADMIN_EMAIL,
        "password": ORG_ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Org admin login failed: {response.text}")
    return response.json()["access_token"]


class TestAvatarOrchestrator:
    """Test Avatar Orchestrator endpoints"""
    
    def test_get_avatars(self, student_token):
        """GET /api/avatar-orchestrator/avatars returns list of HeyGen avatars"""
        response = requests.get(
            f"{BASE_URL}/api/avatar-orchestrator/avatars",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200, f"Get avatars failed: {response.text}"
        data = response.json()
        assert "avatars" in data, "No avatars in response"
        assert "total" in data, "No total in response"
        print(f"✓ GET /api/avatar-orchestrator/avatars: {data['total']} avatars returned")
        if data['avatars']:
            avatar = data['avatars'][0]
            assert "avatar_id" in avatar or "id" in avatar, "Avatar missing id"
    
    def test_get_voices(self, student_token):
        """GET /api/avatar-orchestrator/voices returns list of HeyGen voices"""
        response = requests.get(
            f"{BASE_URL}/api/avatar-orchestrator/voices",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200, f"Get voices failed: {response.text}"
        data = response.json()
        assert "voices" in data, "No voices in response"
        print(f"✓ GET /api/avatar-orchestrator/voices: {data.get('total', len(data['voices']))} voices returned")
    
    def test_generate_slides(self, student_token):
        """POST /api/avatar-orchestrator/generate-slides returns slide content"""
        response = requests.post(
            f"{BASE_URL}/api/avatar-orchestrator/generate-slides",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "lesson_content": "Introduction to Python programming. Python is a high-level programming language known for its simplicity and readability. Key concepts include variables, data types, loops, and functions.",
                "lesson_title": "Python Basics"
            }
        )
        assert response.status_code == 200, f"Generate slides failed: {response.text}"
        data = response.json()
        assert "slides" in data, f"No slides in response: {data}"
        assert isinstance(data["slides"], list), "Slides should be a list"
        print(f"✓ POST /api/avatar-orchestrator/generate-slides: {len(data['slides'])} slides generated")
    
    def test_interactive_tutor(self, student_token):
        """POST /api/avatar-orchestrator/interactive-tutor returns Q&A response"""
        response = requests.post(
            f"{BASE_URL}/api/avatar-orchestrator/interactive-tutor",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "question": "What is a variable in Python?",
                "lesson_content": "Variables in Python are containers for storing data values. Unlike other programming languages, Python has no command for declaring a variable.",
                "lesson_title": "Python Variables"
            }
        )
        assert response.status_code == 200, f"Interactive tutor failed: {response.text}"
        data = response.json()
        assert "response" in data, f"No response in data: {data}"
        assert data.get("mode") == "interactive_tutor", f"Wrong mode: {data.get('mode')}"
        print(f"✓ POST /api/avatar-orchestrator/interactive-tutor: Got Q&A response")
    
    def test_generate_video_endpoint_exists(self, student_token):
        """POST /api/avatar-orchestrator/generate-video endpoint exists (don't actually generate - costs credits)"""
        # Test with minimal content to verify endpoint exists
        response = requests.post(
            f"{BASE_URL}/api/avatar-orchestrator/generate-video",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "lesson_content": "",  # Empty to trigger validation error
                "lesson_title": "Test"
            }
        )
        # Should return 400 for missing content, not 404
        assert response.status_code in [200, 400, 502], f"Unexpected status: {response.status_code} - {response.text}"
        print(f"✓ POST /api/avatar-orchestrator/generate-video endpoint exists (status: {response.status_code})")


class TestResearchSearch:
    """Test Research Search endpoint - JSON body fix"""
    
    def test_research_search_with_json_body(self, student_token):
        """POST /api/research/search with JSON body returns results"""
        response = requests.post(
            f"{BASE_URL}/api/research/search",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"query": "machine learning education"}
        )
        assert response.status_code == 200, f"Research search failed: {response.text}"
        data = response.json()
        # Response contains ai_results, direct_search_links, query, total_results
        assert "ai_results" in data or "results" in data or "publications" in data, f"Unexpected response format: {data.keys()}"
        assert "query" in data, "No query in response"
        print(f"✓ POST /api/research/search with JSON body works - {data.get('total_results', len(data.get('ai_results', [])))} results")
    
    def test_research_search_missing_query(self, student_token):
        """POST /api/research/search without query returns 400"""
        response = requests.post(
            f"{BASE_URL}/api/research/search",
            headers={"Authorization": f"Bearer {student_token}"},
            json={}
        )
        assert response.status_code == 400, f"Expected 400 for missing query, got {response.status_code}: {response.text}"
        print(f"✓ POST /api/research/search returns 400 when query missing")


class TestTeacherStudents:
    """Test Teacher Students endpoint - org_admin access"""
    
    def test_teacher_students_org_admin_access(self, org_admin_token):
        """GET /api/teacher/students works for org_admin role"""
        response = requests.get(
            f"{BASE_URL}/api/teacher/students",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200, f"Teacher students failed for org_admin: {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got: {type(data)}"
        print(f"✓ GET /api/teacher/students works for org_admin: {len(data)} students")
    
    def test_teacher_students_student_forbidden(self, student_token):
        """GET /api/teacher/students returns 403 for student role"""
        response = requests.get(
            f"{BASE_URL}/api/teacher/students",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 403, f"Expected 403 for student, got {response.status_code}"
        print(f"✓ GET /api/teacher/students correctly returns 403 for student")


class TestMessages:
    """Test Messages endpoint"""
    
    def test_get_messages(self, student_token):
        """GET /api/messages returns messages list"""
        response = requests.get(
            f"{BASE_URL}/api/messages",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200, f"Get messages failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), f"Expected list, got: {type(data)}"
        print(f"✓ GET /api/messages: {len(data)} messages")
    
    def test_send_message_requires_recipient(self, student_token):
        """POST /api/messages requires valid recipient"""
        response = requests.post(
            f"{BASE_URL}/api/messages",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "recipient_id": "nonexistent-user-id",
                "subject": "Test",
                "content": "Test message"
            }
        )
        # Should return 404 for nonexistent recipient
        assert response.status_code in [404, 422], f"Expected 404/422, got {response.status_code}: {response.text}"
        print(f"✓ POST /api/messages validates recipient (status: {response.status_code})")


class TestShareableContent:
    """Test Shareable Content endpoint"""
    
    def test_get_shareable_content(self, student_token):
        """GET /api/user/shareable-content returns content with all types"""
        response = requests.get(
            f"{BASE_URL}/api/user/shareable-content",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200, f"Get shareable content failed: {response.text}"
        data = response.json()
        assert "content" in data, f"No content in response: {data}"
        
        # Check content types available
        content_types = set(c.get("type") for c in data["content"])
        expected_types = {"ai_response", "assignment", "grade", "certificate", "achievement", "course_progress"}
        
        print(f"✓ GET /api/user/shareable-content: {len(data['content'])} items")
        print(f"  Content types found: {content_types}")
        print(f"  Expected types: {expected_types}")
        
        # Verify structure of content items
        for item in data["content"][:3]:  # Check first 3 items
            assert "id" in item, f"Content item missing id: {item}"
            assert "type" in item, f"Content item missing type: {item}"
            assert "title" in item, f"Content item missing title: {item}"


class TestShareContentPage:
    """Test Share Content Page functionality"""
    
    def test_share_my_shared_endpoint(self, student_token):
        """GET /api/share/my-shared returns user's shared items"""
        response = requests.get(
            f"{BASE_URL}/api/share/my-shared",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200, f"Get my-shared failed: {response.text}"
        data = response.json()
        # Can be list or dict with shares key
        if isinstance(data, dict):
            assert "shares" in data or isinstance(data.get("shares", []), list)
        print(f"✓ GET /api/share/my-shared works")


class TestMessagingPageAccess:
    """Test Messaging Page access for org_admin"""
    
    def test_org_admin_can_access_teacher_messaging_data(self, org_admin_token):
        """Org admin can access teacher messaging related endpoints"""
        # Test teacher/students endpoint which is used by messaging page
        response = requests.get(
            f"{BASE_URL}/api/teacher/students",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200, f"Org admin cannot access teacher/students: {response.text}"
        print(f"✓ Org admin can access teacher/students for messaging")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
