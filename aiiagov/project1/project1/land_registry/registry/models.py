import datetime
from decimal import Decimal
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image
from django.contrib.auth.models import User
from django.contrib.auth.base_user import BaseUserManager

# ──────────────────────────────────────────────────────────────────────────────
# INSTITUTIONAL CLOUD ARCHIVING UTILITY
# ──────────────────────────────────────────────────────────────────────────────

def archive_to_cloud(file_field, file_name, folder_name, department, user, description=""):
    """
    Archives any uploaded file into the Institutional Cloud (CloudFolder / CloudFile / CloudFileVersion).
    Automatically creates the folder if it doesn't exist.
    Safe to call even if file_field is empty.
    
    Args:
        file_field: A Django FileField / ImageField instance (already saved on a model instance)
        file_name:  Desired name for the cloud file record
        folder_name: Name of the cloud folder (e.g. 'Goods Received Scans')
        department: Department model instance (can be None — skips archiving)
        user:       User who performed the upload
        description: Optional text description for the cloud file

    Returns:
        CloudFileVersion instance if successful, None otherwise.
    """
    if not file_field or not department:
        return None
    
    # Lazy import to avoid circular imports at module load time
    from django.apps import apps
    CloudFolder = apps.get_model('registry', 'CloudFolder')
    CloudFile = apps.get_model('registry', 'CloudFile')
    CloudFileVersion = apps.get_model('registry', 'CloudFileVersion')
    
    try:
        folder, _ = CloudFolder.objects.get_or_create(
            name=folder_name,
            parent=None,
            department=department,
            defaults={'created_by': user}
        )
        
        cloud_file, created = CloudFile.objects.get_or_create(
            name=file_name,
            folder=folder,
            defaults={
                'description': description,
                'owner': user,
                'classification_level': 'Departmental',
            }
        )
        
        last_version = cloud_file.versions.order_by('-version_number').first()
        next_version_number = (last_version.version_number + 1) if last_version else 1
        
        cfv = CloudFileVersion(
            cloud_file=cloud_file,
            version_number=next_version_number,
            uploaded_by=user,
            commit_message=description or f"Uploaded {file_name}",
        )
        cfv.file_content.save(file_field.name.split('/')[-1], file_field.file, save=False)
        
        # Calculate file size
        try:
            cfv.file_size = file_field.size
        except Exception:
            cfv.file_size = 0
        
        cfv.save()
        return cfv
    except Exception:
        # Cloud archiving is non-critical — never fail the main save
        return None

# Create your models here.
class Organization(models.Model):
    name = models.CharField(max_length=250)
    code = models.CharField(max_length=100, unique=True) # e.g., 'MINISTRY_OF_LANDS'
    api_endpoint = models.URLField(max_length=500, blank=True, null=True)
    public_key = models.TextField(blank=True, null=True)
    is_local = models.BooleanField(default=False)
    date_added = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        verbose_name_plural = "Organizations"

class Department(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="departments", null=True, blank=True)
    name = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    efficiency_score = models.FloatField(default=100.0)
    date_added = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Departments"

class FileLocation(models.Model):
    building = models.CharField(max_length=250)
    floor = models.CharField(max_length=250)
    office = models.CharField(max_length=250, blank=True, null=True)
    cabinet = models.CharField(max_length=250)
    shelf = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.building} - {self.floor} - {self.cabinet} - {self.shelf}"

    class Meta:
        verbose_name_plural = "File Locations"

class SLAConfig(models.Model):
    priority = models.CharField(max_length=50, unique=True) # High, Medium, Low
    max_days_user = models.IntegerField(default=3)
    max_days_department = models.IntegerField(default=7)
    escalation_level_1 = models.CharField(max_length=100, default='Supervisor')
    escalation_level_2 = models.CharField(max_length=100, default='Executive')

    def __str__(self):
        return f"SLA: {self.priority}"

class Category(models.Model):
    name = models.CharField(max_length=250)
    description = models.TextField(blank=True, null= True)
    status = models.CharField(max_length=2, choices=(('1','Active'), ('2','Inactive')), default = 1)
    delete_flag = models.IntegerField(default = 0)
    date_added = models.DateTimeField(default = timezone.now)
    date_created = models.DateTimeField(auto_now = True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return str(f"{self.name}")

class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete= models.CASCADE)
    name = models.CharField(max_length=250)
    description = models.TextField(blank=True, null= True)
    status = models.CharField(max_length=2, choices=(('1','Active'), ('2','Inactive')), default = 1)
    delete_flag = models.IntegerField(default = 0)
    date_added = models.DateTimeField(default = timezone.now)
    date_created = models.DateTimeField(auto_now = True)

    class Meta:
        verbose_name_plural = "Sub Categories"

    def __str__(self):
        return str(f"{self.category} - {self.name}")

class RetentionRule(models.Model):
    name = models.CharField(max_length=250)
    years_to_keep = models.IntegerField(default=7)
    action_after_expiry = models.CharField(max_length=100, choices=(('Archive', 'Archive'), ('Destroy', 'Destroy'), ('Review', 'Review')), default='Archive')
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.years_to_keep} Years)"

    class Meta:
        verbose_name_plural = "Retention Rules"

class File(models.Model):
    sub_category = models.ForeignKey(SubCategory, on_delete= models.CASCADE)
    ref_num = models.CharField(max_length=250)
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True, null= True)
    status = models.CharField(max_length=2, choices=(('1','Active'), ('2','Inactive')), default = 1)
    delete_flag = models.IntegerField(default = 0)
    date_added = models.DateTimeField(default = timezone.now)
    date_created = models.DateTimeField(auto_now = True)
    is_encrypted = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.ref_num:
            import datetime
            count = File.objects.count() + 1
            self.ref_num = f"ZRP-DOC-{timezone.now().year}-{count:05d}"
        # Encrypt sensitive fields if not already encrypted
        if hasattr(self, 'sensitivity_level') and self.sensitivity_level in ['Sensitive', 'Highly Confidential'] and not self.is_encrypted:
            from .services.security import EncryptionService
            self.title = EncryptionService.encrypt(self.title)
            self.description = EncryptionService.encrypt(self.description)
            self.is_encrypted = True
        super(File, self).save(*args, **kwargs)
    f_status = models.CharField(max_length=10, default='available')#choices=(('available', 'Available'), ('borrowed', 'Borrowed')))
    file_attachment = models.FileField(upload_to='file_attachments/', blank=True, null=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    risk_score = models.IntegerField(default=0) # 0-100
    risk_level = models.CharField(max_length=20, default='Low')
    is_lost = models.BooleanField(default=False)
    current_location = models.ForeignKey(FileLocation, on_delete=models.SET_NULL, null=True, blank=True)
    current_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    last_moved_at = models.DateTimeField(null=True, blank=True)
    last_handler = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="last_handled_files")
    CLASSIFICATION_CHOICES = (
        ('Open Access', 'Open Access'),
        ('Departmental', 'Departmental'),
        ('Confidential', 'Confidential'),
        ('Restricted/Highly Confidential', 'Restricted/Highly Confidential'),
    )
    sensitivity_level = models.CharField(max_length=20, choices=(('Normal', 'Normal'), ('Sensitive', 'Sensitive'), ('Highly Confidential', 'Highly Confidential')), default='Normal')
    classification_level = models.CharField(max_length=50, choices=CLASSIFICATION_CHOICES, default='Departmental')
    retention_rule = models.ForeignKey(RetentionRule, on_delete=models.SET_NULL, null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    external_link = models.URLField(max_length=500, null=True, blank=True)

    class Meta:
        verbose_name_plural = "List of Files"

    def __str__(self):
        return str(f"{self.ref_num} - {self.title}")

@receiver(post_save, sender=File)
def file_post_save(sender, instance, created, **kwargs):
    if created:
        if not instance.qr_code:
            from registry.utils.qr_utils import generate_file_qr
            generate_file_qr(instance.id)
        
        # Instantiate Digital Twin
        from registry.services.twin import DigitalTwinService
        DigitalTwinService.instantiate_twin(instance)

class Borrower(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="borrower_profile")
    code = models.CharField(max_length=250)
    employee_number = models.CharField(max_length=150, blank=True, null=True, help_text="ZRP Official Employee Number")
    first_name = models.CharField(max_length=250)
    middle_name = models.CharField(max_length=250, blank=True, null= True)
    last_name = models.CharField(max_length=250)
    gender = models.CharField(max_length=20, choices=(('Male','Male'), ('Female','Female')), default = 'Male')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    department_old = models.CharField(max_length=250, blank= True, null = True)
    email = models.EmailField(max_length=250, blank=True, null=True)
    position = models.CharField(max_length=200, blank=True, null=True)
    grade_level = models.CharField(max_length=100, blank=True, null=True)
    employment_status = models.CharField(max_length=50, choices=(('Active','Active'), ('On Leave','On Leave'), ('Probation','Probation'), ('Suspended','Suspended'), ('Terminated','Terminated')), default='Active')
    date_of_appointment = models.DateField(blank=True, null=True)
    contact_phone = models.CharField(max_length=50, blank=True, null=True)
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="supervising_employees")
    
    # Leave Balances
    annual_leave_balance = models.PositiveIntegerField(default=30)
    sick_leave_balance = models.PositiveIntegerField(default=12)
    maternity_paternity_leave_balance = models.PositiveIntegerField(default=90)
    special_leave_balance = models.PositiveIntegerField(default=12)
    study_leave_balance = models.PositiveIntegerField(default=15)
    
    status = models.CharField(max_length=2, choices=(('1','Active'), ('2','Inactive')), default = 1)
    delete_flag = models.IntegerField(default = 0)
    date_added = models.DateTimeField(default = timezone.now)
    date_created = models.DateTimeField(auto_now = True)

    class Meta:
        verbose_name_plural = "List of Borrowers"

    def __str__(self):
        mid = f" {self.middle_name}" if self.middle_name else ""
        fn = self.first_name or ""
        ln = self.last_name or ""
        return f"{self.code} - {fn}{mid} {ln}".strip()

    def name(self):
        mid = f" {self.middle_name}" if self.middle_name else ""
        fn = self.first_name or ""
        ln = self.last_name or ""
        full = f"{fn}{mid} {ln}".strip()
        if not full and self.user:
            return self.user.get_full_name() or self.user.username
        return full or "Employee"

    def save(self, *args, **kwargs):
        if not self.code:
            count = Borrower.objects.count() + 1
            self.code = f"ZRP-EMP-{count:04d}"
        if not self.employee_number:
            self.employee_number = self.code
        super().save(*args, **kwargs)

class Borrow(models.Model):
    STATUS_CHOICES = (
        ('0', 'Issued'),
        ('1', 'Returned'),
    )
    borrower = models.ForeignKey(Borrower, on_delete= models.CASCADE, related_name="borrower_id_fk", null=True)
    file_doc = models.ForeignKey(File, on_delete= models.CASCADE, related_name="file_doc_id_fk", null=True)
    borrowing_date = models.DateField()
    return_date = models.DateField()
    folio_ref = models.CharField(max_length=250, null=True)
    status = models.CharField(max_length=5, choices=STATUS_CHOICES, default = '0')
    modification_notes = models.TextField(blank=True, null=True)
    modified_file = models.FileField(upload_to='modified_files/', blank=True, null=True)
    issued_folder = models.ForeignKey('CloudFolder', on_delete=models.SET_NULL, null=True, blank=True, related_name='issued_borrows')
    folder_permission = models.CharField(max_length=10, choices=(('view', 'View Only'), ('edit', 'Edit Allowed')), default='view')
    folder_zip = models.FileField(upload_to='issued_folder_zips/', blank=True, null=True)
    access_token = models.CharField(max_length=100, blank=True, null=True)
    token_expiry = models.DateTimeField(blank=True, null=True)
    temp_password = models.CharField(max_length=100, blank=True, null=True)
    borrower_signature = models.TextField(blank=True, null=True, help_text='Base64-encoded PNG signature from borrower upon return')
    issuer_signature = models.TextField(blank=True, null=True, help_text='Base64-encoded PNG signature from issuer upon acceptance')
    return_confirmed = models.BooleanField(default=False, help_text='Issuer has confirmed receipt and acceptance of returned file')
    confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='confirmed_returns')
    confirmed_at = models.DateTimeField(null=True, blank=True, help_text='Timestamp when issuer confirmed the return')
    date_added = models.DateTimeField(default = timezone.now)
    date_created = models.DateTimeField(auto_now = True)
    count_issue=models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Borrowing Transactions"


    def __str__(self):
        return str(f"{self.borrower.code}")

class Folio(models.Model):
    filee = models.ForeignKey(File, on_delete= models.CASCADE)
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True, null= True)
    #status = models.CharField(max_length=2, choices=(('1','Active'), ('2','Inactive')), default = 1)
    delete_flag = models.IntegerField(default = 0)
    date_added = models.DateTimeField(default = timezone.now)
    date_created = models.DateTimeField(auto_now = True)

    class Meta:
        verbose_name_plural = "Folio"

    def __str__(self):
        return str(f"{self.filee} - {self.title}")

class FederationLink(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Active', 'Active'),
        ('Revoked', 'Revoked'),
    )
    source_org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="federation_links_out")
    target_org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="federation_links_in")
    link_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    permissions = models.JSONField(default=dict, blank=True)
    shared_secret = models.CharField(max_length=250, blank=True, null=True)
    date_established = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Link: {self.source_org.code} -> {self.target_org.code} ({self.link_status})"

    class Meta:
        unique_together = ('source_org', 'target_org')

class ForensicAudit(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=250)
    method = models.CharField(max_length=10)
    path = models.TextField()
    payload = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Forensic Audit Logs"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.timestamp} - {self.user} - {self.action}"

class SecureLink(models.Model):
    file_doc = models.ForeignKey(File, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    expires_at = models.DateTimeField()
    access_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return timezone.now() < self.expires_at

    def __str__(self):
        return f"Link for {self.file_doc.title} ({self.token})"

class DigitalShare(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('returned', 'Returned'),
    )
    file_doc = models.ForeignKey(File, on_delete=models.CASCADE, related_name="digital_shares")
    shared_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shares_initiated")
    shared_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shares_received")
    token = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    expires_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Share: {self.file_doc.title} to {self.shared_to.username}"

class FileVersion(models.Model):
    file_doc = models.ForeignKey(File, on_delete=models.CASCADE, related_name="versions")
    borrower = models.ForeignKey(Borrower, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='file_versions/')
    date_created = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "File Versions"
        ordering = ['-date_created']

    def __str__(self):
        return f"Version of {self.file_doc.title} by {self.borrower.name() if self.borrower else 'Unknown'}"

class CustodyLog(models.Model):
    file_doc = models.ForeignKey(File, on_delete=models.CASCADE, related_name="custody_logs")
    handler = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    from_organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True, related_name="transfers_out")
    to_organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True, related_name="transfers_in")
    from_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name="transfers_out")
    to_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name="transfers_in")
    action = models.CharField(max_length=100) # Created, Handover, Transfer, Archived
    reason = models.TextField(blank=True, null=True)
    location = models.ForeignKey(FileLocation, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    digital_signature = models.TextField(blank=True, null=True) # For non-repudiation
    acknowledged = models.BooleanField(default=False)
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="custody_received")
    received_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

class LeaveRequest(models.Model):
    LEAVE_TYPES = (
        ('Annual', 'Annual Leave'),
        ('Sick', 'Sick Leave'),
        ('Maternity', 'Maternity Leave'),
        ('Paternity', 'Paternity Leave'),
        ('Special', 'Special Leave'),
        ('Study', 'Study Leave'),
        ('Casual', 'Casual Leave'),
        ('Other', 'Other Approved Category'),
    )
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled'),
    )
    WORKFLOW_STAGES = (
        ('Leave Request', '1. Leave Request Submitted'),
        ('Supervisor Recommendation', '2. Supervisor Recommendation'),
        ('HR Review', '3. HR Verification & Review'),
        ('Approval', '4. Executive Approval'),
        ('Leave Register', '5. Logged in Leave Register'),
        ('Notification', '6. Departure & Notification Sent'),
        ('Return from Leave', '7. Returned from Leave'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="leave_requests")
    leave_type = models.CharField(max_length=50, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    
    # Acting / Alternative Officer
    acting_officer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="acting_officer_duties", help_text="Acting / Alternative Officer while away")
    
    # 7-Stage Workflow Tracking
    workflow_stage = models.CharField(max_length=50, choices=WORKFLOW_STAGES, default='Leave Request')
    supervisor_recommendation = models.CharField(max_length=30, choices=(('Pending', 'Pending'), ('Recommended', 'Recommended'), ('Not Recommended', 'Not Recommended')), default='Pending')
    supervisor_notes = models.TextField(blank=True, null=True)
    hr_review_status = models.CharField(max_length=30, choices=(('Pending', 'Pending'), ('Verified', 'Verified & Cleared'), ('Queried', 'Query Raised')), default='Pending')
    hr_notes = models.TextField(blank=True, null=True)
    
    supporting_document = models.FileField(upload_to='leave_documents/', blank=True, null=True)
    signed_document = models.FileField(upload_to='leave_documents/signed/', blank=True, null=True)
    approvers = models.ManyToManyField(User, blank=True, related_name='leave_requests_to_approve')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    supervisor_comment = models.TextField(blank=True, null=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="leaves_approved")
    
    # ZRP Hierarchy — staged approval tier tracking
    APPROVAL_STAGE_CHOICES = (
        ('pending_management',       'Pending Management Tier (Systems Manager / Supt ICT / Chief Tech)'),
        ('pending_deputy_director',  'Pending Deputy Director'),
        ('pending_chief_director',   'Pending Chief Director'),
        ('complete',                 'All Tiers Approved'),
    )
    approval_stage = models.CharField(
        max_length=30,
        choices=APPROVAL_STAGE_CHOICES,
        default='pending_management',
        blank=True,
        help_text='Current ZRP hierarchy approval tier for this leave request',
    )

    # Return from leave tracking
    is_returned = models.BooleanField(default=False)
    actual_return_date = models.DateField(blank=True, null=True)

    date_applied = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.leave_type} ({self.start_date} to {self.end_date})"

    def approver_names(self):
        return ", ".join([u.get_full_name() or u.username for u in self.approvers.all()])

    @property
    def days(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0

    @property
    def days_requested(self):
        return self.days

class LeaveRequestApproval(models.Model):
    leave_request = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE, related_name='approvals')
    approver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_approvals')
    status = models.CharField(max_length=20, choices=LeaveRequest.STATUS_CHOICES)
    comment = models.TextField(blank=True, null=True)
    signature_data = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('leave_request', 'approver')
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.approver.username} - {self.leave_request} - {self.status}"

