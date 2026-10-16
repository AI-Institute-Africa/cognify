import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'land_registry.settings')
django.setup()

from registry.models import ProjectPhase

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
    },
    {
        'name': 'Documentation',
        'deliverables': '- Technical Manual\n- User Guide\n- API Documentation',
        'criteria': 'Review by peers and technical writer sign-off.'
    },
    {
        'name': 'Verification',
        'deliverables': '- Test Report\n- UAT Results\n- Performance Logs',
        'criteria': 'All critical bugs resolved and UAT approved by stakeholders.'
    }
]

updated_count = 0
for cfg in phases_config:
    # Handle None or empty string
    phases = ProjectPhase.objects.filter(name__iexact=cfg['name']).filter(
        django.db.models.Q(deliverables__isnull=True) | django.db.models.Q(deliverables='')
    )
    for phase in phases:
        phase.deliverables = cfg['deliverables']
        phase.completion_criteria = cfg['criteria']
        phase.save()
        updated_count += 1

print(f"Repaired {updated_count} phase records.")
