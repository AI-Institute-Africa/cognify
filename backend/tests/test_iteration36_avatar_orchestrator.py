"""
Iteration 36 Tests - Avatar Learning Orchestrator & Bug Fixes
Tests for:
1. GET /api/avatar-orchestrator/avatars - returns available HeyGen avatars
2. GET /api/avatar-orchestrator/voices - returns available HeyGen voices
3. POST /api/avatar-orchestrator/generate-video - endpoint exists (don't actually generate)
4. GET /api/avatar-orchestrator/video-status/{id} - returns video status
5. POST /api/avatar-orchestrator/interactive-tutor - returns Q&A response
6. POST /api/avatar-orchestrator/generate-slides - returns slide content
7. POST /api/avatar-orchestrator/generate-assessment - returns quiz questions
8. POST /api/avatar-orchestrator/adaptive-rewrite - returns rewritten content
9. POST /api/avatar-orchestrator/translate-script - translates teaching script
10. POST /api/research/search - accepts JSON body with query field (was broken)
11. POST /api/messages - works for sending messages
12. GET /api/user/shareable-content - returns shareable content
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

# Test course
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


class TestAvatarOrchestratorAvatars:
    """Tests for GET /api/avatar-orchestrator/avatars"""
    
    def test_avatars_endpoint_requires_auth(self):
        """Test that avatars endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/avatar-orchestrator/avatars")
        assert response.status_code in [401, 403], f"Should require auth, got {response.status_code}"
    
    def test_avatars_endpoint_returns_data(self, student_token):
        """Test that avatars endpoint returns list of avatars"""
        response = requests.get(
            f"{BASE_URL}/api/avatar-orchestrator/avatars",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200, f"Avatars endpoint failed: {response.text}"
        
        data = response.json()
        assert "avatars" in data, "Response should have 'avatars' key"
        assert isinstance(data["avatars"], list), "Avatars should be a list"
        assert "total" in data, "Response should have 'total' key"
    
    def test_avatars_have_required_fields(self, student_token):
        """Test that avatars have required fields"""
        response = requests.get(
            f"{BASE_URL}/api/avatar-orchestrator/avatars",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        avatars = data.get("avatars", [])
        
        if len(avatars) > 0:
            avatar = avatars[0]
            # Should have avatar_id and avatar_name
            assert "avatar_id" in avatar or "id" in avatar, "Avatar should have avatar_id or id"
            assert "avatar_name" in avatar or "name" in avatar, "Avatar should have avatar_name or name"


class TestAvatarOrchestratorVoices:
    """Tests for GET /api/avatar-orchestrator/voices"""
    
    def test_voices_endpoint_requires_auth(self):
        """Test that voices endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/avatar-orchestrator/voices")
        assert response.status_code in [401, 403], f"Should require auth, got {response.status_code}"
    
    def test_voices_endpoint_returns_data(self, student_token):
        """Test that voices endpoint returns list of voices"""
        response = requests.get(
            f"{BASE_URL}/api/avatar-orchestrator/voices",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200, f"Voices endpoint failed: {response.text}"
        
        data = response.json()
        assert "voices" in data, "Response should have 'voices' key"
        assert isinstance(data["voices"], list), "Voices should be a list"
        assert "total" in data, "Response should have 'total' key"


class TestAvatarOrchestratorGenerateVideo:
    """Tests for POST /api/avatar-orchestrator/generate-video"""
    
    def test_generate_video_endpoint_requires_auth(self):
        """Test that generate-video endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/avatar-orchestrator/generate-video",
            json={"lesson_content": "Test content"}
        )
        assert response.status_code in [401, 403], f"Should require auth, got {response.status_code}"
    
    def test_generate_video_endpoint_exists(self, student_token):
        """Test that generate-video endpoint exists and accepts requests"""
        # We don't actually generate video (costs credits), just verify endpoint exists
        response = requests.post(
            f"{BASE_URL}/api/avatar-orchestrator/generate-video",
            headers={"Authorization": f"Bearer {student_token}"},
            json={}  # Empty body should return 400, not 404
        )
        # Should return 400 (bad request - no content) not 404 (not found)
        assert response.status_code != 404, "Endpoint should exist"
        # 400 means endpoint exists but needs content
        assert response.status_code in [400, 500, 502], f"Expected 400/500/502, got {response.status_code}"


class TestAvatarOrchestratorVideoStatus:
    """Tests for GET /api/avatar-orchestrator/video-status/{id}"""
    
    def test_video_status_endpoint_requires_auth(self):
        """Test that video-status endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/avatar-orchestrator/video-status/test-id")
        assert response.status_code in [401, 403], f"Should require auth, got {response.status_code}"
    
    def test_video_status_endpoint_exists(self, student_token):
        """Test that video-status endpoint exists"""
        response = requests.get(
            f"{BASE_URL}/api/avatar-orchestrator/video-status/nonexistent-video-id",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        # Should return 200 with status info (even for invalid ID), not 404
        assert response.status_code == 200, f"Endpoint should exist, got {response.status_code}"
        
        data = response.json()
        assert "video_id" in data, "Response should have video_id"
        assert "status" in data, "Response should have status"


class TestAvatarOrchestratorInteractiveTutor:
    """Tests for POST /api/avatar-orchestrator/interactive-tutor"""
    
    def test_interactive_tutor_requires_auth(self):
        """Test that interactive-tutor endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/avatar-orchestrator/interactive-tutor",
            json={"question": "What is this about?"}
        )
        assert response.status_code in [401, 403], f"Should require auth, got {response.status_code}"
    
    def test_interactive_tutor_requires_question(self, student_token):
        """Test that interactive-tutor requires question field"""
        response = requests.post(
            f"{BASE_URL}/api/avatar-orchestrator/interactive-tutor",
            headers={"Authorization": f"Bearer {student_token}"},
            json={}  # No question
        )
        assert response.status_code == 400, f"Should require question, got {response.status_code}"
    
    def test_interactive_tutor_returns_response(self, student_token):
        """Test that interactive-tutor returns Q&A response"""
        response = requests.post(
            f"{BASE_URL}/api/avatar-orchestrator/interactive-tutor",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "question": "What is machine learning?",
                "lesson_content": "Machine learning is a subset of AI that enables systems to learn from data.",
                "lesson_title": "Introduction to ML"
            },
            timeout=60  # AI response may take time
        )
        assert response.status_code == 200, f"Interactive tutor failed: {response.text}"
        
        data = response.json()
        assert "response" in data, "Should have response field"
        assert "mode" in data, "Should have mode field"
        assert data["mode"] == "interactive_tutor", "Mode should be interactive_tutor"