class Budget(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="budgets")
    fiscal_year = models.CharField(max_length=10) # e.g., "2024"
    total_allocation = models.DecimalField(max_digits=15, decimal_places=2)
    spent_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    date_added = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.department.name} - {self.fiscal_year} ({self.total_allocation})"

    @property
    def remaining_amount(self):
        return self.total_allocation - self.spent_amount

class Requisition(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Fulfilled', 'Fulfilled'),
    )
    requestor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="requisitions")
    item_name = models.CharField(max_length=250)
    quantity = models.IntegerField(default=1)
    estimated_unit_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    budget_line = models.ForeignKey(Budget, on_delete=models.SET_NULL, null=True, blank=True, related_name="requisitions_linked")
    financial_document = models.FileField(upload_to='financial_docs/', blank=True, null=True)
    purpose = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    approver_comment = models.TextField(blank=True, null=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="requisitions_approved")
    date_requested = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.item_name} - {self.requestor.username}"

class Expenditure(models.Model):
    requisition = models.OneToOneField(Requisition, on_delete=models.CASCADE, related_name="expenditure")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date_paid = models.DateTimeField(default=timezone.now)
    reference_no = models.CharField(max_length=100, unique=True)
    payment_voucher = models.FileField(upload_to='payment_vouchers/', blank=True, null=True)

    def __str__(self):
        return f"Exp: {self.reference_no} - {self.amount}"

class CostRecovery(models.Model):
    CATEGORY_CHOICES = (
        ('Labour', 'Labour Savings'),
        ('Materials', 'Materials & Procurement'),
        ('Overheads', 'General Overheads'),
        ('Contracts', 'Contract Renegotiation'),
        ('Technology', 'Technology Optimisation'),
        ('Other', 'Other'),
    )
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="cost_recoveries")
    hod = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cost_recoveries_submitted")
    amount_recovered = models.DecimalField(max_digits=15, decimal_places=2)
    cost_savings_category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Other')
    description = models.TextField()
    evidence_document = models.FileField(upload_to='cost_recovery_evidence/', blank=True, null=True)
    date_recorded = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-date_recorded']

    def __str__(self):
        return f"{self.department.name} — {self.cost_savings_category} — {self.amount_recovered}"

class Meeting(models.Model):
    MEETING_TYPES = (
        ('Commission', 'Commission Board Meeting'),
        ('Committee', 'Committee Meeting'),
        ('Executive', 'Executive Management Meeting'),
        ('Departmental', 'Departmental Meeting'),
        ('General', 'General Meeting'),
    )
    MEETING_MODES = (
        ('live', 'Real-Time (Live Session)'),
        ('uploaded', 'Post-Meeting Upload'),
    )
    APPROVAL_STATUS_CHOICES = (
        ('Draft', 'Draft Minutes'),
        ('Secretary Review', 'Secretary Review'),
        ('Chairperson Review', 'Chairperson Review'),
        ('Corrections Required', 'Corrections Required'),
        ('Approved', 'Approved'),
        ('Distributed', 'Distributed'),
        ('Closed', 'Closed'),
    )
    title = models.CharField(max_length=250)
    meeting_date = models.DateTimeField()
    meeting_type = models.CharField(max_length=50, choices=MEETING_TYPES)
    meeting_mode = models.CharField(max_length=20, choices=MEETING_MODES, default='live')
    location = models.CharField(max_length=250, blank=True, null=True)
    venue_or_link = models.CharField(max_length=500, blank=True, null=True, help_text="Venue location or Virtual Online Meeting Link (Zoom/MS Teams)")
    
    chairperson = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="chaired_meetings")
    secretary = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="secretary_meetings")
    participants = models.ManyToManyField(User, related_name="attended_meetings", blank=True)
    apologies = models.ManyToManyField(User, related_name="apology_meetings", blank=True)
    apologies_text = models.TextField(blank=True, null=True, help_text="Free text list of non-registered apologies")
    
    agenda = models.FileField(upload_to='meeting_agendas/', blank=True, null=True)
    agenda_text = models.TextField(blank=True, null=True, help_text="Detailed meeting agenda items")
    minutes = models.FileField(upload_to='meeting_minutes/', blank=True, null=True)
    minutes_text = models.TextField(blank=True, null=True, help_text="Transcribed or typed meeting minutes")
    discussions = models.TextField(blank=True, null=True, help_text="Detailed recorded meeting discussions")
    supporting_documents = models.ManyToManyField(File, related_name="meeting_documents", blank=True)
    
    approval_status = models.CharField(max_length=30, choices=APPROVAL_STATUS_CHOICES, default='Draft')
    secretary_reviewed_at = models.DateTimeField(null=True, blank=True)
    chairperson_approved_at = models.DateTimeField(null=True, blank=True)
    rejection_notes = models.TextField(blank=True, null=True)
    
    organized_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_meetings")
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.meeting_date.date()})"


class MeetingActionItem(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Overdue', 'Overdue'),
    )
    PRIORITY_CHOICES = (
        ('Normal', 'Normal'),
        ('High', 'High'),
        ('Urgent', 'Urgent'),
    )
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name="action_items")
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assigned_meeting_actions")
    description = models.TextField()
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Normal')
    progress_percent = models.IntegerField(default=0)
    completion_date = models.DateTimeField(null=True, blank=True)
    is_escalated = models.BooleanField(default=False)
    escalated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date', '-priority']

    def __str__(self):
        return f"Action: {self.description[:40]} -> {self.assigned_to.username} ({self.status})"


class ActionItemComment(models.Model):
    action_item = models.ForeignKey(MeetingActionItem, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="meeting_action_comments")
    comment = models.TextField()
    progress_percent = models.IntegerField(null=True, blank=True)
    attachment = models.FileField(upload_to='action_item_comments/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on Action {self.action_item.id}"


class MeetingNotification(models.Model):
    NOTIFICATION_TYPES = (
        ('New Meeting', 'New Meeting Scheduled'),
        ('Invitation', 'Meeting Invitation'),
        ('Agenda Submission', 'Agenda Submitted'),
        ('Minutes Awaiting Review', 'Minutes Awaiting Review'),
        ('Assigned Action', 'Assigned Action Item'),
        ('Upcoming Deadline', 'Upcoming Action Deadline'),
        ('Overdue Action', 'Overdue Action Alert'),
        ('Escalation', 'Overdue Escalation Alert'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="meeting_notifications")
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications")
    action_item = models.ForeignKey(MeetingActionItem, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications")
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.notification_type}] for {self.user.username}: {self.message[:50]}"


class Resolution(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Implemented', 'Implemented'),
    )
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name="resolutions")
    resolution_number = models.CharField(max_length=100)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    files = models.ManyToManyField(File, related_name="linked_resolutions", blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_resolutions")
    deadline = models.DateField(blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.resolution_number} - {self.meeting.title}"

# --- Procurement & Contract Lifecycle Management ---

class Tender(models.Model):
    TENDER_STATUS = (
        ('Draft', 'Draft'),
        ('Published', 'Published'),
        ('Evaluation', 'Evaluation'),
        ('Awarded', 'Awarded'),
        ('Cancelled', 'Cancelled'),
    )
    requisition = models.ForeignKey(Requisition, on_delete=models.SET_NULL, null=True, blank=True, related_name="tenders")
    title = models.CharField(max_length=250)
    ref_num = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    tender_type = models.CharField(max_length=50, choices=(('Open', 'Open'), ('Restricted', 'Restricted'), ('Direct', 'Direct')))
    budget = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    closing_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=TENDER_STATUS, default='Draft')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="tenders")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="tenders_created")
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ref_num} - {self.title}"

class Bid(models.Model):
    # ... (existing Bid model)
    BID_STATUS = (
        ('Pending', 'Pending Review'),
        ('Successful', 'Successful'),
        ('Unsuccessful', 'Unsuccessful'),
    )
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, related_name="bids")
    bidder_name = models.CharField(max_length=250)
    bidder_email = models.EmailField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    submission_date = models.DateTimeField(default=timezone.now)
    proposal_doc = models.FileField(upload_to='tender_bids/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=BID_STATUS, default='Pending')
    evaluation_score = models.FloatField(default=0.0)
    evaluation_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Bid by {self.bidder_name} for {self.tender.ref_num}"

class Contract(models.Model):
    CONTRACT_STATUS = (
        ('Active', 'Active'),
        ('Completed', 'Completed'),
        ('Expired', 'Expired'),
        ('Terminated', 'Terminated'),
    )
    tender = models.OneToOneField(Tender, on_delete=models.CASCADE, related_name="contract")
    awarded_bid = models.OneToOneField(Bid, on_delete=models.CASCADE, related_name="contract_awarded")
    title = models.CharField(max_length=250)
    contract_ref = models.CharField(max_length=100, unique=True)
    physical_file = models.ForeignKey(File, on_delete=models.SET_NULL, null=True, blank=True, help_text="Link to physical file trail")
    start_date = models.DateField()
    end_date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=CONTRACT_STATUS, default='Active')
    contract_document = models.FileField(upload_to='contracts/', blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.contract_ref} - {self.title}"

class ContractMilestone(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="milestones")
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    due_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=(('Pending', 'Pending'), ('Met', 'Met'), ('Overdue', 'Overdue')), default='Pending')

    def __str__(self):
        return f"{self.contract.contract_ref} - {self.title}"

class PerformanceEvaluation(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="evaluations")
    evaluation_date = models.DateField(default=timezone.now)
    score = models.IntegerField(help_text="1-10", default=5)
    comments = models.TextField()
    evaluated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Evaluation for {self.contract.contract_ref} ({self.evaluation_date})"

# --- Asset & Inventory Tracking ---

class Asset(models.Model):
    CATEGORY_CHOICES = (
        ('ICT', 'ICT Equipment'),
        ('Furniture', 'Office Furniture'),
        ('Vehicle', 'Motor Vehicle'),
        ('Machinery', 'Industrial Machinery'),
        ('Other', 'Other Assets'),
    )
    STATUS_CHOICES = (
        ('Active', 'In Use / Active'),
        ('Maintenance', 'Under Maintenance'),
        ('Disposed', 'Disposed / Retired'),
        ('Lost', 'Missing / Lost'),
        ('Issued', 'Issued / Dispatched'),
    )
    ITEM_TYPE_CHOICES = (
        ('Asset', 'Capital / Fixed Asset'),
        ('Inventory', 'Inventory / Stock / Consumables'),
    )
    name = models.CharField(max_length=250)
    asset_code = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    item_type = models.CharField(max_length=50, choices=ITEM_TYPE_CHOICES, default='Asset', help_text="Classification (Capital Asset vs Inventory / Stock)")
    contract = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True, related_name="assets", help_text="Procurement linkage")
    physical_file = models.ForeignKey(File, on_delete=models.SET_NULL, null=True, blank=True, help_text="Physical file trail linkage")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="assets")
    acquisition_date = models.DateField()
    acquisition_cost = models.DecimalField(max_digits=15, decimal_places=2)
    useful_life = models.IntegerField(help_text="Expected useful life in years")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Active')
    description = models.TextField(blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    # --- Supplier Intake & PMU Linkage ---
    supplier_name = models.CharField(max_length=250, blank=True, null=True)
    delivery_note_number = models.CharField(max_length=100, blank=True, null=True)
    delivery_note_doc = models.FileField(upload_to='assets/delivery_notes/', blank=True, null=True, help_text="Supplier Delivery Note")
    invoice_number = models.CharField(max_length=100, blank=True, null=True)
    invoice_doc = models.FileField(upload_to='assets/invoices/', blank=True, null=True, help_text="Supplier Invoice")
    pmu_source_doc_ref = models.CharField(max_length=100, blank=True, null=True, help_text="PMU Supporting Reference (PO / Contract / Tender)")
    pmu_source_doc = models.FileField(upload_to='assets/pmu_docs/', blank=True, null=True, help_text="PMU Supporting Document")
    quantity_expected = models.PositiveIntegerField(default=1, null=True, blank=True, help_text="Quantity expected as per PMU supporting documentation / PO")
    quantity_delivered = models.PositiveIntegerField(default=1, null=True, blank=True, help_text="Quantity actually delivered by supplier (supports partial deliveries e.g. 20 instead of 25)")

    # --- Technician Testing & Quality Clearance ---
    INSPECTION_STATUS_CHOICES = (
        ('Pending Inspection', 'Pending Inspection'),
        ('Testing in Progress', 'Testing in Progress'),
        ('Quality Approved', 'Quality Approved / Cleared'),
        ('Rejected', 'Rejected / Non-Compliant'),
    )
    technician = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="inspected_assets")
    technician_name = models.CharField(max_length=200, blank=True, null=True, help_text="Testing Officer / Inspector Name (typed text)")
    inspection_status = models.CharField(max_length=50, choices=INSPECTION_STATUS_CHOICES, default='Pending Inspection')
    inspection_date = models.DateField(null=True, blank=True)
    inspection_notes = models.TextField(blank=True, null=True, help_text="Technician quality test remarks and test metrics")
    quality_test_passed = models.BooleanField(default=False)
    
    # Three Mandatory Technician Approval Documents
    approval_doc_1 = models.FileField(upload_to='assets/approval_docs/', blank=True, null=True, help_text="1. Technical Inspection & Testing Certificate")
    approval_doc_2 = models.FileField(upload_to='assets/approval_docs/', blank=True, null=True, help_text="2. Quality Assurance & Compliance Report")
    approval_doc_3 = models.FileField(upload_to='assets/approval_docs/', blank=True, null=True, help_text="3. Asset Acceptance & Clearance Certificate")
    is_cleared = models.BooleanField(default=False, help_text="Cleared when technician quality testing passes and approval documents are supplied")

    unit_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Unit cost per item/serial number")

    # --- Link to Goods Received Ledger (Asset references from GR entry) ---
    goods_received_entry = models.ForeignKey(
        'GoodsReceivedEntry', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assets', help_text="Goods Received Register entry that brought this asset into store"
    )

    def __str__(self):
        return f"{self.asset_code} - {self.name}"
    
    @property
    def get_inspector_name(self):
        if self.technician_name:
            return self.technician_name
        if self.technician:
            return self.technician.get_full_name() or self.technician.username
        return "Unassigned"

    @property
    def is_partial_delivery(self):
        """Returns True if quantity delivered is less than expected from PMU documentation"""
        if self.quantity_expected and self.quantity_delivered:
            return self.quantity_delivered < self.quantity_expected
        return False

    @property
    def balance_pending_delivery(self):
        """Quantity still outstanding / pending from the supplier"""
        if self.quantity_expected and self.quantity_delivered:
            return max(0, self.quantity_expected - self.quantity_delivered)
        return 0

    @property
    def serial_count(self):
        cnt = self.serial_numbers.count()
        if cnt > 0:
            return cnt
        if self.quantity_delivered and self.quantity_delivered > 0:
            return self.quantity_delivered
        return 1

    @property
    def total_cost(self):
        """Total acquisition cost = unit_cost * number of serials/delivered (or acquisition_cost)"""
        cnt = self.serial_numbers.count()
        effective_qty = cnt if cnt > 0 else (self.quantity_delivered or 1)
        if self.unit_cost and self.unit_cost > 0:
            return self.unit_cost * effective_qty
        return self.acquisition_cost or (self.unit_cost if self.unit_cost else 0)

    @property
    def current_value(self):
        """Calculates current total book value using straight-line depreciation with Decimal arithmetic."""
        import datetime
        from decimal import Decimal

        cost = self.total_cost
        if not cost:
            return Decimal('0.00')
        if not self.useful_life or self.useful_life <= 0:
            return cost
        if not self.acquisition_date:
            return cost

        today = datetime.date.today()
        days_passed = (today - self.acquisition_date).days
        if days_passed <= 0:
            return cost

        years_passed = Decimal(str(days_passed)) / Decimal('365.25')
        useful_life_dec = Decimal(str(self.useful_life))
        if years_passed >= useful_life_dec:
            return Decimal('0.00')

        depreciation_per_year = cost / useful_life_dec
        value = cost - (depreciation_per_year * years_passed)
        return max(Decimal('0.00'), round(value, 2))

    @property
    def unit_current_value(self):
        from decimal import Decimal
        cnt = self.serial_count
        if cnt > 0:
            return round(self.current_value / Decimal(str(cnt)), 2)
        return self.current_value

class AssetSerialNumber(models.Model):
    STATUS_CHOICES = (
        ('Active', 'Active / In Use'),
        ('Faulty', 'Faulty / Unserviceable'),
        ('Under Repair', 'Under Repair'),
        ('Condemned', 'Condemned (Board of Survey)'),
        ('Disposed', 'Disposed'),
        ('Missing', 'Missing / Lost'),
        ('Issued', 'Issued / Dispatched'),
    )
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="serial_numbers")
    serial_number = models.CharField(max_length=150, db_index=True)
    barcode = models.CharField(max_length=150, blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Active')
    custodian = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="custody_serials")
    location = models.CharField(max_length=255, blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['serial_number']
        unique_together = ('asset', 'serial_number')

    def __str__(self):
        return f"{self.asset.name} (SN: {self.serial_number})"

class AssetMaintenance(models.Model):
    STATUS_CHOICES = (
        ('Scheduled', 'Scheduled'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Overdue', 'Overdue'),
    )
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="maintenance_logs")
    description = models.TextField()
    scheduled_date = models.DateField()
    performed_date = models.DateField(null=True, blank=True)
    cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Scheduled')
    performed_by = models.CharField(max_length=250, blank=True, null=True)

    def __str__(self):
        return f"Maintenance for {self.asset.asset_code} on {self.scheduled_date}"

class AssetCustody(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="custody_history")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assigned_assets")
    issue_date = models.DateField(default=timezone.now)
    return_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.asset.name} assigned to {self.user.username}"

class AssetDocument(models.Model):
    DOC_TYPES = (
        ('Delivery Note', 'Supplier Delivery Note'),
        ('Invoice', 'Supplier Invoice'),
        ('PMU Source Document', 'PMU Procurement Source Document'),
        ('Technical Test Cert', '1. Technical Testing Certificate'),
        ('QA Report', '2. Quality Assurance & Compliance Report'),
        ('Clearance Certificate', '3. Asset Acceptance & Clearance Certificate'),
        ('General Scan', 'Scanned Document / Archive Batch'),
    )
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="documents")
    doc_type = models.CharField(max_length=50, choices=DOC_TYPES)
    title = models.CharField(max_length=255)
    document_file = models.FileField(upload_to='assets/digital_archive/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date_uploaded = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date_uploaded']

    def __str__(self):
        return f"[{self.doc_type}] {self.title} - {self.asset.asset_code}"

