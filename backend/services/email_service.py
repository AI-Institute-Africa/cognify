"""
Email Service using Resend API
Handles: Email verification, Password reset, Notifications
"""
import os
import asyncio
import logging
import random
import string
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Resend configuration
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')

# Initialize resend if API key is available
resend_client = None
if RESEND_API_KEY and RESEND_API_KEY != 're_test_placeholder':
    try:
        import resend
        resend.api_key = RESEND_API_KEY
        resend_client = resend
        logger.info("Resend email client initialized")
    except ImportError:
        logger.warning("Resend library not installed")
else:
    logger.warning("Resend API key not configured - emails will be simulated")


def generate_verification_code(length: int = 6) -> str:
    """Generate a random numeric verification code"""
    return ''.join(random.choices(string.digits, k=length))


def generate_reset_token(length: int = 32) -> str:
    """Generate a secure reset token"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


async def send_email(to_email: str, subject: str, html_content: str) -> dict:
    """
    Send email using Resend API
    Returns: {"success": bool, "message": str, "email_id": str|None}
    """
    if not resend_client:
        # Simulate email sending for development/testing
        logger.info(f"[SIMULATED EMAIL] To: {to_email}, Subject: {subject}")
        return {
            "success": True,
            "message": "Email simulated (Resend not configured)",
            "email_id": f"sim_{datetime.now(timezone.utc).timestamp()}"
        }
    
    params = {
        "from": SENDER_EMAIL,
        "to": [to_email],
        "subject": subject,
        "html": html_content
    }
    
    try:
        # Run sync SDK in thread to keep FastAPI non-blocking
        email = await asyncio.to_thread(resend_client.Emails.send, params)
        return {
            "success": True,
            "message": f"Email sent to {to_email}",
            "email_id": email.get("id")
        }
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return {
            "success": False,
            "message": str(e),
            "email_id": None
        }


async def send_verification_email(to_email: str, verification_code: str, user_name: str = "User") -> dict:
    """Send email verification code"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; padding: 40px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ font-size: 28px; font-weight: bold; color: #3B82F6; }}
            .code {{ font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #1E40AF; 
                     background: #EFF6FF; padding: 20px; border-radius: 10px; text-align: center; margin: 30px 0; }}
            .message {{ color: #4B5563; line-height: 1.6; }}
            .footer {{ margin-top: 30px; text-align: center; color: #9CA3AF; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🎓 Cognify</div>
                <p>AI-Powered Education Platform</p>
            </div>
            <p class="message">Hello {user_name},</p>
            <p class="message">Welcome to Cognify! Please use the following verification code to complete your registration:</p>
            <div class="code">{verification_code}</div>
            <p class="message">This code will expire in 15 minutes.</p>
            <p class="message">If you didn't request this verification, please ignore this email.</p>
            <div class="footer">
                <p>© 2026 Cognify - AI Institute Africa</p>
                <p>Transforming Education Across Africa</p>
            </div>
        </div>
    </body>
    </html>
    """
    return await send_email(to_email, "Verify Your Cognify Account", html_content)


async def send_password_reset_email(to_email: str, reset_code: str, user_name: str = "User") -> dict:
    """Send password reset email"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; padding: 40px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ font-size: 28px; font-weight: bold; color: #3B82F6; }}
            .code {{ font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #DC2626; 
                     background: #FEF2F2; padding: 20px; border-radius: 10px; text-align: center; margin: 30px 0; }}
            .message {{ color: #4B5563; line-height: 1.6; }}
            .warning {{ color: #DC2626; font-weight: bold; }}
            .footer {{ margin-top: 30px; text-align: center; color: #9CA3AF; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🎓 Cognify</div>
                <p>Password Reset Request</p>
            </div>
            <p class="message">Hello {user_name},</p>
            <p class="message">We received a request to reset your password. Use this code to reset your password:</p>
            <div class="code">{reset_code}</div>
            <p class="message">This code will expire in 30 minutes.</p>
            <p class="warning">If you didn't request a password reset, please ignore this email and your password will remain unchanged.</p>
            <div class="footer">
                <p>© 2026 Cognify - AI Institute Africa</p>
            </div>
        </div>
    </body>
    </html>
    """
    return await send_email(to_email, "Reset Your Cognify Password", html_content)


async def send_enrollment_confirmation_email(to_email: str, user_name: str, org_name: str, role: str, temp_password: str = None) -> dict:
    """Send enrollment confirmation to new org participants"""
    password_section = ""
    if temp_password:
        password_section = f"""
        <p class="message">Your temporary password is:</p>
        <div class="code" style="font-size: 20px; letter-spacing: 2px;">{temp_password}</div>
        <p class="warning">Please change your password after first login.</p>
        """
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; padding: 40px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ font-size: 28px; font-weight: bold; color: #3B82F6; }}
            .code {{ font-size: 24px; font-weight: bold; color: #059669; 
                     background: #ECFDF5; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0; }}
            .message {{ color: #4B5563; line-height: 1.6; }}
            .warning {{ color: #DC2626; }}
            .footer {{ margin-top: 30px; text-align: center; color: #9CA3AF; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🎓 Cognify</div>
                <p>Welcome to {org_name}!</p>
            </div>
            <p class="message">Hello {user_name},</p>
            <p class="message">You have been enrolled as a <strong>{role}</strong> at <strong>{org_name}</strong> on Cognify.</p>
            {password_section}
            <p class="message">You can now access your account and start your learning journey!</p>
            <div class="footer">
                <p>© 2026 Cognify - AI Institute Africa</p>
            </div>
        </div>
    </body>
    </html>
    """
    return await send_email(to_email, f"Welcome to {org_name} - Cognify", html_content)


async def send_notification_email(to_email: str, user_name: str, notification_title: str, notification_body: str) -> dict:
    """Send general notification email"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; padding: 40px; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ font-size: 28px; font-weight: bold; color: #3B82F6; }}
            .title {{ font-size: 20px; font-weight: bold; color: #1F2937; margin: 20px 0; }}
            .message {{ color: #4B5563; line-height: 1.6; }}
            .footer {{ margin-top: 30px; text-align: center; color: #9CA3AF; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🎓 Cognify</div>
            </div>
            <p class="message">Hello {user_name},</p>
            <div class="title">{notification_title}</div>
            <p class="message">{notification_body}</p>
            <div class="footer">
                <p>© 2026 Cognify - AI Institute Africa</p>
            </div>
        </div>
    </body>
    </html>
    """
    return await send_email(to_email, notification_title, html_content)


async def send_magic_link_email(to_email: str, magic_link: str, org_name: str, course_name: str, expires_hours: int = 72) -> dict:
    """Send magic link for bulk enrollment - one-time login to set password"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #0f172a; padding: 20px; color: #e2e8f0; }}
            .container {{ max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-radius: 16px; padding: 40px; border: 1px solid rgba(59, 130, 246, 0.3); }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .logo {{ font-size: 32px; font-weight: bold; background: linear-gradient(135deg, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
            .tagline {{ color: #94a3b8; font-size: 14px; margin-top: 8px; }}
            .message {{ color: #cbd5e1; line-height: 1.8; margin: 16px 0; }}
            .highlight {{ color: #60a5fa; font-weight: 600; }}
            .button-container {{ text-align: center; margin: 32px 0; }}
            .button {{ display: inline-block; background: linear-gradient(135deg, #3b82f6, #8b5cf6); color: white; padding: 16px 40px; border-radius: 12px; text-decoration: none; font-weight: 600; font-size: 16px; }}
            .link-fallback {{ background: #1e293b; border-radius: 8px; padding: 16px; margin: 20px 0; word-break: break-all; font-size: 12px; color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.2); }}
            .info-box {{ background: rgba(59, 130, 246, 0.1); border-left: 4px solid #3b82f6; padding: 16px; border-radius: 0 8px 8px 0; margin: 24px 0; }}
            .info-box p {{ margin: 4px 0; font-size: 14px; color: #94a3b8; }}
            .warning {{ color: #f59e0b; font-size: 13px; margin-top: 16px; }}
            .footer {{ margin-top: 32px; text-align: center; color: #64748b; font-size: 12px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 24px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">Cognify</div>
                <p class="tagline">AI-Powered Learning Platform</p>
            </div>
            
            <p class="message">Hello!</p>
            <p class="message">You've been invited to join <span class="highlight">{org_name}</span> on Cognify.</p>
            
            <div class="info-box">
                <p><strong>Organization:</strong> {org_name}</p>
                <p><strong>Course:</strong> {course_name}</p>
            </div>
            
            <p class="message">Click the button below to set up your account and start learning:</p>
            
            <div class="button-container">
                <a href="{magic_link}" class="button">Set Up My Account</a>
            </div>
            
            <p class="message" style="font-size: 13px;">Or copy and paste this link into your browser:</p>
            <div class="link-fallback">{magic_link}</div>
            
            <p class="warning">⏰ This link expires in {expires_hours} hours.</p>
            
            <div class="footer">
                <p>© 2026 Cognify - AI Institute Africa</p>
                <p>Transforming Education Across Africa</p>
            </div>
        </div>
    </body>
    </html>
    """
    return await send_email(to_email, f"You're invited to join {org_name} on Cognify!", html_content)
