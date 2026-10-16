from rest_framework import serializers
from django.contrib.auth.models import User
from registry import models

# --- User & Profiles ---
class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Organization
        fields = '__all__'


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Department
        fields = '__all__'


# --- File Registry ---
class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.File
        fields = '__all__'


class FolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Folio
        fields = '__all__'


class BorrowSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Borrow
        fields = '__all__'


# --- Cloud Vault ---
class CloudFolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CloudFolder
        fields = '__all__'


class CloudFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CloudFile
        fields = '__all__'


class CloudShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CloudShare
        fields = '__all__'


# --- Projects & Tasks ---
class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Project
        fields = '__all__'


class ProjectTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProjectTask
        fields = '__all__'


class ProjectSprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProjectSprint
        fields = '__all__'


# --- Supply Requisition ---
class RequisitionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RequisitionItem
        fields = '__all__'
        read_only_fields = ['requisition']


class SupplierQuotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SupplierQuotation
        fields = '__all__'
        read_only_fields = ['requisition']


class RequisitionSignatorySerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)

    class Meta:
        model = models.RequisitionSignatory
        fields = '__all__'


class SupplyRequisitionSerializer(serializers.ModelSerializer):
    items = RequisitionItemSerializer(many=True, required=False)
    quotations = SupplierQuotationSerializer(many=True, read_only=True)
    signatories = RequisitionSignatorySerializer(many=True, read_only=True)
    requester_details = UserSerializer(source='requester', read_only=True)
    supervisor_details = UserSerializer(source='supervisor', read_only=True)
    dept_manager_details = UserSerializer(source='dept_manager', read_only=True)
    purchasing_officer_details = UserSerializer(source='purchasing_officer', read_only=True)
    ceo_details = UserSerializer(source='ceo', read_only=True)
    finance_officer_details = UserSerializer(source='finance_officer', read_only=True)

    class Meta:
        model = models.SupplyRequisition
        fields = '__all__'
        read_only_fields = [
            'ref_number', 'requester', 'status', 'grand_total',
            'rejection_reason', 'rejected_by', 'rejected_at', 'rejected_stage'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        # Set requester as authenticated user from context
        validated_data['requester'] = self.context['request'].user
        validated_data['status'] = 'Pending Requester'
        
        requisition = models.SupplyRequisition.objects.create(**validated_data)
        
        for item_data in items_data:
            models.RequisitionItem.objects.create(requisition=requisition, **item_data)
            
        requisition.save() # Triggers any calculations/ref_number generation
        return requisition


# --- BRD Governance ---
class BRDApproverSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    has_signed = serializers.SerializerMethodField()

    class Meta:
        model = models.BRDApprover
        fields = '__all__'

    def get_has_signed(self, obj):
        return obj.has_signed()


class BRDSignatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BRDSignature
        fields = '__all__'


class BRDSerializer(serializers.ModelSerializer):
    approvers = BRDApproverSerializer(many=True, read_only=True)
    signatures = BRDSignatureSerializer(many=True, read_only=True)
    initiator_details = UserSerializer(source='initiator', read_only=True)
    pmt_quorum_met = serializers.SerializerMethodField()
    hods_quorum_met = serializers.SerializerMethodField()
    board_quorum_met = serializers.SerializerMethodField()

    class Meta:
        model = models.BRD
        fields = '__all__'
        read_only_fields = ['initiator', 'status']

    def get_pmt_quorum_met(self, obj):
        return obj.pmt_quorum_met()

    def get_hods_quorum_met(self, obj):
        return obj.hods_quorum_met()

    def get_board_quorum_met(self, obj):
        return obj.board_quorum_met()


# --- Requisition/BRD Action Serializer ---
class WorkflowActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    signature_data = serializers.CharField(required=False, allow_blank=True, help_text='Base64 signature canvas data')
    comments = serializers.CharField(required=False, allow_blank=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    
    # Purchasing stage specifics
    date_received = serializers.DateField(required=False)
    purchase_order = serializers.CharField(required=False, allow_blank=True)
    bid_analysis = serializers.CharField(required=False, allow_blank=True)
    
    # Finance stage specifics
    payment_status = serializers.ChoiceField(choices=['Pending', 'Paid'], required=False)
    proof_of_payment = serializers.FileField(required=False)

    def validate(self, data):
        action = data.get('action')
        if action == 'reject' and not data.get('rejection_reason'):
            raise serializers.ValidationError({"rejection_reason": "Rejection reason is required when rejecting."})
        return data
