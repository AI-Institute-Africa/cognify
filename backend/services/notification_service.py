"""
Notification Service for Cognify
Handles Email (Resend) and WhatsApp notifications
"""
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ====================  EMAIL NOTIFICATIONS (RESEND) ====================

RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@cognify.edu')

async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    from_name: str = "Cognify"
) -> Dict[str, Any]:
    """Send email using Resend API"""
    try:
        import httpx
        
        if not RESEND_API_KEY:
            logger.warning("Resend API key not configured")
            return {"success": False, "error": "Email service not configured"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": f"{from_name} <{FROM_EMAIL}>",
                    "to": [to_email],
                    "subject": subject,
                    "html": html_content
                },
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                return {"success": True, "message_id": response.json().get('id')}
            else:
                logger.error(f"Resend API error: {response.status_code} - {response.text}")
                return {"success": False, "error": "Failed to send email"}
                
    except Exception as e:
        logger.error(f"Email sending error: {e}")
        return {"success": False, "error": str(e)}


# ====================  WHATSAPP NOTIFICATIONS (TWILIO) ====================

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_WHATSAPP_NUMBER = os.environ.get('TWILIO_WHATSAPP_NUMBER', '')

async def send_whatsapp(
    phone_number: str,
    message: str,
    template_name: Optional[str] = None,
    template_params: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Send WhatsApp message via Twilio
    """
    try:
        # Clean phone number and format for Zimbabwe
        clean_phone = phone_number.replace('+', '').replace(' ', '').replace('-', '')
        if clean_phone.startswith('0'):
            clean_phone = '263' + clean_phone[1:]  # Zimbabwe country code
        
        formatted_phone = f'+{clean_phone}'
        
        if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_WHATSAPP_NUMBER:
            # Production: Use Twilio WhatsApp API
            import httpx
            from base64 import b64encode
            
            auth_string = f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}"
            auth_header = b64encode(auth_string.encode()).decode()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json",
                    headers={
                        "Authorization": f"Basic {auth_header}",
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                    data={
                        "From": f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
                        "To": f"whatsapp:{formatted_phone}",
                        "Body": message
                    },
                    timeout=30
                )
                
                if response.status_code in [200, 201]:
                    response_data = response.json()
                    return {
                        "success": True,
                        "message_id": response_data.get('sid'),
                        "status": response_data.get('status')
                    }
                else:
                    logger.error(f"Twilio WhatsApp error: {response.status_code} - {response.text}")
                    return {"success": False, "error": f"WhatsApp message failed: {response.text}"}
        else:
            # Fallback: Generate wa.me link when Twilio not configured
            encoded_message = message.replace(' ', '%20').replace('\n', '%0A')
            whatsapp_link = f"https://wa.me/{clean_phone}?text={encoded_message}"
            
            logger.warning("Twilio not configured - generating wa.me link instead")
            return {
                "success": True,
                "method": "link",
                "whatsapp_link": whatsapp_link,
                "message": "Twilio not configured - wa.me link generated"
            }
            
    except Exception as e:
        logger.error(f"WhatsApp error: {e}")
        return {"success": False, "error": str(e)}


# ====================  NOTIFICATION TEMPLATES ====================

def get_email_template(template_type: str, **kwargs) -> Dict[str, str]:
    """Get email template by type"""
    templates = {
        "welcome": {
            "subject": "Welcome to Cognify! 🎓",
            "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1 style="color: #6366f1;">Welcome to Cognify!</h1>
                    <p>Hi {kwargs.get('name', 'there')},</p>
                    <p>Thank you for joining Cognify - Africa's leading AI-powered learning platform!</p>
                    <p>Start your learning journey today:</p>
                    <ul>
                        <li>Explore our courses</li>
                        <li>Meet your AI Personal Mentor</li>
                        <li>Join study groups</li>
                    </ul>
                    <a href="{kwargs.get('login_url', '#')}" style="display: inline-block; background: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px;">Get Started</a>
                    <p style="color: #666; margin-top: 20px;">Happy Learning!<br>The Cognify Team</p>
                </div>
            """
        },
        "course_enrolled": {
            "subject": f"You're enrolled! {kwargs.get('course_name', 'New Course')} 📚",
            "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1 style="color: #6366f1;">Enrollment Confirmed! 🎉</h1>
                    <p>Hi {kwargs.get('name', 'there')},</p>
                    <p>You're now enrolled in <strong>{kwargs.get('course_name', 'your course')}</strong>!</p>
                    <p>Your learning journey starts now. Here's what you can do:</p>
                    <ul>
                        <li>Watch the introduction video</li>
                        <li>Meet your classmates</li>
                        <li>Set your learning goals</li>
                    </ul>
                    <a href="{kwargs.get('course_url', '#')}" style="display: inline-block; background: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px;">Start Learning</a>
                    <p style="color: #666; margin-top: 20px;">Happy Learning!<br>The Cognify Team</p>
                </div>
            """
        },
        "payment_success": {
            "subject": "Payment Confirmed ✅",
            "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1 style="color: #10b981;">Payment Successful! ✅</h1>
                    <p>Hi {kwargs.get('name', 'there')},</p>
                    <p>Your payment of <strong>{kwargs.get('amount', '0')} {kwargs.get('currency', 'USD')}</strong> has been processed successfully.</p>
                    <p><strong>Reference:</strong> {kwargs.get('reference', 'N/A')}</p>
                    <p><strong>Course:</strong> {kwargs.get('course_name', 'N/A')}</p>
                    <p>You now have full access to your course. Start learning today!</p>
                    <a href="{kwargs.get('course_url', '#')}" style="display: inline-block; background: #10b981; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px;">Go to Course</a>
                </div>
            """
        },
        "assignment_reminder": {
            "subject": f"Assignment Due Soon: {kwargs.get('assignment_name', 'Assignment')} ⏰",
            "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1 style="color: #f59e0b;">Assignment Reminder ⏰</h1>
                    <p>Hi {kwargs.get('name', 'there')},</p>
                    <p>Don't forget! Your assignment <strong>{kwargs.get('assignment_name', 'assignment')}</strong> is due soon.</p>
                    <p><strong>Due Date:</strong> {kwargs.get('due_date', 'N/A')}</p>
                    <p><strong>Course:</strong> {kwargs.get('course_name', 'N/A')}</p>
                    <a href="{kwargs.get('assignment_url', '#')}" style="display: inline-block; background: #f59e0b; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px;">View Assignment</a>
                </div>
            """
        },
        "class_reminder": {
            "subject": f"Class Starting Soon: {kwargs.get('class_name', 'Class')} 🎥",
            "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1 style="color: #3b82f6;">Class Reminder 🎥</h1>
                    <p>Hi {kwargs.get('name', 'there')},</p>
                    <p>Your class <strong>{kwargs.get('class_name', 'class')}</strong> is starting in {kwargs.get('minutes_until', '15')} minutes!</p>
                    <p><strong>Time:</strong> {kwargs.get('class_time', 'N/A')}</p>
                    <p><strong>Teacher:</strong> {kwargs.get('teacher_name', 'N/A')}</p>
                    <a href="{kwargs.get('join_url', '#')}" style="display: inline-block; background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px;">Join Class</a>
                </div>
            """
        }
    }
    
    return templates.get(template_type, {"subject": "Cognify Notification", "html": "<p>You have a new notification.</p>"})


