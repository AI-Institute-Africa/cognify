# RIFTS-X System Architecture Overview

**System Name:** Records Intelligence & File Tracking System (RIFTS-X)  
**Framework:** Django 5.2.7 + REST Framework  
**Database:** SQLite  
**Status:** Multi-platform integrated system (RIFTS-X + Governance Framework)

---

## Executive Summary

RIFTS-X is a comprehensive enterprise-grade records management, governance, and project tracking system. It integrates:
- **Physical Records Management** (file tracking, custody, location)
- **Project Governance** (multi-tier approval workflows, phase gates)
- **Financial Management** (budgets, requisitions, expenditures, cost recovery)
- **Knowledge Vault** (institutional knowledge management with versioning)
- **Security & Compliance** (forensic auditing, role-based access, MFA)
- **Procurement & Contracts** (tenders, bids, contract lifecycle management)
- **Asset Management** (IT equipment, vehicles, depreciation tracking)
- **Staff Management** (leave requests, requisitions, approvals)
- **AI-Assisted Intelligence** (automated insights, alerts, query processing)

---

## 1. DATABASE MODELS (registry/models.py)

### A. Core Organization & Access Control

| Model | Purpose |
|-------|---------|
| **Organization** | Multi-tenant federation support; stores ministry/org codes, API endpoints, public keys |
| **Department** | Organizational hierarchy; linked to users, budgets, projects, assets |
| **UserSecurity** | Role-based access control with board/PM/team member approval gates; 2FA settings, MFA codes |
| **SecurityAlert** | Security incidents logging (failed MFA, unusual activity, unauthorized access attempts) |
| **FederationLink** | Inter-organization federation with permissions, shared secrets, link status tracking |
| **ForensicAudit** | Complete audit trail: user actions, IP, user agent, timestamp, method, path, payload |

### B. Records & File Management

| Model | Purpose |
|-------|---------|
| **Category** | Top-level file classification; active/inactive status, soft delete |
| **SubCategory** | Secondary file classification under categories |
| **File** | Core file entity with ref_num, title, sensitivity levels, encryption, QR codes, risk scoring |
| **FileLocation** | Physical location tracking (building, floor, cabinet, shelf, office) |
| **FileVersion** | Version history for files; links to borrower, upload metadata |
| **Folio** | Sub-document grouping within files |
| **RetentionRule** | Data lifecycle rules (years to keep, post-expiry actions: Archive/Destroy/Review) |

### C. Borrowing & Access Workflow

| Model | Purpose |
|-------|---------|
| **Borrower** | User profile for file borrowers; department, status, soft delete |
| **Borrow** | Borrowing transaction; tracks issuer/return dates, signature capture, confirmation flow |
| **CustodyLog** | Complete chain of custody; handler, from/to org/dept, action, timestamp, digital signature |
| **DigitalShare** | Temporary file sharing with tokens; expires_at, opened_at, returned_at tracking |
| **SecureLink** | Time-limited secure access links; access counting, expiry validation |

### D. Digital Twin & Cloud Management

| Model | Purpose |
|-------|---------|
| **CloudFolder** | Hierarchical folder structure in cloud vault; parent-child relationships |
| **CloudFile** | Digital representation of physical files |
| **CloudFileVersion** | Version control with checksums, file size, commit messages |
| **CloudShare** | File sharing with granular permissions (download, edit), expiry, revocation |
| **FileAccessLog** | Access tracking (View, Download, Share, Rollback) with IP and user agent |
| **FileApproval** | Approval workflow for handover/transfer/digitization/access actions |

### E. Leave & HR Management

| Model | Purpose |
|-------|---------|
| **LeaveRequest** | Leave applications (Annual, Sick, Maternity, etc.); multi-approver support |
| **LeaveRequestApproval** | Individual approver signatures and timestamps; IP tracking |

### F. Financial Governance

| Model | Purpose |
|-------|---------|
| **Budget** | Departmental fiscal year budgets with spent/remaining amount tracking |
| **Requisition** | Item requests with budget linkage, approval workflow, financial documents |
| **Expenditure** | Payment records with voucher tracking and one-to-one requisition link |
| **CostRecovery** | Labour savings, materials, overhead, tech optimization tracking per department |

### G. Procurement & Contracts

| Model | Purpose |
|-------|---------|
| **Tender** | Public/restricted/direct procurement notices; status workflow (Draft→Published→Evaluation→Awarded) |
| **Bid** | Vendor bidding with proposals, evaluation scores, status |
| **Contract** | Awarded contract lifecycle; links to tender, bid, physical file trail |
| **ContractMilestone** | Deliverables and milestone tracking with status (Pending/Met/Overdue) |
| **PerformanceEvaluation** | Vendor performance scoring (1-10) with comments |

