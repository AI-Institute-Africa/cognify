import base64
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone
from registry import models, serializers

# --- Helper to handle base64 padding ---
def _safe_base64_decode(data_str):
    if not data_str:
        return b''
    if ',' in data_str:
        data_str = data_str.split(',', 1)[1]
    missing_padding = len(data_str) % 4
    if missing_padding:
        data_str += '=' * (4 - missing_padding)
    return base64.b64decode(data_str)


# --- User & Profiles ---
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer


class OrganizationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Organization.objects.all()
    serializer_class = serializers.OrganizationSerializer


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Department.objects.all()
    serializer_class = serializers.DepartmentSerializer


# --- File Registry ---
class FileViewSet(viewsets.ModelViewSet):
    queryset = models.File.objects.all()
    serializer_class = serializers.FileSerializer


class BorrowViewSet(viewsets.ModelViewSet):
    queryset = models.Borrow.objects.all()
    serializer_class = serializers.BorrowSerializer


# --- Cloud Vault ---
class CloudFolderViewSet(viewsets.ModelViewSet):
    queryset = models.CloudFolder.objects.all()
    serializer_class = serializers.CloudFolderSerializer


class CloudFileViewSet(viewsets.ModelViewSet):
    queryset = models.CloudFile.objects.all()
    serializer_class = serializers.CloudFileSerializer


# --- Projects ---
class ProjectViewSet(viewsets.ModelViewSet):
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer


class ProjectTaskViewSet(viewsets.ModelViewSet):
    queryset = models.ProjectTask.objects.all()
    serializer_class = serializers.ProjectTaskSerializer


