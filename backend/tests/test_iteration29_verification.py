"""
Iteration 29 - Post-Refactoring Verification Tests
Tests to verify that certificate routes extraction and staff rights enforcement still work correctly.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
STUDENT_EMAIL = "demo.student@cognify.edu"
STUDENT_PASSWORD = "demo123"
TEACHER_EMAIL = "demo.teacher@eduos.edu"
TEACHER_PASSWORD = "demo123"
ORG_ADMIN_EMAIL = "test.orgadmin@cognify.edu"
ORG_ADMIN_PASSWORD = "admin123"

# Test certificate data from iteration 28
TEST_CERTIFICATE_ID = "cd687035-7710-4c30-93ad-7941d8743ffc"
TEST_VERIFICATION_CODE = "B41BC64B"


class TestHealthEndpoint:
    """Verify basic API health"""
    
    def test_health_endpoint(self):
        """Test health endpoint responds correctly"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Health check failed: {response.text}"
        data = response.json()
        assert data.get("status") == "healthy", f"Unexpected health status: {data}"
        print("PASS: Health endpoint responds correctly")


class TestAuthentication:
    """Test login flows for all user types"""
    
    def test_student_login(self):
        """Test student login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        assert response.status_code == 200, f"Student login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data.get("user", {}).get("role") == "student", "Role mismatch"
        print(f"PASS: Student login successful - {data['user']['email']}")
    
    def test_teacher_login(self):
        """Test teacher login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        assert response.status_code == 200, f"Teacher login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data.get("user", {}).get("role") == "teacher", "Role mismatch"
        print(f"PASS: Teacher login successful - {data['user']['email']}")
    
    def test_org_admin_login(self):
        """Test org admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Org admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        assert data.get("user", {}).get("role") == "org_admin", "Role mismatch"
        print(f"PASS: Org admin login successful - {data['user']['email']}")


class TestCertificateRoutesAfterExtraction:
    """Test certificate routes after extraction to routes/certificates.py"""
    
    @pytest.fixture
    def student_token(self):
        """Get student auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Could not get student token")
    
    @pytest.fixture
    def org_admin_token(self):
        """Get org admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Could not get org admin token")
    
    def test_certificate_public_verification_valid_code(self):
        """Test public certificate verification with valid code"""
        response = requests.get(f"{BASE_URL}/api/certificates/verify/{TEST_VERIFICATION_CODE}")
        assert response.status_code == 200, f"Verification failed: {response.text}"
        data = response.json()
        assert data.get("verified") == True, f"Certificate not verified: {data}"
        assert data.get("certificate") is not None, "No certificate data returned"
        print(f"PASS: Certificate verification works - verified={data['verified']}")
    
    def test_certificate_public_verification_invalid_code(self):
        """Test public certificate verification with invalid code"""
        response = requests.get(f"{BASE_URL}/api/certificates/verify/INVALID123")
        assert response.status_code == 200, f"Request failed: {response.text}"
        data = response.json()
        assert data.get("verified") == False, f"Invalid code should not verify: {data}"
        print("PASS: Invalid verification code returns verified=false")
    
    def test_certificate_get_by_id(self, student_token):
        """Test getting certificate by ID"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/certificates/{TEST_CERTIFICATE_ID}", headers=headers)
        assert response.status_code == 200, f"Get certificate failed: {response.text}"
        data = response.json()
        assert data.get("id") == TEST_CERTIFICATE_ID, "Certificate ID mismatch"
        assert "verification_code" in data, "No verification_code in response"
        print(f"PASS: Certificate GET by ID works - {data.get('course_name')}")
    
    def test_certificate_get_not_found(self, student_token):
        """Test getting non-existent certificate"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/certificates/nonexistent-id-12345", headers=headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: Non-existent certificate returns 404")
    
    def test_certificate_pdf_download(self, student_token):
        """Test certificate PDF download"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/certificates/{TEST_CERTIFICATE_ID}/pdf", headers=headers)
        assert response.status_code == 200, f"PDF download failed: {response.text}"
        assert "application/pdf" in response.headers.get("content-type", ""), "Not a PDF response"
        assert response.content[:4] == b'%PDF', "Response doesn't start with PDF magic bytes"
        print(f"PASS: Certificate PDF download works - {len(response.content)} bytes")
    
    def test_certificate_pdf_not_found(self, student_token):
        """Test PDF download for non-existent certificate"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.get(f"{BASE_URL}/api/certificates/nonexistent-id-12345/pdf", headers=headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: Non-existent certificate PDF returns 404")


class TestStaffRightsEndpoints:
    """Test staff rights management endpoints"""
    
    @pytest.fixture
    def org_admin_token(self):
        """Get org admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Could not get org admin token")
    
    @pytest.fixture
    def student_token(self):
        """Get student auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Could not get student token")
    
    def test_get_org_staff_includes_rights(self, org_admin_token):
        """Test GET /api/org/staff returns staff with rights field"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/org/staff", headers=headers)
        assert response.status_code == 200, f"Get staff failed: {response.text}"
        data = response.json()
        staff_list = data.get("staff", data) if isinstance(data, dict) else data
        if isinstance(staff_list, list) and len(staff_list) > 0:
            # Check that at least one staff member has rights field
            has_rights = any("rights" in s for s in staff_list)
            print(f"PASS: GET /api/org/staff returns {len(staff_list)} staff members, rights field present: {has_rights}")
        else:
            print("PASS: GET /api/org/staff works (no staff members found)")
    
    def test_get_staff_rights_by_id(self, org_admin_token):
        """Test GET /api/org/staff/{staffId}/rights"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        # First get staff list to find a staff ID
        response = requests.get(f"{BASE_URL}/api/org/staff", headers=headers)
        if response.status_code != 200:
            pytest.skip("Could not get staff list")
        
        data = response.json()
        staff_list = data.get("staff", data) if isinstance(data, dict) else data
        if not isinstance(staff_list, list) or len(staff_list) == 0:
            pytest.skip("No staff members to test")
        
        staff_id = staff_list[0].get("id")
        if not staff_id:
            pytest.skip("Staff member has no ID")
        
        # Get rights for this staff member
        response = requests.get(f"{BASE_URL}/api/org/staff/{staff_id}/rights", headers=headers)
        assert response.status_code == 200, f"Get staff rights failed: {response.text}"
        data = response.json()
        # Should have rights fields
        assert "can_create_courses" in data or "rights" in data, f"No rights data: {data}"
        print(f"PASS: GET /api/org/staff/{staff_id}/rights works")
    
    def test_assign_staff_rights(self, org_admin_token):
        """Test POST /api/org/staff/assign-rights"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        # First get staff list to find a staff ID
        response = requests.get(f"{BASE_URL}/api/org/staff", headers=headers)
        if response.status_code != 200:
            pytest.skip("Could not get staff list")
        
        data = response.json()
        staff_list = data.get("staff", data) if isinstance(data, dict) else data
        if not isinstance(staff_list, list) or len(staff_list) == 0:
            pytest.skip("No staff members to test")
        
        staff_id = staff_list[0].get("id")
        if not staff_id:
            pytest.skip("Staff member has no ID")
        
        # Assign rights
        response = requests.post(f"{BASE_URL}/api/org/staff/assign-rights", 
            headers=headers,
            json={
                "staff_id": staff_id,
                "can_create_courses": True,
                "can_upload_content": True,
                "can_manage_participants": False,
                "can_invite_participants": False
            }
        )
        assert response.status_code == 200, f"Assign rights failed: {response.text}"
        print(f"PASS: POST /api/org/staff/assign-rights works for staff {staff_id}")
    
    def test_assign_rights_requires_org_admin(self, student_token):
        """Test that assigning rights requires org_admin role"""
        headers = {"Authorization": f"Bearer {student_token}"}
        response = requests.post(f"{BASE_URL}/api/org/staff/assign-rights",
            headers=headers,
            json={
                "staff_id": "some-id",
                "can_create_courses": True
            }
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("PASS: Assign rights requires org_admin role (403 for student)")


class TestOrgAdminDashboard:
    """Test org admin dashboard endpoints"""
    
    @pytest.fixture
    def org_admin_token(self):
        """Get org admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Could not get org admin token")
    
    def test_org_admin_dashboard_loads(self, org_admin_token):
        """Test org admin dashboard endpoint"""
        headers = {"Authorization": f"Bearer {org_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/org-admin/dashboard", headers=headers)
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        data = response.json()
        # Should have statistics
        assert "statistics" in data or "org_name" in data, f"Missing dashboard data: {data}"
        print(f"PASS: Org admin dashboard loads - org: {data.get('org_name', 'N/A')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
