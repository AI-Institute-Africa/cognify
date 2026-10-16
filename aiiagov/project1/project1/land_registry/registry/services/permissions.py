import logging
from registry.models import UserSecurity

logger = logging.getLogger(__name__)

# Role tiers for quick checks
ADMIN_ROLES      = {'Portfolio Admin'}
PM_ROLES         = {'Portfolio Admin', 'Project Leader', 'Board of Executives', 'HODs', 'Project Management Team', 'MD'}
EXEC_ROLES       = {'Portfolio Admin', 'Board of Executives', 'Executive Viewer', 'Auditor', 'MD'}
DEPT_HEAD_ROLES  = {'Portfolio Admin', 'Board of Executives', 'Project Management Team', 'HODs', 'Executive Viewer', 'MD'}
FINANCIAL_ROLES  = {'Portfolio Admin', 'Board of Executives', 'Executive Viewer', 'Project Management Team', 'HODs', 'Auditor', 'Team Member', 'Project Leader', 'MD'}


class PermissionService:

    # ── Core Role Resolution ──────────────────────────────────────────────────

    @staticmethod
    def get_user_role(user):
        if user.is_superuser:
            return 'Portfolio Admin'
        try:
            return user.security_profile.role
        except Exception:
            return 'Team Member'

    @staticmethod
    def is_team_member_only(user):
        """True if the user has NO elevated governance role."""
        role = PermissionService.get_user_role(user)
        return role == 'Team Member'

    @staticmethod
    def is_pm_or_above(user):
        role = PermissionService.get_user_role(user)
        return role in PM_ROLES

    @staticmethod
    def is_exec_or_above(user):
        role = PermissionService.get_user_role(user)
        return role in EXEC_ROLES

    @staticmethod
    def is_hod(user):
        role = PermissionService.get_user_role(user)
        return role in ('Project Management Team', 'HODs')

    @staticmethod
    def is_md(user):
        role = PermissionService.get_user_role(user)
        return role in ['Board of Executives', 'MD']

    # ── Project Visibility ────────────────────────────────────────────────────

    @staticmethod
    def can_create_project(user):
        """Admins and Board can initiate new projects."""
        role = PermissionService.get_user_role(user)
        return role in {'Portfolio Admin', 'Board of Executives', 'Project Leader'}

    @staticmethod
    def can_view_org_dashboard(user):
        """Board and Admins see the org-wide executive dashboard."""
        role = PermissionService.get_user_role(user)
        return role in EXEC_ROLES

    @staticmethod
    def can_view_dept_projects(user):
        """PMT/HODs and above can see all departmental projects."""
        role = PermissionService.get_user_role(user)
        return role in DEPT_HEAD_ROLES

    # ── Phase & Sprint ────────────────────────────────────────────────────────

    @staticmethod
    def can_approve_phase(user, phase):
        role = PermissionService.get_user_role(user)
        if role == 'Portfolio Admin':
            return True
        if role == 'Project Leader':
            return phase.pm == user or phase.project.owner == user
        return False

    @staticmethod
    def can_manage_sprint(user, sprint):
        role = PermissionService.get_user_role(user)
        if role == 'Portfolio Admin':
            return True
        if role == 'Project Leader':
            return sprint.phase.pm == user or sprint.phase.project.owner == user
        return False

    @staticmethod
    def can_close_sprint(user, sprint):
        """Only PL (of that sprint) or Admin can close a sprint."""
        return PermissionService.can_manage_sprint(user, sprint)

    # ── Task ─────────────────────────────────────────────────────────────────

    @staticmethod
    def can_edit_task(user, task):
        role = PermissionService.get_user_role(user)
        if role in PM_ROLES:
            return True
        if role == 'Team Member':
            return task.owner == user
        return False

    @staticmethod
    def can_approve_task(user, task):
        """PLs and admins can mark a task as officially approved/verified."""
        role = PermissionService.get_user_role(user)
        if role in PM_ROLES:
            return True
        return False

    @staticmethod
    def can_reassign_task(user, task=None):
        """Only PL and Admin can reassign a task to another user."""
        role = PermissionService.get_user_role(user)
        return role in PM_ROLES

    # ── Financial Visibility ──────────────────────────────────────────────────

    @staticmethod
    def can_view_financials(user, project=None):
        role = PermissionService.get_user_role(user)
        return role in FINANCIAL_ROLES

    # ── Commenting ───────────────────────────────────────────────────────────

    @staticmethod
    def can_post_comment(user):
        return user.is_authenticated

    @staticmethod
    def is_approved_member(user, project):
        """Check if user is a PM/Admin OR an approved member of the specific project."""
        role = PermissionService.get_user_role(user)
        if role in PM_ROLES:
            return True
        from registry.models import ProjectMember
        return ProjectMember.objects.filter(project=project, user=user, is_approved=True).exists()

    # ── Convenience: full context dict for a user ─────────────────────────────

    @staticmethod
    def build_context(user, task=None, sprint=None, phase=None):
        """Return a dict of all permission flags suitable for template context."""
        ctx = {
            'user_role': PermissionService.get_user_role(user),
            'can_create_project': PermissionService.can_create_project(user),
            'can_view_financials': PermissionService.can_view_financials(user),
            'can_post_comment': PermissionService.can_post_comment(user),
            'can_view_org_dashboard': PermissionService.can_view_org_dashboard(user),
            'can_view_dept_projects': PermissionService.can_view_dept_projects(user),
            'can_reassign_task': PermissionService.can_reassign_task(user),
            'is_team_member_only': PermissionService.is_team_member_only(user),
        }
        if task:
            ctx['can_edit_task'] = PermissionService.can_edit_task(user, task)
            ctx['can_approve_task'] = PermissionService.can_approve_task(user, task)
        if sprint:
            ctx['can_close_sprint'] = PermissionService.can_close_sprint(user, sprint)
            ctx['can_manage_sprint'] = PermissionService.can_manage_sprint(user, sprint)
        if phase:
            ctx['can_approve_phase'] = PermissionService.can_approve_phase(user, phase)
        return ctx

    # ── ZRP Document Movement & Operation Permissions ────────────────────────

    @staticmethod
    def is_registry_officer_or_admin(user):
        if user.is_superuser:
            return True
        role = (getattr(user, 'security_profile', None) and user.security_profile.role or '').lower()
        return any(r in role for r in ['admin', 'registry', 'archivist', 'records', 'manager', 'director', 'executive'])

    @staticmethod
    def can_create_folder(user):
        return PermissionService.is_registry_officer_or_admin(user)

    @staticmethod
    def can_upload_file(user):
        return user.is_authenticated

    @staticmethod
    def can_move_file(user, file_obj=None):
        return PermissionService.is_registry_officer_or_admin(user)

    @staticmethod
    def can_rename_file(user, file_obj=None):
        return user.is_authenticated

    @staticmethod
    def can_delete_file(user, file_obj=None):
        if user.is_superuser:
            return True
        role = (getattr(user, 'security_profile', None) and user.security_profile.role or '').lower()
        return 'admin' in role or 'director' in role or 'executive' in role

    @staticmethod
    def can_archive_file(user, file_obj=None):
        return PermissionService.is_registry_officer_or_admin(user)

    @staticmethod
    def can_restore_file(user, file_obj=None):
        return PermissionService.is_registry_officer_or_admin(user)

    @staticmethod
    def can_access_classified_file(user, file_obj):
        """
        Open Access: Anyone
        Departmental: Users in department or registry/admin
        Confidential: Designated department staff/managers/directors
        Restricted/Highly Confidential: Registry Officers, Directors, Executives, Superusers
        """
        if user.is_superuser:
            return True
        classification = getattr(file_obj, 'classification_level', 'Departmental') or getattr(file_obj, 'sensitivity_level', 'Normal')
        
        if classification == 'Open Access':
            return True
        
        role = (getattr(user, 'security_profile', None) and user.security_profile.role or '').lower()
        if any(r in role for r in ['admin', 'executive', 'director', 'chief']):
            return True

        if classification == 'Departmental':
            # Check user department match
            user_dept = getattr(user, 'borrower_profile', None) and user.borrower_profile.department
            file_dept = getattr(file_obj, 'current_department', None) or (getattr(file_obj, 'folder', None) and file_obj.folder.department)
            if user_dept and file_dept and user_dept == file_dept:
                return True
            return PermissionService.is_registry_officer_or_admin(user)

        if classification in ['Confidential', 'Restricted/Highly Confidential']:
            return any(r in role for r in ['admin', 'executive', 'director', 'manager', 'registry'])

        return True

    @staticmethod
    def can_approve_document(user, workflow=None):
        if user.is_superuser:
            return True
        if workflow:
            status = workflow.current_status
            if status == 'Submitted' and workflow.reviewer == user: return True
            if status == 'Reviewed' and workflow.recommender == user: return True
            if status == 'Recommended' and workflow.approver == user: return True
        return PermissionService.is_pm_or_above(user)

