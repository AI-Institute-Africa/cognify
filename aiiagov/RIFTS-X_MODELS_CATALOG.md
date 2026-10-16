# RIFTS-X Complete Models Catalog

A comprehensive reference of all database models with their key fields, relationships, and purposes.

---

## Organization & Access Control

### 1. Organization
**Purpose:** Multi-tenant federation support for inter-organizational file sharing

| Field | Type | Notes |
|-------|------|-------|
| `name` | CharField(250) | Organization name (e.g., "Ministry of Lands") |
| `code` | CharField(100, unique=True) | Unique code (e.g., 'MINISTRY_OF_LANDS') |
| `api_endpoint` | URLField(500, blank) | API URL for federation |
| `public_key` | TextField(blank) | Cryptographic key for secure links |
| `is_local` | BooleanField(False) | True if local organization |
| `date_added` | DateTimeField(auto_now_add) | Creation timestamp |

**Relationships:** ← ForeignKey(Department, Tender, Contract)

---

### 2. Department
**Purpose:** Organizational hierarchy; groups users, budgets, projects

| Field | Type | Notes |
|-------|------|-------|
| `organization` | ForeignKey(Organization, blank) | Parent organization |
| `name` | CharField(250) | Department name |
| `description` | TextField(blank) | Department purpose |
| `efficiency_score` | FloatField(100.0) | Performance metric (0-100) |
| `date_added` | DateTimeField(auto_now_add) | Created |

**Relationships:** ← User, Borrower, Project, Budget, Asset, CostRecovery, File, Meeting, CloudFolder

---

### 3. UserSecurity
**Purpose:** Role-based access control with multi-tier approval gates

| Field | Type | Notes |
|-------|------|-------|
| `user` | OneToOneField(User) | Django user link |
| `department` | ForeignKey(Department, blank) | Department assignment |
| `role` | CharField(50, choices=ROLES) | Active role (Clerk→Executive→Board) |
| `platform` | CharField(20, choices=PLATFORMS) | 'RIFTS-X' or 'Governance' |
| `is_email_verified` | BooleanField(False) | Email verification status |
| `email_verification_token` | CharField(100, blank) | One-time verification token |
| `role_requested` | CharField(50, choices=ROLES) | Role requested at registration |
| `is_role_approved` | BooleanField(False) | Board/PL approval status |
| `is_pm_approved` | BooleanField(False) | Project Leader approval (for Team Members) |
| `role_approved_by` | ForeignKey(User, blank, related_name='approved_roles') | Approver identity |
| `role_approved_at` | DateTimeField(blank) | Approval timestamp |
| `mfa_enabled` | BooleanField(False) | MFA active |
| `mfa_code` | CharField(6, blank) | Current OTP |
| `mfa_expiry` | DateTimeField(blank) | OTP expiration |
| `last_login_ip` | GenericIPAddressField(blank) | Last login IP |
| `failed_login_attempts` | IntegerField(0) | Failed login counter |
| `is_locked` | BooleanField(False) | Account lock status |

**Choices - ROLES:**
- 'Clerk' → Registry Clerk
- 'Supervisor' → Registry Supervisor
- 'Auditor' → System Auditor
- 'Executive' → Executive Officer
- 'Portfolio Admin' → Portfolio Administrator
- 'Project Leader' → Project Leader
- 'Team Member' → Project Team Member
- 'Executive Viewer' → Executive Governance Viewer
- 'Project Management Team' → Project Management Team
- 'HODs' → Head of Departments
- 'Board of Executives' → Board of Executives

---

### 4. SecurityAlert
**Purpose:** Security incident logging

| Field | Type | Notes |
|-------|------|-------|
| `alert_type` | CharField(100) | Incident type (Failed MFA, Unauthorized Access, etc.) |
| `description` | TextField() | Details |
| `severity` | CharField(20, choices=SEVERITY) | Low/Medium/High/Critical |
| `user` | ForeignKey(User, blank) | User involved |
| `ip_address` | GenericIPAddressField(blank) | Source IP |
| `timestamp` | DateTimeField(auto_now_add) | Incident time |
| `is_resolved` | BooleanField(False) | Resolution status |

---

### 5. FederationLink
**Purpose:** Inter-organization federation with controlled sharing

| Field | Type | Notes |
|-------|------|-------|
| `source_org` | ForeignKey(Organization, related_name='federation_links_out') | Initiating organization |
| `target_org` | ForeignKey(Organization, related_name='federation_links_in') | Receiving organization |
| `link_status` | CharField(20, choices=STATUS_CHOICES) | Pending/Active/Revoked |
| `permissions` | JSONField(default=dict) | Role-based permissions object |
| `shared_secret` | CharField(250, blank) | Encryption key for link |
| `date_established` | DateTimeField(auto_now_add) | Created |

**Constraint:** `unique_together = ('source_org', 'target_org')`

---

### 6. ForensicAudit
**Purpose:** Complete audit trail of all system actions

| Field | Type | Notes |
|-------|------|-------|
| `user` | ForeignKey(User, blank) | User performing action |
| `action` | CharField(250) | Action description |
| `method` | CharField(10) | HTTP method (GET, POST, etc.) |
| `path` | TextField() | Request path |
| `payload` | JSONField(blank) | Request body data |
| `ip_address` | GenericIPAddressField(blank) | Source IP |
| `user_agent` | TextField(blank) | Browser/client info |
| `timestamp` | DateTimeField(auto_now_add) | Action time |

**Metadata:** Ordered by `-timestamp`, logged by ForensicAuditMiddleware

---

## Records & File Management

### 7. Category
**Purpose:** Top-level file classification

| Field | Type | Notes |
|-------|------|-------|
| `name` | CharField(250) | Category name |
| `description` | TextField(blank) | Purpose/scope |
| `status` | CharField(2, choices=[('1','Active'), ('2','Inactive')]) | Active/inactive |
| `delete_flag` | IntegerField(0) | Soft delete flag |
| `date_added` | DateTimeField(auto_now_add) | Created |
| `date_created` | DateTimeField(auto_now=True) | Last modified |

---

### 8. SubCategory
**Purpose:** Secondary file classification under Category

| Field | Type | Notes |
|-------|------|-------|
| `category` | ForeignKey(Category, on_delete=CASCADE) | Parent category |
| `name` | CharField(250) | Subcategory name |
| `description` | TextField(blank) | Purpose |
| `status` | CharField(2, choices=[('1','Active'), ('2','Inactive')]) | Active/inactive |
| `delete_flag` | IntegerField(0) | Soft delete |
| `date_added` | DateTimeField(auto_now_add) | Created |
| `date_created` | DateTimeField(auto_now=True) | Modified |

---

### 9. FileLocation
**Purpose:** Physical location tracking for paper files

| Field | Type | Notes |
|-------|------|-------|
| `building` | CharField(250) | Building name |
| `floor` | CharField(250) | Floor number/name |
| `office` | CharField(250, blank) | Office number |
| `cabinet` | CharField(250) | Cabinet number/code |
| `shelf` | CharField(250) | Shelf number/code |
| `description` | TextField(blank) | Additional location info |