# --- Statutory Form 60260-6: Board of Survey (BOS) Report ---

class BoardOfSurvey(models.Model):
    FORM_CODE = "G.P&S.34586-S."
    FORM_NUMBER = "60260-6"
    
    STATUS_CHOICES = (
        ('Draft', 'Draft Proceedings'),
        ('Conducted', 'Proceedings Held / Signed by Board'),
        ('Approved', 'Approved by Head of Department'),
        ('Disposed', 'Disposed by Officer-in-Charge'),
        ('Rejected', 'Disapproved / Returned'),
    )
    DISPOSAL_RECOMMENDATION_CHOICES = (
        ('Sold', '(a) Sold'),
        ('Parts Utilised', '(b) Sent to centre for parts to be utilised'),
        ('Destroyed', '(c) Order that they should be destroyed'),
        ('Transfer', '(d) Transfer / Reallocated'),
    )

    report_ref = models.CharField(max_length=100, unique=True, default='', help_text="Official BOS Reference")
    held_at = models.CharField(max_length=255, default='ZRP ICT Central Stores', help_text="Proceedings of a Board of Survey held at...")
    proceedings_date = models.DateField(default=timezone.now, help_text="Held on date")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="board_of_surveys")
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Draft')
    
    # Board Members (Minimum 2 - 4 officers forming the Board of Survey)
    member_1_name = models.CharField(max_length=200, help_text="Board Member 1 (Presiding Officer / Chairman)")
    member_1_rank = models.CharField(max_length=100, blank=True, null=True)
    member_2_name = models.CharField(max_length=200, help_text="Board Member 2")
    member_2_rank = models.CharField(max_length=100, blank=True, null=True)
    member_3_name = models.CharField(max_length=200, blank=True, null=True, help_text="Board Member 3")
    member_3_rank = models.CharField(max_length=100, blank=True, null=True)
    member_4_name = models.CharField(max_length=200, blank=True, null=True, help_text="Board Member 4")
    member_4_rank = models.CharField(max_length=100, blank=True, null=True)
    
    board_signed_date = models.DateField(null=True, blank=True)
    
    # Head of Department Approval
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_surveys")
    approval_date = models.DateField(null=True, blank=True)
    approval_notes = models.TextField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    
    # Officer-in-Charge Certification of Disposal
    officer_in_charge = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="disposed_surveys")
    disposal_certification_date = models.DateField(null=True, blank=True)
    disposal_notes = models.TextField(blank=True, null=True, help_text="Certificate of destruction / sale receipt / dispatch notes")
    sale_cash_receipt_no = models.CharField(max_length=100, blank=True, null=True, help_text="If case of sale, cash receipt / account reference")
    destruction_certificate_file = models.FileField(upload_to='assets/bos_certificates/', blank=True, null=True)
    is_disposed = models.BooleanField(default=False)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-proceedings_date', '-date_created']

    def __str__(self):
        return f"Form {self.FORM_NUMBER} - {self.report_ref} ({self.held_at})"

    @property
    def total_condemned_value(self):
        total = Decimal('0.00')
        for item in self.items.all():
            total += (item.value or Decimal('0.00'))
        return total

    @property
    def total_value(self):
        return self.total_condemned_value

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())

class BoardOfSurveyItem(models.Model):
    DISPOSAL_RECOMMENDATION_CHOICES = (
        ('Sold', '(a) Sold'),
        ('Parts Utilised', '(b) Sent to centre for parts to be utilised'),
        ('Destroyed', '(c) Order that they should be destroyed'),
        ('Transfer', '(d) Transfer / Reallocated'),
    )

    board_of_survey = models.ForeignKey(BoardOfSurvey, on_delete=models.CASCADE, related_name="items")
    asset = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, blank=True, related_name="bos_items")
    serial_number = models.ForeignKey(AssetSerialNumber, on_delete=models.SET_NULL, null=True, blank=True, related_name="bos_items")
    
    description = models.CharField(max_length=255, help_text="Description of article")
    serial_numbers_list = models.TextField(blank=True, null=True, help_text="Serial numbers included")
    quantity = models.IntegerField(default=1, help_text="Number or quantity")
    value = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text="Value ($)")
    reason_for_condemning = models.TextField(help_text="Reason for condemning")
    disposal_recommendation = models.CharField(max_length=50, choices=DISPOSAL_RECOMMENDATION_CHOICES, default='Sold', help_text="How recommended to be disposed of")
    disposal_remarks = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.description} (Qty: {self.quantity})"


# --- Statutory Z.R.P. FORM 27: Requisition/Issue Voucher ---

class ZrpForm27Voucher(models.Model):
    FORM_NUMBER = "FORM 27"
    DEPARTMENT_DEFAULT = "Z.R.POLICE  I.C.T"

    STATUS_CHOICES = (
        ('Draft', 'Draft Voucher'),
        ('Issued', 'Issued by Stores'),
        ('Dispatched', 'Dispatched / In Transit'),
        ('Received', 'Received & Signed by Station'),
    )

    voucher_no = models.CharField(max_length=50, unique=True, help_text="e.g. 85/26")
    date = models.DateField(default=timezone.now, help_text="Voucher Date")
    issued_by = models.CharField(max_length=255, default="O.I.C CENTRAL RADIO STORES   (I.C.T)", help_text="Issued by officer designation")
    station = models.CharField(max_length=255, help_text="Station / Section receiving items")
    station_date = models.DateField(null=True, blank=True, help_text="Station Date")
    requisition_no = models.CharField(max_length=100, blank=True, null=True, help_text="Station Requisition No.")
    how_dispatched = models.CharField(max_length=255, blank=True, null=True, help_text="How Dispatched (Vehicle, Courier, Hand)")
    checker = models.CharField(max_length=200, default="CST KADIKI", help_text="Checker Name & Force Number (text fallback)")
    checker_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="form27_checker_entries", help_text="Checker selected from system users")
    checker_date = models.DateField(default=timezone.now, help_text="Checker Date")
    
    # Destination station receiver signoff
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Issued')
    received_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="form27_received_entries", help_text="Station receiving officer selected from system users")
    received_by_name = models.CharField(max_length=200, blank=True, null=True, help_text="Officer receiving at station")
    received_by_force_no = models.CharField(max_length=100, blank=True, null=True, help_text="Force Number / Rank")
    received_date = models.DateField(null=True, blank=True)
    
    # Digital archive attachment
    signed_voucher_scan = models.FileField(upload_to='assets/form27_scans/', blank=True, null=True, help_text="Scanned signed copy of Form 27")

    # --- REVERSE SIDE: Block (1) Member Requisitioning Goods ---
    # "Certified that all items listed overleaf are essential for the maintenance of Police communication"
    cert_essential_communication = models.BooleanField(default=False, help_text="Block (1): Member certifies items are essential for Police communication maintenance")
    cert_member_name = models.CharField(max_length=200, blank=True, null=True, help_text="Block (1): Officer / Member-in-Charge Name & Force No.")
    cert_member_date = models.DateField(null=True, blank=True, help_text="Block (1): Date of member certification")

    # --- REVERSE SIDE: Block (2) Provincial ICT Officer (PICTO) Demand Reasons ---
    # "Tools and/or Equipment are demanded for the following reasons:-"
    demand_reasons = models.TextField(blank=True, null=True, help_text="Block (2): Reasons why tools/equipment are demanded (PICTO)")
    picto_name = models.CharField(max_length=200, blank=True, null=True, help_text="Block (2): PICTO Name & Designation")
    picto_date_stamp = models.DateField(null=True, blank=True, help_text="Block (2): PICTO Date Stamp")

    # --- REVERSE SIDE: Block (3) Director ICT Approval ---
    # "Issues Approved. Remarks..."
    director_approved = models.BooleanField(default=False, help_text="Block (3): Director ICT has approved the issue")
    director_remarks = models.TextField(blank=True, null=True, help_text="Block (3): Director ICT Remarks")
    director_name = models.CharField(max_length=200, blank=True, null=True, help_text="Block (3): Director ICT Name")
    director_date_stamp = models.DateField(null=True, blank=True, help_text="Block (3): Director ICT Date Stamp")

    # --- REVERSE SIDE: Block (4) Receiving Provincial/District ICT Officer ---
    # "Certified the items overleaf have been received and correctly recorded on the relevant copy of the Stores/Equipment Ledger or Inventory"
    receipt_ledger_certified = models.BooleanField(default=False, help_text="Block (4): Receiving officer certifies items received and correctly recorded in ledger/inventory")
    receiving_ict_officer = models.CharField(max_length=200, blank=True, null=True, help_text="Block (4): Provincial/District ICT Officer Name")
    receiving_date_stamp = models.DateField(null=True, blank=True, help_text="Block (4): Receiving ICT Officer Date Stamp")

    # --- Electronic Receipt Confirmation Signoff (Optional for Supt ICT, Chief Tech, System Manager, Provincial ICT Officers) ---
    electronic_signature_confirmed = models.BooleanField(default=False, help_text="Electronically signed/confirmed receipt of goods (optional)")
    electronic_signed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="form27_electronic_signatures")
    electronic_signed_name = models.CharField(max_length=200, blank=True, null=True, help_text="Name & Rank of signing officer")
    electronic_signed_role = models.CharField(max_length=100, blank=True, null=True, help_text="Role at time of confirmation (Supt ICT, Chief Tech, System Manager, Provincial ICT Officer)")
    electronic_signed_date = models.DateTimeField(null=True, blank=True, help_text="Timestamp of electronic confirmation")
    electronic_signature_notes = models.TextField(blank=True, null=True, help_text="Confirmation remarks or goods condition verification")
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-id']
        verbose_name = "Z.R.P. Form 27 Voucher"
        verbose_name_plural = "Z.R.P. Form 27 Vouchers"

    def __str__(self):
        return f"Form 27 No. {self.voucher_no} - {self.station} ({self.date})"

    @property
    def total_items_count(self):
        return self.items.count()


class ZrpForm27Item(models.Model):
    ITEM_TYPE_CHOICES = (
        ('Asset', 'Capital / Fixed Asset'),
        ('Inventory', 'Inventory / Stock / Consumables'),
    )
    voucher = models.ForeignKey(ZrpForm27Voucher, on_delete=models.CASCADE, related_name="items")
    asset = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, blank=True, related_name="form27_issuances")
    serial_number = models.ForeignKey(AssetSerialNumber, on_delete=models.SET_NULL, null=True, blank=True, related_name="form27_issuances")
    
    item_type = models.CharField(max_length=50, choices=ITEM_TYPE_CHOICES, default='Asset', help_text="Whether this line item is a Capital Asset or Inventory/Stock")
    description = models.CharField(max_length=255, help_text="Description of article e.g. HM785 VHF MOBILE RADIO S/N")
    stores_use_only = models.CharField(max_length=255, default="", blank=True, help_text="For Stores Use Only (Quantity, Serial number, Ledger folios)")
    quantity = models.IntegerField(default=1)
    remarks = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.description} ({self.stores_use_only})"


# --- Statutory Z.R.P. FORM 216: Stores Stock / Ledger Card (Bin Card) ---

class ZrpForm216Card(models.Model):
    FORM_NUMBER = "FORM 216"
    
    code_no = models.CharField(max_length=100, help_text="Code No. (e.g. RAD-VHF-001, IT-LPT-2026)")
    article = models.CharField(max_length=255, help_text="Article description (e.g. HM785 VHF MOBILE RADIO)")
    unit = models.CharField(max_length=50, default="Each", help_text="Unit (e.g. Each, No., Set, Box, Roll)")
    folio_no = models.CharField(max_length=100, help_text="Folio No. (e.g. FOL-2026/01, P-08)")
    
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="form216_cards")
    linked_asset = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, blank=True, related_name="form216_cards")
    location_bin = models.CharField(max_length=100, blank=True, default="", help_text="Location / Bin / Shelf Ref")
    
    initial_bforward_balance = models.IntegerField(default=0, help_text="Initial Balance Brought Forward (B/Forward)")
    bforward_date = models.DateField(default=timezone.now, help_text="Date of B/Forward Balance")
    current_balance = models.IntegerField(default=0, help_text="Current Running Stock Balance")
    date_opened = models.DateField(default=timezone.now)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code_no', 'article']
        verbose_name = "Z.R.P. Form 216 Stock Card"
        verbose_name_plural = "Z.R.P. Form 216 Stock Cards"

    def __str__(self):
        return f"Form 216 - {self.code_no} ({self.article}) [Folio: {self.folio_no}]"

    def recalculate_balances(self):
        """Recalculates running balances for all entries based on initial B/Forward"""
        running = self.initial_bforward_balance
        for entry in self.entries.all().order_by('date', '-receipts', 'id'):
            receipts = entry.receipts or 0
            issues = entry.issues or 0
            running = running + receipts - issues
            if entry.balance != running:
                entry.balance = running
                entry.save(update_fields=['balance'])
        self.current_balance = running
        self.save(update_fields=['current_balance'])
        return running

    @property
    def total_receipts(self):
        return sum(e.receipts for e in self.entries.all())

    @property
    def total_issues(self):
        return sum(e.issues for e in self.entries.all())


class ZrpForm216Entry(models.Model):
    card = models.ForeignKey(ZrpForm216Card, on_delete=models.CASCADE, related_name="entries")
    date = models.DateField(default=timezone.now)
    voucher_no = models.CharField(max_length=100, help_text="Voucher No. (e.g. 85/26, DN-9041, GRV-102, B/Forward)")
    from_to = models.CharField(max_length=255, help_text="From / To (e.g. Central Radio Stores, To Harare Central, From Supplier)")
    receipts = models.PositiveIntegerField(default=0, help_text="Receipts into store (+)")
    issues = models.PositiveIntegerField(default=0, help_text="Issues out of store (-)")
    balance = models.IntegerField(default=0, help_text="Running Balance")
    remarks = models.CharField(max_length=255, blank=True, null=True)
    
    linked_form27_voucher = models.ForeignKey(ZrpForm27Voucher, on_delete=models.SET_NULL, null=True, blank=True, related_name="form216_entries")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', '-receipts', 'id']
        verbose_name = "Form 216 Entry"
        verbose_name_plural = "Form 216 Entries"

    def __str__(self):
        return f"{self.date} | Vchr: {self.voucher_no} | {self.from_to} | +{self.receipts}/-{self.issues} | Bal: {self.balance}"


# --- Statutory Z.R.P. GOODS RECEIVED Ledger / Register ---

