import logging
from django.utils import timezone
from django.db import transaction
from django.core.mail import EmailMessage
from django.conf import settings
from registry.models import Project, ProjectPhase, ProjectTask, ProjectLog, ProjectAlert, PhaseApproval

logger = logging.getLogger(__name__)

class GovernanceService:
    @staticmethod
    def initialize_stage_gates(project, pm=None):
        """
        Creates the 5 standard phases for a new project with detailed deliverables and criteria.
        """
        phases_config = [
            {
                'name': 'Initiation',
                'deliverables': '- Project Charter (Signed)\n- Stakeholder Identification Map\n- Governance Setup',
                'criteria': 'Institutional approval of project charter and formal stakeholder sign-off.'
            },
            {
                'name': 'Planning',
                'deliverables': '- Comprehensive Project Plan\n- Risk Mitigation Registry\n- Resource Allocation Sheet',
                'criteria': 'PMO review of project timeline and resource commitment finalization.'
            },
            {
                'name': 'Execution',
                'deliverables': '- Weekly Status Reports\n- Quality Assurance Logs\n- Deliverable Artifacts',
                'criteria': 'Minimum 95% task completion rate and successful QA verification.'
            },
            {
                'name': 'Monitoring & Control',
                'deliverables': '- Performance Metric Dashboard\n- Mid-stage Audit Report\n- Change Control Logs',
                'criteria': 'Verification of KPIs against baselines and formal change review.'
            },
            {
                'name': 'Closure',
                'deliverables': '- Final Project Report\n- Lessons Learned Repository\n- Handover Documentation',
                'criteria': 'Complete asset transition and formal project closure sign-off.'
            }
        ]
        
        created_phases = []
        for idx, cfg in enumerate(phases_config):
            phase = ProjectPhase.objects.create(
                project=project,
                name=cfg['name'],
                sequence=idx + 1,
                status='Active' if idx == 0 else 'Pending',
                pm=pm or project.owner,
                deliverables=cfg['deliverables'],
                completion_criteria=cfg['criteria'],
                requires_approval=True
            )
            created_phases.append(phase)
            
        ProjectLog.objects.create(
            project=project,
            user=project.owner,
            message=f"Project '{project.name}' initialized with Full Stage-Gate Governance (5 Phases)."
        )
        return created_phases

    @staticmethod
    def advance_phase(phase, user):
        """
        Strictly moves a phase to 'Awaiting Approval' if all tasks and deliverables are verified.
        """
        try:
            with transaction.atomic():
                # 1. Task Completion Check (100% Strict)
                pending_tasks = phase.tasks.exclude(status='Done').count()
                if pending_tasks > 0:
                    msg = f"Gate Locked: Phase '{phase.name}' has {pending_tasks} incomplete tasks."
                    ProjectAlert.objects.create(
                        project=phase.project, phase=phase,
                        alert_type='PhaseCriteria', message=msg
                    )
                    return False, msg

                # 2. Deliverable Verification (File/Link Check)
                doc_count = phase.required_documents.count()
                task_attachment_count = phase.tasks.filter(attachments__isnull=False).distinct().count()
                
                if doc_count == 0 and task_attachment_count == 0:
                    msg = f"Gate Locked: No deliverable documents or task attachments found for Phase '{phase.name}'. Please upload required evidence or complete tasks with attachments."
                    ProjectAlert.objects.create(
                        project=phase.project, phase=phase,
                        alert_type='PhaseCriteria', message=msg
                    )
                    return False, msg

                if phase.status in ('Awaiting Team Member Approval', 'Awaiting Project Leader Approval', 'Awaiting PMT Approval', 'Awaiting HODs Approval', 'Awaiting Board Approval'):
                    return False, "This phase is already in the higher governance review chain."

                # Update status to Review for PL Gate Mastery
                phase.status = 'Awaiting Team Member Approval'
                phase.save()

                return True, "All tasks complete. Phase forwarded for Team Member peer approval."
        except Exception as e:
            return False, str(e)


    @staticmethod
    def team_member_submit_to_pl(phase, user, comments="", signature_data=None):
        """Team Member approves the phase and forwards to Project Leader."""
        from registry.models import UserSecurity
        user_sec = UserSecurity.objects.filter(user=user).first()
        is_pm = phase.pm == user
        allowed_roles = ['Team Member', 'Project Leader', 'Portfolio Admin', 'MD']
        
        if not (user_sec and user_sec.role in allowed_roles) and not user.is_superuser and not is_pm:
            return False, "Only a Team Member or Project Leader can perform this initial phase submission."

        with transaction.atomic():
            approval, created = PhaseApproval.objects.get_or_create(
                phase=phase, 
                approver=user, 
                role='Team Member',
                defaults={'comment': comments, 'signature_data': signature_data}
            )
            if not created:
                if signature_data:
                    approval.signature_data = signature_data
                    approval.comment = comments
                    approval.save()
                else:
                    return False, "You have already approved this phase."

            phase.status = 'Awaiting Project Leader Approval'
            all_comments = "\n".join([f"{a.approver.username}: {a.comment}" for a in phase.approvals.filter(role='Team Member')])
            phase.team_member_comments = all_comments
            phase.save()
            
            if is_pm:
                msg = f"Phase '{phase.name}' peer-approved by {user.username} (Project Leader). Ready for Consolidation."
            else:
                msg = f"Phase '{phase.name}' peer-approved by {user.username}. Forwarded to Project Leader."
            
            ProjectLog.objects.create(project=phase.project, user=user, message=msg)
            
            # Notify PL
            GovernanceService.send_gate_review_notification(phase, ['Project Leader'])
        return True, msg


    @staticmethod
    def pl_submit_to_pmt(phase, user, comments="", signature_data=None):
        """Project Leader approves and forwards to the next enabled gate (PMT, HODs, Board, or Done)."""
        from registry.models import UserSecurity
        user_sec = UserSecurity.objects.filter(user=user).first()
        if not (user_sec and user_sec.role == 'Project Leader') and not user.is_superuser and phase.pm != user:
            return False, "Only the Project Leader can approve this phase."

        incomplete = phase.tasks.exclude(status='Done').count()
        if incomplete > 0:
            return False, f"Cannot consolidate: {incomplete} tasks are not yet completed."

        with transaction.atomic():
            approval, created = PhaseApproval.objects.get_or_create(
                phase=phase,
                approver=user,
                role='Project Leader',
                defaults={'comment': comments, 'signature_data': signature_data}
            )
            if not created:
                if signature_data:
                    approval.signature_data = signature_data
                    approval.comment = comments
                    approval.save()
                else:
                    return False, "You have already approved this phase."

            phase.consolidation_notes = comments
            all_comments = "\\n".join([f"{a.approver.username}: {a.comment}" for a in phase.approvals.filter(role='Project Leader')])
            phase.project_leader_comments = all_comments
            phase.submitted_at = timezone.now()

            # ── Route to next ENABLED gate ──
            project = phase.project
            if project.requires_pmt:
                phase.status = 'Awaiting PMT Approval'
                phase.save()
                GovernanceService.send_gate_review_notification(phase, ['Project Management Team'])
                msg = f"Phase '{phase.name}' approved by PL {user.username} and forwarded to PMT."
            elif project.requires_hods:
                phase.status = 'Awaiting HODs Approval'
                phase.save()
                GovernanceService.send_gate_review_notification(phase, ['HODs'])
                msg = f"Phase '{phase.name}' approved by PL {user.username}. PMT skipped — forwarded to HODs."
            elif project.requires_board:
                phase.status = 'Awaiting Board Approval'
                phase.save()
                GovernanceService.send_gate_review_notification(phase, ['Board of Executives'])
                msg = f"Phase '{phase.name}' approved by PL {user.username}. PMT + HODs skipped — forwarded to Board."
            else:
                phase.status = 'Done'
                phase.approved_at = timezone.now()
                phase.save()
                msg = f"Phase '{phase.name}' approved and closed by PL {user.username}. All upper gates disabled for this project."

            ProjectLog.objects.create(project=phase.project, user=user, message=msg)

        return True, msg

    @staticmethod
    def pmt_submit_to_hods(phase, user, comments="", signature_data=None):
        """Records a PMT approval. When quorum is met, routes to the next ENABLED gate (HODs, Board, or Done)."""
        from registry.models import UserSecurity
        user_sec = UserSecurity.objects.filter(user=user).first()
        if not (user_sec and user_sec.role == 'Project Management Team') and not user.is_superuser:
            return False, "Only a Project Management Team member can verify this phase."

        with transaction.atomic():
            approval, created = PhaseApproval.objects.get_or_create(
                phase=phase,
                approver=user,
                role='Project Management Team',
                defaults={'comment': comments, 'signature_data': signature_data}
            )
            if not created:
                if signature_data:
                    approval.signature_data = signature_data
                    approval.comment = comments
                    approval.save()
                else:
                    return False, "You have already approved this phase."

            approval_count = phase.approvals.filter(role='Project Management Team').count()
            required = phase.pmt_required or 1
            msg = f"Phase '{phase.name}' verified by PMT {user.username} ({approval_count}/{required})."

            if approval_count >= required:
                all_comments = "\n".join([f"{a.approver.username}: {a.comment}" for a in phase.approvals.filter(role='Project Management Team')])
                phase.pmt_comments = all_comments

                # ── Route to next ENABLED gate ──
                project = phase.project
                if project.requires_hods:
                    phase.status = 'Awaiting HODs Approval'
                    phase.save()
                    GovernanceService.send_gate_review_notification(phase, ['HODs'])
                    msg += " Quorum reached. Forwarded to HODs approval."
                elif project.requires_board:
                    phase.status = 'Awaiting Board Approval'
                    phase.save()
                    GovernanceService.send_gate_review_notification(phase, ['Board of Executives'])
                    msg += " Quorum reached. HODs skipped — forwarded to Board."
                else:
                    phase.status = 'Done'
                    phase.approved_at = timezone.now()
                    phase.save()
                    msg += " Quorum reached. HODs + Board skipped — phase closed."
            else:
                phase.save()

            ProjectLog.objects.create(project=phase.project, user=user, message=msg)

            try:
                confirm_subject = f"Action Recorded: Phase Approval - {phase.project.name}"
                confirm_body = f"Hello {user.username},\n\nYou have Approved Phase '{phase.name}' for Project '{phase.project.name}'.\n\nSystem URL: {settings.GOVERNANCE_BASE_URL}\n\nBest regards,\nRIFTS-X Governance"
                confirm_email = EmailMessage(
                    subject=confirm_subject,
                    body=confirm_body,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'governance@registry.gov'),
                    to=[user.email]
                )
                confirm_email.send(fail_silently=True)
            except Exception as e:
                logger.error(f"Failed to send PMT confirmation email: {e}")

        return True, msg

    @staticmethod
    def hods_submit_to_board(phase, user, comments="", signature_data=None):
        """Records HODs approval. When quorum is met, routes to Board (if enabled) or closes the phase."""
        from registry.models import UserSecurity
        user_sec = UserSecurity.objects.filter(user=user).first()
        if not (user_sec and user_sec.role == 'HODs') and not user.is_superuser:
            return False, "Only a Head of Departments can verify this phase."

        with transaction.atomic():
            approval, created = PhaseApproval.objects.get_or_create(
                phase=phase,
                approver=user,
                role='HODs',
                defaults={'comment': comments, 'signature_data': signature_data}
            )
            if not created:
                if signature_data:
                    approval.signature_data = signature_data
                    approval.comment = comments
                    approval.save()
                else:
                    return False, "You have already approved this phase."

            approval_count = phase.approvals.filter(role='HODs').count()
            required = phase.hods_required or 1
            msg = f"Phase '{phase.name}' verified by HODs {user.username} ({approval_count}/{required})."

            if approval_count >= required:
                all_comments = "\n".join([f"{a.approver.username}: {a.comment}" for a in phase.approvals.filter(role='HODs')])
                phase.hods_comments = all_comments

                # ── Route to next ENABLED gate ──
                if phase.project.requires_board:
                    phase.status = 'Awaiting Board Approval'
                    phase.save()
                    GovernanceService.send_gate_review_notification(phase, ['Board of Executives'])
                    msg += " Quorum reached. Forwarded to Board approval."
                else:
                    phase.status = 'Done'
                    phase.approved_at = timezone.now()
                    phase.save()
                    msg += " Quorum reached. Board skipped — phase closed."
            else:
                phase.save()

            ProjectLog.objects.create(project=phase.project, user=user, message=msg)

            try:
                confirm_subject = f"Action Recorded: Phase Approval - {phase.project.name}"
                confirm_body = f"Hello {user.username},\n\nYou have Approved Phase '{phase.name}' for Project '{phase.project.name}'.\n\nSystem URL: {settings.GOVERNANCE_BASE_URL}\n\nBest regards,\nRIFTS-X Governance"
                confirm_email = EmailMessage(
                    subject=confirm_subject,
                    body=confirm_body,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'governance@registry.gov'),
                    to=[user.email]
                )
                confirm_email.send(fail_silently=True)
            except Exception as e:
                logger.error(f"Failed to send HODs confirmation email: {e}")

        return True, msg


    @staticmethod
    def pl_return_to_team_member(phase, user, reason=""):
        """Project Leader rejects and returns to Team Member/Active."""
        from registry.models import UserSecurity
        user_sec = UserSecurity.objects.filter(user=user).first()
        if not (user_sec and user_sec.role == 'Project Leader') and not user.is_superuser and phase.pm != user:
            return False, "Only the Project Leader can return a phase."

        with transaction.atomic():
            phase.status = 'Active' 
            phase.decision_reason = reason
            phase.project_leader_comments = f"REJECTED by {user.username}: {reason}"
            phase.approvals.filter(role='Project Leader').delete()
            phase.approvals.filter(role='Team Member').delete()
            phase.save()
            
            # Reactivate tasks
            phase.tasks.update(status='In Progress', completed_at=None)
            
            ProjectLog.objects.create(
                project=phase.project, user=user,
                message=f"Phase '{phase.name}' returned to Active by PL {user.username}. Reason: {reason[:100]}"
            )
        return True, "Phase returned to Active team status. Tasks reactivated."

    @staticmethod
    def pmt_return_to_pl(phase, user, reason=""):
        """PMT rejects phase and returns to PL for correction."""
        from registry.models import UserSecurity
        user_sec = UserSecurity.objects.filter(user=user).first()
        if not (user_sec and user_sec.role == 'Project Management Team') and not user.is_superuser:
            return False, "Only the Project Management Team can return a phase to PL."

        with transaction.atomic():
            phase.status = 'Awaiting Project Leader Approval'
            phase.decision_reason = reason
            phase.pmt_comments = f"REJECTED by {user.username}: {reason}"
            phase.approvals.filter(role='Project Management Team').delete() # Reset approvals for this level
            phase.save()
            
            # Reactivate tasks
            phase.tasks.update(status='In Progress', completed_at=None)
            
            ProjectLog.objects.create(
                project=phase.project, user=user,
                message=f"Phase '{phase.name}' returned to PL by PMT {user.username}. Reason: {reason[:100]}"
            )
        return True, "Phase returned to Project Leader for correction. Tasks reactivated."

    @staticmethod
    def hods_return_to_pmt(phase, user, reason=""):
        """HODs rejects phase and returns to PMT for correction."""
        from registry.models import UserSecurity
        user_sec = UserSecurity.objects.filter(user=user).first()
        if not (user_sec and user_sec.role == 'HODs') and not user.is_superuser:
            return False, "Only Head of Departments can return a phase to PMT."

        with transaction.atomic():
            phase.status = 'Awaiting PMT Approval'
            phase.decision_reason = reason
            phase.hods_comments = f"REJECTED by {user.username}: {reason}"
            phase.approvals.filter(role='HODs').delete()
            phase.save()
            
            # Reactivate tasks
            phase.tasks.update(status='In Progress', completed_at=None)
            
            ProjectLog.objects.create(
                project=phase.project, user=user,
                message=f"Phase '{phase.name}' returned to PMT by HODs {user.username}. Reason: {reason[:100]}"
            )
        return True, "Phase returned to Project Management Team for correction. Tasks reactivated."

    @staticmethod
    def approve_phase(phase, approver, status, notes="", signature_data=None):
        """Board approval handler with multi-approver logic."""
        try:
            from registry.models import UserSecurity
            user_sec = UserSecurity.objects.filter(user=approver).first()
            if not (user_sec and user_sec.role == 'Board of Executives') and not approver.is_superuser:
                 return False, "Only the Board of Executives can grant phase approval."

            with transaction.atomic():
                if status == 'Approved':
                    # Record individual approval
                    approval, created = PhaseApproval.objects.get_or_create(
                        phase=phase, 
                        approver=approver, 
                        role='Board of Executives',
                        defaults={'comment': notes, 'signature_data': signature_data}
                    )
                    if not created:
                        if signature_data:
                            approval.signature_data = signature_data
                            approval.comment = notes
                            approval.save()
                        else:
                            return False, "You have already approved this phase."

                    approval_count = phase.approvals.filter(role='Board of Executives').count()
                    required = phase.board_required or 1
                    msg = f"Phase '{phase.name}' approved by Board member {approver.username} ({approval_count}/{required})."

                    if approval_count >= required:
                        phase.status = 'Done'
                        # Aggregate comments
                        all_board_comments = "\n".join([f"{a.approver.username}: {a.comment}" for a in phase.approvals.filter(role='Board of Executives')])
                        phase.board_comments = all_board_comments
                        phase.approver = approver # Final approver
                        phase.approved_at = timezone.now()
                        phase.save()
                        
                        # Trigger Deliverables Email
                        GovernanceService.send_phase_deliverables_email(phase)

                        next_phase = ProjectPhase.objects.filter(
                            project=phase.project, 
                            sequence=phase.sequence + 1
                        ).first()
                        
                        if next_phase:
                            next_phase.status = 'Active'
                            next_phase.save()
                            msg += " Phase fully completed. Next phase activated."
                        else:
                            phase.project.status = 'Done'
                            phase.project.save()
                            msg += " Final institutional approval granted. Project complete."
                else:
                    # Rejection - return to HODs and reset Board approvals
                    phase.status = 'Awaiting HODs Approval'
                    phase.decision_reason = notes
                    phase.approvals.filter(role='Board of Executives').delete()
                    phase.save()
                    
                    # Reactivate tasks
                    phase.tasks.update(status='In Progress', completed_at=None)
                    
                    msg = f"Phase '{phase.name}' rejected by Board {approver.username}. Returned to HODs. Tasks reactivated. Reason: {notes}"

                ProjectLog.objects.create(project=phase.project, user=approver, message=msg)
                
                # ── SEND CONFIRMATION EMAIL ──
                try:
                    action_text = "Approved" if status == 'Approved' else "Action Recorded (Return/Reject)"
                    confirm_subject = f"Action Recorded: Board Decision - {phase.project.name}"
                    confirm_body = f"Hello {approver.username},\n\nYou have {action_text} Phase '{phase.name}' for Project '{phase.project.name}'.\n\nSystem URL: {settings.GOVERNANCE_BASE_URL}\n\nBest regards,\nRIFTS-X Governance"
                    confirm_email = EmailMessage(
                        subject=confirm_subject,
                        body=confirm_body,
                        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'governance@registry.gov'),
                        to=[approver.email]
                    )
                    confirm_email.send(fail_silently=True)
                except Exception as e:
                    logger.error(f"Failed to send Board confirmation email: {e}")

                return True, msg
        except Exception as e:
            logger.error(f"Error in approve_phase: {e}")
            return False, str(e)

    @staticmethod
    def send_phase_deliverables_email(phase):
        """Forwards all phase deliverables to Board and HODs."""
        from django.contrib.auth.models import User
        from registry.models import UserSecurity, TaskAttachment

        # Find HOD and Board recipients
        recipients = User.objects.filter(
            security_profile__role__in=['HODs', 'Board of Executives'],
            is_active=True
        ).values_list('email', flat=True)

        if not recipients:
            return

        subject = f"Deliverables Approved: {phase.project.name} - {phase.name}"
        body = f"""
        Dear Executive Team,

        The deliverables for Phase '{phase.name}' of project '{phase.project.name}' have been officially approved by the Board committee.

        Institutional Stage-Gate Governance Check: COMPLETED.
        
        Attached are the documents associated with the deliverables of this phase.

        System URL: {settings.GOVERNANCE_BASE_URL}
        Best regards,
        Registry Governance System
        """

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'governance@registry.gov'),
            to=list(recipients)
        )

        # Include Links in body if available
        links = []
        deliverable_tasks = phase.tasks.filter(is_deliverable=True)
        for task in deliverable_tasks:
            for att in task.attachments.all():
                if att.external_link:
                    links.append(f"- Task '{task.title}': {att.external_link}")
        
        for doc in phase.required_documents.all():
            if doc.external_link:
                links.append(f"- Phase Doc '{doc.title}': {doc.external_link}")
        
        if links:
            email.body += "\n\nEXTERNAL LINKS DELIVERABLES:\n" + "\n".join(links)

        # Attach all files from deliverable tasks
        deliverable_tasks = phase.tasks.filter(is_deliverable=True)
        for task in deliverable_tasks:
            attachments = task.attachments.all()
            for attach in attachments:
                if attach.file:
                    try:
                        email.attach(attach.filename, attach.file.read(), 'application/octet-stream')
                    except Exception as e:
                        logger.error(f"Failed to attach file {attach.filename}: {e}")

        try:
            email.send(fail_silently=True)
        except Exception as e:
            logger.error(f"Failed to send deliverables email: {e}")

    @staticmethod
    def send_gate_review_notification(phase, roles):
        """Notifies HODs or Board that a phase is ready for review, including deliverables (files + links)."""
        from django.contrib.auth.models import User
        recipients = User.objects.filter(
            security_profile__role__in=roles,
            is_active=True
        ).values_list('email', flat=True)
        
        if not recipients:
            return

        subject = f"Action Required: Phase Review - {phase.project.name} ({phase.name})"
        
        # Build deliverable links list
        links = []
        for task in phase.tasks.filter(is_deliverable=True):
            for att in task.attachments.all():
                if att.external_link:
                    links.append(f"- Task '{task.title}': {att.external_link}")
        
        for doc in phase.required_documents.all():
            if doc.external_link:
                links.append(f"- Phase Doc '{doc.title}': {doc.external_link}")

        links_str = "\n".join(links) if links else "None"
        
        body = f"""
        Dear {', '.join(roles)} Team,

        Phase '{phase.name}' of project '{phase.project.name}' has been submitted for your review and approval.

        EXTERNAL LINKS DELIVERABLES:
        {links_str}

        Attached are the file-based deliverables for this phase.

        System URL: {settings.GOVERNANCE_BASE_URL}
        Best regards,
        Strategic Intelligence Platform Governance
        """

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'governance@registry.gov'),
            to=list(recipients)
        )

        # Attach files from tasks
        for task in phase.tasks.filter(is_deliverable=True):
            for att in task.attachments.all():
                if att.file:
                    try:
                        email.attach(att.filename, att.file.read(), 'application/octet-stream')
                    except Exception as e:
                        logger.error(f"Failed to attach file {att.filename}: {e}")
                        
        # Attach phase documents
        for doc in phase.required_documents.all():
            if doc.file_attachment:
                filename = doc.file_attachment.name.split('/')[-1]
                try:
                    email.attach(filename, doc.file_attachment.read(), 'application/octet-stream')
                except Exception as e:
                    logger.error(f"Failed to attach phase doc {doc.title}: {e}")

        try:
            email.send(fail_silently=True)
        except Exception as e:
            logger.error(f"Failed to send gate review email: {e}")

    @staticmethod
    def check_phase_readiness(phase):
        """
        Checks if a phase is ready for gate review and notifies the PM.
        Called whenever a task is marked 'Done'.
        """
        if phase.status == 'Active' and phase.task_completion_percentage == 100:
            msg = f"All tasks in Phase '{phase.name}' are complete. Ready for Gate Review."
            ProjectAlert.objects.get_or_create(
                project=phase.project,
                phase=phase,
                alert_type='PhaseReady',
                message=msg,
                is_resolved=False
            )
            return True
        return False

    @staticmethod
    def calculate_institutional_metrics():
        """
        Computes aggregate metrics across all projects for the Executive Dashboard.
        Metrics: Agility Score, Governance Score, Budget Variance, SLA Breaches, etc.
        """
        from django.db.models import Sum, Avg, Count, Q, F
        from django.contrib.auth.models import User
        from registry.models import Department, Requisition, Project, ProjectPhase, ProjectTask
        
        now = timezone.now().date()
        projects = Project.objects.filter(is_deleted=False)
        total_projects = projects.count()
        
        if total_projects == 0:
            return {
                'total': 0, 'active': 0, 'delayed': 0, 'at_risk': 0, 'on_track': 0,
                'avg_duration': "0d", 'risk_heatmap': {},
                'projects_at_risk': 0, 'score_diff_perc': 1.0,
                'completion_rate': "0%", 'budget_variance': "0.00",
                'sla_breaches': 0, 'agility': "100%", 'score': "10.0",
                'dept_data': [], 'workload_data': []
            }

        # 1. Base Counts & Health
        active_projects = projects.filter(status='Active')
        delayed_count = projects.filter(status='Delayed').count()
        
        # Risk Distribution
        risk_counts = {'On Track': 0, 'At Risk': 0, 'Delayed': 0}
        heatmap = {'Critical': {'Red': 0, 'Yellow': 0, 'Green': 0}, 'High': {'Red': 0, 'Yellow': 0, 'Green': 0}, 'Medium': {'Red': 0, 'Yellow': 0, 'Green': 0}, 'Low': {'Red': 0, 'Yellow': 0, 'Green': 0}}
        
        for p in projects:
            indicator = p.risk_indicator
            risk_counts[indicator['level']] += 1
            
            # Map for heatmap (using project priority if exists, or highest task priority)
            priority = 'Medium' # Default
            top_task = ProjectTask.objects.filter(phase__project=p).order_by('-priority').first()
            if top_task: priority = top_task.priority
            
            color_key = 'Green'
            if indicator['color'] == 'danger': color_key = 'Red'
            elif indicator['color'] == 'warning': color_key = 'Yellow'
            
            if priority in heatmap:
                heatmap[priority][color_key] += 1

        # 2. Avg Project Duration (for completed projects)
        completed_projects = projects.filter(status='Done')
        avg_duration_str = "N/A"
        if completed_projects.exists():
            durations = []
            for cp in completed_projects:
                p_phases = cp.phases.all().order_by('sequence')
                start_p = p_phases.first()
                end_p = p_phases.last()
                if start_p and end_p and start_p.start_date and end_p.approved_at:
                    durations.append((end_p.approved_at.date() - start_p.start_date).days)
            if durations:
                avg_duration_str = f"{round(sum(durations)/len(durations))}d"

        # 3. Overall Completion Rate
        total_progress = sum([p.progress_percentage for p in projects])
        completion_rate = round(total_progress / total_projects) if total_projects > 0 else 0

        # 4. Budget Variance
        total_budget = projects.aggregate(total=Sum('budget'))['total'] or 0
        total_spent = Requisition.objects.filter(linked_projects__in=projects).aggregate(total=Sum('total_amount'))['total'] or 0
        task_spent = Requisition.objects.filter(linked_tasks__phase__project__in=projects).aggregate(total=Sum('total_amount'))['total'] or 0
        
        actual_total_spent = total_spent + task_spent
        budget_variance = float(total_budget - actual_total_spent)

        # 5. SLA Breaches (Total Overdue Tasks)
        sla_breaches = ProjectTask.objects.filter(
            status__in=['Pending', 'In Progress', 'Review'],
            due_date__lt=now
        ).count()

        # 6. Agility (Task Velocity)
        all_tasks = ProjectTask.objects.all()
        total_tasks = all_tasks.count()
        completed_tasks = all_tasks.filter(status='Done').count()
        agility_pct = round((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 100

        # ... (Department & Workload logic remains same)
        dept_stats = []
        for dept in Department.objects.all():
            dept_projects = projects.filter(department=dept)
            if dept_projects.exists():
                dept_progress = sum([p.progress_percentage for p in dept_projects]) / dept_projects.count()
                dept_stats.append({'name': dept.name, 'count': dept_projects.count(), 'progress': round(dept_progress)})

        workload = User.objects.filter(project_tasks__status__in=['Pending', 'In Progress', 'Review']).annotate(
            task_count=Count('project_tasks')
        ).order_by('-task_count')[:10]
        workload_data = [{'user': u.username, 'count': u.task_count} for u in workload]

        # 9. Governance Score Calculation
        completed_phases = ProjectPhase.objects.filter(status='Done', approved_at__isnull=False, submitted_at__isnull=False)
        avg_latency_days = 0
        if completed_phases.exists():
            latencies = [(p.approved_at - p.submitted_at).total_seconds() / 86400 for p in completed_phases]
            avg_latency_days = sum(latencies) / len(latencies)

        sla_score = (1 - (sla_breaches / total_tasks if total_tasks > 0 else 0)) * 4.0
        budget_perf = (actual_total_spent / total_budget if total_budget > 0 else 0)
        budget_score = 2.0 if budget_perf <= 1.0 else max(0, 2.0 - (budget_perf - 1.0) * 5)
        linked_tasks = all_tasks.filter(Q(physical_file__isnull=False) | Q(linked_requisition__isnull=False)).count()
        traceability_score = (linked_tasks / total_tasks if total_tasks > 0 else 0) * 2.0
        latency_score = max(0, 2.0 - (avg_latency_days / 3)) if avg_latency_days > 0 else 2.0
        
        final_governance_score = round(sla_score + budget_score + traceability_score + latency_score, 1)

        return {
            'total': total_projects,
            'active': active_projects.count(),
            'delayed': risk_counts['Delayed'],
            'at_risk': risk_counts['At Risk'],
            'on_track': risk_counts['On Track'],
            'projects_at_risk': risk_counts['At Risk'],  # alias used in some templates
            'avg_duration': avg_duration_str,
            'risk_heatmap': heatmap,
            'completion_rate': f"{completion_rate}%",
            'budget_variance': f"{budget_variance:,.2f}",
            'sla_breaches': sla_breaches,
            'agility': f"{agility_pct}%",
            'score': f"{final_governance_score}",
            'score_diff_perc': round(1.0 - (final_governance_score / 10.0), 4),  # for SVG ring
            'avg_latency': f"{round(avg_latency_days, 1)}d",
            'dept_data': dept_stats,
            'workload_data': workload_data
        }

    @staticmethod
    def scan_deadlines():
        """
        System-wide scan for pending deadlines and overdue tasks.
        Triggers alerts and escalations based on institutional rules.
        """
        from datetime import timedelta
        now = timezone.now()
        today = now.date()
        
        # 🔔 BEFORE DEADLINE (48h and Morning of)
        upcoming_48h = ProjectTask.objects.filter(
            status__in=['Pending', 'In Progress', 'To Do'],
            due_date=today + timedelta(days=2)
        )
        for task in upcoming_48h:
            ProjectAlert.objects.get_or_create(
                project=task.phase.project, task=task,
                alert_type='Deadline', 
                message=f"Deadline Alert: Task '{task.title}' is due in 48 hours."
            )

        upcoming_today = ProjectTask.objects.filter(
            status__in=['Pending', 'In Progress', 'To Do'],
            due_date=today
        )
        for task in upcoming_today:
            ProjectAlert.objects.get_or_create(
                project=task.phase.project, task=task,
                alert_type='DeadlineMorning',
                message=f"Morning Brief: Task '{task.title}' is due TODAY."
            )

        # 🟡 YELLOW WARNING (24h left)
        upcoming_24h = ProjectTask.objects.filter(
            status__in=['Pending', 'In Progress', 'To Do'],
            due_date=today + timedelta(days=1)
        )
        for task in upcoming_24h:
            ProjectAlert.objects.get_or_create(
                project=task.phase.project, task=task,
                alert_type='Warning',
                message=f"Critical Warning: Task '{task.title}' has only 24 hours left before deadline."
            )

        # 🔴 AFTER DEADLINE (Escalations)
        overdue_tasks = ProjectTask.objects.filter(
            status__in=['Pending', 'In Progress', 'To Do', 'Review'],
            due_date__lt=today
        )
        for task in overdue_tasks:
            delay_days = (today - task.due_date).days
            
            # Level 1: Team Member & PM Notification
            ProjectAlert.objects.get_or_create(
                project=task.phase.project, task=task,
                alert_type='Overdue',
                message=f"STRICT OVERDUE: '{task.title}' is {delay_days} days late. Immediate action required."
            )
            
            # Level 2: Escalate to HOD (if > 3 days late)
            if delay_days > 3:
                ProjectAlert.objects.get_or_create(
                    project=task.phase.project, task=task,
                    alert_type='Escalation',
                    message=f"GOVERNANCE ESCALATION (HOD): Task '{task.title}' in {task.phase.project.name} is critically delayed ({delay_days} days)."
                )
            
            # Level 3: Escalate to MD (if phase blocked)
            if delay_days > 7 and task.phase.status == 'Active':
                ProjectAlert.objects.get_or_create(
                    project=task.phase.project, task=task,
                    alert_type='Escalation',
                    message=f"STRATEGIC BLOCKER (MD): Phase '{task.phase.name}' is stalled due to critical task delay. Ministerial oversight requested."
                )
                task.phase.project.status = 'Delayed'
                task.phase.project.save()

        return True

    @staticmethod
    def update_project_health(project):
        """
        Assesses project risk based on task status and deadlines.
        Updates project status to 'Delayed' if high-risk thresholds are met.
        """
        indicator = project.risk_indicator
        
        # Auto-escalate project status if risk is 'Delayed'
        if indicator['level'] == 'Delayed' and project.status == 'Active':
            project.status = 'Delayed'
            project.save()
            
        return indicator

