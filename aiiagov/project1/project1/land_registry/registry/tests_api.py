"""
RIFTS-X System-Wide REST API Tests
====================================
Covers authentication, CRUD, workflow actions, and permission checks
for all major API endpoints.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.utils import timezone
import json

from registry import models


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def create_user(username, password='testpass123', **kwargs):
    return User.objects.create_user(username=username, password=password, **kwargs)


def get_token(user):
    token, _ = Token.objects.get_or_create(user=user)
    return token.key


# ─────────────────────────────────────────────────────────────────────────────
# 1. Token Authentication Tests
# ─────────────────────────────────────────────────────────────────────────────

class TokenAuthTests(APITestCase):
    """Test obtaining and using auth tokens."""

    def setUp(self):
        self.user = create_user('tokenuser', 'pass1234')
        self.token_url = '/registry/api/token-auth/'

    def test_obtain_token_valid_credentials(self):
        resp = self.client.post(self.token_url, {
            'username': 'tokenuser',
            'password': 'pass1234'
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('token', resp.data)

    def test_obtain_token_invalid_credentials(self):
        resp = self.client.post(self.token_url, {
            'username': 'tokenuser',
            'password': 'wrongpassword'
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authenticated_request_succeeds(self):
        token = get_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        resp = self.client.get('/registry/api/users/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_unauthenticated_request_rejected(self):
        resp = self.client.get('/registry/api/users/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ─────────────────────────────────────────────────────────────────────────────
# 2. User Endpoint Tests
# ─────────────────────────────────────────────────────────────────────────────

class UserAPITests(APITestCase):
    """Read-only user listing/detail."""

    def setUp(self):
        self.admin = create_user('admin_u', is_staff=True, is_superuser=True)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {get_token(self.admin)}')

    def test_list_users(self):
        resp = self.client.get('/registry/api/users/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_user(self):
        resp = self.client.get(f'/registry/api/users/{self.admin.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['username'], 'admin_u')

    def test_user_list_contains_full_name(self):
        self.admin.first_name = 'Admin'
        self.admin.last_name = 'User'
        self.admin.save()
        resp = self.client.get(f'/registry/api/users/{self.admin.pk}/')
        self.assertIn('full_name', resp.data)
        self.assertEqual(resp.data['full_name'], 'Admin User')

    def test_user_endpoint_is_read_only(self):
        resp = self.client.post('/registry/api/users/', {'username': 'hacker'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Organization & Department Tests
# ─────────────────────────────────────────────────────────────────────────────

class OrganizationAPITests(APITestCase):
    def setUp(self):
        self.user = create_user('orguser')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {get_token(self.user)}')

    def test_list_organizations(self):
        resp = self.client.get('/registry/api/organizations/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_organizations_is_read_only(self):
        resp = self.client.post('/registry/api/organizations/', {'name': 'Test Org'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class DepartmentAPITests(APITestCase):
    def setUp(self):
        self.user = create_user('deptuser')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {get_token(self.user)}')

    def test_list_departments(self):
        resp = self.client.get('/registry/api/departments/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Cloud Folder & File Tests
# ─────────────────────────────────────────────────────────────────────────────

class CloudAPITests(APITestCase):
    def setUp(self):
        self.user = create_user('clouduser')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {get_token(self.user)}')

    def test_list_cloud_folders(self):
        resp = self.client.get('/registry/api/cloud-folders/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_list_cloud_files(self):
        resp = self.client.get('/registry/api/cloud-files/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Project & Task Tests
# ─────────────────────────────────────────────────────────────────────────────

class ProjectAPITests(APITestCase):
    def setUp(self):
        self.user = create_user('projectuser')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {get_token(self.user)}')

    def test_list_projects(self):
        resp = self.client.get('/registry/api/projects/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_list_project_tasks(self):
        resp = self.client.get('/registry/api/project-tasks/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# 6. Supply Requisition Tests
# ─────────────────────────────────────────────────────────────────────────────

def make_requisition_users():
    """Create a full set of requisition workflow users."""
    requester = create_user('req_user')
    supervisor = create_user('supervisor')
    dept_mgr = create_user('dept_mgr')
    purchasing = create_user('purchasing')
    ceo = create_user('ceo')
    finance = create_user('finance')
    return requester, supervisor, dept_mgr, purchasing, ceo, finance


class SupplyRequisitionAPITests(APITestCase):
    def setUp(self):
        self.requester, self.supervisor, self.dept_mgr, self.purchasing, self.ceo, self.finance = make_requisition_users()
        self.admin = create_user('sr_admin', is_superuser=True, is_staff=True)

        # Create a requisition
        self.req = models.SupplyRequisition.objects.create(
            requester=self.requester,
            supervisor=self.supervisor,
            dept_manager=self.dept_mgr,
            purchasing_officer=self.purchasing,
            ceo=self.ceo,
            finance_officer=self.finance,
            purpose='API test requisition',
            status='Pending Requester',
        )

    def _auth(self, user):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {get_token(user)}')

    # --- List / Retrieve ---

    def test_admin_can_list_all_requisitions(self):
        self._auth(self.admin)
        resp = self.client.get('/registry/api/requisitions/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(resp.data), 1)

    def test_requester_sees_their_own_requisition(self):
        self._auth(self.requester)
        resp = self.client.get('/registry/api/requisitions/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Handle both paginated ({count, results: [...]}) and plain list responses
        results = resp.data.get('results', resp.data) if isinstance(resp.data, dict) else resp.data
        pks = [r['id'] for r in results]
        self.assertIn(self.req.pk, pks)

    def test_retrieve_requisition_detail(self):
        self._auth(self.requester)
        resp = self.client.get(f'/registry/api/requisitions/{self.req.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['id'], self.req.pk)

    def test_requisition_detail_includes_nested_data(self):
        self._auth(self.admin)
        resp = self.client.get(f'/registry/api/requisitions/{self.req.pk}/')
        self.assertIn('items', resp.data)
        self.assertIn('quotations', resp.data)
        self.assertIn('signatories', resp.data)
        self.assertIn('requester_details', resp.data)

    # --- Workflow: Requester Sign ---

    def test_requester_sign_approves_stage_1(self):
        self._auth(self.requester)
        resp = self.client.post(
            f'/registry/api/requisitions/{self.req.pk}/sign/',
            {'action': 'approve', 'signature_data': 'data:image/png;base64,abc123=='},
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Pending Supervisor')

    def test_wrong_user_cannot_sign(self):
        # dept_mgr tries to sign at requester stage
        self._auth(self.dept_mgr)
        resp = self.client.post(
            f'/registry/api/requisitions/{self.req.pk}/sign/',
            {'action': 'approve', 'signature_data': 'data:image/png;base64,abc123=='},
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_sign_requires_signature_data(self):
        self._auth(self.requester)
        resp = self.client.post(
            f'/registry/api/requisitions/{self.req.pk}/sign/',
            {'action': 'approve'},  # missing signature_data
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Workflow: Rejection ---

    def test_dept_manager_can_reject(self):
        # Move to dept stage first
        self.req.status = 'Pending Dept'
        self.req.save()

        self._auth(self.dept_mgr)
        resp = self.client.post(
            f'/registry/api/requisitions/{self.req.pk}/sign/',
            {'action': 'reject', 'rejection_reason': 'Budget exceeded'},
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Rejected')
        self.assertEqual(self.req.rejection_reason, 'Budget exceeded')
        self.assertEqual(self.req.rejected_by, self.dept_mgr)
        self.assertEqual(self.req.rejected_stage, 'dept_manager')

    def test_rejection_requires_reason(self):
        self.req.status = 'Pending Dept'
        self.req.save()

        self._auth(self.dept_mgr)
        resp = self.client.post(
            f'/registry/api/requisitions/{self.req.pk}/sign/',
            {'action': 'reject'},  # missing rejection_reason
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_sign_rejected_requisition(self):
        self.req.status = 'Rejected'
        self.req.rejection_reason = 'Old rejection'
        self.req.save()

        self._auth(self.requester)
        resp = self.client.post(
            f'/registry/api/requisitions/{self.req.pk}/sign/',
            {'action': 'approve', 'signature_data': 'data:image/png;base64,abc123=='},
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_sign_approved_requisition(self):
        self.req.status = 'Approved'
        self.req.save()

        self._auth(self.requester)
        resp = self.client.post(
            f'/registry/api/requisitions/{self.req.pk}/sign/',
            {'action': 'approve', 'signature_data': 'data:image/png;base64,abc123=='},
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Full Workflow Simulation ---

    def test_full_workflow_progression(self):
        """Walk the requisition through every stage to Approved."""
        self._auth(self.requester)

        # Stage 1: Requester
        resp = self.client.post(
            f'/registry/api/requisitions/{self.req.pk}/sign/',
            {'action': 'approve', 'signature_data': 'data:image/png;base64,abc123=='},
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Pending Supervisor')

        # Stage 2: Supervisor
        self._auth(self.supervisor)
        resp = self.client.post(
            f'/registry/api/requisitions/{self.req.pk}/sign/',
            {'action': 'approve', 'signature_data': 'data:image/png;base64,abc123=='},
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Pending Dept')

        # Stage 3: Dept Manager
        self._auth(self.dept_mgr)
        resp = self.client.post(
            f'/registry/api/requisitions/{self.req.pk}/sign/',
            {'action': 'approve', 'signature_data': 'data:image/png;base64,abc123=='},
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Pending Purchasing')

        # Stage 3: Purchasing Officer (with bid analysis)
        self._auth(self.purchasing)
        resp = self.client.post(
            f'/registry/api/requisitions/{self.req.pk}/sign/',
            {
                'action': 'approve',
                'signature_data': 'data:image/png;base64,abc123==',
                'bid_analysis': 'Three quotes obtained. Supplier A is cheapest.',
            },
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Pending Requester Review')

        # Stage 4: Requester Review
        self._auth(self.requester)
        resp = self.client.post(
            f'/registry/api/requisitions/{self.req.pk}/sign/',
            {'action': 'approve', 'signature_data': 'data:image/png;base64,abc123=='},
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Pending Purchasing Final')

        # Stage 5: Purchasing Final Review
        self._auth(self.purchasing)
        resp = self.client.post(
            f'/registry/api/requisitions/{self.req.pk}/sign/',
            {'action': 'approve', 'signature_data': 'data:image/png;base64,abc123=='},
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Pending CEO')

        # Stage 6: CEO
        self._auth(self.ceo)
        resp = self.client.post(
            f'/registry/api/requisitions/{self.req.pk}/sign/',
            {'action': 'approve', 'signature_data': 'data:image/png;base64,abc123=='},
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Pending Finance')

        # Stage 7: Finance Officer
        self._auth(self.finance)
        resp = self.client.post(
            f'/registry/api/requisitions/{self.req.pk}/sign/',
            {'action': 'approve', 'signature_data': 'data:image/png;base64,abc123=='},
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.req.refresh_from_db()
        self.assertEqual(self.req.status, 'Approved')


# ─────────────────────────────────────────────────────────────────────────────
# 7. BRD Tests
# ─────────────────────────────────────────────────────────────────────────────

from django.core.files.uploadedfile import SimpleUploadedFile

class BRDAPITests(APITestCase):
    def setUp(self):
        self.initiator = create_user('brd_initiator')
        self.pmt_approver = create_user('brd_pmt')
        self.hod_approver = create_user('brd_hod')
        self.board_approver = create_user('brd_board')
        self.non_approver = create_user('brd_outsider')
        self.admin = create_user('brd_admin', is_superuser=True, is_staff=True)

        # BRD requires a document file
        dummy_pdf = SimpleUploadedFile('test.pdf', b'%PDF-test', content_type='application/pdf')

        # Create a BRD (one approver per level, required count = 1 each)
        self.brd = models.BRD.objects.create(
            title='Test BRD',
            initiator=self.initiator,
            document=dummy_pdf,
            status='Awaiting PMT',
            pmt_required=1,
            hods_required=1,
            board_required=1,
        )
        # Create approvers at each level
        self.pmt_approver_obj = models.BRDApprover.objects.create(
            brd=self.brd,
            user=self.pmt_approver,
            level='PMT',
            order=1,
        )
        self.hod_approver_obj = models.BRDApprover.objects.create(
            brd=self.brd,
            user=self.hod_approver,
            level='HODs',
            order=2,
        )
        self.board_approver_obj = models.BRDApprover.objects.create(
            brd=self.brd,
            user=self.board_approver,
            level='Board',
            order=3,
        )

    def _auth(self, user):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {get_token(user)}')

    def test_list_brds(self):
        self._auth(self.admin)
        resp = self.client.get('/registry/api/brds/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_brd(self):
        self._auth(self.admin)
        resp = self.client.get(f'/registry/api/brds/{self.brd.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['title'], 'Test BRD')
        self.assertIn('approvers', resp.data)
        self.assertIn('pmt_quorum_met', resp.data)

    def test_brd_pmt_sign(self):
        self._auth(self.pmt_approver)
        resp = self.client.post(
            f'/registry/api/brds/{self.brd.pk}/sign/',
            {'action': 'approve', 'signature_data': 'data:image/png;base64,abc123=='},
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.brd.refresh_from_db()
        self.assertTrue(self.brd.pmt_quorum_met())

    def test_brd_non_approver_rejected(self):
        self._auth(self.non_approver)
        resp = self.client.post(
            f'/registry/api/brds/{self.brd.pk}/sign/',
            {'action': 'approve', 'signature_data': 'data:image/png;base64,abc123=='},
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_brd_full_approval_all_levels(self):
        """All three levels sign — BRD should reach Approved."""
        # PMT signs
        self._auth(self.pmt_approver)
        self.client.post(
            f'/registry/api/brds/{self.brd.pk}/sign/',
            {'action': 'approve', 'signature_data': 'data:image/png;base64,abc123=='},
            format='json'
        )
        # HOD signs
        self._auth(self.hod_approver)
        self.client.post(
            f'/registry/api/brds/{self.brd.pk}/sign/',
            {'action': 'approve', 'signature_data': 'data:image/png;base64,abc123=='},
            format='json'
        )
        # Board signs
        self._auth(self.board_approver)
        resp = self.client.post(
            f'/registry/api/brds/{self.brd.pk}/sign/',
            {'action': 'approve', 'signature_data': 'data:image/png;base64,abc123=='},
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.brd.refresh_from_db()
        self.assertEqual(self.brd.status, 'Approved')

    def test_brd_reject(self):
        self._auth(self.pmt_approver)
        resp = self.client.post(
            f'/registry/api/brds/{self.brd.pk}/sign/',
            {'action': 'reject', 'rejection_reason': 'Scope is unclear'},
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.brd.refresh_from_db()
        self.assertEqual(self.brd.status, 'Rejected')
        self.assertEqual(self.brd.rejection_reason, 'Scope is unclear')

    def test_cannot_sign_rejected_brd(self):
        self.brd.status = 'Rejected'
        self.brd.save()
        self._auth(self.pmt_approver)
        resp = self.client.post(
            f'/registry/api/brds/{self.brd.pk}/sign/',
            {'action': 'approve', 'signature_data': 'data:image/png;base64,abc123=='},
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_brd_sign_requires_signature_data(self):
        self._auth(self.pmt_approver)
        resp = self.client.post(
            f'/registry/api/brds/{self.brd.pk}/sign/',
            {'action': 'approve'},  # no signature_data
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_double_sign_prevented(self):
        """Same approver cannot sign twice."""
        self._auth(self.pmt_approver)
        self.client.post(
            f'/registry/api/brds/{self.brd.pk}/sign/',
            {'action': 'approve', 'signature_data': 'data:image/png;base64,abc123=='},
            format='json'
        )
        resp = self.client.post(
            f'/registry/api/brds/{self.brd.pk}/sign/',
            {'action': 'approve', 'signature_data': 'data:image/png;base64,abc123=='},
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)



# ─────────────────────────────────────────────────────────────────────────────
# 8. API Root & Router Discovery
# ─────────────────────────────────────────────────────────────────────────────

class APIRootTests(APITestCase):
    def setUp(self):
        self.user = create_user('root_user')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {get_token(self.user)}')

    def test_api_root_lists_endpoints(self):
        resp = self.client.get('/registry/api/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # Check key endpoints are present in the root
        expected_keys = ['users', 'organizations', 'departments', 'files',
                         'cloud-folders', 'cloud-files', 'projects',
                         'project-tasks', 'brds', 'requisitions']
        for key in expected_keys:
            self.assertIn(key, resp.data, msg=f"'{key}' not found in API root")

    def test_api_root_unauthenticated_rejected(self):
        self.client.credentials()  # clear auth
        resp = self.client.get('/registry/api/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