class GoodsReceivedEntry(models.Model):
    entry_no = models.CharField(max_length=50, blank=True, null=True, help_text="ENTRY (e.g. GR-001, GRV-25/01)")
    date = models.DateField(default=timezone.now, help_text="DATE (e.g. 12/10/25)")
    goods_received = models.CharField(max_length=255, help_text="GOODS RECEIVED (Description of items delivered)")
    company = models.CharField(max_length=255, help_text="COMPANY / Supplier (e.g. C&T COMPUTERS)")
    qty = models.PositiveIntegerField(default=1, help_text="QTY (Quantity received)")
    bal = models.IntegerField(default=0, help_text="BAL (Running balance or outstanding balance)")
    po_no = models.CharField(max_length=100, help_text="P. O No. (e.g. ZRP01/23)")
    bin_no = models.CharField(max_length=100, blank=True, default="", help_text="BIN No (e.g. Rack A-02, Shelf 3)")
    receiver_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="goods_received_receiver_entries", help_text="Receiver selected from system users")
    checker_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="goods_received_checker_entries", help_text="Checker selected from system users")
    receiver = models.CharField(max_length=150, help_text="RECEIVER (Name / Force No, e.g. MUMBANYIWA)")
    checker = models.CharField(max_length=150, help_text="CHECKER (Name / Force No, e.g. MUMBANYIWA)")
    cross_ref = models.CharField(max_length=100, blank=True, default="", help_text="CROSS REF (e.g. ZRP 01/23, Invoice, Delivery Note)")
    remarks = models.TextField(blank=True, default="", help_text="REMARKS (Condition, warranty, serials, notes)")
    
    # Relationships
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="goods_received_entries")
    linked_asset = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, blank=True, related_name="goods_received_entries")
    linked_stock_card = models.ForeignKey(ZrpForm216Card, on_delete=models.SET_NULL, null=True, blank=True, related_name="goods_received_entries")
    delivery_note_scan = models.FileField(upload_to="goods_received_docs/", null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-id']
        verbose_name = "Goods Received Entry"
        verbose_name_plural = "Goods Received Ledger Entries"

    def __str__(self):
        return f"GR #{self.entry_no or self.id} - {self.date} | {self.goods_received} ({self.company}) | Qty: {self.qty}"

    @classmethod
    def get_next_entry_no(cls, year=None):
        """
        Auto-generates the next sequential entry number formatted as NN/YYYY
        (e.g. 01/2026, 02/2026, 03/2026).
        Always restarts from 1 (01/YYYY) at the beginning of each new year.
        """
        if not year:
            year = timezone.now().year
        year_str = str(year)

        # Look for existing entries ending with /{year}
        entries = cls.objects.filter(entry_no__endswith=f"/{year_str}")
        max_num = 0
        for e in entries:
            if e.entry_no and '/' in e.entry_no:
                parts = e.entry_no.strip().split('/')
                if len(parts) == 2 and parts[1].strip() == year_str:
                    prefix = parts[0].strip()
                    if prefix.isdigit():
                        try:
                            val = int(prefix)
                            if val > max_num:
                                max_num = val
                        except ValueError:
                            pass

        next_val = max_num + 1
        return f"{next_val:02d}/{year_str}"

    @property
    def registered_assets_qty(self):
        """Total quantity of assets registered against this Goods Received entry"""
        return sum(a.quantity_delivered or a.serial_numbers.count() or 0 for a in self.assets.all())

    @property
    def remaining_unregistered_qty(self):
        """Remaining quantity from this GR entry that has not yet been registered as assets"""
        return max(0, (self.qty or 0) - self.registered_assets_qty)

    @property
    def is_fully_registered(self):
        """True if all items from this GR entry have been accounted for in the asset register"""
        return self.registered_assets_qty >= (self.qty or 0)

# --- Statutory Z.R.P. ISSUES REGISTER ---

class IssuesRegisterEntry(models.Model):
    URGENCY_CHOICES = (
        ('Immediate', 'Immediate (Process Now)'),
        ('Urgent', 'Urgent (Process within 48 Hours)'),
        ('Normal', 'Normal (Process after 7 Days)'),
    )

    entry_no = models.CharField(max_length=50, blank=True, null=True, help_text="ENTRY (e.g. 01/2026, 02/2026)")
    date = models.DateField(default=timezone.now, help_text="DATE (e.g. Issue Date)")
    urgency = models.CharField(max_length=50, choices=URGENCY_CHOICES, default='Normal', help_text="Issue urgency / SLA processing timeframe")
    target_date = models.DateField(null=True, blank=True, help_text="Target processing / delivery date based on urgency")
    item_description = models.CharField(max_length=255, help_text="ITEM DESCRIPTION (e.g. Lenovo Laptop Core i7, VHF Radios)")
    qty = models.PositiveIntegerField(default=1, help_text="QTY (Quantity issued)")
    requesting_station = models.CharField(max_length=255, help_text="REQUESTING STATION (e.g. Harare Central, CID Minerals, Signals)")
    station_ref = models.CharField(max_length=100, blank=True, default="", help_text="STATIONREF (e.g. HC/REQ/25/08, Signals 04/26)")
    date_requested = models.DateField(default=timezone.now, help_text="DATE REQUESTED (e.g. 12/12/25)")
    item_class = models.CharField(max_length=100, blank=True, default="", help_text="CLASS (e.g. Class I, Consumable, Capital, ICT, Radio)")
    issuer = models.CharField(max_length=150, help_text="ISSUER (Name, Rank & Force No of issuing storeman)")
    receiver_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="issues_register_receiver_entries", help_text="Receiver selected from system users")
    checker_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="issues_register_checker_entries", help_text="Checker selected from system users")
    receiver_details = models.CharField(max_length=255, help_text="No, RANK, NAME & SIGNATURE OF RECEIVER (e.g. 044122E SGT MUKAMBA T.)")
    receiver_signature_image = models.ImageField(upload_to="issues_signatures/", null=True, blank=True, help_text="Optional digital/scanned receiver signature")
    voucher_scan = models.FileField(upload_to="issues_vouchers/", null=True, blank=True, help_text="Signed voucher or requisition slip")
    remarks = models.TextField(blank=True, default="", help_text="REMARKS / Notes")
    
    # Relationships
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="issues_register_entries")
    linked_asset = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, blank=True, related_name="issues_register_entries")
    linked_stock_card = models.ForeignKey(ZrpForm216Card, on_delete=models.SET_NULL, null=True, blank=True, related_name="issues_register_entries")
    linked_form27_voucher = models.ForeignKey(ZrpForm27Voucher, on_delete=models.SET_NULL, null=True, blank=True, related_name="issues_register_entries")
    issued_serials = models.ManyToManyField(AssetSerialNumber, blank=True, related_name="issues_register_entries", help_text="Specific serial numbers issued in this dispatch")
    issued_assets = models.ManyToManyField(Asset, blank=True, related_name="multi_issues_register_entries", help_text="Assets included in this dispatch")

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-id']
        verbose_name = "Issues Register Entry"
        verbose_name_plural = "Issues Register Entries"

    def __str__(self):
        return f"ISS #{self.entry_no or self.id} - {self.date} | {self.item_description} to {self.requesting_station} (Qty: {self.qty})"

    @classmethod
    def get_next_entry_no(cls, year=None):
        """
        Auto-generates the next sequential entry number formatted as NN/YYYY (e.g. 01/2026, 02/2026).
        Always restarts from 1 (01/YYYY) at the beginning of each new year.
        """
        if not year:
            year = timezone.now().year
        year_str = str(year)
        
        # Look for existing entries ending with /{year}
        entries = cls.objects.filter(entry_no__endswith=f"/{year_str}")
        max_num = 0
        for e in entries:
            if e.entry_no and '/' in e.entry_no:
                prefix = e.entry_no.split('/')[0].strip()
                digits = ''.join(ch for ch in prefix if ch.isdigit())
                if digits:
                    try:
                        val = int(digits)
                        if val > max_num:
                            max_num = val
                    except ValueError:
                        pass
        
        # Fallback check for entries logged with date in that year
        if max_num == 0:
            for e in cls.objects.filter(date__year=year):
                if e.entry_no and '/' in e.entry_no:
                    prefix = e.entry_no.split('/')[0].strip()
                    digits = ''.join(ch for ch in prefix if ch.isdigit())
                    if digits:
                        try:
                            val = int(digits)
                            if val > max_num:
                                max_num = val
                        except ValueError:
                            pass

        next_val = max_num + 1
        return f"{next_val:02d}/{year_str}"


# --- Statutory Z.R.P. TENDER PROCEDURES Ledger / Register ---

class TenderProcedureEntry(models.Model):
    entry_no = models.CharField(max_length=50, blank=True, null=True, help_text="ENTRY (e.g. TND-001, TP-26/04)")
    date = models.DateField(default=timezone.now, help_text="DATE (Tender / Procedure date)")
    item_description = models.CharField(max_length=255, help_text="ITEM DESCRIPTION (e.g. Supply & Installation of Solar Backup Systems)")
    requesting_station = models.CharField(max_length=255, help_text="REQUESTING STATION (e.g. Beitbridge Border Post, Police GHQ)")
    qty = models.PositiveIntegerField(default=1, help_text="QTY (Quantity tendered / procured)")
    total_price = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, help_text="TOTAL PRICE (Contract / Award value)")
    ict_ref = models.CharField(max_length=100, help_text="ICT REF (e.g. ICT/TND/2026/08, SPEC-SOL-02)")
    purchase_order_no = models.CharField(max_length=100, help_text="PURCHASE ORDER No. (e.g. PO-ZRP-9921)")
    remarks = models.TextField(blank=True, default="", help_text="REMARKS (Supplier awarded, tender method, PRAZ ref, notes)")

    # Relationships
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="tender_procedure_entries")
    linked_asset = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, blank=True, related_name="tender_procedure_entries")
    tender_doc_scan = models.FileField(upload_to="tender_procedures_docs/", null=True, blank=True, help_text="Award letter, comparative schedule, or tender document")

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-id']
        verbose_name = "Tender Procedure Entry"
        verbose_name_plural = "Tender Procedure Entries"

    def __str__(self):
        return f"TND #{self.entry_no or self.id} - {self.date} | {self.item_description} for {self.requesting_station} (${self.total_price})"


# --- Institutional Knowledge Vault ---

class KnowledgeTag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    class Meta:
        verbose_name_plural = "Knowledge Tags"
        
    def __str__(self):
        return self.name

class KnowledgeCategory(models.Model):
    name = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, default='fas fa-book-open') # FontAwesome icon class
    
    class Meta:
        verbose_name_plural = "Knowledge Categories"
        
    def __str__(self):
        return self.name

class KnowledgeEntry(models.Model):
    ENTRY_TYPES = (
        ('Decision', 'Major Decision'),
        ('Policy', 'Operational Policy'),
        ('Guidance', 'Legal Guidance'),
    )
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Superseded', 'Superseded'),
        ('Draft', 'Drafting'),
    )
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    entry_type = models.CharField(max_length=50, choices=ENTRY_TYPES)
    content = models.TextField(help_text="Markdown or plain text content")
    category = models.ForeignKey(KnowledgeCategory, on_delete=models.CASCADE, related_name="entries")
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    physical_file = models.ForeignKey(File, on_delete=models.SET_NULL, null=True, blank=True, help_text="Link to paper trail")
    meeting = models.ForeignKey(Meeting, on_delete=models.SET_NULL, null=True, blank=True, related_name="knowledge_entries", help_text="Linking to source meeting")
    tags = models.ManyToManyField(KnowledgeTag, blank=True, related_name="entries")
    current_version = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="knowledge_created")
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Knowledge Entries"
        ordering = ['-last_updated']

    def __str__(self):
        return f"[{self.entry_type}] {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

class KnowledgeVersion(models.Model):
    entry = models.ForeignKey(KnowledgeEntry, on_delete=models.CASCADE, related_name="versions")
    version_num = models.IntegerField()
    content = models.TextField()
    change_summary = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-version_num']
        unique_together = ('entry', 'version_num')

    def __str__(self):
        return f"{self.entry.title} - Version {self.version_num}"

class KnowledgeRelation(models.Model):
    RELATION_TYPES = (
        ('Refers To', 'Refers To'),
        ('Supersedes', 'Supersedes'),
        ('Similar To', 'Similar To / Related Case'),
    )
    source = models.ForeignKey(KnowledgeEntry, on_delete=models.CASCADE, related_name="outgoing_relations")
    target = models.ForeignKey(KnowledgeEntry, on_delete=models.CASCADE, related_name="incoming_relations")
    relation_type = models.CharField(max_length=50, choices=RELATION_TYPES)
    comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.source.title} {self.relation_type} {self.target.title}"

# --- Inter-Department Service Requests ---

class ServiceTicket(models.Model):
    CATEGORY_CHOICES = (
        ('IT', 'IT Support'),
        ('Maintenance', 'General Maintenance'),
        ('HR', 'HR Complaint/Inquiry'),
        ('Facilities', 'Facilities Management'),
        ('Other', 'Other'),
    )
    PRIORITY_CHOICES = (
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Urgent', 'Urgent'),
    )
    STATUS_CHOICES = (
        ('Open', 'Open / Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
    )
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tickets_submitted")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="tickets_received", help_text="Target department for the request")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    subject = models.CharField(max_length=250)
    description = models.TextField()
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_tickets")
    date_created = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Service Tickets"
        ordering = ['-date_created']

    def __str__(self):
        return f"[{self.category}] {self.subject} ({self.status})"

class TicketUpdate(models.Model):
    ticket = models.ForeignKey(ServiceTicket, on_delete=models.CASCADE, related_name="updates")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    new_status = models.CharField(max_length=20, blank=True, null=True)
    date_created = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Ticket Updates"
        ordering = ['date_created']

    def __str__(self):
        return f"Update on {self.ticket.subject} by {self.user.username}"

# --- Digital Signatures & Notice Board ---

class DigitalCertificate(models.Model):
    CERT_TYPES = (
        ('Approval', 'Approval Certificate'),
        ('Clearance', 'Clearance Letter'),
        ('Memo', 'Official Memo'),
        ('Archive', 'Archive Certification'),
    )
    certificate_type = models.CharField(max_length=50, choices=CERT_TYPES)
    subject = models.CharField(max_length=255)
    recipient_name = models.CharField(max_length=255)
    content = models.TextField()
    issuer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="certificates_issued")
    verification_code = models.CharField(max_length=100, unique=True, db_index=True)
    date_created = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name_plural = "Digital Certificates"
        ordering = ['-date_created']

    def __str__(self):
        return f"[{self.certificate_type}] {self.subject} - {self.recipient_name}"

class Announcement(models.Model):
    PRIORITY_CHOICES = (
        ('Normal', 'Normal'),
        ('High', 'High Priority'),
        ('Urgent', 'Urgent/Critical'),
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Normal')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, help_text="Specific department target (optional)")
    date_created = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-priority', '-date_created']

    def __str__(self):
        return self.title
class ScannerDevice(models.Model):
    name = models.CharField(max_length=250)
    api_key = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=250, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(auto_now=True)
    date_added = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

class ScannedDocument(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending Processing'),
        ('Processing', 'OCR/Classification In Progress'),
        ('Completed', 'Successfully Processed'),
        ('Failed', 'Processing Failed'),
        ('Awaiting Link', 'Awaiting Manual Linkage'),
    )
    scanner = models.ForeignKey(ScannerDevice, on_delete=models.SET_NULL, null=True, blank=True)
    raw_file = models.FileField(upload_to='scanned_docs/')
    extracted_text = models.TextField(blank=True, null=True)
    classification = models.CharField(max_length=100, blank=True, null=True)
    confidence_score = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    
    # Optional Linkages
    linked_file = models.ForeignKey(File, on_delete=models.SET_NULL, null=True, blank=True, related_name="scanned_documents")
    linked_requisition = models.ForeignKey(Requisition, on_delete=models.SET_NULL, null=True, blank=True, related_name="scanned_documents")
    linked_contract = models.ForeignKey(Contract, on_delete=models.SET_NULL, null=True, blank=True, related_name="scanned_documents")
    linked_leave_request = models.ForeignKey(LeaveRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name="scanned_documents")
    linked_asset = models.ForeignKey(Asset, on_delete=models.SET_NULL, null=True, blank=True, related_name="scanned_documents")
    
    metadata = models.JSONField(default=dict, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Scan {self.id} - {self.status}"

class CloudFolder(models.Model):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subfolders')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='cloud_folders')
    project_context = models.CharField(max_length=255, blank=True, null=True, help_text="Optional project/case identifier")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Cloud Folders"
        unique_together = ('name', 'parent', 'department')

    def __str__(self):
        return f"{self.department.name} / {self.name}"

class CloudFile(models.Model):
    name = models.CharField(max_length=255)
    folder = models.ForeignKey(CloudFolder, on_delete=models.CASCADE, related_name='files')
    description = models.TextField(blank=True, null=True)
    CLASSIFICATION_CHOICES = (
        ('Open Access', 'Open Access'),
        ('Departmental', 'Departmental'),
        ('Confidential', 'Confidential'),
        ('Restricted/Highly Confidential', 'Restricted/Highly Confidential'),
    )
    is_internal_only = models.BooleanField(default=True)
    classification_level = models.CharField(max_length=50, choices=CLASSIFICATION_CHOICES, default='Departmental')
    status = models.CharField(max_length=20, choices=(('Active', 'Active'), ('Archived', 'Archived'), ('Trash', 'Trash')), default='Active')
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __get_latest_version(self):
        return self.versions.order_by('-version_number').first()

    @property
    def latest_version(self):
        return self.__get_latest_version()

    def __str__(self):
        return self.name

class CloudFileVersion(models.Model):
    cloud_file = models.ForeignKey(CloudFile, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField()
    file_content = models.FileField(upload_to='cloud_vault/%Y/%m/%d/')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    commit_message = models.TextField(blank=True, null=True)
    file_size = models.BigIntegerField(default=0)
    checksum = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-version_number']
        unique_together = ('cloud_file', 'version_number')

    def __str__(self):
        return f"{self.cloud_file.name} (v{self.version_number})"

class FileAccessLog(models.Model):
    ACTIONS = (
        ('View', 'Viewed Preview'),
        ('Download', 'Downloaded File'),
        ('Share', 'Created Share Link'),
        ('Rollback', 'Restored Previous Version'),
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    cloud_file = models.ForeignKey(CloudFile, on_delete=models.CASCADE, related_name='access_logs')
    version = models.ForeignKey(CloudFileVersion, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTIONS)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} {self.action} {self.cloud_file.name} at {self.timestamp}"

class CloudShare(models.Model):
    cloud_file = models.ForeignKey(CloudFile, on_delete=models.CASCADE, related_name='shares')
    shared_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shares_created')
    shared_with_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='shared_files')
    shared_with_email = models.EmailField(blank=True, null=True)
    access_token = models.CharField(max_length=100, unique=True)
    expiry_date = models.DateTimeField()
    can_download = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    is_revoked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return not self.is_revoked and self.expiry_date > timezone.now()

    def __str__(self):
        return f"Share of {self.cloud_file.name} to {self.shared_with_user or self.shared_with_email}"

class FileApproval(models.Model):
    ACTION_TYPES = (
        ('Handover', 'Handover'),
        ('Transfer', 'Transfer'),
        ('Digitization', 'Digitization'),
        ('Access', 'Access Request'),
    )
    STATUS_CHOICES = (
        ('Pending', 'Pending Review'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )
    file_doc = models.ForeignKey(File, on_delete=models.CASCADE, related_name="approvals")
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name="approvals_requested")
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="approvals_handled")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    comments = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Approval for {self.file_doc.ref_num} - {self.action_type} ({self.status})"

    class Meta:
        ordering = ['-timestamp']

class UserSecurity(models.Model):
    PROVINCE_CHOICES = (
        ('Harare', 'Harare Province'),
        ('Bulawayo', 'Bulawayo Province'),
        ('Manicaland', 'Manicaland Province'),
        ('Mashonaland Central', 'Mashonaland Central Province'),
        ('Mashonaland East', 'Mashonaland East Province'),
        ('Mashonaland West', 'Mashonaland West Province'),
        ('Masvingo', 'Masvingo Province'),
        ('Matabeleland North', 'Matabeleland North Province'),
        ('Matabeleland South', 'Matabeleland South Province'),
        ('Midlands', 'Midlands Province'),
        ('National Headquarters', 'National Police Headquarters (PGHQ)'),
    )
    ROLES = (
        ('General Police', 'General Police Officer'),
        ('Supt ICT', 'Superintendent ICT (Supt ICT)'),
        ('Chief Tech', 'Chief Technician (Chief Tech - Comms & Radio)'),
        ('System Manager', 'System Manager (Systems)'),
        ('Systems Manager', 'Systems Manager (ICT Systems)'),
        ('Provincial ICT Officer', 'Provincial ICT Officer (PICTO)'),
        ('Deputy Director Communications', 'Deputy Director Communications (Comms & Radio)'),
        ('Deputy Director ICT', 'Deputy Director ICT (Systems)'),
        ('Deputy Director IT', 'Deputy Director IT (Legacy / Systems)'),
        ('Chief Director', 'Chief Director (Executive Oversight - All)'),
        ('Clerk', 'Registry Clerk'),
        ('Supervisor', 'Registry Supervisor'),
        ('Auditor', 'System Auditor'),
        ('Executive', 'Executive Officer'),
        ('Portfolio Admin', 'Portfolio Administrator'),
        ('Project Leader', 'Project Leader'),
        ('Team Member', 'Project Team Member'),
        ('Executive Viewer', 'Executive Governance Viewer'),
        ('Project Management Team', 'Project Management Team'),
        ('HODs', 'Head of Departments'),
        ('Board of Executives', 'Board of Executives'),
        ('Purchasing Officer', 'Purchasing Officer'),
        ('Finance Officer', 'Finance Officer'),
        ('Department Manager', 'Department Manager'),
    )
    PLATFORMS = (
        ('RIFTS-X', 'RIFTS-X Master Platform'),
        ('Governance', 'Project Governance & Strategy'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='security_profile')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(max_length=50, choices=ROLES, default='Clerk')
    province = models.CharField(max_length=100, choices=PROVINCE_CHOICES, blank=True, null=True, help_text="Assigned ZRP Province for Provincial Officers")
    platform = models.CharField(max_length=20, choices=PLATFORMS, default='RIFTS-X')
    job_title = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)
    
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    
    # Role governance: what the user requested vs. what Board approved
    role_requested = models.CharField(max_length=50, choices=ROLES, default='Team Member',
                                      help_text="Role the user selected at registration")
    is_role_approved = models.BooleanField(default=False,
                                           help_text="Board must approve strategic roles (Board, HODs, PMT, PL)")
    is_pm_approved = models.BooleanField(default=False,
                                         help_text="Project Leader must approve Team Members")
    role_approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_roles', help_text="Board or PL who approved this role"
    )
    role_approved_at = models.DateTimeField(null=True, blank=True)
    
    mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=100, blank=True, null=True)
    mfa_code = models.CharField(max_length=6, blank=True, null=True)
    mfa_expiry = models.DateTimeField(blank=True, null=True)
    
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)

    def __str__(self):
        return f"Security Profile: {self.user.username} ({self.role})"