### H. Asset & Inventory

| Model | Purpose |
|-------|---------|
| **Asset** | Tracked equipment (ICT, Furniture, Vehicles, Machinery); auto-calculates current depreciation value |
| **AssetMaintenance** | Maintenance schedules with cost and completion tracking |
| **AssetCustody** | Equipment assignment history with issue/return dates |

### I. Knowledge Management

| Model | Purpose |
|-------|---------|
| **KnowledgeEntry** | Institutional knowledge (Decisions, Policies, Legal Guidance) with version control |
| **KnowledgeVersion** | Version history with change summary tracking |
| **KnowledgeCategory** | Knowledge classification hierarchy |
| **KnowledgeTag** | Flexible tagging system for knowledge entries |
| **KnowledgeRelation** | Semantic links between entries (Refers To, Supersedes, Similar To) |

### J. Meetings & Resolutions

| Model | Purpose |
|-------|---------|
| **Meeting** | Board/Committee/Departmental/General meetings with live or uploaded minutes |
| **Resolution** | Meeting resolutions with status tracking, file linkage, assigned implementation |

### K. Service & Support

| Model | Purpose |
|-------|---------|
| **ServiceTicket** | Inter-department service requests (IT, Maintenance, HR, Facilities) |
| **TicketUpdate** | Ticket comment history with status transitions |
| **DigitalCertificate** | Approval certs, clearance letters, memos, archive certs with verification codes |
| **Announcement** | Notice board for org-wide/dept-specific announcements with expiry |

### L. Document Scanning & OCR

| Model | Purpose |
|-------|---------|
| **ScannerDevice** | Registered scanner endpoints with API keys, location tracking |
| **ScannedDocument** | Scanned docs awaiting linkage; OCR extraction, classification, confidence scoring |

### M. Project Governance & Agile Management

| Model | Purpose |
|-------|---------|
| **Project** | Strategic initiatives with configurable governance gates (PMT/HODs/Board optional) |
| **ProjectMember** | Team membership with approval workflow |
| **ProjectPhase** | Multi-gate approval phases (Team→PL→PMT→HODs→Board) with flexible quorum settings |
| **PhaseApproval** | Individual role-based approvals with signature capture |
| **ProjectSprint** | Agile sprint management with velocity tracking |
| **ProjectTask** | Individual work items with priority, dependencies, overdue detection |
| **TaskAttachment** | File attachments for tasks (local or external links) |

### N. Offline Sync & Reconciliation

| Model | Purpose |
|-------|---------|
| **OfflineSyncQueue** | Mobile offline-first reconciliation; tracks sync status, conflicts, local UUIDs |

---

## 2. VIEW FUNCTIONS (registry/views.py)

### Authentication & Security (10+ views)
- `login_page()` / `login_user()` - Credential authentication with MFA enforcement
- `verify_mfa()` - OTP validation for Governance platform users
- `userregister()` / `save_register()` - RIFTS-X self-registration with email verification
- `governance_register()` / `save_governance_register()` - Governance-specific registration
- `verify_email()` - Email verification token processing
- `logout_user()` - Session cleanup
- `update_profile()` / `update_password()` - User credential management

### Role-Based Dashboards (5 views)
- `dashboard_md()` - Board strategic view (institutional metrics, benefits, pending board approvals)
- `dashboard_hod()` - PMT/HODs operational control (project oversight, cost recovery)
- `dashboard_pm()` - Project leader operations (managed projects, phase approvals, task reviews)
- `dashboard_member()` - Team member impact view (assigned tasks, project involvement)
- `home()` - Dynamic routing to appropriate dashboard by role

### Governance Administration (4 views)
- `manage_users()` - Board-only user role request panel with filtering (pending/strategic/approved)
- `user_role_action()` - POST handler for approve/reject/change role/change dept/toggle lock
- `pm_manage_members()` - Project Leader approval of Team Members
- `pm_member_action()` - PL approve/reject of team member registrations

### Records Management (24 views)
- **Categories:** `category()` / `manage_category()` / `save_category()` / `view_category()` / `delete_category()`
- **Sub-Categories:** `sub_category()` / `manage_sub_category()` / `save_sub_category()` / `view_sub_category()` / `delete_sub_category()`
- **Files:** `files()` / `manage_file_doc()` / `save_file_doc()` / `view_file_doc()` / `delete_file_doc()` / `download_version()` (with clearance checks)
- **Departments:** `departments()` / `manage_department()` / `save_department()` / `delete_department()`
- **Borrowers:** `borrower()` / `manage_borrower()` / `save_borrower()` / `view_borrower()` / `delete_borrower()`

