import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'land_registry.settings')
django.setup()

from registry.models import Department, SLAConfig

def initialize():
    # Departments
    depts = [
        ('Records Management', 'Central registry and file storage'),
        ('Legal Affairs', 'Land disputes and legal documentation'),
        ('Survey & Mapping', 'Geospatial and survey records'),
        ('Valuation', 'Property valuation and assessment'),
        ('Customer Service', 'Public enquiry and file initiation')
    ]
    for name, desc in depts:
        Department.objects.get_or_create(name=name, defaults={'description': desc})
        print(f"Ensured Department: {name}")

    # SLA Configs
    slas = [
        ('High', 1, 3), # 1 day for user, 3 for dept
        ('Medium', 3, 7), # 3 days for user, 7 for dept
        ('Low', 7, 14) # 7 days for user, 14 for dept
    ]
    for priority, user_days, dept_days in slas:
        SLAConfig.objects.get_or_create(
            priority=priority,
            defaults={
                'max_days_user': user_days,
                'max_days_department': dept_days
            }
        )
        print(f"Ensured SLA: {priority}")

if __name__ == '__main__':
    initialize()
