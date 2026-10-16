# RIFTS-X Quick Reference Guide

## 🚀 Getting Started

### Core Entry Points by Role

**RIFTS-X Records Management:**
- **Clerk:** `/home` → File management, borrowing operations
- **Supervisor:** `/home` → User management, category configuration
- **Auditor:** `/home` → Forensic audit review, compliance reports
- **Executive:** `/home` → Executive dashboard, executive-only views

**Governance Platform:**
- **Board of Executives:** `/dashboard/md` → Strategic oversight, phase approvals
- **HODs:** `/dashboard/hod` → Departmental project oversight
- **Project Leader:** `/dashboard/pm` → Project operations, team management
- **Team Member:** `/dashboard/member` → Personal task dashboard
- **Registration:** `/governance/register` (2FA required after email verification)

---

## 📂 Key Model Categories

### Records & Files
```
File ←→ SubCategory ←→ Category
         │
         ├── FileVersion (historical versions)
         ├── Folio (grouping)
         ├── FileLocation (physical location)
         ├── QR Code (tracking)
         └── CloudFile/CloudFileVersion (digital twin)
```

### Borrowing Pipeline
```
Borrower (user profile)
   ↓
Borrow (transaction)
   ├── CustodyLog (chain of custody)
   ├── FileVersion (modified copies)
   ├── DigitalShare (temporary access tokens)
   └── SecureLink (time-limited links)
```

### Governance Gate Structure
```
Project
   ├── ProjectPhase (gate checkpoint)
   │   ├── PhaseApproval (role-based approvals)
   │   ├── ProjectTask (work items)
   │   │   ├── TaskAttachment (evidence)
   │   │   └── ProjectSprint (agile sprint)
   │   └── ProjectMember (team assignment)
   └── Benefit (realized outcomes)
```

### Financial Spine
```
Budget (fiscal year allocation)
   ├── Requisition (item request)
   │   ├── Expenditure (payment record)
   │   └── CostRecovery (savings tracking)
   └── Tender (procurement notice)
       ├── Bid (vendor proposal)
       └── Contract (awarded agreement)
           ├── ContractMilestone
           └── PerformanceEvaluation
```

### Security Layer
```
User
   └── UserSecurity (role profile)
       ├── SecurityAlert (incidents)
       ├── ForensicAudit (request logs)
       └── LeaveRequest/LeaveRequestApproval
```

---

## 🔗 Most-Used Routes

### File Operations
| Task | Route | Method |
|------|-------|--------|
| Browse files | `/files/` | GET |
| Create file | `/manage_file_doc` | GET (form) |
| Save file | `/save_file_doc` | POST |
| View file detail | `/view_file_doc/<id>` | GET |
| Download version | `/download_version/<id>` | GET (secure) |
| Delete file | `/delete_file_doc/<id>` | POST |

### Borrowing
| Task | Route | Method |
|------|-------|--------|
| Issue file | `/manage_borrow` | GET (form) |
| Create borrow record | `/save_borrow` | POST |
| Track active borrows | `/borrows` | GET |
| Borrower dashboard | `/my_dashboard` | GET |
| Confirm return | `/confirm_borrow_return/<id>` | POST |

### Digital Sharing
| Task | Route | Method |
|------|-------|--------|
| Create secure link | `/secure_link/generate/<id>` | POST |
| Verify link | `/secure_link/verify/<token>` | GET |
| Share with user | `/share_file_digital/<id>` | POST |
| Recipient view | `/verify_digital_share/<token>` | GET |

### Governance Projects
| Task | Route | Method |
|------|-------|--------|
| View board dashboard | `/dashboard/md` | GET |
| View HOD dashboard | `/dashboard/hod` | GET |
| Manage team members | `/governance/pm/members/` | GET |
| Approve phase gate | `/dashboard/pm` | GET (view pending) |

### Leave Management
| Task | Route | Method |
|------|-------|--------|
| Browse leaves | `/leaves` | GET |
| Request leave | `/manage_leave` | GET (form) |
| Submit leave | `/save_leave` | POST |
| Approver panel | `/leave_applications` | GET |
| Approve leave | `/approve_leave` | POST |