@receiver(post_save, sender=User)
def create_user_security(sender, instance, created, **kwargs):
    if created:
        UserSecurity.objects.create(user=instance)

class SecurityAlert(models.Model):
    SEVERITY = (
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    )
    alert_type = models.CharField(max_length=100) # After-Hours Access, Unusual Activity, Failed MFA
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY, default='Medium')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.alert_type} - {self.severity} ({self.timestamp})"

    class Meta:
        ordering = ['-timestamp']

class OfflineSyncQueue(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending Synchronization'),
        ('Synced', 'Successfully Synced'),
        ('Conflict', 'Conflict Detected'),
        ('Failed', 'Processing Failed'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sync_records")
    local_id = models.UUIDField(editable=False) # Generated by mobile device
    ref_num = models.CharField(max_length=250)
    data = models.JSONField(default=dict) # Metadata, coordinates, notes
    attachment = models.FileField(upload_to='sync_outbox/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    conflict_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Sync Record {self.local_id} for {self.ref_num} ({self.status})"

class Project(models.Model):
    STATUS_CHOICES = (
        ('Planned', 'Planned'),
        ('Active', 'Active'),
        ('Delayed', 'Delayed'),
        ('Done', 'Done'),
        ('Cancelled', 'Cancelled'),
    )
    name = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="projects")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_projects")
    budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    requisitions = models.ManyToManyField(Requisition, blank=True, related_name="linked_projects")
    contracts = models.ManyToManyField(Contract, blank=True, related_name="linked_projects")
    files = models.ManyToManyField(File, blank=True, related_name="linked_projects")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Planned')
    external_link = models.URLField(blank=True, null=True, help_text="Link to the live system/website for this project")
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ── Configurable Governance Levels (set by Project Leader) ──
    # Team Member and Project Leader gates are always required.
    # Small organizations can disable PMT, HODs, and/or Board gates.
    requires_pmt   = models.BooleanField(default=True, help_text="Require PMT gate approval for all phases in this project")
    requires_hods  = models.BooleanField(default=True, help_text="Require HODs gate approval for all phases in this project")
    requires_board = models.BooleanField(default=True, help_text="Require Board of Executives gate approval for all phases in this project")

    def __str__(self):
        return f"{self.name} ({self.status})"

    @property
    def active_phase(self):
        return self.phases.filter(status__in=['Active', 'Review', 'Awaiting PMT Approval', 'Awaiting HODs Approval', 'Awaiting Board Approval']).first()

    @property
    def progress_percentage(self):
        total_phases = self.phases.count()
        if total_phases == 0:
            return 0
        completed_phases = self.phases.filter(status='Done').count()
        return int((completed_phases / total_phases) * 100)

    @property
    def risk_indicator(self):
        """
        Calculates project risk level based on overdue tasks and blockers.
        Returns a dict with level, color class, and hex color.
        """
        now = timezone.now().date()
        overdue_tasks = ProjectTask.objects.filter(
            phase__project=self,
            status__in=['To Do', 'In Progress', 'Review'],
            due_date__lt=now
        ).count()
        
        active_blockers = ProjectTask.objects.filter(
            phase__project=self,
            status='Blocked'
        ).count()

        if overdue_tasks > 3 or (self.status == 'Delayed' and active_blockers > 0):
            return {'level': 'Delayed', 'color': 'danger', 'hex': '#dc3545', 'icon': 'fa-exclamation-triangle'}
        elif overdue_tasks > 0 or active_blockers > 0:
            return {'level': 'At Risk', 'color': 'warning', 'hex': '#ffc107', 'icon': 'fa-hourglass-half'}
        
        return {'level': 'On Track', 'color': 'success', 'hex': '#198754', 'icon': 'fa-check-circle'}

    class Meta:
        ordering = ['-created_at']

    @property
    def approved_members(self):
        """Returns QuerySet of users who are approved members of this project."""
        return User.objects.filter(project_memberships__project=self, project_memberships__is_approved=True)

class ProjectMember(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="project_memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="project_memberships")
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_project_members")
    approved_at = models.DateTimeField(null=True, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'user')
        verbose_name_plural = "Project Members"

    def __str__(self):
        status = "Approved" if self.is_approved else "Pending"
        return f"{self.user.username} - {self.project.name} ({status})"

class ProjectPhase(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Active', 'Active'),
        ('Review', 'Review'),
        ('Awaiting Team Member Approval', 'Awaiting Team Member Approval'),
        ('Awaiting Project Leader Approval', 'Awaiting Project Leader Approval'),
        ('Awaiting PMT Approval', 'Awaiting PMT Approval'),
        ('Awaiting HODs Approval', 'Awaiting HODs Approval'),
        ('Awaiting Board Approval', 'Awaiting Board Approval'),
        ('Done', 'Done'),
    )
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="phases")
    name = models.CharField(max_length=200)
    objectives = models.TextField(blank=True, null=True)
    sequence = models.IntegerField(default=1)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    deliverables = models.TextField(blank=True, null=True)
    required_documents = models.ManyToManyField(File, blank=True, related_name="required_in_phases")
    completion_criteria = models.TextField(blank=True, null=True)
    pm = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="managed_phases")
    requires_approval = models.BooleanField(default=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="phase_approvals")
    approved_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    decision_reason = models.TextField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    # New Governance Fields
    consolidation_notes = models.TextField(blank=True, null=True, help_text="Summary of tasks and deliverables for PMT/HODs/Board")
    team_member_comments = models.TextField(blank=True, null=True)
    project_leader_comments = models.TextField(blank=True, null=True)
    pmt_comments = models.TextField(blank=True, null=True)
    hods_comments = models.TextField(blank=True, null=True)
    board_comments = models.TextField(blank=True, null=True)

    # Flexible Quorum Settings (set by Project Leader per phase)
    pmt_required  = models.PositiveIntegerField(default=5, help_text="Number of PMT members required to advance to HODs")
    hods_required = models.PositiveIntegerField(default=5, help_text="Number of HODs members required to advance to Board")
    board_required = models.PositiveIntegerField(default=5, help_text="Number of Board members required to close the phase")

    @property
    def team_member_approvals(self):
        return self.approvals.filter(role='Team Member')

    @property
    def project_leader_approvals(self):
        return self.approvals.filter(role='Project Leader')

    @property
    def pmt_approvals(self):
        return self.approvals.filter(role='Project Management Team')

    @property
    def hods_approvals(self):
        return self.approvals.filter(role='HODs')

    @property
    def board_approvals(self):
        return self.approvals.filter(role='Board of Executives')

    @property
    def team_member_approval_count(self):
        return self.team_member_approvals.count()

    @property
    def project_leader_approval_count(self):
        return self.project_leader_approvals.count()

    @property
    def pmt_approval_count(self):
        return self.pmt_approvals.count()

    @property
    def hods_approval_count(self):
        return self.hods_approvals.count()

    @property
    def board_approval_count(self):
        return self.board_approvals.count()

    @property
    def pmt_approval_percentage(self):
        required = self.pmt_required or 1
        return min(100, int((self.pmt_approval_count / required) * 100))

    @property
    def hods_approval_percentage(self):
        required = self.hods_required or 1
        return min(100, int((self.hods_approval_count / required) * 100))

    @property
    def board_approval_percentage(self):
        required = self.board_required or 1
        return min(100, int((self.board_approval_count / required) * 100))

    def user_has_approved(self, user):
        return self.approvals.filter(approver=user).exists()

    @property
    def approver_ids(self):
        return list(self.approvals.values_list('approver_id', flat=True))

    @property
    def completed_tasks_count(self):
        return self.tasks.filter(status='Done').count()

    @property
    def total_tasks_count(self):
        return self.tasks.count()

    @property
    def task_overdue_count(self):
        from django.utils import timezone
        now = timezone.now().date()
        return self.tasks.filter(
            status__in=['Pending', 'In Progress', 'To Do', 'Review'],
            due_date__lt=now
        ).count()

    @property
    def task_completion_percentage(self):
        total = self.total_tasks_count
        if total == 0:
            return 0
        return int((self.completed_tasks_count / total) * 100)

    @property
    def get_approval_duration(self):
        """Returns the time taken from submission to approval in days/hours."""
        if self.submitted_at and self.approved_at:
            delta = self.approved_at - self.submitted_at
            days = delta.days
            hours = delta.seconds // 3600
            if days > 0:
                return f"{days}d {hours}h"
            return f"{hours}h"
        return "N/A"

    def __str__(self):
        return f"{self.project.name} - {self.name} ({self.status})"

class PhaseApproval(models.Model):
    ROLE_CHOICES = (
        ('Team Member', 'Project Team Member'),
        ('Project Leader', 'Project Leader'),
        ('Project Management Team', 'Project Management Team'),
        ('HODs', 'Head of Departments'),
        ('Board of Executives', 'Board of Executives'),
    )
    STATUS_CHOICES = (
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Pending', 'Pending Review'),
    )
    phase = models.ForeignKey(ProjectPhase, on_delete=models.CASCADE, related_name="approvals")
    approver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="phase_approvals_given")
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    comment = models.TextField()
    signature_data = models.TextField(blank=True, null=True) # Base64 signature data
    timestamp = models.DateTimeField(auto_now_add=True)

    @property
    def is_relevant_history(self):
        """
        A Team Member is only relevant if they have a task in this phase.
        All other roles (PL, PMT, HODs, Board) are always relevant.
        """
        if self.role == 'Team Member':
            return self.phase.tasks.filter(owner=self.approver).exists()
        return True

    class Meta:
        unique_together = ('phase', 'approver', 'role')
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.role} Approval - {self.approver.username} for {self.phase.name}"

class ProjectSprint(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Active', 'Active'),
        ('Done', 'Done'),
    )
    phase = models.ForeignKey(ProjectPhase, on_delete=models.CASCADE, related_name="sprints")
    name = models.CharField(max_length=200)
    goals = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    start_date = models.DateField()
    end_date = models.DateField()
    members = models.ManyToManyField(User, related_name="sprint_memberships", blank=True)

    @property
    def total_tasks(self):
        return self.tasks.count()

    @property
    def completed_tasks(self):
        return self.tasks.filter(status='Done').count()

    @property
    def remaining_tasks(self):
        return self.tasks.exclude(status='Done').count()

    @property
    def progress_percentage(self):
        total = self.total_tasks
        if total == 0:
            return 0
        return round((self.completed_tasks / total) * 100)

    @property
    def duration_days(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days or 1
        return 1

    @property
    def velocity(self):
        """Average tasks completed per day in this sprint."""
        if self.completed_tasks == 0:
            return 0
        return round(self.completed_tasks / self.duration_days, 2)


    def __str__(self):
        return f"{self.name} ({self.phase.project.name})"

class ProjectTask(models.Model):
    # ... (existing ProjectTask fields with additions)
    PRIORITY_CHOICES = (
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    )
    STATUS_CHOICES = [
        ('To Do', 'To Do'),
        ('In Progress', 'In Progress'),
        ('Review', 'Under PM Review'),
        ('Done', 'Completed'),
        ('Blocked', 'Blocked'),
    ]
    phase = models.ForeignKey(ProjectPhase, on_delete=models.CASCADE, related_name="tasks")
    sprint = models.ForeignKey(ProjectSprint, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks")
    title = models.CharField(max_length=250)
    description = models.TextField() # Mandatory
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="project_tasks") # Mandatory by default
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField()
    dependencies = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='blocked_tasks')
    progress = models.IntegerField(default=0) # 0-100
    linked_docs = models.ManyToManyField(File, blank=True, related_name='linked_tasks')
    physical_file = models.ForeignKey(File, on_delete=models.SET_NULL, null=True, blank=True, related_name="task_physical_files")
    linked_requisition = models.ForeignKey('Requisition', on_delete=models.SET_NULL, null=True, blank=True, related_name="linked_tasks")
    linked_contract = models.ForeignKey('Contract', on_delete=models.SET_NULL, null=True, blank=True, related_name="linked_tasks")
    linked_resolution = models.ForeignKey('Resolution', on_delete=models.SET_NULL, null=True, blank=True, related_name="linked_tasks")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='To Do')
    is_deliverable = models.BooleanField(default=False)
    self_assigned = models.BooleanField(default=False)  # True when created by team member, not PM
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks_assigned")
    completed_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_overdue(self):
        if self.status == 'Done' or not self.due_date:
            return False
        return self.due_date < timezone.now().date()

    @property
    def deadline_status(self):
        """Returns 'danger', 'warning', or 'normal' based on due date."""
        if self.status == 'Done' or not self.due_date:
            return 'normal'
        
        now = timezone.now().date()
        if self.due_date < now:
            return 'danger'
        
        time_left = (self.due_date - now).days
        if time_left <= 1:
            return 'warning'
        
        return 'normal'

    def __str__(self):
        return f"{self.title} - {self.owner.username} ({self.status})"


class TaskAttachment(models.Model):
    task = models.ForeignKey(ProjectTask, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to='project_tasks/', null=True, blank=True)
    external_link = models.URLField(max_length=500, null=True, blank=True)
    filename = models.CharField(max_length=250)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename

class ProjectLog(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="logs")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.name}: {self.message[:50]} ({self.timestamp})"


class ProjectAlert(models.Model):
    ALERT_TYPES = (
        ('Deadline', 'Deadline Warning (48h)'),
        ('DeadlineMorning', 'Due Date Morning'),
        ('Overdue', 'Task Overdue'),
        ('Escalation', 'Team Escalation'),
        ('EscalationHOD', 'HOD Escalation'),
        ('EscalationMD', 'MD Escalation'),
        ('SprintEnd', 'Sprint Ending'),
        ('PhaseCriteria', 'Phase Criteria Unmet'),
        ('PhaseApproved', 'Phase Approved'),
        ('PhaseReady', 'Phase Ready for Review'),
        ('Predictive', 'Predictive Delay'),
    )
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="alerts")
    task = models.ForeignKey(ProjectTask, on_delete=models.CASCADE, null=True, blank=True, related_name="alerts")
    phase = models.ForeignKey(ProjectPhase, on_delete=models.CASCADE, null=True, blank=True, related_name="alerts")
    sprint = models.ForeignKey(ProjectSprint, on_delete=models.CASCADE, null=True, blank=True, related_name="alerts")
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="project_alerts")
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.alert_type} - {self.project.name} ({self.created_at.date()})"


class ProjectComment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="comments", null=True, blank=True)
    phase = models.ForeignKey(ProjectPhase, on_delete=models.CASCADE, related_name="comments", null=True, blank=True)
    sprint = models.ForeignKey(ProjectSprint, on_delete=models.CASCADE, related_name="comments", null=True, blank=True)
    task = models.ForeignKey(ProjectTask, on_delete=models.CASCADE, related_name="project_comments", null=True, blank=True)
    
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name="replies")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="project_comments")
    content = models.TextField()
    
    is_decision = models.BooleanField(default=False)
    is_action_item = models.BooleanField(default=False)
    is_resolved = models.BooleanField(default=False)
    
    mentioned_users = models.ManyToManyField(User, blank=True, related_name="mentions_received")
    attachments = models.ManyToManyField(File, blank=True, related_name="linked_comments")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.created_at}"


class CommentEditHistory(models.Model):
    comment = models.ForeignKey(ProjectComment, on_delete=models.CASCADE, related_name="edit_history")
    content_before = models.TextField()
    edited_at = models.DateTimeField(auto_now_add=True)
    edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-edited_at']

class PushSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="push_subscriptions")
    endpoint = models.TextField(unique=True)
    p256dh = models.CharField(max_length=250)
    auth = models.CharField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Push Sub for {self.user.username}"

class Benefit(models.Model):
    revenue_line = models.CharField(max_length=250)
    monthly_savings = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    projected_year_end = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    annual_projection = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="benefits")
    hod = models.ForeignKey(User, on_delete=models.CASCADE, related_name="benefits_added")
    date_added = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-date_added']

    def __str__(self):
        return f"{self.revenue_line} - {self.department.name}"


# ─────────────────────────────────────────────────────────────────────────────
# BRD (Business Requirements Document) E-Signature Workflow
# ─────────────────────────────────────────────────────────────────────────────

class BRD(models.Model):
    STATUS_CHOICES = (
        ('Draft',           'Draft'),
        ('Awaiting PMT',    'Awaiting PMT Approval'),
        ('Awaiting HODs',   'Awaiting HODs Approval'),
        ('Awaiting Board',  'Awaiting Board Approval'),
        ('Approved',        'Approved'),
        ('Rejected',        'Rejected'),
    )

    title           = models.CharField(max_length=300)
    description     = models.TextField(blank=True, null=True)
    initiator       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='initiated_brds')
    document        = models.FileField(upload_to='brds/originals/')
    signed_document = models.FileField(upload_to='brds/signed/', blank=True, null=True)

    status          = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Draft')

    # Required signature counts per level (set by initiator)
    ai_summary = models.TextField(blank=True, null=True)
    ai_highlights = models.JSONField(blank=True, null=True)

    pmt_required    = models.PositiveIntegerField(default=1)
    hods_required   = models.PositiveIntegerField(default=1)
    board_required  = models.PositiveIntegerField(default=1)

    rejection_reason = models.TextField(blank=True, null=True)
    rejected_by      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='rejected_brds')
    rejected_at      = models.DateTimeField(null=True, blank=True)

    created_at      = models.DateTimeField(default=timezone.now)
    updated_at      = models.DateTimeField(auto_now=True)
    forwarded_to_pl_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'BRD'
        verbose_name_plural = 'BRDs'

    def __str__(self):
        return f"BRD: {self.title} [{self.status}]"

    def pmt_signatures_count(self):
        return self.signatures.filter(approver__level='PMT').count()

    def hods_signatures_count(self):
        return self.signatures.filter(approver__level='HODs').count()

    def board_signatures_count(self):
        return self.signatures.filter(approver__level='Board').count()

    def pmt_quorum_met(self):
        return self.pmt_signatures_count() >= self.pmt_required

    def hods_quorum_met(self):
        return self.hods_signatures_count() >= self.hods_required

    def board_quorum_met(self):
        return self.board_signatures_count() >= self.board_required