def get_whatsapp_message(template_type: str, **kwargs) -> str:
    """Get WhatsApp message template"""
    templates = {
        "welcome": f"🎓 Welcome to Cognify, {kwargs.get('name', 'there')}!\n\nYour AI-powered learning journey starts now. Explore courses, meet your AI mentor, and join study groups.\n\nStart learning: {kwargs.get('login_url', 'cognify.edu')}",
        
        "course_enrolled": f"📚 You're enrolled in {kwargs.get('course_name', 'your course')}!\n\nHi {kwargs.get('name', 'there')}, start your learning journey now.\n\nGo to course: {kwargs.get('course_url', '#')}",
        
        "payment_success": f"✅ Payment Confirmed!\n\nAmount: {kwargs.get('amount', '0')} {kwargs.get('currency', 'USD')}\nReference: {kwargs.get('reference', 'N/A')}\nCourse: {kwargs.get('course_name', 'N/A')}\n\nStart learning now!",
        
        "assignment_reminder": f"⏰ Assignment Due Soon!\n\n{kwargs.get('assignment_name', 'Assignment')}\nDue: {kwargs.get('due_date', 'Soon')}\nCourse: {kwargs.get('course_name', 'N/A')}\n\nSubmit now: {kwargs.get('assignment_url', '#')}",
        
        "class_reminder": f"🎥 Class Starting in {kwargs.get('minutes_until', '15')} minutes!\n\n{kwargs.get('class_name', 'Class')}\nTeacher: {kwargs.get('teacher_name', 'N/A')}\n\nJoin: {kwargs.get('join_url', '#')}"
    }
    
    return templates.get(template_type, "You have a new notification from Cognify.")


# ====================  NOTIFICATION DISPATCHER ====================

async def send_notification(
    user_id: str,
    notification_type: str,
    channels: List[str],  # ['email', 'whatsapp']
    template_type: str,
    template_data: Dict[str, Any],
    db
) -> Dict[str, Any]:
    """
    Send notification to user via specified channels
    """
    # Get user details
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        return {"success": False, "error": "User not found"}
    
    results = {}
    template_data['name'] = user.get('full_name', '').split()[0] if user.get('full_name') else 'there'
    
    # Send email
    if 'email' in channels and user.get('email'):
        email_template = get_email_template(template_type, **template_data)
        email_result = await send_email(
            to_email=user['email'],
            subject=email_template['subject'],
            html_content=email_template['html']
        )
        results['email'] = email_result
    
    # Send WhatsApp
    if 'whatsapp' in channels and user.get('phone'):
        whatsapp_message = get_whatsapp_message(template_type, **template_data)
        whatsapp_result = await send_whatsapp(
            phone_number=user['phone'],
            message=whatsapp_message
        )
        results['whatsapp'] = whatsapp_result
    
    # Store notification record
    notification_record = {
        "user_id": user_id,
        "type": notification_type,
        "template_type": template_type,
        "channels": channels,
        "results": results,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification_record)
    
    return {"success": True, "results": results}
