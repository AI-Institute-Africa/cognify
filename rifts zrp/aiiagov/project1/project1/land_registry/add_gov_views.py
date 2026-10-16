views_code = """
# ==========================================
# 5-LEVEL PROJECT APPROVAL HIERARCHY VIEWS
# ==========================================
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from registry.models import ProjectPhase
from registry.services.governance import GovernanceService

@login_required
def advance_phase_view(request, pk):
    \"\"\"Team Member submits phase for PL review.\"\"\"
    phase = get_object_or_404(ProjectPhase, pk=pk)
    if request.method == 'POST':
        comments = request.POST.get('comments', '')
        success, msg = GovernanceService.team_member_submit_to_pl(phase, request.user, comments=comments)
        if success:
            messages.success(request, msg)
        else:
            messages.error(request, msg)
    return redirect('project-detail', pk=phase.project.pk)

@login_required
def pm_consolidate_phase(request, pk):
    \"\"\"Project Leader approves and consolidates phase for PMT.\"\"\"
    phase = get_object_or_404(ProjectPhase, pk=pk)
    if request.method == 'POST':
        comments = request.POST.get('comments', '')
        success, msg = GovernanceService.pl_submit_to_pmt(phase, request.user, comments=comments)
        if success:
            messages.success(request, msg)
        else:
            messages.error(request, msg)
    return redirect('project-detail', pk=phase.project.pk)

@login_required
def pm_auto_consolidate_phase(request, pk):
    \"\"\"Auto consolidation if needed (fallback to normal consolidation).\"\"\"
    return pm_consolidate_phase(request, pk)

@login_required
def pmt_verify_phase(request, pk):
    \"\"\"PMT verifies and forwards to HODs.\"\"\"
    phase = get_object_or_404(ProjectPhase, pk=pk)
    if request.method == 'POST':
        comments = request.POST.get('comments', '')
        success, msg = GovernanceService.pmt_submit_to_hods(phase, request.user, comments=comments)
        if success:
            messages.success(request, msg)
        else:
            messages.error(request, msg)
    return redirect('project-detail', pk=phase.project.pk)

@login_required
def hods_verify_phase(request, pk):
    \"\"\"HODs verifies and forwards to Board.\"\"\"
    phase = get_object_or_404(ProjectPhase, pk=pk)
    if request.method == 'POST':
        comments = request.POST.get('comments', '')
        success, msg = GovernanceService.hods_submit_to_board(phase, request.user, comments=comments)
        if success:
            messages.success(request, msg)
        else:
            messages.error(request, msg)
    return redirect('project-detail', pk=phase.project.pk)

@login_required
def approve_phase(request, pk, status):
    \"\"\"Board final approval or rejection.\"\"\"
    phase = get_object_or_404(ProjectPhase, pk=pk)
    if request.method == 'POST':
        comments = request.POST.get('comments', '')
        success, msg = GovernanceService.approve_phase(phase, request.user, status, notes=comments)
        if success:
            messages.success(request, msg)
        else:
            messages.error(request, msg)
    return redirect('project-detail', pk=phase.project.pk)

@login_required
def return_phase(request, pk):
    \"\"\"Generic return/reject phase based on user role.\"\"\"
    phase = get_object_or_404(ProjectPhase, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('reason', 'Returned for corrections')
        user_sec = getattr(request.user, 'security_profile', None)
        role = user_sec.role if user_sec else None

        if role == 'Project Leader' or phase.pm == request.user:
            success, msg = GovernanceService.pl_return_to_team_member(phase, request.user, reason=reason)
        elif role == 'Project Management Team':
            success, msg = GovernanceService.pmt_return_to_pl(phase, request.user, reason=reason)
        elif role == 'HODs':
            success, msg = GovernanceService.hods_return_to_pmt(phase, request.user, reason=reason)
        else:
            success, msg = False, "Unauthorized to return phase or unknown role."

        if success:
            messages.success(request, msg)
        else:
            messages.error(request, msg)

    return redirect('project-detail', pk=phase.project.pk)

"""

filepath = r"c:\Users\USER 2\Downloads\project1\project1\land_registry\registry\views.py"
with open(filepath, "a", encoding="utf-8") as f:
    f.write("\n" + views_code + "\n")
print("Successfully appended governance views.")
