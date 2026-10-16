from django.utils import timezone
from datetime import timedelta
from registry.models import File, CustodyLog, SLAConfig, Borrow

class SLAManager:
    @staticmethod
    def check_file_sla(file_obj):
        """
        Analyzes the current SLA status of a file.
        Returns a dict with status and days overdue.
        """
        # Determine priority. For now, we'll use 'Medium' as default
        # In a real system, this would be based on File type or category
        sla = SLAConfig.objects.filter(priority='Medium').first()
        if not sla:
            return {'status': 'Normal', 'delay': 0}

        # Find the last movement
        last_log = CustodyLog.objects.filter(file_doc=file_obj).first()
        if not last_log:
            return {'status': 'Normal', 'delay': 0}

        time_since_last_move = timezone.now() - last_log.timestamp
        days_held = time_since_last_move.days

        # Check against department threshold (if it was a transfer)
        if last_log.action == 'TRANSFER':
            if days_held > sla.max_days_department:
                return {
                    'status': 'BREACHED',
                    'delay': days_held - sla.max_days_department,
                    'level': 2,
                    'escalate_to': sla.escalation_level_2
                }
        
        # Check against user threshold (handover/creation)
        if days_held > sla.max_days_user:
            return {
                'status': 'WARNING',
                'delay': days_held - sla.max_days_user,
                'level': 1,
                'escalate_to': sla.escalation_level_1
            }

        return {'status': 'Normal', 'delay': 0}

    @staticmethod
    def get_system_health():
        """
        Calculates overall system health based on active breaches.
        """
        active_files = File.objects.filter(delete_flag=0)
        total = active_files.count()
        if total == 0: return 100
        
        breached_count = 0
        for f in active_files:
            status = SLAManager.check_file_sla(f)
            if status['status'] == 'BREACHED':
                breached_count += 1
        
        health = ((total - breached_count) / total) * 100
        return round(health, 2)

    @staticmethod
    def get_breached_count():
        """
        Returns the count of active files currently in BREACHED status.
        """
        count = 0
        for f in File.objects.filter(delete_flag=0):
            if SLAManager.check_file_sla(f)['status'] == 'BREACHED':
                count += 1
        return count