class TestAvatarOrchestratorGenerateSlides:
    """Tests for POST /api/avatar-orchestrator/generate-slides"""
    
    def test_generate_slides_requires_auth(self):
        """Test that generate-slides endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/avatar-orchestrator/generate-slides",
            json={"lesson_content": "Test content"}
        )
        assert response.status_code in [401, 403], f"Should require auth, got {response.status_code}"
    
    def test_generate_slides_requires_content(self, student_token):
        """Test that generate-slides requires lesson_content"""
        response = requests.post(
            f"{BASE_URL}/api/avatar-orchestrator/generate-slides",
            headers={"Authorization": f"Bearer {student_token}"},
            json={}  # No content
        )
        assert response.status_code == 400, f"Should require content, got {response.status_code}"
    
    def test_generate_slides_returns_slides(self, student_token):
        """Test that generate-slides returns slide content"""
        response = requests.post(
            f"{BASE_URL}/api/avatar-orchestrator/generate-slides",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "lesson_content": "Machine learning is a subset of artificial intelligence that enables systems to learn from data. Key concepts include supervised learning, unsupervised learning, and reinforcement learning.",
                "lesson_title": "Introduction to Machine Learning"
            },
            timeout=60  # AI response may take time
        )
        assert response.status_code == 200, f"Generate slides failed: {response.text}"
        
        data = response.json()
        assert "slides" in data, "Should have slides field"
        assert isinstance(data["slides"], list), "Slides should be a list"
        assert len(data["slides"]) > 0, "Should have at least one slide"


class TestAvatarOrchestratorGenerateAssessment:
    """Tests for POST /api/avatar-orchestrator/generate-assessment"""
    
    def test_generate_assessment_requires_auth(self):
        """Test that generate-assessment endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/avatar-orchestrator/generate-assessment",
            json={"lesson_content": "Test content"}
        )
        assert response.status_code in [401, 403], f"Should require auth, got {response.status_code}"
    
    def test_generate_assessment_requires_content(self, student_token):
        """Test that generate-assessment requires lesson_content"""
        response = requests.post(
            f"{BASE_URL}/api/avatar-orchestrator/generate-assessment",
            headers={"Authorization": f"Bearer {student_token}"},
            json={}  # No content
        )
        assert response.status_code == 400, f"Should require content, got {response.status_code}"
    
    def test_generate_assessment_returns_questions(self, student_token):
        """Test that generate-assessment returns quiz questions"""
        response = requests.post(
            f"{BASE_URL}/api/avatar-orchestrator/generate-assessment",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "lesson_content": "Machine learning is a subset of artificial intelligence. Supervised learning uses labeled data. Unsupervised learning finds patterns in unlabeled data.",
                "lesson_title": "ML Basics",
                "question_count": 3
            },
            timeout=60  # AI response may take time
        )
        assert response.status_code == 200, f"Generate assessment failed: {response.text}"
        
        data = response.json()
        assert "questions" in data, "Should have questions field"
        assert isinstance(data["questions"], list), "Questions should be a list"
        assert len(data["questions"]) > 0, "Should have at least one question"