### Financial
| Task | Route | Method |
|------|-------|--------|
| Create requisition | `/manage_requisition` | GET (form) |
| Submit requisition | `/save_requisition` | POST |
| View requisitions | `/requisition_list` | GET |
| Approve requisition | `/approve_requisition` | POST |
| Financial dashboard | `/financial/dashboard/` | GET |

---

## 🛡️ Security Quick Tips

### Access Control
- **Always use:** `@login_required` decorator on protected views
- **Sensitive files:** Use `@role_required(['Executive'])` decorator
- **Borrowers only:** Use `@user_is_not_borrower` decorator

### Data Protection
- Files with `sensitivity_level='Highly Confidential'` are auto-encrypted
- Non-executives see `[CONFIDENTIAL - MASKED]` if they lack clearance
- All downloads trigger ForensicAudit logging
- Unauthorized access attempts create SecurityAlert records

### Approval Workflows
- Board must approve **strategic roles** (Board, HODs, PMT, PL)
- PL must approve **Team Member** registrations
- Email verification required before platform access
- 2FA (OTP via email) required for Governance users

---

## 📊 Service Layer Quick Map

### User Queries
- **AI Query?** → `ai_assistant_enhanced.py:process_intelligent_query()`
- **Permission Check?** → `permissions.py:PermissionService.can_do_X()`
- **Risk Score?** → `risk.py:RiskEngine.score_file()`
- **Location Info?** → `location.py:LocationIntelligence.get_last_known_location()`

### File Operations
- **Encrypt Field?** → `security.py:EncryptionService.encrypt()`
- **Generate QR?** → `utils/qr_utils.py:generate_file_qr()`
- **Create Digital Twin?** → `twin.py:DigitalTwinService.instantiate_twin()`
- **Track Custody?** → `custody.py:CustodyService.record_creation()`

### Governance
- **Evaluate Phase?** → `governance.py:GovernanceService.evaluate_phase_gate()`
- **Calculate Metrics?** → `governance.py:GovernanceService.calculate_institutional_metrics()`
- **Detect Intent?** → `ai_assistant_enhanced.py:detect_intent()`
- **Extract Entities?** → `ai_assistant_enhanced.py:extract_entities()`

### Integrations
- **OnlyOffice Config?** → `onlyoffice_service.py:OnlyOfficeService.prepare_config()`
- **Scan Document?** → `scanner.py:ScannerService.process_scan()`
- **Cloud Sync?** → `cloud.py:CloudService.sync_file()`
- **Background Task?** → `automation.py:Automation.schedule_task()`

---

## 🎯 Common Task Patterns

### Creating a New File Record
```python
# 1. Create File instance
file = File.objects.create(
    sub_category=subcategory,
    ref_num="DOC-2024-001",
    title="Important Document",
    sensitivity_level='Normal'  # or 'Sensitive' or 'Highly Confidential'
)

# 2. Signal fires automatically:
#    - QR code generated (via @receiver post_save)
#    - Digital Twin created (via DigitalTwinService)
#    - CustodyLog recorded (creation event)
```

### Issuing a File to Borrower
```python
# 1. Create Borrow record
borrow = Borrow.objects.create(
    borrower=borrower,
    file_doc=file,
    borrowing_date=today,
    return_date=today + timedelta(days=7),
    status='0'  # Issued
)

# 2. Generate access token
import secrets
token = secrets.token_urlsafe(32)
secure_link = SecureLink.objects.create(
    file_doc=file,
    token=token,
    expires_at=timezone.now() + timedelta(hours=72)
)

# 3. Send email with token
send_mail(
    f"File Issued: {file.ref_num}",
    f"Access link: /verify_digital_share/{token}",
    settings.DEFAULT_FROM_EMAIL,
    [borrower.user.email]
)
```

### Tracking File Movement
```python
# Every handover/transfer creates a CustodyLog
log = CustodyLog.objects.create(
    file_doc=file,
    handler=request.user,
    from_department=old_dept,
    to_department=new_dept,
    action="Transfer",  # or 'Handover', 'Created', 'Archived'
    reason="Departmental reorganization",
    timestamp=timezone.now()
)

# Chain of custody visible via file_timeline view
# /file_timeline/<file_id>/
```