class BRDApprover(models.Model):
    LEVEL_CHOICES = (
        ('PMT',   'Project Management Team'),
        ('HODs',  'Head of Departments'),
        ('Board', 'Board of Executives'),
    )

    brd         = models.ForeignKey(BRD, on_delete=models.CASCADE, related_name='approvers')
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='brd_approvals')
    level       = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    designation = models.CharField(max_length=150, blank=True, null=True,
                                   help_text="Role/title at time of assignment")
    order       = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['level', 'order']
        unique_together = [['brd', 'user', 'level']]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} — {self.level} on {self.brd.title}"

    def has_signed(self):
        return self.brd.signatures.filter(approver=self).exists()


class BRDSignature(models.Model):
    brd             = models.ForeignKey(BRD, on_delete=models.CASCADE, related_name='signatures')
    approver        = models.ForeignKey(BRDApprover, on_delete=models.CASCADE, related_name='signature_records')
    signature_data  = models.TextField(help_text='Base64-encoded PNG canvas signature')
    designation     = models.CharField(max_length=150, blank=True, null=True)
    signed_at       = models.DateTimeField(default=timezone.now)
    ip_address      = models.GenericIPAddressField(null=True, blank=True)
    comments        = models.TextField(blank=True, null=True, help_text='Reviewer comments made during signing')

    class Meta:
        ordering = ['signed_at']

    def __str__(self):
        return f"Signature by {self.approver.user.username} on {self.brd.title} at {self.signed_at}"

class UserSignature(models.Model):
    user            = models.OneToOneField(User, on_delete=models.CASCADE, related_name='signature_profile')
    signature_data  = models.TextField(help_text='Base64-encoded PNG signature for reuse')
    updated_at      = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Signature Profile for {self.user.username}"


class LeaveApprovalToken(models.Model):
    leave_request = models.ForeignKey('LeaveRequest', on_delete=models.CASCADE, related_name='approval_tokens')
    approver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_tokens')
    token = models.CharField(max_length=128, unique=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return (not self.used) and (self.expires_at and timezone.now() < self.expires_at)

    def mark_used(self):
        self.used = True
        self.save(update_fields=['used'])


# ─────────────────────────────────────────────────────────
#  Enhanced Supply Requisition System
# ─────────────────────────────────────────────────────────

class SupplyRequisition(models.Model):
    STATUS_CHOICES = (
        ('Draft',                      'Draft'),
        ('Pending Requester',          'Pending Requester Signature'),
        ('Pending Supervisor',         'Pending Supervisor Signature'),
        ('Pending Dept',               'Pending Department Manager'),
        ('Pending Deputy Director',    'Pending Deputy Director Approval'),
        ('Pending Purchasing',         'Pending Purchasing Officer (Bid Analysis)'),
        ('Pending Requester Review',   'Pending Requester Review & Sign'),
        ('Pending Purchasing Final',   'Pending Purchasing Officer (Final Review)'),
        ('Pending CEO',                'Pending Chief Director Signature'),
        ('Pending Finance',            'Pending Finance Officer'),
        ('Approved',                   'Fully Approved'),
        ('Rejected',                   'Rejected'),
    )

    # Identification
    ref_number      = models.CharField(max_length=30, unique=True, blank=True)
    department      = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='supply_requisitions')
    requester       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='supply_requisitions')
    purpose         = models.TextField(help_text='Purpose / justification for this requisition')
    budget_line     = models.ForeignKey(Budget, on_delete=models.SET_NULL, null=True, blank=True, related_name='supply_requisitions')

    # Approvers (chosen per-requisition)
    supervisor      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='supply_req_as_supervisor')
    dept_manager    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='supply_req_as_dept_manager')
    deputy_director = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='supply_req_as_deputy_director',
                                        help_text='Deputy Director who approves after Department Manager')
    ceo             = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='supply_req_as_ceo',
                                        verbose_name='Chief Director')
    purchasing_officer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='supply_req_as_purchasing_officer')
    finance_officer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='supply_req_as_finance_officer')


    # Optional document upload (Word / PDF)
    uploaded_document = models.FileField(upload_to='supply_requisitions/docs/', blank=True, null=True,
                                         help_text='Optional: upload a Word/PDF requisition document')

    # Procurement Requirement 6 Enhancements
    required_date   = models.DateField(null=True, blank=True, help_text='Required delivery date')
    delegated_authority_level = models.CharField(max_length=100, default='Officer Level (<= $500)', help_text='ZRP Delegated Authority Threshold')
    procurement_status = models.CharField(max_length=100, default='Requisition Initiated', help_text='Current Procurement Workflow Stage')
    
    # Purchase Order & Delivery Tracking
    purchase_order_number = models.CharField(max_length=100, blank=True, null=True)
    po_document = models.FileField(upload_to='supply_requisitions/pos/', blank=True, null=True)
    po_issued_date = models.DateTimeField(null=True, blank=True)
    
    delivery_status = models.CharField(max_length=50, choices=(('Pending', 'Pending'), ('Partial Delivery', 'Partial Delivery'), ('Full Delivery Received', 'Full Delivery Received'), ('Verified', 'Verified')), default='Pending')
    delivery_date = models.DateField(null=True, blank=True)
    delivery_notes = models.TextField(blank=True, null=True)

    bid_analysis    = models.TextField(blank=True, null=True, help_text='Purchasing Officer Bid Analysis')
    payment_status  = models.CharField(max_length=20, choices=(('Pending', 'Pending'), ('Paid', 'Paid')), default='Pending')
    proof_of_payment = models.FileField(upload_to='supply_requisitions/pop/', blank=True, null=True, help_text='Proof of Payment')

    # Urgent flag – bypasses email batching and sends immediately
    is_urgent       = models.BooleanField(default=False, help_text='Mark as urgent to bypass email batch windows')

    # Rejection fields – captured permanently when any stage rejects
    rejection_reason = models.TextField(blank=True, null=True, help_text='Reason for rejection, if applicable')
    rejected_by      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='rejected_requisitions',
                                         help_text='The user who rejected this requisition')
    rejected_at      = models.DateTimeField(null=True, blank=True, help_text='Timestamp of rejection')
    rejected_stage   = models.CharField(max_length=50, blank=True, default='',
                                        help_text='Stage at which rejection occurred')

    status          = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Draft')
    date_requested  = models.DateTimeField(default=timezone.now)
    date_updated    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_requested']
        verbose_name = 'Purchase Requisition'
        verbose_name_plural = 'Purchase Requisitions'

    def __str__(self):
        return f"{self.ref_number} – {self.requester.get_full_name() or self.requester.username}"

    def save(self, *args, **kwargs):
        if not self.ref_number:
            # Find last ref across both old (NBSZ-) and new (ZRP-PR-) prefixes
            last_new = SupplyRequisition.objects.filter(ref_number__startswith='ZRP-PR-').order_by('-ref_number').first()
            last_old = SupplyRequisition.objects.filter(ref_number__startswith='NBSZ-').order_by('-ref_number').first()
            next_num = 1
            for last_req in [last_new, last_old]:
                if last_req:
                    try:
                        # ZRP-PR-00001 → parts[-1], NBSZ-00001 → parts[-1]
                        last_num = int(last_req.ref_number.split('-')[-1])
                        next_num = max(next_num, last_num + 1)
                    except (ValueError, IndexError):
                        pass
            self.ref_number = f'ZRP-PR-{next_num:05d}'
        super().save(*args, **kwargs)

    @property
    def grand_total(self):
        return sum(item.line_total for item in self.items.all())

    @property
    def requester_signatory(self):
        return self.signatories.filter(stage='requester').first()

    @property
    def supervisor_signatory(self):
        return self.signatories.filter(stage='supervisor').first()

    @property
    def dept_manager_signatory(self):
        return self.signatories.filter(stage='dept_manager').first()

    @property
    def deputy_director_signatory(self):
        return self.signatories.filter(stage='deputy_director').first()

    @property
    def ceo_signatory(self):
        return self.signatories.filter(stage='ceo').first()

    @property
    def purchasing_officer_signatory(self):
        """First (Bid Analysis) PO signatory."""
        return self.signatories.filter(stage='purchasing_officer').first()

    @property
    def purchasing_officer_review_signatory(self):
        """Second (Final Review) PO signatory."""
        return self.signatories.filter(stage='purchasing_officer_review').first()

    @property
    def finance_officer_signatory(self):
        return self.signatories.filter(stage='finance_officer').first()

    @property
    def requester_review_signatory(self):
        return self.signatories.filter(stage='requester_review').first()

    @property
    def approver_accountability_info(self):
        """
        Accountability property stating the exact name of who approved,
        who rejected, or who is currently holding the requisition.
        """
        if self.status == 'Approved':
            approver = self.finance_officer or self.ceo
            name = (approver.get_full_name() or approver.username) if approver else 'Authorized Authority'
            role = 'Finance Officer' if approver == self.finance_officer else 'Chief Director'
            return {
                'status_type': 'approved',
                'label': 'Approved',
                'officer_name': name,
                'officer_role': role,
                'details_str': f"Approved by {name} ({role})"
            }

        if self.status == 'Rejected':
            if self.rejected_by:
                name = self.rejected_by.get_full_name() or self.rejected_by.username
                stage = self.rejected_stage or 'Review Stage'
                return {
                    'status_type': 'rejected',
                    'label': 'Rejected',
                    'officer_name': name,
                    'officer_role': stage,
                    'details_str': f"Rejected by {name} ({stage})"
                }
            return {
                'status_type': 'rejected',
                'label': 'Rejected',
                'officer_name': 'Reviewing Officer',
                'officer_role': self.rejected_stage or 'Requisition Stage',
                'details_str': f"Rejected: {self.rejection_reason or 'Formal Rejection'}"
            }

        pending_map = {
            'Pending Requester': (self.requester, 'Initiator Signature'),
            'Pending Supervisor': (self.supervisor, 'Line Supervisor'),
            'Pending Dept': (self.dept_manager, 'Department Manager'),
            'Pending Deputy Director': (self.deputy_director, 'Deputy Director'),
            'Pending Purchasing': (self.purchasing_officer, 'Purchasing Officer (Bid Analysis)'),
            'Pending Requester Review': (self.requester, 'Initiator Review & Sign'),
            'Pending Purchasing Final': (self.purchasing_officer, 'Purchasing Officer (Final Review)'),
            'Pending CEO': (self.ceo, 'Chief Director'),
            'Pending Finance': (self.finance_officer, 'Finance Officer (Payment Processing)'),
        }

        user, role = pending_map.get(self.status, (None, self.status))
        if user:
            name = user.get_full_name() or user.username
            return {
                'status_type': 'pending',
                'label': self.status,
                'officer_name': name,
                'officer_role': role,
                'details_str': f"Pending: {name} ({role})"
            }

        return {
            'status_type': 'pending',
            'label': self.status,
            'officer_name': 'Awaiting Action',
            'officer_role': self.status,
            'details_str': f"Pending: {self.status}"
        }


class RequisitionItem(models.Model):
    requisition     = models.ForeignKey(SupplyRequisition, on_delete=models.CASCADE, related_name='items')
    description     = models.TextField(help_text='Detailed description of the item/supply')
    quantity        = models.PositiveIntegerField(default=1)
    unit_cost       = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    annual_budget   = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                          help_text='Annual budget allocated for this item')
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0,
                                          help_text='Current remaining budget balance')
    order           = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Item #{self.order}: {self.description[:40]} (x{self.quantity})"

    @property
    def line_total(self):
        return self.quantity * self.unit_cost

    @property
    def budget_balance(self):
        """Balance after deducting this line total from current balance."""
        return self.current_balance - self.line_total


class RequisitionSignatory(models.Model):
    STAGE_CHOICES = (
        ('requester',                 'Requested By'),
        ('supervisor',                'Supervisor Approval'),
        ('dept_manager',              'Department Manager'),
        ('purchasing_officer',        'Purchasing Officer (Bid Analysis)'),
        ('requester_review',          'Requester Review & Sign'),
        ('purchasing_officer_review', 'Purchasing Officer (Final Review)'),
        ('ceo',                       'CEO Approval'),
        ('finance_officer',           'Finance Officer'),
    )

    requisition     = models.ForeignKey(SupplyRequisition, on_delete=models.CASCADE, related_name='signatories')
    stage           = models.CharField(max_length=30, choices=STAGE_CHOICES)
    user            = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requisition_signatories')
    signature_data  = models.TextField(blank=True, null=True, help_text='Base64-encoded PNG signature (canvas or uploaded)')
    uploaded_signature = models.ImageField(upload_to='supply_requisitions/signatures/', blank=True, null=True,
                                           help_text='Optional: upload a signature image instead of drawing')
    date_signed     = models.DateTimeField(null=True, blank=True)
    date_received   = models.DateField(null=True, blank=True, help_text='For Purchasing Officer: date document was received')
    purchase_order  = models.CharField(max_length=100, blank=True, null=True, help_text='Purchase Order reference number')
    comments        = models.TextField(blank=True, null=True)
    ip_address      = models.GenericIPAddressField(null=True, blank=True)
    is_signed       = models.BooleanField(default=False)

    class Meta:
        unique_together = ('requisition', 'stage')
        ordering = ['requisition', 'stage']

    def __str__(self):
        return f"{self.get_stage_display()} – {self.user.get_full_name() or self.user.username} – {'Signed' if self.is_signed else 'Pending'}"


class SupplierQuotation(models.Model):
    requisition     = models.ForeignKey(SupplyRequisition, on_delete=models.CASCADE, related_name='quotations')
    supplier_name   = models.CharField(max_length=250)
    contact_person  = models.CharField(max_length=250, blank=True, null=True)
    phone           = models.CharField(max_length=50, blank=True, null=True)
    email           = models.EmailField(blank=True, null=True)
    quoted_amount   = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    notes           = models.TextField(blank=True, null=True)
    quotation_file  = models.FileField(upload_to='supply_requisitions/quotations/', blank=True, null=True)
    order           = models.PositiveIntegerField(default=1)

    # Set to True for the supplier selected by the Purchasing Officer
    is_chosen       = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Supplier {self.order}: {self.supplier_name} – {self.quoted_amount}"


class RequisitionEmailQueue(models.Model):
    """Holds outbound email notifications for batch delivery."""
    requisition         = models.ForeignKey('SupplyRequisition', on_delete=models.CASCADE, related_name='email_queue')
    recipient_user      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requisition_email_queue')
    stage_label         = models.CharField(max_length=100)
    sign_url            = models.TextField()
    scheduled_send_time = models.DateTimeField()
    sent                = models.BooleanField(default=False)
    sent_at             = models.DateTimeField(null=True, blank=True)
    created_at          = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_send_time']

    def __str__(self):
        return f"Email to {self.recipient_user} for {self.requisition.ref_number} @ {self.scheduled_send_time}"


# ──────────────────────────────────────────────────────────────────────────────
# Institutional Folder Permission
# Superuser / Admin grants per-user access to Cloud Vault folder operations.
# ──────────────────────────────────────────────────────────────────────────────

class InstitutionalFolderPermission(models.Model):
    """
    Stores which Cloud Vault (Institutional Folder) operations a user is
    allowed to perform.  Superusers always bypass this table.
    """
    user                = models.OneToOneField(
        User, on_delete=models.CASCADE,
        related_name='folder_permission',
        verbose_name='User',
    )
    can_create_folder   = models.BooleanField(
        default=False,
        help_text='Allows the user to create new institutional folders in the Cloud Vault.',
    )
    can_delete_folder   = models.BooleanField(
        default=False,
        help_text='Allows the user to delete (soft-delete) institutional folders.',
    )
    can_download_folder = models.BooleanField(
        default=False,
        help_text='Allows the user to download the full contents of a folder as a ZIP archive.',
    )
    can_view_all_folders = models.BooleanField(
        default=False,
        help_text='Allows the user to view institutional folders from all departments (e.g. newly created institutional folders).',
    )
    granted_by          = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='folder_permissions_granted',
        verbose_name='Granted By',
    )
    granted_at          = models.DateTimeField(auto_now_add=True)
    notes               = models.TextField(
        blank=True,
        help_text='Optional notes explaining why this permission was granted.',
    )

    class Meta:
        verbose_name        = 'Institutional Folder Permission'
        verbose_name_plural = 'Institutional Folder Permissions'
        ordering            = ['user__username']

    def __str__(self):
        flags = []
        if self.can_create_folder:   flags.append('Create')
        if self.can_delete_folder:   flags.append('Delete')
        if self.can_download_folder: flags.append('Download')
        if self.can_view_all_folders: flags.append('ViewAll')
        return f"{self.user.username} → [{', '.join(flags) or 'No permissions'}]"

    # ── Convenience helpers ──────────────────────────────────────────────────

    @classmethod
    def user_can(cls, user, permission: str) -> bool:
        """
        Return True if *user* has the given permission or is a superuser.
        ``permission`` should be one of: 'can_create_folder', 'can_delete_folder',
        'can_download_folder', 'can_view_all_folders'.
        """
        if user.is_superuser:
            return True
        try:
            return bool(getattr(user.folder_permission, permission, False))
        except cls.DoesNotExist:
            return False


# ─────────────────────────────────────────────────────────
#  ZRP Electronic Records & Document Governance Engine
# ─────────────────────────────────────────────────────────

class DocumentAuditLog(models.Model):
    ACTION_CHOICES = (
        ('Create', 'Created Document'),
        ('View', 'Viewed Document'),
        ('Download', 'Downloaded Document'),
        ('Edit', 'Edited Document'),
        ('Move', 'Moved Document'),
        ('Approve', 'Approved Document'),
        ('Reject', 'Rejected Document'),
        ('Archive', 'Archived Document'),
        ('Delete', 'Deleted Document'),
        ('Restore', 'Restored Document'),
        ('Share', 'Shared Document'),
        ('Rename', 'Renamed Document'),
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    file_doc = models.ForeignKey(File, on_delete=models.CASCADE, null=True, blank=True, related_name="audit_logs")
    cloud_file = models.ForeignKey(CloudFile, on_delete=models.CASCADE, null=True, blank=True, related_name="audit_logs")
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    details = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Document Audit Logs"

    def __str__(self):
        doc_name = self.file_doc.title if self.file_doc else (self.cloud_file.name if self.cloud_file else 'Unknown')
        return f"{self.timestamp} - {self.user} - {self.action} on {doc_name}"


class DocumentWorkflow(models.Model):
    STATUS_CHOICES = (
        ('Initiated', 'Initiated'),
        ('Submitted', 'Submitted'),
        ('Reviewed', 'Reviewed'),
        ('Recommended', 'Recommended'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Implemented', 'Implemented'),
        ('Closed', 'Closed/Archived'),
    )
    file_doc = models.ForeignKey(File, on_delete=models.CASCADE, related_name="workflows", null=True, blank=True)
    cloud_file = models.ForeignKey(CloudFile, on_delete=models.CASCADE, related_name="workflows", null=True, blank=True)
    title = models.CharField(max_length=250)
    current_status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Initiated')
    initiator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="doc_workflows_initiated")
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="doc_workflows_reviewed")
    recommender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="doc_workflows_recommended")
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="doc_workflows_approved")
    comments = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Document Workflows"

    def __str__(self):
        return f"{self.title} - {self.current_status}"


