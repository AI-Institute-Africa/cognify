from registry.models import File, CustodyLog

class RiskEngine:
    @staticmethod
    def update_file_risk(file_obj):
        """
        Recalculates the risk score (0-100) and level for a file.
        Factors:
        - Sensitivity level (Normal=0, Sensitive=20, Confidential=40)
        - Movement frequency (Frequent = High Risk)
        - Current SLA status (Breached = +20)
        """
        score = 0
        
        # 1. Sensitivity Base
        sensitivity_map = {
            'Normal': 0,
            'Sensitive': 20,
            'Highly Confidential': 40
        }
        score += sensitivity_map.get(file_obj.sensitivity_level, 0)
        
        # 2. Movement Frequency (last 30 days)
        # More movement = higher risk of displacement
        recent_logs = CustodyLog.objects.filter(file_doc=file_obj).count()
        if recent_logs > 5:
            score += 20
        elif recent_logs > 2:
            score += 10
            
        # 3. SLA Weight
        from registry.services.sla import SLAManager
        sla_status = SLAManager.check_file_sla(file_obj)
        if sla_status['status'] == 'BREACHED':
            score += 30
        elif sla_status['status'] == 'WARNING':
            score += 15
            
        # Cap at 100
        file_obj.risk_score = min(score, 100)
        
        # Categorize
        if file_obj.risk_score >= 70:
            file_obj.risk_level = 'Critical'
        elif file_obj.risk_score >= 40:
            file_obj.risk_level = 'Moderate'
        else:
            file_obj.risk_level = 'Low'
            
        file_obj.save()
        return file_obj.risk_score

    @staticmethod
    def get_critical_count():
        """
        Returns count of files with 'Critical' risk level.
        """
        return File.objects.filter(risk_level='Critical', delete_flag=0).count()