### Borrowing Transactions (8 views)
- `borrows()` - Borrowing transaction list
- `manage_borrow()` / `save_borrow()` / `view_borrow()` / `delete_borrow()`
- `confirm_borrow_return()` - Issuer confirmation of returned files
- `recipient_dashboard()` - Borrower's personal borrow management

### Digital Sharing & Access Control (8 views)
- `generate_secure_link()` - Create time-limited secure access tokens
- `verify_secure_link()` / `verify_digital_share()` - Token validation
- `share_file_digital()` - Initiate digital sharing workflow
- `return_digital_share()` - Mark share as returned
- `download_file_bundle()` - Download issued folder as ZIP
- `access_with_token()` - Token-based access entry point

### File Custody & Transfer (6 views)
- `handover_file()` / `handover_modal()` - Department-to-department handover initiation
- `transfer_file()` / `transfer_modal()` - Inter-organization file transfer
- `file_timeline()` - Complete custody history visualization
- `acknowledge_transfer()` - Recipient acknowledgment of transferred files

### Forensic Audit & Compliance (3 views)
- `forensic_audit_export()` - Audit trail extraction for specific file
- `get_audit_highlights()` - Key audit events summary
- `executive_dashboard()` - Executive compliance overview

### OnlyOffice Integration (4 views)
- `edit_issued_file()` / `save_issued_file_edit()` - LibreOffice/Word editing workflow
- `get_onlyoffice_document_config()` - OnlyOffice document editor configuration
- `get_onlyoffice_file()` - File serving for OnlyOffice
- `onlyoffice_callback()` - Document save callback handler

### Leave Management (8 views)
- `leave_list()` / `manage_leave()` / `save_leave()` - Employee leave request submission
- `leave_applications()` / `approve_leave()` - Manager approval workflow
- `leave_sign_visual()` / `leave_view()` - Visual signature capture
- `verify_leave_approval()` - Email verification of approvals
- `manage_signature()` - User signature profile management
- `approver_directory()` - Directory of approvers

### Financial Management (8 views)
- `requisition_list()` / `manage_requisition()` / `save_requisition()` / `all_requisitions()` - Requisition CRUD
- `approve_requisition()` - Manager approval with budget check
- `expenditure_dashboard()` - Financial overview
- `manage_expenditure()` / `save_expenditure()` - Payment record creation

### Procurement & Contracts (10 views)
- `tender_list()` / `manage_tender()` / `save_tender()` / `view_tender()` - Tender lifecycle
- `bid_list()` / `manage_bid()` / `save_bid()` / `award_bid()` - Bidding process
- `contract_list()` / `view_contract()` - Contract management
- `save_milestone()` / `save_performance()` - Milestone & evaluation tracking

### Asset Management (6 views)
- `asset_list()` / `manage_asset()` / `save_asset()` / `view_asset()` - Asset CRUD
- `save_asset_maintenance()` - Maintenance record creation
- `save_asset_custody()` - Asset assignment tracking
- `asset_depreciation_report()` - Financial reporting

### Knowledge Vault (5 views)
- `knowledge_vault()` - Institutional knowledge browsing
- `manage_knowledge()` / `save_knowledge()` - Knowledge entry creation/editing
- `view_knowledge()` - Knowledge entry detail view
- `save_knowledge_relation()` - Semantic relationship creation

### Meetings & Resolutions (7 views)
- `meeting_list()` / `manage_meeting()` / `save_meeting()` / `view_meeting()` - Meeting management
- `manage_resolution()` / `save_resolution()` - Resolution tracking
- `update_resolution_status()` - Status updates
- `record_minutes()` / `save_minutes_text()` - Meeting minutes (text & transcription)
- `download_minutes_pdf()` - PDF export of minutes

### User & Administration (8 views)
- `profile()` - User profile view
- `users()` / `manage_user()` / `save_user()` / `delete_user()` - User administration
- `folio()` / `manage_folio()` / `save_folio()` / `view_folio()` / `delete_folio()` - Folio management
- `get_overdue_count()` - AJAX endpoint for overdue files

### AI & Intelligence
- `ai_assistant()` - AI assistant interface

### Support Functions
- `context_data()` - Global template context builder
- `docx_version_to_html()` - Document version rendering
- `mask_sensitive_data()` - Role-based data masking for confidential files
- `role_required()` - Decorator for role-based access
- `user_is_not_borrower()` - Decorator restricting borrowers to recipient dashboard

---

## 3. SERVICE LAYER (registry/services/)

### Core Services