---

### 10. RetentionRule
**Purpose:** Data lifecycle management and archival rules

| Field | Type | Notes |
|-------|------|-------|
| `name` | CharField(250) | Rule name |
| `years_to_keep` | IntegerField(7) | Retention period in years |
| `action_after_expiry` | CharField(100, choices=[...]) | Archive/Destroy/Review |
| `description` | TextField(blank) | Rule details |

---

### 11. File
**Purpose:** Core file entity with comprehensive tracking

| Field | Type | Notes |
|-------|------|-------|
| `sub_category` | ForeignKey(SubCategory, CASCADE) | Classification |
| `ref_num` | CharField(250) | Reference number (unique identifier) |
| `title` | CharField(250) | File title |
| `description` | TextField(blank) | Content description |
| `status` | CharField(2, choices=[('1','Active'), ('2','Inactive')]) | Active/inactive |
| `delete_flag` | IntegerField(0) | Soft delete flag |
| `date_added` | DateTimeField(auto_now_add) | Created |
| `date_created` | DateTimeField(auto_now=True) | Modified |
| `is_encrypted` | BooleanField(False) | Encryption status |
| `f_status` | CharField(10) | 'available' or 'borrowed' |
| `file_attachment` | FileField(upload_to='file_attachments/', blank) | Physical file upload |
| `qr_code` | ImageField(upload_to='qr_codes/', blank) | QR code image |
| `risk_score` | IntegerField(0) | Risk rating (0-100) |
| `risk_level` | CharField(20) | Low/Medium/High classification |
| `is_lost` | BooleanField(False) | Lost file flag |
| `current_location` | ForeignKey(FileLocation, blank) | Current physical location |
| `current_department` | ForeignKey(Department, blank) | Current department |
| `last_moved_at` | DateTimeField(blank) | Last movement timestamp |
| `last_handler` | ForeignKey(User, blank, related_name='last_handled_files') | Last person who handled |
| `sensitivity_level` | CharField(20, choices=[...]) | Normal/Sensitive/Highly Confidential |
| `retention_rule` | ForeignKey(RetentionRule, blank) | Linked retention policy |
| `expiry_date` | DateField(blank) | Retention expiry date |
| `external_link` | URLField(500, blank) | External reference URL |

**Signals:**
- `post_save`: Auto-generates QR code, creates Digital Twin, records creation in CustodyLog
- `save()`: Auto-encrypts sensitive fields if marked for encryption

---

### 12. FileVersion
**Purpose:** Version history for modified files

| Field | Type | Notes |
|-------|------|-------|
| `file_doc` | ForeignKey(File, CASCADE, related_name='versions') | Parent file |
| `borrower` | ForeignKey(Borrower, blank) | Who modified it |
| `notes` | TextField(blank) | Modification notes |
| `file` | FileField(upload_to='file_versions/') | Version content |
| `date_created` | DateTimeField(auto_now_add) | Version timestamp |

**Ordering:** `-date_created` (newest first)

---

### 13. Folio
**Purpose:** Sub-document grouping within a file

| Field | Type | Notes |
|-------|------|-------|
| `filee` | ForeignKey(File, CASCADE) | Parent file |
| `title` | CharField(250) | Folio title |
| `description` | TextField(blank) | Content |
| `delete_flag` | IntegerField(0) | Soft delete |
| `date_added` | DateTimeField(auto_now_add) | Created |
| `date_created` | DateTimeField(auto_now=True) | Modified |

---

## Borrowing & Access Workflow

### 14. Borrower
**Purpose:** User profile for file borrowers (external to Django User)

| Field | Type | Notes |
|-------|------|-------|
| `user` | OneToOneField(User, blank, related_name='borrower_profile') | Django user link |
| `code` | CharField(250) | Borrower ID code |
| `first_name` | CharField(250) | First name |
| `middle_name` | CharField(250, blank) | Middle name |
| `last_name` | CharField(250) | Last name |
| `gender` | CharField(20, choices=[('Male','Male'), ('Female','Female')]) | Gender |
| `department` | ForeignKey(Department, blank) | Department |
| `department_old` | CharField(250, blank) | Previous department |
| `email` | EmailField(250, blank) | Email |
| `status` | CharField(2, choices=[('1','Active'), ('2','Inactive')]) | Active/inactive |
| `delete_flag` | IntegerField(0) | Soft delete |
| `date_added` | DateTimeField(auto_now_add) | Created |
| `date_created` | DateTimeField(auto_now=True) | Modified |

**Methods:**
- `name()` → Returns formatted full name

---

### 15. Borrow
**Purpose:** File borrowing transaction tracking

| Field | Type | Notes |
|-------|------|-------|
| `borrower` | ForeignKey(Borrower, CASCADE, related_name='borrower_id_fk') | Who borrowed |
| `file_doc` | ForeignKey(File, CASCADE, related_name='file_doc_id_fk') | What was borrowed |
| `borrowing_date` | DateField() | Issue date |
| `return_date` | DateField() | Due date |
| `folio_ref` | CharField(250, blank) | Folio reference |
| `status` | CharField(5, choices=[('0','Issued'), ('1','Returned')]) | Issue/return status |
| `modification_notes` | TextField(blank) | Changes made by borrower |
| `modified_file` | FileField(upload_to='modified_files/', blank) | Updated version |
| `issued_folder` | ForeignKey('CloudFolder', blank, related_name='issued_borrows') | Cloud folder issued |
| `folder_permission` | CharField(10, choices=[('view','View Only'), ('edit','Edit Allowed')]) | Folder permissions |
| `folder_zip` | FileField(upload_to='issued_folder_zips/', blank) | Zipped folder download |
| `access_token` | CharField(100, blank) | Access token for recipient |
| `token_expiry` | DateTimeField(blank) | Token expiration |
| `temp_password` | CharField(100, blank) | Temporary password for access |
| `borrower_signature` | TextField(blank) | Base64-encoded signature from borrower (return) |
| `issuer_signature` | TextField(blank) | Base64-encoded signature from issuer (acceptance) |
| `return_confirmed` | BooleanField(False) | Issuer confirmed receipt |
| `confirmed_by` | ForeignKey(User, blank, related_name='confirmed_returns') | Who confirmed |
| `confirmed_at` | DateTimeField(blank) | Confirmation time |
| `date_added` | DateTimeField(auto_now_add) | Created |
| `date_created` | DateTimeField(auto_now=True) | Modified |
| `count_issue` | IntegerField(0) | Issue count |

---

### 16. CustodyLog
**Purpose:** Complete chain-of-custody tracking

