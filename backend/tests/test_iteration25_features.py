"""
Iteration 25 Backend Tests
Tests for:
1. Dashboard stats endpoint - KeyError fix for profile['id']
2. Achievements endpoint - KeyError fix
3. Social URL analysis endpoint - LinkedIn company and individual URLs
4. LinkedIn analysis endpoint
5. Certificate and Credentials endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from test_credentials.md
STUDENT_EMAIL = "demo.student@cognify.edu"
STUDENT_PASSWORD = "demo123"
TEACHER_EMAIL = "demo.teacher@eduos.edu"
TEACHER_PASSWORD = "demo123"
ORG_ADMIN_EMAIL = "test.orgadmin@cognify.edu"
ORG_ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def student_token(api_client):
    """Get student authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": STUDENT_EMAIL,
        "password": STUDENT_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Student authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def teacher_token(api_client):
    """Get teacher authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEACHER_EMAIL,
        "password": TEACHER_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Teacher authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def org_admin_token(api_client):
    """Get org admin authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ORG_ADMIN_EMAIL,
        "password": ORG_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Org admin authentication failed: {response.status_code} - {response.text}")


class TestAuthentication:
    """Test authentication for all user types"""
    
    def test_student_login(self, api_client):
        """Test student login"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        assert response.status_code == 200, f"Student login failed: {response.text}"
        data = response.json()
        assert "access_token" in data or "token" in data
        assert "user" in data
        print(f"✓ Student login successful: {data['user'].get('email')}")
    
    def test_teacher_login(self, api_client):
        """Test teacher login"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        assert response.status_code == 200, f"Teacher login failed: {response.text}"
        data = response.json()
        assert "access_token" in data or "token" in data
        assert "user" in data
        print(f"✓ Teacher login successful: {data['user'].get('email')}")
    
    def test_org_admin_login(self, api_client):
        """Test org admin login"""
        response = api_client.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Org admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data or "token" in data
        assert "user" in data
        print(f"✓ Org admin login successful: {data['user'].get('email')}")


