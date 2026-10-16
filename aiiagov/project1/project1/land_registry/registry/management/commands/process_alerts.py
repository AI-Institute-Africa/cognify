from django.core.management.base import BaseCommand
from ...services.automation import AutomationService

class Command(BaseCommand):
    help = 'Processes all project-related smart alerts and automation tasks.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Smart Alerts & Automation Engine...'))
        
        try:
            AutomationService.process_all_alerts()
            self.stdout.write(self.style.SUCCESS('Successfully processed all alerts.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error processing alerts: {str(e)}'))
