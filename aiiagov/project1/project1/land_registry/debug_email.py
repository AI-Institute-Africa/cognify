import os
import django
from django.core.mail import send_mail
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'land_registry.settings')
django.setup()

def test_email():
    print("Attempting to send test email...")
    print(f"SMTP Host: {settings.EMAIL_HOST}")
    print(f"SMTP Port: {settings.EMAIL_PORT}")
    print(f"User: {settings.EMAIL_HOST_USER}")
    
    recipient = 'confluencesystemspvtltd@gmail.com'
    try:
        send_mail(
            'RIFTS-X SMTP Diagnostic Test',
            'This is a diagnostic test to verify SMTP settings.',
            settings.EMAIL_HOST_USER, # Using the exact authenticated user as sender first
            [recipient],
            fail_silently=False,
        )
        print("SUCCESS: Email sent successfully!")
    except Exception as e:
        print(f"FAILURE: Could not send email. Error: {e}")

if __name__ == "__main__":
    test_email()