# ─────────────────────────────────────────────────────────
#  ZRP Interview & Selection Governance Engine
# ─────────────────────────────────────────────────────────

class InterviewExercise(models.Model):
    INTERVIEW_TYPES = (
        ('Recruitment', 'Recruitment Interview'),
        ('Internal Promotion', 'Internal Promotion Interview'),
        ('Special Category', 'Special Category Interview'),
    )
    RECRUITMENT_MODES = (
        ('Internal', 'Internal Recruitment'),
        ('External', 'External Recruitment'),
        ('Combined', 'Combined Internal & External'),
    )
    STAGES = (
        ('Initial Screening', 'Initial Screening'),
        ('First Round', 'First Round'),
        ('Technical Assessment', 'Technical Assessment'),
        ('Final Panel Interview', 'Final Panel Interview'),
    )
    WORKFLOW_STATUS = (
        ('Vacancy Request', 'Vacancy / Interview Request'),
        ('Request Approved', 'Request Approved'),
        ('Candidate Selection', 'Candidate Selection'),
        ('Scheduled', 'Interview Scheduled'),
        ('Panel Notified', 'Panel Notified'),
        ('In Progress', 'Interviews In Progress'),
        ('Assessment Submitted', 'Assessment & Scoring Submitted'),
        ('Panel Recommended', 'Panel Recommended'),
        ('Executive Approved', 'Executive Approved'),
        ('Closed/Archived', 'Closed / Archived'),
    )
    title = models.CharField(max_length=250)
    interview_type = models.CharField(max_length=50, choices=INTERVIEW_TYPES, default='Recruitment')
    recruitment_mode = models.CharField(max_length=50, choices=RECRUITMENT_MODES, default='External')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="interview_exercises")
    position_title = models.CharField(max_length=250)
    grade_level = models.CharField(max_length=100)
    interview_stage = models.CharField(max_length=50, choices=STAGES, default='Final Panel Interview')
    workflow_status = models.CharField(max_length=50, choices=WORKFLOW_STATUS, default='Vacancy Request')
    
    scheduled_date = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=45)
    venue_or_link = models.CharField(max_length=500, blank=True, null=True, help_text="Physical venue or virtual meeting link")
    
    organized_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="organized_interviews")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_date']
        verbose_name_plural = "Interview Exercises"

    def __str__(self):
        return f"{self.title} ({self.position_title} - {self.grade_level})"


class InterviewPanelMember(models.Model):
    ROLES = (
        ('Panel Chair', 'Panel Chairperson'),
        ('Panel Secretary', 'Panel Secretary / Scribe'),
        ('Panelist', 'Technical Panelist'),
        ('HR Representative', 'HR Representative'),
        ('External Assessor', 'External Assessor'),
    )
    exercise = models.ForeignKey(InterviewExercise, on_delete=models.CASCADE, related_name="panel_members")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="interview_panel_assignments")
    role = models.CharField(max_length=50, choices=ROLES, default='Panelist')
    is_notified = models.BooleanField(default=False)
    notified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('exercise', 'user')

    def __str__(self):
        return f"{self.user.username} ({self.role}) -> {self.exercise.title}"


class InterviewCandidate(models.Model):
    CANDIDATE_TYPES = (
        ('Internal Staff', 'Internal Staff Member'),
        ('External Applicant', 'External Applicant'),
    )
    ATTENDANCE_STATUS = (
        ('Pending', 'Pending Confirmation'),
        ('Confirmed', 'Confirmed Attendance'),
        ('Rescheduled', 'Rescheduled'),
        ('Cancelled', 'Cancelled'),
        ('Attended', 'Attended'),
        ('No Show', 'No Show'),
    )
    VETTING_STATUS = (
        ('Pending Vetting', 'Pending Police Vetting'),
        ('Clearance Passed', 'Police Clearance Passed'),
        ('Vetting Failed', 'Vetting Clearance Failed'),
        ('Conditional', 'Conditional Clearance'),
    )
    exercise = models.ForeignKey(InterviewExercise, on_delete=models.CASCADE, related_name="candidates")
    full_name = models.CharField(max_length=250)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True, null=True)
    candidate_type = models.CharField(max_length=50, choices=CANDIDATE_TYPES, default='External Applicant')
    sequence_number = models.PositiveIntegerField(default=1)
    interview_time = models.DateTimeField(null=True, blank=True)
    attendance_status = models.CharField(max_length=30, choices=ATTENDANCE_STATUS, default='Pending')
    
    # Vetting & Police Clearance
    vetting_status = models.CharField(max_length=30, choices=VETTING_STATUS, default='Pending Vetting')
    police_clearance_ref = models.CharField(max_length=100, blank=True, null=True, help_text="Police Clearance Reference Number")
    vetting_notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['sequence_number', 'full_name']

    def __str__(self):
        return f"{self.full_name} ({self.exercise.position_title})"


class CandidateAssessment(models.Model):
    RECOMMENDATION_CHOICES = (
        ('Strongly Recommend', 'Strongly Recommend for Appointment'),
        ('Recommend', 'Recommend for Appointment'),
        ('Reserve Candidate', 'Reserve / Standby Candidate'),
        ('Do Not Recommend', 'Do Not Recommend'),
    )
    candidate = models.ForeignKey(InterviewCandidate, on_delete=models.CASCADE, related_name="assessments")
    panel_member = models.ForeignKey(User, on_delete=models.CASCADE, related_name="candidate_assessments")
    
    # Weighted Criteria Scores (Total Max: 100)
    academic_qualifications_score = models.PositiveIntegerField(default=0, help_text="Max 10 pts")
    relevant_experience_score = models.PositiveIntegerField(default=0, help_text="Max 15 pts")
    technical_knowledge_score = models.PositiveIntegerField(default=0, help_text="Max 25 pts")
    competencies_score = models.PositiveIntegerField(default=0, help_text="Max 15 pts")
    communication_skills_score = models.PositiveIntegerField(default=0, help_text="Max 10 pts")
    problem_solving_score = models.PositiveIntegerField(default=0, help_text="Max 10 pts")
    leadership_management_score = models.PositiveIntegerField(default=0, help_text="Max 15 pts")
    
    total_score = models.PositiveIntegerField(default=0, help_text="Automated Sum Max 100")
    comments = models.TextField(blank=True, null=True)
    recommendation = models.CharField(max_length=50, choices=RECOMMENDATION_CHOICES, default='Recommend')
    
    # Tamper-proofing protection
    is_locked = models.BooleanField(default=False, help_text="Protected against unauthorized alteration after submission")
    submitted_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('candidate', 'panel_member')
        ordering = ['-total_score']

    def save(self, *args, **kwargs):
        # Auto-compute total score
        self.total_score = (
            (self.academic_qualifications_score or 0) +
            (self.relevant_experience_score or 0) +
            (self.technical_knowledge_score or 0) +
            (self.competencies_score or 0) +
            (self.communication_skills_score or 0) +
            (self.problem_solving_score or 0) +
            (self.leadership_management_score or 0)
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Score for {self.candidate.full_name} by {self.panel_member.username}: {self.total_score}/100"


class InterviewAuditLog(models.Model):
    exercise = models.ForeignKey(InterviewExercise, on_delete=models.CASCADE, related_name="audit_logs")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)
    details = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.timestamp} - {self.user} - {self.action} on {self.exercise.title}"


class EmployeeTraining(models.Model):
    employee = models.ForeignKey(Borrower, on_delete=models.CASCADE, related_name="training_records")
    course_title = models.CharField(max_length=250)
    institution = models.CharField(max_length=250)
    completion_date = models.DateField()
    certificate_reference = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=50, default='Completed')

    class Meta:
        ordering = ['-completion_date']

    def __str__(self):
        return f"{self.employee.name()} - {self.course_title}"


class EmployeePerformance(models.Model):
    RATING_CHOICES = (
        ('Outstanding', 'Outstanding Performance'),
        ('Exceeds Expectations', 'Exceeds Expectations'),
        ('Meets Expectations', 'Meets Expectations'),
        ('Needs Improvement', 'Needs Improvement'),
        ('Unsatisfactory', 'Unsatisfactory'),
    )
    employee = models.ForeignKey(Borrower, on_delete=models.CASCADE, related_name="performance_evaluations")
    appraisal_period = models.CharField(max_length=100) # e.g., "2025 Annual Review"
    evaluator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="evaluations_conducted")
    score_percent = models.PositiveIntegerField(default=0)
    rating = models.CharField(max_length=50, choices=RATING_CHOICES, default='Meets Expectations')
    comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.name()} - {self.appraisal_period} ({self.rating})"


class RequisitionMovementLog(models.Model):
    requisition = models.ForeignKey(SupplyRequisition, on_delete=models.CASCADE, related_name='movement_history')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    from_stage = models.CharField(max_length=100)
    to_stage = models.CharField(max_length=100)
    comments = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.requisition.ref_number}: {self.from_stage} -> {self.to_stage} at {self.timestamp}"


# ─────────────────────────────────────────────────────────
#  ZRP Training, Travel & Subsistence Allowance (TSA) Engine
# ─────────────────────────────────────────────────────────

class TSARateConfig(models.Model):
    grade_level = models.CharField(max_length=100, unique=True, help_text="e.g. Executive, Director, Manager, Officer")
    daily_subsistence_rate = models.DecimalField(max_digits=10, decimal_places=2, default=80.00)
    nightly_accommodation_rate = models.DecimalField(max_digits=10, decimal_places=2, default=120.00)
    incidentals_rate = models.DecimalField(max_digits=10, decimal_places=2, default=20.00)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"TSA Rates for {self.grade_level}: ${self.daily_subsistence_rate}/day, ${self.nightly_accommodation_rate}/night"


class TravelRequest(models.Model):
    CATEGORY_CHOICES = (
        ('Training-Related Travel', 'Training-Related Travel'),
        ('Official Business Travel', 'Official Business Travel'),
        ('Other Authorised Travel', 'Other Authorised Travel'),
    )
    WORKFLOW_STAGES = (
        ('Training/Travel Request', '1. Training/Travel Request Initiated'),
        ('Supervisor Recommendation', '2. Supervisor Recommendation'),
        ('Budget/Finance Verification', '3. Budget & Finance Verification'),
        ('Approval', '4. Delegated Authority Approval'),
        ('TSA Request', '5. TSA Calculation & Request'),
        ('TSA Approval', '6. TSA Approval'),
        ('Payment', '7. Payment Processed'),
        ('Travel/Training In Progress', '8. Travel/Training In Progress'),
        ('Acquittal', '9. Acquittal & Receipts Review'),
        ('Closed', '10. Completed & Closed'),
    )
    STATUS_CHOICES = (
        ('Pending', 'Pending Approval'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled'),
    )
    ACQUITTAL_STATUS_CHOICES = (
        ('Pending Departure', 'Pending Departure'),
        ('Pending Acquittal', 'Pending Acquittal'),
        ('Submitted', 'Acquittal Submitted'),
        ('Cleared', 'Acquittal Cleared'),
        ('Overdue', 'Overdue Acquittal'),
    )
    
    ref_number = models.CharField(max_length=50, unique=True, blank=True)
    title = models.CharField(max_length=250)
    travel_category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Official Business Travel')
    requestor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='travel_requests')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='travel_requests')
    destination = models.CharField(max_length=250)
    purpose = models.TextField()
    
    start_date = models.DateField()
    end_date = models.DateField()
    num_days = models.PositiveIntegerField(default=1)
    num_nights = models.PositiveIntegerField(default=0)
    
    attendees = models.ManyToManyField(User, related_name='attended_travels', blank=True)
    budget_line = models.ForeignKey(Budget, on_delete=models.SET_NULL, null=True, blank=True, related_name='travel_requests')
    supporting_document = models.FileField(upload_to='travel_documents/', blank=True, null=True)
    
    # Automated TSA Rates & Calculations
    daily_subsistence_rate = models.DecimalField(max_digits=10, decimal_places=2, default=80.00)
    nightly_accommodation_rate = models.DecimalField(max_digits=10, decimal_places=2, default=120.00)
    transport_mileage_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_tsa_calculated = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # 10-Stage Workflow Tracking
    workflow_stage = models.CharField(max_length=50, choices=WORKFLOW_STAGES, default='Training/Travel Request')
    approval_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    
    supervisor_recommendation = models.CharField(max_length=30, choices=(('Pending', 'Pending'), ('Recommended', 'Recommended'), ('Not Recommended', 'Not Recommended')), default='Pending')
    supervisor_notes = models.TextField(blank=True, null=True)
    finance_verification = models.CharField(max_length=30, choices=(('Pending', 'Pending'), ('Verified', 'Verified & Funds Blocked'), ('Insufficient', 'Insufficient Funds')), default='Pending')
    finance_notes = models.TextField(blank=True, null=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_travels')
    
    # Payment Tracking
    payment_status = models.CharField(max_length=20, choices=(('Pending', 'Pending'), ('Paid', 'Paid')), default='Pending')
    proof_of_payment = models.FileField(upload_to='travel_pop/', blank=True, null=True)
    
    # Acquittal & Reminders Tracking
    acquittal_status = models.CharField(max_length=30, choices=ACQUITTAL_STATUS_CHOICES, default='Pending Departure')
    acquittal_due_date = models.DateField(blank=True, null=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        from decimal import Decimal
        import datetime
        from django.utils import timezone
        
        if not self.ref_number:
            count = TravelRequest.objects.count() + 1
            self.ref_number = f"ZRP-TSA-{timezone.now().year}-{count:04d}"
            
        # Parse start_date and end_date if passed as strings
        if isinstance(self.start_date, str) and self.start_date:
            try:
                self.start_date = datetime.date.fromisoformat(self.start_date.split('T')[0])
            except Exception:
                pass
        if isinstance(self.end_date, str) and self.end_date:
            try:
                self.end_date = datetime.date.fromisoformat(self.end_date.split('T')[0])
            except Exception:
                pass

        # Calculate days & nights
        if self.start_date and self.end_date and hasattr(self.start_date, 'strftime') and hasattr(self.end_date, 'strftime'):
            self.num_days = max(1, (self.end_date - self.start_date).days + 1)
            self.num_nights = max(0, (self.end_date - self.start_date).days)
            if not self.acquittal_due_date:
                self.acquittal_due_date = self.end_date + datetime.timedelta(days=7) # 7 days after travel return
                
        # Auto-compute total TSA expenditure
        self.total_tsa_calculated = (
            (Decimal(str(self.num_days or 1)) * Decimal(str(self.daily_subsistence_rate or 0))) +
            (Decimal(str(self.num_nights or 0)) * Decimal(str(self.nightly_accommodation_rate or 0))) +
            Decimal(str(self.transport_mileage_cost or 0))
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ref_number} - {self.title} ({self.travel_category})"


class TravelAcquittal(models.Model):
    travel_request = models.OneToOneField(TravelRequest, on_delete=models.CASCADE, related_name='acquittal')
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submitted_acquittals')
    
    actual_subsistence_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    actual_accommodation_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    actual_transport_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_actual_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    surplus_or_deficit = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Positive = Refund to ZRP, Negative = Claim from ZRP")
    
    acquittal_report_summary = models.TextField(help_text="Summary of travel outcomes and training achievements")
    receipts_attachment = models.FileField(upload_to='travel_acquittals/', blank=True, null=True, help_text="Scanned receipts & proof of expenditure")
    
    submitted_at = models.DateTimeField(default=timezone.now)
    is_verified_by_finance = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_acquittals')

    class Meta:
        ordering = ['-submitted_at']

    def save(self, *args, **kwargs):
        from decimal import Decimal
        self.total_actual_spent = (
            Decimal(str(self.actual_subsistence_spent or 0)) +
            Decimal(str(self.actual_accommodation_spent or 0)) +
            Decimal(str(self.actual_transport_spent or 0))
        )
        self.surplus_or_deficit = Decimal(str(self.travel_request.total_tsa_calculated or 0)) - self.total_actual_spent
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Acquittal for {self.travel_request.ref_number} by {self.submitted_by.username}"


class TravelAuditLog(models.Model):
    travel_request = models.ForeignKey(TravelRequest, on_delete=models.CASCADE, related_name='audit_history')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=100)
    details = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.timestamp} - {self.user} - {self.action} on {self.travel_request.ref_number}"


# ─────────────────────────────────────────────────────────
#  ZRP Universal Electronic Approval & Signing Engine
# ─────────────────────────────────────────────────────────

class ElectronicApprovalRecord(models.Model):
    STAGE_CHOICES = (
        ('Submitted', 'Submitted by'),
        ('Reviewed', 'Reviewed by'),
        ('Recommended', 'Recommended by'),
        ('Approved', 'Approved by'),
        ('Rejected', 'Rejected by'),
        ('Signed', 'Digitally Signed by'),
    )
    STATUS_CHOICES = (
        ('Pending', 'Pending Action'),
        ('Completed', 'Action Completed'),
        ('Rejected', 'Rejected'),
    )
    entity_type = models.CharField(max_length=100, help_text="e.g. LeaveRequest, SupplyRequisition, TravelRequest, TravelAcquittal, Meeting, InterviewExercise, FileDoc")
    entity_id = models.PositiveIntegerField()
    entity_reference = models.CharField(max_length=100, help_text="Transaction reference number")
    
    stage = models.CharField(max_length=50, choices=STAGE_CHOICES, default='Submitted')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='electronic_approvals')
    user_role = models.CharField(max_length=150, blank=True, null=True, help_text="Role or designation at time of signing")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Completed')
    
    signature_type = models.CharField(max_length=50, default='Digital Canvas Signature')
    signature_data = models.TextField(blank=True, null=True, help_text="Base64 encoded PNG canvas signature or stored signature reference")
    verification_hash = models.CharField(max_length=128, blank=True, null=True, help_text="SHA-256 Cryptographic Verification Hash")
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['timestamp']

    def save(self, *args, **kwargs):
        if not self.verification_hash:
            import hashlib
            payload = f"{self.entity_type}:{self.entity_id}:{self.user_id}:{self.stage}:{self.status}:{self.timestamp.isoformat()}:{self.signature_data or ''}"
            self.verification_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.stage} {self.user.username} on {self.entity_type} ({self.entity_reference}) at {self.timestamp}"


