from django.utils import timezone
from datetime import timedelta
from .. import models
from django.db.models import Count, Q

class AutomationService:
    @staticmethod
    def process_all_alerts():
        """Main entry point to run all automated checks."""
        AutomationService.check_upcoming_deadlines()
        AutomationService.check_overdue_tasks()
        AutomationService.check_sprint_status()
        AutomationService.check_predictive_velocity()

    @staticmethod
    def check_upcoming_deadlines():
        """Alert team members 48 hours before and on morning of deadline."""
        now = timezone.now().date()
        warning_48h = now + timedelta(hours=48)
        
        # 48-hour alert
        tasks_48h = models.ProjectTask.objects.filter(
            due_date=warning_48h,
            status__in=['To Do', 'In Progress', 'Review']
        ).exclude(alerts__alert_type='Deadline')

        for task in tasks_48h:
            models.ProjectAlert.objects.create(
                project=task.phase.project,
                task=task,
                alert_type='Deadline',
                message=f"🔔 48h Warning: '{task.title}' is due in 2 days ({task.due_date})."
            )

        # Morning of deadline alert
        tasks_today = models.ProjectTask.objects.filter(
            due_date=now,
            status__in=['To Do', 'In Progress', 'Review']
        ).exclude(alerts__alert_type='DeadlineMorning')

        for task in tasks_today:
            models.ProjectAlert.objects.create(
                project=task.phase.project,
                task=task,
                alert_type='DeadlineMorning',
                message=f"☀️ Due Today: Task '{task.title}' must be completed by EOD."
            )

    @staticmethod
    def check_overdue_tasks():
        """Standard escalation: Day 0 (Team/PM), Day 3 (HOD), Phase Blocked (MD)."""
        now = timezone.now().date()
        overdue_tasks = models.ProjectTask.objects.filter(
            due_date__lt=now,
            status__in=['To Do', 'In Progress', 'Review', 'Blocked']
        )

        for task in overdue_tasks:
            delay_days = (now - task.due_date).days
            project = task.phase.project

            # Day 0: Team Member & PM Alert
            if not task.alerts.filter(alert_type='Overdue').exists():
                models.ProjectAlert.objects.create(
                    project=project,
                    task=task,
                    alert_type='Overdue',
                    message=f"🔴 Overdue: '{task.title}' missed its deadline of {task.due_date}."
                )
            
            # Day 3: Escalate to HOD
            if delay_days >= 3 and not task.alerts.filter(alert_type='EscalationHOD').exists():
                models.ProjectAlert.objects.create(
                    project=project,
                    task=task,
                    alert_type='EscalationHOD',
                    message=f"🚨 HOD ESCALATION: Task '{task.title}' is {delay_days} days overdue. Direct intervention required."
                )

            # MD Escalation if Phase is Blocked
            # A phase is blocked if it's 'Active' but has an overdue task preventing progress (Stage-Gate logic)
            if task.phase.status == 'Active' and not task.alerts.filter(alert_type='EscalationMD').exists():
                models.ProjectAlert.objects.create(
                    project=project,
                    task=task,
                    phase=task.phase,
                    alert_type='EscalationMD',
                    message=f"⚖️ MD COMMAND: Phase '{task.phase.name}' is BLOCKED due to overdue task '{task.title}'. Institutional impact risk."
                )

    @staticmethod
    def check_sprint_status():
        """Notify when sprint is ending soon (within 24h)."""
        threshold = timezone.now() + timedelta(hours=24)
        active_sprints = models.ProjectSprint.objects.filter(
            end_date__lte=threshold.date(),
            end_date__gte=timezone.now().date(),
            status='Active'
        ).exclude(alerts__alert_type='SprintEnd')

        for sprint in active_sprints:
            models.ProjectAlert.objects.create(
                project=sprint.project,
                sprint=sprint,
                alert_type='SprintEnd',
                message=f"Sprint Notification: '{sprint.name}' is ending in less than 24 hours."
            )

    @staticmethod
    def check_predictive_velocity():
        """Predictive alert based on current sprint velocity."""
        active_sprints = models.ProjectSprint.objects.filter(status='Active')
        
        for sprint in active_sprints:
            total_tasks = sprint.tasks.count()
            if total_tasks == 0:
                continue
                
            completed_tasks = sprint.tasks.filter(status='Done').count()
            
            # Simple velocity: tasks per day since start
            start_date = sprint.start_date
            now = timezone.now().date()
            days_passed = (now - start_date).days
            
            if days_passed > 0:
                velocity = completed_tasks / days_passed
                remaining_tasks = total_tasks - completed_tasks
                days_remaining = (sprint.end_date - now).days
                
                if days_remaining > 0:
                    predicted_needed_velocity = remaining_tasks / days_remaining
                    
                    if velocity < predicted_needed_velocity:
                        # Only alert once per sprint unless status changes significantly? 
                        # For now, alert if not already alerted for this sprint's predictive delay
                        if not models.ProjectAlert.objects.filter(sprint=sprint, alert_type='Predictive').exists():
                            models.ProjectAlert.objects.create(
                                project=sprint.project,
                                sprint=sprint,
                                alert_type='Predictive',
                                message=f"FUTURISTIC INSIGHT: Based on current velocity ({velocity:.2f} tasks/day), this sprint may miss its deadline. Required velocity is {predicted_needed_velocity:.2f} tasks/day."
                            )