| Field | Type | Notes |
|-------|------|-------|
| `file_doc` | ForeignKey(File, CASCADE, related_name='custody_logs') | Tracked file |
| `handler` | ForeignKey(User, blank) | Handler identity |
| `from_organization` | ForeignKey(Organization, blank, related_name='transfers_out') | Source org |
| `to_organization` | ForeignKey(Organization, blank, related_name='transfers_in') | Destination org |
| `from_department` | ForeignKey(Department, blank, related_name='transfers_out') | Source dept |
| `to_department` | ForeignKey(Department, blank, related_name='transfers_in') | Destination dept |
| `action` | CharField(100) | Created/Handover/Transfer/Archived |
| `reason` | TextField(blank) | Why moved |
| `location` | ForeignKey(FileLocation, blank) | Physical location |
| `timestamp` | DateTimeField(auto_now_add) | Action time |
| `digital_signature` | TextField(blank) | Handler signature (Base64) |
| `acknowledged` | BooleanField(False) | Recipient acknowledgment |
| `received_by` | ForeignKey(User, blank, related_name='custody_received') | Recipient identity |
| `received_at` | DateTimeField(blank) | Receipt time |

**Ordering:** `-timestamp`

---

### 17. DigitalShare
**Purpose:** Temporary digital file sharing with token-based access

| Field | Type | Notes |
|-------|------|-------|
| `file_doc` | ForeignKey(File, CASCADE, related_name='digital_shares') | Shared file |
| `shared_by` | ForeignKey(User, CASCADE, related_name='shares_initiated') | Sharer |
| `shared_to` | ForeignKey(User, CASCADE, related_name='shares_received') | Recipient |
| `token` | CharField(100, unique=True) | Access token |
| `status` | CharField(10, choices=[('active','Active'), ('returned','Returned')]) | Share status |
| `expires_at` | DateTimeField(blank) | Expiration time |
| `opened_at` | DateTimeField(blank) | When recipient first accessed |
| `returned_at` | DateTimeField(blank) | When returned |
| `created_at` | DateTimeField(auto_now_add) | Created |

---

### 18. SecureLink
**Purpose:** Time-limited secure download links

| Field | Type | Notes |
|-------|------|-------|
| `file_doc` | ForeignKey(File, CASCADE) | Linked file |
| `token` | CharField(100, unique=True) | Secure token |
| `expires_at` | DateTimeField() | Link expiration |
| `access_count` | IntegerField(0) | Download count |
| `created_at` | DateTimeField(auto_now_add) | Created |

**Methods:**
- `is_valid()` → True if not expired

---

## Digital Twin & Cloud Management

### 19. CloudFolder
**Purpose:** Hierarchical folder structure in digital twin vault

| Field | Type | Notes |
|-------|------|-------|
| `name` | CharField(255) | Folder name |
| `parent` | ForeignKey('self', blank, related_name='subfolders') | Parent folder |
| `department` | ForeignKey(Department, CASCADE, related_name='cloud_folders') | Owner department |
| `project_context` | CharField(255, blank) | Project/case reference |
| `created_by` | ForeignKey(User, blank) | Creator |
| `created_at` | DateTimeField(auto_now_add) | Created |
| `is_deleted` | BooleanField(False) | Soft delete |
| `deleted_at` | DateTimeField(blank) | Deletion time |

**Constraint:** `unique_together = ('name', 'parent', 'department')`

---

### 20. CloudFile
**Purpose:** Digital file representation

| Field | Type | Notes |
|-------|------|-------|
| `name` | CharField(255) | File name |
| `folder` | ForeignKey(CloudFolder, CASCADE, related_name='files') | Parent folder |
| `description` | TextField(blank) | File details |
| `is_internal_only` | BooleanField(True) | Internal/external visibility |
| `status` | CharField(20, choices=[...]) | Active/Archived/Trash |
| `owner` | ForeignKey(User, blank) | Owner |
| `tags` | JSONField(default=list) | Tag array |
| `created_at` | DateTimeField(auto_now_add) | Created |
| `updated_at` | DateTimeField(auto_now=True) | Modified |

**Property:**
- `latest_version` → Returns newest CloudFileVersion

---

### 21. CloudFileVersion
**Purpose:** Version control for cloud files

| Field | Type | Notes |
|-------|------|-------|
| `cloud_file` | ForeignKey(CloudFile, CASCADE, related_name='versions') | Parent file |
| `version_number` | PositiveIntegerField() | Version seq |
| `file_content` | FileField(upload_to='cloud_vault/%Y/%m/%d/') | Version content |
| `uploaded_by` | ForeignKey(User, blank) | Uploader |
| `commit_message` | TextField(blank) | Change log |
| `file_size` | BigIntegerField(0) | Size in bytes |
| `checksum` | CharField(255, blank) | Integrity check |
| `created_at` | DateTimeField(auto_now_add) | Timestamp |

**Constraint:** `unique_together = ('cloud_file', 'version_number')`

---

### 22. CloudShare
**Purpose:** File sharing with granular permissions

| Field | Type | Notes |
|-------|------|-------|
| `cloud_file` | ForeignKey(CloudFile, CASCADE, related_name='shares') | Shared file |
| `shared_by` | ForeignKey(User, CASCADE, related_name='shares_created') | Sharer |
| `shared_with_user` | ForeignKey(User, CASCADE, blank, related_name='shared_files') | Recipient (user) |
| `shared_with_email` | EmailField(blank) | Recipient (email) |
| `access_token` | CharField(100, unique=True) | Share token |
| `expiry_date` | DateTimeField() | Expiration |
| `can_download` | BooleanField(False) | Download permission |
| `can_edit` | BooleanField(False) | Edit permission |
| `is_revoked` | BooleanField(False) | Revocation status |
| `created_at` | DateTimeField(auto_now_add) | Created |

**Method:**
- `is_valid()` → True if not revoked and not expired

---

### 23. FileAccessLog
**Purpose:** Track digital file interactions

| Field | Type | Notes |
|-------|------|-------|
| `user` | ForeignKey(User, blank) | User performing action |
| `cloud_file` | ForeignKey(CloudFile, CASCADE, related_name='access_logs') | Accessed file |
| `version` | ForeignKey(CloudFileVersion, blank, related_name=...) | Specific version |
| `action` | CharField(20, choices=ACTIONS) | View/Download/Share/Rollback |
| `ip_address` | GenericIPAddressField(blank) | Source IP |
| `user_agent` | TextField(blank) | Browser info |
| `timestamp` | DateTimeField(auto_now_add) | Action time |

---

### 24. FileApproval
**Purpose:** Approval workflow for file operations

| Field | Type | Notes |
|-------|------|-------|
| `file_doc` | ForeignKey(File, CASCADE, related_name='approvals') | Approval target |
| `action_type` | CharField(50, choices=ACTION_TYPES) | Handover/Transfer/Digitization/Access |
| `requester` | ForeignKey(User, CASCADE, related_name='approvals_requested') | Who requested |
| `approver` | ForeignKey(User, blank, related_name='approvals_handled') | Who approves |
| `status` | CharField(20, choices=STATUS_CHOICES) | Pending/Approved/Rejected |
| `comments` | TextField(blank) | Approval comments |
| `timestamp` | DateTimeField(auto_now_add) | Created |
| `updated_at` | DateTimeField(auto_now=True) | Modified |

