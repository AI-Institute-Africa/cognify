import logging
from django.utils import timezone
from django.db.models import Avg, Count, Q, F
from datetime import timedelta
from registry.models import Project, ProjectPhase, ProjectSprint, ProjectTask

logger = logging.getLogger(__name__)

class ProjectIntelligenceService:
    """
    Heuristic-based intelligence layer for RIFTS-X Project Governance.
    Provides predictive insights, deadline suggestions, and workload optimization.
    """

    @staticmethod
    def get_suggested_deadline(task_title=None, phase=None):
        """
        Suggests a task deadline based on historical completion times for similar tasks/phases.
        """
        now = timezone.now().date()
        
        # Heuristic: Find average duration of completed tasks in this phase type
        if phase:
            avg_duration = ProjectTask.objects.filter(
                phase__name=phase.name,
                status='Done',
                completed_at__isnull=False
            ).annotate(
                duration=F('completed_at__date') - F('phase__start_date')
            ).aggregate(avg=Avg('duration'))['avg']
            
            if avg_duration:
                return now + timedelta(days=max(1, int(avg_duration.days / 2))) # Mid-phase suggestion
        
        # Default fallback: 3 days for small tasks, 7 for others
        return now + timedelta(days=7)

    @staticmethod
    def analyze_sprint_feasibility(sprint):
        """
        Detects unrealistic timelines by comparing task count vs. historical sprint velocity.
        """
        tasks = sprint.tasks.all()
        task_count = tasks.count()
        if task_count == 0:
            return {'score': 100, 'status': 'Optimal', 'message': 'Sprint is empty.'}

        # Historical velocity: Avg tasks per completed sprint in this project
        avg_velocity = ProjectSprint.objects.filter(
            phase__project=sprint.phase.project,
            status='Done'
        ).annotate(t_count=Count('tasks')).aggregate(avg=Avg('t_count'))['avg'] or 5
        
        complexity_score = (task_count / avg_velocity) * 100
        
        if complexity_score > 150:
            return {
                'score': round(complexity_score),
                'status': 'Unrealistic',
                'message': f"Sprint load ({task_count} tasks) exceeds historical capacity ({round(avg_velocity, 1)}). Recommend removing at least {int(task_count - avg_velocity)} tasks."
            }
        elif complexity_score > 120:
             return {
                'score': round(complexity_score),
                'status': 'Challenging',
                'message': "Sprint is heavily loaded. Monitor closely for delays."
            }
        
        return {'score': round(complexity_score), 'status': 'Healthy', 'message': 'Task load is within historical bounds.'}

    @staticmethod
    def detect_user_overload(user):
        """
        Identifies if a team member has an excessive workload.
        """
        active_tasks = user.project_tasks.filter(status__in=['To Do', 'In Progress', 'Review'])
        critical_count = active_tasks.filter(priority__in=['Critical', 'High']).count()
        total_count = active_tasks.count()
        
        # Heuristic: > 3 critical/high tasks OR > 8 total tasks = Overloaded
        if critical_count > 3:
            return True, f"User '{user.username}' is overloaded with {critical_count} critical/high priority tasks."
        if total_count > 10:
            return True, f"User '{user.username}' has an excessive task count ({total_count})."
            
        return False, "Workload is manageable."

    @staticmethod
    def predict_project_delay(project):
        """
        Predicts delay probability based on elapsed time vs. completion rate and active blockers.
        """
        now = timezone.now().date()
        total_days = (project.end_date - project.start_date).days if project.end_date and project.start_date else 30
        elapsed_days = (now - project.start_date).days if project.start_date else 0
        
        if elapsed_days <= 0: return 5 # Minimum baseline risk
        
        time_ratio = elapsed_days / total_days if total_days > 0 else 1
        completion_ratio = project.progress_percentage / 100
        
        # Delay Probability Factor (DPF)
        # If time_ratio > completion_ratio, we are likely to be delayed
        dpf = (time_ratio - completion_ratio) * 100
        
        # Add risk for active blockers or overdue tasks
        overdue_tasks = ProjectTask.objects.filter(
            phase__project=project,
            status__in=['To Do', 'In Progress', 'Review'],
            due_date__lt=now
        ).count()
        
        risk_adjustment = overdue_tasks * 5
        final_probability = min(99, max(5, dpf + risk_adjustment))
        
        status = "Healthy"
        if final_probability > 70: status = "CRITICAL"
        elif final_probability > 40: status = "Warning"
        
        return {
            'probability': f"{int(final_probability)}%",
            'status': status,
            'overdue_count': overdue_tasks,
            'message': f"Delayed likelihood is {int(final_probability)}% based on current velocity."
        }

    @staticmethod
    def predict_sprint_delay(sprint):
        """
        Predicts sprint delay probability based on elapsed time vs. completion rate.
        """
        now = timezone.now().date()
        total_days = sprint.duration_days
        elapsed_days = (now - sprint.start_date).days if sprint.start_date <= now else 0
        
        if elapsed_days <= 0: return {'probability': '5%', 'status': 'Healthy', 'message': 'Sprint has not started or is in early stages.'}
        
        time_ratio = elapsed_days / total_days if total_days > 0 else 1
        completion_ratio = sprint.progress_percentage / 100
        
        # Delay Probability Factor
        dpf = (time_ratio - completion_ratio) * 100
        
        overdue_tasks = sprint.tasks.filter(
            status__in=['To Do', 'In Progress', 'Review'],
            due_date__lt=now
        ).count()
        
        risk_adjustment = overdue_tasks * 10
        final_probability = min(99, max(5, dpf + risk_adjustment))
        
        status = "Healthy"
        if final_probability > 75: status = "CRITICAL"
        elif final_probability > 45: status = "Warning"
        
        return {
            'probability': f"{int(final_probability)}%",
            'status': status,
            'overdue_count': overdue_tasks,
            'message': f"Sprint risk is {status} ({int(final_probability)}%) with {overdue_tasks} overdue tasks."
        }