| Service | Purpose | Key Methods |
|---------|---------|-------------|
| **ai_assistant.py** | AI-powered query processing and insights | Generate responses, analyze patterns |
| **ai_assistant_enhanced.py** | Advanced NLP with intent detection, entity extraction | `detect_intent()`, `extract_entities()`, `process_intelligent_query()` |
| **automation.py** | Background task automation | `process_all_alerts()`, `check_upcoming_deadlines()`, `check_overdue_tasks()`, `check_sprint_status()` |
| **cloud.py** | Digital Twin cloud vault management | `CloudService`, `DocxHTMLParser` |
| **collaboration.py** | Real-time collaboration features | Document sync, concurrent editing support |
| **custody.py** | Chain-of-custody tracking | `CustodyService` with creation, handover, transfer logging |
| **document_signer.py** | Digital signature capture and validation | Signature metadata, verification |
| **federation.py** | Inter-organizational federation protocols | Link establishment, permission sharing |
| **governance.py** | Governance workflow orchestration | Phase gates, approval quorum logic, role transitions |
| **intelligence.py** | AI Governor with institutional intelligence | `AIGovernor` for predictive analytics, anomaly detection |
| **location.py** | Physical location intelligence | `LocationIntelligence` for tracking file movements |
| **onlyoffice_service.py** | LibreOffice/OnlyOffice integration | Document editing callbacks, version management |
| **permissions.py** | Fine-grained permission enforcement | `PermissionService` with PM_ROLES, governance permission checks |
| **risk.py** | Risk scoring and management | `RiskEngine` for file risk assessment |
| **scanner.py** | Document scanner integration | `ScannerService` for OCR, classification, confidence scoring |
| **security.py** | Encryption, decryption, security operations | `EncryptionService` for sensitive field encryption |
| **sla.py** | Service level agreement enforcement | `SLAManager` for deadline tracking |
| **sync.py** | Offline-first synchronization | Conflict resolution, queue processing |
| **twin.py** | Digital Twin lifecycle management | `DigitalTwinService` auto-provisioning for new files |

---

## 4. TEMPLATE HIERARCHY (registry/templates/)

### Main Templates (HTML)
- **base.html** - Master layout with navigation, footer, messaging
- **login.html** - Authentication interface
- **register.html** - RIFTS-X user registration
- **topNavigation.html** - Shared top navbar component
- **home.html** - Landing page
- **profile.html** - User profile display
- **manage_profile.html** - Profile editor
- **update_password.html** - Password change form

### Governance Platform (`governance/` subfolder)
- **register.html** - Governance-specific registration form
- **dashboard_md.html** - Board strategic dashboard
- **dashboard_hod.html** - PMT/HODs operational dashboard
- **dashboard_pm.html** - Project leader project dashboard
- **dashboard_member.html** - Team member task dashboard
- **manage_users.html** - Board user governance panel
- **pm_manage_members.html** - PL team member approval

### Records Management
- **category.html** / **manage_category.html** / **view_category.html**
- **sub_category.html** / **manage_sub_category.html** / **view_sub_category.html**
- **files.html** / **manage_files.html** / **view_files.html**
- **borrower.html** / **manage_borrower.html** / **view_borrower.html**
- **borrows.html** / **manage_borrow.html** / **view_borrow.html**
- **folio.html** / **manage_folio.html** / **view_folio.html**
- **department.html** / **manage_department.html**

### Digital Sharing & Access
- **digital_share_view.html** - Share recipient interface
- **digital_twin.html** - Digital Twin visualization
- **file_digital_twin.html** - File-specific twin view
- **file_timeline.html** - Custody history timeline
- **recipient_dashboard.html** - Borrower personal dashboard
- **secure_verify.html** - Secure link verification

### File Operations
- **manage_handover.html** - Handover form
- **manage_transfer.html** - Transfer form
- **manage_share.html** - Share creation form
- **file_mark_lost.html** / **file_mark_found.html** - File status updates
- **borrow_folder_view.html** - Issued folder viewer
- **edit_issued_file.html** - Inline document editing

### Leave Management
- **leave_list.html** - Employee leave listing
- **manage_leave.html** - Leave request form
- **leave_applications.html** - Manager approval list
- **leave_view.html** - Leave detail view
- **leave_sign_visual.html** - Signature capture interface
- **approver_directory.html** - Approver listing

### Financial & Procurement
- **requisition_list.html** / **manage_requisition.html** / **requisitions_admin.html**
- **expenditure_dashboard.html** - Financial overview
- **manage_expenditure.html**
- **tender_list.html** / **manage_tender.html** / **view_tender.html**
- **bid_list.html** / **manage_bid.html**
- **contract_list.html** / **view_contract.html**
- **budget_list.html** / **manage_budget.html**

### Asset Management
- **asset_list.html** / **manage_asset.html** / **view_asset.html**
- **asset_depreciation.html** - Depreciation reports

### Knowledge & Documentation
- **knowledge_vault.html** - Knowledge entry browsing
- **manage_knowledge.html** - Knowledge editor
- **view_knowledge.html** - Knowledge detail view

