from registry.models import File, FileLocation, CustodyLog, Department

class LocationIntelligence:
    @staticmethod
    def get_last_known_location(file_obj):
        """
        Retrieves the last confirmed physical location details.
        """
        # 1. Check current_location FK
        if file_obj.current_location:
            return {
                'building': file_obj.current_location.building,
                'floor': file_obj.current_location.floor,
                'office': file_obj.current_location.office,
                'cabinet': file_obj.current_location.cabinet,
                'shelf': file_obj.current_location.shelf,
                'is_precise': True
            }
        
        # 2. Check last CustodyLog with location info
        last_log = CustodyLog.objects.filter(file_doc=file_obj).exclude(location=None).first()
        if last_log and last_log.location:
            return {
                'building': last_log.location.building,
                'floor': last_log.location.floor,
                'office': last_log.location.office,
                'cabinet': last_log.location.cabinet,
                'shelf': last_log.location.shelf,
                'is_precise': True
            }
            
        return {'details': 'Location Unknown', 'is_precise': False}

    @staticmethod
    def suggest_routing(file_obj, target_dept):
        """
        Suggests an optimal physical route for file transfer.
        Currently based on Department standard locations.
        """
        # Placeholder for routing logic
        # In a real system, we'd use a Graph of buildings/offices
        return f"Route via Transit Hub -> {target_dept.name} Registry Desk"

    @staticmethod
    def get_location_heatmap():
        """
        Aggregates file counts by building/floor.
        """
        from django.db.models import Count
        stats = FileLocation.objects.annotate(file_count=Count('file')).values('building', 'floor', 'office', 'file_count')
        return list(stats)

    @staticmethod
    def get_department_heatmap():
        """
        Aggregates file counts by department.
        """
        from django.db.models import Count
        from registry.models import Department
        stats = Department.objects.annotate(file_count=Count('file')).values('name', 'file_count')
        return list(stats)