# ─────────────────────────────────────────────────────────
#  ZRP Attendance Management Engine
# ─────────────────────────────────────────────────────────

class EmployeeAttendance(models.Model):
    STATUS_CHOICES = (
        ('Present', 'Present (Normal Clock-In)'),
        ('Absence Without Leave', 'Absence Without Leave (AWOL)'),
        ('Approved Leave', 'Approved Leave'),
        ('Official Business', 'Official Business Travel'),
        ('Training', 'Training'),
        ('Approved Out-of-Office', 'Approved Out-of-Office Status'),
    )
    employee = models.ForeignKey(Borrower, on_delete=models.CASCADE, related_name='attendance_records', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_attendance_records')
    date = models.DateField(default=timezone.now)
    
    clock_in_time = models.DateTimeField(null=True, blank=True)
    clock_out_time = models.DateTimeField(null=True, blank=True)
    total_work_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Present')
    clock_in_ip = models.GenericIPAddressField(null=True, blank=True)
    clock_out_ip = models.GenericIPAddressField(null=True, blank=True)
    location_notes = models.CharField(max_length=250, default='ZRP Harare HQ')
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date', '-clock_in_time']

    def save(self, *args, **kwargs):
        if self.clock_in_time and self.clock_out_time:
            diff_sec = (self.clock_out_time - self.clock_in_time).total_seconds()
            self.total_work_hours = round(max(0, diff_sec / 3600.0), 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Attendance for {self.user.username} on {self.date}: {self.status}"


# ─────────────────────────────────────────────────────────
#  ZRP Admin, Stores, Vehicle, Fuel & GRV Models
# ─────────────────────────────────────────────────────────

class StoresItem(models.Model):
    item_name = models.CharField(max_length=250)
    category = models.CharField(max_length=100, default='Stationery')
    stock_balance = models.PositiveIntegerField(default=100)
    reorder_level = models.PositiveIntegerField(default=10)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.item_name} (Stock: {self.stock_balance})"


class StoresRequest(models.Model):
    ref_number = models.CharField(max_length=50, unique=True, blank=True)
    requestor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stores_requests')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='stores_requests')
    item = models.ForeignKey(StoresItem, on_delete=models.CASCADE, related_name='requests')
    quantity_requested = models.PositiveIntegerField()
    quantity_issued = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=30, choices=(('Pending', 'Pending Approval'), ('Approved', 'Approved'), ('Issued', 'Issued'), ('Rejected', 'Rejected')), default='Pending')
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='stores_issued')
    date_requested = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.ref_number:
            count = StoresRequest.objects.count() + 1
            self.ref_number = f"ZRP-STR-{timezone.now().year}-{count:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ref_number} - {self.item.item_name} (x{self.quantity_requested})"


class VehicleRequest(models.Model):
    ref_number = models.CharField(max_length=50, unique=True, blank=True)
    requestor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicle_requests')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='vehicle_requests')
    destination = models.CharField(max_length=250)
    purpose = models.TextField()
    travel_date = models.DateField()
    vehicle_allocated = models.CharField(max_length=100, blank=True, null=True, help_text="e.g. Toyota Fortuner AAE-4819")
    driver_allocated = models.CharField(max_length=100, blank=True, null=True, help_text="e.g. Mr. T. Moyo")
    status = models.CharField(max_length=30, choices=(('Pending', 'Pending'), ('Approved', 'Approved'), ('Allocated', 'Allocated'), ('Trip Completed', 'Trip Completed'), ('Rejected', 'Rejected')), default='Pending')
    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.ref_number:
            count = VehicleRequest.objects.count() + 1
            self.ref_number = f"ZRP-VEH-{timezone.now().year}-{count:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ref_number} - {self.destination} ({self.status})"


class FuelRequest(models.Model):
    ref_number = models.CharField(max_length=50, unique=True, blank=True)
    requestor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fuel_requests')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='fuel_requests')
    vehicle_registration = models.CharField(max_length=50)
    fuel_type = models.CharField(max_length=20, choices=(('Diesel', 'Diesel'), ('Petrol', 'Petrol')), default='Diesel')
    litres_requested = models.DecimalField(max_digits=8, decimal_places=2)
    litres_issued = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    coupon_number = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=30, choices=(('Pending', 'Pending'), ('Approved', 'Approved'), ('Issued', 'Issued'), ('Exceeded Limit', 'Exceeded Limit'), ('Rejected', 'Rejected')), default='Pending')
    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.ref_number:
            count = FuelRequest.objects.count() + 1
            self.ref_number = f"ZRP-FUL-{timezone.now().year}-{count:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ref_number} - {self.litres_requested}L ({self.vehicle_registration})"


class GoodsReceivedVoucher(models.Model):
    grv_number = models.CharField(max_length=50, unique=True, blank=True)
    requisition = models.ForeignKey(SupplyRequisition, on_delete=models.SET_NULL, null=True, blank=True, related_name='grvs')
    supplier_name = models.CharField(max_length=250)
    invoice_number = models.CharField(max_length=100)
    date_received = models.DateField(default=timezone.now)
    received_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_grvs')
    inspection_status = models.CharField(max_length=50, choices=(('Passed Inspection', 'Passed Inspection'), ('Partial Defect', 'Partial Defect'), ('Rejected', 'Rejected')), default='Passed Inspection')
    delivery_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.grv_number:
            count = GoodsReceivedVoucher.objects.count() + 1
            self.grv_number = f"ZRP-GRV-{timezone.now().year}-{count:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.grv_number} - {self.supplier_name} (Inv: {self.invoice_number})"


# ─────────────────────────────────────────────────────────
#  ZRP Universal Notification & Alert System Engine
# ─────────────────────────────────────────────────────────

class SystemNotification(models.Model):
    CATEGORY_CHOICES = (
        ('Leave', 'Leave Request Notification'),
        ('Procurement', 'Procurement Requisition Notification'),
        ('Travel/TSA', 'Training & Travel / TSA Approval'),
        ('Acquittal', 'Acquittal Due / Overdue Alert'),
        ('Meeting', 'Meeting Scheduled Notification'),
        ('Minutes', 'Minutes Approval Required'),
        ('Action Item', 'Action Item Deadline / Overdue Alert'),
        ('Interview', 'Interview Scheduled Notification'),
        ('Attendance', 'Attendance Exception Alert (AWOL/Late)'),
        ('Document', 'Document Workflow Action Required'),
    )
    CHANNEL_CHOICES = (
        ('In-System', 'In-System Portal Notification'),
        ('Email', 'Email Notification'),
        ('SMS', 'SMS Alert'),
        ('Multi-Channel', 'Multi-Channel (In-System + Email + SMS)'),
    )
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Document')
    title = models.CharField(max_length=250)
    message = models.TextField()
    link_url = models.CharField(max_length=250, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    channel = models.CharField(max_length=30, choices=CHANNEL_CHOICES, default='Multi-Channel')
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.category}] {self.title} -> {self.recipient.username} (Read: {self.is_read})"


# ─────────────────────────────────────────────────────────
#  ZRP Requirement 13: Inter-Module Automation Signals
# ─────────────────────────────────────────────────────────

@receiver(post_save, sender=LeaveRequest)
def auto_integrate_leave_approval(sender, instance, created, **kwargs):
    """
    Requirement 13 Core Principle: Capture information once and reuse across the system.
    When a LeaveRequest is approved:
    1. Deducts leave balance from Borrower/Employee profile.
    2. Auto-creates EmployeeAttendance records for approved days.
    3. Auto-logs ElectronicApprovalRecord SHA-256 hash.
    4. Dispatches SystemNotification to employee.
    """
    if instance.status == 'Approved':
        # 1. Update Borrower Leave Balance
        try:
            employee = Borrower.objects.get(user=instance.user)
            if instance.leave_type == 'Annual Leave' and employee.annual_leave_balance >= instance.days_requested:
                employee.annual_leave_balance -= instance.days_requested
                employee.save()
            elif instance.leave_type == 'Sick Leave' and employee.sick_leave_balance >= instance.days_requested:
                employee.sick_leave_balance -= instance.days_requested
                employee.save()
        except Borrower.DoesNotExist:
            pass

        # 2. Auto-synchronize Attendance & Out-of-Office for approved dates
        curr_date = instance.start_date
        while curr_date <= instance.end_date:
            EmployeeAttendance.objects.get_or_create(
                user=instance.user,
                date=curr_date,
                defaults={
                    'status': 'Approved Leave',
                    'location_notes': f"On {instance.leave_type}",
                    'remarks': f"Automated Leave Sync (Req #{instance.pk})"
                }
            )
            curr_date += datetime.timedelta(days=1)

        # 3. Auto-log Electronic Approval SHA-256 Record
        ElectronicApprovalRecord.objects.get_or_create(
            entity_type='LeaveRequest',
            entity_id=instance.pk,
            stage='Approved',
            defaults={
                'entity_reference': f"ZRP-LEV-{instance.pk:04d}",
                'user': instance.user,
                'user_role': 'HR Approver',
                'status': 'Completed',
                'comments': 'Automated cross-module single-point approval integration'
            }
        )

        # 4. Dispatch SystemNotification
        SystemNotification.objects.get_or_create(
            recipient=instance.user,
            category='Leave',
            title=f"Leave Request #{instance.pk} Approved",
            defaults={
                'message': f"Your {instance.leave_type} request for {instance.days} days starting {instance.start_date} has been approved.",
                'link_url': '/registry/leave-list/',
                'channel': 'Multi-Channel'
            }
        )


@receiver(post_save, sender=TravelRequest)
def auto_integrate_travel_approval(sender, instance, created, **kwargs):
    """
    Requirement 13 Integration:
    When a TravelRequest is approved:
    1. Auto-synchronizes Attendance to 'Official Business' or 'Training'.
    2. Auto-logs ElectronicApprovalRecord SHA-256 hash.
    3. Dispatches SystemNotification for TSA Disbursement.
    """
    if instance.approval_status == 'Approved':
        status_val = 'Training' if instance.travel_category == 'Training-Related Travel' else 'Official Business'
        curr_date = instance.start_date
        while curr_date <= instance.end_date:
            EmployeeAttendance.objects.get_or_create(
                user=instance.requestor,
                date=curr_date,
                defaults={
                    'status': status_val,
                    'location_notes': instance.destination,
                    'remarks': f"Automated Travel/TSA Sync ({instance.ref_number})"
                }
            )
            curr_date += datetime.timedelta(days=1)

        # Log Electronic Approval Record
        ElectronicApprovalRecord.objects.get_or_create(
            entity_type='TravelRequest',
            entity_id=instance.pk,
            stage='Approved',
            defaults={
                'entity_reference': instance.ref_number,
                'user': instance.requestor,
                'user_role': 'CEO / Authorizing Authority',
                'status': 'Completed',
                'comments': f"TSA Allowance Approved: ${instance.total_tsa_calculated}"
            }
        )

        # Dispatch SystemNotification
        SystemNotification.objects.get_or_create(
            recipient=instance.requestor,
            category='Travel/TSA',
            title=f"Travel & TSA Request {instance.ref_number} Approved",
            defaults={
                'message': f"Your travel to {instance.destination} has been approved with calculated TSA of ${instance.total_tsa_calculated}.",
                'link_url': '/registry/travel-tsa/',
                'channel': 'Multi-Channel'
            }
        )


# ─────────────────────────────────────────────────────────
#  ZRP Requirement 14: Institutional Templates & SOP Models
# ─────────────────────────────────────────────────────────

class ZrpDocumentTemplate(models.Model):
    """
    Fully flexible ZRP document template.
    Category is free-text — the organisation decides what categories exist.
    template_body stores the WYSIWYG HTML designed by the user.
    """
    title = models.CharField(max_length=250)
    # Free-text — no hard-coded choices.  Examples: "Leave Form", "Duty Roster", "GRV", "Station Report"
    category = models.CharField(max_length=120, blank=True, default='General')
    description = models.TextField(blank=True, null=True)
    version = models.CharField(max_length=20, default='1.0')
    # Rich HTML body built in the WYSIWYG editor
    template_body = models.TextField(blank=True, default='')
    template_file = models.FileField(upload_to='zrp_templates/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    requires_approvals = models.BooleanField(default=False)
    approvers_json = models.TextField(blank=True, default='[]')
    created_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_templates'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Keep using the existing DB table — class was renamed from ZmcDocumentTemplate to ZrpDocumentTemplate
        db_table = 'registry_zmcdocumenttemplate'
        ordering = ['category', 'title']

    def __str__(self):
        return f"{self.title} ({self.category} v{self.version})"

# Backward-compat alias
ZmcDocumentTemplate = ZrpDocumentTemplate


class InstitutionalPolicyDocument(models.Model):
    POLICY_TYPES = (
        ('HR Procedure', 'HR & Employee Procedures'),
        ('Procurement Procedure', 'Procurement & Delegated Authority Matrix'),
        ('Training & Travel Procedure', 'Training, Travel & TSA Procedures'),
        ('Records Management Procedure', 'Records Management & Classification Policy'),
        ('Attendance Procedure', 'Attendance & Timekeeping Policy'),
        ('Meeting Procedure', 'Board & Committee Meeting Procedures'),
        ('Recruitment Procedure', 'Recruitment & Candidate Assessment SOP'),
        ('ICT Security Policy', 'ICT Security & Data Protection Policy'),
    )
    title = models.CharField(max_length=250)
    policy_type = models.CharField(max_length=50, choices=POLICY_TYPES)
    summary = models.TextField()
    document_file = models.FileField(upload_to='zrp_policies/', null=True, blank=True)
    effective_date = models.DateField(default=timezone.now)
    approval_status = models.CharField(max_length=30, default='Approved')

    def __str__(self):
        return f"{self.title} ({self.policy_type})"













# ─────────────────────────────────────────────────────────────
# SYSTEMS MANAGER EQUIPMENT ASSET REGISTER
# ─────────────────────────────────────────────────────────────
class SystemsManagerEquipmentRegister(models.Model):
    STATUS_CHOICES = (
        ('Serviceable',   'Serviceable'),
        ('Unserviceable', 'Unserviceable'),
        ('Under Repair',  'Under Repair'),
        ('Written Off',   'Written Off / Condemned'),
        ('Issued',        'Issued Out'),
        ('In Store',      'In Store'),
    )

    entry_number    = models.CharField(max_length=50, unique=True, blank=True, help_text="Auto-generated entry number e.g. SM-001/2026")
    equipment_name  = models.CharField(max_length=255, help_text="Name/description of the equipment")
    serial_number   = models.CharField(max_length=200, blank=True, default='', help_text="Serial number(s) of the equipment")
    location        = models.CharField(max_length=255, blank=True, default='', help_text="Physical location / office / station")
    assigned_user   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sm_register_assignments', help_text="System user assigned to this equipment")
    assigned_user_name = models.CharField(max_length=200, blank=True, default='', help_text="Name (if not a system user)")
    status          = models.CharField(max_length=50, choices=STATUS_CHOICES, default='In Store')
    comments        = models.TextField(blank=True, default='', help_text="Additional comments or observations")
    cross_reference = models.CharField(max_length=255, blank=True, default='', help_text="Cross-reference to GR Voucher, Form 27, Asset Code, or PO number")
    linked_asset    = models.ForeignKey('Asset', on_delete=models.SET_NULL, null=True, blank=True, related_name='sm_register_entries')
    created_by      = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sm_register_created')
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Systems Manager Equipment Register Entry"
        verbose_name_plural = "Systems Manager Equipment Register"

    def __str__(self):
        return f"{self.entry_number} | {self.equipment_name} (S/N: {self.serial_number or '—'})"

    def save(self, *args, **kwargs):
        if not self.entry_number:
            year = timezone.now().year
            last = SystemsManagerEquipmentRegister.objects.filter(
                entry_number__startswith='SM-'
            ).order_by('-id').first()
            if last and last.entry_number:
                try:
                    num = int(last.entry_number.split('-')[1].split('/')[0]) + 1
                except Exception:
                    num = 1
            else:
                num = 1
            self.entry_number = f"SM-{num:03d}/{year}"
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────────────────────
# SYSTEMS MANAGER ISSUES REGISTER
# ─────────────────────────────────────────────────────────────
class SystemsManagerIssue(models.Model):
    STATUS_CHOICES = (
        ('Issued',   'Issued'),
        ('Returned', 'Returned'),
        ('Lost',     'Lost'),
    )

    issue_number      = models.CharField(max_length=50, unique=True, blank=True)
    equipment         = models.ForeignKey(SystemsManagerEquipmentRegister, on_delete=models.CASCADE, related_name='issues')
    issued_to_user    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sm_issues_received')
    issued_to_name    = models.CharField(max_length=200, blank=True, default='', help_text="Name, Rank & Force No. of receiver")
    issued_to_station = models.CharField(max_length=255, blank=True, default='', help_text="Station / Location")
    date_issued       = models.DateField(default=timezone.now)
    date_returned     = models.DateField(null=True, blank=True)
    issued_by         = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sm_issues_issued')
    qty               = models.PositiveIntegerField(default=1)
    status            = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Issued')
    remarks           = models.TextField(blank=True, default='')
    return_remarks    = models.TextField(blank=True, default='')
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_issued', '-id']
        verbose_name = "Systems Manager Issue"
        verbose_name_plural = "Systems Manager Issues Register"

    def __str__(self):
        receiver = self.issued_to_name or (self.issued_to_user.get_full_name() if self.issued_to_user else '—')
        return f"{self.issue_number} | {self.equipment.equipment_name} → {receiver}"

    def save(self, *args, **kwargs):
        if not self.issue_number:
            year = timezone.now().year
            last = SystemsManagerIssue.objects.filter(
                issue_number__startswith='SMI-'
            ).order_by('-id').first()
            if last and last.issue_number:
                try:
                    num = int(last.issue_number.split('-')[1].split('/')[0]) + 1
                except Exception:
                    num = 1
            else:
                num = 1
            self.issue_number = f"SMI-{num:03d}/{year}"
        super().save(*args, **kwargs)