### Meetings & Collaboration
- **meeting_list.html** / **manage_meeting.html** / **view_meeting.html**
- **record_minutes.html** - Meeting minutes recorder
- **manage_resolution.html** - Resolution tracking
- **manage_announcement.html** - Notice board posting

### Support & Integration
- **service_tickets.html** / **manage_ticket.html** / **view_ticket.html**
- **scanned_docs.html** - OCR document viewer
- **scanner_devices.html** - Scanner management
- **mobile_capture.html** - Mobile scanning interface
- **ai_assistant.html** - AI query interface
- **cloud/** - Cloud vault templates
- **registry/** - Specialized registry templates
- **certificates.html** / **certificate_template.html** / **manage_certificate.html**
- **notice_board.html** - Announcements

---

## 5. URL ROUTING PATTERNS (registry/urls.py)

### Key Route Categories

**Authentication Routes**
```
/login → login_page / login_user
/register → userregister / save_register
/governance/register → governance_register / save_governance_register
/verify-email/<token> → verify_email
/verify_mfa → verify_mfa
/logout → logout_user
```

**Governance Dashboard Routes**
```
/dashboard/md → dashboard_md (Board Strategic)
/dashboard/hod → dashboard_hod (PMT/HODs)
/dashboard/pm → dashboard_pm (Project Leader)
/dashboard/member → dashboard_member (Team Member)
/governance/users/ → manage_users
/governance/users/action/ → user_role_action
/governance/pm/members/ → pm_manage_members
/governance/pm/members/action/ → pm_member_action
```

**Records Management Routes**
```
/files/ → files
/manage_file_doc → manage_file_doc
/manage_file_doc/<pk> → manage_file_doc
/save_file_doc → save_file_doc
/view_file_doc/<pk> → view_file_doc
/delete_file_doc/<pk> → delete_file_doc
/download_version/<pk> → download_version (secure)
```

**Borrowing Routes**
```
/borrows → borrows (list)
/manage_borrow → manage_borrow
/manage_borrow/<pk> → manage_borrow
/save_borrow → save_borrow
/view_borrow/<pk> → view_borrow
/delete_borrow/<pk> → delete_borrow
/confirm_borrow_return/<pk> → confirm_borrow_return
```

**Digital Sharing Routes**
```
/share_file_digital/<pk> → share_file_digital
/verify_digital_share/<token> → verify_digital_share
/return_digital_share/<token> → return_digital_share
/secure_link/generate/<pk> → generate_secure_link
/secure_link/verify/<token> → verify_secure_link
/access/<token> → access_with_token
```

**Custody & Transfer Routes**
```
/handover_file/ → handover_file
/handover_modal/ → handover_modal
/transfer_file/ → transfer_file
/transfer_modal/ → transfer_modal
/acknowledge_transfer/<pk> → acknowledge_transfer
/file_timeline/<pk>/ → file_timeline
```

**Leave Management Routes**
```
/leaves → leave_list
/manage_leave → manage_leave
/save_leave → save_leave
/leave_applications → leave_applications
/approve_leave → approve_leave
/leave/<pk>/sign-visual/ → leave_sign_visual
/leave/<pk>/view/ → leave_view
/leave/verify/<token>/ → verify_leave_approval
/profile/signature/ → manage_signature
/approvers/directory/ → approver_directory
```

**Financial Routes**
```
/requisitions → requisition_list
/manage_requisition → manage_requisition
/save_requisition → save_requisition
/all_requisitions → all_requisitions
/approve_requisition → approve_requisition
/financial/dashboard/ → expenditure_dashboard
/financial/expenditure/manage/ → manage_expenditure
/financial/expenditure/save/ → save_expenditure
/budgets/ → budget_list
/budget/manage/ → manage_budget
/budget/save/ → save_budget
```

**Procurement Routes**
```
/procurement/tenders/ → tender_list
/procurement/tender/manage/ → manage_tender
/procurement/tender/save/ → save_tender
/procurement/tender/<pk>/ → view_tender
/procurement/tender/<pk>/bids/ → bid_list
/procurement/bid/manage/<pk>/ → manage_bid
/procurement/bid/save/ → save_bid
/procurement/bid/award/<pk>/ → award_bid
/procurement/contracts/ → contract_list
/procurement/contract/view/<pk>/ → view_contract
/procurement/contract/milestone/save/ → save_milestone
/procurement/contract/performance/save/ → save_performance
```

**Asset Management Routes**
```
/assets/ → asset_list
/assets/manage/ → manage_asset
/assets/save/ → save_asset
/assets/view/<pk>/ → view_asset
/assets/maintenance/save/ → save_asset_maintenance
/assets/custody/save/ → save_asset_custody
/assets/reports/depreciation/ → asset_depreciation_report
```

**Knowledge Vault Routes**
```
/knowledge/ → knowledge_vault
/manage_knowledge/ → manage_knowledge
/manage_knowledge/<pk>/ → manage_knowledge
/save_knowledge/ → save_knowledge
/view_knowledge/<pk>/ → view_knowledge
/save_knowledge_relation/ → save_knowledge_relation
```

**Meeting & Resolution Routes**
```
/meetings → meeting_list
/manage_meeting → manage_meeting
/manage_meeting/<id> → manage_meeting
/save_meeting → save_meeting
/view_meeting/<id> → view_meeting
/manage_resolution/<meeting_id> → manage_resolution
/manage_resolution/<meeting_id>/<id> → manage_resolution
/save_resolution → save_resolution
/update_resolution_status → update_resolution_status
/record_minutes/<meeting_id> → record_minutes
/save_minutes_text/<meeting_id> → save_minutes_text
/download_minutes_pdf/<meeting_id> → download_minutes_pdf
```

**Audit & Forensics Routes**
```
/forensic_audit/<pk>/ → forensic_audit_export
/audit_highlights/<pk> → get_audit_highlights
/executive_dashboard/ → executive_dashboard
```

**AI Assistant Route**
```
/ai_assistant/ → ai_assistant
```

---

## 6. PROJECT STRUCTURE & KEY FILES

```
land_registry/                          # Main Django project
├── manage.py                           # Django CLI
├── requirements.txt                    # Dependencies
├── db.sqlite3                          # SQLite database
├── web.config                          # IIS configuration
│
├── land_registry/                      # Project config
│   ├── settings.py                     # Django settings
│   ├── urls.py                         # Root URL config
│   ├── asgi.py                         # ASGI entry point
│   ├── wsgi.py                         # WSGI entry point
│
├── registry/                           # Main app
│   ├── models.py                       # ~1,500 lines - 45+ models
│   ├── views.py                        # ~3,000+ lines - 100+ view functions
│   ├── urls.py                         # 150+ URL patterns
│   ├── forms.py                        # User registration, update forms
│   ├── admin.py                        # Django admin config
│   ├── apps.py                         # App configuration
│   ├── tests.py                        # Test suite
│   ├── middleware.py                   # ForensicAuditMiddleware
│   │
│   ├── services/                       # Service layer (15 modules)
│   │   ├── __init__.py
│   │   ├── ai_assistant.py             # AI query processing
│   │   ├── ai_assistant_enhanced.py    # Advanced NLP & intent detection
│   │   ├── automation.py               # Background tasks & alerts
│   │   ├── cloud.py                    # Digital Twin vault
│   │   ├── collaboration.py            # Real-time collaboration
│   │   ├── custody.py                  # Chain-of-custody tracking
│   │   ├── document_signer.py          # Digital signatures
│   │   ├── federation.py               # Inter-org federation
│   │   ├── governance.py               # Governance workflow
│   │   ├── intelligence.py             # AI Governor insights
│   │   ├── location.py                 # Location tracking
│   │   ├── onlyoffice_service.py       # Document editing
│   │   ├── permissions.py              # Permission checks
│   │   ├── risk.py                     # Risk scoring
│   │   ├── scanner.py                  # OCR scanning
│   │   ├── security.py                 # Encryption/decryption
│   │   ├── sla.py                      # SLA management
│   │   ├── sync.py                     # Offline sync
│   │   └── twin.py                     # Digital Twin lifecycle
│   │
│   ├── management/                     # Custom management commands
│   │   └── commands/
│   │
│   ├── migrations/                     # Database migrations
│   │
│   ├── templates/                      # 50+ HTML templates
│   │   ├── base.html                   # Master layout
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── home.html
│   │   ├── governance/                 # Governance-specific templates
│   │   │   ├── dashboard_md.html
│   │   │   ├── dashboard_hod.html
│   │   │   ├── dashboard_pm.html
│   │   │   ├── dashboard_member.html
│   │   │   └── manage_users.html
│   │   ├── files/                      # File management templates
│   │   ├── cloud/                      # Cloud vault templates
│   │   └── [other domain-specific templates]
│   │
│   ├── templatetags/                   # Custom template filters
│   │
│   ├── utils/                          # Utility modules
│   │   ├── qr_utils.py                 # QR code generation
│   │   └── intelligence.py             # AIGovernor utilities
│   │
│   ├── static/                         # CSS, JS, images
│   │
│   └── media/                          # User uploads
│       ├── brds/
│       ├── cloud_vault/
│       ├── cost_recovery_evidence/
│       ├── file_attachments/
│       ├── file_versions/
│       ├── issued_folder_zips/
│       ├── leave_documents/
│       ├── meeting_agendas/
│       ├── meeting_minutes/
│       ├── members/
│       ├── modified_files/
│       ├── project_tasks/
│       ├── qr_codes/
│       ├── scanned_docs/
│       └── [other document folders]
```

---

## 7. DEPENDENCIES (requirements.txt)

```
Django==5.2.7              # Core framework
djangorestframework        # REST API support
Pillow                     # Image processing (QR codes)
reportlab                  # PDF generation (reports, certificates)
python-docx                # DOCX file manipulation
mammoth                    # High-fidelity DOCX→HTML conversion
requests                   # HTTP client (federation, external APIs)
PyJWT                      # JWT token handling
```

---

## 8. PROJECT CONFIGURATION (settings.py highlights)

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'registry.apps.RegistryConfig',
    'rest_framework',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'registry.middleware.ForensicAuditMiddleware',  # Custom audit logging
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

---

## 9. MULTI-PLATFORM ARCHITECTURE

### Two Primary Platforms

#### A. RIFTS-X Platform (Records & Files)
- **Roles:** Clerk, Supervisor, Auditor, Executive, Portfolio Admin
- **Focus:** Physical records management, custody, digital twins
- **Portal:** Home page routes to registry operations
- **Key Models:** File, Borrow, CustodyLog, DigitalShare, CloudFile

#### B. Governance Platform (Projects & Strategy)
- **Roles:** Board of Executives, HODs, Project Management Team, Project Leader, Team Member
- **Focus:** Strategic initiatives, multi-gate approval, benefits tracking
- **Registration:** Separate `/governance/register` endpoint
- **MFA Enforced:** All Governance users must authenticate with 2FA
- **Key Models:** Project, ProjectPhase, PhaseApproval, ProjectTask, Benefit

### Inter-Platform Integration
- Shared `UserSecurity` model with platform flag
- Projects can link to physical File records
- Tasks can reference procurement (Requisition, Contract)
- Resolutions can attach file trails

---

## 10. ROLE-BASED ACCESS CONTROL (RBAC)

### Role Hierarchy (RIFTS-X)
```
Executive (highest)
  ↓ [can manage]
Supervisor
  ↓ [can manage]
Auditor (read-only specialist)
Portfolio Admin
  ↓ [manages]
Clerk (data entry)
```

### Role Hierarchy (Governance)
```
Board of Executives (strategic approval)
  ↓ [approves]
HODs (departmental approvals)
  ↓ [approves]
Project Management Team (PMT oversight)
  ↓ [approves]
Project Leader (project execution)
  ↓ [assigns & approves]
Team Member (individual contributor)
```

### Approval Workflow Example (Project Phase)
```
Team Member (task completion)
    ↓ [submits phase]
Project Leader (reviews consolidation)
    ↓ [if requires_pmt=True, escalates]
Project Management Team (operational review)
    ↓ [if requires_hods=True, escalates]
HODs (departmental verification)
    ↓ [if requires_board=True, escalates]
Board of Executives (strategic approval)
    ↓
Phase Status → Done
```

---

## 11. SECURITY FEATURES

### Authentication
- Django user system with email verification
- Multi-factor authentication (MFA) for Governance users
- Password validation (minimum length, complexity)
- Failed login attempt tracking with account locking

### Authorization
- Role-based access control (RBAC) via UserSecurity
- Board approval gates for strategic roles
- PM approval gates for Team Members
- Decorator-based view protection (`@login_required`, `@role_required`)

### Data Protection
- Field-level encryption for sensitive files (Highly Confidential)
- Role-based data masking (non-execs can't view executive-only content)
- Digital signatures on approvals and transfers
- Document versioning with user attribution

### Audit & Compliance
- ForensicAuditMiddleware logs every request (user, action, IP, user agent, method, path, payload)
- SecurityAlert model tracks suspicious activity
- CustodyLog tracks complete chain-of-custody for every file
- FileAccessLog tracks digital file interactions
- ForensicAudit tracks document downloads with clearance validation

### API Security
- CSRF protection enabled
- Cross-origin request restrictions
- SQL injection prevention (ORM parameterization)
- XSS protection via template auto-escaping

---

## 12. KEY WORKFLOWS

### File Borrowing Workflow
```
1. File Owner → Issue File
   - Create Borrow record
   - Generate access token/temporary password
   - Email to borrower
   - Create CustodyLog (Created/Issued)

2. Borrower → Access File
   - Use token to access digital twin
   - Can edit if folder_permission='edit'
   - OnlyOffice integration for live editing
   - Save modifications as FileVersion

3. Borrower → Return File
   - Submit return with borrower_signature
   - Create custody acknowledgment

4. Issuer → Confirm Return
   - Review submitted changes
   - Add issuer_signature
   - Mark return_confirmed = True
   - Archive modified versions
   - Create CustodyLog (Returned)
```

### Project Phase Gate Workflow
```
1. Team Members → Complete Tasks
   - Update task progress
   - Mark tasks Done
   - Provide evidence/artifacts

2. Team Member → Submit Phase
   - Submit phase for review
   - Provide consolidation_notes

3. Project Leader → Review
   - Add project_leader_comments
   - Approve or Reject
   - If approved, escalate based on config:
     - requires_pmt? → PMT review
     - requires_hods? → HODs review
     - requires_board? → Board review
   - If not required, mark Done

4. Each Approver → Quorum-Based Approval
   - Required count determined by phase settings
   - Collect signatures from each role
   - Once quorum met, auto-advance to next gate
   - Final Board approval → Phase Done
```

### Tender & Procurement Workflow
```
1. Department → Create Requisition
2. Budget Holder → Approve Requisition
3. Procurement → Create Tender (Open/Restricted/Direct)
4. Bidders → Submit Proposals
5. Evaluation Committee → Score Bids
6. Procurement → Award Winning Bid
7. Contract Creation → Link Tender + Bid
8. Track Milestones → Performance Evaluations
9. Completion → Archive
```

---

## 13. REPORTING & ANALYTICS

### Built-in Dashboards
- **MD Dashboard:** Institutional metrics, benefit analysis, pending board approvals
- **HOD Dashboard:** Project overview, cost recovery, team capacity
- **PM Dashboard:** Project health, task distribution, benefit tracking
- **Member Dashboard:** Personal task list, project involvement, priorities
- **Executive Dashboard:** Cross-cutting compliance view, forensic audit highlights

### Exportable Reports
- Forensic audit trail (per file)
- Asset depreciation schedule
- Meeting minutes (PDF)
- Cost recovery summary
- Project phase gate history
- Tender/bid evaluation summary

---

## 14. SYSTEM STATISTICS

- **Total Models:** 45+
- **Total View Functions:** 100+
- **Total Templates:** 50+
- **URL Patterns:** 150+
- **Service Modules:** 15+
- **Custom Middleware:** 1 (ForensicAuditMiddleware)
- **Lines of Code:** ~7,000+ (views alone)

---

## 15. INTEGRATION POINTS

### External Systems
- **OnlyOffice/LibreOffice:** Document editing (via onlyoffice_service.py)
- **Email System (SMTP):** Notifications, verification links, OTP
- **Scanner Devices:** Document ingestion via API keys
- **Federation APIs:** Inter-organizational data sharing
- **Cloud Vault:** Optional cloud storage (AWS S3, Azure, etc.)

### Internal Integrations
- Governance Platform ↔ RIFTS-X (shared UserSecurity, cross-platform approvals)
- Project Tasks → File versioning (linked_docs)
- Contracts → Asset Management (cost tracking)
- Resolutions → Knowledge Vault (institutional learning)
- Tenders → Requisitions (budget linkage)

---

## 16. DEPLOYMENT ARCHITECTURE

### Current Setup
- **Framework:** Django 5.2.7 (latest stable)
- **Database:** SQLite (development/small deployment)
- **Media Storage:** Local filesystem (`/media/`)
- **Server:** Development server or IIS (web.config provided)

### Production Considerations
- Migrate to PostgreSQL for scalability
- Use gunicorn/uWSGI WSGI server
- Implement Redis caching layer
- S3/Azure blob storage for media
- Celery for background tasks (automation.py workflows)
- Docker containerization for consistency

---

## 17. EXTENSION POINTS FOR CUSTOMIZATION

1. **Custom Validators:** Extend `models.py` with field validators
2. **Custom Decorators:** Add authorization decorators in `views.py`
3. **Custom Services:** Add modules to `registry/services/`
4. **Custom Reports:** Add export formats in reporting utilities
5. **Custom Workflows:** Extend `governance.py` approval logic
6. **Custom Notifications:** Extend email templates and messaging
7. **Custom Metrics:** Add model methods for analytics
8. **Custom Integrations:** Add service clients in `services/`

---

## Summary

RIFTS-X is a **comprehensive, multi-faceted enterprise system** that seamlessly integrates:
- **Records Management** with custody tracking and digital twins
- **Project Governance** with configurable multi-tier approval workflows
- **Financial Stewardship** with budgets, requisitions, and cost recovery
- **Institutional Knowledge** with versioned policy documentation
- **Compliance & Audit** with forensic logging and role-based masking
- **Procurement Lifecycle** from tender to contract completion
- **HR & Administrative** functions (leave, approvals, announcements)
- **AI-Assisted Intelligence** for pattern recognition and automation

The architecture is **modular, scalable, and auditable**, designed for large governmental or institutional deployments requiring strict compliance, transparency, and accountability.

