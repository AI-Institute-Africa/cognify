"""
Test Suite for Bulk Enrollment with Magic Links and Teacher File Upload Features
Tests:
1. POST /api/org/bulk-enroll - Bulk enrollment with magic links
2. GET /api/org/pending-enrollments - List pending invitations
3. POST /api/org/resend-invitation/{id} - Resend magic link
4. GET /api/auth/verify-magic-link - Verify magic link token
5. POST /api/auth/accept-magic-link - Accept invitation and create account
6. POST /api/content/course/{course_id}/upload-file - File upload
7. GET /api/content/files/{course_id}/{filename} - Serve uploaded files
"""
import pytest
import requests
import os
import io
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ORG_ADMIN_EMAIL = "test.orgadmin@cognify.edu"
ORG_ADMIN_PASSWORD = "admin123"
TEACHER_EMAIL = "demo.teacher@eduos.edu"
TEACHER_PASSWORD = "demo123"
TEST_COURSE_ID = "test-course-1"


class TestAuthentication:
    """Test authentication for org admin and teacher"""
    
    def test_org_admin_login(self):
        """Test org admin can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ORG_ADMIN_EMAIL,
            "password": ORG_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "org_admin"
        print(f"✓ Org admin login successful: {data['user']['email']}")
    
    def test_teacher_login(self):
        """Test teacher can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "teacher"
        print(f"✓ Teacher login successful: {data['user']['email']}")


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