---

## Leave & HR Management

### 25. LeaveRequest
**Purpose:** Staff leave applications with multi-approver workflow

| Field | Type | Notes |
|-------|------|-------|
| `user` | ForeignKey(User, CASCADE, related_name='leave_requests') | Applicant |
| `leave_type` | CharField(50, choices=LEAVE_TYPES) | Annual/Sick/Maternity/Paternity/Casual/Other |
| `start_date` | DateField() | Leave start |
| `end_date` | DateField() | Leave end |
| `reason` | TextField() | Leave reason |
| `supporting_document` | FileField(upload_to='leave_documents/', blank) | Medical cert, etc. |
| `signed_document` | FileField(upload_to='leave_documents/signed/', blank) | Approval signature document |
| `approvers` | ManyToManyField(User, blank, related_name='leave_requests_to_approve') | Required approvers |
| `status` | CharField(20, choices=STATUS_CHOICES) | Pending/Approved/Rejected/Cancelled |
| `supervisor_comment` | TextField(blank) | Approval comment |
| `approved_by` | ForeignKey(User, blank, related_name='leaves_approved') | Final approver |
| `date_applied` | DateTimeField(auto_now_add) | Application date |

---

### 26. LeaveRequestApproval
**Purpose:** Individual approver signatures and tracking

| Field | Type | Notes |
|-------|------|-------|
| `leave_request` | ForeignKey(LeaveRequest, CASCADE, related_name='approvals') | Approval target |
| `approver` | ForeignKey(User, CASCADE, related_name='leave_approvals') | Approver identity |
| `status` | CharField(20, choices=STATUS_CHOICES) | Approved/Rejected/Pending |
| `comment` | TextField(blank) | Approver comment |
| `signature_data` | TextField(blank) | Base64-encoded signature |
| `ip_address` | GenericIPAddressField(blank) | Approver IP |
| `signed_at` | DateTimeField(blank) | Signature timestamp |
| `timestamp` | DateTimeField(auto_now_add) | Record created |

**Constraint:** `unique_together = ('leave_request', 'approver')`

---

## Financial Governance

### 27. Budget
**Purpose:** Departmental fiscal year budgets

| Field | Type | Notes |
|-------|------|-------|
| `department` | ForeignKey(Department, CASCADE, related_name='budgets') | Budget owner |
| `fiscal_year` | CharField(10) | Year (e.g., "2024") |
| `total_allocation` | DecimalField(15, 2) | Allocated amount |
| `spent_amount` | DecimalField(15, 2, default=0) | Amount spent |
| `date_added` | DateTimeField(auto_now_add) | Created |

**Property:**
- `remaining_amount` → Calculated: total_allocation - spent_amount

---

### 28. Requisition
**Purpose:** Item requests with approval and budget tracking

| Field | Type | Notes |
|-------|------|-------|
| `requestor` | ForeignKey(User, CASCADE, related_name='requisitions') | Who requested |
| `item_name` | CharField(250) | Item description |
| `quantity` | IntegerField(1) | Requested quantity |
| `estimated_unit_cost` | DecimalField(15, 2, default=0) | Cost per unit |
| `total_amount` | DecimalField(15, 2, default=0) | Total cost |
| `budget_line` | ForeignKey(Budget, blank, related_name='requisitions_linked') | Charged budget |
| `financial_document` | FileField(upload_to='financial_docs/', blank) | Support docs |
| `purpose` | TextField() | Purpose/justification |
| `status` | CharField(20, choices=STATUS_CHOICES) | Pending/Approved/Rejected/Fulfilled |
| `approver_comment` | TextField(blank) | Approval comment |
| `approved_by` | ForeignKey(User, blank, related_name='requisitions_approved') | Approver |
| `date_requested` | DateTimeField(auto_now_add) | Request date |

---

### 29. Expenditure
**Purpose:** Payment records linked to requisitions

| Field | Type | Notes |
|-------|------|-------|
| `requisition` | OneToOneField(Requisition, CASCADE, related_name='expenditure') | Paid requisition |
| `amount` | DecimalField(15, 2) | Paid amount |
| `date_paid` | DateTimeField(auto_now_add) | Payment date |
| `reference_no` | CharField(100, unique=True) | Payment reference |
| `payment_voucher` | FileField(upload_to='payment_vouchers/', blank) | Receipt/voucher |

---

### 30. CostRecovery
**Purpose:** Tracking cost savings and efficiency gains

| Field | Type | Notes |
|-------|------|-------|
| `department` | ForeignKey(Department, CASCADE, related_name='cost_recoveries') | Beneficiary dept |
| `hod` | ForeignKey(User, CASCADE, related_name='cost_recoveries_submitted') | HOD submitter |
| `amount_recovered` | DecimalField(15, 2) | Savings amount |
| `cost_savings_category` | CharField(50, choices=CATEGORY_CHOICES) | Labour/Materials/Overheads/Contracts/Technology/Other |
| `description` | TextField() | Savings details |
| `evidence_document` | FileField(upload_to='cost_recovery_evidence/', blank) | Supporting evidence |
| `date_recorded` | DateTimeField(auto_now_add) | Recorded |

---

## Procurement & Contracts

### 31. Tender
**Purpose:** Procurement notice/request for proposal

| Field | Type | Notes |
|-------|------|-------|
| `requisition` | ForeignKey(Requisition, blank) | Source requisition |
| `title` | CharField(250) | Tender title |
| `ref_num` | CharField(100, unique=True) | Reference number |
| `description` | TextField() | Scope of work |
| `tender_type` | CharField(50, choices=[...]) | Open/Restricted/Direct |
| `budget` | DecimalField(15, 2, blank) | Budget ceiling |
| `closing_date` | DateTimeField() | Bid closure time |
| `status` | CharField(20, choices=TENDER_STATUS) | Draft/Published/Evaluation/Awarded/Cancelled |
| `department` | ForeignKey(Department, CASCADE, related_name='tenders') | Requesting dept |
| `created_by` | ForeignKey(User, blank) | Creator |
| `date_created` | DateTimeField(auto_now_add) | Created |

---

### 32. Bid
**Purpose:** Vendor proposal in response to tender

| Field | Type | Notes |
|-------|------|-------|
| `tender` | ForeignKey(Tender, CASCADE, related_name='bids') | Parent tender |
| `bidder_name` | CharField(250) | Vendor name |
| `bidder_email` | EmailField() | Vendor email |
| `amount` | DecimalField(15, 2) | Bid amount |
| `submission_date` | DateTimeField(auto_now_add) | Submission time |
| `proposal_doc` | FileField(upload_to='tender_bids/', blank) | Proposal document |
| `status` | CharField(20, choices=BID_STATUS) | Pending/Successful/Unsuccessful |
| `evaluation_score` | FloatField(0.0) | Evaluation rating |
| `evaluation_notes` | TextField(blank) | Evaluator comments |

