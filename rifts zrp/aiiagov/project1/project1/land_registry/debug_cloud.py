import os, sys, traceback
os.environ['DJANGO_SETTINGS_MODULE'] = 'land_registry.settings'
os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = '1'

import django
# Patch ALLOWED_HOSTS before setup
from django.conf import settings

django.setup()

# Override ALLOWED_HOSTS for the test
from django.conf import settings as djsettings
djsettings.ALLOWED_HOSTS = ['*']

from django.test import Client
from django.contrib.auth.models import User

c = Client(SERVER_NAME='127.0.0.1')

u = User.objects.filter(is_active=True).first()
if not u:
    print("ERROR: No active users")
    sys.exit(1)

print(f"Logging in as: {u.username}")
c.force_login(u)

print("\n=== GET /cloud/ ===")
try:
    resp = c.get('/cloud/')
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        content = resp.content.decode('utf-8', errors='replace')
        if 'Institutional Cloud Vault' in content:
            print("SUCCESS: Cloud dashboard rendered correctly")
        else:
            print("WARNING: mismatched title")
            print("First 500 chars:", content[:500])
    else:
        content = resp.content.decode('utf-8', errors='replace')
        import re
        # Extract exception value
        exc = re.search(r'exception_value["\s>]+([^<]{0,300})', content)
        if exc:
            print("DJANGO EXCEPTION:", exc.group(1).strip())
        # Extract traceback lines
        lines = re.findall(r'<code>(.*?)</code>', content)
        for l in lines[:10]:
            print("  TB:", l.strip()[:120])
        if not exc and not lines:
            print("Raw content:", content[:1200])
except Exception as e:
    traceback.print_exc()
