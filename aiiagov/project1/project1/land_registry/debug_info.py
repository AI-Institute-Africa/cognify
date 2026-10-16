import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'land_registry.settings')
django.setup()
from django.contrib.auth.models import User
from registry.models import UserSecurity, ProjectPhase

output_path = r'c:\Users\USER 2\Downloads\project1\project1\land_registry\debug_results.txt'

with open(output_path, 'w') as f:
    f.write("USERS:\n")
    for u in User.objects.all():
        sec = UserSecurity.objects.filter(user=u).first()
        role = sec.role if sec else 'None'
        f.write(f"USER: {u.username} | ROLE: {role} | SUPER: {u.is_superuser}\n")
    
    f.write("\nPHASES:\n")
    for ph in ProjectPhase.objects.all():
        pm_name = ph.pm.username if ph.pm else 'None'
        f.write(f"PHASE: {ph.project.name} - {ph.name} | STATUS: {ph.status} | PM: {pm_name}\n")