---

### 33. Contract
**Purpose:** Awarded contract from tender/bid

| Field | Type | Notes |
|-------|------|-------|
| `tender` | OneToOneField(Tender, CASCADE, related_name='contract') | Source tender |
| `awarded_bid` | OneToOneField(Bid, CASCADE, related_name='contract_awarded') | Winning bid |
| `title` | CharField(250) | Contract title |
| `contract_ref` | CharField(100, unique=True) | Reference number |
| `physical_file` | ForeignKey(File, blank) | Paper file link |
| `start_date` | DateField() | Contract start |
| `end_date` | DateField() | Contract end |
| `amount` | DecimalField(15, 2) | Contract value |
| `status` | CharField(20, choices=CONTRACT_STATUS) | Active/Completed/Expired/Terminated |
| `contract_document` | FileField(upload_to='contracts/', blank) | Contract document |
| `date_created` | DateTimeField(auto_now_add) | Created |

---

### 34. ContractMilestone
**Purpose:** Deliverable tracking within contract

| Field | Type | Notes |
|-------|------|-------|
| `contract` | ForeignKey(Contract, CASCADE, related_name='milestones') | Parent contract |
| `title` | CharField(250) | Milestone name |
| `description` | TextField(blank) | Details |
| `due_date` | DateField() | Expected completion |
| `completed_date` | DateField(blank) | Actual completion |
| `status` | CharField(20, choices=[...]) | Pending/Met/Overdue |

---

### 35. PerformanceEvaluation
**Purpose:** Vendor/contractor performance scoring

| Field | Type | Notes |
|-------|------|-------|
| `contract` | ForeignKey(Contract, CASCADE, related_name='evaluations') | Evaluated contract |
| `evaluation_date` | DateField(auto_now_add) | Evaluation date |
| `score` | IntegerField(5) | Score 1-10 |
| `comments` | TextField() | Evaluator remarks |
| `evaluated_by` | ForeignKey(User, blank) | Evaluator |

---

## Asset & Inventory

### 36. Asset
**Purpose:** Equipment and asset tracking with depreciation

| Field | Type | Notes |
|-------|------|-------|
| `name` | CharField(250) | Asset name |
| `asset_code` | CharField(100, unique=True) | Asset ID |
| `category` | CharField(50, choices=CATEGORY_CHOICES) | ICT/Furniture/Vehicle/Machinery/Other |
| `contract` | ForeignKey(Contract, blank) | Procurement contract |
| `physical_file` | ForeignKey(File, blank) | Paper file link |
| `department` | ForeignKey(Department, CASCADE, related_name='assets') | Owner dept |
| `acquisition_date` | DateField() | Purchase date |
| `acquisition_cost` | DecimalField(15, 2) | Purchase price |
| `useful_life` | IntegerField() | Expected life in years |
| `status` | CharField(50, choices=STATUS_CHOICES) | Active/Maintenance/Disposed/Lost |
| `description` | TextField(blank) | Details |
| `date_created` | DateTimeField(auto_now_add) | Created |

**Property:**
- `current_value` → Calculated depreciation using straight-line method

---

### 37. AssetMaintenance
**Purpose:** Maintenance schedule and tracking

| Field | Type | Notes |
|-------|------|-------|
| `asset` | ForeignKey(Asset, CASCADE, related_name='maintenance_logs') | Asset |
| `description` | TextField() | Maintenance description |
| `scheduled_date` | DateField() | Scheduled date |
| `performed_date` | DateField(blank) | Actual date |
| `cost` | DecimalField(15, 2, default=0) | Maintenance cost |
| `status` | CharField(50, choices=STATUS_CHOICES) | Scheduled/In Progress/Completed/Overdue |
| `performed_by` | CharField(250, blank) | Maintenance provider |

---

### 38. AssetCustody
**Purpose:** Asset assignment history

| Field | Type | Notes |
|-------|------|-------|
| `asset` | ForeignKey(Asset, CASCADE, related_name='custody_history') | Asset |
| `user` | ForeignKey(User, CASCADE, related_name='assigned_assets') | Assigned user |
| `issue_date` | DateField(auto_now_add) | Assignment date |
| `return_date` | DateField(blank) | Return date |
| `notes` | TextField(blank) | Custody notes |

---

## Knowledge Management

### 39. KnowledgeTag
**Purpose:** Flexible tagging for knowledge entries

| Field | Type | Notes |
|-------|------|-------|
| `name` | CharField(100, unique=True) | Tag name |

---

### 40. KnowledgeCategory
**Purpose:** Knowledge taxonomy

| Field | Type | Notes |
|-------|------|-------|
| `name` | CharField(250) | Category name |
| `description` | TextField(blank) | Purpose |
| `icon` | CharField(50) | FontAwesome icon class |

---

### 41. KnowledgeEntry
**Purpose:** Institutional knowledge (policies, decisions, guidance)

| Field | Type | Notes |
|-------|------|-------|
| `title` | CharField(250) | Entry title |
| `slug` | SlugField(250, unique=True, blank) | URL slug |
| `entry_type` | CharField(50, choices=ENTRY_TYPES) | Decision/Policy/Guidance |
| `content` | TextField() | Markdown/text content |
| `category` | ForeignKey(KnowledgeCategory, CASCADE, related_name='entries') | Category |
| `department` | ForeignKey(Department, blank) | Responsible dept |
| `physical_file` | ForeignKey(File, blank) | Paper trail |
| `meeting` | ForeignKey(Meeting, blank, related_name='knowledge_entries') | Source meeting |
| `tags` | ManyToManyField(KnowledgeTag, blank, related_name='entries') | Tags |
| `current_version` | IntegerField(1) | Latest version number |
| `status` | CharField(20, choices=STATUS_CHOICES) | Active/Superseded/Draft |
| `created_by` | ForeignKey(User, blank) | Author |
| `date_created` | DateTimeField(auto_now_add) | Created |
| `last_updated` | DateTimeField(auto_now=True) | Modified |

---

### 42. KnowledgeVersion
**Purpose:** Version history for knowledge entries

| Field | Type | Notes |
|-------|------|-------|
| `entry` | ForeignKey(KnowledgeEntry, CASCADE, related_name='versions') | Parent entry |
| `version_num` | IntegerField() | Version seq |
| `content` | TextField() | Version content |
| `change_summary` | TextField(blank) | Change log |
| `created_by` | ForeignKey(User, blank) | Editor |
| `created_at` | DateTimeField(auto_now_add) | Timestamp |

---

### 43. KnowledgeRelation
**Purpose:** Semantic links between knowledge entries

