import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from registry.models import MeetingActionItem, MeetingNotification

class Command(BaseCommand):
    help = "Checks meeting action item deadlines, marks overdue items, sends reminders, and escalates overdue actions."

    def handle(self, *args, **options):
        today = timezone.now().date()
        self.stdout.write(f"Checking ZRP Meeting Action Item deadlines for {today}...")

        # 1. Mark Overdue Items
        overdue_items = MeetingActionItem.objects.filter(
            due_date__lt=today,
            status__in=['Pending', 'In Progress']
        )
        marked_count = 0
        escalated_count = 0

        for item in overdue_items:
            item.status = 'Overdue'
            
            # Check for escalation (if overdue by more than 3 days)
            days_overdue = (today - item.due_date).days
            if days_overdue >= 3 and not item.is_escalated:
                item.is_escalated = True
                item.escalated_at = timezone.now()
                escalated_count += 1
                
                # Escalation notification
                MeetingNotification.objects.create(
                    user=item.assigned_to,
                    meeting=item.meeting,
                    action_item=item,
                    notification_type='Escalation',
                    message=f"CRITICAL ESCALATION: Action Item '{item.description[:60]}' is overdue by {days_overdue} days and has been escalated to Management."
                )

            item.save()
            marked_count += 1

            # Notification to assignee
            MeetingNotification.objects.get_or_create(
                user=item.assigned_to,
                meeting=item.meeting,
                action_item=item,
                notification_type='Overdue Action',
                defaults={'message': f"OVERDUE ALERT: Action Item '{item.description[:60]}' was due on {item.due_date}."}
            )

        # 2. Upcoming Deadline Reminders (Due in 2 days)
        reminder_date = today + datetime.timedelta(days=2)
        upcoming_items = MeetingActionItem.objects.filter(
            due_date=reminder_date,
            status__in=['Pending', 'In Progress']
        )
        reminder_count = 0

        for item in upcoming_items:
            MeetingNotification.objects.get_or_create(
                user=item.assigned_to,
                meeting=item.meeting,
                action_item=item,
                notification_type='Upcoming Deadline',
                defaults={'message': f"DEADLINE REMINDER: Action Item '{item.description[:60]}' is due on {item.due_date}."}
            )
            reminder_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Completed deadline check: {marked_count} marked overdue, {escalated_count} escalated, {reminder_count} reminders sent."
            )
        )
