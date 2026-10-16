from django.utils import timezone
from datetime import timedelta
from registry.models import Borrow, File
from django.db.models import Count

class AIGovernor:
    """
    The Predictive Layer of RIFTS-X.
    Analyzes workflows to anticipate needs and mitigate risks.
    """
    
    @staticmethod
    def assess_risk(officer):
        """
        Assesses 'Data Hoarding' risk for a specific officer.
        """
        active_borrows = Borrow.objects.filter(borrower=officer, status='0')
        now = timezone.now().date()
        
        risks = []
        for borrow in active_borrows:
            if borrow.return_date < now:
                overdue_days = (now - borrow.return_date).days
                risks.append({
                    'file': borrow.file_doc.title,
                    'overdue_days': overdue_days,
                    'risk_level': 'High' if overdue_days > 7 else 'Medium'
                })
        return risks

    @staticmethod
    def predict_next_files(officer):
        """
        Analyzes historical patterns to predict which files might be needed.
        Currently uses 'Classification Co-occurrence' logic.
        """
        recent_borrows = Borrow.objects.filter(borrower=officer).order_by('-date_added')[:5]
        if not recent_borrows:
            return []
            
        common_subcats = recent_borrows.values_list('file_doc__sub_category', flat=True).distinct()
        
        # Suggest files in the same sub-categories that aren't currently borrowed
        predictions = File.objects.filter(
            sub_category__in=common_subcats,
            status='1' # Active
        ).exclude(
            id__in=Borrow.objects.filter(status='0').values_list('file_doc_id', flat=True)
        ).order_by('?')[:3] # Randomly surface some for discovery
        
        return predictions

    @staticmethod
    def get_system_health():
        """
        Calculates a global health score using the SLAManager.
        """
        from registry.services.sla import SLAManager
        return SLAManager.get_system_health()

    @staticmethod
    def get_risk_metrics():
        """
        Returns aggregate risk statistics for the dashboard.
        """
        from registry.models import File
        total_files = File.objects.filter(delete_flag=0).count()
        critical_files = File.objects.filter(risk_level='Critical', delete_flag=0).count()
        moderate_files = File.objects.filter(risk_level='Moderate', delete_flag=0).count()
        
        return {
            'critical': critical_files,
            'moderate': moderate_files,
            'low': total_files - critical_files - moderate_files,
            'health': SLAManager.get_system_health()
        }
