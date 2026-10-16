import ssl
from django.core.mail.backends.smtp import EmailBackend

class InsecureEmailBackend(EmailBackend):
    """
    Subclass of Django's SMTP EmailBackend that bypasses SSL certificate verification.
    Useful for development environments with SSL/TLS configuration issues.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Create a custom SSL context that doesn't verify certificates
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    @property
    def connection_class(self):
        # We need to ensure the connection class uses our context
        # But for starttls, it's actually handled in the open() method
        return super().connection_class

    def open(self):
        if self.connection:
            return False
        try:
            connection_class = self.connection_class
            self.connection = connection_class(self.host, self.port, timeout=self.timeout)
            
            if self.use_tls:
                # This is where we pass our insecure context
                self.connection.starttls(context=self.ssl_context)
                
            if self.username and self.password:
                self.connection.login(self.username, self.password)
                
            return True
        except Exception:
            if not self.fail_silently:
                raise
            return False

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        from django.conf import settings
        from django.core.mail import EmailMultiAlternatives
        import datetime
        import re

        default_from = getattr(settings, 'DEFAULT_FROM_EMAIL', '')

        for i, msg in enumerate(email_messages):
            # 1. Standardize From header to prevent spoofing/misalignment flags
            if not msg.from_email or msg.from_email == 'webmaster@localhost' or '@' not in msg.from_email:
                msg.from_email = default_from

            if 'takudzwasamuelc@gmail.com' not in msg.from_email:
                msg.from_email = default_from

            # 2. Inject anti-spam headers
            if not msg.extra_headers:
                msg.extra_headers = {}
            msg.extra_headers['Auto-Submitted'] = 'auto-generated'
            msg.extra_headers['X-Auto-Response-Suppress'] = 'All'

            # 3. Upgrade plain-text notifications to HTML multi-part
            has_html = False
            if hasattr(msg, 'alternatives'):
                for _, mimetype in msg.alternatives:
                    if mimetype == 'text/html':
                        has_html = True
                        break

            if not has_html and msg.body:
                # Convert to EmailMultiAlternatives if it's a basic EmailMessage
                if not hasattr(msg, 'attach_alternative'):
                    new_msg = EmailMultiAlternatives(
                        subject=msg.subject,
                        body=msg.body,
                        from_email=msg.from_email,
                        to=msg.to,
                        bcc=msg.bcc,
                        headers=msg.extra_headers,
                        cc=msg.cc,
                        reply_to=msg.reply_to,
                    )
                    new_msg.attachments = msg.attachments
                    msg = new_msg
                    email_messages[i] = msg

                # Clean paragraphs and format URLs
                paragraphs = msg.body.strip().split('\n\n')
                html_paragraphs = []
                for p in paragraphs:
                    lines = p.split('\n')
                    html_lines = []
                    for line in lines:
                        # Find URLs and wrap them in styled anchor tags
                        url_pattern = re.compile(r'(https?://\S+)')
                        line_with_links = url_pattern.sub(
                            r'<a href="\1" style="background-color: #003EA6; color: #ffffff; text-decoration: none; padding: 10px 20px; border-radius: 20px; display: inline-block; font-weight: bold; font-size: 14px; margin: 8px 0;">Open Transaction Link &rarr;</a><br><span style="font-size: 11px; color: #64748b; word-break: break-all;">\1</span>',
                            line
                        )
                        html_lines.append(line_with_links)
                    html_paragraphs.append(
                        '<p style="margin: 0 0 16px 0; line-height: 1.6; color: #1e293b; font-size: 15px;">'
                        + '<br>'.join(html_lines)
                        + '</p>'
                    )

                body_html = '\n'.join(html_paragraphs)
                year = datetime.datetime.now().year

                html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #060d1f; margin: 0; padding: 40px 20px;">
    <table cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #060d1f;">
        <tr>
            <td align="center">
                <table cellpadding="0" cellspacing="0" border="0" width="100%" style="max-width: 620px; background-color: #ffffff; border-radius: 14px; overflow: hidden; box-shadow: 0 8px 24px rgba(0,0,0,0.25); border: 2px solid #003EA6;">
                    <!-- ZRP Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #003EA6, #002070); padding: 24px 32px; text-align: left; border-bottom: 4px solid #D4AF37;">
                            <table cellpadding="0" cellspacing="0" border="0" width="100%">
                                <tr>
                                    <td>
                                        <div style="color: #ffffff; font-size: 20px; font-weight: 800; letter-spacing: 0.5px;">Zimbabwe Republic Police</div>
                                        <div style="color: #D4AF37; font-size: 13px; font-weight: 700; margin-top: 2px;">ZRP Integrated Management System (ZRP-IMS)</div>
                                    </td>
                                    <td align="right">
                                        <span style="background-color: rgba(212, 175, 55, 0.2); border: 1px solid #D4AF37; color: #ffffff; padding: 6px 12px; border-radius: 12px; font-size: 11px; font-weight: bold;">OFFICIAL NOTIFICATION</span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 36px 32px 28px 32px; text-align: left;">
                            {body_html}
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 24px 32px; background-color: #f8fafc; border-top: 1px solid #e2e8f0; text-align: center;">
                            <p style="margin: 0 0 6px 0; font-size: 12px; font-weight: bold; color: #003EA6;">
                                Zimbabwe Republic Police &bull; Harare, Zimbabwe
                            </p>
                            <p style="margin: 0; font-size: 11px; color: #64748b; line-height: 1.5;">
                                Automated notification from <strong>ZRP-IMS</strong>. Please do not reply directly.<br>
                                &copy; {year} <strong>Zimbabwe Republic Police</strong>. All Rights Reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""
                msg.attach_alternative(html_content, "text/html")

        return super().send_messages(email_messages)