| Field | Type | Notes |
|-------|------|-------|
| `source` | ForeignKey(KnowledgeEntry, CASCADE, related_name='outgoing_relations') | Source entry |
| `target` | ForeignKey(KnowledgeEntry, CASCADE, related_name='incoming_relations') | Target entry |
| `relation_type` | CharField(50, choices=RELATION_TYPES) | Refers To/Supersedes/Similar To |
| `comments` | TextField(blank) | Relation details |
| `created_at` | DateTimeField(auto_now_add) | Created |

---

## Meetings & Resolutions

### 44. Meeting
**Purpose:** Board, committee, departmental meetings

| Field | Type | Notes |
|-------|------|-------|
| `title` | CharField(250) | Meeting title |
| `meeting_date` | DateTimeField() | Meeting time |
| `meeting_type` | CharField(50, choices=MEETING_TYPES) | Board/Committee/Departmental/General |
| `meeting_mode` | CharField(20, choices=MEETING_MODES) | Live (real-time) or Uploaded (post-meeting) |
| `location` | CharField(250, blank) | Physical location |
| `agenda` | FileField(upload_to='meeting_agendas/', blank) | Agenda document |
| `minutes` | FileField(upload_to='meeting_minutes/', blank) | Minutes document (PDF/Word) |
| `minutes_text` | TextField(blank) | Transcribed minutes |
| `organized_by` | ForeignKey(User, CASCADE, related_name='organized_meetings') | Organizer |
| `date_created` | DateTimeField(auto_now_add) | Record created |

---

### 45. Resolution
**Purpose:** Meeting resolutions with implementation tracking

| Field | Type | Notes |
|-------|------|-------|
| `meeting` | ForeignKey(Meeting, CASCADE, related_name='resolutions') | Source meeting |
| `resolution_number` | CharField(100) | Sequence number |
| `description` | TextField() | Resolution text |
| `status` | CharField(20, choices=STATUS_CHOICES) | Pending/In Progress/Implemented |
| `files` | ManyToManyField(File, blank, related_name='linked_resolutions') | Attached files |
| `assigned_to` | ForeignKey(User, blank) | Responsibility owner |
| `deadline` | DateField(blank) | Implementation deadline |
| `date_created` | DateTimeField(auto_now_add) | Created |

---

## Service & Support

### 46. ServiceTicket
**Purpose:** Inter-department service requests

| Field | Type | Notes |
|-------|------|-------|
| `requester` | ForeignKey(User, CASCADE, related_name='tickets_submitted') | Requester |
| `department` | ForeignKey(Department, CASCADE, related_name='tickets_received') | Target dept |
| `category` | CharField(50, choices=CATEGORY_CHOICES) | IT/Maintenance/HR/Facilities/Other |
| `priority` | CharField(20, choices=PRIORITY_CHOICES) | Low/Medium/High/Urgent |
| `status` | CharField(20, choices=STATUS_CHOICES) | Open/In Progress/Resolved/Closed |
| `subject` | CharField(250) | Ticket subject |
| `description` | TextField() | Issue details |
| `assigned_to` | ForeignKey(User, blank, related_name='assigned_tickets') | Assigned staff |
| `date_created` | DateTimeField(auto_now_add) | Created |
| `date_updated` | DateTimeField(auto_now=True) | Modified |

---

### 47. TicketUpdate
**Purpose:** Ticket comment and status history

| Field | Type | Notes |
|-------|------|-------|
| `ticket` | ForeignKey(ServiceTicket, CASCADE, related_name='updates') | Parent ticket |
| `user` | ForeignKey(User, CASCADE) | Commenter |
| `comment` | TextField() | Comment text |
| `new_status` | CharField(20, blank) | Status change (if any) |
| `date_created` | DateTimeField(auto_now_add) | Timestamp |

---

### 48. DigitalCertificate
**Purpose:** Digital credentials (approvals, clearances, memos)

| Field | Type | Notes |
|-------|------|-------|
| `certificate_type` | CharField(50, choices=CERT_TYPES) | Approval/Clearance/Memo/Archive |
| `subject` | CharField(255) | Certificate subject |
| `recipient_name` | CharField(255) | Recipient name |
| `content` | TextField() | Certificate text |
| `issuer` | ForeignKey(User, CASCADE, related_name='certificates_issued') | Issuer |
| `verification_code` | CharField(100, unique=True, db_index=True) | Verification code |
| `date_created` | DateTimeField(auto_now_add) | Issued |

---

### 49. Announcement
**Purpose:** Notice board announcements

| Field | Type | Notes |
|-------|------|-------|
| `title` | CharField(255) | Announcement title |
| `content` | TextField() | Announcement text |
| `priority` | CharField(20, choices=PRIORITY_CHOICES) | Normal/High Priority/Urgent |
| `author` | ForeignKey(User, CASCADE) | Author |
| `department` | ForeignKey(Department, blank) | Target dept (optional) |
| `date_created` | DateTimeField(auto_now_add) | Created |
| `expiry_date` | DateTimeField(blank) | Expiration |
| `is_active` | BooleanField(True) | Active status |

---

## Document Management

### 50. ScannerDevice
**Purpose:** Registered document scanners

| Field | Type | Notes |
|-------|------|-------|
| `name` | CharField(250) | Scanner name |
| `api_key` | CharField(100, unique=True) | API authentication |
| `location` | CharField(250, blank) | Physical location |
| `is_active` | BooleanField(True) | Active status |
| `last_seen` | DateTimeField(auto_now=True) | Last connection |
| `date_added` | DateTimeField(auto_now_add) | Registered |

---

### 51. ScannedDocument
**Purpose:** Scanned documents awaiting OCR and linkage

| Field | Type | Notes |
|-------|------|-------|
| `scanner` | ForeignKey(ScannerDevice, blank) | Source scanner |
| `raw_file` | FileField(upload_to='scanned_docs/') | Scanned image |
| `extracted_text` | TextField(blank) | OCR-extracted text |
| `classification` | CharField(100, blank) | Auto-detected category |
| `confidence_score` | FloatField(0.0) | OCR confidence (0-1) |
| `status` | CharField(20, choices=STATUS_CHOICES) | Pending/Processing/Completed/Failed/Awaiting Link |
| `linked_file` | ForeignKey(File, blank, related_name='scanned_documents') | Linked physical file |
| `linked_requisition` | ForeignKey(Requisition, blank) | Linked requisition |
| `linked_contract` | ForeignKey(Contract, blank) | Linked contract |
| `linked_leave_request` | ForeignKey(LeaveRequest, blank) | Linked leave |
| `metadata` | JSONField(default=dict) | Additional JSON data |
| `processed_at` | DateTimeField(blank) | Processing completion |
| `created_at` | DateTimeField(auto_now_add) | Scan timestamp |

---

## Synchronization

### 52. OfflineSyncQueue
**Purpose:** Mobile offline-first sync reconciliation

