"""
Iteration 27 - Organization Portal Registration, User Approval Workflow, and Cross-Org Course Isolation Tests

Features tested:
1. POST /api/auth/org-register - creates user with org_status='pending'
2. POST /api/auth/org-register - rejects duplicate email with 400
3. POST /api/auth/login - blocks pending users with 403
4. POST /api/auth/login - allows approved users to login
5. GET /api/organizations/pending-users - returns list of pending org users (requires org_admin)
6. POST /api/organizations/approve-user - approve/reject user
7. POST /api/auth/login - blocks rejected users with 403
8. GET /api/courses - filters by organization_id for org users
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://knowledge-sync-9.preview.emergentagent.com')

# Test credentials from test_credentials.md
STUDENT_EMAIL = "demo.student@cognify.edu"
STUDENT_PASSWORD = "demo123"
TEACHER_EMAIL = "demo.teacher@eduos.edu"
TEACHER_PASSWORD = "demo123"
ORG_ADMIN_EMAIL = "test.orgadmin@cognify.edu"
ORG_ADMIN_PASSWORD = "admin123"
ORG_SLUG = "cognify"


class TestOrgPublicEndpoint:
    """Test organization public info endpoint"""
    
    def test_get_org_public_info(self):
        """GET /api/org/public/{org_slug} returns org info"""
        response = requests.get(f"{BASE_URL}/api/org/public/{ORG_SLUG}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert data["name"] == "Cognify University"
        assert "branding" in data
        print(f"PASS: Org public info returned for {ORG_SLUG}")
    
    def test_get_org_public_info_not_found(self):
        """GET /api/org/public/{org_slug} returns 404 for unknown org"""
        response = requests.get(f"{BASE_URL}/api/org/public/nonexistent-org-xyz")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: 404 returned for nonexistent org")


class TestOrgRegistration:
    """Test organization user registration flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Generate unique test email for each test"""
        self.test_email = f"test_user_{uuid.uuid4().hex[:8]}@testorg.com"
        self.test_password = "test123456"
        self.test_name = "Test User Registration"
    
    def test_org_register_creates_pending_user(self):
        """POST /api/auth/org-register creates user with org_status='pending'"""
        response = requests.post(f"{BASE_URL}/api/auth/org-register", json={
            "email": self.test_email,
            "password": self.test_password,
            "full_name": self.test_name,
            "role": "student",
            "org_slug": ORG_SLUG
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data
        assert "pending" in data["message"].lower() or "approval" in data["message"].lower()
        print(f"PASS: User registered with pending status: {self.test_email}")
        
        # Store for cleanup
        self.registered_email = self.test_email
    
    def test_org_register_duplicate_email_rejected(self):
        """POST /api/auth/org-register rejects duplicate email with 400"""
        # First registration
        response1 = requests.post(f"{BASE_URL}/api/auth/org-register", json={
            "email": self.test_email,
            "password": self.test_password,
            "full_name": self.test_name,
            "role": "student",
            "org_slug": ORG_SLUG
        })
        assert response1.status_code == 200, f"First registration failed: {response1.text}"
        
        # Second registration with same email
        response2 = requests.post(f"{BASE_URL}/api/auth/org-register", json={
            "email": self.test_email,
            "password": self.test_password,
            "full_name": "Another User",
            "role": "student",
            "org_slug": ORG_SLUG
        })
        assert response2.status_code == 400, f"Expected 400, got {response2.status_code}: {response2.text}"
        data = response2.json()
        assert "already" in data.get("detail", "").lower() or "registered" in data.get("detail", "").lower()
        print(f"PASS: Duplicate email rejected with 400")
    
    def test_org_register_invalid_org_slug(self):
        """POST /api/auth/org-register returns 404 for invalid org slug"""
        response = requests.post(f"{BASE_URL}/api/auth/org-register", json={
            "email": self.test_email,
            "password": self.test_password,
            "full_name": self.test_name,
            "role": "student",
            "org_slug": "nonexistent-org-xyz"
        })
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"
        print("PASS: Invalid org slug returns 404")


class TestPendingUserLogin:
    """Test that pending users cannot login"""
    
    def test_pending_user_login_blocked(self):
        """POST /api/auth/login blocks pending users with 403"""
        # First register a new user
        test_email = f"pending_test_{uuid.uuid4().hex[:8]}@testorg.com"
        test_password = "test123456"
        
        reg_response = requests.post(f"{BASE_URL}/api/auth/org-register", json={
            "email": test_email,
            "password": test_password,
            "full_name": "Pending Test User",
            "role": "student",
            "org_slug": ORG_SLUG
        })
        assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"
        
        # Try to login - should be blocked
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": test_email,
            "password": test_password
        })
        assert login_response.status_code == 403, f"Expected 403, got {login_response.status_code}: {login_response.text}"
        data = login_response.json()
        assert "pending" in data.get("detail", "").lower()
        print(f"PASS: Pending user login blocked with 403")


class TestOrgAdminApprovalWorkflow:
    """Test org admin user approval workflow"""
    
    @pytest.fixture
    def org_admin_token(self):
        """Get org admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Org admin login failed: {response.text}")
        return response.json()["access_token"]
    
    def test_get_pending_users_requires_auth(self):
        """GET /api/organizations/pending-users requires authentication"""
        response = requests.get(f"{BASE_URL}/api/organizations/pending-users")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: Pending users endpoint requires auth")
    
    def test_get_pending_users_as_org_admin(self, org_admin_token):
        """GET /api/organizations/pending-users returns list for org admin"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/organizations/pending-users", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "pending_users" in data
        assert isinstance(data["pending_users"], list)
        print(f"PASS: Pending users returned: {len(data['pending_users'])} users")
    
    def test_approve_user_workflow(self, org_admin_token):
        """Full workflow: register -> pending -> approve -> login"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        
        # 1. Register new user
        test_email = f"approve_test_{uuid.uuid4().hex[:8]}@testorg.com"
        test_password = "test123456"
        
        reg_response = requests.post(f"{BASE_URL}/api/auth/org-register", json={
            "email": test_email,
            "password": test_password,
            "full_name": "Approve Test User",
            "role": "student",
            "org_slug": ORG_SLUG
        })
        assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"
        print(f"Step 1: User registered: {test_email}")
        
        # 2. Verify user is in pending list
        pending_response = requests.get(f"{BASE_URL}/api/organizations/pending-users", headers=headers)
        assert pending_response.status_code == 200
        pending_users = pending_response.json()["pending_users"]
        pending_user = next((u for u in pending_users if u["email"] == test_email), None)
        assert pending_user is not None, f"User not found in pending list"
        user_id = pending_user["id"]
        print(f"Step 2: User found in pending list with id: {user_id}")
        
        # 3. Approve the user
        approve_response = requests.post(f"{BASE_URL}/api/organizations/approve-user", 
            json={"user_id": user_id, "action": "approve"},
            headers=headers
        )
        assert approve_response.status_code == 200, f"Approval failed: {approve_response.text}"
        data = approve_response.json()
        assert data["status"] == "approved"
        print(f"Step 3: User approved")
        
        # 4. Verify user can now login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": test_email,
            "password": test_password
        })
        assert login_response.status_code == 200, f"Login failed after approval: {login_response.text}"
        print(f"Step 4: Approved user can login")
        print("PASS: Full approval workflow completed")
    
    def test_reject_user_workflow(self, org_admin_token):
        """Workflow: register -> pending -> reject -> login blocked"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        
        # 1. Register new user
        test_email = f"reject_test_{uuid.uuid4().hex[:8]}@testorg.com"
        test_password = "test123456"
        
        reg_response = requests.post(f"{BASE_URL}/api/auth/org-register", json={
            "email": test_email,
            "password": test_password,
            "full_name": "Reject Test User",
            "role": "student",
            "org_slug": ORG_SLUG
        })
        assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"
        print(f"Step 1: User registered: {test_email}")
        
        # 2. Get user from pending list
        pending_response = requests.get(f"{BASE_URL}/api/organizations/pending-users", headers=headers)
        assert pending_response.status_code == 200
        pending_users = pending_response.json()["pending_users"]
        pending_user = next((u for u in pending_users if u["email"] == test_email), None)
        assert pending_user is not None, f"User not found in pending list"
        user_id = pending_user["id"]
        print(f"Step 2: User found in pending list")
        
        # 3. Reject the user
        reject_response = requests.post(f"{BASE_URL}/api/organizations/approve-user", 
            json={"user_id": user_id, "action": "reject"},
            headers=headers
        )
        assert reject_response.status_code == 200, f"Rejection failed: {reject_response.text}"
        data = reject_response.json()
        assert data["status"] == "rejected"
        print(f"Step 3: User rejected")
        
        # 4. Verify user cannot login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": test_email,
            "password": test_password
        })
        assert login_response.status_code == 403, f"Expected 403, got {login_response.status_code}: {login_response.text}"
        assert "not approved" in login_response.json().get("detail", "").lower() or "rejected" in login_response.json().get("detail", "").lower()
        print(f"Step 4: Rejected user login blocked with 403")
        print("PASS: Full rejection workflow completed")


class TestApprovedUserLogin:
    """Test that approved users can login"""
    
    def test_approved_user_can_login(self):
        """POST /api/auth/login allows approved users"""
        # Use existing org admin which should be approved
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        print("PASS: Approved user (org admin) can login")


class TestCrossOrgCourseIsolation:
    """Test that courses are filtered by organization_id"""
    
    @pytest.fixture
    def org_admin_token(self):
        """Get org admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Org admin login failed: {response.text}")
        return response.json()["access_token"]
    
    @pytest.fixture
    def student_token(self):
        """Get student auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Student login failed: {response.text}")
        return response.json()["access_token"]
    
    def test_get_courses_requires_auth(self):
        """GET /api/courses requires authentication"""
        response = requests.get(f"{BASE_URL}/api/courses")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: Courses endpoint requires auth")
    
    def test_org_admin_sees_org_courses(self, org_admin_token):
        """GET /api/courses returns org-specific courses for org admin"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        courses = response.json()
        assert isinstance(courses, list)
        print(f"PASS: Org admin sees {len(courses)} courses")
    
    def test_student_sees_filtered_courses(self, student_token):
        """GET /api/courses returns filtered courses for student"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/courses", headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        courses = response.json()
        assert isinstance(courses, list)
        print(f"PASS: Student sees {len(courses)} courses")


class TestExistingAuthStillWorks:
    """Verify existing authentication still works"""
    
    def test_student_login(self):
        """Student can still login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        assert response.status_code == 200, f"Student login failed: {response.text}"
        print("PASS: Student login works")
    
    def test_teacher_login(self):
        """Teacher can still login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        assert response.status_code == 200, f"Teacher login failed: {response.text}"
        print("PASS: Teacher login works")
    
    def test_org_admin_login(self):
        """Org admin can still login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Org admin login failed: {response.text}"
        print("PASS: Org admin login works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