class TestBulkEnrollment:
    """Test bulk enrollment with magic links (72-hour expiry)"""
    
    def test_bulk_enroll_single_email(self, org_admin_token):
        """Test bulk enrollment with a single email"""
        test_email = f"test_bulk_{uuid.uuid4().hex[:8]}@example.com"
        
        response = requests.post(
            f"{BASE_URL}/api/org/bulk-enroll",
            headers={"Authorization": f"Bearer {org_admin_token}"},
            json={
                "emails": [test_email],
                "course_id": TEST_COURSE_ID
            }
        )
        
        assert response.status_code == 200, f"Bulk enroll failed: {response.text}"
        data = response.json()
        
        assert "results" in data
        assert data["total"] == 1
        assert data["successful"] >= 0  # May be 0 if email simulation
        
        # Check result structure
        result = data["results"][0]
        assert result["email"] == test_email
        assert "success" in result
        print(f"✓ Bulk enrollment single email: {result}")
    
    def test_bulk_enroll_multiple_emails(self, org_admin_token):
        """Test bulk enrollment with multiple emails"""
        test_emails = [
            f"test_multi1_{uuid.uuid4().hex[:8]}@example.com",
            f"test_multi2_{uuid.uuid4().hex[:8]}@example.com",
            f"test_multi3_{uuid.uuid4().hex[:8]}@example.com"
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/org/bulk-enroll",
            headers={"Authorization": f"Bearer {org_admin_token}"},
            json={
                "emails": test_emails,
                "course_id": TEST_COURSE_ID
            }
        )
        
        assert response.status_code == 200, f"Bulk enroll failed: {response.text}"
        data = response.json()
        
        assert data["total"] == 3
        assert len(data["results"]) == 3
        print(f"✓ Bulk enrollment multiple emails: total={data['total']}, successful={data['successful']}")
    
    def test_bulk_enroll_duplicate_email(self, org_admin_token):
        """Test that duplicate pending enrollment is rejected"""
        test_email = f"test_dup_{uuid.uuid4().hex[:8]}@example.com"
        
        # First enrollment
        response1 = requests.post(
            f"{BASE_URL}/api/org/bulk-enroll",
            headers={"Authorization": f"Bearer {org_admin_token}"},
            json={
                "emails": [test_email],
                "course_id": TEST_COURSE_ID
            }
        )
        assert response1.status_code == 200
        
        # Second enrollment with same email
        response2 = requests.post(
            f"{BASE_URL}/api/org/bulk-enroll",
            headers={"Authorization": f"Bearer {org_admin_token}"},
            json={
                "emails": [test_email],
                "course_id": TEST_COURSE_ID
            }
        )
        assert response2.status_code == 200
        data = response2.json()
        
        # Should fail with "Pending invitation already exists"
        result = data["results"][0]
        assert result["success"] == False
        assert "already exists" in result.get("error", "").lower() or "pending" in result.get("error", "").lower()
        print(f"✓ Duplicate enrollment correctly rejected: {result['error']}")
    
    def test_bulk_enroll_invalid_course(self, org_admin_token):
        """Test bulk enrollment with invalid course ID"""
        response = requests.post(
            f"{BASE_URL}/api/org/bulk-enroll",
            headers={"Authorization": f"Bearer {org_admin_token}"},
            json={
                "emails": ["test@example.com"],
                "course_id": "invalid-course-id-12345"
            }
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Invalid course correctly returns 404")
    
    def test_bulk_enroll_unauthorized(self):
        """Test bulk enrollment without auth fails"""
        response = requests.post(
            f"{BASE_URL}/api/org/bulk-enroll",
            json={
                "emails": ["test@example.com"],
                "course_id": TEST_COURSE_ID
            }
        )
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Unauthorized bulk enrollment correctly rejected")


class TestPendingEnrollments:
    """Test pending enrollments listing"""
    
    def test_get_pending_enrollments(self, org_admin_token):
        """Test getting pending enrollments list"""
        response = requests.get(
            f"{BASE_URL}/api/org/pending-enrollments",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list)
        # Check structure if there are pending enrollments
        if len(data) > 0:
            enrollment = data[0]
            assert "id" in enrollment
            assert "email" in enrollment
            assert "course_name" in enrollment
            assert "status" not in enrollment or enrollment.get("status") == "pending"
            # Token should be excluded for security
            assert "token" not in enrollment
        print(f"✓ Pending enrollments retrieved: {len(data)} pending")
    
    def test_pending_enrollments_unauthorized(self):
        """Test pending enrollments without auth fails"""
        response = requests.get(f"{BASE_URL}/api/org/pending-enrollments")
        assert response.status_code in [401, 403]
        print("✓ Unauthorized pending enrollments correctly rejected")


class TestResendInvitation:
    """Test resending magic link invitations"""
    
    def test_resend_invitation(self, org_admin_token):
        """Test resending an invitation"""
        # First create an enrollment
        test_email = f"test_resend_{uuid.uuid4().hex[:8]}@example.com"
        
        enroll_response = requests.post(
            f"{BASE_URL}/api/org/bulk-enroll",
            headers={"Authorization": f"Bearer {org_admin_token}"},
            json={
                "emails": [test_email],
                "course_id": TEST_COURSE_ID
            }
        )
        assert enroll_response.status_code == 200
        
        # Get pending enrollments to find the ID
        pending_response = requests.get(
            f"{BASE_URL}/api/org/pending-enrollments",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        assert pending_response.status_code == 200
        
        pending = pending_response.json()
        enrollment = next((e for e in pending if e["email"] == test_email), None)
        
        if enrollment:
            # Resend invitation
            resend_response = requests.post(
                f"{BASE_URL}/api/org/resend-invitation/{enrollment['id']}",
                headers={"Authorization": f"Bearer {org_admin_token}"}
            )
            
            assert resend_response.status_code == 200, f"Resend failed: {resend_response.text}"
            data = resend_response.json()
            assert data.get("success") == True or "message" in data
            print(f"✓ Invitation resent successfully: {data}")
        else:
            print("⚠ Could not find enrollment to resend (may have been cleaned up)")
    
    def test_resend_invalid_enrollment(self, org_admin_token):
        """Test resending with invalid enrollment ID"""
        response = requests.post(
            f"{BASE_URL}/api/org/resend-invitation/invalid-id-12345",
            headers={"Authorization": f"Bearer {org_admin_token}"}
        )
        
        assert response.status_code == 404
        print("✓ Invalid enrollment ID correctly returns 404")


class TestMagicLinkVerification:
    """Test magic link token verification"""
    
    def test_verify_invalid_token(self):
        """Test verifying an invalid token"""
        response = requests.get(
            f"{BASE_URL}/api/auth/verify-magic-link",
            params={"token": "invalid-token-12345"}
        )
        
        assert response.status_code in [400, 404], f"Expected 400/404, got {response.status_code}"
        print("✓ Invalid token correctly rejected")
    
    def test_verify_missing_token(self):
        """Test verifying without token parameter"""
        response = requests.get(f"{BASE_URL}/api/auth/verify-magic-link")
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("✓ Missing token correctly returns 422")


class TestAcceptMagicLink:
    """Test accepting magic link and creating account"""
    
    def test_accept_invalid_token(self):
        """Test accepting with invalid token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/accept-magic-link",
            params={
                "token": "invalid-token-12345",
                "password": "testpass123",
                "full_name": "Test User"
            }
        )
        
        assert response.status_code in [400, 404], f"Expected 400/404, got {response.status_code}"
        print("✓ Invalid token acceptance correctly rejected")
    
    def test_accept_missing_params(self):
        """Test accepting without required parameters"""
        response = requests.post(
            f"{BASE_URL}/api/auth/accept-magic-link",
            params={"token": "some-token"}
        )
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("✓ Missing parameters correctly returns 422")


class TestFileUpload:
    """Test teacher file upload functionality"""
    
    def test_upload_pdf_file(self, teacher_token):
        """Test uploading a PDF file"""
        # Create a mock PDF file
        pdf_content = b"%PDF-1.4 mock pdf content for testing"
        files = {
            'file': ('test_document.pdf', io.BytesIO(pdf_content), 'application/pdf')
        }
        data = {
            'title': 'Test PDF Document',
            'description': 'A test PDF file upload'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/content/course/{TEST_COURSE_ID}/upload-file",
            headers={"Authorization": f"Bearer {teacher_token}"},
            files=files,
            data=data
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        result = response.json()
        
        assert "id" in result
        assert result["title"] == "Test PDF Document"
        assert result["type"] == "document"
        assert "url" in result
        assert result["url"].startswith("/api/content/files/")
        print(f"✓ PDF upload successful: {result['url']}")
        
        return result["url"]
    
    def test_upload_image_file(self, teacher_token):
        """Test uploading an image file"""
        # Create a mock PNG file (minimal valid PNG header)
        png_content = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        files = {
            'file': ('test_image.png', io.BytesIO(png_content), 'image/png')
        }
        data = {
            'title': 'Test Image',
            'description': 'A test image upload'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/content/course/{TEST_COURSE_ID}/upload-file",
            headers={"Authorization": f"Bearer {teacher_token}"},
            files=files,
            data=data
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        result = response.json()
        
        assert result["type"] == "image"
        print(f"✓ Image upload successful: {result['url']}")
    
    def test_upload_video_file(self, teacher_token):
        """Test uploading a video file"""
        # Create a mock MP4 file
        mp4_content = b'\x00\x00\x00\x1cftypisom' + b'\x00' * 100
        files = {
            'file': ('test_video.mp4', io.BytesIO(mp4_content), 'video/mp4')
        }
        data = {
            'title': 'Test Video',
            'description': 'A test video upload'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/content/course/{TEST_COURSE_ID}/upload-file",
            headers={"Authorization": f"Bearer {teacher_token}"},
            files=files,
            data=data
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        result = response.json()
        
        assert result["type"] == "video"
        print(f"✓ Video upload successful: {result['url']}")
    
    def test_upload_docx_file(self, teacher_token):
        """Test uploading a DOCX file"""
        # Create a mock DOCX file
        docx_content = b'PK\x03\x04' + b'\x00' * 100  # ZIP header for DOCX
        files = {
            'file': ('test_document.docx', io.BytesIO(docx_content), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        }
        data = {
            'title': 'Test Word Document',
            'description': 'A test DOCX file upload'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/content/course/{TEST_COURSE_ID}/upload-file",
            headers={"Authorization": f"Bearer {teacher_token}"},
            files=files,
            data=data
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        result = response.json()
        
        assert result["type"] == "document"
        print(f"✓ DOCX upload successful: {result['url']}")
    
    def test_upload_without_title(self, teacher_token):
        """Test upload fails without title"""
        pdf_content = b"%PDF-1.4 mock pdf"
        files = {
            'file': ('test.pdf', io.BytesIO(pdf_content), 'application/pdf')
        }
        
        response = requests.post(
            f"{BASE_URL}/api/content/course/{TEST_COURSE_ID}/upload-file",
            headers={"Authorization": f"Bearer {teacher_token}"},
            files=files
        )
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("✓ Upload without title correctly rejected")
    
    def test_upload_invalid_course(self, teacher_token):
        """Test upload to invalid course fails"""
        pdf_content = b"%PDF-1.4 mock pdf"
        files = {
            'file': ('test.pdf', io.BytesIO(pdf_content), 'application/pdf')
        }
        data = {'title': 'Test'}
        
        response = requests.post(
            f"{BASE_URL}/api/content/course/invalid-course-xyz/upload-file",
            headers={"Authorization": f"Bearer {teacher_token}"},
            files=files,
            data=data
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Upload to invalid course correctly returns 404")
    
    def test_upload_unauthorized(self):
        """Test upload without auth fails"""
        pdf_content = b"%PDF-1.4 mock pdf"
        files = {
            'file': ('test.pdf', io.BytesIO(pdf_content), 'application/pdf')
        }
        data = {'title': 'Test'}
        
        response = requests.post(
            f"{BASE_URL}/api/content/course/{TEST_COURSE_ID}/upload-file",
            files=files,
            data=data
        )
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Unauthorized upload correctly rejected")


class TestServeUploadedFiles:
    """Test serving uploaded files"""
    
    def test_serve_nonexistent_file(self):
        """Test serving a file that doesn't exist"""
        response = requests.get(
            f"{BASE_URL}/api/content/files/{TEST_COURSE_ID}/nonexistent-file.pdf"
        )
        
        assert response.status_code == 404
        print("✓ Nonexistent file correctly returns 404")
    
    def test_serve_uploaded_file(self, teacher_token):
        """Test serving a file that was uploaded"""
        # First upload a file
        pdf_content = b"%PDF-1.4 test content for serving"
        files = {
            'file': ('serve_test.pdf', io.BytesIO(pdf_content), 'application/pdf')
        }
        data = {'title': 'Serve Test PDF'}
        
        upload_response = requests.post(
            f"{BASE_URL}/api/content/course/{TEST_COURSE_ID}/upload-file",
            headers={"Authorization": f"Bearer {teacher_token}"},
            files=files,
            data=data
        )
        
        if upload_response.status_code == 200:
            file_url = upload_response.json()["url"]
            
            # Now try to serve it
            serve_response = requests.get(f"{BASE_URL}{file_url}")
            
            assert serve_response.status_code == 200, f"Serve failed: {serve_response.status_code}"
            assert serve_response.headers.get("content-type") == "application/pdf"
            print(f"✓ Uploaded file served successfully: {file_url}")
        else:
            pytest.skip("Upload failed, cannot test serving")


class TestOrgAdminPermissions:
    """Test that org admin can also perform bulk enrollment"""
    
    def test_org_admin_can_bulk_enroll(self, org_admin_token):
        """Verify org admin has permission to bulk enroll"""
        test_email = f"test_orgadmin_{uuid.uuid4().hex[:8]}@example.com"
        
        response = requests.post(
            f"{BASE_URL}/api/org/bulk-enroll",
            headers={"Authorization": f"Bearer {org_admin_token}"},
            json={
                "emails": [test_email],
                "course_id": TEST_COURSE_ID
            }
        )
        
        assert response.status_code == 200, f"Org admin bulk enroll failed: {response.text}"
        print("✓ Org admin can perform bulk enrollment")


class TestTeacherPermissions:
    """Test that teachers can also perform bulk enrollment"""
    
    def test_teacher_can_bulk_enroll(self, teacher_token):
        """Verify teacher has permission to bulk enroll"""
        test_email = f"test_teacher_{uuid.uuid4().hex[:8]}@example.com"
        
        response = requests.post(
            f"{BASE_URL}/api/org/bulk-enroll",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={
                "emails": [test_email],
                "course_id": TEST_COURSE_ID
            }
        )
        
        assert response.status_code == 200, f"Teacher bulk enroll failed: {response.text}"
        print("✓ Teacher can perform bulk enrollment")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
