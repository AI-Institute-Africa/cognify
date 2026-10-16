import re

filepath = r"c:\Users\USER 2\Downloads\project1\project1\land_registry\registry\services\governance.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update advance_phase to team_member_submit_to_pl
content = content.replace(
    "if phase.status in ('Awaiting PMT Approval', 'Awaiting HODs Approval', 'Awaiting Board Approval'):",
    "if phase.status in ('Awaiting Team Member Approval', 'Awaiting Project Leader Approval', 'Awaiting PMT Approval', 'Awaiting HODs Approval', 'Awaiting Board Approval'):"
)

content = content.replace(
    "phase.status = 'Review'",
    "phase.status = 'Awaiting Team Member Approval'"
)
content = content.replace(
    "return True, \"All tasks submitted for PL Review. PL must now approve tasks and consolidate phase.\"",
    "return True, \"All tasks complete. Phase forwarded for Team Member peer approval.\""
)

# 2. We need to add `team_member_submit_to_pl` method right after `advance_phase`
# advance_phase ends with `return False, str(e)` around line 101.
team_member_method = """
    @staticmethod
    def team_member_submit_to_pl(phase, user, comments="", signature_data=None):
        \"\"\"Team Member approves the phase and forwards to Project Leader.\"\"\"
        from registry.models import UserSecurity
        user_sec = UserSecurity.objects.filter(user=user).first()
        if not (user_sec and user_sec.role == 'Team Member') and not user.is_superuser:
            return False, "Only a Team Member can perform this initial phase approval."

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
            all_comments = "\\n".join([f"{a.approver.username}: {a.comment}" for a in phase.approvals.filter(role='Team Member')])
            phase.team_member_comments = all_comments
            phase.save()
            
            msg = f"Phase '{phase.name}' peer-approved by {user.username}. Forwarded to Project Leader."
            ProjectLog.objects.create(project=phase.project, user=user, message=msg)
            
            # Notify PL
            GovernanceService.send_gate_review_notification(phase, ['Project Leader'])
        return True, msg
"""

# Find where pl_submit_to_pmt starts and insert team_member_method before it
content = content.replace(
    "    @staticmethod\n    def pl_submit_to_pmt(phase, user, notes=\"\"):",
    team_member_method + "\n    @staticmethod\n    def pl_submit_to_pmt(phase, user, notes=\"\"):"
)

# 3. Update pl_submit_to_pmt to be an actual approval step
pl_approval_logic = """
    @staticmethod
    def pl_submit_to_pmt(phase, user, comments="", signature_data=None):
        \"\"\"Project Leader approves and forwards to PMT.\"\"\"
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

            phase.status = 'Awaiting PMT Approval'
            phase.consolidation_notes = comments
            all_comments = "\\n".join([f"{a.approver.username}: {a.comment}" for a in phase.approvals.filter(role='Project Leader')])
            phase.project_leader_comments = all_comments
            phase.submitted_at = timezone.now()
            phase.save()
            
            msg = f"Phase '{phase.name}' approved by PL {user.username} and forwarded to PMT."
            ProjectLog.objects.create(project=phase.project, user=user, message=msg)
            
            # Notify PMT
            GovernanceService.send_gate_review_notification(phase, ['Project Management Team'])
            
        return True, msg
"""

# Use regex to replace the old pl_submit_to_pmt entirely
import re
content = re.sub(
    r'    @staticmethod\n    def pl_submit_to_pmt\(phase, user, notes=""\):.*?return True, "Phase consolidated and forwarded to PMT\."\n',
    pl_approval_logic,
    content,
    flags=re.DOTALL
)

# Add PL reject (pl_return_to_team_member)
pl_reject_logic = """
    @staticmethod
    def pl_return_to_team_member(phase, user, reason=""):
        \"\"\"Project Leader rejects and returns to Team Member/Active.\"\"\"
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
            
            ProjectLog.objects.create(
                project=phase.project, user=user,
                message=f"Phase '{phase.name}' returned to Active by PL {user.username}. Reason: {reason[:100]}"
            )
        return True, "Phase returned to Active team status. PL approvals reset."
"""

content = content.replace(
    "    @staticmethod\n    def pmt_return_to_pl(phase, user, reason=\"\"):",
    pl_reject_logic + "\n    @staticmethod\n    def pmt_return_to_pl(phase, user, reason=\"\"):"
)

# Fix pmt_return_to_pl to return to 'Awaiting Project Leader Approval'
content = content.replace(
    "phase.status = 'Active' # Return to Active for PL to fix/re-consolidate",
    "phase.status = 'Awaiting Project Leader Approval'"
)


with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated governance.py successfully.")