# --- Supply Requisition ViewSet ---
class SupplyRequisitionViewSet(viewsets.ModelViewSet):
    queryset = models.SupplyRequisition.objects.all()
    serializer_class = serializers.SupplyRequisitionSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return models.SupplyRequisition.objects.all()
        # Show requisitions user is involved in
        from django.db.models import Q
        return models.SupplyRequisition.objects.filter(
            Q(requester=user) |
            Q(supervisor=user) |
            Q(dept_manager=user) |
            Q(purchasing_officer=user) |
            Q(ceo=user) |
            Q(finance_officer=user)
        ).distinct()

    @action(detail=True, methods=['post'], url_path='sign', serializer_class=serializers.WorkflowActionSerializer)
    def sign(self, request, pk=None):
        req = self.get_object()

        if req.status == 'Rejected':
            return Response(
                {"error": f"Requisition {req.ref_number} is rejected and closed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if req.status == 'Approved':
            return Response(
                {"error": f"Requisition {req.ref_number} is already fully approved."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Map current status to stage name
        status_to_stage = {
            'Pending Requester':        'requester',
            'Pending Supervisor':       'supervisor',
            'Pending Dept':             'dept_manager',
            'Pending Deputy Director':   'deputy_director',
            'Pending Purchasing':       'purchasing_officer',
            'Pending Requester Review': 'requester_review',
            'Pending Purchasing Final': 'purchasing_officer_review',
            'Pending CEO':              'ceo',
            'Pending Finance':          'finance_officer',
        }
        stage = status_to_stage.get(req.status)
        if not stage:
            return Response(
                {"error": f"Requisition {req.ref_number} is in status '{req.status}' which cannot be signed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Map stage to expected user
        stage_user_map = {
            'requester':                 req.requester,
            'supervisor':                req.supervisor,
            'dept_manager':              req.dept_manager,
            'deputy_director':           req.deputy_director,
            'purchasing_officer':        req.purchasing_officer,
            'requester_review':          req.requester,
            'purchasing_officer_review': req.purchasing_officer,
            'ceo':                       req.ceo,
            'finance_officer':           req.finance_officer,
        }
        expected_user = stage_user_map.get(stage)
        if request.user != expected_user and not request.user.is_superuser:
            return Response(
                {"error": f"You are not authorized to sign at the current stage ({stage})."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate input parameters
        ser = self.get_serializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        action_type = ser.validated_data['action']
        comments = ser.validated_data.get('comments', '')

        # --- Handle Rejection ---
        if action_type == 'reject':
            rejection_reason = ser.validated_data.get('rejection_reason')
            
            stage_labels = {
                'supervisor':                'Supervisor',
                'dept_manager':              'Department Manager',
                'deputy_director':           'Deputy Director',
                'purchasing_officer':        'Purchasing Officer (Bid Analysis)',
                'requester_review':          'Requester Review',
                'purchasing_officer_review': 'Purchasing Officer (Final Review)',
                'ceo':                       'Chief Director',
                'finance_officer':           'Finance Officer',
            }
            rejected_stage_label = stage_labels.get(stage, stage)

            req.status = 'Rejected'
            req.rejection_reason = rejection_reason
            req.rejected_by = request.user
            req.rejected_at = timezone.now()
            req.rejected_stage = stage
            req.save()

            # Trigger email notification
            try:
                from registry.views import _notify_rejection
                _notify_rejection(req, req.requester, 'Requester', rejection_reason, f"/registry/supply_requisition/{req.pk}/")
            except Exception:
                pass

            return Response({
                "message": f"Requisition {req.ref_number} successfully rejected.",
                "status": req.status,
                "rejected_by": request.user.username,
                "rejected_stage": rejected_stage_label
            })

        # --- Handle Approval / Signing ---
        sig_data = ser.validated_data.get('signature_data', '')
        if not sig_data and 'proof_of_payment' not in request.FILES:
            # Requisition stage 3 & 5 & 7 might upload files, but signature data is generally required
            # If not provided, return error
            if stage not in ['finance_officer'] or not request.FILES.get('proof_of_payment'):
                return Response(
                    {"error": "signature_data is required for approval."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Stage specific logic
        if stage == 'purchasing_officer':
            bid_analysis = ser.validated_data.get('bid_analysis')
            date_received = ser.validated_data.get('date_received')
            purchase_order = ser.validated_data.get('purchase_order', '')
            if not bid_analysis:
                return Response({"error": "bid_analysis is required at purchasing_officer stage."}, status=status.HTTP_400_BAD_REQUEST)
            req.bid_analysis = bid_analysis
            req.save()

            # Handle quotations from JSON payload
            # Supporting: {"quotations": [{"supplier_name": "S1", "quoted_amount": 100, "is_chosen": true}, ...]}
            quotes_data = request.data.get('quotations', [])
            if quotes_data:
                req.quotations.all().delete()
                for i, qd in enumerate(quotes_data):
                    models.SupplierQuotation.objects.create(
                        requisition=req,
                        order=i+1,
                        supplier_name=qd.get('supplier_name', ''),
                        contact_person=qd.get('contact_person', ''),
                        phone=qd.get('phone', ''),
                        email=qd.get('email', ''),
                        quoted_amount=float(qd.get('quoted_amount', 0)),
                        is_chosen=qd.get('is_chosen', False),
                        notes=qd.get('notes', '')
                    )

        elif stage == 'finance_officer':
            payment_status = ser.validated_data.get('payment_status', 'Pending')
            req.payment_status = payment_status
            if 'proof_of_payment' in request.FILES:
                req.proof_of_payment = request.FILES['proof_of_payment']
            req.save()

        # Save signature record
        sig_obj, _ = models.RequisitionSignatory.objects.get_or_create(
            requisition=req,
            stage=stage,
            defaults={'user': request.user}
        )
        sig_obj.user = request.user
        sig_obj.is_signed = True
        sig_obj.date_signed = timezone.now()
        sig_obj.comments = comments
        if sig_data:
            sig_obj.signature_data = sig_data
        sig_obj.save()

        # Progress stage
        stage_transitions = {
            'requester':                 ('Pending Supervisor', 'supervisor'),
            'supervisor':                ('Pending Dept', 'dept_manager'),
            'dept_manager':              ('Pending Deputy Director', 'deputy_director'),
            'deputy_director':           ('Pending Purchasing', 'purchasing_officer'),
            'purchasing_officer':        ('Pending Requester Review', 'requester_review'),
            'requester_review':          ('Pending Purchasing Final', 'purchasing_officer_review'),
            'purchasing_officer_review': ('Pending CEO', 'ceo'),
            'ceo':                       ('Pending Finance', 'finance_officer'),
            'finance_officer':           ('Approved', None),
        }
        next_status, next_stage = stage_transitions[stage]
        req.status = next_status
        req.save()

        # Send notifications
        try:
            from registry.views import _notify_next_stage, _notify_fully_approved
            if next_stage:
                next_user = stage_user_map[next_stage]
                _notify_next_stage(req, next_user, next_stage.replace('_', ' ').title(), f"/registry/supply_requisition/{req.pk}/sign/{next_stage}/")
            else:
                _notify_fully_approved(req)
        except Exception:
            pass

        # Trigger auto-bundling
        try:
            from registry.views import _bundle_requisition_to_cloud
            _bundle_requisition_to_cloud(request, req)
        except Exception:
            pass

        return Response({
            "message": f"Requisition {req.ref_number} successfully signed.",
            "status": req.status,
            "next_stage": next_stage
        })


# --- BRD ViewSet ---
class BRDViewSet(viewsets.ModelViewSet):
    queryset = models.BRD.objects.all()
    serializer_class = serializers.BRDSerializer

    def perform_create(self, serializer):
        serializer.save(initiator=self.request.user)

    @action(detail=True, methods=['post'], url_path='sign', serializer_class=serializers.WorkflowActionSerializer)
    def sign(self, request, pk=None):
        brd = self.get_object()

        if brd.status == 'Rejected':
            return Response({"error": "BRD is rejected and closed."}, status=status.HTTP_400_BAD_REQUEST)
        if brd.status == 'Approved':
            return Response({"error": "BRD is already fully approved."}, status=status.HTTP_400_BAD_REQUEST)

        # Find this user's BRDApprover record for this BRD
        approver_record = brd.approvers.filter(user=request.user).first()
        if not approver_record and not request.user.is_superuser:
            return Response(
                {"error": "You are not an assigned approver for this BRD."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Prevent double-signing
        if approver_record and approver_record.has_signed():
            return Response(
                {"error": "You have already signed this BRD."},
                status=status.HTTP_400_BAD_REQUEST
            )

        ser = self.get_serializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        action_type = ser.validated_data['action']
        comments = ser.validated_data.get('comments', '')

        if action_type == 'reject':
            rejection_reason = ser.validated_data.get('rejection_reason')
            brd.status = 'Rejected'
            brd.rejection_reason = rejection_reason
            brd.rejected_by = request.user
            brd.rejected_at = timezone.now()
            brd.save()
            return Response({"message": "BRD successfully rejected.", "status": brd.status})

        sig_data = ser.validated_data.get('signature_data', '')
        if not sig_data:
            return Response({"error": "signature_data is required for approval."}, status=status.HTTP_400_BAD_REQUEST)

        # Create signature record (linked to BRDApprover)
        models.BRDSignature.objects.create(
            brd=brd,
            approver=approver_record,
            signature_data=sig_data,
            designation=getattr(approver_record, 'designation', ''),
            comments=comments
        )

        # Check quorums and advance BRD status
        level_order = ['PMT', 'HODs', 'Board']
        if brd.pmt_quorum_met() and brd.hods_quorum_met() and brd.board_quorum_met():
            brd.status = 'Approved'
        elif not brd.pmt_quorum_met():
            brd.status = 'Awaiting PMT'
        elif not brd.hods_quorum_met():
            brd.status = 'Awaiting HODs'
        else:
            brd.status = 'Awaiting Board'
        brd.save()

        return Response({
            "message": "BRD successfully signed.",
            "status": brd.status,
            "pmt_quorum_met": brd.pmt_quorum_met(),
            "hods_quorum_met": brd.hods_quorum_met(),
            "board_quorum_met": brd.board_quorum_met(),
        })