class TestDashboardStats:
    """Test dashboard stats endpoint - KeyError fix verification"""
    
    def test_student_dashboard_stats(self, api_client, student_token):
        """Test dashboard stats for student - should not throw KeyError"""
        response = api_client.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200, f"Student dashboard stats failed: {response.text}"
        data = response.json()
        # Verify expected fields for student
        assert "gpa" in data or "enrolled_courses" in data or "attendance_rate" in data
        print(f"✓ Student dashboard stats: {data}")
    
    def test_teacher_dashboard_stats(self, api_client, teacher_token):
        """Test dashboard stats for teacher - should not throw KeyError"""
        response = api_client.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        assert response.status_code == 200, f"Teacher dashboard stats failed: {response.text}"
        data = response.json()
        # Verify expected fields for teacher
        assert "total_courses" in data or "total_students" in data
        print(f"✓ Teacher dashboard stats: {data}")
    
    def test_org_admin_dashboard_stats(self, api_client, org_admin_token):
        """Test dashboard stats for org admin - should not throw KeyError"""
        response = api_client.get(
            f"{BASE_URL}/api/dashboard/stats",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert response.status_code == 200, f"Org admin dashboard stats failed: {response.text}"
        data = response.json()
        # Verify expected fields for admin
        assert "total_students" in data or "total_teachers" in data or "total_courses" in data
        print(f"✓ Org admin dashboard stats: {data}")


class TestAchievements:
    """Test achievements endpoint - KeyError fix verification"""
    
    def test_student_achievements(self, api_client, student_token):
        """Test achievements for student - should not throw KeyError"""
        response = api_client.get(
            f"{BASE_URL}/api/achievements",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200, f"Student achievements failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Student achievements returned: {len(data)} achievements")
    
    def test_teacher_achievements(self, api_client, teacher_token):
        """Test achievements for teacher"""
        response = api_client.get(
            f"{BASE_URL}/api/achievements",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        assert response.status_code == 200, f"Teacher achievements failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Teacher achievements returned: {len(data)} achievements")


class TestSocialUrlAnalysis:
    """Test social URL analysis endpoint - LinkedIn company and individual URLs"""
    
    def test_analyze_linkedin_company_url(self, api_client, student_token):
        """Test analyzing a LinkedIn company URL"""
        response = api_client.post(
            f"{BASE_URL}/api/mentor/analyze-social-url",
            json={"url": "https://www.linkedin.com/company/microsoft"},
            headers={"Authorization": f"Bearer {student_token}"}
        )
        # Should return 200 even if Proxycurl fails (AI fallback)
        assert response.status_code == 200, f"LinkedIn company URL analysis failed: {response.text}"
        data = response.json()
        # Check response structure
        assert "success" in data
        print(f"✓ LinkedIn company URL analysis: success={data.get('success')}, url_type={data.get('url_type')}")
    
    def test_analyze_linkedin_individual_url(self, api_client, student_token):
        """Test analyzing a LinkedIn individual profile URL"""
        response = api_client.post(
            f"{BASE_URL}/api/mentor/analyze-social-url",
            json={"url": "https://www.linkedin.com/in/satyanadella"},
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200, f"LinkedIn individual URL analysis failed: {response.text}"
        data = response.json()
        assert "success" in data
        print(f"✓ LinkedIn individual URL analysis: success={data.get('success')}, url_type={data.get('url_type')}")
    
    def test_analyze_github_url(self, api_client, student_token):
        """Test analyzing a GitHub URL"""
        response = api_client.post(
            f"{BASE_URL}/api/mentor/analyze-social-url",
            json={"url": "https://github.com/torvalds"},
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200, f"GitHub URL analysis failed: {response.text}"
        data = response.json()
        assert "success" in data
        print(f"✓ GitHub URL analysis: success={data.get('success')}, url_type={data.get('url_type')}")
    
    def test_analyze_empty_url(self, api_client, student_token):
        """Test analyzing empty URL - should return error"""
        response = api_client.post(
            f"{BASE_URL}/api/mentor/analyze-social-url",
            json={"url": ""},
            headers={"Authorization": f"Bearer {student_token}"}
        )
        # Should return 400 for empty URL
        assert response.status_code in [400, 422], f"Empty URL should fail: {response.text}"
        print(f"✓ Empty URL correctly rejected with status {response.status_code}")


class TestLinkedInAnalysis:
    """Test LinkedIn analysis endpoint"""
    
    def test_analyze_linkedin_profile(self, api_client, student_token):
        """Test LinkedIn profile analysis - may fail if no LinkedIn URL set"""
        response = api_client.post(
            f"{BASE_URL}/api/mentor/analyze-linkedin",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200, f"LinkedIn analysis failed: {response.text}"
        data = response.json()
        # Should return success=False if no LinkedIn URL is set
        assert "success" in data
        print(f"✓ LinkedIn analysis: success={data.get('success')}, message={data.get('message', 'N/A')}")


class TestCertificateAndCredentials:
    """Test certificate and credentials endpoints"""
    
    def test_get_student_credentials(self, api_client, student_token):
        """Test getting student credentials"""
        # First get the student profile to get student_id
        response = api_client.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200
        user_data = response.json()
        student_id = user_data.get('id')
        
        # Get credentials
        response = api_client.get(
            f"{BASE_URL}/api/credentials/student/{student_id}",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200, f"Get credentials failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Student credentials returned: {len(data)} credentials")
    
    def test_verify_credential_invalid_hash(self, api_client):
        """Test verifying a credential with invalid hash"""
        response = api_client.get(f"{BASE_URL}/api/credentials/verify/invalid-hash-12345")
        # Should return 404 for invalid hash
        assert response.status_code in [200, 404], f"Verify credential unexpected status: {response.text}"
        print(f"✓ Credential verification endpoint works (status: {response.status_code})")


class TestMentorProfile:
    """Test mentor profile endpoints"""
    
    def test_get_mentor_profile(self, api_client, student_token):
        """Test getting mentor profile"""
        response = api_client.get(
            f"{BASE_URL}/api/mentor/profile",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200, f"Get mentor profile failed: {response.text}"
        data = response.json()
        print(f"✓ Mentor profile retrieved: {data.get('learning_style', 'N/A')}")


class TestKnowledgeGraphSync:
    """Test knowledge graph sync functionality"""
    
    def test_get_learner_concept_states(self, api_client, student_token):
        """Test getting learner concept states"""
        response = api_client.get(
            f"{BASE_URL}/api/knowledge/learner-state",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        # May return 200 or 404 depending on data
        assert response.status_code in [200, 404], f"Get learner state failed: {response.text}"
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Learner concept states: {len(data) if isinstance(data, list) else 'N/A'}")
        else:
            print(f"✓ Learner concept states endpoint exists (no data yet)")
    
    def test_get_concepts(self, api_client, student_token):
        """Test getting concepts"""
        response = api_client.get(
            f"{BASE_URL}/api/knowledge/concepts",
            headers={"Authorization": f"Bearer {student_token}"}
        )
        assert response.status_code == 200, f"Get concepts failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Concepts returned: {len(data)} concepts")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
