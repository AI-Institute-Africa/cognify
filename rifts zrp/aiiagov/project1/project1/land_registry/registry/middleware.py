import json
from .models import ForensicAudit, SecurityAlert, UserSecurity
from django.utils import timezone
from django.core.cache import cache

class ForensicAuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Capture IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        # 1. Unusual Activity Detection (Simple Rate Limiting)
        # Check for request frequency per IP/Session
        cache_key = f"req_count_{ip}"
        req_count = cache.get(cache_key, 0)
        if req_count > 50: # Trigger alert on >50 requests in 1 minute
            if not cache.get(f"alert_sent_{ip}"):
                SecurityAlert.objects.create(
                    alert_type="Unusual Activity Detected",
                    description=f"IP {ip} made over 50 requests in a short period.",
                    severity="High",
                    user=request.user if request.user.is_authenticated else None,
                    ip_address=ip
                )
                cache.set(f"alert_sent_{ip}", True, 300) # Cooldown for 5 mins
        cache.set(cache_key, req_count + 1, 60) # 1 minute window

        # 2. After-Hours Monitoring
        current_hour = timezone.now().hour
        if current_hour >= 18 or current_hour <= 7: # Between 6 PM and 8 AM
            if request.user.is_authenticated and not request.user.is_superuser:
                # Log a Medium severity alert for after-hours access
                # We use a cooldown to avoid flooding alerts for every single request
                alert_key = f"after_hours_alert_{request.user.id}"
                if not cache.get(alert_key):
                    SecurityAlert.objects.create(
                        alert_type="After-Hours Access",
                        description=f"User {request.user.username} accessed the system at {timezone.now()}",
                        severity="Medium",
                        user=request.user,
                        ip_address=ip
                    )
                    cache.set(alert_key, True, 3600) # Alert once per hour

        # Capture pre-request metadata
        response = self.get_response(request)

        # We log state-changing actions or high-value GET requests
        # High value GETs: download_bundle, certificates, cloud_file_view
        is_sensitive_get = request.method == 'GET' and any(tag in request.path for tag in ['download', 'view_file', 'cloud_file', 'certificate'])
        
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE'] or is_sensitive_get or request.path.startswith('/api/'):
            try:
                payload = None
                if request.method == 'POST':
                    # Sensitive fields filtering
                    data = request.POST.copy()
                    if 'password' in data:
                        data['password'] = '********'
                    if 'csrfmiddlewaretoken' in data:
                        del data['csrfmiddlewaretoken']
                    payload = dict(data)

                # Log to the forensic stream
                ForensicAudit.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action=f"Accessing {request.path}",
                    method=request.method,
                    path=request.path,
                    payload=payload,
                    ip_address=ip,
                    user_agent=request.META.get('HTTP_USER_AGENT'),
                    timestamp=timezone.now()
                )
            except Exception as e:
                # Forensic logging must NEVER crash the main thread
                print(f"Forensic Audit Error: {e}")

        return response