| Field | Type | Notes |
|-------|------|-------|
| `user` | ForeignKey(User, CASCADE, related_name='sync_records') | Mobile user |
| `local_id` | UUIDField(editable=False) | Device-generated ID |
| `ref_num` | CharField(250) | File/record reference |
| `data` | JSONField(default=dict) | Metadata, GPS coords, etc. |
| `attachment` | FileField(upload_to='sync_outbox/') | Document file |
| `status` | CharField(20, choices=STATUS_CHOICES) | Pending/Synced/Conflict/Failed |
| `conflict_notes` | TextField(blank) | Conflict resolution notes |
| `created_at` | DateTimeField(auto_now_add) | Created offline |
| `processed_at` | DateTimeField(blank) | Synced timestamp |

---

## Project Governance

### 53. Project
**Purpose:** Strategic initiatives with configurable approval gates

| Field | Type | Notes |
|-------|------|-------|
| `name` | CharField(250) | Project name |
| `description` | TextField(blank) | Project scope |
| `department` | ForeignKey(Department, CASCADE, related_name='projects') | Responsible dept |
| `owner` | ForeignKey(User, CASCADE, related_name='owned_projects') | Project leader |
| `budget` | DecimalField(15, 2, default=0) | Project budget |
| `start_date` | DateField(blank) | Start date |
| `end_date` | DateField(blank) | End date |
| `requisitions` | ManyToManyField(Requisition, blank, related_name='linked_projects') | Linked requisitions |
| `contracts` | ManyToManyField(Contract, blank, related_name='linked_projects') | Linked contracts |
| `files` | ManyToManyField(File, blank, related_name='linked_projects') | Linked files |
| `status` | CharField(20, choices=STATUS_CHOICES) | Planned/Active/Delayed/Done/Cancelled |
| `external_link` | URLField(blank) | Project URL |
| `is_deleted` | BooleanField(False) | Soft delete |
| `deleted_at` | DateTimeField(blank) | Deletion time |
| `created_at` | DateTimeField(auto_now_add) | Created |
| `updated_at` | DateTimeField(auto_now=True) | Modified |
| `requires_pmt` | BooleanField(True) | PMT gate required |
| `requires_hods` | BooleanField(True) | HODs gate required |
| `requires_board` | BooleanField(True) | Board gate required |

**Properties:**
- `active_phase` → Current active/review/awaiting phase
- `progress_percentage` → Calculated completion %
- `risk_indicator` → Dict with level, color, icon
- `approved_members` → QuerySet of approved team users

---

### 54. ProjectMember
**Purpose:** Team membership with approval

| Field | Type | Notes |
|-------|------|-------|
| `project` | ForeignKey(Project, CASCADE, related_name='project_memberships') | Project |
| `user` | ForeignKey(User, CASCADE, related_name='project_memberships') | Team member |
| `is_approved` | BooleanField(False) | Approval status |
| `approved_by` | ForeignKey(User, blank, related_name='approved_project_members') | Approver |
| `approved_at` | DateTimeField(blank) | Approval time |
| `joined_at` | DateTimeField(auto_now_add) | Joined |

**Constraint:** `unique_together = ('project', 'user')`

---

### 55. ProjectPhase
**Purpose:** Multi-gate approval checkpoint in project

| Field | Type | Notes |
|-------|------|-------|
| `project` | ForeignKey(Project, CASCADE, related_name='phases') | Parent project |
| `name` | CharField(200) | Phase name |
| `objectives` | TextField(blank) | Phase objectives |
| `sequence` | IntegerField(1) | Phase order |
| `start_date` | DateField(blank) | Planned start |
| `end_date` | DateField(blank) | Planned end |
| `deliverables` | TextField(blank) | Expected outputs |
| `required_documents` | ManyToManyField(File, blank, related_name='required_in_phases') | Required docs |
| `completion_criteria` | TextField(blank) | Acceptance criteria |
| `pm` | ForeignKey(User, blank, related_name='managed_phases') | Phase lead |
| `requires_approval` | BooleanField(True) | Needs gate approval |
| `status` | CharField(50, choices=STATUS_CHOICES) | Complex state (Pending→Done or rejection paths) |
| `approver` | ForeignKey(User, blank, related_name='phase_approvals') | Final gate approver |
| `approved_at` | DateTimeField(blank) | Gate completion time |
| `submitted_at` | DateTimeField(blank) | Submission time |
| `decision_reason` | TextField(blank) | Approval/rejection rationale |
| `is_deleted` | BooleanField(False) | Soft delete |
| `deleted_at` | DateTimeField(blank) | Deletion time |
| `consolidation_notes` | TextField(blank) | PM consolidation for gates |
| `team_member_comments` | TextField(blank) | Team member feedback |
| `project_leader_comments` | TextField(blank) | PL feedback |
| `pmt_comments` | TextField(blank) | PMT feedback |
| `hods_comments` | TextField(blank) | HODs feedback |
| `board_comments` | TextField(blank) | Board feedback |
| `pmt_required` | PositiveIntegerField(5) | Number of PMT approvals needed |
| `hods_required` | PositiveIntegerField(5) | Number of HODs approvals needed |
| `board_required` | PositiveIntegerField(5) | Number of Board approvals needed |

**Properties & Methods:**
- `team_member_approvals()` → QS of team member approvals
- `project_leader_approvals()` → QS of PL approvals
- `pmt_approvals()` → QS of PMT approvals
- `hods_approvals()` → QS of HODs approvals
- `board_approvals()` → QS of Board approvals
- `*_approval_count` → Count of each role's approvals
- `*_approval_percentage()` → Progress toward quorum
- `user_has_approved(user)` → Boolean
- `approver_ids` → List of approver user IDs
- `completed_tasks_count` → Completed phase tasks
- `total_tasks_count` → Total phase tasks
- `task_overdue_count` → Overdue task count
- `task_completion_percentage` → Phase completion %
- `get_approval_duration` → Time from submission to approval

---

### 56. PhaseApproval
**Purpose:** Individual role-based approval with signature

| Field | Type | Notes |
|-------|------|-------|
| `phase` | ForeignKey(ProjectPhase, CASCADE, related_name='approvals') | Gate |
| `approver` | ForeignKey(User, CASCADE, related_name='phase_approvals_given') | Approver |
| `role` | CharField(30, choices=ROLE_CHOICES) | Approver role (Team Member→Board) |
| `status` | CharField(20, choices=STATUS_CHOICES) | Approved/Rejected/Pending |
| `comment` | TextField() | Approval comment |
| `signature_data` | TextField(blank) | Base64 signature |
| `timestamp` | DateTimeField(auto_now_add) | Signature time |

**Property:**
- `is_relevant_history()` → Filters by role relevance

**Constraint:** `unique_together = ('phase', 'approver', 'role')`

---

### 57. ProjectSprint
**Purpose:** Agile sprint within a phase

| Field | Type | Notes |
|-------|------|-------|
| `phase` | ForeignKey(ProjectPhase, CASCADE, related_name='sprints') | Parent phase |
| `name` | CharField(200) | Sprint name |
| `goals` | TextField(blank) | Sprint goals |
| `status` | CharField(20, choices=STATUS_CHOICES) | Pending/Active/Done |
| `start_date` | DateField() | Sprint start |
| `end_date` | DateField() | Sprint end |
| `members` | ManyToManyField(User, blank, related_name='sprint_memberships') | Team members |