### Submitting a Project Phase
```python
# 1. Tasks must be marked Done
tasks = ProjectTask.objects.filter(phase=phase, status__in=['To Do', 'In Progress'])
# All tasks should be Done or moved to next phase

# 2. Phase submission
phase.status = 'Review'
phase.submitted_at = timezone.now()
phase.consolidation_notes = "Summary of accomplishments..."
phase.save()

# 3. PM/HODs/Board automatically notified based on project settings
# Next step: Project Leader review → PMT/HODs/Board approval
```

### Approving a Leave Request
```python
# 1. Approver views pending leaves
pending = LeaveRequest.objects.filter(status='Pending')

# 2. Create approval record
approval = LeaveRequestApproval.objects.create(
    leave_request=leave,
    approver=request.user,
    status='Approved',  # or 'Rejected'
    comment="Approved - cover arranged",
    signature_data=base64_signature
)

# 3. Update leave status if quorum met
if leave.approvals.filter(status='Approved').count() >= 2:
    leave.status = 'Approved'
    leave.approved_by = request.user
    leave.save()
```

---

## 🔍 Debugging Common Issues

### Issue: File not visible to user
**Check:**
1. Is `delete_flag = 0`? (Soft deleted files hidden)
2. Is sensitivity level too high? (Run `mask_sensitive_data()`)
3. Does user have department access?
4. Is user role sufficient? (`@role_required(['Supervisor', 'Executive']`)

**Fix:**
```python
# View all files including masked
files = File.objects.filter(delete_flag=0)
for f in files:
    f = mask_sensitive_data(f, request.user)  # Apply masking
    print(f.title)  # May show [CONFIDENTIAL - MASKED]
```

### Issue: Borrow confirmation not working
**Check:**
1. Is `return_confirmed = False`?
2. Has borrower submitted `borrower_signature`?
3. Is issuer role 'Supervisor' or higher?
4. Is borrow status still '0' (Issued)?

**Fix:**
```python
# Manually confirm return
borrow = Borrow.objects.get(id=borrow_id)
borrow.return_confirmed = True
borrow.confirmed_by = request.user
borrow.confirmed_at = timezone.now()
borrow.status = '1'  # Returned
borrow.save()
```

### Issue: Phase stuck in "Review" status
**Check:**
1. Are all task statuses 'Done'?
2. Is `consolidation_notes` provided?
3. Is PM assigned to phase?
4. Has PM approved the phase?

**Fix:**
```python
# Force phase advance (admin only)
phase.status = 'Awaiting PMT Approval' if project.requires_pmt else 'Done'
phase.approved_at = timezone.now()
phase.save()
```

### Issue: User can't login (email not verified)
**Check:**
1. Is `is_email_verified = False` in UserSecurity?
2. Does verification token exist?
3. Has user clicked email link?

**Fix (Admin):**
```python
# Manually verify email (console output)
security = UserSecurity.objects.get(user_id=user_id)
security.is_email_verified = True
security.save()

# Or print verification link to console
token = security.email_verification_token
print(f"Verification link: /verify-email/{token}")
```

---

## 📈 Performance Optimization Tips

### Database Queries
```python
# ❌ Bad: N+1 queries
files = File.objects.all()
for f in files:
    print(f.sub_category.category.name)  # Extra query each loop

# ✅ Good: Use select_related
files = File.objects.select_related('sub_category', 'sub_category__category')
for f in files:
    print(f.sub_category.category.name)  # Single query

# ✅ Also good: Use prefetch_related for ManyToMany
tasks = ProjectTask.objects.prefetch_related('dependencies')
```

### Caching
```python
# Cache sensitive data masking
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # 15 minutes
@login_required
def files(request):
    # This view will be cached per user
    pass
```

### Indexing
```python
# Add index to frequently queried fields
class File(models.Model):
    ref_num = models.CharField(max_length=250, db_index=True)
    status = models.CharField(max_length=10, db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['delete_flag', 'status']),
        ]
```