class TestAvatarOrchestratorAdaptiveRewrite:
    """Tests for POST /api/avatar-orchestrator/adaptive-rewrite"""
    
    def test_adaptive_rewrite_requires_auth(self):
        """Test that adaptive-rewrite endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/avatar-orchestrator/adaptive-rewrite",
            json={"content": "Test content"}
        )
        assert response.status_code in [401, 403], f"Should require auth, got {response.status_code}"
    
    def test_adaptive_rewrite_requires_content(self, student_token):
        """Test that adaptive-rewrite requires content"""
        response = requests.post(
            f"{BASE_URL}/api/avatar-orchestrator/adaptive-rewrite",
            headers={"Authorization": f"Bearer {student_token}"},
            json={}  # No content
        )
        assert response.status_code == 400, f"Should require content, got {response.status_code}"
    
    def test_adaptive_rewrite_returns_rewritten(self, student_token):
        """Test that adaptive-rewrite returns rewritten content"""
        response = requests.post(
            f"{BASE_URL}/api/avatar-orchestrator/adaptive-rewrite",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "content": "Machine learning algorithms utilize statistical methods to identify patterns in data.",
                "target_level": "beginner"
            },
            timeout=60  # AI response may take time
        )
        assert response.status_code == 200, f"Adaptive rewrite failed: {response.text}"
        
        data = response.json()
        assert "updated_script" in data, "Should have updated_script field"
        assert "target_level" in data, "Should have target_level field"
        assert data["target_level"] == "beginner", "Target level should match"


class TestAvatarOrchestratorTranslateScript:
    """Tests for POST /api/avatar-orchestrator/translate-script"""
    
    def test_translate_script_requires_auth(self):
        """Test that translate-script endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/avatar-orchestrator/translate-script",
            json={"script": "Hello world"}
        )
        assert response.status_code in [401, 403], f"Should require auth, got {response.status_code}"
    
    def test_translate_script_requires_script(self, student_token):
        """Test that translate-script requires script"""
        response = requests.post(
            f"{BASE_URL}/api/avatar-orchestrator/translate-script",
            headers={"Authorization": f"Bearer {student_token}"},
            json={}  # No script
        )
        assert response.status_code == 400, f"Should require script, got {response.status_code}"
    
    def test_translate_script_returns_translation(self, student_token):
        """Test that translate-script returns translated content"""
        response = requests.post(
            f"{BASE_URL}/api/avatar-orchestrator/translate-script",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "script": "Welcome to this lesson about machine learning.",
                "target_language": "sw",  # Swahili
                "source_language": "en"
            },
            timeout=60  # AI response may take time
        )
        assert response.status_code == 200, f"Translate script failed: {response.text}"
        
        data = response.json()
        assert "translated_script" in data, "Should have translated_script field"
        assert "target_language" in data, "Should have target_language field"
        assert data["mode"] == "multi_language", "Mode should be multi_language"


class TestResearchSearchFix:
    """Tests for POST /api/research/search - Bug fix verification"""
    
    def test_research_search_requires_auth(self):
        """Test that research/search endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/research/search",
            json={"query": "machine learning"}
        )
        assert response.status_code in [401, 403], f"Should require auth, got {response.status_code}"
    
    def test_research_search_accepts_json_body(self, student_token):
        """Test that research/search accepts JSON body with query field (was broken - used query param)"""
        response = requests.post(
            f"{BASE_URL}/api/research/search",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"query": "machine learning education"}
        )
        # Should not return 422 (validation error) or 400 (missing query)
        assert response.status_code in [200, 500], f"Should accept JSON body, got {response.status_code}: {response.text}"
    
    def test_research_search_requires_query(self, student_token):
        """Test that research/search requires query field"""
        response = requests.post(
            f"{BASE_URL}/api/research/search",
            headers={"Authorization": f"Bearer {student_token}"},
            json={}  # No query
        )
        assert response.status_code == 400, f"Should require query, got {response.status_code}"


class TestMessagesEndpoint:
    """Tests for POST /api/messages"""
    
    def test_messages_endpoint_requires_auth(self):
        """Test that messages endpoint requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/messages",
            json={"content": "Test message"}
        )
        assert response.status_code in [401, 403], f"Should require auth, got {response.status_code}"
    
    def test_messages_endpoint_exists(self, student_token):
        """Test that messages endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/messages",
            headers={"Authorization": f"Bearer {student_token}"},
            json={}  # Empty body
        )
        # Should not return 404
        assert response.status_code != 404, f"Messages endpoint should exist, got {response.status_code}"


class TestShareableContentEndpoint:
    """Tests for GET /api/user/shareable-content"""
    
    def test_shareable_content_requires_auth(self):
        """Test that shareable-content endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/user/shareable-content")
        assert response.status_code in [401, 403], f"Should require auth, got {response.status_code}"
    
    def test_shareable_content_returns_data(self, student_token):
        """Test that shareable-content endpoint returns data"""
        response = requests.get(
            f"{BASE_URL}/api/user/shareable-content",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200, f"Shareable content failed: {response.text}"
        
        data = response.json()
        # Should return some structure (list or object)
        assert data is not None, "Should return data"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