**Properties:**
- `total_tasks` → Task count
- `completed_tasks` → Done task count
- `remaining_tasks` → Pending/In Progress count
- `progress_percentage` → Completion %
- `duration_days` → Days in sprint
- `velocity` → Tasks/day average

---

### 58. ProjectTask
**Purpose:** Individual work item in sprint/phase

| Field | Type | Notes |
|-------|------|-------|
| `phase` | ForeignKey(ProjectPhase, CASCADE, related_name='tasks') | Parent phase |
| `sprint` | ForeignKey(ProjectSprint, blank, related_name='tasks') | Assigned sprint |
| `title` | CharField(250) | Task title |
| `description` | TextField() | Task details (mandatory) |
| `owner` | ForeignKey(User, CASCADE, related_name='project_tasks') | Assigned team member |
| `priority` | CharField(20, choices=PRIORITY_CHOICES) | Low/Medium/High/Critical |
| `start_date` | DateField(blank) | Start date |
| `due_date` | DateField() | Due date |
| `dependencies` | ManyToManyField('self', blank, symmetrical=False, related_name='blocked_tasks') | Blocking tasks |
| `progress` | IntegerField(0) | Progress % (0-100) |
| `linked_docs` | ManyToManyField(File, blank, related_name='linked_tasks') | Supporting docs |
| `physical_file` | ForeignKey(File, blank, related_name='task_physical_files') | Related file |
| `linked_requisition` | ForeignKey(Requisition, blank, related_name='linked_tasks') | Related requisition |
| `linked_contract` | ForeignKey(Contract, blank, related_name='linked_tasks') | Related contract |
| `linked_resolution` | ForeignKey(Resolution, blank, related_name='linked_tasks') | Related resolution |
| `status` | CharField(20, choices=STATUS_CHOICES) | To Do/In Progress/Review/Done/Blocked |
| `is_deliverable` | BooleanField(False) | Deliverable flag |
| `self_assigned` | BooleanField(False) | Self-created by team member |
| `assigned_by` | ForeignKey(User, blank, related_name='tasks_assigned') | Assigner (PM) |
| `completed_at` | DateTimeField(blank) | Completion time |
| `is_deleted` | BooleanField(False) | Soft delete |
| `deleted_at` | DateTimeField(blank) | Deletion time |

**Properties:**
- `is_overdue` → Boolean (past due date, not Done)
- `deadline_status` → 'danger'/'warning'/'normal'

---

### 59. TaskAttachment
**Purpose:** Files attached to tasks

| Field | Type | Notes |
|-------|------|-------|
| `task` | ForeignKey(ProjectTask, CASCADE, related_name='attachments') | Parent task |
| `file` | FileField(upload_to='project_tasks/', blank) | Local file |
| `external_link` | URLField(500, blank) | External URL |
| `filename` | CharField(250) | File name |
| `uploaded_at` | DateTimeField(auto_now_add) | Upload time |

---

## Summary Table

| # | Model | Category | Purpose |
|---|-------|----------|---------|
| 1 | Organization | Org | Federation support |
| 2 | Department | Org | Hierarchy |
| 3 | UserSecurity | Access | Role management |
| 4 | SecurityAlert | Access | Incident logging |
| 5 | FederationLink | Org | Inter-org sharing |
| 6 | ForensicAudit | Access | Complete audit trail |
| 7 | Category | Records | File classification L1 |
| 8 | SubCategory | Records | File classification L2 |
| 9 | FileLocation | Records | Physical location |
| 10 | RetentionRule | Records | Lifecycle rules |
| 11 | File | Records | Core file entity |
| 12 | FileVersion | Records | Version history |
| 13 | Folio | Records | Sub-grouping |
| 14 | Borrower | Borrowing | Borrower profile |
| 15 | Borrow | Borrowing | Borrowing transaction |
| 16 | CustodyLog | Borrowing | Chain of custody |
| 17 | DigitalShare | Borrowing | Temp sharing |
| 18 | SecureLink | Borrowing | Secure access links |
| 19 | CloudFolder | Digital Twin | Cloud hierarchy |
| 20 | CloudFile | Digital Twin | Digital file |
| 21 | CloudFileVersion | Digital Twin | Version control |
| 22 | CloudShare | Digital Twin | Cloud sharing |
| 23 | FileAccessLog | Digital Twin | Access tracking |
| 24 | FileApproval | Digital Twin | Approval workflow |
| 25 | LeaveRequest | HR | Leave application |
| 26 | LeaveRequestApproval | HR | Approver signature |
| 27 | Budget | Finance | Fiscal budget |
| 28 | Requisition | Finance | Purchase request |
| 29 | Expenditure | Finance | Payment record |
| 30 | CostRecovery | Finance | Savings tracking |
| 31 | Tender | Procurement | RFP/RFQ |
| 32 | Bid | Procurement | Vendor proposal |
| 33 | Contract | Procurement | Awarded agreement |
| 34 | ContractMilestone | Procurement | Deliverable tracking |
| 35 | PerformanceEvaluation | Procurement | Vendor scoring |
| 36 | Asset | Asset Mgmt | Equipment tracking |
| 37 | AssetMaintenance | Asset Mgmt | Maintenance schedule |
| 38 | AssetCustody | Asset Mgmt | Equipment assignment |
| 39 | KnowledgeTag | Knowledge | Tag system |
| 40 | KnowledgeCategory | Knowledge | Knowledge hierarchy |
| 41 | KnowledgeEntry | Knowledge | Policy/decision doc |
| 42 | KnowledgeVersion | Knowledge | Knowledge versioning |
| 43 | KnowledgeRelation | Knowledge | Semantic links |
| 44 | Meeting | Meetings | Meeting record |
| 45 | Resolution | Meetings | Action items |
| 46 | ServiceTicket | Support | Service request |
| 47 | TicketUpdate | Support | Request comment/history |
| 48 | DigitalCertificate | Support | Credentials |
| 49 | Announcement | Support | Notice board |
| 50 | ScannerDevice | Scanning | Scanner registration |
| 51 | ScannedDocument | Scanning | OCR document |
| 52 | OfflineSyncQueue | Sync | Mobile sync |
| 53 | Project | Governance | Strategic initiative |
| 54 | ProjectMember | Governance | Team membership |
| 55 | ProjectPhase | Governance | Gate checkpoint |
| 56 | PhaseApproval | Governance | Role approval |
| 57 | ProjectSprint | Governance | Agile sprint |
| 58 | ProjectTask | Governance | Work item |
| 59 | TaskAttachment | Governance | Task evidence |

**Total: 59 Core Models**

---

**Last Updated:** 2026-06-12  
**Django Version:** 5.2.7