---

## 📚 Reference: Model Relationships

```
Organization (1) ─→ (∞) FederationLink ←─ (1) Organization
Organization (1) ─→ (∞) Department
Department (1) ─→ (∞) File
Department (1) ─→ (∞) Borrower
Department (1) ─→ (∞) Project
Department (1) ─→ (∞) Budget

User (1) ─→ (1) UserSecurity
User (1) ─→ (∞) LeaveRequest
User (1) ─→ (∞) Requisition
User (1) ─→ (∞) File (as last_handler)

Category (1) ─→ (∞) SubCategory
SubCategory (1) ─→ (∞) File
File (1) ─→ (∞) FileVersion
File (1) ─→ (∞) CustodyLog
File (1) ─→ (∞) DigitalShare
File (1) ─→ (1) FileLocation

Borrower (1) ─→ (∞) Borrow
File (1) ─→ (∞) Borrow

Project (1) ─→ (∞) ProjectPhase
ProjectPhase (1) ─→ (∞) ProjectTask
ProjectTask (1) ─→ (∞) TaskAttachment
ProjectPhase (1) ─→ (∞) PhaseApproval
ProjectPhase (1) ─→ (∞) ProjectSprint
ProjectSprint (1) ─→ (∞) ProjectTask

Tender (1) ─→ (∞) Bid
Bid (1) ←→ (1) Contract
Contract (1) ─→ (∞) ContractMilestone
Contract (1) ─→ (∞) PerformanceEvaluation

Budget (1) ─→ (∞) Requisition
Requisition (1) ←→ (1) Expenditure
Requisition (1) ─→ (∞) CostRecovery

Meeting (1) ─→ (∞) Resolution
```

---

## 🎓 Learning Path

1. **Start Here:** `RIFTS-X_ARCHITECTURE_OVERVIEW.md` (this document's companion)
2. **Understand Models:** Read `registry/models.py` (organized by section comments)
3. **Explore Routes:** Study `registry/urls.py` (150+ patterns, well-organized)
4. **Trace Workflows:** Follow a complete user journey through `views.py`
5. **Deep Dive Services:** Pick a service module, e.g., `governance.py`
6. **Study Templates:** Review base.html → domain-specific templates
7. **Security Review:** Examine middleware.py, ForensicAuditMiddleware
8. **Integration Study:** Check onlyoffice_service.py, federation.py

---

## 🚨 Critical Security Checklist

- [ ] Change `SECRET_KEY` in production settings.py
- [ ] Set `DEBUG = False` in production
- [ ] Configure `ALLOWED_HOSTS` with actual domains
- [ ] Set up HTTPS/SSL certificates
- [ ] Configure SMTP server for email (registration verification)
- [ ] Set environment variables for sensitive config
- [ ] Enable database backups and versioning
- [ ] Configure rate limiting on login attempts
- [ ] Review and update `MIDDLEWARE` for production
- [ ] Test MFA flow before deployment
- [ ] Audit all custom decorators and permission checks
- [ ] Monitor ForensicAudit logs regularly

---

## 📞 Support

For detailed information on specific components:
- **Models:** See `1. DATABASE MODELS` in RIFTS-X_ARCHITECTURE_OVERVIEW.md
- **Views:** See `2. VIEW FUNCTIONS` in RIFTS-X_ARCHITECTURE_OVERVIEW.md
- **Services:** See `3. SERVICE LAYER` in RIFTS-X_ARCHITECTURE_OVERVIEW.md
- **Templates:** See `4. TEMPLATE HIERARCHY` in RIFTS-X_ARCHITECTURE_OVERVIEW.md
- **Routes:** See `5. URL ROUTING PATTERNS` in RIFTS-X_ARCHITECTURE_OVERVIEW.md
- **Security:** See `11. SECURITY FEATURES` in RIFTS-X_ARCHITECTURE_OVERVIEW.md

---

**Last Updated:** 2026-06-12  
**System Version:** RIFTS-X Multi-Platform  
**Framework:** Django 5.2.7  
