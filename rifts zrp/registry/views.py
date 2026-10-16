import re
import datetime
from datetime import timedelta
from django.utils import timezone
import secrets
import string
import random
import hashlib
import time
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
import json
import os
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden, FileResponse, Http404
from django.http import HttpResponseRedirect
from urllib.parse import quote as urlquote
from django.db import transaction
import logging
from django.db.models import Q, Sum, Count
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from . import models, forms
from .models import (
    File, Borrow, Department, CustodyLog, UserSecurity, SecurityAlert, 
    KnowledgeEntry, KnowledgeVersion, KnowledgeTag, Organization, BRD, BRDSignature
)
from .forms import (
    SaveUser, GovernanceRegistrationForm, BenefitForm, 
    SaveServiceTicket, TicketUpdateForm
)
from django.http import HttpResponseBadRequest, JsonResponse
from rest_framework.decorators import api_view
from .utils.intelligence import AIGovernor
from .services.ai_assistant import AIAssistantService

logger = logging.getLogger(__name__)

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from .services.scanner import ScannerService
from .services.cloud import CloudService, DocxHTMLParser
from .services.sla import SLAManager
from .services.risk import RiskEngine
from .services.custody import CustodyService
from .services.onlyoffice_service import OnlyOfficeService, download_edited_document
from django.utils.html import strip_tags
import html
import threading
from django.db import close_old_connections

import zipfile
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from docx import Document
import tempfile
try:
    import mammoth
except Exception:
    mammoth = None

try:
    import pypandoc
except Exception:
    pypandoc = None

from .services.permissions import PermissionService, PM_ROLES


def context_data(request):
    fullpath = request.get_full_path()
    abs_uri = request.build_absolute_uri()
    abs_uri = abs_uri.split(fullpath)[0]
    context = {
        'system_host' : abs_uri,
        'page_name' : '',
        'page_title' : '',
        'system_name' : 'RIFTS-X Zimbabwe Republic Police',
        'org_name': 'Zimbabwe Republic Police',
        'topbar' : True,
        'footer' : True,
        'today' : timezone.now(),
        'riftsx_url': getattr(settings, 'RIFTSX_BASE_URL', 'http://127.0.0.1:8000'),
        'governance_url': getattr(settings, 'GOVERNANCE_BASE_URL', 'http://127.0.0.1:8000/projects/'),
    }

    if request.user.is_authenticated:
        security_profile, created = UserSecurity.objects.get_or_create(user=request.user)
        context['user_role'] = security_profile.role
        context['security_profile'] = security_profile

        user_dept = security_profile.department
        context['user_dept'] = user_dept
        context['dept_name'] = user_dept.name if user_dept else "General Registry"
        context['all_departments'] = models.Department.objects.all().order_by('name')

        # ── Grade Level Hierarchy (Officer, Manager, Director, Chief Director/Executive Secretary) ──
        role_lower = (security_profile.role or '').lower()
        is_super = request.user.is_superuser
        
        context['is_officer'] = 'officer' in role_lower or 'staff' in role_lower or (not is_super and not any(r in role_lower for r in ['manager', 'director', 'executive', 'chief']))
        context['is_manager'] = 'manager' in role_lower or 'supervisor' in role_lower or 'head' in role_lower
        context['is_director'] = 'director' in role_lower and 'chief' not in role_lower
        context['is_exec_secretary'] = 'chief director' in role_lower or 'executive secretary' in role_lower or 'commissioner' in role_lower or is_super

        # ── Governance Permissions (comprehensive) ──
        context['can_create_project']      = PermissionService.can_create_project(request.user)
        context['can_view_financials']     = PermissionService.can_view_financials(request.user)
        context['can_post_comment']        = PermissionService.can_post_comment(request.user)
        context['can_view_org_dashboard']  = PermissionService.can_view_org_dashboard(request.user)
        context['can_view_dept_projects']  = PermissionService.can_view_dept_projects(request.user)
        context['can_reassign_task']       = PermissionService.can_reassign_task(request.user)
        context['is_team_member_only']     = PermissionService.is_team_member_only(request.user)
        context['is_pm_or_above']          = PermissionService.is_pm_or_above(request.user)
        context['is_exec_or_above']        = PermissionService.is_exec_or_above(request.user)

        # ── ZRP Hierarchy Roles & Statutory Stores Scoping ──
        user_province = security_profile.province or ''
        context['user_province'] = user_province
        role_raw = security_profile.role or 'General Police'
        context['user_role'] = role_raw
        context['can_sign_form27_electronic'] = (
            is_super or
            role_raw in [
                'Supt ICT', 'Chief Tech', 'System Manager', 'Systems Manager', 'Provincial ICT Officer',
                'Deputy Director Communications', 'Deputy Director IT', 'Deputy Director ICT', 'Chief Director'
            ]
        )
        context['is_supt_ict'] = (role_raw == 'Supt ICT')
        context['is_chief_tech'] = (role_raw == 'Chief Tech')
        context['is_system_manager'] = (role_raw in ['System Manager', 'Systems Manager'])
        context['is_picto'] = (role_raw == 'Provincial ICT Officer')
        context['is_deputy_director_comms'] = (role_raw == 'Deputy Director Communications')
        context['is_deputy_director_it'] = (role_raw in ['Deputy Director IT', 'Deputy Director ICT'])
        context['is_deputy_director_ict'] = (role_raw in ['Deputy Director IT', 'Deputy Director ICT'])
        context['is_deputy_director'] = (role_raw in ['Deputy Director Communications', 'Deputy Director IT', 'Deputy Director ICT'])
        context['is_management_tier'] = (role_raw in ['System Manager', 'Systems Manager', 'Supt ICT', 'Chief Tech'])
        context['is_chief_director'] = (role_raw == 'Chief Director') or (is_super and not role_raw)
        context['is_general_police'] = (role_raw in ['General Police', 'Officer', 'Clerk'])

    return context


def docx_version_to_html(version):
    # Prefer mammoth for high-fidelity DOCX -> HTML conversion if available
    version.file_content.open('rb')
    try:
        data = version.file_content.read()
        if mammoth:
            try:
                result = mammoth.convert_to_html(BytesIO(data))
                return result.value
            except Exception:
                pass

        # Fallback: simple conversion using python-docx (less fidelity)
        document = Document(BytesIO(data))
        html_lines = []
        for paragraph in document.paragraphs:
            paragraph_text = ''
            for run in paragraph.runs:
                run_text = html.escape(run.text)
                if run.bold:
                    run_text = f'<strong>{run_text}</strong>'
                if run.italic:
                    run_text = f'<em>{run_text}</em>'
                if run.underline:
                    run_text = f'<u>{run_text}</u>'
                paragraph_text += run_text

            tag = 'p'
            style_name = paragraph.style.name.lower() if paragraph.style else ''
            if 'heading 1' in style_name:
                tag = 'h1'
            elif 'heading 2' in style_name:
                tag = 'h2'
            elif 'heading 3' in style_name:
                tag = 'h3'
            elif 'list bullet' in style_name:
                tag = 'p'
            elif 'list number' in style_name:
                tag = 'p'

            html_lines.append(f'<{tag}>{paragraph_text}</{tag}>')

        return '\n'.join(html_lines)
    finally:
        version.file_content.close()


def userregister(request):
    context = context_data(request)
    context['topbar'] = False
    context['footer'] = False
    context['page_title'] = "User Registration"
    context['departments'] = models.Department.objects.all()
    if request.user.is_authenticated:
        return redirect("home-page")
    return render(request, 'register.html', context)

def save_register(request):
    resp = {'status': 'failed', 'msg': '', 'email_sent': False}
    if not request.method == 'POST':
        resp['msg'] = "No data has been sent on this request"
    else:
        form = forms.SaveUser(request.POST)
        if form.is_valid():
            import uuid
            user = form.save()

            # Update UserSecurity profile created by signal
            security = user.security_profile
            requested_role = form.cleaned_data.get('requested_role')
            security.platform = form.cleaned_data.get('platform')
            security.role = requested_role
            security.role_requested = requested_role
            security.department = form.cleaned_data.get('department')
            security.job_title = form.cleaned_data.get('job_title')
            security.position = form.cleaned_data.get('position')
            security.is_role_approved = False
            security.email_verification_token = str(uuid.uuid4())
            if security.platform == 'RIFTS-X':
                security.mfa_enabled = True
            security.save()

            platform_url = settings.GOVERNANCE_BASE_URL if security.platform == 'Governance' else settings.RIFTSX_BASE_URL
            verify_url = f"{settings.RIFTSX_BASE_URL.rstrip('/')}/verify-email/{security.email_verification_token}"

            # Always print to server console as admin fallback
            print(f"\n{'='*60}")
            print(f"[{security.platform}] REGISTRATION VERIFICATION for '{user.username}'")
            print(f"  Email    : {user.email}")
            print(f"  Platform : {security.platform}")
            print(f"  Role     : {security.role}")
            print(f"  Link     : {verify_url}")
            print(f"{'='*60}\n")

            subject = f"Verify your {security.platform} Account"
            html_message = f"""
            <html><body style="font-family:Arial,sans-serif;background:#f4f6f9;padding:30px;">
            <div style="max-width:560px;margin:auto;background:#fff;border-radius:10px;padding:36px;box-shadow:0 2px 12px rgba(0,0,0,.08);">
                <h2 style="color:#1a237e;margin-bottom:4px;">Account Verification</h2>
                <p style="color:#555;font-size:15px;">Hello <strong>{user.get_full_name() or user.username}</strong>,</p>
                <p style="color:#555;font-size:15px;">
                    Thank you for registering on the <strong>{security.platform}</strong> platform as
                    <strong>{security.role}</strong>. Please click the button below to verify your
                    email address and activate your account.
                </p>
                <div style="text-align:center;margin:32px 0;">
                    <a href="{verify_url}"
                       style="background:#1a237e;color:#fff;padding:14px 36px;border-radius:50px;
                              font-size:16px;font-weight:bold;text-decoration:none;display:inline-block;">
                        &#10003;&nbsp; Verify My Email
                    </a>
                </div>
                <p style="color:#888;font-size:13px;">Or copy and paste this link into your browser:</p>
                <p style="font-size:12px;word-break:break-all;color:#1a237e;">{verify_url}</p>
                <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
                <p style="color:#aaa;font-size:12px;text-align:center;">
                    If you did not register on {security.platform}, please ignore this email.
                </p>
            </div></body></html>
            """
            plain_message = (
                f"Hello {user.username},\n\n"
                f"Please verify your email by clicking the link below:\n\n"
                f"{verify_url}\n\n"
                f"Platform: {security.platform} | Role: {security.role}\n"
                f"System URL: {platform_url}"
            )

            email_sent = False
            try:
                from django.core.mail import EmailMultiAlternatives
                msg = EmailMultiAlternatives(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                )
                msg.attach_alternative(html_message, "text/html")
                msg.send(fail_silently=False)
                email_sent = True
            except Exception as e:
                print(f"[EMAIL ERROR] Could not send verification to {user.email}: {e}")

            resp['status'] = 'success'
            resp['email_sent'] = email_sent
            resp['user_email'] = user.email
            resp['platform'] = security.platform
            resp['verify_url'] = verify_url
        else:
            for field in form:
                for error in field.errors:
                    if resp['msg'] != '':
                        resp['msg'] += '<br />'
                    resp['msg'] += f"[{field.name}] {error}."

    return HttpResponse(json.dumps(resp), content_type="application/json")


def governance_register(request):
    """Separate registration page for Governance users."""
    context = context_data(request)
    context['topbar'] = False
    context['footer'] = False
    context['page_title'] = "Governance Registration"
    context['departments'] = models.Department.objects.all()
    if request.user.is_authenticated:
        return redirect("home-page")
    return render(request, 'governance/register.html', context)


def save_governance_register(request):
    """Processes Governance specific registration."""
    resp = {'status': 'failed', 'msg': ''}
    if not request.method == 'POST':
        resp['msg'] = "No data has been sent on this request"
    else:
        form = GovernanceRegistrationForm(request.POST)
        if form.is_valid():
            import uuid
            user = form.save()

            security = user.security_profile
            requested_role = form.cleaned_data.get('requested_role')
            security.platform = 'Governance'
            security.role = requested_role
            security.role_requested = requested_role
            security.department = form.cleaned_data.get('department')
            security.job_title = form.cleaned_data.get('job_title')
            security.position = form.cleaned_data.get('position')

            # Tiered approval flags
            security.is_role_approved = False
            security.is_pm_approved = False

            security.email_verification_token = str(uuid.uuid4())
            security.save()

            # Send Verification Email
            platform_url = settings.GOVERNANCE_BASE_URL
            verify_url = f"{settings.RIFTSX_BASE_URL.rstrip('/')}/verify-email/{security.email_verification_token}"

            print(f"\n{'='*60}")
            print(f"[GOVERNANCE] EMAIL VERIFICATION LINK for '{user.username}'")
            print(f"  Role Requested : {requested_role}")
            print(f"  Link           : {verify_url}")
            print(f"{'='*60}\n")

            subject = "Confirm your Governance Strategic Registration"
            message = f"Hello {user.username},\n\nPlease confirm your registration as {security.role} on the Governance platform by clicking the link below:\n\n{verify_url}\n\nSystem URL: {platform_url}\n\nNote: Your account will require approval from the MD (for strategic roles) or PM (for team members) after email verification."

            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=True,
                )
            except Exception:
                pass

            resp['status'] = 'success'
            resp['verify_url'] = verify_url
            messages.success(request, "Governance registration successful! Please verify your email.")
        else:
            for field in form:
                for error in field.errors:
                    if resp['msg'] != '':
                        resp['msg'] += '<br />'
                    resp['msg'] += f"[{field.name}] {error}."

    return HttpResponse(json.dumps(resp), content_type="application/json")


@login_required
def pm_manage_members(request):
    """PL-only: Review and approve Team Members for their department."""
    security = getattr(request.user, 'security_profile', None)
    if not (request.user.is_superuser or (security and security.role == 'Project Leader')):
        messages.error(request, "Access Denied: Only Project Leaders can approve Team Members.")
        return redirect('home-page')

    context = context_data(request)
    context['page_title'] = "Team Member Approval"

    # PLs approve Team Members in their department who have verified emails but not yet approved
    pending_members = UserSecurity.objects.filter(
        role_requested='Team Member',
        is_pm_approved=False,
        is_email_verified=True,
        department=security.department if security else None
    ).select_related('user')

    context['pending_members'] = pending_members
    return render(request, 'governance/pm_manage_members.html', context)


@login_required
def pm_member_action(request):
    """Processes PL approval/rejection of Team Members."""
    if request.method != 'POST':
        return redirect('pm-manage-members')

    security = getattr(request.user, 'security_profile', None)
    if not (request.user.is_superuser or (security and security.role == 'Project Leader')):
        return HttpResponseForbidden("Access Denied")

    action = request.POST.get('action')
    user_id = request.POST.get('user_id')

    target_security = get_object_or_404(UserSecurity, user_id=user_id)

    if action == 'approve':
        target_security.is_pm_approved = True
        target_security.role = 'Team Member'
        target_security.role_approved_by = request.user
        target_security.role_approved_at = timezone.now()
        target_security.save()
        messages.success(request, f"✅ Team Member '{target_security.user.username}' approved.")
    elif action == 'reject':
        target_security.user.is_active = False
        target_security.user.save()
        messages.warning(request, f"⛔ Team Member '{target_security.user.username}' rejected and deactivated.")

    return redirect('pm-manage-members')

@login_required
def update_profile(request):
    context = context_data(request)
    context['page_title'] = 'Update Profile'
    user = User.objects.get(id = request.user.id)
    if not request.method == 'POST':
        form = forms.UpdateProfile(instance=user)
        context['form'] = form
        print(form)
    else:
        form = forms.UpdateProfile(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile has been updated")
            return redirect("profile-page")
        else:
            context['form'] = form
            
    return render(request, 'manage_profile.html',context)

@login_required
def update_password(request):
    context =context_data(request)
    context['page_title'] = "Update Password"
    if request.method == 'POST':
        form = forms.UpdatePasswords(user = request.user, data= request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"Your Account Password has been updated successfully")
            update_session_auth_hash(request, form.user)
            return redirect("profile-page")
        else:
            context['form'] = form
    else:
        form = forms.UpdatePasswords(user=request.user)
        context['form'] = form
    return render(request,'update_password.html',context)

def verify_email(request, token):
    try:
        security = UserSecurity.objects.get(email_verification_token=token)
        security.is_email_verified = True
        security.email_verification_token = "" # Clear token after use
        security.save()
        messages.success(request, "Email verified successfully! You can now login.")
    except UserSecurity.DoesNotExist:
        # Link was either already clicked (pre-scanned) or is invalid
        messages.info(request, "Email already verified or the link has expired. Please try to login.")
    
    return redirect("login-page")


def resend_verification(request):
    """Resend verification email to a user who hasn't verified yet.
    Accepts POST with 'username' field. Returns JSON."""
    import uuid
    resp = {'status': 'failed', 'msg': ''}
    if request.method != 'POST':
        resp['msg'] = 'Invalid request method.'
        return HttpResponse(json.dumps(resp), content_type='application/json')

    username = request.POST.get('username', '').strip()
    if not username:
        resp['msg'] = 'Please enter your username so we can resend the verification email.'
        return HttpResponse(json.dumps(resp), content_type='application/json')

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        # Don't reveal if the user exists or not
        resp['status'] = 'success'
        resp['msg'] = 'If that username exists and is unverified, a new verification email has been sent.'
        return HttpResponse(json.dumps(resp), content_type='application/json')

    security = getattr(user, 'security_profile', None)
    if not security:
        resp['status'] = 'success'
        resp['msg'] = 'If that username exists and is unverified, a new verification email has been sent.'
        return HttpResponse(json.dumps(resp), content_type='application/json')

    if security.is_email_verified:
        resp['status'] = 'success'
        resp['msg'] = 'Your email is already verified. Please login normally.'
        return HttpResponse(json.dumps(resp), content_type='application/json')

    if not user.email:
        resp['msg'] = 'No email address found on your account. Please contact the administrator.'
        return HttpResponse(json.dumps(resp), content_type='application/json')

    # Generate a fresh token
    security.email_verification_token = str(uuid.uuid4())
    security.save()

    verify_url = f"{settings.RIFTSX_BASE_URL.rstrip('/')}/verify-email/{security.email_verification_token}"
    platform_url = settings.GOVERNANCE_BASE_URL if security.platform == 'Governance' else settings.RIFTSX_BASE_URL

    # Always print to server console as admin fallback
    print(f"\n{'='*60}")
    print(f"[RESEND] EMAIL VERIFICATION LINK for '{user.username}'")
    print(f"  Email    : {user.email}")
    print(f"  Platform : {security.platform}")
    print(f"  Link     : {verify_url}")
    print(f"{'='*60}\n")

    subject = f"[Resent] Confirm your {security.platform} Registration"
    message = (
        f"Hello {user.username},\n\n"
        f"You requested a new verification link. "
        f"Please confirm your email by clicking the link below:\n\n"
        f"{verify_url}\n\n"
        f"This link will remain valid until you click it.\n\n"
        f"System URL: {platform_url}"
    )

    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,  # Raise so we can catch and report the error
        )
        resp['status'] = 'success'
        resp['msg'] = f'A new verification link has been sent to {user.email}. Please check your inbox (and spam folder).'
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send verification to {user.email}: {e}")
        resp['msg'] = (
            f'Could not send the email automatically. '
            f'Please contact your administrator and provide this link: {verify_url}'
        )

    return HttpResponse(json.dumps(resp), content_type='application/json')

# Create your views here.
def login_page(request):
    context = context_data(request)
    context['topbar'] = False
    context['footer'] = False
    context['page_name'] = 'login'
    context['page_title'] = 'Login'
    context['next'] = request.GET.get('next', '')
    return render(request, 'login.html', context)

def login_user(request):
    logout(request)
    resp = {"status":'failed','msg':'', 'mfa_required': False}
    username = ''
    password = ''
    next_page = ''
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']
        next_page = request.POST.get('next', '')

        user = authenticate(username=username, password=password)
        if user is not None:
            security_profile, created = UserSecurity.objects.get_or_create(user=user)
            
            # 1. Check Email Verification (superusers are always exempt)
            if not security_profile.is_email_verified and not user.is_superuser:
                # Print a fresh verify link to console so admin can forward it
                token = security_profile.email_verification_token
                if token:
                    verify_url = f"{settings.RIFTSX_BASE_URL.rstrip('/')}/verify-email/{token}"
                    print(f"\n[{security_profile.platform}] UNVERIFIED LOGIN ATTEMPT — '{user.username}'")
                    print(f"  Email            : {user.email}")
                    print(f"  Verification Link: {verify_url}\n")
                resp['msg'] = (
                    "Your email address has not been verified yet. "
                    "Please check your inbox (including spam/junk folder) for the verification email. "
                    "If you did not receive it, use the 'Resend Verification Email' button below."
                )
                resp['email_unverified'] = True
                resp['username'] = username
                return HttpResponse(json.dumps(resp), content_type='application/json')
            
            if user.is_active:
                # 2. Check for Forced MFA (Governance & RIFTS-X platforms) or Optional MFA
                if security_profile.platform in ('Governance', 'RIFTS-X') or security_profile.mfa_enabled:
                    # Generate OTP (6 digits)
                    import random, string, threading
                    otp = ''.join(random.choices(string.digits, k=6))
                    security_profile.mfa_code = otp
                    security_profile.mfa_expiry = timezone.now() + timedelta(minutes=10)
                    security_profile.save()
                    
                    # Store user ID in session temporarily
                    request.session['mfa_user_id'] = user.id
                    if next_page:
                        request.session['login_next'] = next_page
                    resp['status'] = 'success'
                    resp['mfa_required'] = True
                    resp['msg'] = 'MFA code sent. Please check your email or enter the OTP.'
                    
                    # Log & print OTP to console immediately so admin/user can see it without delay
                    print(f"\n" + "="*50)
                    print(f"[SECURITY 2FA] OTP for user '{user.username}' is: {otp}")
                    print(f"="*50 + "\n")
                    
                    # Send MFA Code via Email in background thread (non-blocking)
                    platform_url = settings.GOVERNANCE_BASE_URL if security_profile.platform == 'Governance' else settings.RIFTSX_BASE_URL
                    
                    def async_send_mfa():
                        try:
                            send_mail(
                                f"Your {security_profile.platform} 2FA Code",
                                f"Your security code is: {otp}. It expires in 10 minutes.\n\nSystem URL: {platform_url}",
                                settings.DEFAULT_FROM_EMAIL,
                                [user.email],
                                fail_silently=True,
                            )
                        except Exception as e:
                            print(f"[EMAIL WARNING] Could not send MFA email to {user.email}: {e}")
                    
                    email_thread = threading.Thread(target=async_send_mfa, daemon=True)
                    email_thread.start()
                else:
                    login(request, user)
                    security_profile.last_login_ip = request.META.get('REMOTE_ADDR')
                    security_profile.save()
                    resp['status']='success'
                    if next_page:
                        resp['next'] = next_page
            else:
                resp['msg'] = "Account is inactive"
        else:
            resp['msg'] = "Incorrect username or password"
    return HttpResponse(json.dumps(resp),content_type='application/json')

def verify_mfa(request):
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        otp = request.POST.get('otp')
        user_id = request.session.get('mfa_user_id')
        
        if not user_id:
            resp['msg'] = "Session expired. Please login again."
            return HttpResponse(json.dumps(resp), content_type='application/json')
            
        user = get_object_or_404(User, id=user_id)
        security_profile = user.security_profile
        
        if security_profile.mfa_code == otp and security_profile.mfa_expiry > timezone.now():
            login(request, user)
            security_profile.mfa_code = None # Clear after use
            security_profile.last_login_ip = request.META.get('REMOTE_ADDR')
            security_profile.save()
            next_page = request.session.pop('login_next', '') if 'login_next' in request.session else ''
            if next_page:
                resp['next'] = next_page
            del request.session['mfa_user_id']
            resp['status'] = 'success'
        else:
            resp['msg'] = "Invalid or expired OTP"
            # Log failed MFA attempt
            SecurityAlert.objects.create(
                alert_type="Failed MFA Attempt",
                description=f"User {user.username} entered incorrect OTP.",
                severity="Medium",
                user=user,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
    return HttpResponse(json.dumps(resp), content_type='application/json')

from functools import wraps

def user_is_not_borrower(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if hasattr(request.user, 'borrower_profile') and not request.user.is_superuser:
            messages.warning(request, "Access Denied: You are restricted to the Recipient Dashboard.")
            return redirect('recipient-dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def role_required(allowed_roles=[]):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login-page')
            
            # Superusers bypass all checks
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
                
            security_profile, created = UserSecurity.objects.get_or_create(user=request.user)
            if security_profile.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            # Log unauthorized access attempt
            SecurityAlert.objects.create(
                alert_type="Unauthorized Access Attempt",
                description=f"User {request.user.username} (Role: {security_profile.role}) tried to access {request.path}",
                severity="High",
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            return render(request, '403.html', {'msg': 'You do not have permission to access this resource.'}, status=403)
        return _wrapped_view
    return decorator

def mask_sensitive_data(file_doc, user):
    """
    Modifies the file_doc object in-memory to mask or decrypt sensitive fields.
    """
    from .services.security import EncryptionService
    
    # Decrypt first so logic works on real values
    if hasattr(file_doc, 'is_encrypted') and file_doc.is_encrypted:
        file_doc.title = EncryptionService.decrypt(file_doc.title)
        file_doc.description = EncryptionService.decrypt(file_doc.description)
        # Note: We don't decrypt ref_num for now as it's not encrypted in the save hook yet
        
    if user.is_superuser:
        return file_doc
        
    security_profile, _ = UserSecurity.objects.get_or_create(user=user)
    role = security_profile.role
    
    # Masking Rules
    if file_doc.sensitivity_level == 'Highly Confidential':
        if role != 'Executive':
            file_doc.title = "[CONFIDENTIAL - MASKED]"
            file_doc.description = "You do not have the clearance level to view this document's details."
            file_doc.ref_num = "CONF-****"
            file_doc.is_masked = True
    elif file_doc.sensitivity_level == 'Sensitive':
        if role not in ['Supervisor', 'Executive', 'Auditor']:
            file_doc.title = "[SENSITIVE - MASKED]"
            file_doc.description = "SENSITIVE: Clearance required."
            file_doc.is_masked = True
            
    return file_doc

@login_required
def home(request):
    if not request.user.is_authenticated:
        return redirect('login-page')

    # ── Role-Based Landing Page Redirect ──────────────────────────────────
    # Each ZRP ICT role is redirected to their most relevant starting dashboard.
    # The query param ?home=1 bypasses the redirect so users can still visit home.
    if not request.GET.get('home'):
        _sp = getattr(request.user, 'security_profile', None)
        _role = (_sp.role or '') if _sp else ''
        _redirect_map = {
            'Supt ICT':              'admin-operations-dashboard',
            'System Manager':        'asset-list',
            'Chief Tech':            'asset-list',
            'Provincial ICT Officer':'form27-list',
            'General Police':        'goods-received-list',
            'Chief Director':        'procurement-analytics-dashboard',
        }
        if _role in _redirect_map:
            return redirect(_redirect_map[_role])

    context = context_data(request)
    security = getattr(request.user, 'security_profile', None)
    user_dept = security.department if security else None
    
    # ── Global Counts ──
    context['files'] = models.File.objects.filter(delete_flag=0).count()
    context['issued'] = models.Borrow.objects.filter(status='0').count()
    context['transactions'] = models.CustodyLog.objects.count()

    # ── Departmental Metrics & Analytics ──
    if user_dept:
        dept_reqs = models.SupplyRequisition.objects.filter(department=user_dept)
        dept_budgets = models.Budget.objects.filter(department=user_dept)
        dept_files = models.File.objects.filter(current_department=user_dept, delete_flag=0)
    else:
        dept_reqs = models.SupplyRequisition.objects.all()
        dept_budgets = models.Budget.objects.all()
        dept_files = models.File.objects.filter(delete_flag=0)

    # Requisition Metrics
    context['dept_requisition_count'] = dept_reqs.count()
    context['dept_pending_req_count'] = dept_reqs.filter(status__icontains='Pending').count()
    context['dept_approved_req_count'] = dept_reqs.filter(status__icontains='Approved').count()
    
    # Budget Metrics
    budget_tot = sum(b.total_allocation for b in dept_budgets)
    budget_spent = sum(b.spent_amount for b in dept_budgets)
    context['dept_budget_total'] = budget_tot
    context['dept_budget_spent'] = budget_spent
    context['dept_budget_remaining'] = max(0, budget_tot - budget_spent)
    context['dept_budget_utilization'] = round((budget_spent / budget_tot * 100), 1) if budget_tot > 0 else 0.0

    # Leave Metrics
    dept_leaves = models.LeaveRequest.objects.filter(user__security_profile__department=user_dept) if user_dept else models.LeaveRequest.objects.all()
    context['dept_leave_count'] = dept_leaves.count()
    context['dept_leave_pending'] = dept_leaves.filter(status='Pending').count()

    # Files Metrics
    context['dept_files_count'] = dept_files.count()
    
    # Recent Lists
    context['dept_recent_requisitions'] = dept_reqs.order_by('-date_requested')[:6]
    context['dept_recent_leaves'] = dept_leaves.order_by('-date_applied')[:6]
    context['dept_recent_files'] = dept_files.order_by('-date_added')[:6]

    # Chart Data Preparation
    import json
    pending_cnt = context['dept_pending_req_count']
    approved_cnt = context['dept_approved_req_count']
    completed_cnt = dept_reqs.filter(status__icontains='Completed').count() + dept_reqs.filter(status__icontains='Delivered').count()
    other_cnt = max(0, context['dept_requisition_count'] - (pending_cnt + approved_cnt + completed_cnt))

    context['chart_status_labels'] = json.dumps(["Pending Approval", "Approved", "Completed/Delivered", "In Review/Other"])
    context['chart_status_data'] = json.dumps([pending_cnt, approved_cnt, completed_cnt, other_cnt])

    context['chart_budget_labels'] = json.dumps(["Spent Allocation ($)", "Remaining Budget ($)"])
    context['chart_budget_data'] = json.dumps([float(budget_spent), float(max(0, budget_tot - budget_spent))])

    all_depts = models.Department.objects.all().order_by('name')
    dept_names = [d.name for d in all_depts]
    dept_counts = [models.SupplyRequisition.objects.filter(department=d).count() for d in all_depts]
    context['chart_dept_names'] = json.dumps(dept_names)
    context['chart_dept_counts'] = json.dumps(dept_counts)

    return render(request, 'home.html', context)



@login_required
def dashboard_dept_manager(request):
    security = getattr(request.user, 'security_profile', None)
    if not (security and (security.role in ['Department Manager', 'HODs', 'Project Management Team'])) and not request.user.is_superuser:
        messages.error(request, "Access Denied: Department Manager credentials required.")
        return redirect('home-page')

    context = context_data(request)
    context['page_title'] = "Department Manager Dashboard"
    context['page'] = 'dashboard_dept_manager'

    context['pending_requisitions'] = models.SupplyRequisition.objects.filter(
        dept_manager=request.user,
        status='Pending Dept'
    ).order_by('-is_urgent', '-date_requested')

    if security and security.department:
        dept_qs = models.SupplyRequisition.objects.filter(department=security.department)
        context['dept_budgets'] = models.Budget.objects.filter(department=security.department)
    else:
        dept_qs = models.SupplyRequisition.objects.all()
        context['dept_budgets'] = models.Budget.objects.all()

    # Group by department for display
    from django.db.models import Count
    dept_groups = {}
    for r in dept_qs.order_by('-is_urgent', 'department__name', '-date_requested'):
        dept_name = r.department.name if r.department else 'Unassigned'
        dept_groups.setdefault(dept_name, []).append(r)
    context['dept_requisitions_grouped'] = dept_groups
    context['dept_requisitions'] = dept_qs

    return render(request, 'dashboard_dept_manager.html', context)


@login_required
def dashboard_ceo(request):
    security = getattr(request.user, 'security_profile', None)
    if not (security and (security.role in ['Chief Director', 'Board of Executives', 'Executive'])) and not request.user.is_superuser:
        messages.error(request, "Access Denied: Chief Director credentials required.")
        return redirect('home-page')

    context = context_data(request)
    context['page_title'] = "Chief Director Strategic Dashboard"
    context['page'] = 'dashboard_ceo'

    context['pending_requisitions'] = models.SupplyRequisition.objects.filter(
        ceo=request.user,
        status='Pending CEO'
    ).order_by('-is_urgent', '-date_requested')

    all_reqs = models.SupplyRequisition.objects.all()
    context['total_requisitions'] = all_reqs.count()
    context['pending_count'] = all_reqs.filter(status__startswith='Pending').count()
    context['approved_count'] = all_reqs.filter(status='Approved').count()

    approved_reqs = all_reqs.filter(status='Approved')
    context['total_approved_spend'] = sum(r.grand_total for r in approved_reqs)

    from django.db.models import Sum, DecimalField
    from django.db.models.functions import Cast
    dept_spend = approved_reqs.values('department__name').annotate(total=Sum(Cast('items__unit_cost', DecimalField()) * Cast('items__quantity', DecimalField()))).order_by('-total')
    dept_spend = [d for d in dept_spend if d['department__name']]
    context['dept_labels'] = json.dumps([d['department__name'] for d in dept_spend])
    context['dept_data'] = json.dumps([float(d['total'] or 0) for d in dept_spend])

    # Group by department for requisition list
    ceo_reqs = models.SupplyRequisition.objects.filter(ceo=request.user)
    dept_groups = {}
    for r in ceo_reqs.order_by('-is_urgent', 'department__name', '-date_requested'):
        dept_name_key = r.department.name if r.department else 'Unassigned'
        dept_groups.setdefault(dept_name_key, []).append(r)
    context['dept_requisitions_grouped'] = dept_groups

    return render(request, 'dashboard_ceo.html', context)


@login_required
def dashboard_purchasing_officer(request):
    security = getattr(request.user, 'security_profile', None)
    dept_name = security.department.name.lower() if (security and security.department) else ''
    is_po = security and (security.role == 'Purchasing Officer' or 'purchasing' in dept_name or 'procurement' in dept_name)
    if not is_po and not request.user.is_superuser:
        messages.error(request, "Access Denied: Purchasing Officer credentials required.")
        return redirect('home-page')

    context = context_data(request)
    context['page_title'] = "Purchasing Officer Dashboard"
    context['page'] = 'dashboard_purchasing_officer'

    # First-pass (Bid Analysis) + Second-pass (Final Review)
    context['pending_bid_analysis'] = models.SupplyRequisition.objects.filter(
        purchasing_officer=request.user,
        status='Pending Purchasing'
    ).order_by('-is_urgent', '-date_requested')

    context['pending_final_review'] = models.SupplyRequisition.objects.filter(
        purchasing_officer=request.user,
        status='Pending Purchasing Final'
    ).order_by('-is_urgent', '-date_requested')

    # Legacy alias so existing templates don't break
    context['pending_requisitions'] = context['pending_bid_analysis']

    all_po_reqs = models.SupplyRequisition.objects.filter(purchasing_officer=request.user)
    context['processed_requisitions'] = all_po_reqs.exclude(
        status__in=['Draft', 'Pending Requester', 'Pending Dept', 'Pending Purchasing', 'Pending Requester Review', 'Pending Purchasing Final']
    )

    # Group all requisitions by department
    dept_groups = {}
    for r in all_po_reqs.order_by('-is_urgent', 'department__name', '-date_requested'):
        dept_name_key = r.department.name if r.department else 'Unassigned'
        dept_groups.setdefault(dept_name_key, []).append(r)
    context['dept_requisitions_grouped'] = dept_groups

    return render(request, 'dashboard_purchasing_officer.html', context)


@login_required
def dashboard_finance_officer(request):
    security = getattr(request.user, 'security_profile', None)
    dept_name = security.department.name.lower() if (security and security.department) else ''
    is_fo = security and (security.role == 'Finance Officer' or 'finance' in dept_name)
    if not is_fo and not request.user.is_superuser:
        messages.error(request, "Access Denied: Finance Officer credentials required.")
        return redirect('home-page')

    context = context_data(request)
    context['page_title'] = "Finance Officer Dashboard"
    context['page'] = 'dashboard_finance_officer'

    all_fo_reqs = models.SupplyRequisition.objects.filter(finance_officer=request.user)

    context['pending_requisitions'] = all_fo_reqs.filter(
        status='Pending Finance'
    ).order_by('-is_urgent', '-date_requested')

    context['paid_requisitions'] = all_fo_reqs.filter(payment_status='Paid')

    context['budgets'] = models.Budget.objects.all()

    # Group by department
    dept_groups = {}
    for r in all_fo_reqs.order_by('-is_urgent', 'department__name', '-date_requested'):
        dept_name_key = r.department.name if r.department else 'Unassigned'
        dept_groups.setdefault(dept_name_key, []).append(r)
    context['dept_requisitions_grouped'] = dept_groups

    return render(request, 'dashboard_finance_officer.html', context)


@login_required
def dashboard_md(request):
    context = context_data(request)
    context['page_title'] = "Board Strategic Dashboard"
    from .services.governance import GovernanceService
    context['stats'] = GovernanceService.calculate_institutional_metrics()
    context['projects'] = models.Project.objects.filter(is_deleted=False)
    
    # Benefit Analytics
    benefits = models.Benefit.objects.all()
    context['total_monthly_benefits'] = benefits.aggregate(Sum('monthly_savings'))['monthly_savings__sum'] or 0
    context['total_annual_benefits'] = benefits.aggregate(Sum('annual_projection'))['annual_projection__sum'] or 0
    context['benefits_data'] = benefits.order_by('-annual_projection')[:5]
    
    # Chart Data: Benefits by Department
    dept_benefits = benefits.values('department__name').annotate(total=Sum('annual_projection')).order_by('-total')
    context['benefit_dept_labels'] = json.dumps([d['department__name'] for d in dept_benefits])
    context['benefit_dept_data'] = json.dumps([float(d['total']) for d in dept_benefits])
    
    # Board-specific: Phases awaiting final Board approval (exclude deleted projects)
    context['pending_approvals'] = models.ProjectPhase.objects.filter(
        status='Awaiting Board Approval',
        project__is_deleted=False
    ).order_by('submitted_at')
    
    return render(request, 'governance/dashboard_md.html', context)

@login_required
def dashboard_hod(request):
    context = context_data(request)
    security = getattr(request.user, 'security_profile', None)
    
    # PMT or HODs role check
    if not (security and security.role in ['Project Management Team', 'HODs']) and not request.user.is_superuser:
        messages.error(request, "Access Denied: PMT or HODs credentials required.")
        return redirect('home-page')

    context['page_title'] = f"{security.role} Governance Control"
    
    # PMT/HODs sees and approves all projects from all PLs despite which department the PL belongs to
    projects = models.Project.objects.filter(is_deleted=False)
    context['projects'] = projects
    context['total_projects'] = projects.count()
    context['active_projects'] = projects.filter(status='Active').count()
    
    # Institutional metrics
    context['pm_count'] = UserSecurity.objects.filter(role='Project Leader').count()
    context['member_count'] = UserSecurity.objects.filter(role='Team Member').count()
    
    # Health Metrics
    total_progress = sum([p.progress_percentage for p in projects])
    total_count = projects.count()
    context['avg_progress'] = round(total_progress / total_count) if total_count > 0 else 0
    
    # SLA & Risks (Global for HODs)
    context['overdue_tasks_count'] = models.ProjectTask.objects.filter(
        status__in=['Pending', 'In Progress', 'To Do'],
        due_date__lt=timezone.now().date()
    ).count()

    # HOD approval chain: Phases awaiting departmental verification (exclude deleted projects)
    if security and security.role == 'HODs':
        pending_status = 'Awaiting HODs Approval'
    else:
        pending_status = 'Awaiting PMT Approval'

    context['pending_approvals'] = models.ProjectPhase.objects.filter(
        status=pending_status,
        project__is_deleted=False
    ).order_by('submitted_at')

    # Add Cost Recovery Summary
    from .models import CostRecovery
    from django.db.models import Sum
    context['total_recovered'] = CostRecovery.objects.aggregate(t=Sum('amount_recovered'))['t'] or 0

    return render(request, 'governance/dashboard_hod.html', context)

@login_required
def dashboard_pm(request):
    context = context_data(request)
    context['page_title'] = "Project Operations Dashboard"
    
    # Projects where user is the designated PL — exclude deleted ones
    managed_projects = models.Project.objects.filter(owner=request.user, is_deleted=False)
    context['projects'] = managed_projects
    
    # Critical Governing Actions (Phase Gate Approvals)
    context['pending_approvals'] = models.ProjectPhase.objects.filter(
        pm=request.user,
        status='Awaiting Project Leader Approval',
        project__is_deleted=False
    ).order_by('submitted_at')

    # Tasks awaiting PL review
    context['pending_task_reviews'] = models.ProjectTask.objects.filter(
        phase__pm=request.user,
        status='Awaiting Project Leader Approval',
        phase__project__is_deleted=False,
        is_deleted=False
    ).select_related('owner', 'phase__project')
    
    # Portfolio Health
    context['total_tasks'] = models.ProjectTask.objects.filter(
        phase__project__owner=request.user,
        phase__project__is_deleted=False,
        is_deleted=False
    ).count()
    context['overdue_tasks'] = models.ProjectTask.objects.filter(
        phase__project__owner=request.user,
        phase__project__is_deleted=False,
        is_deleted=False,
        status__in=['Pending', 'In Progress', 'To Do'],
        due_date__lt=timezone.now().date()
    )

    # Benefit Analytics (Exposed to PM)
    benefits = models.Benefit.objects.all()
    context['total_monthly_benefits'] = benefits.aggregate(Sum('monthly_savings'))['monthly_savings__sum'] or 0
    context['total_annual_benefits'] = benefits.aggregate(Sum('annual_projection'))['annual_projection__sum'] or 0
    context['benefits_data'] = benefits.order_by('-annual_projection')[:5]

    # Chart Data: Benefits by Department
    dept_benefits = benefits.values('department__name').annotate(total=Sum('annual_projection')).order_by('-total')
    context['benefit_dept_labels'] = json.dumps([d['department__name'] for d in dept_benefits])
    context['benefit_dept_data'] = json.dumps([float(d['total']) for d in dept_benefits])
    
    return render(request, 'governance/dashboard_pm.html', context)

@login_required
def dashboard_member(request):
    context = context_data(request)
    context['page_title'] = "Personal Impact Dashboard"
    
    # User's directly assigned tasks — exclude tasks from deleted projects
    assigned_tasks = models.ProjectTask.objects.filter(
        owner=request.user,
        is_deleted=False,
        phase__project__is_deleted=False
    )
    context['tasks'] = assigned_tasks.order_by('due_date')
    
    # High Impact items (Priority: High / Critical)
    context['priority_items'] = assigned_tasks.filter(
        priority__in=['High', 'Critical'],
        status__in=['Pending', 'In Progress', 'To Do']
    ).count()
    
    # Overdue Personal Commitments
    context['overdue_tasks'] = assigned_tasks.filter(
        status__in=['Pending', 'In Progress', 'To Do'],
        due_date__lt=timezone.now().date()
    )
    
    # Recent Project Involvement — exclude deleted projects
    context['active_projects'] = models.Project.objects.filter(
        phases__tasks__owner=request.user,
        is_deleted=False
    ).distinct()

    # Benefit Analytics (Exposed to Team Members)
    benefits = models.Benefit.objects.all()
    context['total_monthly_benefits'] = benefits.aggregate(Sum('monthly_savings'))['monthly_savings__sum'] or 0
    context['total_annual_benefits'] = benefits.aggregate(Sum('annual_projection'))['annual_projection__sum'] or 0
    context['benefits_data'] = benefits.order_by('-annual_projection')[:5]

    # Chart Data: Benefits by Department
    dept_benefits = benefits.values('department__name').annotate(total=Sum('annual_projection')).order_by('-total')
    context['benefit_dept_labels'] = json.dumps([d['department__name'] for d in dept_benefits])
    context['benefit_dept_data'] = json.dumps([float(d['total']) for d in dept_benefits])

    return render(request, 'governance/dashboard_member.html', context)

@login_required
def manage_users(request):
    """Board-only: View and manage all user role requests."""
    security = getattr(request.user, 'security_profile', None)
    if not (request.user.is_superuser or (security and security.role == 'Board of Executives')):
        messages.error(request, "Access Denied: Only the Board of Executives can access this page.")
        return redirect('home-page')
    
    context = context_data(request)
    context['page_title'] = "User Governance Panel"
    
    filter_tab = request.GET.get('filter', 'pending')
    
    all_profiles = UserSecurity.objects.select_related('user', 'department').all().order_by('-user__date_joined')
    
    # Strategic roles: Board, HODs, PMT, PL
    strategic_roles = ['Board of Executives', 'HODs', 'Project Management Team', 'Project Leader']
    
    if filter_tab == 'pending':
        profiles = all_profiles.filter(is_role_approved=False)
    elif filter_tab == 'strategic':
        profiles = all_profiles.filter(role_requested__in=strategic_roles, is_role_approved=False)
    elif filter_tab == 'approved':
        profiles = all_profiles.filter(is_role_approved=True)
    else:
        profiles = all_profiles
    
    context['profiles'] = profiles
    context['filter_tab'] = filter_tab
    context['pending_count'] = all_profiles.filter(is_role_approved=False).count()
    context['strategic_pending_count'] = all_profiles.filter(role_requested__in=strategic_roles, is_role_approved=False).count()
    context['approved_count'] = all_profiles.filter(is_role_approved=True).count()
    context['total_count'] = all_profiles.count()
    context['departments'] = models.Department.objects.all()
    context['roles'] = UserSecurity.ROLES
    context['strategic_roles'] = strategic_roles
    
    return render(request, 'governance/manage_users.html', context)

@login_required
def user_role_action(request):
    """Board-only: Process approve/reject/change role actions via POST."""
    if request.method != 'POST':
        return redirect('manage-users')
    
    security = getattr(request.user, 'security_profile', None)
    if not (request.user.is_superuser or (security and security.role == 'Board of Executives')):
        return HttpResponse(json.dumps({'status': 'failed', 'msg': 'Access denied.'}), content_type='application/json')
    
    action = request.POST.get('action')
    user_id = request.POST.get('user_id')
    
    try:
        target_security = UserSecurity.objects.select_related('user').get(user_id=user_id)
    except UserSecurity.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('manage-users')
    
    if action == 'approve':
        new_role = request.POST.get('role', target_security.role_requested)
        dept_id = request.POST.get('department')
        target_security.role = new_role
        target_security.is_role_approved = True
        target_security.role_approved_by = request.user
        target_security.role_approved_at = timezone.now()
        if dept_id:
            target_security.department_id = int(dept_id)
        target_security.save()
        messages.success(request, f"✅ '{target_security.user.username}' approved as {new_role}.")
        print(f"[RIFTS-X] USER APPROVED: '{target_security.user.username}' → {new_role} by {request.user.username}")
    
    elif action == 'reject':
        target_security.user.is_active = False
        target_security.user.save()
        target_security.is_role_approved = False
        target_security.save()
        messages.warning(request, f"⛔ '{target_security.user.username}' registration rejected. Account deactivated.")
        print(f"[RIFTS-X] USER REJECTED: '{target_security.user.username}' by {request.user.username}")
    
    elif action == 'change_role':
        new_role = request.POST.get('role')
        if new_role:
            old_role = target_security.role
            target_security.role = new_role
            target_security.save()
            messages.success(request, f"Role changed: '{target_security.user.username}' from {old_role} → {new_role}.")
    
    elif action == 'change_department':
        dept_id = request.POST.get('department')
        if dept_id:
            target_security.department_id = int(dept_id)
            target_security.save()
            messages.success(request, f"Department updated for '{target_security.user.username}'.")
    
    elif action == 'toggle_lock':
        target_security.is_locked = not target_security.is_locked
        target_security.save()
        state = "locked" if target_security.is_locked else "unlocked"
        messages.info(request, f"Account '{target_security.user.username}' {state}.")
    
    elif action == 'reactivate':
        target_security.user.is_active = True
        target_security.user.save()
        messages.success(request, f"Account '{target_security.user.username}' reactivated.")
    
    return redirect('manage-users')

@login_required
def logout_user(request):
    logout(request)
    return redirect('login-page')
    
@login_required
def profile(request):
    context = context_data(request)
    context['page'] = 'profile'
    context['page_title'] = "Profile"
    return render(request,'profile.html', context)

@login_required
@user_is_not_borrower
@role_required(allowed_roles=[
    'Supervisor', 'Executive', 'Chief Director', 'Deputy Director ICT',
    'Deputy Director Communications', 'Deputy Director IT', 'Systems Manager',
    'System Manager', 'Supt ICT', 'Chief Tech', 'Board of Executives',
    'Department Manager', 'Portfolio Admin', 'Auditor'
])
def users(request):
    context = context_data(request)
    context['page'] = 'users'
    context['page_title'] = "User List"
    context['users'] = User.objects.exclude(pk=request.user.pk).filter(is_superuser = False).all()
    return render(request, 'users.html', context)

@login_required
@user_is_not_borrower
def save_user(request):
    resp = { 'status': 'failed', 'msg' : '' }
    if request.method == 'POST':
        post = request.POST
        if not post['id'] == '':
            user = User.objects.get(id = post['id'])
            form = forms.UpdateUser(request.POST, instance=user)
        else:
            form = forms.SaveUser(request.POST) 

        if form.is_valid():
            import uuid as _uuid
            is_new_user = (post['id'] == '')
            user = form.save()

            # Update Security Profile
            security = user.security_profile
            platform_val = form.cleaned_data.get('platform') or post.get('platform')
            if platform_val:
                security.platform = platform_val

            role_val = form.cleaned_data.get('requested_role') or post.get('requested_role')
            if role_val:
                security.role = role_val
                security.role_requested = role_val

            dept_val = form.cleaned_data.get('department')
            if dept_val:
                security.department = dept_val
            elif post.get('department'):
                try:
                    security.department = models.Department.objects.get(id=post.get('department'))
                except Exception:
                    pass

            job_title_val = form.cleaned_data.get('job_title') or post.get('job_title')
            if job_title_val is not None:
                security.job_title = job_title_val

            pos_val = form.cleaned_data.get('position') or post.get('position')
            if pos_val is not None:
                security.position = pos_val

            security.is_role_approved = True  # Admin-created users are pre-approved

            # Send verification email for ALL newly admin-created users
            if is_new_user and user.email:
                security.email_verification_token = str(_uuid.uuid4())
                if security.platform == 'RIFTS-X':
                    security.mfa_enabled = True
            security.save()

            if is_new_user and user.email and security.email_verification_token:
                platform_url = settings.GOVERNANCE_BASE_URL if security.platform == 'Governance' else settings.RIFTSX_BASE_URL
                verify_url = f"{settings.RIFTSX_BASE_URL.rstrip('/')}/verify-email/{security.email_verification_token}"

                print(f"\n{'='*60}")
                print(f"[ADMIN-CREATED] VERIFICATION LINK for '{user.username}'")
                print(f"  Email    : {user.email}")
                print(f"  Platform : {security.platform}")
                print(f"  Link     : {verify_url}")
                print(f"{'='*60}\n")

                subject = f"Your {security.platform} Account Has Been Created"
                html_message = f"""
                <html><body style="font-family:Arial,sans-serif;background:#f4f6f9;padding:30px;">
                <div style="max-width:560px;margin:auto;background:#fff;border-radius:10px;padding:36px;box-shadow:0 2px 12px rgba(0,0,0,.08);">
                    <h2 style="color:#1a237e;margin-bottom:4px;">Welcome to {security.platform}</h2>
                    <p style="color:#555;font-size:15px;">Hello <strong>{user.get_full_name() or user.username}</strong>,</p>
                    <p style="color:#555;font-size:15px;">
                        An administrator has created an account for you on the
                        <strong>{security.platform}</strong> platform with the role of
                        <strong>{security.role}</strong>.
                    </p>
                    <p style="color:#555;font-size:15px;">Please verify your email address to activate your account:</p>
                    <div style="text-align:center;margin:32px 0;">
                        <a href="{verify_url}"
                           style="background:#1a237e;color:#fff;padding:14px 36px;border-radius:50px;
                                  font-size:16px;font-weight:bold;text-decoration:none;display:inline-block;">
                            &#10003;&nbsp; Verify My Email
                        </a>
                    </div>
                    <p style="color:#888;font-size:13px;">Or copy and paste this link into your browser:</p>
                    <p style="font-size:12px;word-break:break-all;color:#1a237e;">{verify_url}</p>
                    <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
                    <p style="color:#aaa;font-size:12px;text-align:center;">
                        System URL: {platform_url}
                    </p>
                </div></body></html>
                """
                plain_message = (
                    f"Hello {user.username},\n\n"
                    f"Your {security.platform} account has been created by an administrator.\n"
                    f"Role: {security.role}\n\n"
                    f"Verify your email here:\n{verify_url}\n\n"
                    f"System URL: {platform_url}"
                )
                try:
                    from django.core.mail import EmailMultiAlternatives
                    msg = EmailMultiAlternatives(
                        subject, plain_message,
                        settings.DEFAULT_FROM_EMAIL, [user.email]
                    )
                    msg.attach_alternative(html_message, "text/html")
                    msg.send(fail_silently=False)
                    messages.success(request, f"User created. A verification email has been sent to {user.email}.")
                except Exception as e:
                    print(f"[EMAIL ERROR] Could not send to {user.email}: {e}")
                    messages.warning(request, f"User created but email could not be sent. Verification link: {verify_url}")
            else:
                if is_new_user:
                    messages.success(request, "User has been saved successfully.")
                else:
                    messages.success(request, "User has been updated successfully.")
            resp['status'] = 'success'
        else:
            for field in form:
                for error in field.errors:
                    if not resp['msg'] == '':
                        resp['msg'] += str('<br/>')
                    resp['msg'] += str(f'[{field.name}] {error}')
    else:
         resp['msg'] = "There's no data sent on the request"

    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
@role_required(allowed_roles=[
    'Supervisor', 'Executive', 'Chief Director', 'Deputy Director ICT',
    'Deputy Director Communications', 'Deputy Director IT', 'Systems Manager',
    'System Manager', 'Supt ICT', 'Chief Tech', 'Board of Executives',
    'Department Manager', 'Portfolio Admin'
])
def manage_user(request, pk = None):
    context = context_data(request)
    context['page'] = 'manage_user'
    context['page_title'] = 'Manage User'
    if pk is None:
        context['user'] = {}
    else:
        context['user'] = User.objects.get(id=pk)
    context['departments'] = models.Department.objects.all()
    return render(request, 'manage_user.html', context)

@login_required
@role_required(allowed_roles=[
    'Supervisor', 'Executive', 'Chief Director', 'Deputy Director ICT',
    'Deputy Director Communications', 'Deputy Director IT', 'Systems Manager',
    'System Manager', 'Supt ICT', 'Chief Tech', 'Board of Executives',
    'Department Manager', 'Portfolio Admin'
])
def delete_user(request, pk = None):
    resp = { 'status' : 'failed', 'msg':''}
    if pk is None:
        resp['msg'] = 'User ID is invalid'
    else:
        try:
            User.objects.filter(pk = pk).delete()
            messages.success(request, "User has been deleted successfully.")
            resp['status'] = 'success'
        except:
            resp['msg'] = "Deleting User Failed"

    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
@user_is_not_borrower
def category(request):
    context = context_data(request)
    context['page'] = 'category'
    context['page_title'] = "Category List"
    context['category'] = models.Category.objects.filter(delete_flag = 0).all()
    return render(request, 'category.html', context)

@login_required
@user_is_not_borrower
def save_category(request):
    resp = { 'status': 'failed', 'msg' : '' }
    if request.method == 'POST':
        try:
            post = request.POST
            if not post.get('id', '') == '':
                category = models.Category.objects.get(id = post.get('id'))
                form = forms.SaveCategory(request.POST, instance=category)
            else:
                form = forms.SaveCategory(request.POST)
            
            if form.is_valid():
                form.save()
                if post.get('id', '') == '':
                    messages.success(request, "Category has been saved successfully.")
                else:
                    messages.success(request, "Category has been updated successfully.")
                resp['status'] = 'success'
            else:
                for field in form:
                    for error in field.errors:
                        if not resp['msg'] == '':
                            resp['msg'] += str('<br/>')
                        resp['msg'] += str(f'[{field.name}] {error}')
        except Exception as e:
            resp['msg'] = f"An internal error occurred: {str(e)}"
    else:
         resp['msg'] = "There's no data sent on the request"

    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def view_category(request, pk = None):
    context = context_data(request)
    context['page'] = 'view_category'
    context['page_title'] = 'View Category'
    if pk is None:
        context['category'] = {}
    else:
        context['category'] = models.Category.objects.get(id=pk)
    
    return render(request, 'view_category.html', context)

@login_required
@role_required(allowed_roles=['Supervisor', 'Executive'])
def manage_category(request, pk = None):
    context = context_data(request)
    context['page'] = 'manage_category'
    context['page_title'] = 'Manage Category'
    if pk is None:
        context['category'] = {}
    else:
        context['category'] = models.Category.objects.get(id=pk)
    
    return render(request, 'manage_category.html', context)

@login_required
@role_required(allowed_roles=['Supervisor', 'Executive'])
def delete_category(request, pk = None):
    resp = { 'status' : 'failed', 'msg':''}
    if pk is None:
        resp['msg'] = 'Category ID is invalid'
    else:
        try:
            models.Category.objects.filter(pk = pk).update(delete_flag = 1)
            messages.success(request, "Category has been deleted successfully.")
            resp['status'] = 'success'
        except:
            resp['msg'] = "Deleting Category Failed"

    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
@user_is_not_borrower
def sub_category(request):
    context = context_data(request)
    context['page'] = 'sub_category'
    context['page_title'] = "Sub Category List"
    context['sub_category'] = models.SubCategory.objects.filter(delete_flag = 0).all()
    return render(request, 'sub_category.html', context)

@login_required
@user_is_not_borrower
def save_sub_category(request):
    resp = { 'status': 'failed', 'msg' : '' }
    if request.method == 'POST':
        try:
            post = request.POST
            if not post.get('id', '') == '':
                sub_category = models.SubCategory.objects.get(id = post.get('id'))
                form = forms.SaveSubCategory(request.POST, instance=sub_category)
            else:
                form = forms.SaveSubCategory(request.POST)
            
            if form.is_valid():
                form.save()
                if post.get('id', '') == '':
                    messages.success(request, "Sub Category has been saved successfully.")
                else:
                    messages.success(request, "Sub Category has been updated successfully.")
                resp['status'] = 'success'
            else:
                for field in form:
                    for error in field.errors:
                        if not resp['msg'] == '':
                            resp['msg'] += str('<br/>')
                        resp['msg'] += str(f'[{field.name}] {error}')
        except Exception as e:
            resp['msg'] = f"An internal error occurred: {str(e)}"
    else:
         resp['msg'] = "There's no data sent on the request"

    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def view_sub_category(request, pk = None):
    context = context_data(request)
    context['page'] = 'view_sub_category'
    context['page_title'] = 'View Sub Category'
    if pk is None:
        context['sub_category'] = {}
    else:
        context['sub_category'] = models.SubCategory.objects.get(id=pk)
    
    return render(request, 'view_sub_category.html', context)

@login_required
def manage_sub_category(request, pk = None):
    context = context_data(request)
    context['page'] = 'manage_sub_category'
    context['page_title'] = 'Manage Sub Category'
    if pk is None:
        context['sub_category'] = {}
    else:
        context['sub_category'] = models.SubCategory.objects.get(id=pk)
    context['categories'] = models.Category.objects.filter(delete_flag = 0, status = 1).all()
    return render(request, 'manage_sub_category.html', context)

@login_required
def delete_sub_category(request, pk = None):
    resp = { 'status' : 'failed', 'msg':''}
    if pk is None:
        resp['msg'] = 'Sub Category ID is invalid'
    else:
        try:
            models.SubCategory.objects.filter(pk = pk).update(delete_flag = 1)
            messages.success(request, "Sub Category has been deleted successfully.")
            resp['status'] = 'success'
        except:
            resp['msg'] = "Deleting Sub Category Failed"

    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
@user_is_not_borrower
def departments(request):
    context = context_data(request)
    context['page'] = 'department'
    context['page_title'] = "Department List"
    context['departments'] = models.Department.objects.order_by('name').all()
    return render(request, 'department.html', context)

@login_required
@user_is_not_borrower
def save_department(request):
    resp = { 'status': 'failed', 'msg' : '' }
    if request.method == 'POST':
        post = request.POST
        if not str(post.get('id')).isdigit():
            try:
                models.Department.objects.create(name=post.get('name'), description=post.get('description'))
                messages.success(request, "Department has been saved successfully.")
                resp['status'] = 'success'
            except Exception as e:
                resp['msg'] = str(e)
        else:
            try:
                models.Department.objects.filter(id=post.get('id')).update(name=post.get('name'), description=post.get('description'))
                messages.success(request, "Department has been updated successfully.")
                resp['status'] = 'success'
            except Exception as e:
                resp['msg'] = str(e)
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
@user_is_not_borrower
def manage_department(request, pk = None):
    context = context_data(request)
    context['page'] = 'manage_department'
    context['page_title'] = 'Manage Department'
    if pk is None:
        context['department'] = {}
    else:
        context['department'] = models.Department.objects.get(id=pk)
    return render(request, 'manage_department.html', context)

@login_required
@user_is_not_borrower
def delete_department(request, pk = None):
    resp = { 'status' : 'failed', 'msg':''}
    if pk is None:
        resp['msg'] = 'Department ID is invalid'
    else:
        try:
            models.Department.objects.filter(pk = pk).delete()
            messages.success(request, "Department has been deleted successfully.")
            resp['status'] = 'success'
        except:
            resp['msg'] = "Deleting Department Failed"
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
@user_is_not_borrower
def files(request):
    context = context_data(request)
    context['page'] = 'file_doc'
    context['page_title'] = "File List"
    
    # Base queryset
    queryset = models.File.objects.filter(delete_flag=0)
    
    # Search by File ID or Title
    q = request.GET.get('q')
    if q:
        queryset = queryset.filter(
            Q(ref_num__icontains=q) | 
            Q(title__icontains=q)
        )
        
    # Filter by Current Handler
    handler_id = request.GET.get('handler')
    if handler_id:
        queryset = queryset.filter(last_handler_id=handler_id)
        
    # Filter by Current Department
    dept_id = request.GET.get('department')
    if dept_id:
        queryset = queryset.filter(current_department_id=dept_id)
        
    file_list = []
    for f in queryset.all().order_by('-date_added'):
        file_list.append(mask_sensitive_data(f, request.user))
    context['file_doc'] = file_list
    context['departments'] = models.Department.objects.all()
    context['users'] = User.objects.all()
    
    return render(request, 'files.html', context)

@login_required
@user_is_not_borrower
def save_file_doc(request):
    resp = { 'status': 'failed', 'msg' : '' }
    if request.method == 'POST':
        try:
            post = request.POST
            if not post.get('id', '') == '':
                file_doc = models.File.objects.get(id = post.get('id'))
                form = forms.SaveFile(request.POST, request.FILES, instance=file_doc)
            else:
                form = forms.SaveFile(request.POST, request.FILES)
            
            if form.is_valid():
                obj = form.save()
                
                # Save ZRP Classification Level
                if post.get('classification_level'):
                    obj.classification_level = post.get('classification_level')
                    obj.save()
                
                # Physical Location Logic
                building = post.get('building')
                floor = post.get('floor')
                cabinet = post.get('cabinet')
                shelf = post.get('shelf')
                office = post.get('office', '')

                loc_obj = None
                if building and floor and cabinet and shelf:
                    loc_obj = models.FileLocation.objects.create(
                        building = building,
                        floor = floor,
                        cabinet = cabinet,
                        shelf = shelf,
                        office = office
                    )
                    obj.current_location = loc_obj
                    obj.save()
                    
                # Audit trail logging
                is_new = post.get('id', '') == ''
                log_document_action(
                    request.user, 'Create' if is_new else 'Edit',
                    file_doc=obj,
                    details=f"Document '{obj.title}' ({obj.ref_num}) saved with classification '{obj.classification_level}'.",
                    request=request
                )

                # Set initial handler and create Digital Twin Folder if new file
                if is_new:
                    from registry.services.custody import CustodyService
                    from registry.services.cloud import CloudService
                    CustodyService.record_creation(obj, request.user, loc_obj)
                    
                    # Auto-provision Digital Twin Cloud Folder
                    if obj.current_department:
                        CloudService.get_or_create_folder(obj.ref_num, obj.current_department, user=request.user)
                
                obj.save()
                
                if post.get('id', '') == '':
                    messages.success(request, "File has been saved successfully.")
                else:
                    messages.success(request, "File has been updated successfully.")
                resp['status'] = 'success'
            else:
                for field in form:
                    for error in field.errors:
                        if not resp['msg'] == '':
                            resp['msg'] += str('<br/>')
                        resp['msg'] += str(f'[{field.name}] {error}')
        except Exception as e:
            resp['msg'] = f"An internal error occurred: {str(e)}"
    else:
         resp['msg'] = "There's no data sent on the request"

    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def view_file_doc(request, pk = None):
    context = context_data(request)
    context['page'] = 'view_file_doc'
    context['page_title'] = 'View File'
    if pk is None:
        return HttpResponseBadRequest("Invalid request")
    
    file_obj = get_object_or_404(models.File, id=pk)
    
    # Audit trail logging
    log_document_action(
        request.user, 'View',
        file_doc=file_obj,
        details=f"Document '{file_obj.title}' ({file_obj.ref_num}) viewed by {request.user.username}.",
        request=request
    )
    
    context['file_doc'] = mask_sensitive_data(file_obj, request.user)
    context['original_file'] = file_obj
    
    # Fetch related data
    from registry.services.location import LocationIntelligence
    context['location'] = LocationIntelligence.get_last_known_location(file_obj)
    context['logs'] = models.CustodyLog.objects.filter(file_doc=file_obj).order_by('-timestamp')
    
    return render(request, 'view_files.html', context)

@login_required
def manage_file_doc(request, pk = None):
    context = context_data(request)
    context['page'] = 'manage_file_doc'
    context['page_title'] = 'Manage File'
    if pk is None:
        context['file_doc'] = {}
        context['location'] = {}
    else:
        file_doc = models.File.objects.get(id=pk)
        context['file_doc'] = file_doc
        from registry.services.location import LocationIntelligence
        context['location'] = LocationIntelligence.get_last_known_location(file_doc)
    context['sub_categories'] = models.SubCategory.objects.filter(delete_flag = 0, status = 1).all()
    return render(request, 'manage_files.html', context)



@login_required
@role_required(allowed_roles=['Supervisor', 'Executive'])
@login_required
def download_version(request, pk):
    version = get_object_or_404(models.FileVersion, id=pk)
    file_doc = version.file_doc
    
    # Check clearance level
    security_profile, _ = UserSecurity.objects.get_or_create(user=request.user)
    role = security_profile.role
    
    if file_doc.sensitivity_level == 'Highly Confidential' and role != 'Executive':
        SecurityAlert.objects.create(
            alert_type="Unauthorized Download Attempt",
            description=f"User {request.user.username} tried to download highly confidential document {file_doc.ref_num}.",
            severity="High",
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        return HttpResponseForbidden("Unauthorised Clearance Level")

    # Log successful download
    SecurityAlert.objects.create(
        alert_type="Document Download",
        description=f"User {request.user.username} downloaded {file_doc.ref_num} (Version {version.id}).",
        severity="Low",
        user=request.user,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    # Track as Forensic Audit too
    models.ForensicAudit.objects.create(
        user=request.user,
        action=f"Downloaded Document: {file_doc.ref_num}",
        method="GET",
        path=request.path,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT')
    )
    
    # Serve file
    try:
        response = HttpResponse(version.file, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(version.file.name)}"'
        return response
    except Exception as e:
        return HttpResponse(f"Error serving file: {str(e)}", status=500)

@login_required
def delete_file_doc(request, pk = None):
    resp = { 'status' : 'failed', 'msg':''}
    if pk is None:
        resp['msg'] = 'File ID is invalid'
    else:
        try:
            models.File.objects.filter(pk = pk).update(delete_flag = 1)
            messages.success(request, "File has been deleted successfully.")
            resp['status'] = 'success'
        except:
            resp['msg'] = "Deleting File Failed"

    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
@user_is_not_borrower
def borrower(request):
    context = context_data(request)
    context['page'] = 'borrower'
    context['page_title'] = "Borrower List"
    context['borrower'] = models.Borrower.objects.filter(delete_flag = 0).all()
    return render(request, 'borrower.html', context)

@login_required
@user_is_not_borrower
def save_borrower(request):
    resp = { 'status': 'failed', 'msg' : '' }
    if request.method == 'POST':
        try:
            post = request.POST
            if not post.get('id', '') == '':
                borrower = models.Borrower.objects.get(id = post.get('id'))
                form = forms.SaveBorrower(request.POST, instance=borrower)
            else:
                form = forms.SaveBorrower(request.POST)
            
            if form.is_valid():
                form.save()
                if post.get('id', '') == '':
                    messages.success(request, "Borrower has been saved successfully.")
                else:
                    messages.success(request, "Borrower has been updated successfully.")
                resp['status'] = 'success'
            else:
                for field in form:
                    for error in field.errors:
                        if not resp['msg'] == '':
                            resp['msg'] += str('<br/>')
                        resp['msg'] += str(f'[{field.name}] {error}')
        except Exception as e:
            resp['msg'] = f"An internal error occurred: {str(e)}"
    else:
         resp['msg'] = "There's no data sent on the request"

    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
@user_is_not_borrower
def view_borrower(request, pk = None):
    context = context_data(request)
    context['page'] = 'view_borrower'
    context['page_title'] = 'View Borrower'
    if pk is None:
        context['borrower'] = {}
    else:
        context['borrower'] = models.Borrower.objects.get(id=pk)
    
    return render(request, 'view_borrower.html', context)

@login_required
@user_is_not_borrower
def manage_borrower(request, pk = None):
    context = context_data(request)
    context['page'] = 'manage_borrower'
    context['page_title'] = 'Manage Borrower'
    if pk is None:
        context['borrower'] = {}
    else:
        context['borrower'] = models.Borrower.objects.get(id=pk)
    context['departments'] = models.Department.objects.all()
    return render(request, 'manage_borrower.html', context)

@login_required
@user_is_not_borrower
def delete_borrower(request, pk = None):
    resp = { 'status' : 'failed', 'msg':''}
    if pk is None:
        resp['msg'] = 'Borrower ID is invalid'
    else:
        try:
            models.Borrower.objects.filter(pk = pk).update(delete_flag = 1)
            messages.success(request, "Borrower has been deleted successfully.")
            resp['status'] = 'success'
        except:
            resp['msg'] = "Deleting Borrower Failed"

    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
@user_is_not_borrower
def borrows(request):
    context = context_data(request)
    context['page'] = 'borrow'
    context['page_title'] = "Borrowing Transaction List"
    context['borrows'] = models.Borrow.objects.order_by('status').all()
    return render(request, 'borrows.html', context)

@login_required
@user_is_not_borrower
def save_borrow(request):
    resp = { 'status': 'failed', 'msg' : '' }
    if request.method == 'POST':
        try:
            post = request.POST
            if not post.get('id', '') == '':
                borrow = models.Borrow.objects.get(id = post.get('id'))
                form = forms.SaveBorrow(request.POST, instance=borrow)
            else:
                file_id = post.get('file_doc')

                if models.Borrow.objects.filter(file_doc_id=file_id, status='0').exists():
                    resp['msg'] = "This file is already issued and has not been returned yet."
                    return HttpResponse(json.dumps(resp), content_type="application/json")
                
                form = forms.SaveBorrow(request.POST)
                
            if form.is_valid():
                instance = form.save()
                cloud_folder_id = post.get('cloud_folder_id', '').strip()
                if cloud_folder_id:
                    folder = models.CloudFolder.objects.filter(id=cloud_folder_id, is_deleted=False).first()
                    if folder:
                        instance.issued_folder = folder
                        permission = post.get('folder_permission', 'view')
                        instance.folder_permission = permission if permission in ('view', 'edit') else 'view'
                        try:
                            zip_buffer = _zip_cloud_folder(folder)
                            zip_name = f"{folder.name.replace(' ', '_')}_issued.zip"
                            instance.folder_zip.save(zip_name, ContentFile(zip_buffer.getvalue()), save=False)
                        except Exception:
                            pass
                        borrower_user = instance.borrower.user if instance.borrower else None
                        for cloud_file in folder.files.filter(status='Active'):
                            CloudService.create_share(
                                cloud_file,
                                request.user,
                                expiry_days=30,
                                shared_with_user=borrower_user,
                                shared_with_email=instance.borrower.email,
                                can_download=True,
                                can_edit=(instance.folder_permission == 'edit')
                            )
                instance.save()
                if post.get('id', '') == '':
                    # Update file status
                    file_obj = instance.file_doc
                    file_obj.f_status = 'borrowed'
                    file_obj.save()
                    
                    try:
                        # Secure Access Logic
                        access_token = secrets.token_urlsafe(32)
                        instance.access_token = access_token
                        instance.token_expiry = timezone.now() + datetime.timedelta(days=3)
                        
                        borrower = instance.borrower
                        temp_pass = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
                        
                        # Check if borrower has a linked User
                        if not borrower.user:
                            # Try to find by email
                            user = User.objects.filter(email=borrower.email).first()
                            if not user:
                                # Create new user
                                username = borrower.email.split('@')[0] if borrower.email else f"officer_{borrower.code}"
                                # Ensure uniqueness
                                if User.objects.filter(username=username).exists():
                                    username = f"{username}_{secrets.token_hex(2)}"
                                
                                user = User.objects.create_user(username=username, email=borrower.email, password=temp_pass)
                                user.first_name = borrower.first_name
                                user.last_name = borrower.last_name
                                user.save()
                            else:
                                # Existing user found, update password to OTP
                                user.set_password(temp_pass)
                                user.save()
                                
                            borrower.user = user
                            borrower.save()
                        else:
                            # Already linked user, update password to OTP
                            borrower.user.set_password(temp_pass)
                            borrower.user.save()
                            
                        instance.temp_password = temp_pass
                        instance.save()

                        if borrower.email:
                            subject = f'RIFTS-X: File Issued - {instance.file_doc.ref_num}'
                            # Build secure access URL
                            access_url = request.build_absolute_uri(reverse('access-with-token', kwargs={'token': access_token}))
                            
                            html_message = render_to_string('registry/email/borrow_notification.html', {
                                'ctx_borrower_name': borrower.name(),
                                'ctx_file_ref': instance.file_doc.ref_num,
                                'ctx_file_title': instance.file_doc.title,
                                'ctx_folio_ref': instance.folio_ref,
                                'ctx_return_date': instance.return_date.strftime('%d-%b-%Y') if instance.return_date else 'N/A',
                                'ctx_issuer_name': request.user.get_full_name() or request.user.username,
                                'ctx_access_url': access_url,
                                'ctx_username': borrower.user.username,
                                'ctx_temp_password': temp_pass,
                                'ctx_system_url': settings.RIFTSX_BASE_URL,
                                'ctx_issued_folder_name': instance.issued_folder.name if instance.issued_folder else '',
                                'ctx_folder_permission': 'Edit Allowed' if instance.folder_permission == 'edit' else 'View Only',
                                'ctx_folder_link': request.build_absolute_uri(reverse('borrow-folder-view', kwargs={'pk': instance.pk})) if instance.issued_folder else '',
                                'ctx_folder_download_url': request.build_absolute_uri(reverse('download-issued-folder', kwargs={'pk': instance.pk})) if instance.folder_zip else ''
                            })
                            plain_message = strip_tags(html_message)
                            
                            send_mail(
                                subject,
                                plain_message,
                                request.user.email or None,
                                [borrower.email],
                                html_message=html_message,
                                fail_silently=False
                            )
                    except Exception as e:
                        print(f"Email/Security Error: {e}")

                if post.get('status') == '1': # Returned
                    file_obj = instance.file_doc
                    file_obj.f_status = 'available'
                    file_obj.save()

                resp['status'] = 'success'
            else:
                for field in form:
                    for error in field.errors:
                        if not resp['msg'] == '':
                            resp['msg'] += str('<br/>')
                        resp['msg'] += str(f'[{field.name}] {error}')
        except Exception as e:
            resp['msg'] = f"An internal error occurred: {str(e)}"
    else:
         resp['msg'] = "There's no data sent on the request"

    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def view_borrow(request, pk = None):
    context = context_data(request)
    context['page'] = 'view_borrow'
    context['page_title'] = 'View Transaction Details'
    if pk is None:
        context['borrow'] = {}
    else:
        context['borrow'] = models.Borrow.objects.get(id=pk)
    
    return render(request, 'view_borrow.html', context)

@login_required
def manage_borrow(request, pk = None):
    context = context_data(request)
    context['page'] = 'manage_borrow'
    context['page_title'] = 'Manage Transaction Details'
    if pk is None:
        context['borrow'] = {}
    else:
        context['borrow'] = models.Borrow.objects.get(id=pk)
    context['borrower'] = models.Borrower.objects.filter(delete_flag = 0, status = 1).all()
    context['file_doc'] = models.File.objects.filter(delete_flag = 0, status = 1).all()
    context['cloud_folders'] = models.CloudFolder.objects.filter(is_deleted=False).all()
    return render(request, 'manage_borrow.html',  context)               

@login_required
def delete_borrow(request, pk = None):
    resp = { 'status' : 'failed', 'msg':''}
    if pk is None:
        resp['msg'] = 'Transaction ID is invalid'
    else:
        try:
            models.Borrow.objects.filter(pk = pk).delete()
            messages.success(request, "Transaction has been deleted successfully.")
            resp['status'] = 'success'
        except:
            resp['msg'] = "Deleting Transaction Failed"

    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
@user_is_not_borrower
def folio(request):
    context = context_data(request)
    context['page'] = 'folio'
    context['page_title'] = "folio List"
    context['folio'] = models.Folio.objects.filter(delete_flag = 0).all()
    return render(request, 'folio.html', context)

@login_required
@login_required
@user_is_not_borrower
def save_folio(request):
    resp = { 'status': 'failed', 'msg' : '' }
    if request.method == 'POST':
        try:
            post = request.POST
            if not post.get('id', '') == '':
                folio = models.Folio.objects.get(id = post.get('id'))
                form = forms.SaveFolio(request.POST, instance=folio)
            else:
                form = forms.SaveFolio(request.POST)
            
            if form.is_valid():
                form.save()
                if post.get('id', '') == '':
                    messages.success(request, "Folio has been saved successfully.")
                else:
                    messages.success(request, "Folio has been updated successfully.")
                resp['status'] = 'success'
            else:
                for field in form:
                    for error in field.errors:
                        if not resp['msg'] == '':
                            resp['msg'] += str('<br/>')
                        resp['msg'] += str(f'[{field.name}] {error}')
        except Exception as e:
            resp['msg'] = f"An internal error occurred: {str(e)}"
    else:
         resp['msg'] = "There's no data sent on the request"

    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def view_folio(request, pk = None):
    context = context_data(request)
    context['page'] = 'view_folio'
    context['page_title'] = 'View Folio'
    if pk is None:
        context['folio'] = {}
    else:
        context['folio'] = models.Folio.objects.get(id=pk)
    
    return render(request, 'view_folio.html', context)

@login_required
def manage_folio(request, pk = None):
    context = context_data(request)
    context['page'] = 'manage_folio'
    context['page_title'] = 'Manage Folio'
    if pk is None:
        context['folio'] = {}
    else:
        context['folio'] = models.Folio.objects.get(id=pk)
    context['folios'] = models.File.objects.filter(delete_flag = 0, status = 1).all()
    return render(request, 'manage_folio.html', context)

@login_required
def delete_folio(request, pk = None):
    resp = { 'status' : 'failed', 'msg':''}
    if pk is None:
        resp['msg'] = 'Folio ID is invalid'
    else:
        try:
            models.Folio.objects.filter(pk = pk).update(delete_flag = 1)
            messages.success(request, "Folio has been deleted successfully.")
            resp['status'] = 'success'
        except:
            resp['msg'] = "Deleting Folio Failed"

    return HttpResponse(json.dumps(resp), content_type="application/json")


@login_required
def generate_secure_link(request, pk):
    file_obj = get_object_or_404(models.File, pk=pk)
    import secrets
    from django.urls import reverse
    
    token = secrets.token_urlsafe(32)
    # Link expires in 2 hours
    expires_at = timezone.now() + datetime.timedelta(hours=2)
    
    models.SecureLink.objects.create(
        file_doc=file_obj,
        token=token,
        expires_at=expires_at
    )
    
    verify_url = request.build_absolute_uri(reverse('verify-secure-link', args=[token]))
    
    return HttpResponse(json.dumps({'status': 'success', 'url': verify_url}), content_type='application/json')

def verify_secure_link(request, token):
    link = get_object_or_404(models.SecureLink, token=token)
    
    if not link.is_valid():
        return render(request, 'secure_verify.html', {'error': 'Link Expired or Invalid'})
    
    if request.method == 'POST':
        # Simple "Zero-Knowledge" proof simulation: User must provide a matching ref number or verification key
        proof = request.POST.get('proof')
        if proof == link.file_doc.ref_num:
            link.access_count += 1
            link.save()
            return render(request, 'secure_verify.html', {'file_doc': link.file_doc, 'success': True})
        else:
            return render(request, 'secure_verify.html', {'error': 'Verification Failed: Proof of Knowledge Incorrect'})
            
    return render(request, 'secure_verify.html', {'link': link})

    


@login_required
def share_file_digital(request, pk):
    file_doc = get_object_or_404(models.File, pk=pk)
    
    # Physical Integrity Check before sharing
    if models.Folio.objects.filter(filee=file_doc, delete_flag=0).count() == 0:
        if request.method == 'GET':
            from django.http import HttpResponse
            return HttpResponse(
                '<div class="alert alert-danger mb-0"><i class="fa fa-exclamation-triangle me-2"></i><strong>Physical Integrity Error:</strong> This file has no folios/components. You must add folios before initiating a digital transfer.</div>'
                '<script>$("#uni_modal #submit").hide();</script>'
            )
        return JsonResponse({'status': 'failed', 'msg': 'Physical Integrity Error: File has no Folios/Components. Please add folios before sharing.'})

    if request.method == 'POST':
        shared_to_id = request.POST.get('shared_to')
        duration_hours = int(request.POST.get('duration', 24)) # Default 24 hours
        shared_to = get_object_or_404(User, pk=shared_to_id)
        
        expires_at = timezone.now() + datetime.timedelta(hours=duration_hours)
        
        import secrets
        token = secrets.token_urlsafe(32)
        
        models.DigitalShare.objects.create(
            file_doc=file_doc,
            shared_by=request.user,
            shared_to=shared_to,
            token=token,
            expires_at=expires_at,
            status='active'
        )
        
        share_url = request.build_absolute_uri(reverse('verify-digital-share', args=[token]))
        return JsonResponse({'status': 'success', 'url': share_url})
    
    # For GET, return list of users to share with
    users = User.objects.exclude(pk=request.user.pk).all()
    context = {
        'file_doc': file_doc,
        'users': users
    }
    return render(request, 'manage_share.html', context)

@login_required
def verify_digital_share(request, token):
    share = get_object_or_404(models.DigitalShare, token=token, status='active')
    
    if request.user != share.shared_to:
        return render(request, 'error.html', {'msg': 'Unauthorized access to this digital share.'})
    
    if not share.opened_at:
        share.opened_at = timezone.now()
        share.save()
    
    context = context_data(request)
    context['share'] = share
    context['file_doc'] = share.file_doc
    context['page_title'] = f"Digital View: {share.file_doc.title}"
    
    return render(request, 'digital_share_view.html', context)

@login_required
def return_digital_share(request, token):
    share = get_object_or_404(models.DigitalShare, token=token, status='active')
    
    if request.user != share.shared_to:
         return JsonResponse({'status': 'failed', 'msg': 'Unauthorized.'})
    
    share.status = 'returned'
    share.returned_at = timezone.now()
    share.save()
    
    return JsonResponse({'status': 'success', 'msg': 'File returned successfully.'})

@login_required
def get_audit_highlights(request, pk):
    """
    Scans ForensicAudit for actions performed on a file between Issued/Received and Returned.
    """
    file_doc = get_object_or_404(models.File, pk=pk)
    
    # Find the most recent return (either Borrow or DigitalShare)
    last_digital = models.DigitalShare.objects.filter(file_doc=file_doc, status='returned').order_by('-returned_at').first()
    
    if not last_digital:
        return JsonResponse({'status': 'success', 'highlights': []})
    
    # Highlight actions performed by the recipient while they had the file
    highlights = models.ForensicAudit.objects.filter(
        user=last_digital.shared_to,
        timestamp__gte=last_digital.opened_at,
        timestamp__lte=last_digital.returned_at
    ).values('action', 'method', 'path', 'timestamp')
    
    return JsonResponse({'status': 'success', 'highlights': list(highlights)})

@login_required
def get_overdue_count(request):
    """
    Returns the count of overdue borrowed files.
    """
    from django.utils import timezone
    today = timezone.now().date()
    # status '0' means 'Issued'
    count = models.Borrow.objects.filter(status='0', return_date__lt=today).count()
    return JsonResponse({'status': 'success', 'count': count})

@login_required
def download_file_bundle(request, token):
    share = get_object_or_404(models.DigitalShare, token=token)
    file_doc = share.file_doc
    folios = models.Folio.objects.filter(filee=file_doc, delete_flag=0)
    
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
        # 1. Main File Metadata (PDF)
        pdf_buffer = io.BytesIO()
        p = canvas.Canvas(pdf_buffer, pagesize=letter)
        p.drawString(100, 750, f"RIFTS-X STRATEGIC INTELLIGENCE PLATFORM FILE: {file_doc.title}")
        p.drawString(100, 730, f"Reference Number: {file_doc.ref_num}")
        p.drawString(100, 710, f"Category: {file_doc.sub_category.category.name} > {file_doc.sub_category.name}")
        p.drawString(100, 690, "Description:")
        p.drawString(100, 670, file_doc.description[:500] if file_doc.description else "No description")
        p.showPage()
        p.save()
        zip_file.writestr(f"{file_doc.ref_num}_summary.pdf", pdf_buffer.getvalue())
        
        # 2. Main File Metadata (DOCX)
        doc = Document()
        doc.add_heading(file_doc.title, 0)
        doc.add_paragraph(f"Reference Number: {file_doc.ref_num}")
        doc.add_paragraph(f"Category: {file_doc.sub_category.category.name} > {file_doc.sub_category.name}")
        doc.add_heading("Description", level=1)
        doc.add_paragraph(file_doc.description or "No description")
        doc_buffer = io.BytesIO()
        doc.save(doc_buffer)
        zip_file.writestr(f"{file_doc.ref_num}_summary.docx", doc_buffer.getvalue())
        
        # 3. Folios
        for folio in folios:
            # Folio PDF
            f_pdf_buffer = io.BytesIO()
            p = canvas.Canvas(f_pdf_buffer, pagesize=letter)
            p.drawString(100, 750, f"FOLIO: {folio.title}")
            p.drawString(100, 730, f"Parent File: {file_doc.title} ({file_doc.ref_num})")
            p.drawString(100, 710, "Component Description:")
            p.drawString(100, 690, folio.description[:500] if folio.description else "No description")
            p.showPage()
            p.save()
            zip_file.writestr(f"components/{folio.title}.pdf", f_pdf_buffer.getvalue())
            
            # Folio DOCX
            f_doc = Document()
            f_doc.add_heading(f"Folio: {folio.title}", 0)
            f_doc.add_paragraph(f"Parent File: {file_doc.title}")
            f_doc.add_paragraph(folio.description or "No description")
            f_doc_buffer = io.BytesIO()
            f_doc.save(f_doc_buffer)
            zip_file.writestr(f"components/{folio.title}.docx", f_doc_buffer.getvalue())

    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer.read(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{file_doc.ref_num}_bundle.zip"'
    return response

@login_required
def recipient_dashboard(request):
    context = context_data(request)
    context['page'] = 'recipient_dashboard'
    context['page_title'] = "My Issued Files"
    
    # Get the borrower profile for the logged in user
    try:
        # Check if user is linked to a borrower profile
        borrower = models.Borrower.objects.get(user=request.user)
        context['my_borrows'] = models.Borrow.objects.filter(borrower=borrower, status='0').order_by('-date_added')
        context['returned_borrows'] = models.Borrow.objects.filter(borrower=borrower, status='1', return_confirmed=True).order_by('-date_added')
        context['pending_return_borrows'] = models.Borrow.objects.filter(borrower=borrower, status='1', return_confirmed=False).order_by('-date_added')
    except models.Borrower.DoesNotExist:
        # Fallback to matching by email if not explicitly linked
        borrower = models.Borrower.objects.filter(email=request.user.email).first()
        if borrower:
            context['my_borrows'] = models.Borrow.objects.filter(borrower=borrower, status='0').order_by('-date_added')
            context['returned_borrows'] = models.Borrow.objects.filter(borrower=borrower, status='1', return_confirmed=True).order_by('-date_added')
            context['pending_return_borrows'] = models.Borrow.objects.filter(borrower=borrower, status='1', return_confirmed=False).order_by('-date_added')
        else:
                context['my_borrows'] = []
                context['returned_borrows'] = []
                context['pending_return_borrows'] = []
            
    return render(request, 'recipient_dashboard.html', context)

@login_required
def submit_modification(request):
    resp = { 'status': 'failed', 'msg' : '' }
    if request.method == 'POST':
        try:
            borrow_id = request.POST.get('id')
            borrow = models.Borrow.objects.get(id=borrow_id)
            
            # Security check: Ensure the borrower is the owner of this record
            # check by user link or email
            is_owner = False
            if borrow.borrower.user == request.user:
                is_owner = True
            elif borrow.borrower.email == request.user.email:
                is_owner = True
                
            if not is_owner:
                resp['msg'] = "You are not authorized to modify this file."
                return HttpResponse(json.dumps(resp), content_type="application/json")
            
            borrow.modification_notes = request.POST.get('modification_notes')
            
            # Capture borrower's signature on return
            signature_data = request.POST.get('signature_data', '')
            if signature_data and signature_data != 'data:,':
                borrow.borrower_signature = signature_data
            
            if 'modified_file' in request.FILES:
                # Create a new FileVersion so the system keeps the updated copy (uploaded file - handled synchronously)
                uploaded = request.FILES['modified_file']
                uploaded.seek(0)
                version = models.FileVersion.objects.create(
                    file_doc=borrow.file_doc,
                    borrower=borrow.borrower,
                    notes=borrow.modification_notes,
                    file=uploaded
                )
                borrow.modified_file = request.FILES['modified_file']
            else:
                # If no new file upload, spawn a background thread to copy the existing attachment
                if borrow.file_doc and borrow.file_doc.file_attachment:
                    attachment_path = getattr(borrow.file_doc.file_attachment, 'path', None)
                    if not attachment_path or not os.path.exists(attachment_path):
                        resp['msg'] = 'The original attached file is missing from storage. Please upload a new file before finalizing the return.'
                        return HttpResponse(json.dumps(resp), content_type="application/json")

                    # Background worker: create a FileVersion by reading the existing attachment
                    def create_version_from_existing(borrow_id, notes):
                        try:
                            # Ensure DB connections are fresh in the thread
                            close_old_connections()
                            b = models.Borrow.objects.get(pk=borrow_id)
                            if not b.file_doc or not b.file_doc.file_attachment:
                                return
                            b.file_doc.file_attachment.open('rb')
                            data = b.file_doc.file_attachment.read()
                            b.file_doc.file_attachment.close()
                            models.FileVersion.objects.create(
                                file_doc=b.file_doc,
                                borrower=b.borrower,
                                notes=notes,
                                file=ContentFile(data, name=os.path.basename(b.file_doc.file_attachment.name))
                            )
                            # attach the modified_file pointer to the borrow for record
                            b.modified_file = b.file_doc.file_attachment
                            b.save()
                        except Exception:
                            # Log and continue; avoid crashing the request thread
                            logger.exception('Background file-version creation failed for borrow id %s', borrow_id)
                        finally:
                            close_old_connections()

                    thread = threading.Thread(target=create_version_from_existing, args=(borrow.id, borrow.modification_notes))
                    thread.daemon = True
                    thread.start()

            # Mark as Returned (status='1') but NOT confirmed yet
            # Issuer must separately confirm the return
            borrow.status = '1' # Returned (awaiting issuer confirmation)
            borrow.return_confirmed = False
            borrow.confirmed_by = None
            borrow.confirmed_at = None
            borrow.save()
            
            # Update File status to reflect it's pending return confirmation
            file_doc = borrow.file_doc
            file_doc.f_status = 'pending_confirmation'
            file_doc.save()
            
            # Create an in-app notification for the issuer (last handler) so front-end polling plays the sound
            try:
                issuer = None
                if file_doc and getattr(file_doc, 'last_handler', None):
                    issuer = file_doc.last_handler

                # Choose a project context: prefer a linked project, else one owned by issuer, else any project
                project = None
                if file_doc and hasattr(file_doc, 'linked_projects'):
                    project = file_doc.linked_projects.first()
                if not project and issuer:
                    from .models import Project
                    project = Project.objects.filter(owner=issuer).first()
                if not project:
                    from .models import Project
                    project = Project.objects.first()

                if issuer and project:
                    from .models import ProjectAlert
                    alert_msg = f"Returned file: {file_doc.ref_num} was returned by {borrow.borrower.name()}. Please review and confirm."
                    ProjectAlert.objects.create(
                        project=project,
                        recipient=issuer,
                        alert_type='PhaseReady',
                        message=alert_msg
                    )

                # Email the issuer as a fallback/secondary channel
                try:
                    if issuer and issuer.email:
                        subject = f'RIFTS-X: File Returned - {file_doc.ref_num}'
                        html_message = render_to_string('registry/email/borrow_notification.html', {
                            'ctx_issuer_name': issuer.get_full_name() or issuer.username,
                            'ctx_file_ref': file_doc.ref_num,
                            'ctx_file_title': file_doc.title,
                            'ctx_borrower_name': borrow.borrower.name(),
                            'ctx_return_time': timezone.now().strftime('%d-%b-%Y %H:%M')
                        })
                        plain_message = strip_tags(html_message)
                        send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, [issuer.email], html_message=html_message, fail_silently=True)
                except Exception:
                    logger.exception('Failed to send return notification email to issuer')
            except Exception:
                logger.exception('Failed to create in-app notification for issuer')

            resp['status'] = 'success'
            resp['msg'] = "File returned with your signature. Awaiting issuer confirmation."
        except Exception as e:
            resp['msg'] = str(e)
            
    return HttpResponse(json.dumps(resp), content_type="application/json")

def access_with_token(request, token):
    # Find the borrow record with this token
    borrow = get_object_or_404(models.Borrow, access_token=token)
    
    # Check if token is expired
    if borrow.token_expiry and timezone.now() > borrow.token_expiry:
        return HttpResponse("This access link has expired. Please contact the administrator.", status=403)
    
    folder_url = reverse('borrow-folder-view', kwargs={'pk': borrow.pk})

    # If user is already logged in as the correct person
    if request.user.is_authenticated and (request.user == borrow.borrower.user or request.user.email == borrow.borrower.email):
        return redirect(folder_url)
    
    # Otherwise, redirect to login with a message and preserve destination
    request.session['borrow_access_token'] = token
    request.session['login_next'] = folder_url
    login_next = urlquote(folder_url)
    messages.info(request, "Secure link verified. Please log in with your credentials to access the issued folder.")
    return redirect(f"{reverse('login-page')}?next={login_next}")

@login_required
def borrow_folder_view(request, pk):
    borrow = get_object_or_404(models.Borrow, pk=pk)
    if not request.user.is_superuser and request.user != borrow.borrower.user and request.user.email != borrow.borrower.email:
        return HttpResponseForbidden("Unauthorized")
    if not borrow.issued_folder:
        messages.error(request, "No issued folder is associated with this record.")
        return redirect('recipient-dashboard')

    files = borrow.issued_folder.files.all()
    context = context_data(request)
    context.update({
        'page_title': f'Issued Folder: {borrow.issued_folder.name}',
        'borrow': borrow,
        'files': files,
        'permission_text': 'Edit Allowed' if borrow.folder_permission == 'edit' else 'View Only'
    })
    return render(request, 'registry/borrow_folder_view.html', context)

@login_required
def edit_issued_file(request, borrow_id, file_id):
    """Allow borrower to edit an issued file within the browser."""
    borrow = get_object_or_404(models.Borrow, pk=borrow_id)
    cloud_file = get_object_or_404(models.CloudFile, pk=file_id)
    
    # Verify ownership and permissions
    if not request.user.is_superuser and request.user != borrow.borrower.user and request.user.email != borrow.borrower.email:
        return HttpResponseForbidden("Unauthorized")
    
    if borrow.folder_permission != 'edit':
        messages.error(request, "You do not have edit permission for this file.")
        return redirect('borrow-folder-view', pk=borrow.pk)
    
    if cloud_file not in borrow.issued_folder.files.all():
        return HttpResponseForbidden("This file is not part of your issued folder.")
    
    context = context_data(request)
    document_html = ''
    is_docx_editable = False

    latest_version = cloud_file.latest_version
    if latest_version and cloud_file.name.lower().endswith('.docx'):
        try:
            document_html = docx_version_to_html(latest_version)
            is_docx_editable = True
        except Exception:
            document_html = ''
            is_docx_editable = False

    context.update({
        'page_title': f'Edit: {cloud_file.name}',
        'borrow': borrow,
        'cloud_file': cloud_file,
        'latest_version': latest_version,
        'document_html': document_html,
        'is_docx_editable': is_docx_editable,
    })
    
    return render(request, 'registry/edit_issued_file.html', context)

@login_required
def save_issued_file_edit(request):
    resp = {'status': 'failed', 'msg': ''}
    if request.method != 'POST':
        resp['msg'] = 'Invalid request method.'
        return JsonResponse(resp, status=405)

    try:
        borrow_id = request.POST.get('borrow_id')
        file_id = request.POST.get('file_id')
        borrow = get_object_or_404(models.Borrow, pk=borrow_id)
        cloud_file = get_object_or_404(models.CloudFile, pk=file_id)

        if not request.user.is_superuser and request.user != borrow.borrower.user and request.user.email != borrow.borrower.email:
            resp['msg'] = 'Unauthorized.'
            return JsonResponse(resp, status=403)

        if borrow.folder_permission != 'edit':
            resp['msg'] = 'You do not have edit permission for this file.'
            return JsonResponse(resp, status=403)

        if not borrow.issued_folder or cloud_file not in borrow.issued_folder.files.all():
            resp['msg'] = 'This file is not part of your issued folder.'
            return JsonResponse(resp, status=403)

        edit_notes = request.POST.get('edit_notes', '').strip()
        latest_version = cloud_file.latest_version
        edited_html = request.POST.get('edited_html', '').strip()

        if edited_html:
            # Try converting edited HTML back to DOCX using pypandoc (requires pandoc).
            converted_bytes = None
            if pypandoc:
                try:
                    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as out:
                        pypandoc.convert_text(edited_html, 'docx', format='html', outputfile=out.name)
                        out.flush()
                        out.seek(0)
                        converted_bytes = open(out.name, 'rb').read()
                except Exception:
                    converted_bytes = None

            if converted_bytes:
                # Create a new CloudFileVersion with the converted docx bytes
                next_version = latest_version.version_number + 1 if latest_version else 1
                models.CloudFileVersion.objects.create(
                    cloud_file=cloud_file,
                    version_number=next_version,
                    file_content=ContentFile(converted_bytes, name=cloud_file.name),
                    uploaded_by=request.user,
                    commit_message=edit_notes or 'Edited document in browser',
                    file_size=len(converted_bytes),
                    checksum=hashlib.sha256(converted_bytes).hexdigest(),
                )
            else:
                # Fallback: use CloudService.create_document which converts HTML -> DOCX via python-docx parser
                CloudService.create_document(
                    cloud_file.folder,
                    cloud_file.name,
                    edited_html,
                    request.user,
                    commit_message=edit_notes or 'Edited document in browser',
                    is_internal_only=cloud_file.is_internal_only,
                )
        elif 'edited_file' in request.FILES and request.FILES['edited_file']:
            uploaded = request.FILES['edited_file']
            uploaded_data = uploaded.read()
            uploaded.seek(0)
            checksum = hashlib.sha256(uploaded_data).hexdigest()
            next_version = latest_version.version_number + 1 if latest_version else 1
            models.CloudFileVersion.objects.create(
                cloud_file=cloud_file,
                version_number=next_version,
                file_content=ContentFile(uploaded_data, name=uploaded.name),
                uploaded_by=request.user,
                commit_message=edit_notes,
                file_size=uploaded.size,
                checksum=checksum,
            )
        else:
            if not latest_version:
                resp['msg'] = 'No existing version available to preserve.'
                return JsonResponse(resp, status=400)

            latest_version.file_content.open('rb')
            existing_data = latest_version.file_content.read()
            latest_version.file_content.close()
            next_version = latest_version.version_number + 1
            models.CloudFileVersion.objects.create(
                cloud_file=cloud_file,
                version_number=next_version,
                file_content=ContentFile(existing_data, name=os.path.basename(latest_version.file_content.name)),
                uploaded_by=request.user,
                commit_message=edit_notes or 'Saved system-managed version without upload.',
                file_size=len(existing_data),
                checksum=hashlib.sha256(existing_data).hexdigest(),
            )

        cloud_file.updated_at = timezone.now()
        cloud_file.save()

        resp['status'] = 'success'
        resp['msg'] = 'Changes saved and version history updated.'
    except Exception as e:
        resp['msg'] = str(e)

    return JsonResponse(resp)

@login_required
def get_onlyoffice_document_config(request, borrow_id, file_id):
    """Get OnlyOffice document configuration and serve DOCX file for editing."""
    import tempfile
    from django.views.static import serve as serve_static
    
    try:
        borrow = get_object_or_404(models.Borrow, pk=borrow_id)
        cloud_file = get_object_or_404(models.CloudFile, pk=file_id)
        
        # Verify permissions
        if not request.user.is_superuser and request.user != borrow.borrower.user and request.user.email != borrow.borrower.email:
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        if borrow.folder_permission != 'edit':
            return JsonResponse({'error': 'No edit permission'}, status=403)
        
        if cloud_file not in borrow.issued_folder.files.all():
            return JsonResponse({'error': 'File not in folder'}, status=403)
        
        latest_version = cloud_file.latest_version
        if not latest_version or not cloud_file.name.lower().endswith('.docx'):
            return JsonResponse({'error': 'File is not a valid DOCX'}, status=400)
        
        # Get file path and generate config
        file_path = latest_version.file_content.path
        document_config = OnlyOfficeService.generate_document_config(
            file_path=file_path,
            document_title=cloud_file.name,
            edit_mode=True,
            user_id=request.user.id,
            user_name=request.user.get_full_name() or request.user.username
        )
        
        # Set document URL and callback URL
        document_config['document']['url'] = request.build_absolute_uri(
            reverse('get-onlyoffice-file', args=[borrow_id, file_id])
        )
        document_config['editorConfig']['callbackUrl'] = request.build_absolute_uri(
            reverse('onlyoffice-callback', args=[borrow_id, file_id])
        )
        
        # Sign the config if secret is configured
        from django.conf import settings
        if getattr(settings, 'ONLYOFFICE_SECRET', None):
            config_json = json.dumps(document_config, separators=(',', ':'), sort_keys=True)
            document_config['token'] = OnlyOfficeService.sign_token(config_json)
        
        return JsonResponse(document_config)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_onlyoffice_file(request, borrow_id, file_id):
    """Serve DOCX file for OnlyOffice Document Server."""
    try:
        borrow = get_object_or_404(models.Borrow, pk=borrow_id)
        cloud_file = get_object_or_404(models.CloudFile, pk=file_id)
        
        # Verify permissions
        if not request.user.is_superuser and request.user != borrow.borrower.user and request.user.email != borrow.borrower.email:
            return HttpResponseForbidden("Unauthorized")
        
        latest_version = cloud_file.latest_version
        if not latest_version:
            raise Http404("No file version found")
        
        # Serve the DOCX file
        file_path = latest_version.file_content.path
        return FileResponse(open(file_path, 'rb'), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    
    except Exception as e:
        return HttpResponseForbidden(f"Error: {str(e)}")

@csrf_exempt
@login_required
def onlyoffice_callback(request, borrow_id, file_id):
    """Handle OnlyOffice Document Server callback when document is saved."""
    resp = {'error': 0}
    
    if request.method != 'POST':
        return JsonResponse({'error': 1, 'msg': 'Method not allowed'}, status=405)
    
    try:
        # Get callback data
        callback_data = json.loads(request.body.decode('utf-8'))
        status = callback_data.get('status')
        
        # Verify signature if secret is configured
        from django.conf import settings
        secret = getattr(settings, 'ONLYOFFICE_SECRET', None)
        if secret:
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                signature = auth_header[7:]
                if not OnlyOfficeService.verify_callback_signature(callback_data, signature, secret):
                    return JsonResponse({'error': 1, 'msg': 'Invalid signature'}, status=403)
        
        # Handle different statuses
        if status == 2:  # Document ready for saving
            download_url = callback_data.get('url')
            if not download_url:
                return JsonResponse({'error': 1, 'msg': 'No download URL'}, status=400)
            
            try:
                borrow = get_object_or_404(models.Borrow, pk=borrow_id)
                cloud_file = get_object_or_404(models.CloudFile, pk=file_id)
                
                # Verify permissions
                if not request.user.is_superuser and request.user != borrow.borrower.user and request.user.email != borrow.borrower.email:
                    return JsonResponse({'error': 1, 'msg': 'Unauthorized'}, status=403)
                
                # Download edited document
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
                    temp_path = tmp.name
                
                if download_edited_document(download_url, temp_path):
                    # Read downloaded file
                    with open(temp_path, 'rb') as f:
                        edited_data = f.read()
                    
                    # Create new version
                    latest_version = cloud_file.latest_version
                    next_version = latest_version.version_number + 1 if latest_version else 1
                    
                    models.CloudFileVersion.objects.create(
                        cloud_file=cloud_file,
                        version_number=next_version,
                        file_content=ContentFile(edited_data, name=cloud_file.name),
                        uploaded_by=request.user,
                        commit_message='Edited in OnlyOffice Document Editor',
                        file_size=len(edited_data),
                        checksum=hashlib.sha256(edited_data).hexdigest(),
                    )
                    
                    cloud_file.updated_at = timezone.now()
                    cloud_file.save()
                    
                    # Clean up temp file
                    os.unlink(temp_path)
                    
                    return JsonResponse({'error': 0})
                else:
                    return JsonResponse({'error': 1, 'msg': 'Failed to download document'}, status=500)
            
            except Exception as e:
                return JsonResponse({'error': 1, 'msg': str(e)}, status=500)
        
        elif status == 1:  # Document is being edited
            return JsonResponse({'error': 0})
        
        else:
            # Process callback using service
            return JsonResponse(OnlyOfficeService.process_callback(callback_data))
    
    except Exception as e:
        return JsonResponse({'error': 1, 'msg': str(e)}, status=500)

@login_required
def confirm_borrow_return(request, borrow_id):
    """Issuer confirmation of a returned borrow."""
    borrow = get_object_or_404(models.Borrow, pk=borrow_id)
    
    # Only the issuer (or superuser) can confirm
    if not request.user.is_superuser and borrow.file_doc.last_handler and request.user != borrow.file_doc.last_handler:
        return HttpResponseForbidden("Unauthorized")
    
    if request.method == 'POST':
        # Verify issuer signature
        issuer_signature = request.POST.get('issuer_signature', '')
        if not issuer_signature or issuer_signature == 'data:,':
            messages.error(request, "Issuer signature is required for confirmation.")
            return redirect('confirm-borrow-return', borrow_id=borrow.id)
        
        # Confirm the return
        borrow.issuer_signature = issuer_signature
        borrow.return_confirmed = True
        borrow.confirmed_by = request.user
        borrow.confirmed_at = timezone.now()
        borrow.save()
        
        # Mark file as available again
        file_doc = borrow.file_doc
        file_doc.f_status = 'available'
        file_doc.save()
        
        # Send confirmation email to borrower
        try:
            if borrow.borrower.email:
                subject = f'RIFTS-X: Return Confirmed - {file_doc.ref_num}'
                html_message = render_to_string('registry/email/return_confirmed.html', {
                    'ctx_borrower_name': borrow.borrower.name(),
                    'ctx_file_ref': file_doc.ref_num,
                    'ctx_file_title': file_doc.title,
                    'ctx_issuer_name': request.user.get_full_name() or request.user.username,
                    'ctx_confirmed_at': borrow.confirmed_at.strftime('%d-%b-%Y %H:%M'),
                })
                plain_message = strip_tags(html_message)
                
                send_mail(
                    subject,
                    plain_message,
                    request.user.email or None,
                    [borrow.borrower.email],
                    html_message=html_message,
                    fail_silently=True
                )
        except Exception as e:
            logger.warning(f"Failed to send return confirmation email: {e}")
        
        messages.success(request, f"Return confirmed for {file_doc.title}.")
        return redirect('view-borrow-pk', pk=borrow.id)
    
    # GET - Show confirmation page
    context = context_data(request)
    context.update({
        'page_title': f'Confirm Return: {borrow.file_doc.ref_num}',
        'borrow': borrow,
        'file_doc': borrow.file_doc
    })
    
    return render(request, 'registry/confirm_borrow_return.html', context)

@login_required
def download_issued_folder_zip(request, pk):
    borrow = get_object_or_404(models.Borrow, pk=pk)
    if not request.user.is_superuser and request.user != borrow.borrower.user and request.user.email != borrow.borrower.email:
        return HttpResponseForbidden("Unauthorized")
    if not borrow.folder_zip:
        raise Http404("Folder ZIP not available")

    filename = os.path.basename(borrow.folder_zip.name)
    response = FileResponse(borrow.folder_zip.open('rb'), as_attachment=True, filename=filename)
    return response

@login_required
def file_timeline(request, pk):
    from registry.services.location import LocationIntelligence
    file_doc = get_object_or_404(File, pk=pk)
    logs = CustodyLog.objects.filter(file_doc=file_doc).order_by('-timestamp')
    
    context = {
        'page_title': f'Timeline: {file_doc.ref_num}',
        'file_doc': file_doc,
        'logs': logs,
        'location': LocationIntelligence.get_last_known_location(file_doc)
    }
    return render(request, 'file_timeline.html', context)

def handover_file(request):
    if request.method == 'POST':
        file_id = request.POST.get('file_id')
        target_user_id = request.POST.get('target_user_id')
        reason = request.POST.get('reason')
        file_obj = get_object_or_404(File, id=file_id)

        target_user = get_object_or_404(User, id=target_user_id)
        
        # Physical location tracking
        building = request.POST.get('building')
        floor = request.POST.get('floor')
        office = request.POST.get('office')
        cabinet = request.POST.get('cabinet')
        shelf = request.POST.get('shelf')
        
        location = None
        if building:
            location = models.FileLocation.objects.create(
                building=building,
                floor=floor,
                office=office,
                cabinet=cabinet,
                shelf=shelf
            )
            
        from registry.services.custody import CustodyService
        CustodyService.handover(file_obj, request.user, target_user, reason, location=location)
        
        messages.success(request, f"File {file_obj.ref_num} handover successful.")
        return redirect('file-timeline', pk=file_id)
    return redirect('home-page')

@login_required
def federated_transfer_file(request):
    if request.method == 'POST':
        resp = {'status': 'failed', 'msg': ''}
        try:
            file_id = request.POST.get('file_id')
            target_org_id = request.POST.get('target_org_id')
            target_dept_name = request.POST.get('target_dept_name', '').strip()
            reason = request.POST.get('reason', '').strip()

            if not file_id or not target_org_id or not target_dept_name or not reason:
                resp['msg'] = 'All fields (File, Organization, Department, and Reason) are required for federated transfer.'
                return JsonResponse(resp)

            file_obj = get_object_or_404(File, id=file_id)
            target_org = get_object_or_404(Organization, id=target_org_id)

            from registry.services.custody import CustodyService
            CustodyService.federated_transfer(file_obj, request.user, target_org, target_dept_name, reason)

            resp['status'] = 'success'
            resp['msg'] = f"File {file_obj.ref_num} successfully initiated for federated transfer to {target_org.name}."
            messages.success(request, resp['msg'])

        except Exception as e:
            resp['msg'] = f"Federation Error: {str(e)}"

        return JsonResponse(resp)

    return JsonResponse({'status': 'failed', 'msg': 'Invalid request method.'})

@login_required
def organizations(request):
    context = context_data(request)
    context['page_title'] = "Federated Organizations"
    context['organizations'] = models.Organization.objects.all()
    return render(request, 'organizations.html', context)

@login_required
def federation_links(request):
    context = context_data(request)
    context['page_title'] = "Federation Links"
    context['links'] = models.FederationLink.objects.all()
    return render(request, 'federation_links.html', context)

@login_required
def manage_organization(request, pk=None):
    context = context_data(request)
    if pk:
        org = get_object_or_404(models.Organization, pk=pk)
        context['org'] = org
    return render(request, 'manage_organization.html', context)

@login_required
def save_organization(request):
    if request.method == 'POST':
        from django.db import IntegrityError
        id = request.POST.get('id')
        try:
            if id:
                org = get_object_or_404(models.Organization, pk=id)
                org.name = request.POST.get('name')
                org.code = request.POST.get('code')
                org.api_endpoint = request.POST.get('api_endpoint')
                org.save()
            else:
                models.Organization.objects.create(
                    name=request.POST.get('name'),
                    code=request.POST.get('code'),
                    api_endpoint=request.POST.get('api_endpoint')
                )
        except IntegrityError:
            return JsonResponse({'status': 'failed', 'msg': 'An organization with this Identifier Code already exists.'})
        return JsonResponse({'status': 'success', 'msg': 'Organization saved successfully'})
    return JsonResponse({'status': 'failed', 'msg': 'Invalid request'})

@login_required
def federated_transfer_modal(request):
    file_id = request.GET.get('id')
    file_obj = get_object_or_404(File, id=file_id)
    organizations = Organization.objects.filter(is_local=False)
    context = {
        'file_obj': file_obj,
        'organizations': organizations,
    }
    return render(request, 'manage_federated_transfer.html', context)

@login_required
def transfer_file(request):
    if request.method == 'POST':
        resp = {'status': 'failed', 'msg': ''}
        try:
            file_id = request.POST.get('file_id')
            target_dept_id = request.POST.get('target_dept_id')
            reason = request.POST.get('reason', '').strip()

            if not file_id:
                resp['msg'] = 'File ID is missing.'
                return JsonResponse(resp)
            if not target_dept_id:
                resp['msg'] = 'Please select a target department.'
                return JsonResponse(resp)
            if not reason:
                resp['msg'] = 'A reason for the transfer is required.'
                return JsonResponse(resp)

            file_obj = get_object_or_404(File, id=file_id)
            target_dept = get_object_or_404(Department, id=target_dept_id)

            # Physical location tracking
            building = request.POST.get('building', '').strip()
            floor = request.POST.get('floor', '').strip()
            office = request.POST.get('office', '').strip()
            cabinet = request.POST.get('cabinet', '').strip()
            shelf = request.POST.get('shelf', '').strip()

            location = None
            if building and floor and cabinet and shelf:
                location = models.FileLocation.objects.create(
                    building=building,
                    floor=floor,
                    office=office,
                    cabinet=cabinet,
                    shelf=shelf
                )

            from registry.services.custody import CustodyService
            CustodyService.transfer(file_obj, request.user, target_dept, reason, location=location)

            resp['status'] = 'success'
            resp['msg'] = f"File {file_obj.ref_num} successfully transferred to {target_dept.name}."
            messages.success(request, resp['msg'])

        except Exception as e:
            resp['msg'] = f"An error occurred: {str(e)}"

        return JsonResponse(resp)

    return JsonResponse({'status': 'failed', 'msg': 'Invalid request method.'})

@login_required
def acknowledge_transfer(request, pk):
    from registry.services.custody import CustodyService
    if CustodyService.acknowledge_receipt(pk, request.user):
        messages.success(request, "Receipt acknowledged successfully.")
    else:
        messages.error(request, "Failed to acknowledge receipt.")
    
    # Redirect back to where they came from
    return redirect(request.META.get('HTTP_REFERER', 'home-page'))

def handover_modal(request):
    file_id = request.GET.get('id')
    file_obj = get_object_or_404(File, id=file_id)
    users = User.objects.exclude(id=request.user.id).all()
    from registry.services.location import LocationIntelligence
    context = {
        'file_obj': file_obj,
        'users': users,
        'location': LocationIntelligence.get_last_known_location(file_obj)
    }
    return render(request, 'manage_handover.html', context)

def transfer_modal(request):
    file_id = request.GET.get('id')
    file_obj = get_object_or_404(File, id=file_id)
    departments = Department.objects.all()
    from registry.services.location import LocationIntelligence
    context = {
        'file_obj': file_obj,
        'departments': departments,
        'location': LocationIntelligence.get_last_known_location(file_obj)
    }
    return render(request, 'manage_transfer.html', context)

@login_required
@role_required(allowed_roles=['Executive'])
def executive_dashboard(request):
    if not request.user.is_superuser:
        messages.error(request, "Access Denied: Forensic/Executive access required.")
        return redirect('home-page')
    from registry.services.sla import SLAManager
    from registry.services.risk import RiskEngine
    from registry.services.location import LocationIntelligence
    from registry.models import CustodyLog, Department
    
    # Calculate Last 24h Movement
    yesterday = timezone.now() - timedelta(days=1)
    movement_count = CustodyLog.objects.filter(timestamp__gte=yesterday).count()
    
    context = {
        'page_title': 'Executive Intelligence Dashboard',
        'health': SLAManager.get_system_health(),
        'breached_count': SLAManager.get_breached_count(),
        'critical_count': RiskEngine.get_critical_count(),
        'movement_count': movement_count,
        'departments': Department.objects.all().order_by('-efficiency_score'),
        'location_heatmap': LocationIntelligence.get_location_heatmap(),
        'department_heatmap': LocationIntelligence.get_department_heatmap()
    }
    return render(request, 'executive_dashboard.html', context)

@login_required
def forensic_audit_export(request, pk):
    if not request.user.is_superuser:
        messages.error(request, "Access Denied: Forensic/Executive access required.")
        return redirect('home-page')
    from registry.models import File, CustodyLog
    import csv
    
    file_obj = get_object_or_404(File, pk=pk)
    logs = CustodyLog.objects.filter(file_doc=file_obj).order_by('timestamp')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="Forensic_Audit_{file_obj.ref_num}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Immutable Audit Log', 'RIFTS-X Forensic Mode'])
    writer.writerow(['File Reference', file_obj.ref_num])
    writer.writerow(['Exported By', request.user.username])
    writer.writerow(['Export Date', timezone.now()])
    writer.writerow([])
    writer.writerow(['Timestamp', 'Action', 'From (Officer/Dept)', 'To (Officer/Dept)', 'Reason', 'Location'])
    
    for log in logs:
        from_val = log.from_department.name if log.from_department else "SYSTEM"
        to_val = log.to_department.name if log.to_department else "-"
        handler_val = log.handler.username if log.handler else "-"
        writer.writerow([
            log.timestamp,
            log.action,
            f"{handler_val} ({from_val})",
            to_val,
            log.reason,
            str(log.location) if log.location else "-"
        ])
    
    return response

# --- Leave Management Views ---
@login_required
def leave_list(request):
    context = context_data(request)
    context['page_title'] = "My Leave Requests"
    context['leaves'] = models.LeaveRequest.objects.filter(user=request.user).order_by('-date_applied')
    return render(request, 'leave_list.html', context)


@login_required
def ai_assistant(request):
    context = context_data(request)
    context['page_title'] = "AI Query Assistant"
    return render(request, 'ai_assistant.html', context)

@login_required
def process_ai_query(request):
    if request.method == 'POST':
        query = request.POST.get('query', '').strip()
        if not query:
            return JsonResponse({'status': 'failed', 'msg': 'Query cannot be empty'}, status=400)
        
        try:
            # Try to use enhanced AI Assistant Service
            try:
                from registry.services.ai_assistant_enhanced import EnhancedAIAssistantService
                results = EnhancedAIAssistantService.parse_query(query)
                return JsonResponse({'status': 'success', 'results': results})
            except (ImportError, ModuleNotFoundError):
                # Fallback to basic service
                logger.info("Enhanced service not available, using basic service")
                results = AIAssistantService.parse_query(query)
                return JsonResponse({'status': 'success', 'results': results})
                
        except Exception as e:
            logger.exception(f"Error processing AI query: {query}")
            return JsonResponse({
                'status': 'failed', 
                'msg': f'Error processing query: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'failed', 
        'msg': 'Only POST requests are allowed'
    }, status=405)

@login_required
def query_with_rag(request):
    """Query system using RAG with document analysis capabilities."""
    if request.method == 'POST':
        query = request.POST.get('query', '').strip()
        if not query:
            return JsonResponse({'status': 'failed', 'msg': 'Query cannot be empty'}, status=400)
        
        try:
            from registry.services.ai_assistant_enhanced import EnhancedAIAssistantService
            
            # Get uploaded documents if any
            document_files = []
            for uploaded_file in request.FILES.getlist('documents'):
                # Save to temp location
                import tempfile
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1])
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                temp_file.close()
                document_files.append(temp_file.name)
            
            # Query with RAG
            results = EnhancedAIAssistantService.query_with_rag(query, document_files)
            
            # Clean up temp files
            for temp_file in document_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass
            
            return JsonResponse({'status': 'success', 'results': results})
        
        except Exception as e:
            logger.exception(f"Error processing RAG query: {query}")
            return JsonResponse({
                'status': 'failed',
                'msg': f'Error processing query: {str(e)}'
            }, status=500)
    
    return JsonResponse({'status': 'failed', 'msg': 'Only POST requests are allowed'}, status=405)

@login_required
def analyze_document(request):
    """Analyze uploaded document (PDF, DOCX, image, etc)."""
    if request.method == 'POST':
        if 'document' not in request.FILES:
            return JsonResponse({'status': 'failed', 'msg': 'No document provided'}, status=400)
        
        try:
            from registry.services.rag_system import DocumentAnalyzer
            
            uploaded_file = request.FILES['document']
            
            # Save to temp location
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1])
            for chunk in uploaded_file.chunks():
                temp_file.write(chunk)
            temp_file.close()
            
            # Analyze document
            analysis = DocumentAnalyzer.analyze_document(temp_file.name)
            
            # Clean up
            try:
                os.unlink(temp_file.name)
            except:
                pass
            
            return JsonResponse({'status': 'success', 'analysis': analysis})
        
        except Exception as e:
            logger.exception(f"Error analyzing document")
            return JsonResponse({
                'status': 'failed',
                'msg': f'Error analyzing document: {str(e)}'
            }, status=500)
    
    return JsonResponse({'status': 'failed', 'msg': 'Only POST requests are allowed'}, status=405)

@login_required
def rag_knowledge_base(request):
    """Display and manage RAG knowledge base."""
    try:
        from registry.services.rag_system import SystemComponentsKnowledgeBase, RAGRetriever
        
        context = context_data(request)
        context['page_title'] = 'RAG Knowledge Base'
        
        # Build knowledge base
        kb = SystemComponentsKnowledgeBase.build_system_knowledge()
        
        # Count statistics
        context['stats'] = {
            'total_models': len(kb['components'].get('models', {})),
            'total_services': len(kb['components'].get('services', {})),
            'total_workflows': len(kb['workflows']),
        }
        
        context['components'] = kb['components']
        context['workflows'] = kb['workflows']
        
        return render(request, 'rag_knowledge_base.html', context)
    
    except Exception as e:
        return JsonResponse({'status': 'failed', 'msg': str(e)}, status=500)

# --- Service Tickets Views ---

@login_required
def service_tickets(request):
    context = context_data(request)
    context['page_title'] = "Inter-Department Service Desk"
    
    # Staff/Superusers from target departments can see tickets assigned to them or their department
    # Regular users can only see their own tickets
    if request.user.is_superuser:
        context['tickets'] = models.ServiceTicket.objects.all()
    else:
        # Check if user is linked to a department via Borrower profile
        user_dept = None
        if hasattr(request.user, 'borrower_profile'):
            user_dept = request.user.borrower_profile.department
        
        if user_dept:
            # See tickets they requested OR tickets sent to their department
            context['tickets'] = models.ServiceTicket.objects.filter(
                Q(requester=request.user) | Q(department=user_dept)
            ).distinct()
        else:
            context['tickets'] = models.ServiceTicket.objects.filter(requester=request.user)
            
    return render(request, 'service_tickets.html', context)

@login_required
def manage_ticket(request, pk=None):
    context = context_data(request)
    if pk:
        ticket = get_object_or_404(models.ServiceTicket, pk=pk)
        form = SaveServiceTicket(instance=ticket)
    else:
        form = SaveServiceTicket()
    
    context['form'] = form
    context['pk'] = pk
    return render(request, 'manage_ticket.html', context)

@login_required
def save_service_ticket(request):
    if request.method == 'POST':
        pk = request.POST.get('id')
        if pk:
            ticket = get_object_or_404(models.ServiceTicket, pk=pk)
            form = SaveServiceTicket(request.POST, instance=ticket)
        else:
            form = SaveServiceTicket(request.POST)
            
        if form.is_valid():
            is_new = not pk
            ticket = form.save(commit=False)
            if is_new:
                ticket.requester = request.user
            ticket.save()

            # On new service request, notify all users in that department
            if is_new and ticket.department:
                try:
                    from django.db.models import Q
                    from django.contrib.auth.models import User
                    dept_users = User.objects.filter(
                        Q(borrower_profile__department=ticket.department) |
                        Q(security_profile__department=ticket.department)
                    ).distinct()

                    dept_name = ticket.department.name
                    requester_name = ticket.requester.get_full_name() or ticket.requester.username
                    for u in dept_users:
                        if u != request.user:
                            try:
                                send_system_notification(
                                    recipient=u,
                                    category="Service Request",
                                    title=f"New Service Request: {ticket.subject}",
                                    message=f"A new service ticket has been submitted for {dept_name} by {requester_name} (Priority: {ticket.priority}, Category: {ticket.category}). Subject: {ticket.subject}",
                                    sender=request.user,
                                    link_url=f"/registry/tickets/view/{ticket.id}/",
                                    channel="Multi-Channel"
                                )
                            except Exception:
                                pass
                except Exception:
                    pass

            return JsonResponse({'status': 'success', 'msg': 'Service ticket saved successfully'})
        else:
            return JsonResponse({'status': 'failed', 'msg': 'Form is invalid', 'errors': form.errors})
    return JsonResponse({'status': 'failed', 'msg': 'Invalid request'})

@login_required
def view_ticket(request, pk):
    context = context_data(request)
    ticket = get_object_or_404(models.ServiceTicket, pk=pk)
    context['ticket'] = ticket
    context['updates'] = ticket.updates.all()
    context['update_form'] = TicketUpdateForm()
    context['page_title'] = f"Ticket: {ticket.subject}"
    return render(request, 'view_ticket.html', context)

@login_required
def save_ticket_update(request, pk):
    if request.method == 'POST':
        ticket = get_object_or_404(models.ServiceTicket, pk=pk)
        form = TicketUpdateForm(request.POST)
        if form.is_valid():
            update = form.save(commit=False)
            update.ticket = ticket
            update.user = request.user
            update.save()
            
            if update.new_status:
                ticket.status = update.new_status
                ticket.save()
                
            return JsonResponse({'status': 'success', 'msg': 'Update posted successfully'})
        else:
            return JsonResponse({'status': 'failed', 'msg': 'Invalid data'})
    return JsonResponse({'status': 'failed', 'msg': 'Invalid request'})

@login_required
def delete_ticket(request, pk):
    ticket = get_object_or_404(models.ServiceTicket, pk=pk)
    if request.user == ticket.requester or request.user.is_superuser:
        ticket.delete()
        return JsonResponse({'status': 'success', 'msg': 'Ticket deleted successfully'})
    return JsonResponse({'status': 'failed', 'msg': 'Permission denied'})

def get_hierarchy_tier_for_user(user):
    """
    Classifies a user into their ZRP organizational tier:
    - officer: Day-to-day operational personnel
    - management: Systems Manager, Supt ICT, Chief Tech
    - deputy_director: Deputy Director ICT, Deputy Director Communications, Deputy Director IT
    - chief_director: Chief Director (Apex)
    """
    role = None
    if hasattr(user, 'security_profile') and getattr(user.security_profile, 'role', None):
        role = user.security_profile.role
    
    if role == 'Chief Director':
        return 'chief_director'
    elif role in ['Deputy Director ICT', 'Deputy Director IT', 'Deputy Director Communications']:
        return 'deputy_director'
    elif role in ['Systems Manager', 'System Manager', 'Supt ICT', 'Chief Tech']:
        return 'management'
    return 'officer'


def get_leave_approvers_for_stage(user, stage):
    """
    Returns the users who are authorized to approve for a specific hierarchy tier stage.
    """
    dept = None
    if hasattr(user, 'security_profile') and getattr(user.security_profile, 'department', None):
        dept = user.security_profile.department
    elif hasattr(user, 'borrower_profile') and getattr(user.borrower_profile, 'department', None):
        dept = user.borrower_profile.department

    approvers = []
    def add_users(qs):
        for u in qs:
            if u.id != user.id and u not in approvers:
                approvers.append(u)

    if stage == 'pending_management':
        mgmt_roles = ['Systems Manager', 'System Manager', 'Supt ICT', 'Chief Tech']
        if dept:
            add_users(User.objects.filter(security_profile__department=dept, security_profile__role__in=mgmt_roles, is_active=True))
        if not approvers:
            add_users(User.objects.filter(security_profile__role__in=mgmt_roles, is_active=True))

    elif stage == 'pending_deputy_director':
        # Subordination logic:
        # DD ICT supervises Systems Manager / ICT
        # DD Communications supervises Chief Tech / Comms
        user_role = getattr(getattr(user, 'security_profile', None), 'role', '')
        if 'Tech' in user_role or 'Comms' in str(dept) or 'Communication' in str(dept):
            dd_roles = ['Deputy Director Communications', 'Deputy Director ICT', 'Deputy Director IT']
        else:
            dd_roles = ['Deputy Director ICT', 'Deputy Director IT', 'Deputy Director Communications']

        for r in dd_roles:
            add_users(User.objects.filter(security_profile__role=r, is_active=True))

    elif stage == 'pending_chief_director':
        add_users(User.objects.filter(security_profile__role='Chief Director', is_active=True))

    if not approvers:
        add_users(User.objects.filter(is_superuser=True, is_active=True))

    return approvers


def get_leave_approvers(user):
    """
    Return all hierarchy approvers across the escalation chain for this user:
    Management Tier -> Deputy Director Tier -> Chief Director
    """
    approvers = []
    def add_unique(user_list):
        for u in user_list:
            if u not in approvers and u.id != user.id:
                approvers.append(u)

    for st in ['pending_management', 'pending_deputy_director', 'pending_chief_director']:
        stage_approvers = get_leave_approvers_for_stage(user, st)
        add_unique(stage_approvers)

    if not approvers:
        add_unique(User.objects.filter(is_superuser=True, is_active=True))

    return approvers


def user_can_approve_leave_stage(user, leave):
    """
    Strict hierarchy stage validator.
    Only allows users of the current tier (or superusers) to act on a leave request.
    """
    if user.is_superuser:
        return True
    if leave.status != 'Pending':
        return False

    user_role = getattr(getattr(user, 'security_profile', None), 'role', '')
    stage = getattr(leave, 'approval_stage', 'pending_management') or 'pending_management'

    if stage == 'pending_management':
        return user_role in ['Systems Manager', 'System Manager', 'Supt ICT', 'Chief Tech']
    elif stage == 'pending_deputy_director':
        return user_role in ['Deputy Director ICT', 'Deputy Director IT', 'Deputy Director Communications']
    elif stage == 'pending_chief_director':
        return user_role in ['Chief Director']
    return False



def get_leave_approver(user):
    approvers = get_leave_approvers(user)
    return approvers[0] if approvers else None


def notify_leave_approver(leave_obj, action, approver):
    if not approver or not approver.email:
        return
    base_url = getattr(settings, 'RIFTSX_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
    # Create single-use secure token for this approver
    import secrets, datetime
    token = secrets.token_urlsafe(32)
    expires_at = timezone.now() + datetime.timedelta(hours=24)
    from registry.models import LeaveApprovalToken
    try:
        LeaveApprovalToken.objects.create(leave_request=leave_obj, approver=approver, token=token, expires_at=expires_at)
        verify_url = request.build_absolute_uri(reverse('verify-leave-approval', args=[token]))
    except Exception:
        # Fallback to regular sign URL
        verify_url = f"{base_url}/leave/{leave_obj.id}/sign-visual/"

    subject = f"Leave Request {action}: {leave_obj.user.username}"
    message = (
        f"Hello {approver.get_full_name() or approver.username},\n\n"
        f"A leave request has been {action.lower()} by {leave_obj.user.get_full_name() or leave_obj.user.username}.\n"
        f"Leave type: {leave_obj.leave_type}\n"
        f"Period: {leave_obj.start_date} to {leave_obj.end_date}\n"
        f"Reason: {leave_obj.reason}\n"
        f"Current status: {leave_obj.status}\n\n"
        f"Please review and action the request here: {verify_url}\n\n"
        f"This link is for your use only and expires in 24 hours.\n\n"
        f"Thank you."
    )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [approver.email], fail_silently=True)
    except Exception:
        pass


def notify_leave_approvers(leave_obj, action, approvers):
    for approver in approvers:
        notify_leave_approver(leave_obj, action, approver)


def notify_leave_requester(leave_obj, action, approvers=None):
    if not leave_obj.user.email:
        return
    subject = f"Your Leave Request Has Been {action}"
    if isinstance(approvers, (list, tuple)):
        approver_names = ", ".join([a.get_full_name() or a.username for a in approvers if a])
        approver_line = f"Assigned approvers: {approver_names}."
    elif approvers:
        approver_line = f"This request is assigned to {approvers.get_full_name() or approvers.username}."
    else:
        approver_line = ''

    status_line = f"The request is currently {leave_obj.status}."
    if action.lower() in ['approved', 'rejected'] and approvers:
        if isinstance(approvers, (list, tuple)):
            status_line = f"The request has been {action.lower()} by {approver_names}."
        else:
            status_line = f"The request has been {action.lower()} by {approvers.get_full_name() or approvers.username}."

    message = (
        f"Hello {leave_obj.user.get_full_name() or leave_obj.user.username},\n\n"
        f"Your leave request has been {action.lower()}.\n"
        f"Leave type: {leave_obj.leave_type}\n"
        f"Period: {leave_obj.start_date} to {leave_obj.end_date}\n"
        f"Reason: {leave_obj.reason}\n"
        f"{status_line}\n"
        f"{approver_line}\n"
        f"Comment from approver: {leave_obj.supervisor_comment or 'None'}\n\n"
        f"Thank you."
    )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [leave_obj.user.email], fail_silently=True)
    except Exception:
        pass

@login_required
def manage_leave(request):
    context = context_data(request)
    id = request.GET.get('id')
    if id:
        leave = get_object_or_404(models.LeaveRequest, id=id, user=request.user)
        form = forms.LeaveRequestForm(instance=leave)
        context['page_title'] = "Edit Leave Request"
    else:
        form = forms.LeaveRequestForm()
        context['page_title'] = "Apply for Leave"
    
    try:
        form.fields['approvers'].queryset = User.objects.filter(security_profile__isnull=False, is_active=True).order_by('security_profile__department__name', 'username')
    except Exception:
        form.fields['approvers'].queryset = User.objects.filter(is_active=True)

    employee = models.Borrower.objects.filter(user=request.user).first()
    context['employee'] = employee
    context['form'] = form
    context['id'] = id

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('is_modal') == '1'
    if is_ajax:
        return render(request, 'manage_leave_modal.html', context)
    return render(request, 'manage_leave.html', context)

@login_required
def save_leave(request):
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        id = request.POST.get('id')
        if id and id != 'None':
            leave = get_object_or_404(models.LeaveRequest, id=id, user=request.user)
            form = forms.LeaveRequestForm(request.POST, request.FILES, instance=leave)
        else:
            form = forms.LeaveRequestForm(request.POST, request.FILES)
        # Ensure approvers field has a valid queryset for validation (picker appends IDs client-side)
        try:
            form.fields['approvers'].queryset = User.objects.filter(security_profile__isnull=False, is_active=True).order_by('security_profile__department__name', 'username')
        except Exception:
            form.fields['approvers'].queryset = User.objects.filter(is_active=True)
        
        if form.is_valid():
            leave_obj = form.save(commit=False)
            leave_obj.user = request.user
            if not id or id == 'None':
                leave_obj.status = 'Pending'
                leave_obj.approved_by = None
                leave_obj.supervisor_comment = ''
                
                # Determine initial hierarchy approval stage based on requester's role
                req_tier = get_hierarchy_tier_for_user(request.user)
                if req_tier == 'officer':
                    leave_obj.approval_stage = 'pending_management'
                    leave_obj.workflow_stage = 'Leave Request'
                elif req_tier == 'management':
                    leave_obj.approval_stage = 'pending_deputy_director'
                    leave_obj.workflow_stage = 'Supervisor Recommendation'
                elif req_tier == 'deputy_director':
                    leave_obj.approval_stage = 'pending_chief_director'
                    leave_obj.workflow_stage = 'Approval'
                else: # Chief Director
                    leave_obj.approval_stage = 'complete'
                    leave_obj.status = 'Approved'
                    leave_obj.workflow_stage = 'Leave Register'
                    leave_obj.approved_by = request.user
            else:
                # Any edit after an approval or rejection reopens the request.
                if leave_obj.status != 'Pending':
                    leave_obj.status = 'Pending'
                    leave_obj.approved_by = None
                    leave_obj.supervisor_comment = ''
                    leave_obj.approval_stage = 'pending_management'
            leave_obj.save()
            # save m2m approvers
            try:
                form.save_m2m()
            except Exception:
                pass

            # If no approvers selected or to ensure hierarchy chain is populated
            approvers_qs = leave_obj.approvers.all()
            if not approvers_qs.exists():
                hierarchy_approvers = get_leave_approvers(request.user)
                if hierarchy_approvers:
                    leave_obj.approvers.set(hierarchy_approvers)
                    approvers_qs = leave_obj.approvers.all()

            if not approvers_qs.exists():
                resp['msg'] = 'No approvers could be identified for this leave request.'
                return HttpResponse(json.dumps(resp), content_type="application/json")

            active_approvers = get_leave_approvers_for_stage(request.user, leave_obj.approval_stage)
            notify_leave_approvers(leave_obj, 'Submitted', active_approvers or list(approvers_qs))
            notify_leave_requester(leave_obj, 'Submitted', active_approvers or list(approvers_qs))

            resp['status'] = 'success'
            messages.success(request, f"Leave request submitted. Currently routed to: {leave_obj.get_approval_stage_display()}.")
        else:
            resp['msg'] = form.errors.as_text()
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def leave_applications(request):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Access Denied.")
        return redirect('home-page')
    
    context = context_data(request)
    context['page_title'] = "Leave Applications Management"
    leaves = models.LeaveRequest.objects.all().order_by('-date_applied')
    for leave in leaves:
        leave.is_assigned_approver = leave.approvers.filter(id=request.user.id).exists()
        leave.can_current_user_approve = user_can_approve_leave_stage(request.user, leave)
        leave.total_approvers = leave.approvers.count()
        leave.approved_count = leave.approvals.filter(status='Approved').count()
        leave.rejected_count = leave.approvals.filter(status='Rejected').count()
    context['leaves'] = leaves
    return render(request, 'leave_applications.html', context)

@login_required
def approve_leave(request):
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        id = request.POST.get('id')
        status = request.POST.get('status')
        comment = request.POST.get('comment', '').strip()
        
        leave = get_object_or_404(models.LeaveRequest, id=id)
        if not user_can_approve_leave_stage(request.user, leave):
            current_stage_label = leave.get_approval_stage_display()
            resp['msg'] = f"Permission denied. This leave request is currently awaiting action at the '{current_stage_label}' stage."
            return HttpResponse(json.dumps(resp), content_type="application/json")

        approval, created = models.LeaveRequestApproval.objects.update_or_create(
            leave_request=leave,
            approver=request.user,
            defaults={
                'status': status,
                'comment': comment,
                'timestamp': timezone.now(),
                'signed_at': timezone.now()
            }
        )

        current_stage = leave.approval_stage or 'pending_management'

        if status == 'Rejected':
            leave.status = 'Rejected'
            leave.supervisor_comment = comment or 'Rejected by reviewing authority.'
            leave.save()
            notify_leave_requester(leave, 'Rejected', request.user)
            resp['status'] = 'success'
            messages.warning(request, f"Leave request for {leave.user.username} rejected.")
            return HttpResponse(json.dumps(resp), content_type="application/json")

        # Handle Approved - sequential escalation through ZRP hierarchy
        if current_stage == 'pending_management':
            leave.approval_stage = 'pending_deputy_director'
            leave.workflow_stage = 'Supervisor Recommendation'
            leave.supervisor_recommendation = 'Recommended'
            leave.supervisor_notes = comment
            leave.supervisor_comment = comment
            leave.status = 'Pending'
            leave.save()
            next_approvers = get_leave_approvers_for_stage(leave.user, 'pending_deputy_director')
            notify_leave_approvers(leave, 'Pending Review', next_approvers)
            notify_leave_requester(leave, 'Recommended by Management (Escalated to Deputy Director)', next_approvers)
            resp['status'] = 'success'
            messages.success(request, f"Leave request approved at Management Tier and escalated to Deputy Director.")

        elif current_stage == 'pending_deputy_director':
            leave.approval_stage = 'pending_chief_director'
            leave.workflow_stage = 'Approval'
            leave.supervisor_comment = comment
            leave.status = 'Pending'
            leave.save()
            next_approvers = get_leave_approvers_for_stage(leave.user, 'pending_chief_director')
            notify_leave_approvers(leave, 'Pending Review', next_approvers)
            notify_leave_requester(leave, 'Approved by Deputy Director (Escalated to Chief Director)', next_approvers)
            resp['status'] = 'success'
            messages.success(request, f"Leave request approved by Deputy Director and escalated to Chief Director.")

        elif current_stage == 'pending_chief_director' or request.user.is_superuser:
            leave.approval_stage = 'complete'
            leave.status = 'Approved'
            leave.workflow_stage = 'Leave Register'
            leave.approved_by = request.user
            leave.supervisor_comment = comment
            leave.save()
            all_approvers = list(leave.approvers.all())
            notify_leave_requester(leave, 'Approved', all_approvers)
            notify_leave_approvers(leave, 'Approved', all_approvers)
            resp['status'] = 'success'
            messages.success(request, f"Leave request for {leave.user.username} has been FULLY APPROVED by Chief Director.")

        return HttpResponse(json.dumps(resp), content_type="application/json")


@login_required
def leave_sign_visual(request, pk):
    leave = get_object_or_404(models.LeaveRequest, pk=pk)
    if not (request.user.is_superuser or leave.approvers.filter(id=request.user.id).exists() or user_can_approve_leave_stage(request.user, leave)):
        messages.error(request, "Permission denied. Only authorized approvers can review this leave request.")
        return redirect('leave-applications')

    already_actioned = leave.status in ('Rejected', 'Approved')

    if request.method == 'POST':
        if already_actioned:
            messages.error(request, f'This leave request has already been {leave.status.lower()}. No further action can be taken.')
            return redirect('leave-sign-visual', pk=pk)

        if not user_can_approve_leave_stage(request.user, leave):
            messages.warning(request, f"This leave request is currently awaiting action at the '{leave.get_approval_stage_display()}' stage.")
            return redirect('leave-applications')

        action = request.POST.get('action', 'approve')
        comment = request.POST.get('comments', request.POST.get('comment', '')).strip()
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR')
        signed_at = timezone.now()

        # Handle Rejection
        if action == 'reject':
            models.LeaveRequestApproval.objects.update_or_create(
                leave_request=leave,
                approver=request.user,
                defaults={
                    'status': 'Rejected',
                    'comment': comment or 'Leave request rejected by approver.',
                    'ip_address': ip,
                    'signed_at': signed_at,
                    'timestamp': signed_at
                }
            )
            leave.status = 'Rejected'
            leave.supervisor_comment = comment or 'Rejected by approver.'
            leave.save(update_fields=['status', 'supervisor_comment'])
            
            try:
                notify_leave_requester(leave, 'Rejected', list(leave.approvers.all()))
            except Exception as e:
                print(f"Leave notification error: {e}")

            messages.warning(request, f'Leave request for {leave.user.username} has been REJECTED.')
            return redirect('leave-applications')

        # Handle Approval & Signature
        signature_data = request.POST.get('signature_data')
        save_to_profile = request.POST.get('save_to_profile') == 'on'
        page_num = request.POST.get('page_num', '0')
        x_pct = request.POST.get('x_pct', '0')
        y_pct = request.POST.get('y_pct', '0')
        date_page = request.POST.get('date_page_num')
        date_x = request.POST.get('date_x_pct')
        date_y = request.POST.get('date_y_pct')

        if not signature_data or signature_data == 'data:,':
            messages.error(request, 'Please prepare or generate a valid signature first.')
            return redirect('leave-sign-visual', pk=pk)

        if save_to_profile and signature_data:
            from registry.models import UserSignature
            profile, created = UserSignature.objects.get_or_create(user=request.user)
            profile.signature_data = signature_data
            profile.save()

        approval, created = models.LeaveRequestApproval.objects.update_or_create(
            leave_request=leave,
            approver=request.user,
            defaults={
                'status': 'Approved',
                'comment': comment,
                'signature_data': signature_data,
                'ip_address': ip,
                'signed_at': signed_at,
                'timestamp': signed_at
            }
        )

        # Stamp the document if possible
        if leave.supporting_document:
            leave.document = leave.supporting_document
            leave.signed_document = getattr(leave, 'signed_document', None)
            try:
                from registry.services.document_signer import stamp_signature_at_coordinates
                stamp_signature_at_coordinates(
                    leave,
                    request.user,
                    signature_data,
                    int(page_num) if page_num else 0,
                    float(x_pct) if x_pct else 0.0,
                    float(y_pct) if y_pct else 0.0,
                    ip,
                    signed_at,
                    date_page=int(date_page) if date_page else None,
                    date_x=float(date_x) if date_x else None,
                    date_y=float(date_y) if date_y else None
                )
            except Exception as e:
                print(f"Leave document stamping failed: {e}")

        # Staged escalation through ZRP hierarchy
        current_stage = leave.approval_stage or 'pending_management'
        if current_stage == 'pending_management':
            leave.approval_stage = 'pending_deputy_director'
            leave.workflow_stage = 'Supervisor Recommendation'
            leave.supervisor_recommendation = 'Recommended'
            leave.supervisor_notes = comment
            leave.supervisor_comment = comment
            leave.status = 'Pending'
            leave.save()
            next_approvers = get_leave_approvers_for_stage(leave.user, 'pending_deputy_director')
            notify_leave_approvers(leave, 'Pending Review', next_approvers)
            notify_leave_requester(leave, 'Recommended by Management (Escalated to Deputy Director)', next_approvers)
            messages.success(request, f'Leave request for {leave.user.username} approved at Management Tier and escalated to Deputy Director.')

        elif current_stage == 'pending_deputy_director':
            leave.approval_stage = 'pending_chief_director'
            leave.workflow_stage = 'Approval'
            leave.supervisor_comment = comment
            leave.status = 'Pending'
            leave.save()
            next_approvers = get_leave_approvers_for_stage(leave.user, 'pending_chief_director')
            notify_leave_approvers(leave, 'Pending Review', next_approvers)
            notify_leave_requester(leave, 'Approved by Deputy Director (Escalated to Chief Director)', next_approvers)
            messages.success(request, f'Leave request for {leave.user.username} approved by Deputy Director and escalated to Chief Director.')

        elif current_stage == 'pending_chief_director' or request.user.is_superuser:
            leave.approval_stage = 'complete'
            leave.status = 'Approved'
            leave.workflow_stage = 'Leave Register'
            leave.approved_by = request.user
            leave.supervisor_comment = comment
            leave.save()
            all_approvers = list(leave.approvers.all())
            notify_leave_requester(leave, 'Approved', all_approvers)
            notify_leave_approvers(leave, 'Approved', all_approvers)
            messages.success(request, f'Leave request for {leave.user.username} has been FULLY APPROVED by Chief Director.')

        return redirect('leave-applications')

    # Render document pages for visual signing
    leave.document = leave.supporting_document
    leave.signed_document = getattr(leave, 'signed_document', None)
    pages = []
    try:
        from registry.services.document_signer import render_document_to_images
        pages = render_document_to_images(leave)
    except Exception:
        pages = []

    from registry.models import UserSignature
    user_sig = UserSignature.objects.filter(user=request.user).first()

    context = context_data(request)
    context.update({
        'page_title': 'Sign Leave Request',
        'leave': leave,
        'pages': pages,
        'saved_signature': user_sig.signature_data if user_sig else None,
        'today_date': timezone.now().strftime('%Y-%m-%d'),
        'already_actioned': already_actioned,
    })
    return render(request, 'leave_sign_visual.html', context)


@login_required
def leave_view(request, pk):
    leave = get_object_or_404(models.LeaveRequest, pk=pk)
    # Allow requester, approvers, staff or superuser to view
    if not (request.user == leave.user or request.user.is_superuser or request.user.is_staff or leave.approvers.filter(id=request.user.id).exists()):
        messages.error(request, "Permission denied.")
        return redirect('leave-applications')

    # If download requested, stream the file
    if request.GET.get('download'):
        if leave.supporting_document:
            from django.http import FileResponse
            try:
                return FileResponse(leave.supporting_document.open('rb'), as_attachment=True, filename=leave.supporting_document.name)
            except Exception:
                messages.error(request, 'Unable to stream file for download.')
                return redirect('leave-view', pk=pk)

    # Render document pages for viewing (no signing controls)
    leave.document = leave.supporting_document
    leave.signed_document = getattr(leave, 'signed_document', None)
    pages = []
    try:
        from registry.services.document_signer import render_document_to_images
        pages = render_document_to_images(leave)
    except Exception:
        pages = []

    context = context_data(request)
    context.update({
        'page_title': 'View Leave Document',
        'leave': leave,
        'pages': pages,
    })
    return render(request, 'leave_view.html', context)


def verify_leave_approval(request, token):
    from registry.models import LeaveApprovalToken
    link = get_object_or_404(LeaveApprovalToken, token=token)
    if not link.is_valid():
        messages.error(request, 'Approval link expired or already used.')
        return redirect('leave-applications')

    # require login and ensure user matches intended approver
    if not request.user.is_authenticated:
        messages.info(request, 'Please login to proceed to approve this request.')
        # Redirect to login and return to this verify URL after login
        from django.urls import reverse
        login_url = settings.LOGIN_URL if hasattr(settings, 'LOGIN_URL') else reverse('login')
        next_url = request.build_absolute_uri(reverse('verify-leave-approval', args=[token]))
        return redirect(f"{login_url}?next={next_url}")

    if request.user.id != link.approver_id and not request.user.is_superuser:
        messages.error(request, 'This approval link is not for your account.')
        return redirect('leave-applications')

    # mark token used and redirect to visual signer
    try:
        link.mark_used()
    except Exception:
        pass

    return redirect('leave-sign-visual', pk=link.leave_request_id)


@login_required
def approver_directory(request):
    # Lists users grouped by department and role so requesters can choose approvers
    users = User.objects.filter(is_active=True).select_related('security_profile').order_by('security_profile__department__name', 'security_profile__role', 'username')
    # Build a simple grouping
    grouped = {}
    for u in users:
        dept = getattr(getattr(u, 'security_profile', None), 'department', None)
        dept_name = dept.name if dept else 'Unassigned'
        role = getattr(getattr(u, 'security_profile', None), 'role', 'Unknown')
        grouped.setdefault(dept_name, {}).setdefault(role, []).append(u)

    context = context_data(request)
    context.update({'page_title': 'Approver Directory', 'grouped_users': grouped})
    # If requested as JSON, return flat list for picker modal
    if request.GET.get('json'):
        out = []
        for dept, roles in grouped.items():
            for role, users in roles.items():
                for u in users:
                    out.append({'id': u.id, 'name': u.get_full_name() or u.username, 'email': u.email, 'department': dept, 'role': role})
        return JsonResponse(out, safe=False)

    return render(request, 'approver_directory.html', context)


@login_required
def manage_signature(request):
    from base64 import b64encode
    profile, _ = models.UserSignature.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        sig_data = request.POST.get('signature_data')
        sig_file = request.FILES.get('signature_file')
        if sig_data and sig_data != 'data:,' :
            profile.signature_data = sig_data
            profile.save()
            messages.success(request, 'Signature saved to your profile.')
            return redirect('manage-signature')
        elif sig_file:
            try:
                content = sig_file.read()
                mime = sig_file.content_type or 'image/png'
                b64 = b64encode(content).decode('utf-8')
                profile.signature_data = f"data:{mime};base64,{b64}"
                profile.save()
                messages.success(request, 'Signature uploaded to your profile.')
                return redirect('manage-signature')
            except Exception:
                messages.error(request, 'Failed to process uploaded signature.')
        else:
            messages.error(request, 'No signature data provided.')

    context = context_data(request)
    context.update({'page_title': 'Manage Signature', 'profile': profile})
    return render(request, 'approver_signature.html', context)


# --- Requisition Management Views ---
@login_required
def requisition_list(request):
    context = context_data(request)
    context['page_title'] = "My Requisitions"
    context['requisitions'] = models.Requisition.objects.filter(requestor=request.user).order_by('-date_requested')
    return render(request, 'requisition_list.html', context)

@login_required
def manage_requisition(request):
    context = context_data(request)
    id = request.GET.get('id')
    if id:
        req = get_object_or_404(models.Requisition, id=id, requestor=request.user)
        form = forms.RequisitionForm(instance=req)
        context['page_title'] = "Edit Requisition"
    else:
        form = forms.RequisitionForm()
        context['page_title'] = "Submit New Requisition"
    
    context['form'] = form
    context['id'] = id
    return render(request, 'manage_requisition.html', context)

@login_required
def save_requisition(request):
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        id = request.POST.get('id')
        if id and id != 'None':
            req = get_object_or_404(models.Requisition, id=id, requestor=request.user)
            form = forms.RequisitionForm(request.POST, request.FILES, instance=req)
        else:
            form = forms.RequisitionForm(request.POST, request.FILES)
        
        if form.is_valid():
            req_obj = form.save(commit=False)
            req_obj.requestor = request.user
            # Recalculate total if not set or just as safety
            req_obj.total_amount = req_obj.quantity * req_obj.estimated_unit_cost
            req_obj.save()
            resp['status'] = 'success'
            messages.success(request, "Requisition submitted successfully.")
        else:
            resp['msg'] = form.errors.as_text()
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def all_requisitions(request):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Access Denied.")
        return redirect('home-page')
    
    context = context_data(request)
    context['page_title'] = "All Requisitions"
    context['requisitions'] = models.Requisition.objects.all().order_by('-date_requested')
    return render(request, 'requisitions_admin.html', context)

@login_required
def approve_requisition(request):
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        id = request.POST.get('id')
        status = request.POST.get('status')
        comment = request.POST.get('comment')
        
        req = get_object_or_404(models.Requisition, id=id)
        
        # Budget Validation logic
        if status == 'Approved' and req.budget_line:
            if req.total_amount > req.budget_line.remaining_amount:
                resp['msg'] = f"Over-expenditure Alert: Insufficient budget in {req.budget_line.department.name} ({req.budget_line.fiscal_year}). Available: {req.budget_line.remaining_amount}"
                return HttpResponse(json.dumps(resp), content_type="application/json")
        
        req.status = status
        req.approver_comment = comment
        req.approved_by = request.user
        req.save()
        
        # If approved, we could auto-deduct, but usually it's better to deduct when fulfilled or paid.
        # However, the user asked for Over-expenditure alerts.
        
        resp['status'] = 'success'
        messages.success(request, f"Requisition {status}.")
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def meeting_list(request):
    context = context_data(request)
    context['page'] = 'meetings'
    context['page_title'] = "Meeting & Resolution Tracking"
    context['meetings'] = models.Meeting.objects.all().order_by('-meeting_date')
    context['pending_resolution_count'] = models.Resolution.objects.filter(status='Pending').count()
    return render(request, 'meeting_list.html', context)

@login_required
def manage_meeting(request, id=None):
    context = context_data(request)
    context['page'] = 'manage_meeting'
    context['page_title'] = "Manage Meeting"
    if id:
        meeting = get_object_or_404(models.Meeting, id=id)
        context['meeting'] = meeting
        form = forms.MeetingForm(instance=meeting)
    else:
        form = forms.MeetingForm()
    context['form'] = form
    return render(request, 'manage_meeting.html', context)

@login_required
def save_meeting(request):
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        id = request.POST.get('id')
        if id and id != 'None':
            meeting = get_object_or_404(models.Meeting, id=id)
            form = forms.MeetingForm(request.POST, request.FILES, instance=meeting)
        else:
            form = forms.MeetingForm(request.POST, request.FILES)
        
        if form.is_valid():
            is_new = not id or id == 'None'
            meeting_obj = form.save(commit=False)
            if is_new:
                meeting_obj.organized_by = request.user
            meeting_obj.save()
            resp['status'] = 'success'
            messages.success(request, "Meeting saved successfully.")
            # Notify organizer and department staff about new meeting
            if is_new:
                meeting_date_str = meeting_obj.meeting_date.strftime('%d %B %Y at %H:%M') if hasattr(meeting_obj.meeting_date, 'strftime') else str(meeting_obj.meeting_date)
                notif_msg = f"Meeting '{meeting_obj.title}' has been scheduled for {meeting_date_str}. Venue: {meeting_obj.venue_or_link or 'TBA'}."
                send_system_notification(
                    recipient=request.user,
                    category='Meeting',
                    title=f"Meeting Scheduled: {meeting_obj.title}",
                    message=notif_msg,
                    sender=request.user,
                    link_url=f"/registry/meetings/minute-taking/{meeting_obj.pk}/",
                    channel='In-System'
                )
        else:
            resp['msg'] = form.errors.as_text()
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def view_meeting(request, id):
    context = context_data(request)
    meeting = get_object_or_404(models.Meeting, id=id)
    context['meeting'] = meeting
    context['resolutions'] = meeting.resolutions.all().order_by('-date_created')
    context['page_title'] = f"Meeting: {meeting.title}"
    return render(request, 'view_meeting.html', context)

@login_required
def manage_resolution(request, meeting_id, id=None):
    context = context_data(request)
    meeting = get_object_or_404(models.Meeting, id=meeting_id)
    context['meeting'] = meeting
    if id:
        resolution = get_object_or_404(models.Resolution, id=id, meeting=meeting)
        context['resolution'] = resolution
        form = forms.ResolutionForm(instance=resolution)
    else:
        form = forms.ResolutionForm()
    context['form'] = form
    context['files'] = models.File.objects.filter(delete_flag=0, status=1)
    context['users'] = User.objects.all()
    return render(request, 'manage_resolution.html', context)

@login_required
def save_resolution(request):
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        id = request.POST.get('id')
        meeting_id = request.POST.get('meeting')
        meeting = get_object_or_404(models.Meeting, id=meeting_id)
        
        if id and id != 'None':
            resolution = get_object_or_404(models.Resolution, id=id, meeting=meeting)
            form = forms.ResolutionForm(request.POST, instance=resolution)
        else:
            form = forms.ResolutionForm(request.POST)
        
        if form.is_valid():
            res_obj = form.save(commit=False)
            res_obj.meeting = meeting
            res_obj.save()
            form.save_m2m() # Important for ManyToMany mapping
            resp['status'] = 'success'
            messages.success(request, "Resolution saved successfully.")
        else:
            resp['msg'] = form.errors.as_text()
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def update_resolution_status(request):
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        id = request.POST.get('id')
        status = request.POST.get('status')
        resolution = get_object_or_404(models.Resolution, id=id)
        resolution.status = status
        resolution.save()
        resp['status'] = 'success'
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def record_minutes(request, meeting_id):
    """Serve the audio recorder / transcript editor page."""
    context = context_data(request)
    meeting = get_object_or_404(models.Meeting, id=meeting_id)
    context['meeting'] = meeting
    context['page_title'] = f"Record Minutes – {meeting.title}"
    return render(request, 'record_minutes.html', context)

def generate_minutes_pdf_buffer(meeting, transcript):
    """Helper: Generate a PDF buffer from a transcript."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
    from reportlab.lib.units import cm
    import io

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2.5*cm, rightMargin=2.5*cm,
        topMargin=2.5*cm, bottomMargin=2.5*cm,
        title=f"Minutes – {meeting.title}",
    )

    styles = getSampleStyleSheet()
    primary_color = colors.HexColor('#0d6efd')
    dark = colors.HexColor('#1a1a2e')

    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Title'],
        textColor=dark, fontSize=20, spaceAfter=6, leading=24,
    )
    sub_style = ParagraphStyle(
        'Sub', parent=styles['Normal'],
        textColor=colors.HexColor('#6c757d'), fontSize=10, spaceAfter=4,
    )
    heading_style = ParagraphStyle(
        'Heading', parent=styles['Heading2'],
        textColor=primary_color, fontSize=12, spaceBefore=14, spaceAfter=6,
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontSize=10, leading=16, spaceAfter=6,
        textColor=dark,
    )

    story = []

    # Header
    story.append(Paragraph(meeting.title, title_style))
    story.append(Paragraph(f"{meeting.get_meeting_type_display()} &nbsp;|&nbsp; "
                           f"{meeting.meeting_date.strftime('%d %B %Y, %H:%M')} "
                           + (f"&nbsp;|&nbsp; {meeting.location}" if meeting.location else ''), sub_style))
    story.append(Paragraph(f"Organised by: {meeting.organized_by.get_full_name() or meeting.organized_by.username}", sub_style))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=2, color=primary_color))
    story.append(Spacer(1, 12))

    # Minutes body
    story.append(Paragraph("Meeting Minutes", heading_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#dee2e6')))
    story.append(Spacer(1, 8))

    if transcript:
        for para in transcript.split('\n'):
            para = para.strip()
            if para:
                story.append(Paragraph(para, body_style))
    else:
        story.append(Paragraph("<i>(No minutes text recorded.)</i>", body_style))

    # Footer info – Resolutions
    resolutions = meeting.resolutions.all()
    if resolutions.exists():
        story.append(Spacer(1, 16))
        story.append(HRFlowable(width="100%", thickness=2, color=primary_color))
        story.append(Spacer(1, 8))
        story.append(Paragraph("Resolutions Passed", heading_style))
        data = [['Ref #', 'Resolution', 'Status', 'Deadline']]
        for res in resolutions:
            data.append([
                res.resolution_number,
                Paragraph(res.description[:120] + ('…' if len(res.description) > 120 else ''), body_style),
                res.status,
                str(res.deadline) if res.deadline else '—',
            ])
        tbl = Table(data, colWidths=[2.5*cm, 9*cm, 2.5*cm, 2.5*cm])
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), primary_color),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('FONTSIZE', (0,1), (-1,-1), 9),
            ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#dee2e6')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(tbl)

    # Generated timestamp
    story.append(Spacer(1, 20))
    from django.utils import timezone as tz
    story.append(Paragraph(
        f"<i>Generated: {tz.localtime().strftime('%d %B %Y at %H:%M')} | RIFTS-X Strategic Intelligence Platform System</i>",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8,
                       textColor=colors.HexColor('#adb5bd'), alignment=1)
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer

@login_required
def save_minutes_text(request, meeting_id):
    """AJAX: save the transcript text back to the Meeting record."""
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        meeting = get_object_or_404(models.Meeting, id=meeting_id)
        transcript = request.POST.get('transcript', '')
        meeting.minutes_text = transcript
        
        # Also auto-generate/update the PDF file
        buffer = generate_minutes_pdf_buffer(meeting, transcript)
        safe_name = meeting.title.replace(' ', '_')[:40]
        filename = f"Minutes_{safe_name}_{meeting.meeting_date.strftime('%Y%m%d')}.pdf"
        meeting.minutes.save(filename, ContentFile(buffer.getvalue()), save=False)
        
        meeting.save()
        resp['status'] = 'success'
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def download_minutes_pdf(request, meeting_id):
    """Generate and return a PDF of the meeting minutes from the submitted transcript."""
    meeting = get_object_or_404(models.Meeting, id=id if 'id' in locals() else meeting_id)
    transcript = request.POST.get('transcript', meeting.minutes_text or '')

    # Save text and update the stored PDF as well
    meeting.minutes_text = transcript
    buffer = generate_minutes_pdf_buffer(meeting, transcript)
    safe_name = meeting.title.replace(' ', '_')[:40]
    filename = f"Minutes_{safe_name}_{meeting.meeting_date.strftime('%Y%m%d')}.pdf"
    meeting.minutes.save(filename, ContentFile(buffer.getvalue()), save=False)
    meeting.save()

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

# --- Procurement & Contract Lifecycle Views ---

@login_required
def tender_list(request):
    from django.utils import timezone
    context = {
        'page_title': 'Tenders / Procurement Opportunities',
        'tenders': models.Tender.objects.all().order_by('-date_created'),
        'now': timezone.now()
    }
    return render(request, 'tender_list.html', context)

@login_required
def manage_tender(request, pk=None):
    if pk:
        tender = get_object_or_404(models.Tender, pk=pk)
        form = forms.TenderForm(instance=tender)
    else:
        tender = None
        form = forms.TenderForm()
    
    context = {
        'form': form,
        'tender': tender,
        'departments': models.Department.objects.all()
    }
    return render(request, 'manage_tender.html', context)

@login_required
def save_tender(request):
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        id = request.POST.get('id')
        if id:
            tender = get_object_or_404(models.Tender, id=id)
            form = forms.TenderForm(request.POST, instance=tender)
        else:
            form = forms.TenderForm(request.POST)
            
        if form.is_valid():
            tender_obj = form.save(commit=False)
            if not id:
                tender_obj.created_by = request.user
            tender_obj.save()

            # ── e-GP Integration: publish via EgpPortalService ──────────────
            if tender_obj.status == 'Published' and tender_obj.bids.count() == 0:
                try:
                    from registry.services.egp_service import EgpPortalService
                    pub_result = EgpPortalService.publish_tender(tender_obj)
                    bid_result = EgpPortalService.fetch_bids(tender_obj)
                    logger.info(f"[e-GP] {pub_result['message']} | {bid_result['message']}")
                except Exception as _egp_exc:
                    logger.exception(f"[e-GP] Error during tender publish/bid fetch: {_egp_exc}")


            resp['status'] = 'success'
            messages.success(request, "Tender saved successfully.")
        else:
            resp['msg'] = form.errors.as_text()
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def view_tender(request, pk):
    tender = get_object_or_404(models.Tender, pk=pk)
    context = {
        'page_title': f"Tender: {tender.ref_num}",
        'tender': tender,
        'bids': tender.bids.all().order_by('-amount')
    }
    return render(request, 'view_tender.html', context)


@login_required
def egp_tender_sync(request, pk):
    """AJAX endpoint — sync a single tender's bids from e-GP portal."""
    if request.method != 'POST':
        return JsonResponse({'status': 'failed', 'msg': 'POST required.'})
    tender = get_object_or_404(models.Tender, pk=pk)
    try:
        from registry.services.egp_service import EgpPortalService
        pub_result = EgpPortalService.publish_tender(tender)
        bid_result = EgpPortalService.fetch_bids(tender)
        return JsonResponse({
            'status': 'success',
            'publish': pub_result,
            'bids': bid_result,
            'msg': f"{pub_result['message']} | {bid_result['message']}",
        })
    except Exception as exc:
        logger.exception(f"[e-GP] egp_tender_sync error: {exc}")
        return JsonResponse({'status': 'failed', 'msg': str(exc)})


@login_required
def egp_test_connection(request):
    """AJAX endpoint — test live e-GP portal connection and return latency."""
    try:
        from registry.services.egp_service import EgpPortalService
        result = EgpPortalService.test_connection()
        return JsonResponse({'status': 'success', 'result': result})
    except Exception as exc:
        logger.exception(f"[e-GP] egp_test_connection error: {exc}")
        return JsonResponse({'status': 'failed', 'msg': str(exc)})


@login_required
def bid_list(request, tender_id):
    tender = get_object_or_404(models.Tender, pk=tender_id)
    context = {
        'page_title': f"Bids for {tender.ref_num}",
        'tender': tender,
        'bids': tender.bids.all()
    }
    return render(request, 'bid_list.html', context)

@login_required
def manage_bid(request, tender_pk=None, pk=None, tender_id=None):
    t_id = tender_pk or tender_id
    tender = get_object_or_404(models.Tender, pk=t_id)
    if pk:
        bid = get_object_or_404(models.Bid, pk=pk, tender=tender)
        form = forms.BidForm(instance=bid)
    else:
        bid = None
        form = forms.BidForm()
    
    context = {
        'form': form,
        'bid': bid,
        'tender': tender
    }
    return render(request, 'manage_bid.html', context)

@login_required
def save_bid(request):
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        id = request.POST.get('id')
        tender_id = request.POST.get('tender')
        tender = get_object_or_404(models.Tender, id=tender_id)
        
        if id:
            bid = get_object_or_404(models.Bid, id=id)
            form = forms.BidForm(request.POST, request.FILES, instance=bid)
        else:
            form = forms.BidForm(request.POST, request.FILES)
            
        if form.is_valid():
            bid_obj = form.save(commit=False)
            bid_obj.tender = tender
            if request.POST.get('evaluation_score'):
                try:
                    bid_obj.evaluation_score = float(request.POST.get('evaluation_score'))
                except (ValueError, TypeError):
                    pass
            if 'evaluation_notes' in request.POST:
                bid_obj.evaluation_notes = request.POST.get('evaluation_notes')
            bid_obj.save()
            resp['status'] = 'success'
            messages.success(request, "Bid registered successfully.")
        else:
            resp['msg'] = form.errors.as_text()
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def award_bid(request, pk):
    bid = get_object_or_404(models.Bid, pk=pk)
    tender = bid.tender
    
    # Update statuses
    bid.status = 'Successful'
    bid.save()
    
    tender.status = 'Awarded'
    tender.save()
    
    # Mark others as unsuccessful
    tender.bids.exclude(pk=pk).update(status='Unsuccessful')
    
    # Also update requisition status if linked
    if tender.requisition:
        tender.requisition.status = 'Fulfilled'
        tender.requisition.save()
    
    # Auto-initiate Contract
    contract = models.Contract.objects.create(
        tender=tender,
        awarded_bid=bid,
        title=f"Contract for {tender.title}",
        contract_ref=f"ZRP-CON-{tender.ref_num}",
        amount=bid.amount,
        start_date=timezone.now().date(),
        end_date=timezone.now().date() + timedelta(days=365) # Default 1 year
    )
    
    messages.success(request, f"Bid awarded! Requisition fulfilled and Contract {contract.contract_ref} initiated.")
    return redirect('view-contract-pk', pk=contract.pk)

@login_required
@login_required
def contract_list(request):
    from django.utils import timezone
    context = {
        'page_title': 'Contract Management',
        'contracts': models.Contract.objects.all().order_by('-date_created'),
        'now': timezone.now()
    }
    return render(request, 'contract_list.html', context)

@login_required
def view_contract(request, pk):
    contract = get_object_or_404(models.Contract, pk=pk)
    context = {
        'page_title': f"Contract: {contract.contract_ref}",
        'contract': contract,
        'milestones': contract.milestones.all().order_by('due_date'),
        'evaluations': contract.evaluations.all().order_by('-evaluation_date'),
        'files': models.File.objects.filter(delete_flag=0)
    }
    return render(request, 'view_contract.html', context)

@login_required
def save_milestone(request):
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        contract_id = request.POST.get('contract')
        contract = get_object_or_404(models.Contract, id=contract_id)
        form = forms.ContractMilestoneForm(request.POST)
        if form.is_valid():
            ms = form.save(commit=False)
            ms.contract = contract
            ms.save()
            resp['status'] = 'success'
        else:
            resp['msg'] = form.errors.as_text()
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def save_performance(request):
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        contract_id = request.POST.get('contract')
        contract = get_object_or_404(models.Contract, id=contract_id)
        form = forms.PerformanceEvaluationForm(request.POST)
        if form.is_valid():
            pe = form.save(commit=False)
            pe.contract = contract
            pe.evaluated_by = request.user
            pe.save()
            resp['status'] = 'success'
        else:
            resp['msg'] = form.errors.as_text()
    return HttpResponse(json.dumps(resp), content_type="application/json")

def get_procurement_user_scope(request):
    """
    Evaluates role and provincial scope for procurement and stores records:
    1. Chief Director / Superuser: Highest executive level, sees ALL system-wide records & statistics.
    2. Supt ICT: Responsible to see ALL.
    3. General Police: Responsible for day-to-day operations (GR, Asset Register, Form 27, Form 216, Issues Register).
    4. Chief Tech & Deputy Director Communications: Sees ONLY Communications & Radio.
    5. System Manager & Deputy Director IT: Sees ONLY Systems.
    6. Provincial ICT Officer (PICTO): Sees EVERYTHING issued/recorded for their assigned province.
    """
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {'role': 'Anonymous', 'scope': 'none', 'province': '', 'can_sign_electronic': False, 'is_chief_director': False, 'is_supt_ict': False, 'is_provincial': False}

    security_profile = getattr(user, 'security_profile', None)
    if not security_profile:
        security_profile, _ = models.UserSecurity.objects.get_or_create(user=user)

    if user.is_superuser:
        role = security_profile.role if (security_profile and security_profile.role) else 'Chief Director'
        province = security_profile.province or ''
        is_picto = (role == 'Provincial ICT Officer')
        
        # If superuser is designated as a specific role (like PICTO), respect that role's scope; otherwise default to 'all'
        if role == 'Provincial ICT Officer' and province:
            scope = 'province'
        elif role in ['Chief Tech', 'Deputy Director Communications']:
            scope = 'comms'
        elif role in ['System Manager', 'Systems Manager', 'Deputy Director IT', 'Deputy Director ICT']:
            scope = 'systems'
        else:
            scope = 'all'

        return {
            'role': role,
            'scope': scope,
            'province': province,
            'can_sign_electronic': True,
            'is_chief_director': (role == 'Chief Director' or not role),
            'is_supt_ict': (role == 'Supt ICT'),
            'is_provincial': is_picto,
        }

    role = security_profile.role or 'General Police'
    province = security_profile.province or ''

    can_sign = role in [
        'Supt ICT', 'Chief Tech', 'System Manager', 'Systems Manager', 'Provincial ICT Officer',
        'Deputy Director Communications', 'Deputy Director IT', 'Deputy Director ICT', 'Chief Director'
    ]

    if role in ['Chief Director', 'Supt ICT', 'General Police', 'Purchasing Officer', 'Department Manager']:
        scope = 'all'
    elif role in ['Chief Tech', 'Deputy Director Communications']:
        scope = 'comms'
    elif role in ['System Manager', 'Systems Manager', 'Deputy Director IT', 'Deputy Director ICT']:
        scope = 'systems'
    elif role == 'Provincial ICT Officer':
        scope = 'province'
    else:
        scope = 'all'

    return {
        'role': role,
        'scope': scope,
        'province': province,
        'can_sign_electronic': can_sign,
        'is_chief_director': (role == 'Chief Director'),
        'is_supt_ict': (role == 'Supt ICT'),
        'is_provincial': (role == 'Provincial ICT Officer'),
    }

# Centralized Keyword & Category Filters for Comms vs Systems
Q_COMMS_ASSET = (
    Q(category='Equipment') |
    Q(name__icontains='radio') |
    Q(name__icontains='vhf') |
    Q(name__icontains='uhf') |
    Q(name__icontains='repeater') |
    Q(name__icontains='antenna') |
    Q(name__icontains='handset') |
    Q(name__icontains='communication') |
    Q(name__icontains='transceiver') |
    Q(name__icontains='signals') |
    Q(name__icontains='battery') |
    Q(name__icontains='solar') |
    Q(name__icontains='walkie') |
    Q(name__icontains='telecom') |
    Q(description__icontains='radio') |
    Q(description__icontains='communication')
)

Q_SYSTEMS_ASSET = (
    Q(category='ICT') |
    Q(name__icontains='laptop') |
    Q(name__icontains='desktop') |
    Q(name__icontains='computer') |
    Q(name__icontains='server') |
    Q(name__icontains='monitor') |
    Q(name__icontains='printer') |
    Q(name__icontains='system') |
    Q(name__icontains='software') |
    Q(name__icontains='network') |
    Q(name__icontains='switch') |
    Q(name__icontains='router') |
    Q(name__icontains='ups') |
    Q(name__icontains='all in one') |
    Q(name__icontains='scanner') |
    Q(description__icontains='system') |
    Q(description__icontains='computer')
)

# --- Asset Management Views ---

@login_required
def asset_list(request):
    scope_info = get_procurement_user_scope(request)
    scope = scope_info['scope']
    province = scope_info['province']

    assets = models.Asset.objects.all().order_by('-date_created')

    if scope == 'comms':
        assets = assets.filter(Q_COMMS_ASSET)
    elif scope == 'systems':
        assets = assets.filter(Q_SYSTEMS_ASSET)
    elif scope == 'province' and province:
        assets = assets.filter(
            Q(serial_numbers__location__icontains=province) |
            Q(issues_register_entries__requesting_station__icontains=province) |
            Q(form27_issuances__voucher__station__icontains=province)
        ).distinct()

    # Executive Overview Metrics (for Chief Director, Supt ICT, executives)
    all_gr = models.GoodsReceivedEntry.objects.all()
    total_received_qty = sum(g.qty for g in all_gr)
    all_cards = models.ZrpForm216Card.objects.all()
    total_stock_on_hand = sum(max(0, c.current_balance) for c in all_cards)
    all_issues = models.IssuesRegisterEntry.objects.all()
    total_issued_qty = sum(i.qty for i in all_issues)
    all_vouchers = models.ZrpForm27Voucher.objects.all()

    systems_assets_count = models.Asset.objects.filter(Q_SYSTEMS_ASSET).count()
    comms_assets_count = models.Asset.objects.filter(Q_COMMS_ASSET).count()

    # Only General Police Officers can add / edit / delete assets
    try:
        _sec = request.user.security_profile
        _role = _sec.role
    except Exception:
        _role = ''
    can_edit_assets = (request.user.is_superuser or _role == 'General Police')

    context = {
        'page_title': 'Asset & Inventory Records Intelligence',
        'assets': assets,
        'maintenance_count': assets.filter(status='Maintenance').count(),
        'categories': models.Asset.CATEGORY_CHOICES,
        'scope_info': scope_info,
        'total_received_qty': total_received_qty,
        'total_stock_on_hand': total_stock_on_hand,
        'total_issued_qty': total_issued_qty,
        'total_vouchers_count': all_vouchers.count(),
        'systems_assets_count': systems_assets_count,
        'comms_assets_count': comms_assets_count,
        'can_edit_assets': can_edit_assets,
    }
    return render(request, 'asset_list.html', context)


@login_required
def manage_asset(request, pk=None):
    # Only General Police Officers (or superusers) can add / edit assets
    if not request.user.is_superuser:
        try:
            _role = request.user.security_profile.role
        except Exception:
            _role = ''
        if _role != 'General Police':
            from django.contrib import messages
            messages.error(request, "Access Denied: Only General Police Officers can add or edit asset records.")
            return redirect('asset-list')

    if pk:
        asset = get_object_or_404(models.Asset, pk=pk)
        form = forms.AssetForm(instance=asset)
    else:
        asset = None
        form = forms.AssetForm()
    
    # Pass goods received entries with metadata for auto-fill
    gr_entries = models.GoodsReceivedEntry.objects.all().order_by('-date', '-id')[:100]
    gr_data = []
    for gr in gr_entries:
        gr_data.append({
            'id': gr.id,
            'entry_no': gr.entry_no or f"GR-{gr.id}",
            'company': gr.company,
            'goods_received': gr.goods_received,
            'qty': gr.qty,
            'registered_qty': gr.registered_assets_qty,
            'remaining_qty': gr.remaining_unregistered_qty,
            'is_fully_registered': gr.is_fully_registered,
            'po_no': gr.po_no,
            'date': gr.date.strftime('%Y-%m-%d') if gr.date else '',
            'bin_no': gr.bin_no,
            'department_id': gr.department_id,
        })

    context = {
        'form': form,
        'asset': asset,
        'gr_json': json.dumps(gr_data),
    }
    return render(request, 'manage_asset.html', context)

@login_required
def save_asset(request):
    resp = {'status': 'failed', 'msg': ''}
    # Only General Police Officers (or superusers) can save assets
    if not request.user.is_superuser:
        try:
            _role = request.user.security_profile.role
        except Exception:
            _role = ''
        if _role != 'General Police':
            return JsonResponse({'status': 'failed', 'msg': 'Access Denied: Only General Police Officers can add or update asset records.'})
    if request.method == 'POST':
        id = request.POST.get('id')

        if id:
            asset = get_object_or_404(models.Asset, id=id)
            form = forms.AssetForm(request.POST, request.FILES, instance=asset)
        else:
            form = forms.AssetForm(request.POST, request.FILES)
            
        if form.is_valid():
            asset_obj = form.save(commit=False)
            
            # Extract serial numbers from POST (dynamic serials and bulk paste)
            additional_serials = request.POST.getlist('additional_serials[]')
            bulk_serials_text = request.POST.get('bulk_serials', '')
            
            all_serials = []
            for sn in additional_serials:
                sn_clean = sn.strip()
                if sn_clean and sn_clean not in all_serials:
                    all_serials.append(sn_clean)
            if bulk_serials_text:
                for line in bulk_serials_text.replace(',', '\n').splitlines():
                    sn_clean = line.strip()
                    if sn_clean and sn_clean not in all_serials:
                        all_serials.append(sn_clean)

            # Auto-generate or maintain asset_code (no longer manual primary serial field)
            if not asset_obj.asset_code:
                if all_serials:
                    # Use the first serial number as the asset's code/base reference
                    first_sn = all_serials[0]
                    # Ensure uniqueness
                    if not models.Asset.objects.filter(asset_code=first_sn).exists():
                        asset_obj.asset_code = first_sn
                    else:
                        from django.utils import timezone
                        asset_obj.asset_code = f"{first_sn}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
                else:
                    from django.utils import timezone
                    cat_code = (asset_obj.category or 'AST')[:3].upper()
                    count = models.Asset.objects.count() + 1
                    asset_obj.asset_code = f"AST-{cat_code}-{count:04d}"

            # Validation: Serial numbers count must match actual quantity received!
            delivered_qty = asset_obj.quantity_delivered or 0
            entered_serials_count = len(all_serials)
            is_new = not id

            if delivered_qty > 0:
                if entered_serials_count > 0 and entered_serials_count != delivered_qty:
                    resp['msg'] = f"The number of serial numbers entered ({entered_serials_count}) does not match the actual quantity received ({delivered_qty}). Exactly {delivered_qty} serial numbers must be entered."
                    return HttpResponse(json.dumps(resp), content_type="application/json")
                if entered_serials_count == 0 and is_new:
                    resp['msg'] = f"Please enter all {delivered_qty} serial numbers matching the actual quantity received ({delivered_qty})."
                    return HttpResponse(json.dumps(resp), content_type="application/json")
            elif entered_serials_count > 0:
                delivered_qty = entered_serials_count
                asset_obj.quantity_delivered = delivered_qty
            else:
                delivered_qty = 1
                asset_obj.quantity_delivered = 1

            # Tally Reconciliation Validation: If linked to Goods Received Ledger entry, check quantity cap
            if asset_obj.goods_received_entry:
                gr = asset_obj.goods_received_entry
                # Existing registered qty excluding this asset if editing
                other_registered = sum(
                    a.quantity_delivered or a.serial_numbers.count() or 0
                    for a in gr.assets.exclude(pk=asset_obj.pk if asset_obj.pk else None)
                )
                total_new_registered = other_registered + delivered_qty
                if total_new_registered > gr.qty:
                    remaining = max(0, gr.qty - other_registered)
                    resp['msg'] = (
                        f"Registration exceeds Goods Received Register consignment total for {gr.entry_no or 'this entry'}! "
                        f"Consignment total is {gr.qty} units; already registered in assets: {other_registered} units; "
                        f"Remaining unregistered capacity: {remaining} units. You entered {delivered_qty} units."
                    )
                    return HttpResponse(json.dumps(resp), content_type="application/json")

            # Auto-calculate acquisition_cost based on unit_cost * delivered quantity
            from decimal import Decimal
            u_cost = asset_obj.unit_cost or Decimal('0.00')
            qty = len(all_serials) if len(all_serials) > 0 else delivered_qty
            if u_cost > 0:
                asset_obj.acquisition_cost = u_cost * Decimal(str(qty))
            elif asset_obj.acquisition_cost and qty > 0 and (not asset_obj.unit_cost or asset_obj.unit_cost == 0):
                asset_obj.unit_cost = round(asset_obj.acquisition_cost / Decimal(str(qty)), 2)

            asset_obj.save()

            # Save / sync all entered serial numbers into AssetSerialNumber
            for sn_val in all_serials:
                models.AssetSerialNumber.objects.get_or_create(
                    asset=asset_obj,
                    serial_number=sn_val,
                    defaults={'status': 'Active', 'barcode': sn_val}
                )

            # Form 216 Stock Card Integration: Ensure card exists and initial intake receipt is recorded
            card, created_card = models.ZrpForm216Card.objects.get_or_create(
                code_no=asset_obj.asset_code,
                defaults={
                    'article': asset_obj.name,
                    'unit': 'Each',
                    'folio_no': f"FOL-{asset_obj.acquisition_date.year if asset_obj.acquisition_date else timezone.now().year}/{asset_obj.pk}",
                    'department': asset_obj.department,
                    'current_balance': 0,
                    'created_by': request.user,
                    'linked_asset': asset_obj,
                }
            )
            if not card.linked_asset:
                card.linked_asset = asset_obj
                card.save(update_fields=['linked_asset'])
            
            # Ensure the initial intake receipt exists on this card
            receipt_exists = card.entries.filter(receipts__gt=0).exists()
            if not receipt_exists and delivered_qty > 0:
                voucher_ref = ""
                if asset_obj.goods_received_entry:
                    voucher_ref = asset_obj.goods_received_entry.entry_no
                elif asset_obj.delivery_note_number:
                    voucher_ref = asset_obj.delivery_note_number
                else:
                    voucher_ref = f"REC-{asset_obj.asset_code}"
                
                models.ZrpForm216Entry.objects.create(
                    card=card,
                    date=asset_obj.acquisition_date or timezone.now().date(),
                    voucher_no=voucher_ref,
                    from_to=f"From {asset_obj.supplier_name or (asset_obj.goods_received_entry.company if asset_obj.goods_received_entry else 'Supplier')}",
                    receipts=delivered_qty,
                    issues=0,
                    remarks=f"Initial stock intake: {asset_obj.name}",
                    created_by=request.user
                )
                card.recalculate_balances()
            
            # Auto-archive delivery note, invoice and PMU documents into AssetDocument, ScannedDocument, AND Institutional Cloud
            if 'delivery_note_doc' in request.FILES and asset_obj.delivery_note_doc:
                models.AssetDocument.objects.create(
                    asset=asset_obj,
                    doc_type='Delivery Note',
                    title=f"Delivery Note #{asset_obj.delivery_note_number or asset_obj.asset_code}",
                    document_file=asset_obj.delivery_note_doc,
                    uploaded_by=request.user,
                    notes=f"Delivered by {asset_obj.supplier_name or 'Supplier'}"
                )
                models.ScannedDocument.objects.create(
                    raw_file=asset_obj.delivery_note_doc,
                    classification="Supplier Delivery Note",
                    status="Completed",
                    linked_asset=asset_obj,
                    metadata={'asset_code': asset_obj.asset_code, 'supplier': asset_obj.supplier_name, 'dn_num': asset_obj.delivery_note_number}
                )
                # Institutional Cloud Archiving
                models.archive_to_cloud(
                    file_field=asset_obj.delivery_note_doc,
                    file_name=f"Asset_DN_{asset_obj.asset_code}",
                    folder_name="Asset Documentation",
                    department=asset_obj.department,
                    user=request.user,
                    description=f"Delivery note for asset {asset_obj.name} ({asset_obj.asset_code})"
                )

            if 'invoice_doc' in request.FILES and asset_obj.invoice_doc:
                models.AssetDocument.objects.create(
                    asset=asset_obj,
                    doc_type='Invoice',
                    title=f"Invoice #{asset_obj.invoice_number or asset_obj.asset_code}",
                    document_file=asset_obj.invoice_doc,
                    uploaded_by=request.user,
                    notes=f"Invoice from {asset_obj.supplier_name or 'Supplier'}"
                )
                models.ScannedDocument.objects.create(
                    raw_file=asset_obj.invoice_doc,
                    classification="Supplier Invoice",
                    status="Completed",
                    linked_asset=asset_obj,
                    metadata={'asset_code': asset_obj.asset_code, 'supplier': asset_obj.supplier_name, 'invoice_num': asset_obj.invoice_number}
                )
                models.archive_to_cloud(
                    file_field=asset_obj.invoice_doc,
                    file_name=f"Asset_Invoice_{asset_obj.asset_code}",
                    folder_name="Asset Documentation",
                    department=asset_obj.department,
                    user=request.user,
                    description=f"Supplier invoice for {asset_obj.name} ({asset_obj.asset_code})"
                )

            if 'pmu_source_doc' in request.FILES and asset_obj.pmu_source_doc:
                models.AssetDocument.objects.create(
                    asset=asset_obj,
                    doc_type='PMU Source Document',
                    title=f"PMU Source Document ({asset_obj.pmu_source_doc_ref or 'Procurement'})",
                    document_file=asset_obj.pmu_source_doc,
                    uploaded_by=request.user,
                    notes=f"PMU supporting paperwork {asset_obj.pmu_source_doc_ref or ''}"
                )
                models.ScannedDocument.objects.create(
                    raw_file=asset_obj.pmu_source_doc,
                    classification="PMU Procurement Source Document",
                    status="Completed",
                    linked_asset=asset_obj,
                    metadata={'asset_code': asset_obj.asset_code, 'pmu_ref': asset_obj.pmu_source_doc_ref}
                )
                models.archive_to_cloud(
                    file_field=asset_obj.pmu_source_doc,
                    file_name=f"Asset_PMU_{asset_obj.asset_code}",
                    folder_name="Asset Documentation",
                    department=asset_obj.department,
                    user=request.user,
                    description=f"PMU procurement doc for {asset_obj.name} ({asset_obj.asset_code})"
                )

            resp['status'] = 'success'
            resp['asset_id'] = asset_obj.pk
            messages.success(request, f"Asset registered with {qty} item(s)/serial number(s). Total Cost: ${asset_obj.acquisition_cost}.")
        else:
            resp['msg'] = form.errors.as_text()
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def view_asset(request, pk):
    asset = get_object_or_404(models.Asset, pk=pk)
    context = {
        'page_title': f"Asset: {asset.asset_code}",
        'asset': asset,
        'serial_numbers': asset.serial_numbers.all(),
        'maintenance_logs': asset.maintenance_logs.all().order_by('-scheduled_date'),
        'custody_history': asset.custody_history.all().order_by('-issue_date'),
        'documents': asset.documents.all().order_by('-date_uploaded'),
        'scanned_docs': asset.scanned_documents.all().order_by('-created_at'),
        'inspection_form': forms.AssetInspectionForm(instance=asset),
        'upload_doc_form': forms.AssetDocumentUploadForm(),
        'users': User.objects.all()
    }
    return render(request, 'view_asset.html', context)

@login_required
def save_asset_serial(request, pk):
    """Adds a new serial number to an existing asset and updates the total cost accordingly"""
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        from decimal import Decimal
        asset = get_object_or_404(models.Asset, pk=pk)
        serial_number = request.POST.get('serial_number', '').strip()
        location = request.POST.get('location', '').strip()
        status = request.POST.get('status', 'Active')
        
        if not serial_number:
            resp['msg'] = "Serial number cannot be empty."
            return HttpResponse(json.dumps(resp), content_type="application/json")

        if models.AssetSerialNumber.objects.filter(asset=asset, serial_number=serial_number).exists():
            resp['msg'] = f"Serial number '{serial_number}' already registered for this asset."
            return HttpResponse(json.dumps(resp), content_type="application/json")

        models.AssetSerialNumber.objects.create(
            asset=asset,
            serial_number=serial_number,
            barcode=serial_number,
            location=location,
            status=status
        )

        # Recalculate cost = unit_cost * new count
        cnt = asset.serial_numbers.count()
        if asset.unit_cost and asset.unit_cost > 0:
            asset.acquisition_cost = asset.unit_cost * Decimal(str(cnt))
            asset.save(update_fields=['acquisition_cost'])

        resp['status'] = 'success'
        resp['new_count'] = cnt
        resp['new_total_cost'] = float(asset.acquisition_cost)
        messages.success(request, f"Serial number '{serial_number}' added successfully. Total items: {cnt}.")
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def delete_asset_serial(request, pk, serial_id):
    """Removes a serial number from an asset and adjusts the total cost"""
    resp = {'status': 'failed', 'msg': ''}
    # Only General Police Officers (or superusers) can delete asset records
    if not request.user.is_superuser:
        try:
            _role = request.user.security_profile.role
        except Exception:
            _role = ''
        if _role != 'General Police':
            return JsonResponse({'status': 'failed', 'msg': 'Access Denied: Only General Police Officers can delete asset serial records.'})
    from decimal import Decimal
    asset = get_object_or_404(models.Asset, pk=pk)
    sn_obj = get_object_or_404(models.AssetSerialNumber, pk=serial_id, asset=asset)
    sn_obj.delete()


    cnt = asset.serial_numbers.count()
    if asset.unit_cost and asset.unit_cost > 0 and cnt > 0:
        asset.acquisition_cost = asset.unit_cost * Decimal(str(cnt))
        asset.save(update_fields=['acquisition_cost'])

    resp['status'] = 'success'
    messages.success(request, "Serial number removed.")
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def technician_inspect_asset(request, pk):
    """
    Handles technician quality tests, verification metrics, and uploads
    the 3 mandatory approval clearance documents:
    1. Technical Inspection Certificate
    2. Quality Assurance & Compliance Report
    3. Asset Acceptance & Clearance Certificate
    """
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        asset = get_object_or_404(models.Asset, pk=pk)
        form = forms.AssetInspectionForm(request.POST, request.FILES, instance=asset)
        if form.is_valid():
            asset_obj = form.save(commit=False)
            # Typed Testing Officer / Inspector name
            if form.cleaned_data.get('technician_name'):
                asset_obj.technician_name = form.cleaned_data['technician_name'].strip()
            elif not asset_obj.technician_name:
                asset_obj.technician_name = request.user.get_full_name() or request.user.username

            # Also associate technician FK if empty or matches user
            if not asset_obj.technician:
                asset_obj.technician = request.user

            if not asset_obj.inspection_date:
                asset_obj.inspection_date = timezone.now().date()

            # REQUIREMENT: Only ONE Mandatory Clearance Document is required (not 3)
            has_doc1 = bool(asset_obj.approval_doc_1)
            has_doc2 = bool(asset_obj.approval_doc_2)
            has_doc3 = bool(asset_obj.approval_doc_3)
            has_clearance_doc = has_doc1 or has_doc2 or has_doc3
            
            # If at least 1 clearance document is present and quality test is checked
            if has_clearance_doc and asset_obj.quality_test_passed:
                asset_obj.is_cleared = True
                asset_obj.inspection_status = 'Quality Approved'
            elif asset_obj.inspection_status == 'Quality Approved' and not has_clearance_doc:
                asset_obj.is_cleared = False
                asset_obj.inspection_status = 'Testing in Progress'

            asset_obj.save()

            # Auto-archive the 3 approval documents into the Asset digital archive
            if 'approval_doc_1' in request.FILES and asset_obj.approval_doc_1:
                models.AssetDocument.objects.create(
                    asset=asset_obj,
                    doc_type='Technical Test Cert',
                    title="1. Technical Testing & Inspection Certificate",
                    document_file=asset_obj.approval_doc_1,
                    uploaded_by=request.user,
                    notes=f"Tested by {request.user.get_full_name() or request.user.username}"
                )
                models.ScannedDocument.objects.create(
                    raw_file=asset_obj.approval_doc_1,
                    classification="Technical Testing Certificate",
                    status="Completed",
                    linked_asset=asset_obj,
                    metadata={'asset_code': asset_obj.asset_code, 'tech': request.user.username}
                )

            if 'approval_doc_2' in request.FILES and asset_obj.approval_doc_2:
                models.AssetDocument.objects.create(
                    asset=asset_obj,
                    doc_type='QA Report',
                    title="2. Quality Assurance & Compliance Report",
                    document_file=asset_obj.approval_doc_2,
                    uploaded_by=request.user,
                    notes=f"QA verified by {request.user.get_full_name() or request.user.username}"
                )
                models.ScannedDocument.objects.create(
                    raw_file=asset_obj.approval_doc_2,
                    classification="Quality Assurance Report",
                    status="Completed",
                    linked_asset=asset_obj,
                    metadata={'asset_code': asset_obj.asset_code, 'tech': request.user.username}
                )

            if 'approval_doc_3' in request.FILES and asset_obj.approval_doc_3:
                models.AssetDocument.objects.create(
                    asset=asset_obj,
                    doc_type='Clearance Certificate',
                    title="3. Asset Acceptance & Clearance Certificate",
                    document_file=asset_obj.approval_doc_3,
                    uploaded_by=request.user,
                    notes=f"Cleared by {request.user.get_full_name() or request.user.username}"
                )
                models.ScannedDocument.objects.create(
                    raw_file=asset_obj.approval_doc_3,
                    classification="Asset Acceptance Certificate",
                    status="Completed",
                    linked_asset=asset_obj,
                    metadata={'asset_code': asset_obj.asset_code, 'tech': request.user.username}
                )

            resp['status'] = 'success'
            resp['is_cleared'] = asset_obj.is_cleared
            messages.success(request, "Technician quality inspection and clearance documents saved successfully.")
        else:
            resp['msg'] = form.errors.as_text()
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def upload_asset_document(request, pk):
    """
    Directly ingests a document or scanner batch into the asset digital archive
    """
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        asset = get_object_or_404(models.Asset, pk=pk)
        form = forms.AssetDocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.asset = asset
            doc.uploaded_by = request.user
            doc.save()

            # Mirror to ScannedDocument archive
            models.ScannedDocument.objects.create(
                raw_file=doc.document_file,
                classification=f"Asset Archive: {doc.get_doc_type_display()}",
                status="Completed",
                linked_asset=asset,
                metadata={'asset_code': asset.asset_code, 'doc_title': doc.title}
            )

            resp['status'] = 'success'
            messages.success(request, f"Document '{doc.title}' added to digital archive.")
        else:
            resp['msg'] = form.errors.as_text()
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def print_asset_dossier(request, pk):
    """
    Institutional printable ledger & clearance dossier for the asset,
    including supplier intake documents, PMU references, technician quality test results,
    and the 3 clearance certificates. Formatted for paper print and PDF export.
    """
    asset = get_object_or_404(models.Asset, pk=pk)
    context = {
        'asset': asset,
        'serial_numbers': asset.serial_numbers.all(),
        'documents': asset.documents.all().order_by('date_uploaded'),
        'custody_history': asset.custody_history.all().order_by('-issue_date'),
        'maintenance_logs': asset.maintenance_logs.all().order_by('-scheduled_date'),
        'print_date': timezone.now()
    }
    return render(request, 'print_asset_dossier.html', context)

# ══════════════════════════════════════════════════════════════════════════════
# STATUTORY FORM 60260-6: BOARD OF SURVEY (BOS) VIEWS
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def board_of_survey_list(request):
    """Displays all Board of Survey proceedings and condemned equipment files"""
    surveys = models.BoardOfSurvey.objects.all().order_by('-proceedings_date')
    context = {
        'page_title': 'Board of Survey Reports (Form 60260-6)',
        'surveys': surveys,
        'draft_count': surveys.filter(status='Draft').count(),
        'approved_count': surveys.filter(status='Approved').count(),
        'disposed_count': surveys.filter(status='Disposed').count(),
    }
    return render(request, 'board_of_survey_list.html', context)

@login_required
def manage_board_of_survey(request, pk=None):
    """Creates or updates a Board of Survey report header and board members"""
    if pk:
        survey = get_object_or_404(models.BoardOfSurvey, pk=pk)
        form = forms.BoardOfSurveyForm(instance=survey)
    else:
        survey = None
        form = forms.BoardOfSurveyForm(initial={
            'report_ref': f"BOS-{timezone.now().year}-{models.BoardOfSurvey.objects.count() + 1:03d}",
            'held_at': 'ZRP ICT Central Stores',
            'proceedings_date': timezone.now().date(),
        })
    
    context = {
        'form': form,
        'survey': survey,
    }
    return render(request, 'manage_board_of_survey.html', context)

@login_required
def save_board_of_survey(request):
    """Saves Board of Survey report"""
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        pk = request.POST.get('id')
        if pk:
            survey = get_object_or_404(models.BoardOfSurvey, pk=pk)
            form = forms.BoardOfSurveyForm(request.POST, instance=survey)
        else:
            form = forms.BoardOfSurveyForm(request.POST)
            
        if form.is_valid():
            survey_obj = form.save(commit=False)
            if not pk:
                survey_obj.created_by = request.user
            survey_obj.save()
            resp['status'] = 'success'
            resp['id'] = survey_obj.id
            messages.success(request, f"Board of Survey Form 60260-6 ({survey_obj.report_ref}) saved successfully.")
        else:
            resp['msg'] = form.errors.as_text()
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def view_board_of_survey(request, pk):
    """View Board of Survey report with items, disposal recommendations, and approval workflow"""
    survey = get_object_or_404(models.BoardOfSurvey, pk=pk)
    context = {
        'page_title': f"Board of Survey: {survey.report_ref}",
        'survey': survey,
        'items': survey.items.all(),
        'assets': models.Asset.objects.all().order_by('name'),
        'item_form': forms.BoardOfSurveyItemForm(),
        'departments': models.Department.objects.all(),
    }
    return render(request, 'view_board_of_survey.html', context)

@login_required
def save_board_of_survey_item(request, pk):
    """Adds an examined unserviceable article to the Board of Survey report"""
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        survey = get_object_or_404(models.BoardOfSurvey, pk=pk)
        form = forms.BoardOfSurveyItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.board_of_survey = survey
            item.save()

            # Mark linked asset/serial status as Condemned if applicable
            if item.asset:
                item.asset.status = 'Disposed' if survey.is_disposed else 'Maintenance'
                item.asset.save(update_fields=['status'])
            if item.serial_number:
                item.serial_number.status = 'Condemned'
                item.serial_number.save(update_fields=['status'])

            resp['status'] = 'success'
            messages.success(request, f"Examined article '{item.description}' added to Board of Survey.")
        else:
            resp['msg'] = form.errors.as_text()
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def delete_board_of_survey_item(request, pk, item_id):
    """Deletes an item from the Board of Survey"""
    survey = get_object_or_404(models.BoardOfSurvey, pk=pk)
    item = get_object_or_404(models.BoardOfSurveyItem, pk=item_id, board_of_survey=survey)
    item.delete()
    messages.success(request, "Item removed from report.")
    return redirect('view-board-of-survey', pk=survey.pk)

@login_required
def approve_board_of_survey(request, pk):
    """Head of Department approval of Board of Survey proceedings"""
    survey = get_object_or_404(models.BoardOfSurvey, pk=pk)
    survey.is_approved = True
    survey.status = 'Approved'
    survey.approved_by = request.user
    survey.approval_date = timezone.now().date()
    survey.approval_notes = request.POST.get('approval_notes', 'Approved by Head of Department.')
    survey.save()
    messages.success(request, f"Board of Survey {survey.report_ref} officially APPROVED by Head of Department.")
    return redirect('view-board-of-survey', pk=survey.pk)

@login_required
def certify_disposal_board_of_survey(request, pk):
    """Officer-in-charge certification that articles have been disposed of as authorized"""
    survey = get_object_or_404(models.BoardOfSurvey, pk=pk)
    survey.is_disposed = True
    survey.status = 'Disposed'
    survey.officer_in_charge = request.user
    survey.disposal_certification_date = timezone.now().date()
    survey.disposal_notes = request.POST.get('disposal_notes', '')
    survey.sale_cash_receipt_no = request.POST.get('sale_cash_receipt_no', '')
    if 'destruction_certificate_file' in request.FILES:
        survey.destruction_certificate_file = request.FILES['destruction_certificate_file']
    survey.save()

    # Update asset statuses to Disposed
    for item in survey.items.all():
        if item.asset:
            item.asset.status = 'Disposed'
            item.asset.save(update_fields=['status'])
        if item.serial_number:
            item.serial_number.status = 'Disposed'
            item.serial_number.save(update_fields=['status'])

    messages.success(request, f"Disposal certified for Board of Survey {survey.report_ref} by Officer-in-Charge.")
    return redirect('view-board-of-survey', pk=survey.pk)

@login_required
def print_board_of_survey(request, pk):
    """Renders the official statutory Form 60260-6 (G.P&S.34586-S.) for print & triplicate archive"""
    survey = get_object_or_404(models.BoardOfSurvey, pk=pk)
    context = {
        'survey': survey,
        'items': survey.items.all(),
        'print_date': timezone.now(),
    }
    return render(request, 'print_board_of_survey.html', context)


# --- Statutory Z.R.P. FORM 27 Views (Requisition/Issue Voucher) ---

@login_required
def form27_list(request):
    """Lists all ZRP Form 27 Requisition/Issue Vouchers with scope filtering"""
    scope_info = get_procurement_user_scope(request)
    scope = scope_info['scope']
    province = scope_info['province']

    vouchers = models.ZrpForm27Voucher.objects.all().prefetch_related('items')

    comms_f27_q = (
        Q(items__asset__category='Equipment') |
        Q(items__description__icontains='radio') |
        Q(items__description__icontains='vhf') |
        Q(items__description__icontains='repeater') |
        Q(items__description__icontains='antenna') |
        Q(items__description__icontains='handset') |
        Q(issued_by__icontains='RADIO')
    )
    systems_f27_q = (
        Q(items__asset__category='ICT') |
        Q(items__description__icontains='laptop') |
        Q(items__description__icontains='desktop') |
        Q(items__description__icontains='computer') |
        Q(items__description__icontains='system') |
        Q(items__description__icontains='server') |
        Q(items__description__icontains='printer')
    )

    if scope == 'comms':
        vouchers = vouchers.filter(comms_f27_q).distinct()
    elif scope == 'systems':
        vouchers = vouchers.filter(systems_f27_q).distinct()
    elif scope == 'province' and province:
        vouchers = vouchers.filter(
            Q(station__icontains=province) |
            Q(items__serial_number__location__icontains=province)
        ).distinct()

    context = {
        'page_title': 'Z.R.P. Form 27 - Requisition/Issue Vouchers',
        'vouchers': vouchers,
        'total_count': vouchers.count(),
        'issued_count': vouchers.filter(status='Issued').count(),
        'dispatched_count': vouchers.filter(status='Dispatched').count(),
        'received_count': vouchers.filter(status='Received').count(),
        'electronic_signed_count': vouchers.filter(electronic_signature_confirmed=True).count(),
        'scope_info': scope_info,
    }
    return render(request, 'form27_list.html', context)

@login_required
def manage_form27(request, pk=None):
    """Creates or updates a Form 27 Voucher header"""
    if pk:
        voucher = get_object_or_404(models.ZrpForm27Voucher, pk=pk)
        form = forms.ZrpForm27VoucherForm(instance=voucher)
    else:
        voucher = None
        yr_short = str(timezone.now().year)[-2:]
        count = models.ZrpForm27Voucher.objects.count() + 1
        default_voucher_no = f"{count:02d}/{yr_short}"
        form = forms.ZrpForm27VoucherForm(initial={
            'voucher_no': default_voucher_no,
            'date': timezone.now().date(),
            'station_date': timezone.now().date(),
            'checker_date': timezone.now().date(),
            'issued_by': 'O.I.C CENTRAL RADIO STORES   (I.C.T)',
            'checker': 'CST KADIKI',
            'status': 'Issued',
        })
    context = {
        'voucher': voucher,
        'form': form,
    }
    return render(request, 'manage_form27.html', context)

@login_required
def save_form27(request):
    """Saves a Form 27 Voucher via AJAX"""
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        pk = request.POST.get('id')
        if pk:
            voucher = get_object_or_404(models.ZrpForm27Voucher, pk=pk)
            form = forms.ZrpForm27VoucherForm(request.POST, instance=voucher)
        else:
            form = forms.ZrpForm27VoucherForm(request.POST)
            
        if form.is_valid():
            v_obj = form.save(commit=False)
            if not v_obj.created_by:
                v_obj.created_by = request.user
            if v_obj.checker_user and not v_obj.checker:
                v_obj.checker = v_obj.checker_user.get_full_name() or v_obj.checker_user.username
            if v_obj.received_by_user and not v_obj.received_by_name:
                v_obj.received_by_name = v_obj.received_by_user.get_full_name() or v_obj.received_by_user.username
            v_obj.save()
            resp['status'] = 'success'
            resp['msg'] = f"Form 27 Voucher {v_obj.voucher_no} saved successfully."
            resp['redirect_url'] = reverse('view-form27', kwargs={'pk': v_obj.pk})
        else:
            resp['msg'] = form.errors.as_text()
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def view_form27(request, pk):
    """Detailed view for Form 27 Voucher with items ledger"""
    voucher = get_object_or_404(models.ZrpForm27Voucher, pk=pk)
    context = {
        'page_title': f"Z.R.P. Form 27 No. {voucher.voucher_no}",
        'voucher': voucher,
        'items': voucher.items.all(),
        'item_form': forms.ZrpForm27ItemForm(),
        'receive_form': forms.ZrpForm27ReceiveForm(instance=voucher),
        'assets': models.Asset.objects.all().order_by('name'),
    }
    return render(request, 'view_form27.html', context)

@login_required
def save_form27_item(request, pk):
    """Adds an item to the Form 27 Voucher"""
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        voucher = get_object_or_404(models.ZrpForm27Voucher, pk=pk)
        form = forms.ZrpForm27ItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.voucher = voucher
            item.save()
            
            # If item links to a specific serial number, mark serial number as In Use at that station
            if item.serial_number:
                item.serial_number.status = 'In Use'
                item.serial_number.location = voucher.station
                item.serial_number.save(update_fields=['status', 'location'])
                
            resp['status'] = 'success'
        else:
            resp['msg'] = form.errors.as_text()
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def delete_form27_item(request, pk, item_id):
    """Deletes an item from the Form 27 Voucher"""
    voucher = get_object_or_404(models.ZrpForm27Voucher, pk=pk)
    item = get_object_or_404(models.ZrpForm27Item, pk=item_id, voucher=voucher)
    item.delete()
    messages.success(request, "Item removed from Form 27 voucher.")
    return redirect('view-form27', pk=voucher.pk)

@login_required
def receive_form27(request, pk):
    """Records station receiver signoff for Form 27 Voucher"""
    voucher = get_object_or_404(models.ZrpForm27Voucher, pk=pk)
    if request.method == 'POST':
        form = forms.ZrpForm27ReceiveForm(request.POST, request.FILES, instance=voucher)
        if form.is_valid():
            v_obj = form.save(commit=False)
            if v_obj.received_by_user and not v_obj.received_by_name:
                v_obj.received_by_name = v_obj.received_by_user.get_full_name() or v_obj.received_by_user.username
            v_obj.status = 'Received'
            v_obj.save()

            # Digital Archiving in Institutional Cloud
            if 'signed_voucher_scan' in request.FILES and v_obj.signed_voucher_scan:
                dept = models.Department.objects.filter(name__icontains="ICT").first() or models.Department.objects.first()
                models.archive_to_cloud(
                    file_field=v_obj.signed_voucher_scan,
                    file_name=f"Form27_{v_obj.voucher_no}_Signed_Scan",
                    folder_name="Form 27 Delivery Notes",
                    department=dept,
                    user=request.user,
                    description=f"Signed Form 27 delivery voucher for {v_obj.station}"
                )

            messages.success(request, f"Form 27 Voucher {voucher.voucher_no} marked as RECEIVED & signed by station.")
        else:
            messages.error(request, form.errors.as_text())
    return redirect('view-form27', pk=voucher.pk)

@login_required
def print_form27(request, pk):
    """Renders the official statutory printable Z.R.P. FORM 27 (Requisition/Issue Voucher)"""
    voucher = get_object_or_404(models.ZrpForm27Voucher, pk=pk)
    context = {
        'voucher': voucher,
        'items': voucher.items.all(),
        'print_date': timezone.now(),
    }
    return render(request, 'print_form27.html', context)

@login_required
def sign_form27_electronic(request, pk):
    """
    Optional electronic receipt confirmation on Z.R.P. Form 27 Voucher:
    Authorized for Supt ICT, Chief Tech, System Manager, Provincial ICT Officers,
    Deputy Directors, Chief Director, and Superusers.
    """
    resp = {'status': 'failed', 'msg': ''}
    voucher = get_object_or_404(models.ZrpForm27Voucher, pk=pk)

    scope_info = get_procurement_user_scope(request)
    if not scope_info['can_sign_electronic']:
        msg = f"User role '{scope_info['role']}' is not authorized to electronically confirm Form 27 receipt."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax'):
            resp['msg'] = msg
            return HttpResponse(json.dumps(resp), content_type="application/json")
        messages.error(request, msg)
        return redirect('view-form27', pk=voucher.pk)

    if request.method == 'POST':
        officer_name = request.POST.get('officer_name', '').strip()
        if not officer_name:
            officer_name = request.user.get_full_name() or request.user.username
        role_title = request.POST.get('role_title', '').strip()
        if not role_title:
            role_title = scope_info['role']
        notes = request.POST.get('notes', '').strip()

        voucher.electronic_signature_confirmed = True
        voucher.electronic_signed_by = request.user
        voucher.electronic_signed_name = officer_name
        voucher.electronic_signed_role = role_title
        voucher.electronic_signed_date = timezone.now()
        voucher.electronic_signature_notes = notes
        voucher.save()

        msg = f"Z.R.P. Form 27 #{voucher.voucher_no} successfully confirmed and signed electronically by {officer_name} ({role_title})."
        try:
            messages.success(request, msg)
        except Exception:
            pass
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax'):
            resp['status'] = 'success'
            resp['msg'] = msg
            return HttpResponse(json.dumps(resp), content_type="application/json")
        return redirect('view-form27', pk=voucher.pk)

    context = {
        'voucher': voucher,
        'scope_info': scope_info,
    }
    return render(request, 'modal_sign_form27_electronic.html', context)


# --- Statutory Z.R.P. FORM 216 Views (Stores Stock / Ledger Card) ---

@login_required
def form216_list(request):
    """Lists all ZRP Form 216 Stock Ledger Cards with scope filtering"""
    scope_info = get_procurement_user_scope(request)
    scope = scope_info['scope']
    province = scope_info['province']

    cards = models.ZrpForm216Card.objects.all().prefetch_related('entries')

    comms_card_q = (
        Q(linked_asset__category='Equipment') |
        Q(article__icontains='radio') |
        Q(article__icontains='vhf') |
        Q(article__icontains='repeater') |
        Q(article__icontains='antenna') |
        Q(article__icontains='handset') |
        Q(article__icontains='battery')
    )
    systems_card_q = (
        Q(linked_asset__category='ICT') |
        Q(article__icontains='laptop') |
        Q(article__icontains='desktop') |
        Q(article__icontains='computer') |
        Q(article__icontains='server') |
        Q(article__icontains='printer') |
        Q(article__icontains='system')
    )

    if scope == 'comms':
        cards = cards.filter(comms_card_q)
    elif scope == 'systems':
        cards = cards.filter(systems_card_q)
    elif scope == 'province' and province:
        cards = cards.filter(
            Q(entries__from_to__icontains=province) |
            Q(linked_asset__serial_numbers__location__icontains=province)
        ).distinct()

    total_balance = sum(c.current_balance for c in cards)
    total_receipts = sum(c.total_receipts for c in cards)
    total_issues = sum(c.total_issues for c in cards)
    context = {
        'page_title': 'Z.R.P. Form 216 - Stores Stock Ledger Cards',
        'cards': cards,
        'total_cards': cards.count(),
        'total_balance': total_balance,
        'total_receipts': total_receipts,
        'total_issues': total_issues,
        'scope_info': scope_info,
    }
    return render(request, 'form216_list.html', context)

@login_required
def manage_form216(request, pk=None):
    """Creates or updates a Form 216 Stock Card header"""
    if pk:
        card = get_object_or_404(models.ZrpForm216Card, pk=pk)
        form = forms.ZrpForm216CardForm(instance=card)
    else:
        card = None
        count = models.ZrpForm216Card.objects.count() + 1
        yr = timezone.now().year
        default_folio = f"FOL-{yr}/{count:03d}"
        form = forms.ZrpForm216CardForm(initial={
            'folio_no': default_folio,
            'unit': 'Each',
            'bforward_date': timezone.now().date(),
            'initial_bforward_balance': 0,
        })
    context = {
        'card': card,
        'form': form,
        'assets': models.Asset.objects.all().order_by('name'),
    }
    return render(request, 'manage_form216.html', context)

@login_required
def save_form216(request):
    """Saves a Form 216 Stock Card via AJAX"""
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        pk = request.POST.get('id')
        if pk:
            card = get_object_or_404(models.ZrpForm216Card, pk=pk)
            form = forms.ZrpForm216CardForm(request.POST, instance=card)
        else:
            form = forms.ZrpForm216CardForm(request.POST)
            
        if form.is_valid():
            c_obj = form.save(commit=False)
            if not c_obj.created_by:
                c_obj.created_by = request.user
            c_obj.save()
            c_obj.recalculate_balances()
            resp['status'] = 'success'
            resp['msg'] = f"Form 216 Stock Card {c_obj.code_no} saved successfully."
            resp['redirect_url'] = reverse('view-form216', kwargs={'pk': c_obj.pk})
        else:
            resp['msg'] = form.errors.as_text()
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def view_form216(request, pk):
    """Detailed view for Form 216 Stock Card with transactions ledger"""
    card = get_object_or_404(models.ZrpForm216Card, pk=pk)
    card.recalculate_balances()
    entries = list(card.entries.all().order_by('date', '-receipts', 'id'))
    
    # Split entries into pairs for dual-column stock card display
    mid = (len(entries) + 1) // 2
    left_entries = entries[:mid] if len(entries) > 0 else []
    right_entries = entries[mid:] if len(entries) > 0 else []
    
    context = {
        'page_title': f"Z.R.P. Form 216: {card.code_no} - {card.article}",
        'card': card,
        'entries': entries,
        'left_entries': left_entries,
        'right_entries': right_entries,
        'entry_form': forms.ZrpForm216EntryForm(initial={'date': timezone.now().date()}),
        'form27_vouchers': models.ZrpForm27Voucher.objects.all().order_by('-date')[:20],
    }
    return render(request, 'view_form216.html', context)

@login_required
def save_form216_entry(request, pk):
    """Posts a Receipt or Issue transaction into the Form 216 ledger"""
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        card = get_object_or_404(models.ZrpForm216Card, pk=pk)
        form = forms.ZrpForm216EntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.card = card
            entry.created_by = request.user
            
            vchr_id = request.POST.get('linked_form27_voucher')
            if vchr_id:
                entry.linked_form27_voucher = models.ZrpForm27Voucher.objects.filter(pk=vchr_id).first()
                if entry.linked_form27_voucher and not entry.voucher_no:
                    entry.voucher_no = entry.linked_form27_voucher.voucher_no
                    
            entry.save()
            card.recalculate_balances()
            resp['status'] = 'success'
        else:
            resp['msg'] = form.errors.as_text()
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def delete_form216_entry(request, pk, entry_id):
    """Deletes an entry from Form 216 and recalculates balances"""
    card = get_object_or_404(models.ZrpForm216Card, pk=pk)
    entry = get_object_or_404(models.ZrpForm216Entry, pk=entry_id, card=card)
    entry.delete()
    card.recalculate_balances()
    messages.success(request, "Stock card entry deleted and balance recalculated.")
    return redirect('view-form216', pk=card.pk)

@login_required
def print_form216(request, pk):
    """Renders the official statutory printable Z.R.P. FORM 216 (Stock / Ledger Card)"""
    card = get_object_or_404(models.ZrpForm216Card, pk=pk)
    card.recalculate_balances()
    entries = list(card.entries.all().order_by('date', '-receipts', 'id'))
    
    # Split into 2 columns of up to 25 rows each, matching standard physical Form 216
    rows_per_col = 25
    left_entries = entries[:rows_per_col]
    right_entries = entries[rows_per_col:rows_per_col * 2]
    
    # Pad to create paired rows for the physical dual-column layout
    paired_rows = []
    max_rows = max(24, max(len(left_entries), len(right_entries)))
    for i in range(max_rows):
        l = left_entries[i] if i < len(left_entries) else None
        r = right_entries[i] if i < len(right_entries) else None
        paired_rows.append((l, r))
        
    context = {
        'card': card,
        'paired_rows': paired_rows,
        'entries': entries,
        'print_date': timezone.now(),
    }
    return render(request, 'print_form216.html', context)


# --- Statutory GOODS RECEIVED Ledger Views ---

@login_required
def goods_received_list(request):
    """Displays the Goods Received Ledger/Register with search, scope filter, and KPI counts"""
    scope_info = get_procurement_user_scope(request)
    scope = scope_info['scope']
    province = scope_info['province']

    entries = models.GoodsReceivedEntry.objects.all().order_by('-date', '-id')
    
    # Filter by search query if present
    q = request.GET.get('q', '').strip()
    if q:
        entries = entries.filter(
            Q(goods_received__icontains=q) |
            Q(company__icontains=q) |
            Q(po_no__icontains=q) |
            Q(receiver__icontains=q) |
            Q(checker__icontains=q) |
            Q(cross_ref__icontains=q) |
            Q(bin_no__icontains=q) |
            Q(entry_no__icontains=q)
        )

    comms_gr_q = (
        Q(goods_received__icontains='radio') |
        Q(goods_received__icontains='vhf') |
        Q(goods_received__icontains='repeater') |
        Q(goods_received__icontains='antenna') |
        Q(goods_received__icontains='handset') |
        Q(goods_received__icontains='comms')
    )
    systems_gr_q = (
        Q(goods_received__icontains='laptop') |
        Q(goods_received__icontains='desktop') |
        Q(goods_received__icontains='computer') |
        Q(goods_received__icontains='server') |
        Q(goods_received__icontains='system') |
        Q(goods_received__icontains='printer') |
        Q(goods_received__icontains='all in one')
    )

    if scope == 'comms':
        entries = entries.filter(comms_gr_q)
    elif scope == 'systems':
        entries = entries.filter(systems_gr_q)
    elif scope == 'province' and province:
        entries = entries.filter(
            Q(goods_received__icontains=province) |
            Q(receiver__icontains=province) |
            Q(company__icontains=province)
        )
    
    total_qty = sum(e.qty for e in entries)
    total_entries = entries.count()
    companies = entries.values('company').distinct().count()
    
    context = {
        'page_title': 'GOODS RECEIVED Ledger & Register',
        'entries': entries,
        'total_entries': total_entries,
        'total_qty': total_qty,
        'companies_count': companies,
        'q': q,
        'scope_info': scope_info,
    }
    return render(request, 'goods_received_list.html', context)

@login_required
def manage_goods_received(request, pk=None):
    """Modal view for recording or editing a Goods Received entry"""
    if pk:
        entry = get_object_or_404(models.GoodsReceivedEntry, pk=pk)
        form = forms.GoodsReceivedEntryForm(instance=entry)
        suggested_entry_no = entry.entry_no
    else:
        entry = None
        suggested_entry_no = models.GoodsReceivedEntry.get_next_entry_no()
        user_name = request.user.last_name.upper() if request.user.last_name else request.user.username.upper()
        form = forms.GoodsReceivedEntryForm(initial={
            'date': timezone.now().date(),
            'receiver_user': request.user,
            'checker_user': request.user,
            'receiver': user_name,
            'checker': user_name,
            'qty': 1,
            'bal': 0,
        })
    context = {
        'entry': entry,
        'form': form,
        'suggested_entry_no': suggested_entry_no,
    }
    return render(request, 'manage_goods_received.html', context)

@login_required
def save_goods_received(request):
    """Saves a Goods Received entry via AJAX"""
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        pk = request.POST.get('id')
        if pk:
            entry = get_object_or_404(models.GoodsReceivedEntry, pk=pk)
            form = forms.GoodsReceivedEntryForm(request.POST, request.FILES, instance=entry)
        else:
            form = forms.GoodsReceivedEntryForm(request.POST, request.FILES)
            
        if form.is_valid():
            gr = form.save(commit=False)
            if not gr.created_by:
                gr.created_by = request.user

            # Auto-generate sequential entry number (NN/YYYY) for new records
            # For edits, keep the existing entry_no unchanged
            if not pk or not gr.entry_no:
                entry_year = gr.date.year if gr.date else timezone.now().year
                gr.entry_no = models.GoodsReceivedEntry.get_next_entry_no(entry_year)

            # Prioritize directly typed receiver and checker names
            typed_receiver = request.POST.get('receiver', '').strip()
            if typed_receiver:
                gr.receiver = typed_receiver
            elif gr.receiver_user:
                gr.receiver = gr.receiver_user.get_full_name() or gr.receiver_user.username
            elif not gr.receiver:
                gr.receiver = request.user.get_full_name() or request.user.username

            typed_checker = request.POST.get('checker', '').strip()
            if typed_checker:
                gr.checker = typed_checker
            elif gr.checker_user:
                gr.checker = gr.checker_user.get_full_name() or gr.checker_user.username
            elif not gr.checker:
                gr.checker = request.user.get_full_name() or request.user.username
            gr.save()
            
            # Digital Archiving in Institutional Cloud
            if 'delivery_note_scan' in request.FILES and gr.delivery_note_scan:
                models.archive_to_cloud(
                    file_field=gr.delivery_note_scan,
                    file_name=f"GR_{gr.entry_no or gr.pk}_Delivery_Note",
                    folder_name="Goods Received Scans",
                    department=gr.department,
                    user=request.user,
                    description=f"Goods Received delivery note for {gr.goods_received} from {gr.company}"
                )

            resp['status'] = 'success'
            resp['entry_no'] = gr.entry_no
            resp['msg'] = f"Goods Received entry #{gr.entry_no} saved successfully."
        else:
            resp['msg'] = form.errors.as_text()
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def delete_goods_received(request, pk):
    """Deletes a Goods Received ledger entry"""
    entry = get_object_or_404(models.GoodsReceivedEntry, pk=pk)
    entry.delete()
    messages.success(request, "Goods Received entry deleted.")
    return redirect('goods-received-list')

@login_required
def print_goods_received_ledger(request):
    """Renders the official statutory printable GOODS RECEIVED ledger matching physical format"""
    entries = list(models.GoodsReceivedEntry.objects.all().order_by('date', 'id'))
    
    # Pad to at least 25 ruled rows for standard printed ledger sheet
    total_pad = max(25, len(entries))
    padded_rows = []
    for i in range(total_pad):
        if i < len(entries):
            padded_rows.append(entries[i])
        else:
            padded_rows.append(None)
            
    context = {
        'entries': entries,
        'padded_rows': padded_rows,
        'print_date': timezone.now(),
        'total_qty': sum(e.qty for e in entries),
    }
    return render(request, 'print_goods_received.html', context)


# --- Statutory ISSUES REGISTER Views ---

@login_required
def issues_register_list(request):
    """Displays the Issues Register with search, scope filter, and metrics"""
    scope_info = get_procurement_user_scope(request)
    scope = scope_info['scope']
    province = scope_info['province']

    entries = models.IssuesRegisterEntry.objects.all().order_by('-date', '-id')
    
    q = request.GET.get('q', '').strip()
    urgency_filter = request.GET.get('urgency', '').strip()

    if q:
        entries = entries.filter(
            Q(item_description__icontains=q) |
            Q(requesting_station__icontains=q) |
            Q(station_ref__icontains=q) |
            Q(item_class__icontains=q) |
            Q(issuer__icontains=q) |
            Q(receiver_details__icontains=q) |
            Q(entry_no__icontains=q)
        )
    if urgency_filter:
        entries = entries.filter(urgency=urgency_filter)

    comms_ir_q = (
        Q(item_description__icontains='radio') |
        Q(item_description__icontains='vhf') |
        Q(item_description__icontains='repeater') |
        Q(item_description__icontains='antenna') |
        Q(item_description__icontains='handset') |
        Q(item_class__icontains='comms') |
        Q(item_class__icontains='radio')
    )
    systems_ir_q = (
        Q(item_description__icontains='laptop') |
        Q(item_description__icontains='desktop') |
        Q(item_description__icontains='computer') |
        Q(item_description__icontains='server') |
        Q(item_description__icontains='system') |
        Q(item_description__icontains='printer') |
        Q(item_class__icontains='ict') |
        Q(item_class__icontains='system')
    )

    if scope == 'comms':
        entries = entries.filter(comms_ir_q)
    elif scope == 'systems':
        entries = entries.filter(systems_ir_q)
    elif scope == 'province' and province:
        entries = entries.filter(requesting_station__icontains=province)
        
    total_qty = sum(e.qty for e in entries)
    total_entries = entries.count()
    stations_count = entries.values('requesting_station').distinct().count()
    
    context = {
        'page_title': 'ISSUES REGISTER - Equipment Dispatch Ledger',
        'entries': entries,
        'total_entries': total_entries,
        'total_qty': total_qty,
        'stations_count': stations_count,
        'q': q,
        'urgency_filter': urgency_filter,
        'scope_info': scope_info,
    }
    return render(request, 'issues_register_list.html', context)

@login_required
def manage_issues_register(request, pk=None):
    """Modal view for recording or editing an Issues Register entry with Asset and Serial Number selection"""
    current_year = timezone.now().year
    if pk:
        entry = get_object_or_404(models.IssuesRegisterEntry, pk=pk)
        form = forms.IssuesRegisterEntryForm(instance=entry)
        suggested_entry_no = entry.entry_no
    else:
        entry = None
        suggested_entry_no = models.IssuesRegisterEntry.get_next_entry_no(current_year)
        user_name = request.user.get_full_name() or request.user.username
        # Default target_date for Normal (7 days)
        target_date_default = timezone.now().date() + datetime.timedelta(days=7)
        form = forms.IssuesRegisterEntryForm(initial={
            'entry_no': suggested_entry_no,
            'date': timezone.now().date(),
            'date_requested': timezone.now().date(),
            'urgency': 'Normal',
            'target_date': target_date_default,
            'issuer': user_name.upper(),
            'qty': 1,
        })

    # Ensure every active asset has concrete serial numbers in AssetSerialNumber
    for a in models.Asset.objects.exclude(status='Issued'):
        if a.serial_numbers.count() == 0:
            qty = a.quantity_delivered or 1
            if qty == 1:
                models.AssetSerialNumber.objects.get_or_create(
                    asset=a, serial_number=a.asset_code, defaults={'status': a.status, 'barcode': a.asset_code}
                )
            else:
                for i in range(1, qty + 1):
                    models.AssetSerialNumber.objects.get_or_create(
                        asset=a, serial_number=f"{a.asset_code}-{i:02d}", defaults={'status': a.status, 'barcode': f"{a.asset_code}-{i:02d}"}
                    )

    # Active serial numbers in stores (unissued)
    available_serials = models.AssetSerialNumber.objects.filter(status='Active').select_related('asset').order_by('asset__category', 'asset__name', 'serial_number')

    serials_data = []
    for sn in available_serials:
        is_t = bool(sn.asset and sn.asset.quality_test_passed and sn.asset.inspection_status == 'Quality Approved' and sn.asset.is_cleared)
        serials_data.append({
            'serial_id': sn.id,
            'serial_number': sn.serial_number,
            'asset_id': sn.asset.id if sn.asset else None,
            'asset_name': sn.asset.name if sn.asset else '',
            'asset_code': sn.asset.asset_code if sn.asset else '',
            'category': sn.asset.category if sn.asset else '',
            'category_display': sn.asset.get_category_display() if sn.asset else '',
            'item_type': getattr(sn.asset, 'item_type', 'Asset') if sn.asset else 'Asset',
            'is_tested': is_t,
            'inspection_status': sn.asset.inspection_status if sn.asset else 'Pending Inspection',
            'location': sn.location or 'Central Stores',
        })

    # Available assets with active stock
    available_assets = models.Asset.objects.exclude(status='Issued').filter(
        Q(quantity_delivered__gt=0) | Q(quantity_delivered__isnull=True)
    ).order_by('category', 'name')

    assets_data = []
    for a in available_assets:
        act_serials = list(a.serial_numbers.filter(status='Active').values_list('serial_number', flat=True))
        is_t = bool(a.quality_test_passed and a.inspection_status == 'Quality Approved' and a.is_cleared)
        assets_data.append({
            'id': a.id,
            'name': a.name,
            'asset_code': a.asset_code,
            'category': a.category,
            'category_display': a.get_category_display(),
            'item_type': getattr(a, 'item_type', 'Asset'),
            'qty': a.quantity_delivered if a.quantity_delivered is not None else len(act_serials) or 1,
            'active_serials': act_serials,
            'is_tested': is_t,
            'inspection_status': a.inspection_status or 'Pending Inspection',
            'department': a.department.name if a.department else '',
        })

    context = {
        'entry': entry,
        'form': form,
        'suggested_entry_no': suggested_entry_no,
        'available_assets': available_assets,
        'assets_json': json.dumps(assets_data),
        'serials_json': json.dumps(serials_data),
        'categories': models.Asset.CATEGORY_CHOICES,
        'item_types': getattr(models.Asset, 'ITEM_TYPE_CHOICES', (('Asset', 'Capital / Fixed Asset'), ('Inventory', 'Inventory / Stock / Consumables'))),
        'available_users': User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username'),
    }
    return render(request, 'manage_issues_register.html', context)

@login_required
def save_issues_register(request):
    """Saves an Issues Register entry via AJAX, deducts specific serial numbers & asset quantities, and auto-generates Form 27 (Delivery Note)"""
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        pk = request.POST.get('id')
        if pk:
            entry = get_object_or_404(models.IssuesRegisterEntry, pk=pk)
            form = forms.IssuesRegisterEntryForm(request.POST, request.FILES, instance=entry)
        else:
            form = forms.IssuesRegisterEntryForm(request.POST, request.FILES)
            
        if form.is_valid():
            iss = form.save(commit=False)
            if not iss.created_by:
                iss.created_by = request.user
            
            # Ensure entry_no is formatted as NN/YYYY (e.g. 01/2026, 02/2026)
            issue_year = iss.date.year if iss.date else timezone.now().year
            if not iss.entry_no or iss.entry_no.strip() == '' or iss.entry_no.startswith('ISS-'):
                iss.entry_no = models.IssuesRegisterEntry.get_next_entry_no(issue_year)

            # Auto-calculate target_date based on urgency
            if iss.urgency == 'Immediate':
                iss.target_date = iss.date
            elif iss.urgency == 'Urgent':
                iss.target_date = iss.date + datetime.timedelta(days=2)
            else: # Normal
                iss.target_date = iss.date + datetime.timedelta(days=7)

            # Extract selected serial number IDs
            raw_serial_ids = request.POST.getlist('selected_serial_ids[]')
            if not raw_serial_ids and request.POST.get('selected_serial_ids'):
                raw_serial_ids = [s.strip() for s in request.POST.get('selected_serial_ids').split(',') if s.strip()]
            
            serial_ids = []
            for sid in raw_serial_ids:
                try:
                    serial_ids.append(int(sid))
                except (ValueError, TypeError):
                    pass

            serials_qs = models.AssetSerialNumber.objects.filter(id__in=serial_ids).select_related('asset')

            # REQUIREMENT: Do not allow to issue an item if it is not 100% fully tested.
            assets_to_validate = set()
            if serials_qs.exists():
                for sn in serials_qs:
                    if sn.asset:
                        assets_to_validate.add(sn.asset)
            elif iss.linked_asset:
                assets_to_validate.add(iss.linked_asset)

            untested_assets = []
            for a_obj in assets_to_validate:
                if not (a_obj.quality_test_passed and a_obj.inspection_status == 'Quality Approved' and a_obj.is_cleared):
                    untested_assets.append(a_obj)

            if untested_assets:
                untested_names = ", ".join(f"'{a.name}' (Code: {a.asset_code}, Status: {a.inspection_status or 'Pending Inspection'})" for a in untested_assets)
                resp['msg'] = f"Dispatch Blocked: {untested_names} is not 100% fully tested. All items must pass technical testing and quality clearance before issuance."
                return HttpResponse(json.dumps(resp), content_type="application/json")

            if serials_qs.exists():
                # Auto-populate quantity to total number of selected serial numbers
                iss.qty = serials_qs.count()
                
                # Group by parent asset
                asset_serials_map = {}
                for sn in serials_qs:
                    asset_serials_map.setdefault(sn.asset, []).append(sn)
                
                # Auto-compile item description listing all assets and their serial numbers
                desc_lines = []
                for asset_obj, sn_list in asset_serials_map.items():
                    sn_tokens = [s.serial_number for s in sn_list]
                    desc_lines.append(f"{asset_obj.name} (S/N: {', '.join(sn_tokens)})")
                
                compiled_desc = "; ".join(desc_lines)
                if not iss.item_description or iss.item_description.strip() == '' or len(serials_qs) > 1:
                    iss.item_description = compiled_desc
                
                iss.save()
                
                # 1. Deduct every selected serial number from Asset Registry (set status='Issued')
                for sn in serials_qs:
                    sn.status = 'Issued'
                    sn.location = f"Issued to {iss.requesting_station}"
                    sn.notes = f"Dispatched under Issues Reg #{iss.entry_no} to {iss.requesting_station} on {iss.date}"
                    sn.save(update_fields=['status', 'location', 'notes'])
                    iss.issued_serials.add(sn)
                
                # 2. Deduct from each parent asset & mark 'Issued' if all serials are dispatched
                first_asset = None
                for asset_obj, sn_list in asset_serials_map.items():
                    if not first_asset:
                        first_asset = asset_obj
                    iss.issued_assets.add(asset_obj)
                    
                    count_issued = len(sn_list)
                    current_qty = asset_obj.quantity_delivered if asset_obj.quantity_delivered is not None else asset_obj.serial_numbers.count()
                    asset_obj.quantity_delivered = max(0, current_qty - count_issued)
                    
                    # Remaining active serials in registry
                    remaining_active = asset_obj.serial_numbers.filter(status='Active').count()
                    if remaining_active == 0 or asset_obj.quantity_delivered <= 0:
                        asset_obj.quantity_delivered = 0
                        asset_obj.status = 'Issued'
                    
                    if asset_obj.unit_cost and asset_obj.unit_cost > 0:
                        asset_obj.acquisition_cost = asset_obj.unit_cost * (asset_obj.quantity_delivered or 1)
                    
                    asset_obj.save()

                if not iss.linked_asset and first_asset:
                    iss.linked_asset = first_asset
                    iss.save(update_fields=['linked_asset'])
            else:
                # Fallback: single asset deduction without explicit serial numbers
                iss.save()
                if iss.linked_asset:
                    asset = iss.linked_asset
                    current_qty = asset.quantity_delivered if asset.quantity_delivered is not None else 1
                    issued_qty = iss.qty or 1
                    
                    if issued_qty >= current_qty:
                        asset.quantity_delivered = 0
                        asset.status = 'Issued'
                    else:
                        asset.quantity_delivered = current_qty - issued_qty
                    
                    if asset.unit_cost and asset.unit_cost > 0:
                        asset.acquisition_cost = asset.unit_cost * (asset.quantity_delivered or 1)
                    asset.save()

            # Digital Cloud Archiving of Issues Register documents
            if 'voucher_scan' in request.FILES and iss.voucher_scan:
                models.archive_to_cloud(
                    file_field=iss.voucher_scan,
                    file_name=f"Issues_Voucher_{iss.entry_no or iss.pk}",
                    folder_name="Issues Register Scans",
                    department=iss.department,
                    user=request.user,
                    description=f"Signed voucher scan for Issue #{iss.entry_no} to {iss.requesting_station}"
                )
            if 'receiver_signature_image' in request.FILES and iss.receiver_signature_image:
                models.archive_to_cloud(
                    file_field=iss.receiver_signature_image,
                    file_name=f"Issues_Sig_{iss.entry_no or iss.pk}",
                    folder_name="Issues Register Scans",
                    department=iss.department,
                    user=request.user,
                    description=f"Receiver signature image for Issue #{iss.entry_no}"
                )

            # 3. Determine checker and receiver names for Form 27 and Issues Register
            typed_receiver_details = request.POST.get('receiver_details', '').strip()
            if typed_receiver_details:
                iss.receiver_details = typed_receiver_details
            elif iss.receiver_user:
                rec_name = iss.receiver_user.get_full_name() or iss.receiver_user.username
                iss.receiver_details = f"{rec_name} (Received in Good Order)"

            checker_user_id = request.POST.get('checker_user')
            checker_user_obj = None
            checker_name = request.POST.get('checker_name', '').strip()
            if checker_user_id:
                try:
                    checker_user_obj = User.objects.get(pk=int(checker_user_id))
                    if not checker_name:
                        checker_name = checker_user_obj.get_full_name() or checker_user_obj.username
                    iss.checker_user = checker_user_obj
                except (User.DoesNotExist, ValueError):
                    pass
            if not checker_name:
                checker_name = 'CST KADIKI'
            iss.save()

            item_type_val = request.POST.get('issue_item_type', 'Asset')

            # 4. Auto-generate Form 27 (Delivery Note) with separate line items for each asset
            form27_voucher = iss.linked_form27_voucher
            if not form27_voucher:
                voucher_candidate = f"F27-{iss.entry_no}"
                if models.ZrpForm27Voucher.objects.filter(voucher_no=voucher_candidate).exists():
                    voucher_candidate = f"F27-{iss.entry_no}-{iss.pk}"
                
                form27_voucher = models.ZrpForm27Voucher.objects.create(
                    voucher_no=voucher_candidate,
                    date=iss.date,
                    issued_by=iss.issuer or "O.I.C CENTRAL RADIO STORES   (I.C.T)",
                    station=iss.requesting_station,
                    station_date=iss.date_requested or iss.date,
                    requisition_no=iss.station_ref or f"ISS-{iss.entry_no}",
                    how_dispatched=f"Dispatched under Issues Reg #{iss.entry_no} ({iss.urgency})",
                    checker=checker_name,
                    checker_user=checker_user_obj,
                    checker_date=iss.date,
                    received_by_user=iss.receiver_user,
                    received_by_name=iss.receiver_details or (iss.receiver_user.get_full_name() if iss.receiver_user else ""),
                    status='Issued',
                    created_by=request.user
                )
                
                # If multiple assets with serials were issued, create separate line items for each asset
                if serials_qs.exists():
                    for asset_obj, sn_list in asset_serials_map.items():
                        sn_tokens = [s.serial_number for s in sn_list]
                        models.ZrpForm27Item.objects.create(
                            voucher=form27_voucher,
                            asset=asset_obj,
                            item_type=getattr(asset_obj, 'item_type', item_type_val),
                            description=f"{asset_obj.name} (S/N: {', '.join(sn_tokens)})",
                            quantity=len(sn_list),
                            stores_use_only=f"Issues Reg #{iss.entry_no} [{iss.urgency}]",
                            remarks=f"Dispatched to {iss.requesting_station}"
                        )
                else:
                    models.ZrpForm27Item.objects.create(
                        voucher=form27_voucher,
                        asset=iss.linked_asset,
                        item_type=getattr(iss.linked_asset, 'item_type', item_type_val) if iss.linked_asset else item_type_val,
                        description=iss.item_description,
                        stores_use_only=f"Issues Reg #{iss.entry_no} [{iss.urgency}]",
                        quantity=iss.qty,
                        remarks=f"Issued to {iss.requesting_station} (Due: {iss.target_date})"
                    )
                
                iss.linked_form27_voucher = form27_voucher
                iss.save(update_fields=['linked_form27_voucher'])

            # 5. Form 216 Audit Trail interpreting Form 27 (creates debit entries on stock card)
            for f27_item in form27_voucher.items.all():
                art_name = f27_item.asset.name if f27_item.asset else f27_item.description.split('(')[0].strip()
                code_no = f27_item.asset.asset_code if f27_item.asset else f"STK-{f27_item.pk:04d}"
                card, created_card = models.ZrpForm216Card.objects.get_or_create(
                    code_no=code_no,
                    defaults={
                        'article': art_name,
                        'unit': 'Each',
                        'folio_no': f"FOL-{iss.date.year if iss.date else timezone.now().year}/{iss.pk}",
                        'department': iss.department,
                        'current_balance': 0,
                        'created_by': request.user,
                        'linked_asset': f27_item.asset,
                    }
                )
                if not card.linked_asset and f27_item.asset:
                    card.linked_asset = f27_item.asset
                    card.save(update_fields=['linked_asset'])

                # IMPORTANT: If card has no intake receipts, record the initial consignment intake first
                # so the stock on hand balance is accurate and never negative!
                if card.entries.filter(receipts__gt=0).count() == 0:
                    target_asset = f27_item.asset or card.linked_asset or models.Asset.objects.filter(asset_code=card.code_no).first()
                    intake_qty = f27_item.quantity
                    intake_voucher = f"REC-{card.code_no}"
                    intake_from = "From Supplier"
                    intake_date = iss.date
                    if target_asset:
                        serials_total = target_asset.serial_numbers.count()
                        deliv = target_asset.quantity_delivered or 0
                        exp = target_asset.quantity_expected or 0
                        intake_qty = max(serials_total, deliv + f27_item.quantity, exp, f27_item.quantity)
                        if target_asset.goods_received_entry:
                            intake_voucher = target_asset.goods_received_entry.entry_no
                            intake_from = f"From {target_asset.goods_received_entry.company}"
                        elif target_asset.delivery_note_number:
                            intake_voucher = target_asset.delivery_note_number
                            intake_from = f"From {target_asset.supplier_name or 'Supplier'}"
                        else:
                            intake_voucher = f"REC-{target_asset.asset_code}"
                            intake_from = f"From {target_asset.supplier_name or 'Supplier'}"
                        intake_date = target_asset.acquisition_date or iss.date

                    models.ZrpForm216Entry.objects.create(
                        card=card,
                        date=intake_date,
                        voucher_no=intake_voucher,
                        from_to=intake_from,
                        receipts=intake_qty,
                        issues=0,
                        remarks=f"Initial consignment intake: {art_name}",
                        created_by=request.user
                    )

                models.ZrpForm216Entry.objects.create(
                    card=card,
                    date=iss.date,
                    voucher_no=form27_voucher.voucher_no,
                    from_to=f"To {iss.requesting_station}",
                    receipts=0,
                    issues=f27_item.quantity,
                    remarks=f"Audit trail: Form 27 #{form27_voucher.voucher_no} Issue to {iss.requesting_station} [Issues Reg #{iss.entry_no}]",
                    linked_form27_voucher=form27_voucher,
                    created_by=request.user
                )
                card.recalculate_balances()

            form27_print_url = reverse('print-form27', kwargs={'pk': form27_voucher.pk})
            form27_view_url = reverse('view-form27', kwargs={'pk': form27_voucher.pk})

            resp['status'] = 'success'
            resp['entry_no'] = iss.entry_no
            resp['form27_id'] = form27_voucher.pk
            resp['form27_no'] = form27_voucher.voucher_no
            resp['form27_print_url'] = form27_print_url
            resp['form27_view_url'] = form27_view_url
            resp['msg'] = (
                f"Issues Register entry #{iss.entry_no} recorded successfully! "
                f"Z.R.P. Form 27 (Delivery Note) #{form27_voucher.voucher_no} has been automatically generated, "
                f"and Form 216 Stock Card audit trail updated."
            )
        else:
            resp['msg'] = form.errors.as_text()
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def delete_issues_register(request, pk):
    """Deletes an Issues Register entry"""
    entry = get_object_or_404(models.IssuesRegisterEntry, pk=pk)
    entry.delete()
    messages.success(request, "Issues Register entry deleted.")
    return redirect('issues-register-list')

@login_required
def print_issues_register(request):
    """Renders the official statutory printable ISSUES REGISTER sheet"""
    entries = list(models.IssuesRegisterEntry.objects.all().order_by('date', 'id'))
    
    total_pad = max(25, len(entries))
    padded_rows = []
    for i in range(total_pad):
        if i < len(entries):
            padded_rows.append(entries[i])
        else:
            padded_rows.append(None)
            
    context = {
        'entries': entries,
        'padded_rows': padded_rows,
        'print_date': timezone.now(),
        'total_qty': sum(e.qty for e in entries),
    }
    return render(request, 'print_issues_register.html', context)


# --- Statutory TENDER PROCEDURES Views ---

@login_required
def tender_procedures_list(request):
    """Displays the Tender Procedures ledger with search, filter, and value metrics"""
    entries = models.TenderProcedureEntry.objects.all().order_by('-date', '-id')
    
    q = request.GET.get('q', '').strip()
    if q:
        entries = entries.filter(
            Q(item_description__icontains=q) |
            Q(requesting_station__icontains=q) |
            Q(ict_ref__icontains=q) |
            Q(purchase_order_no__icontains=q) |
            Q(remarks__icontains=q) |
            Q(entry_no__icontains=q)
        )
        
    total_qty = sum(e.qty for e in entries)
    total_value = sum(e.total_price for e in entries)
    total_entries = entries.count()
    stations_count = entries.values('requesting_station').distinct().count()
    
    context = {
        'page_title': 'TENDER PROCEDURES - Procurement & Contract Ledger',
        'entries': entries,
        'total_entries': total_entries,
        'total_qty': total_qty,
        'total_value': total_value,
        'stations_count': stations_count,
        'q': q,
    }
    return render(request, 'tender_procedures_list.html', context)

@login_required
def manage_tender_procedure(request, pk=None):
    """Modal view for recording or editing a Tender Procedure entry"""
    if pk:
        entry = get_object_or_404(models.TenderProcedureEntry, pk=pk)
        form = forms.TenderProcedureEntryForm(instance=entry)
    else:
        entry = None
        count = models.TenderProcedureEntry.objects.count() + 1
        yr = timezone.now().year
        default_entry_no = f"TND-{count:03d}/{str(yr)[2:]}"
        form = forms.TenderProcedureEntryForm(initial={
            'entry_no': default_entry_no,
            'date': timezone.now().date(),
            'qty': 1,
            'total_price': 0.00,
        })
    context = {
        'entry': entry,
        'form': form,
    }
    return render(request, 'manage_tender_procedure.html', context)

@login_required
def save_tender_procedure(request):
    """Saves a Tender Procedure entry via AJAX"""
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        pk = request.POST.get('id')
        if pk:
            entry = get_object_or_404(models.TenderProcedureEntry, pk=pk)
            form = forms.TenderProcedureEntryForm(request.POST, request.FILES, instance=entry)
        else:
            form = forms.TenderProcedureEntryForm(request.POST, request.FILES)
            
        if form.is_valid():
            tp = form.save(commit=False)
            if not tp.created_by:
                tp.created_by = request.user
            tp.save()
            resp['status'] = 'success'
            resp['msg'] = f"Tender Procedure entry {tp.entry_no or tp.pk} saved successfully."
        else:
            resp['msg'] = form.errors.as_text()
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def delete_tender_procedure(request, pk):
    """Deletes a Tender Procedure entry"""
    entry = get_object_or_404(models.TenderProcedureEntry, pk=pk)
    entry.delete()
    messages.success(request, "Tender Procedure entry deleted.")
    return redirect('tender-procedures-list')

@login_required
def print_tender_procedures(request):
    """Renders the official statutory printable TENDER PROCEDURES ledger"""
    entries = list(models.TenderProcedureEntry.objects.all().order_by('date', 'id'))
    
    total_pad = max(25, len(entries))
    padded_rows = []
    for i in range(total_pad):
        if i < len(entries):
            padded_rows.append(entries[i])
        else:
            padded_rows.append(None)
            
    context = {
        'entries': entries,
        'padded_rows': padded_rows,
        'print_date': timezone.now(),
        'total_qty': sum(e.qty for e in entries),
        'total_value': sum(e.total_price for e in entries),
    }
    return render(request, 'print_tender_procedures.html', context)


@login_required
def save_asset_maintenance(request):
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        asset_id = request.POST.get('asset')
        asset = get_object_or_404(models.Asset, id=asset_id)
        form = forms.AssetMaintenanceForm(request.POST)
        if form.is_valid():
            mnt = form.save(commit=False)
            mnt.asset = asset
            mnt.save()
            resp['status'] = 'success'
        else:
            resp['msg'] = form.errors.as_text()
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def save_asset_custody(request):
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        asset_id = request.POST.get('asset')
        asset = get_object_or_404(models.Asset, id=asset_id)
        form = forms.AssetCustodyForm(request.POST)
        if form.is_valid():
            # Close previous custody if open
            models.AssetCustody.objects.filter(asset=asset, return_date__isnull=True).update(return_date=timezone.now().date())
            
            cstd = form.save(commit=False)
            cstd.asset = asset
            cstd.save()
            resp['status'] = 'success'
        else:
            resp['msg'] = form.errors.as_text()
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def asset_depreciation_report(request):
    from decimal import Decimal
    assets = models.Asset.objects.all()
    total_cost = Decimal('0.00')
    total_value = Decimal('0.00')
    
    report_data = []
    for asset in assets:
        c_val = asset.current_value
        total_cost += asset.acquisition_cost
        total_value += c_val
        report_data.append({
            'asset': asset,
            'current_value': c_val,
            'depreciation': asset.acquisition_cost - c_val
        })
        
    context = {
        'page_title': 'Asset Depreciation Report',
        'report_data': report_data,
        'total_cost': total_cost,
        'total_value': total_value
    }
    return render(request, 'asset_depreciation.html', context)

# --- Institutional Knowledge Vault Views ---

@login_required
def knowledge_vault(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    type_filter = request.GET.get('type', '')
    
    entries = models.KnowledgeEntry.objects.exclude(status='Superseded')
    
    if query:
        from django.db.models import Q
        entries = entries.filter(Q(title__icontains=query) | Q(content__icontains=query) | Q(tags__name__icontains=query)).distinct()
    
    if category_id:
        entries = entries.filter(category_id=category_id)
        try:
            category_id = int(category_id)
        except:
            pass
        
    if type_filter:
        entries = entries.filter(entry_type=type_filter)
        
    context = {
        'page_title': 'Institutional Knowledge Vault',
        'entries': entries,
        'categories': models.KnowledgeCategory.objects.all(),
        'recent_decisions': models.KnowledgeEntry.objects.filter(entry_type='Decision').order_by('-date_created')[:5],
        'tags': models.KnowledgeTag.objects.all()[:20],
        'query': query,
        'selected_category': category_id,
        'selected_type': type_filter
    }
    return render(request, 'knowledge_vault.html', context)

@login_required
def manage_knowledge(request, pk=None):
    if pk:
        entry = get_object_or_404(models.KnowledgeEntry, pk=pk)
        form = forms.KnowledgeEntryForm(instance=entry)
    else:
        entry = None
        form = forms.KnowledgeEntryForm()
    
    context = {
        'form': form,
        'entry': entry,
        'categories': models.KnowledgeCategory.objects.all()
    }
    return render(request, 'manage_knowledge.html', context)

@login_required
def save_knowledge(request):
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        pk = request.POST.get('id')
        if pk:
            entry = get_object_or_404(models.KnowledgeEntry, pk=pk)
            # Check for versioning
            old_content = entry.content
            form = forms.KnowledgeEntryForm(request.POST, instance=entry)
        else:
            entry = None
            form = forms.KnowledgeEntryForm(request.POST)

        if form.is_valid():
            new_entry = form.save(commit=False)
            if not pk:
                new_entry.created_by = request.user
            
            # If content changed and it's an existing entry, create a version
            if pk and old_content != new_entry.content:
                models.KnowledgeVersion.objects.create(
                    entry=entry,
                    version_num=getattr(entry, 'current_version', 0) or 1,
                    content=old_content,
                    change_summary=request.POST.get('change_summary', 'Updated content'),
                    created_by=request.user
                )
                if not hasattr(new_entry, 'current_version') or new_entry.current_version is None:
                    new_entry.current_version = 1
                new_entry.current_version += 1
            
            new_entry.save()
            form.save_m2m() # Save tags if any
            
            # Handle tags (comma separated)
            tag_names = request.POST.get('tag_names', '').split(',')
            for name in tag_names:
                name = name.strip()
                if name:
                    tag, _ = models.KnowledgeTag.objects.get_or_create(name=name)
                    new_entry.tags.add(tag)
            
            resp['status'] = 'success'
            resp['msg'] = 'Knowledge record saved successfully.'
        else:
            resp['msg'] = form.errors.as_text()
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def view_knowledge(request, pk):
    entry = get_object_or_404(models.KnowledgeEntry, pk=pk)
    
    # Related cases logic: overlapping tags or same category
    related_entries = models.KnowledgeEntry.objects.filter(
        category=entry.category
    ).exclude(pk=entry.pk).distinct()[:5]
    
    if entry.tags.exists():
        tag_related = models.KnowledgeEntry.objects.filter(
            tags__in=entry.tags.all()
        ).exclude(pk=entry.pk).distinct()[:5]
        # Combine and unique
        related_entries = (related_entries | tag_related).distinct()[:5]

    context = {
        'page_title': entry.title,
        'entry': entry,
        'related_entries': related_entries,
        'versions': entry.versions.all(),
        'relations': entry.outgoing_relations.all() | entry.incoming_relations.all()
    }
    return render(request, 'view_knowledge.html', context)

@login_required
def save_knowledge_relation(request):
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        form = forms.KnowledgeRelationForm(request.POST)
        source_id = request.POST.get('source_id')
        source = get_object_or_404(models.KnowledgeEntry, id=source_id)
        
        if form.is_valid():
            rel = form.save(commit=False)
            rel.source = source
            rel.save()
            resp['status'] = 'success'
            messages.success(request, "Relation saved successfully.")
        else:
            resp['msg'] = form.errors.as_text()
    return HttpResponse(json.dumps(resp), content_type="application/json")

# --- Financial Governance (Budget & Expenditure) ---

@login_required
def budget_list(request):
    if not request.user.is_superuser:
        messages.error(request, "Access Denied.")
        return redirect('home-page')
    context = context_data(request)
    context['page_title'] = "Departmental Budgets"
    context['budgets'] = models.Budget.objects.all().order_by('department__name', '-fiscal_year')
    return render(request, 'budget_list.html', context)

@login_required
def manage_budget(request, pk=None):
    if not request.user.is_superuser:
        messages.error(request, "Access Denied.")
        return redirect('home-page')
    context = context_data(request)
    if pk:
        budget = get_object_or_404(models.Budget, pk=pk)
        form = forms.BudgetForm(instance=budget)
        context['page_title'] = "Edit Budget Allocation"
    else:
        budget = None
        form = forms.BudgetForm()
        context['page_title'] = "New Budget Allocation"
    
    context['form'] = form
    context['budget'] = budget
    return render(request, 'manage_budget.html', context)

@login_required
def save_budget(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        id = request.POST.get('id')
        if id:
            budget = get_object_or_404(models.Budget, id=id)
            form = forms.BudgetForm(request.POST, instance=budget)
        else:
            form = forms.BudgetForm(request.POST)
        
        if form.is_valid():
            form.save()
            resp['status'] = 'success'
            messages.success(request, "Budget saved successfully.")
        else:
            resp['msg'] = form.errors.as_text()
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def expenditure_dashboard(request):
    if not request.user.is_superuser:
        messages.error(request, "Access Denied.")
        return redirect('home-page')
    context = context_data(request)
    context['page_title'] = "Financial Governance Dashboard"
    context['budgets'] = models.Budget.objects.all()
    context['recent_expenditures'] = models.Expenditure.objects.all().order_by('-date_paid')[:10]
    
    # Simple aggregation for chart (labels and data)
    dept_names = []
    spent_data = []
    alloc_data = []
    
    for b in context['budgets']:
        dept_names.append(f"{b.department.name} ({b.fiscal_year})")
        spent_data.append(float(b.spent_amount))
        alloc_data.append(float(b.total_allocation))
        
    context['chart_labels'] = json.dumps(dept_names)
    context['chart_spent'] = json.dumps(spent_data)
    context['chart_alloc'] = json.dumps(alloc_data)
    
    return render(request, 'expenditure_dashboard.html', context)

@login_required
def save_expenditure(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        form = forms.ExpenditureForm(request.POST, request.FILES)
        if form.is_valid():
            exp = form.save()
            # Linkage: Update budget spent_amount
            if exp.requisition.budget_line:
                budget = exp.requisition.budget_line
                budget.spent_amount += exp.amount
                budget.save()
            
            # Update requisition status to Fulfilled
            req = exp.requisition
            req.status = 'Fulfilled'
            req.save()
            
            resp['status'] = 'success'
            messages.success(request, "Expenditure recorded and budget updated.")
        else:
            resp['msg'] = form.errors.as_text()
    return HttpResponse(json.dumps(resp), content_type="application/json")
@login_required
def manage_expenditure(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    req_id = request.GET.get('req_id')
    requisition = get_object_or_404(models.Requisition, id=req_id)
    
    # Pre-fill amount with estimated total
    form = forms.ExpenditureForm(initial={'requisition': requisition, 'amount': requisition.total_amount})
    
    context = {
        'form': form,
        'requisition': requisition
    }
    return render(request, 'manage_expenditure.html', context)

# --- Digital Certificate Engine Views ---

@login_required
def certificates(request):
    context = context_data(request)
    context['page_title'] = "Digital Certificate Engine"
    if request.user.is_superuser:
        context['certificates'] = models.DigitalCertificate.objects.all()
    else:
        context['certificates'] = models.DigitalCertificate.objects.filter(issuer=request.user)
    return render(request, 'certificates.html', context)

@login_required
def manage_certificate(request, pk=None):
    context = context_data(request)
    if pk:
        cert = get_object_or_404(models.DigitalCertificate, pk=pk)
        form = forms.SaveDigitalCertificate(instance=cert)
    else:
        form = forms.SaveDigitalCertificate()
    context['form'] = form
    context['pk'] = pk
    return render(request, 'manage_certificate.html', context)

@login_required
def save_certificate(request):
    if request.method == 'POST':
        pk = request.POST.get('id')
        if pk:
            cert = get_object_or_404(models.DigitalCertificate, pk=pk)
            form = forms.SaveDigitalCertificate(request.POST, instance=cert)
        else:
            form = forms.SaveDigitalCertificate(request.POST)
            
        if form.is_valid():
            cert = form.save(commit=False)
            if not pk:
                cert.issuer = request.user
                # Generate unique verification code
                raw_str = f"{cert.certificate_type}-{cert.recipient_name}-{time.time()}"
                cert.verification_code = hashlib.sha256(raw_str.encode()).hexdigest()[:16].upper()
            cert.save()
            return JsonResponse({'status': 'success', 'msg': 'Certificate generated successfully', 'code': cert.verification_code})
        else:
            errors = ""
            for field in form:
                for error in field.errors:
                    errors += f"[{field.label}] {error} "
            return JsonResponse({'status': 'failed', 'msg': errors if errors else 'Invalid data'})
    return JsonResponse({'status': 'failed', 'msg': 'Invalid request'})

@login_required
def view_certificate(request, pk):
    context = context_data(request)
    cert = get_object_or_404(models.DigitalCertificate, pk=pk)
    context['cert'] = cert
    context['page_title'] = f"Certificate: {cert.verification_code}"
    return render(request, 'certificate_template.html', context)

def verify_certificate_public(request):
    context = context_data(request)
    context['page_title'] = "Verify Document Authenticity"
    code = request.GET.get('code', '').strip()
    if code:
        cert = models.DigitalCertificate.objects.filter(verification_code=code).first()
        context['cert'] = cert
        context['searched'] = True
    return render(request, 'verify_certificate.html', context)

# --- Notice Board Views ---

@login_required
def notice_board(request):
    context = context_data(request)
    context['page_title'] = "Official Notice Board"
    
    # Filter active and non-expired announcements
    now = timezone.now()
    announcements = models.Announcement.objects.filter(is_active=True).filter(
        Q(expiry_date__gt=now) | Q(expiry_date__isnull=True)
    )
    
    # Filter by user department if applicable
    if not request.user.is_superuser:
        user_dept = None
        try:
            # Check if user has a profile or is staff
            user_dept = request.user.borrower_profile.department
        except:
            pass
        
        if user_dept:
            announcements = announcements.filter(Q(department=user_dept) | Q(department__isnull=True))
        else:
            announcements = announcements.filter(department__isnull=True)
            
    context['announcements'] = announcements
    return render(request, 'notice_board.html', context)

@login_required
def manage_announcement(request, pk=None):
    if not request.user.is_superuser:
        return HttpResponseForbidden()
    
    context = context_data(request)
    if pk:
        ann = get_object_or_404(models.Announcement, pk=pk)
        form = forms.SaveAnnouncement(instance=ann)
    else:
        form = forms.SaveAnnouncement()
    context['form'] = form
    context['pk'] = pk
    return render(request, 'manage_announcement.html', context)

@login_required
def save_announcement(request):
    if not request.user.is_superuser:
        return JsonResponse({'status': 'failed', 'msg': 'Permission denied'})
        
    if request.method == 'POST':
        pk = request.POST.get('id')
        if pk:
            ann = get_object_or_404(models.Announcement, pk=pk)
            form = forms.SaveAnnouncement(request.POST, instance=ann)
        else:
            form = forms.SaveAnnouncement(request.POST)
            
        if form.is_valid():
            ann = form.save(commit=False)
            if not pk:
                ann.author = request.user
            ann.save()
            return JsonResponse({'status': 'success', 'msg': 'Announcement posted successfully'})
        else:
            errors = ""
            for field in form:
                for error in field.errors:
                    errors += f"[{field.label}] {error} "
            return JsonResponse({'status': 'failed', 'msg': errors if errors else 'Invalid data'})
    return JsonResponse({'status': 'failed', 'msg': 'Invalid request'})

# --- Organizational Digital Twin Views ---

@login_required
def digital_twin(request):
    context = context_data(request)
    context['page_title'] = "Organizational Digital Twin (Ops Center)"
    context['departments'] = models.Department.objects.all()
    # Calculate Floating Files (Issued but borrower has no department)
    floating_count = models.Borrow.objects.filter(
        status='0',
        borrower__department__isnull=True
    ).count()

    context['floating_files'] = floating_count
    return render(request, 'digital_twin.html', context)

def get_digital_twin_updates(request):
    """API for real-time visualization data"""
    # 1. Department Nodes Data
    departments = models.Department.objects.all()
    nodes = []
    
    # Threshold for congestion (e.g., 20+ active files)
    CONGESTION_THRESHOLD = 20
    
    for dept in departments:
        # Count current files in this department (or borrowed by someone in this department)
        file_count = models.File.objects.filter(
            Q(current_department=dept) | Q(file_doc_id_fk__borrower__department=dept, file_doc_id_fk__status='0'),
            delete_flag=0
        ).distinct().count()
        
        # Count overdue/slow files (> 48h since last move)
        overdue_limit = timezone.now() - timedelta(hours=48)
        slow_files = models.File.objects.filter(
            Q(current_department=dept) | Q(file_doc_id_fk__borrower__department=dept, file_doc_id_fk__status='0'),
            last_moved_at__lt=overdue_limit,
            delete_flag=0
        ).distinct().count()
        
        is_congested = file_count > CONGESTION_THRESHOLD
        is_slow = slow_files > (file_count * 0.2) and file_count > 0
        
        nodes.append({
            'id': dept.id,
            'name': dept.name,
            'file_count': file_count,
            'efficiency': dept.efficiency_score,
            'slow_files': slow_files,
            'is_congested': is_congested,
            'is_slow': is_slow
        })
        
    # 2. Real-time Flow Data (Last 5 minutes of movement)
    recent_limit = timezone.now() - timedelta(minutes=5)
    recent_logs = models.CustodyLog.objects.filter(
        timestamp__gt=recent_limit
    ).select_related('from_department', 'to_department')
    
    flows = []
    for log in recent_logs:
        flows.append({
            'from_id': log.from_department.id if log.from_department else 'floating',
            'to_id': log.to_department.id if log.to_department else 'floating',
            'action': log.action,
            'timestamp': log.timestamp.strftime('%H:%M:%S')
        })
        
    # 3. Overall Vitals
    vitals = {
        'total_files': models.File.objects.filter(delete_flag=0).count(),
        'total_overdue': models.Borrow.objects.filter(
            Q(status='0', return_date__lt=timezone.now()) |
            Q(status='0', borrowing_date__lt=timezone.now() - timedelta(days=14))
        ).count(),
        'floating_files': models.Borrow.objects.filter(
            status='0',
            borrower__department__isnull=True
        ).count(),
        'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return JsonResponse({
        'nodes': nodes,
        'flows': flows,
        'vitals': vitals,
    })

# --- Smart Scanner Integration Views ---

@csrf_exempt
def scanner_upload_api(request):
    """
    Direct API endpoint for scanners.
    Expects multi-part POST with 'file' and 'scanner_token'.
    """
    if request.method == 'POST':
        scanner_token = request.POST.get('scanner_token')
        uploaded_file = request.FILES.get('file')
        
        if not scanner_token or not uploaded_file:
            return JsonResponse({'status': 'failed', 'msg': 'Missing scanner_token or file'}, status=400)
            
        doc = ScannerService.ingest(uploaded_file, scanner_token)
        if doc:
            # Process in background (simulated)
            ScannerService.process_document(doc.id)
            return JsonResponse({
                'status': 'success', 
                'msg': 'Ingestion successful',
                'doc_id': doc.id,
                'status': 'Processing'
            })
        else:
            return JsonResponse({'status': 'failed', 'msg': 'Invalid scanner token'}, status=401)
            
    return JsonResponse({'status': 'failed', 'msg': 'Only POST allowed'}, status=405)

@login_required
def scanned_docs_list(request):
    context = context_data(request)
    context['page_title'] = "Scanner Ingestion Pipeline"
    
    query = request.GET.get('q')
    if query:
        # Use AI Assistant to parse and execute search
        from registry.services.ai_assistant import AIAssistantService
        ai_result = AIAssistantService.parse_query(query)
        # For simplicity, we filter the current queryset if we want to stay on the same page
        # or we could display the AI results specifically.
        # Let's just filter the ScannedDocument objects if it's a "Scan" entity
        if ai_result['entity'] == 'ScannedDocument':
            # This is a bit redundant since AIAssistant already ran the query,
            # but let's keep it clean for the template.
            context['scanned_docs'] = models.ScannedDocument.objects.filter(Q(extracted_text__icontains=query) | Q(classification__icontains=query)).order_by('-created_at')
        else:
            context['scanned_docs'] = models.ScannedDocument.objects.all().order_by('-created_at')
        context['ai_search_query'] = query
        context['ai_results'] = ai_result['data']
    else:
        context['scanned_docs'] = models.ScannedDocument.objects.all().order_by('-created_at')
        
    return render(request, 'scanned_docs.html', context)

@login_required
def smart_search_docs(request):
    """
    AJAX endpoint for Google-like search
    """
    query = request.GET.get('q', '')
    from registry.services.ai_assistant import AIAssistantService
    results = AIAssistantService.parse_query(query)
    return JsonResponse(results)

@login_required
def process_scan(request, pk):
    doc = get_object_or_404(models.ScannedDocument, pk=pk)
    ScannerService.process_document(doc.id)
    messages.success(request, f"Document {doc.id} processed and classified as {doc.classification}.")
    return redirect('scanned-docs-list')

@login_required
def scanner_devices(request):
    context = context_data(request)
    context['page_title'] = "Managed Scanners"
    context['devices'] = models.ScannerDevice.objects.all().order_by('-date_added')
    return render(request, 'scanner_devices.html', context)

@login_required
def save_scanner_device(request):
    if request.method == 'POST':
        id = request.POST.get('id')
        name = request.POST.get('name')
        location = request.POST.get('location')
        
        if id:
            device = get_object_or_404(models.ScannerDevice, id=id)
            device.name = name
            device.location = location
            device.save()
        else:
            # Generate a new API Key
            import secrets
            api_key = secrets.token_urlsafe(32)
            models.ScannerDevice.objects.create(
                name=name,
                location=location,
                api_key=api_key
            )
        return JsonResponse({'status': 'success', 'msg': 'Scanner device saved'})
    return JsonResponse({'status': 'failed', 'msg': 'Invalid request'})

@login_required
def delete_scanner_device(request, pk):
    device = get_object_or_404(models.ScannerDevice, pk=pk)
    device.delete()
    return JsonResponse({'status': 'success', 'msg': 'Scanner removed'})

# --- RIFTS Document Cloud Views ---

def _soft_delete_cloud_folder(folder):
    folder.is_deleted = True
    folder.deleted_at = timezone.now()
    folder.save()
    for file in folder.files.filter(status__in=['Active', 'Archived']):
        file.status = 'Trash'
        file.save()
    for sub in folder.subfolders.all():
        _soft_delete_cloud_folder(sub)


def _restore_cloud_folder(folder):
    folder.is_deleted = False
    folder.deleted_at = None
    folder.save()
    for file in folder.files.filter(status='Trash'):
        file.status = 'Active'
        file.save()
    for sub in folder.subfolders.all():
        _restore_cloud_folder(sub)


def _zip_cloud_folder(folder):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        def walk_folder(current, path_prefix):
            for cloud_file in current.files.filter(status='Active'):
                latest = cloud_file.latest_version
                if latest and latest.file_content:
                    try:
                        latest.file_content.open('rb')
                        file_bytes = latest.file_content.read()
                        latest.file_content.close()
                        zip_file.writestr(f"{path_prefix}{cloud_file.name}", file_bytes)
                    except Exception:
                        continue
            for subfolder in current.subfolders.filter(is_deleted=False):
                next_prefix = f"{path_prefix}{subfolder.name}/"
                walk_folder(subfolder, next_prefix)
        walk_folder(folder, f"{folder.name}/")
    zip_buffer.seek(0)
    return zip_buffer

@login_required
def cloud_dashboard(request):
    context = context_data(request)
    context['page_title'] = "Institutional Cloud Vault"
    
    # Get top-level folders for the user's department or common folders
    # Retrieve from security profile department
    user_dept = request.user.security_profile.department if hasattr(request.user, 'security_profile') else None
    
    folder_id = request.GET.get('folder')
    show_deleted = request.GET.get('show_deleted') == '1'

    from registry.models import InstitutionalFolderPermission
    can_view_all = InstitutionalFolderPermission.user_can(request.user, 'can_view_all_folders')

    if folder_id:
        current_folder = get_object_or_404(models.CloudFolder, id=folder_id)
        # Verify access permission
        if not request.user.is_superuser and not can_view_all and user_dept != current_folder.department:
            messages.error(request, "You do not have permission to access institutional folders from other departments.")
            return redirect('cloud-dashboard')

        if show_deleted:
            folders = current_folder.subfolders.filter(is_deleted=True)
            files = current_folder.files.filter(status='Trash')
        else:
            folders = current_folder.subfolders.filter(is_deleted=False)
            files = current_folder.files.filter(status='Active')
        context['current_folder'] = current_folder
        context['breadcrumbs'] = [] # Could implement recursive path here
    else:
        if show_deleted:
            if can_view_all or request.user.is_superuser:
                folders = models.CloudFolder.objects.filter(parent=None, is_deleted=True)
            elif user_dept:
                folders = models.CloudFolder.objects.filter(department=user_dept, parent=None, is_deleted=True)
            else:
                folders = models.CloudFolder.objects.filter(parent=None, is_deleted=True)
            files = models.CloudFile.objects.filter(status='Trash', folder__parent=None)
        else:
            if can_view_all or request.user.is_superuser:
                folders = models.CloudFolder.objects.filter(parent=None, is_deleted=False)
            elif user_dept:
                folders = models.CloudFolder.objects.filter(department=user_dept, parent=None, is_deleted=False)
            else:
                folders = models.CloudFolder.objects.filter(parent=None, is_deleted=False)
            files = []
        context['current_folder'] = None

    context['deleted_mode'] = show_deleted
    context['folders'] = folders
    context['files'] = files
    context['departments'] = models.Department.objects.all()
    
    return render(request, 'cloud/dashboard.html', context)

@login_required
def cloud_file_view(request, pk):
    context = context_data(request)
    cloud_file = get_object_or_404(models.CloudFile, pk=pk)

    # Verify access permission
    user_dept = request.user.security_profile.department if hasattr(request.user, 'security_profile') else None
    from registry.models import InstitutionalFolderPermission
    can_view_all = InstitutionalFolderPermission.user_can(request.user, 'can_view_all_folders')
    if not request.user.is_superuser and not can_view_all and user_dept != cloud_file.folder.department:
        messages.error(request, "You do not have permission to access institutional files from other departments.")
        return redirect('cloud-dashboard')

    context['page_title'] = f"Document: {cloud_file.name}"
    context['file'] = cloud_file
    context['versions'] = cloud_file.versions.all().order_by('-version_number')
    context['access_logs'] = cloud_file.access_logs.all().order_by('-timestamp')[:20]
    
    CloudService.log_access(request.user if request.user.is_authenticated else None, cloud_file, 'View', request=request)
    
    return render(request, 'cloud/file_view.html', context)

@login_required
def cloud_upload_version(request, pk=None):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        folder_id = request.POST.get('folder_id')
        commit_message = request.POST.get('commit_message', '')

        if pk:
            # New version of existing file
            cloud_file = get_object_or_404(models.CloudFile, pk=pk)
            CloudService.upload_file(cloud_file.folder, uploaded_file, request.user, commit_message)
            messages.success(request, f"New version of '{cloud_file.name}' uploaded successfully.")
            return redirect('cloud-file-view', pk=cloud_file.pk)
        else:
            # New file in folder
            folder = get_object_or_404(models.CloudFolder, id=folder_id)
            cf = CloudService.upload_file(folder, uploaded_file, request.user, commit_message)
            messages.success(request, f"File '{cf.name}' uploaded to {folder.name}.")
            return redirect('cloud-dashboard')

    return redirect('cloud-dashboard')

@login_required
def cloud_create_doc(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        content = request.POST.get('content', '')
        folder_id = request.POST.get('folder_id')
        commit_message = request.POST.get('commit_message', 'Created new Word document')

        if not name:
            messages.error(request, "Document name is required.")
            return redirect('cloud-dashboard')

        folder = get_object_or_404(models.CloudFolder, id=folder_id)
        cf = CloudService.create_document(folder, name, content, request.user, commit_message)
        messages.success(request, f"Document '{cf.name}' created in {folder.name}.")

    return redirect('cloud-dashboard')

@login_required
def cloud_create_folder(request):
    # ── Permission guard ──────────────────────────────────────────────────────
    from registry.models import InstitutionalFolderPermission
    if not InstitutionalFolderPermission.user_can(request.user, 'can_create_folder'):
        messages.error(
            request,
            "You do not have permission to create institutional folders. "
            "Please contact your administrator."
        )
        return redirect('cloud-dashboard')

    if request.method == 'POST':
        name = request.POST.get('name')
        dept_id = request.POST.get('department_id')
        parent_id = request.POST.get('parent_id')

        department = get_object_or_404(models.Department, id=dept_id)
        parent = models.CloudFolder.objects.filter(id=parent_id).first() if parent_id else None

        CloudService.get_or_create_folder(name, department, parent=parent, user=request.user)
        messages.success(request, f"Folder '{name}' created successfully.")

    return redirect('cloud-dashboard')


@login_required
def cloud_delete_folder(request, pk):
    # ── Permission guard ──────────────────────────────────────────────────────
    from registry.models import InstitutionalFolderPermission
    if not InstitutionalFolderPermission.user_can(request.user, 'can_delete_folder'):
        messages.error(
            request,
            "You do not have permission to delete institutional folders. "
            "Please contact your administrator."
        )
        return redirect('cloud-dashboard')

    if request.method == 'POST':
        folder = get_object_or_404(models.CloudFolder, pk=pk)
        folder_name = folder.name
        _soft_delete_cloud_folder(folder)
        messages.success(request, f"Folder '{folder_name}' and its contents were moved to the Cloud Vault recycle bin.")
    return redirect('cloud-dashboard')

@login_required
def cloud_restore_folder(request, pk):
    if request.method == 'POST':
        folder = get_object_or_404(models.CloudFolder, pk=pk)
        folder_name = folder.name
        _restore_cloud_folder(folder)
        messages.success(request, f"Folder '{folder_name}' has been restored.")
    return redirect(f"{reverse('cloud-dashboard')}?show_deleted=1")

@login_required
def cloud_delete_file(request, pk):
    if request.method == 'POST':
        cloud_file = get_object_or_404(models.CloudFile, pk=pk)
        cloud_file.status = 'Trash'
        cloud_file.save()
        messages.success(request, f"Document '{cloud_file.name}' was moved to the Cloud Vault recycle bin.")
    return redirect('cloud-dashboard')

@login_required
def cloud_restore_file(request, pk):
    if request.method == 'POST':
        cloud_file = get_object_or_404(models.CloudFile, pk=pk)
        cloud_file.status = 'Active'
        cloud_file.save()
        messages.success(request, f"Document '{cloud_file.name}' has been restored.")
    return redirect(f"{reverse('cloud-dashboard')}?show_deleted=1")


@login_required
def cloud_download_folder(request, pk):
    """
    Streams the full contents of a Cloud Vault folder as a ZIP download.
    Requires the 'can_download_folder' institutional permission (or superuser).
    """
    from registry.models import InstitutionalFolderPermission
    if not InstitutionalFolderPermission.user_can(request.user, 'can_download_folder'):
        messages.error(
            request,
            "You do not have permission to download institutional folder contents. "
            "Please contact your administrator."
        )
        return redirect('cloud-dashboard')

    folder = get_object_or_404(models.CloudFolder, pk=pk, is_deleted=False)

    # Verify access permission
    user_dept = request.user.security_profile.department if hasattr(request.user, 'security_profile') else None
    can_view_all = InstitutionalFolderPermission.user_can(request.user, 'can_view_all_folders')
    if not request.user.is_superuser and not can_view_all and user_dept != folder.department:
        messages.error(request, "You do not have permission to access institutional folders from other departments.")
        return redirect('cloud-dashboard')

    # Log the download access
    import zipfile as _zipfile
    import io as _io
    # Re-use the existing _zip_cloud_folder helper
    zip_buffer = _zip_cloud_folder(folder)

    safe_name = folder.name.replace(' ', '_').replace('/', '-')
    response = HttpResponse(zip_buffer.read(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{safe_name}_bundle.zip"'
    return response


@login_required
def cloud_generate_share(request, pk):
    """Generate a secure, time-limited sharing token for a CloudFile and return the link as JSON."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed.'}, status=405)

    cloud_file = get_object_or_404(models.CloudFile, pk=pk)

    expiry_map = {'24h': 1, '7d': 7, '30d': 30}
    expiry_key = request.POST.get('expiry', '7d')
    expiry_days = expiry_map.get(expiry_key, 7)

    from registry.services.cloud import CloudService
    from django.conf import settings as dj_settings

    share = CloudService.create_share(
        cloud_file=cloud_file,
        shared_by=request.user,
        expiry_days=expiry_days,
        can_download=False,
        can_edit=False,
    )

    base_url = getattr(dj_settings, 'RIFTSX_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
    share_url = f"{base_url}/registry/cloud/s/{share.access_token}/"

    return JsonResponse({
        'status': 'ok',
        'url': share_url,
        'expires_at': share.expiry_date.strftime('%d %B %Y, %H:%M'),
        'token': share.access_token,
    })


def cloud_share_access(request, token):

    share = get_object_or_404(models.CloudShare, access_token=token)

    
    if not share.is_valid():
        return render(request, 'cloud/share_error.html', {'error': 'This sharing link has expired or been revoked.'})
        
    context = {
        'share': share,
        'file': share.cloud_file,
        'latest_version': share.cloud_file.latest_version,
        'system_name': 'RIFTS-X Secure Gateway'
    }
    
    # Log the access even for public shares if possible
    CloudService.log_access(request.user if request.user.is_authenticated else None, share.cloud_file, 'View', request=request)
    
    return render(request, 'cloud/share_view.html', context)

@login_required
@login_required
def file_digital_twin(request, pk):
    file_obj = get_object_or_404(models.File, pk=pk)
    
    # Audit trail logging
    log_document_action(
        request.user, 'View',
        file_doc=file_obj,
        details=f"Digital Twin viewed for '{file_obj.title}' ({file_obj.ref_num}).",
        request=request
    )
    
    context = context_data(request)
    context['page_title'] = f"Digital Twin: {file_obj.ref_num}"
    context['file_doc'] = file_obj
    context['logs'] = models.CustodyLog.objects.filter(file_doc=file_obj).order_by('-timestamp')
    context['approvals'] = file_obj.approvals.all()
    context['scans'] = file_obj.scanned_documents.all()
    
    # Calculate Metrics
    context['sla_status'] = SLAManager.check_file_sla(file_obj)
    context['risk_score'] = RiskEngine.update_file_risk(file_obj)
    
    # Digital Twin Resilience
    from registry.services.twin import DigitalTwinService
    context['resilience_score'] = DigitalTwinService.get_twin_resilience(file_obj)
    
    # Link to Cloud Folder if exists
    from registry.services.cloud import CloudService
    context['cloud_folder'] = models.CloudFolder.objects.filter(name=file_obj.ref_num).first()
    
    return render(request, 'file_digital_twin.html', context)

@login_required
def sync_digital_twin(request, pk):
    file_obj = get_object_or_404(models.File, pk=pk)
    from registry.services.twin import DigitalTwinService
    success = DigitalTwinService.instantiate_twin(file_obj, user=request.user)
    if success:
        messages.success(request, f"Digital Twin for {file_obj.ref_num} synchronized successfully.")
    else:
        messages.error(request, f"Failed to synchronize Digital Twin for {file_obj.ref_num}.")
    return redirect('file-digital-twin', pk=pk)

@login_required
def mark_file_lost(request, pk):
    file_obj = get_object_or_404(models.File, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('reason', 'Not specified.')
        CustodyService.mark_lost(file_obj, request.user, reason)
        messages.warning(request, f"File {file_obj.ref_num} has been marked as LOST. Digital trail remains active.")
        return redirect('file-digital-twin', pk=pk)
    return render(request, 'file_mark_lost.html', {'file_doc': file_obj})

@login_required
def mark_file_found(request, pk):
    file_obj = get_object_or_404(models.File, pk=pk)
    if request.method == 'POST':
        location_id = request.POST.get('location_id')
        reason = request.POST.get('reason', 'Recovery.')
        location = get_object_or_404(models.FileLocation, id=location_id)
        CustodyService.mark_found(file_obj, request.user, location, reason)
        messages.success(request, f"File {file_obj.ref_num} has been RECOVERED and placed at {location}.")
        return redirect('file-digital-twin', pk=pk)
    locations = models.FileLocation.objects.all()
    return render(request, 'file_mark_found.html', {'file_doc': file_obj, 'locations': locations})

@login_required
def mobile_capture(request):
    """
    Renders the mobile-optimized capture interface.
    """
    context = context_data(request)
    context['page_title'] = "Mobile Field Capture"
    # Fetch recent sync records for the user
    context['sync_records'] = models.OfflineSyncQueue.objects.filter(user=request.user)[:10]
    return render(request, 'mobile_capture.html', context)

@login_required
@csrf_exempt # In a real system, use token-based auth for mobile
def upload_sync_record(request):
    """
    Endpoint for mobile devices to upload captured documents.
    """
    if request.method == 'POST':
        try:
            import uuid
            local_id = request.POST.get('local_id', uuid.uuid4())
            ref_num = request.POST.get('ref_num')
            notes = request.POST.get('notes', "")
            attachment = request.FILES.get('attachment')

            if not ref_num or not attachment:
                return JsonResponse({'status': 'error', 'message': 'Missing data or attachment'}, status=400)

            record = models.OfflineSyncQueue.objects.create(
                user=request.user,
                local_id=local_id,
                ref_num=ref_num,
                data={'notes': notes},
                attachment=attachment
            )
            
            return JsonResponse({
                'status': 'success', 
                'message': 'Record uploaded to queue',
                'id': record.id
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

@login_required
def trigger_sync(request):
    """
    Manual trigger for processing the sync queue.
    """
    from registry.services.sync import SyncService
    results = SyncService.process_queue()
    messages.info(request, f"Sync complete: {results['synced']} synced, {results['conflicts']} conflicts, {results['failed']} failed.")
    return redirect('mobile-capture')

@login_required
def project_governance_list(request):
    """
    Scopes project visibility by role:
    - MD / Admin / Executive Viewer / Auditor: all projects (org-wide)
    - HOD: all projects in their department only
    - Project Leader: projects they own or are PM on a phase
    - Team Member: only projects where they have assigned tasks
    """
    context = context_data(request)
    context['page_title'] = "Institutional Project Governance"

    role = PermissionService.get_user_role(request.user)
    context['gov_role'] = role

    if role in {'Portfolio Admin', 'Board of Executives', 'Executive Viewer', 'Auditor', 'Supervisor'}:
        # Org-wide view — exclude soft-deleted projects
        projects = models.Project.objects.filter(is_deleted=False).order_by('-created_at')

    elif role in ('HODs', 'Project Management Team'):
        # Department-scoped
        dept = None
        if hasattr(request.user, 'security_profile'):
            dept = request.user.security_profile.department
        projects = (
            models.Project.objects.filter(department=dept, is_deleted=False).order_by('-created_at')
            if dept else models.Project.objects.none()
        )

    elif role == 'Project Leader':
        # Projects they own or are assigned as PM on a phase
        from django.db.models import Q
        projects = models.Project.objects.filter(
            (Q(owner=request.user) | Q(phases__pm=request.user)) & Q(is_deleted=False)
        ).distinct().order_by('-created_at')

        # DISCOVER: Projects in their department that they are NOT yet in
        dept = None
        if hasattr(request.user, 'security_profile'):
            dept = request.user.security_profile.department
        
        if dept:
            context['available_projects'] = models.Project.objects.filter(
                department=dept, is_deleted=False
            ).exclude(id__in=projects.values_list('id', flat=True)).order_by('-created_at')

    # DISCOVER: All projects in the system that the user is NOT yet part of (nor owner/PM)
    my_member_ids = list(models.ProjectMember.objects.filter(user=request.user).values_list('project_id', flat=True))
    if role == 'Project Leader':
        my_managed_ids = list(models.Project.objects.filter(
            Q(owner=request.user) | Q(phases__pm=request.user),
            is_deleted=False
        ).values_list('id', flat=True))
        all_my_project_ids = list(set(my_member_ids) | set(my_managed_ids))
    else:
        all_my_project_ids = my_member_ids
        # Restore projects context for Team Members
        projects = models.Project.objects.filter(id__in=my_member_ids, is_deleted=False).order_by('-created_at')

    context['projects'] = projects
    context['available_projects'] = models.Project.objects.filter(
        is_deleted=False
    ).exclude(id__in=all_my_project_ids).order_by('-created_at')[:20]
    
    context['my_tasks'] = models.ProjectTask.objects.filter(
        owner=request.user,
        is_deleted=False,
        phase__project__is_deleted=False
    ).select_related('phase__project', 'sprint').order_by('due_date')

    return render(request, 'governance/project_list.html', context)

@login_required
def project_detail(request, pk):
    project = get_object_or_404(models.Project, pk=pk, is_deleted=False)
    context = context_data(request)
    context['page_title'] = f"Governance: {project.name}"
    context['project'] = project
    context['phases'] = project.phases.all().order_by('sequence')
    context['logs'] = project.logs.all().order_by('-timestamp')

    # ── Role resolution ──
    role = PermissionService.get_user_role(request.user)
    context['gov_role'] = role
    
    # ── Membership logic ──
    context['is_approved_member'] = project.project_memberships.filter(user=request.user, is_approved=True).exists()
    all_memberships = project.project_memberships.all().select_related('user').order_by('is_approved', '-joined_at')
    context['project_memberships'] = all_memberships
    context['has_pending_request'] = project.project_memberships.filter(user=request.user, is_approved=False).exists()
    context['pending_members_count'] = project.project_memberships.filter(is_approved=False).count()

    # ── Tasks scoped by role ──
    all_tasks = models.ProjectTask.objects.filter(phase__project=project).select_related('owner', 'sprint', 'phase')
    context['all_tasks'] = all_tasks.order_by('due_date')
    context['show_all_tasks'] = True
    context['my_tasks'] = all_tasks.filter(owner=request.user).order_by('due_date')

    # ── Team Workload (PM + above) ──
    if role in {'Portfolio Admin', 'Project Leader', 'MD', 'Board of Executives', 'HODs', 'Project Management Team'}:
        from django.db.models import Count
        context['team_workload'] = (
            all_tasks
            .values('owner__username')
            .annotate(total=Count('id'))
            .order_by('-total')[:8]
        )
        context['overdue_tasks'] = all_tasks.filter(
            due_date__lt=timezone.now().date(),
            status__in=['Pending', 'In Progress']
        ).count()

    # ── Phase-level permission flags (for PM approval bars) ──
    context['can_approve_phase_any'] = role in {'Portfolio Admin', 'Project Leader'}

    from .services.governance import GovernanceService
    health = GovernanceService.update_project_health(project)
    context['health'] = health

    # SVG gauge
    pct = project.progress_percentage
    context['progress_offset'] = round(427 * (1 - pct / 100))

    # Project/Phase Collaboration
    context['project_comments'] = project.comments.filter(parent=None).prefetch_related(
        'replies', 'author', 'attachments', 'mentioned_users'
    )
    context['action_items'] = project.comments.filter(is_action_item=True, is_resolved=False)

    from .services.intelligence import ProjectIntelligenceService
    context['ai_prediction'] = ProjectIntelligenceService.predict_project_delay(project)

    # ── Governance Level Config (for conditional rendering and PL settings panel) ──
    context['is_project_leader'] = (role == 'Project Leader' or request.user == project.owner or request.user.is_superuser)

    return render(request, 'governance/project_detail.html', context)

@login_required
def delete_project(request, pk):
    project = get_object_or_404(models.Project, pk=pk)
    
    # Permission Check: ONLY Project Leaders or superusers may delete
    user_role = PermissionService.get_user_role(request.user)
    if user_role != 'Project Leader' and not request.user.is_superuser:
        messages.error(request, "Only Project Leaders can delete projects.")
        return redirect('project-detail', pk=pk)

    if request.method == 'POST':
        project.is_deleted = True
        project.deleted_at = timezone.now()
        project.save()
        
        # Cascading Soft Delete
        project.phases.update(is_deleted=True, deleted_at=timezone.now())
        models.ProjectTask.objects.filter(phase__project=project).update(is_deleted=True, deleted_at=timezone.now())
        
        # Log the deletion
        models.ProjectLog.objects.create(
            project=project,
            user=request.user,
            message="Project and all related tasks/phases moved to Recycle Bin."
        )
        
        messages.success(request, f"Project '{project.name}' has been moved to the Recycle Bin.")
        return redirect('project-list')

    return render(request, 'governance/confirm_delete.html', {'project': project})

@login_required
def restore_project(request, pk):
    project = get_object_or_404(models.Project, pk=pk)
    
    # ONLY Project Leaders or superusers may restore
    user_role = PermissionService.get_user_role(request.user)
    if user_role != 'Project Leader' and not request.user.is_superuser:
        messages.error(request, "Only Project Leaders can restore projects.")
        return redirect('recycle-bin')

    project.is_deleted = False
    project.deleted_at = None
    project.save()
    
    models.ProjectLog.objects.create(
        project=project,
        user=request.user,
        message="Project restored from Recycle Bin."
    )
    
    messages.success(request, f"Project '{project.name}' has been restored.")
    return redirect('project-detail', pk=pk)

@login_required
def recycle_bin(request):
    context = context_data(request)
    user_role = PermissionService.get_user_role(request.user)
    
    # ONLY Project Leaders (and superusers) can view the Recycle Bin
    if user_role != 'Project Leader' and not request.user.is_superuser:
        messages.error(request, "Access Denied: Only Project Leaders can view the Recycle Bin.")
        return redirect('project-list')

    # PLs only see their own deleted projects
    if request.user.is_superuser:
        projects = models.Project.objects.filter(is_deleted=True)
    else:
        projects = models.Project.objects.filter(owner=request.user, is_deleted=True)

    context['deleted_projects'] = projects.order_by('-deleted_at')
    context['page_title'] = "Governance: Recycle Bin"
    
    return render(request, 'governance/recycle_bin.html', context)

@csrf_exempt
@login_required
def save_push_subscription(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        endpoint = data.get('endpoint')
        keys = data.get('keys')
        
        if not endpoint:
            return JsonResponse({'status': 'error', 'message': 'Missing endpoint'}, status=400)
            
        models.PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                'user': request.user,
                'p256dh': keys.get('p256dh'),
                'auth': keys.get('auth')
            }
        )
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

@login_required
def test_push_notification(request):
    # This is a placeholder for actual push triggering
    # In a real app, you'd use a library like `pywebpush`
    messages.info(request, "Push notification test triggered (backend logic pending library installation).")
    return redirect('project-list')

@login_required
def create_project(request):
    user_role = PermissionService.get_user_role(request.user)
    if user_role != 'Project Leader' and not request.user.is_superuser:
        messages.error(request, "Access Denied: You do not have permission to initiate new projects.")
        return redirect('project-list')
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        
        from .services.governance import GovernanceService
        dept = None
        if hasattr(request.user, 'borrower_profile'):
            dept = request.user.borrower_profile.department
        if not dept:
            dept = models.Department.objects.first()
            
        budget_raw = request.POST.get('budget', '0')
        budget = float(budget_raw) if budget_raw.strip() else 0.0
        
        try:
            with transaction.atomic():
                project = models.Project.objects.create(
                    name=name,
                    description=description,
                    department=dept,
                    owner=request.user,
                    budget=budget,
                    start_date=request.POST.get('start_date') or None,
                    end_date=request.POST.get('end_date') or None,
                    external_link=request.POST.get('external_link') or None,
                    status='Active',
                    requires_pmt=request.POST.get('requires_pmt') == 'on',
                    requires_hods=request.POST.get('requires_hods') == 'on',
                    requires_board=request.POST.get('requires_board') == 'on',
                )

                # Initialize phases (Check for custom phases from form)
                custom_phases_raw = request.POST.get('phases')
                if custom_phases_raw:
                    phase_names = [p.strip() for p in custom_phases_raw.split(',') if p.strip()]
                    if phase_names:
                        for idx, p_name in enumerate(phase_names):
                            models.ProjectPhase.objects.create(
                                project=project,
                                name=p_name,
                                sequence=idx + 1,
                                status='Active' if idx == 0 else 'Pending',
                                pm=request.user,
                                requires_approval=True
                            )
                    else:
                        GovernanceService.initialize_stage_gates(project)
                else:
                    GovernanceService.initialize_stage_gates(project)

                # PM is automatically an approved member
                models.ProjectMember.objects.create(
                    project=project, user=request.user, is_approved=True,
                    approved_by=request.user, approved_at=timezone.now()
                )

                messages.success(request, f"Project '{name}' successfully initialized with Stage-Gate system.")
                return redirect('project-detail', pk=project.pk)
        except Exception as e:
            messages.error(request, f"Failed to initialize project: {str(e)}")
        
    context = context_data(request)
    context['page_title'] = "Initialize Records Intelligence Project"
    return render(request, 'governance/create_project.html', context)

@login_required
def advance_phase_view(request, pk):
    """
    Level 1: Phase Submission Gate.
    Team Member (or PM on behalf) triggers formal review. 
    Checks task completion and forwards to PL.
    """
    phase = get_object_or_404(models.ProjectPhase, pk=pk)
    if request.method == 'POST':
        from .services.governance import GovernanceService
        comments = request.POST.get('comments', '')
        signature_data = request.POST.get('signature_data', None)
        
        # 1. First ensure system criteria (100% tasks) are met
        ready, msg = GovernanceService.advance_phase(phase, request.user)
        if not ready and "already in" not in msg:
            messages.error(request, msg)
            return redirect('project-detail', pk=phase.project.pk)
            
        # 2. Progress to PL Gate
        success, msg = GovernanceService.team_member_submit_to_pl(phase, request.user, comments, signature_data)
        if success:
            messages.success(request, msg)
        else:
            messages.error(request, msg)
            
    return redirect('project-detail', pk=phase.project.pk)

@login_required
@login_required
def approve_phase(request, pk, status):
    """
    Board-level final approval (Level 5).
    Expects comments and electronic signature data.
    """
    phase = get_object_or_404(models.ProjectPhase, pk=pk)
    
    if request.method == 'POST':
        from .services.governance import GovernanceService
        comments = request.POST.get('comments', '')
        signature_data = request.POST.get('signature_data', None)
        success, msg = GovernanceService.approve_phase(phase, request.user, status, notes=comments, signature_data=signature_data)
        
        if success:
            messages.success(request, msg)
        else:
            messages.error(request, msg)
            
    return redirect('project-detail', pk=phase.project.pk)

@login_required
@login_required
def pm_consolidate_phase(request, pk):
    """
    Level 2: Project Leader Gate Review.
    Consolidates task deliverables into a ZIP and forwards to PMT.
    """
    phase = get_object_or_404(models.ProjectPhase, pk=pk)
    if request.method == 'POST':
        comments = request.POST.get('comments', '')
        signature_data = request.POST.get('signature_data', None)
        consolidated_file = request.FILES.get('consolidated_file')
        from .services.governance import GovernanceService

        # 1. Performance Consolidation of task deliverables
        try:
            from .models import SubCategory, File
            from django.core.files.base import ContentFile
            import secrets

            subcat = SubCategory.objects.filter(name__icontains='Governance').first() or SubCategory.objects.first()
            
            if consolidated_file:
                # User uploaded a manual consolidation document
                file_doc = File.objects.create(
                    sub_category=subcat,
                    ref_num=f"ZRP-CONS-{phase.project.id}-{secrets.token_hex(2).upper()}",
                    title=f"Manual Consolidated Deliverable - {phase.name}",
                    current_department=phase.project.department,
                    status='1'
                )
                file_doc.file_attachment.save(consolidated_file.name, consolidated_file)
                phase.required_documents.add(file_doc)
            else:
                # Fallback to Auto-Consolidation (Zip all task deliverables)
                deliverable_tasks = phase.tasks.filter(attachments__isnull=False).distinct()
                if deliverable_tasks.exists() or phase.required_documents.exists():
                    import io, zipfile
                    buffer = io.BytesIO()
                    with zipfile.ZipFile(buffer, 'w') as zip_file:
                        for task in deliverable_tasks:
                            owner_name = task.owner.username if task.owner else "Unknown"
                            for attach in task.attachments.all():
                                if attach.file:
                                    try:
                                        # Filename: [OwnerName]/[OwnerName]_[Filename]
                                        zip_file.writestr(f"{owner_name}/{owner_name}_{attach.filename}", attach.file.read())
                                    except: pass
                                elif attach.external_link:
                                    # We could also add a link to a report inside the zip
                                    pass
                    
                    buffer.seek(0)
                    zip_filename = f"Phase_{phase.name.replace(' ', '_')}_Consolidated_Deliverables.zip"
                    
                    # Check if a consolidation already exists to avoid duplicates
                    existing = phase.required_documents.filter(title__icontains='Consolidated Deliverables').first()
                    if existing:
                        existing.file_attachment.save(zip_filename, ContentFile(buffer.read()))
                    else:
                        file_doc = File.objects.create(
                            sub_category=subcat,
                            ref_num=f"ZRP-CONS-{phase.project.id}-{secrets.token_hex(2).upper()}",
                            title=f"Auto-Consolidated Deliverables - {phase.name}",
                            current_department=phase.project.department,
                            status='1'
                        )
                        file_doc.file_attachment.save(zip_filename, ContentFile(buffer.read()))
                        phase.required_documents.add(file_doc)
        except Exception as e:
            messages.warning(request, f"Review continued, but deliverable consolidation encountered an issue: {str(e)}")

        # 2. Record PL approval and advance status
        success, msg = GovernanceService.pl_submit_to_pmt(phase, request.user, comments, signature_data)
        if success:
            messages.success(request, msg)
        else:
            messages.error(request, msg)

    return redirect('project-detail', pk=phase.project.pk)

@login_required
def pm_auto_consolidate_phase(request, pk):
    """
    PM tool to automatically gather all task deliverables and zip them into a phase document.
    """
    phase = get_object_or_404(models.ProjectPhase, pk=pk)
    
    # Permission Check: PM or above
    if not PermissionService.is_pm_or_above(request.user):
        messages.error(request, "Permission denied: Only the Project Manager can auto-consolidate deliverables.")
        return redirect('project-detail', pk=phase.project.pk)

    # Gather ALL tasks that have attachments (Team Deliverables)
    deliverable_tasks = phase.tasks.filter(attachments__isnull=False).distinct()
    
    if not deliverable_tasks.exists() and not phase.required_documents.exists():
        messages.warning(request, "No deliverables (task attachments or phase documents) found to consolidate.")
        return redirect('project-detail', pk=phase.project.pk)

    try:
        # Create the zip file in memory
        buffer = io.BytesIO()
        external_links_report = []
        
        with zipfile.ZipFile(buffer, 'w') as zip_file:
            # 1. Gather Task Attachments
            for task in deliverable_tasks:
                owner_name = task.owner.username if task.owner else "Unknown"
                for attach in task.attachments.all():
                    if attach.file:
                        # Path structure: [OwnerName]_Task_[ID]/File
                        file_path = f"{owner_name}_Task_{task.id}/{attach.filename}"
                        try:
                            zip_file.writestr(file_path, attach.file.read())
                        except Exception as e:
                            logger.error(f"Failed to add {attach.filename} to consolidation zip: {e}")
                    elif attach.external_link:
                        external_links_report.append(f"Task: {task.title} (By: {owner_name})\nLink: {attach.external_link}\n---")

            # 2. Gather Phase Documents
            for doc in phase.required_documents.all():
                if doc.file_attachment:
                    file_path = f"Phase_Evidence/{doc.file_attachment.name.split('/')[-1]}"
                    try:
                        zip_file.writestr(file_path, doc.file_attachment.read())
                    except Exception as e:
                        logger.error(f"Failed to add phase document {doc.title} to zip: {e}")
                elif doc.external_link:
                    external_links_report.append(f"Phase Document: {doc.title}\nLink: {doc.external_link}\n---")

            # 3. Add External Links Report if any
            if external_links_report:
                report_content = "EXTERNAL LINKS DELIVERABLES\n" + "="*30 + "\n\n"
                report_content += "\n".join(external_links_report)
                zip_file.writestr("deliverable_links.txt", report_content)

        buffer.seek(0)
        zip_filename = f"Phase_{phase.name.replace(' ', '_')}_Consolidated_Deliverables.zip"
        
        from .models import SubCategory
        subcat = SubCategory.objects.filter(name__icontains='Governance').first() or SubCategory.objects.first()
        
        # Create the File record
        file_doc = models.File.objects.create(
            sub_category=subcat,
            ref_num=f"ZRP-CONS-{phase.project.id}-{secrets.token_hex(3).upper()}",
            title=f"Consolidated Deliverables - {phase.name}",
            current_department=phase.project.department,
            status='1'
        )
        file_doc.file_attachment.save(zip_filename, ContentFile(buffer.read()))
        
        # Link to phase as a required/verified deliverable
        phase.required_documents.add(file_doc)
        
        # Audit Log
        models.ProjectLog.objects.create(
            project=phase.project,
            user=request.user,
            message=f"PM Auto-Consolidation: Gathered all task deliverables into {zip_filename} (Ref: {file_doc.ref_num})"
        )
        
        messages.success(request, f"Successfully consolidated deliverables into '{zip_filename}'.")
    except Exception as e:
        messages.error(request, f"Consolidation failed: {str(e)}")

    return redirect('project-detail', pk=phase.project.pk)

@login_required
def pmt_verify_phase(request, pk):
    """PMT verifies consolidation and forwards to HODs."""
    phase = get_object_or_404(models.ProjectPhase, pk=pk)
    if request.method == 'POST':
        comments = request.POST.get('comments', '')
        signature_data = request.POST.get('signature_data', None)
        from .services.governance import GovernanceService
        success, msg = GovernanceService.pmt_submit_to_hods(phase, request.user, comments, signature_data)
        if success:
            messages.success(request, msg)
        else:
            messages.error(request, msg)
    return redirect('project-detail', pk=phase.project.pk)

@login_required
def hods_verify_phase(request, pk):
    """HODs verifies consolidation and forwards to Board."""
    phase = get_object_or_404(models.ProjectPhase, pk=pk)
    if request.method == 'POST':
        comments = request.POST.get('comments', '')
        signature_data = request.POST.get('signature_data', None)
        from .services.governance import GovernanceService
        success, msg = GovernanceService.hods_submit_to_board(phase, request.user, comments, signature_data)
        if success:
            messages.success(request, msg)
        else:
            messages.error(request, msg)
    return redirect('project-detail', pk=phase.project.pk)

@login_required
def return_phase(request, pk):
    """Higher tier rejects phase and returns to previous tier."""
    phase = get_object_or_404(models.ProjectPhase, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        from .services.governance import GovernanceService
        
        user_role = PermissionService.get_user_role(request.user)
        if user_role == 'Project Management Team':
            success, msg = GovernanceService.pmt_return_to_pl(phase, request.user, reason)
        elif user_role == 'HODs':
            success, msg = GovernanceService.hods_return_to_pmt(phase, request.user, reason)
        elif user_role == 'Board of Executives' or request.user.is_superuser:
            success, msg = GovernanceService.approve_phase(phase, request.user, 'Rejected', reason)
        else:
            success, msg = False, "Insufficient permissions to return this phase."

        if success:
            messages.success(request, msg)
        else:
            messages.error(request, msg)
    return redirect('project-detail', pk=phase.project.pk)

@login_required
def edit_phase_meta(request, pk):
    """Update phase deliverables and completion criteria."""
    phase = get_object_or_404(models.ProjectPhase, pk=pk)
    
    # Permission Check: PM or Staff
    if not PermissionService.is_pm_or_above(request.user):
        messages.error(request, "Permission denied: Only the Project Leader or Senior Executives can modify this metadata.")
        return redirect('project-detail', pk=phase.project.pk)
    
    if request.method == 'POST':
        phase.deliverables = request.POST.get('deliverables', '')
        phase.completion_criteria = request.POST.get('completion_criteria', '')

        # Flexible Quorum Settings — Project Leader specifies how many reviewers are required
        try:
            pmt_req = int(request.POST.get('pmt_required', phase.pmt_required))
            hods_req = int(request.POST.get('hods_required', phase.hods_required))
            board_req = int(request.POST.get('board_required', phase.board_required))
            phase.pmt_required  = max(1, pmt_req)
            phase.hods_required = max(1, hods_req)
            phase.board_required = max(1, board_req)
        except (ValueError, TypeError):
            pass  # Keep existing values if input is invalid

        phase.save()
        messages.success(request, f"Governance metadata for phase '{phase.name}' updated successfully.")
        
    return redirect('project-detail', pk=phase.project.pk)

@login_required
def edit_governance_levels(request, pk):
    """
    Allows the Project Leader to enable/disable PMT, HODs, and Board gates
    for the project. All phases will use the updated routing on their next submission.
    """
    project = get_object_or_404(models.Project, pk=pk, is_deleted=False)
    user_role = PermissionService.get_user_role(request.user)

    if user_role != 'Project Leader' and request.user != project.owner and not request.user.is_superuser:
        messages.error(request, "Only the Project Leader can change governance levels.")
        return redirect('project-detail', pk=pk)

    if request.method == 'POST':
        project.requires_pmt   = request.POST.get('requires_pmt') == 'on'
        project.requires_hods  = request.POST.get('requires_hods') == 'on'
        project.requires_board = request.POST.get('requires_board') == 'on'
        project.save(update_fields=['requires_pmt', 'requires_hods', 'requires_board'])

        active_gates = []
        if project.requires_pmt:   active_gates.append('PMT')
        if project.requires_hods:  active_gates.append('HODs')
        if project.requires_board: active_gates.append('Board')
        gate_summary = ', '.join(active_gates) if active_gates else 'None (PL only)'

        models.ProjectLog.objects.create(
            project=project,
            user=request.user,
            message=f"Governance levels updated by {request.user.username}. Active upper gates: {gate_summary}."
        )
        messages.success(request, f"Governance levels updated. Active upper gates: {gate_summary}.")

    return redirect('project-detail', pk=pk)


@login_required
def executive_governance(request):
    """
    Board/HODs/PMT Dashboard: High-level visibility into all projects and delays.
    """
    from .models import UserSecurity
    user_sec = UserSecurity.objects.filter(user=request.user).first()
    allowed_roles = ['Executive', 'Supervisor', 'Auditor', 'Board of Executives', 'HODs', 'Project Management Team', 'Portfolio Admin', 'Executive Viewer']
    if user_sec and user_sec.role not in allowed_roles and not request.user.is_superuser:
        return HttpResponseForbidden("This dashboard is reserved for Executive Governance.")
        
    context = context_data(request)
    context['page_title'] = "Executive Project Governance"
    projects = models.Project.objects.filter(is_deleted=False)
    
    from .services.governance import GovernanceService
    stats = GovernanceService.calculate_institutional_metrics()
    
    context['projects'] = projects
    context['stats'] = stats
    
    # Strategic Benefits
    benefits = models.Benefit.objects.all()
    context['total_monthly_benefits'] = benefits.aggregate(Sum('monthly_savings'))['monthly_savings__sum'] or 0
    context['total_annual_benefits'] = benefits.aggregate(Sum('annual_projection'))['annual_projection__sum'] or 0
    context['benefits'] = benefits
    
    # Chart Data: Benefits by Department
    dept_benefits = benefits.values('department__name').annotate(total=Sum('annual_projection')).order_by('-total')
    context['benefit_dept_labels'] = json.dumps([d['department__name'] for d in dept_benefits])
    context['benefit_dept_data'] = json.dumps([float(d['total']) for d in dept_benefits])
    
    return render(request, 'governance/executive_dashboard.html', context)

@login_required
def project_visualization_data(request, pk):
    """
    Returns JSON data for Gantt, Burndown, and Risk Heatmap.
    """
    project = get_object_or_404(models.Project, pk=pk)
    tasks = models.ProjectTask.objects.filter(phase__project=project).select_related('owner', 'phase', 'sprint')
    
    # Gantt Data
    gantt_data = []
    for t in tasks:
        gantt_data.append({
            'id': t.id,
            'name': t.title,
            'start': t.phase.start_date.isoformat() if t.phase.start_date else project.start_date.isoformat(),
            'end': t.due_date.isoformat(),
            'progress': t.progress,
            'dependencies': list(t.dependencies.values_list('id', flat=True)),
            'owner': t.owner.username,
            'status': t.status
        })

    # Burndown Data (Simple version based on task completion)
    # Target: Uniform completion from project start to end
    # Actual: Cumulative completed tasks
    from django.db.models import Count
    from datetime import timedelta
    
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='Done').order_by('completed_at')
    
    # Simple risk heatmap logic
    now = timezone.now().date()
    risk_data = {
        'Red': tasks.filter(due_date__lt=now, status__in=['Pending', 'In Progress', 'Blocked']).count(),
        'Yellow': tasks.filter(due_date__gte=now, due_date__lte=now + timedelta(days=3), status__in=['Pending', 'In Progress']).count(),
        'Green': tasks.filter(status='Done').count() + tasks.filter(due_date__gt=now + timedelta(days=3)).count()
    }

    # Burndown Data
    burndown = []
    start_point = project.start_date or project.created_at.date()
    end_point = project.end_date or (start_point + timedelta(days=30))
    
    # Ideal line
    days_total = int((end_point - start_point).days or 1)
    for i in range(days_total + 1):
        day = start_point + timedelta(days=i)
        ideal_val = total_tasks - (total_tasks * (float(i) / float(days_total)))
        
        # Actual val
        completed_count = tasks.filter(status='Done', completed_at__date__lte=day).count()
        actual_val = total_tasks - completed_count
        
        burndown.append({
            'day': day.isoformat(),
            'ideal': round(ideal_val, 2),
            'actual': actual_val if day <= timezone.now().date() else None
        })

    # Phase Progress Data
    phase_progress = []
    for phase in project.phases.all().order_by('sequence'):
        phase_progress.append({
            'name': phase.name,
            'percentage': phase.task_completion_percentage,
            'status': phase.status,
            'is_current': phase.status == 'Active'
        })

    # Enhanced Risk Data
    risk_indicator = project.risk_indicator
    enhanced_risk = {
        'distribution': risk_data,
        'project_level': risk_indicator['level'],
        'project_color': risk_indicator['color'],
        'project_hex': risk_indicator['hex'],
        'project_icon': risk_indicator['icon']
    }

    return JsonResponse({
        'gantt': gantt_data,
        'risk': enhanced_risk,
        'burndown': burndown,
        'phase_progress': phase_progress,
        'total_tasks': total_tasks
    })

@login_required
def update_task_kanban(request):
    """
    AJAX view for SortableJS drag-and-drop.
    """
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        task_id = data.get('task_id')
        new_status = data.get('status')
        
        task = get_object_or_404(models.ProjectTask, pk=task_id)
        task.status = new_status
        if new_status == 'Done':
            task.completed_at = timezone.now()
            task.progress = 100
        task.save()
        
        # Recalculate health and check readiness
        from .services.governance import GovernanceService
        GovernanceService.update_project_health(task.phase.project)
        GovernanceService.check_phase_readiness(task.phase)
        
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def update_task(request, pk):
    """
    Modal-friendly view for Team Members to update their assigned task status.
    GET  → returns a small HTML form (for use inside uni_modal).
    POST → saves the status update, then redirects to the member dashboard.
    """
    task = get_object_or_404(models.ProjectTask, pk=pk)

    # Only the task owner, PM, or admin can access this
    security = getattr(request.user, 'security_profile', None)
    is_owner = task.owner == request.user
    is_pm_or_above = request.user.is_superuser or (security and security.role in ('MD', 'Board of Executives', 'HODs', 'Project Management Team', 'Project Leader'))

    if not (is_owner or is_pm_or_above):
        return HttpResponse('<div class="alert alert-danger">Access Denied.</div>', status=403)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        comment_text = request.POST.get('comment') # Changed from 'notes' to 'comment'

        if new_status in dict(models.ProjectTask.STATUS_CHOICES):
            old_status = task.status
            task.status = new_status
            if new_status == 'Done':
                task.completed_at = timezone.now()
                task.progress = 100 # Ensure progress is 100% when done
            else:
                task.completed_at = None
                # Optionally reset progress if not done, or leave as is
                # task.progress = 0 # Or some other logic
            task.save()
            
            # Save comment if provided
            if comment_text:
                models.ProjectComment.objects.create(
                    author=request.user,
                    content=comment_text,
                    task=task
                )

            # Log the change
            log_msg = f"Task '{task.title}' status changed from {old_status} to {new_status} by {request.user.username}."
            if comment_text:
                log_msg += f" Notes: {comment_text}"
            models.ProjectLog.objects.create(
                project=task.phase.project,
                user=request.user,
                message=log_msg
            )

            # Recalculate health
            from .services.governance import GovernanceService
            GovernanceService.update_project_health(task.phase.project)
            if new_status == 'Done':
                GovernanceService.check_phase_readiness(task.phase)

            messages.success(request, f"Task '{task.title}' updated to '{new_status}'.")
        else:
            messages.error(request, "Invalid status.")

        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/dashboard/member'))

    # GET: return a minimal modal-friendly HTML snippet
    status_choices = models.ProjectTask.STATUS_CHOICES
    html = f"""
    <div class="p-2">
        <div class="mb-3">
            <div class="d-flex align-items-center gap-2 mb-2">
                <i class="fas fa-tasks text-primary"></i>
                <strong class="">{task.title}</strong>
            </div>
            <span class="badge bg-secondary">{task.priority} Priority</span>
            <span class="badge bg-info ms-1">Due: {task.due_date}</span>
        </div>
        <form method="post" action="/projects/update-task/{task.pk}/">
            <input type="hidden" name="csrfmiddlewaretoken" value="__CSRF__">
            <div class="mb-3">
                <label class="form-label fw-semibold text-muted extra-small text-uppercase">New Status</label>
                <select name="status" class="form-select rounded-pill">
                    {''.join(f'<option value="{v}" {"selected" if v == task.status else ""}>{l}</option>' for v, l in status_choices)}
                </select>
            </div>
            <div class="mb-3">
                <label class="form-label fw-semibold text-muted extra-small text-uppercase">Progress Notes (optional)</label>
                <textarea name="notes" class="form-control rounded-3" rows="3" placeholder="Add a brief update on your progress..."></textarea>
            </div>
            <button type="submit" class="btn btn-primary rounded-pill px-4 w-100 fw-bold">
                <i class="fas fa-save me-2"></i> Save Update
            </button>
        </form>
    </div>
    <style>.extra-small {{ font-size: 0.75rem; }}</style>
    """
    # Inject CSRF token from the request into the plain HTML snippet
    from django.middleware.csrf import get_token
    csrf = get_token(request)
    html = html.replace('__CSRF__', csrf)
    return HttpResponse(html)


@login_required
def update_task_status(request, pk):

    """
    Updates a ProjectTask status and logs the event.
    """
    if request.method == 'POST':
        task = get_object_or_404(models.ProjectTask, pk=pk)
        new_status = request.POST.get('status')
        
        if new_status in dict(models.ProjectTask.STATUS_CHOICES):
            old_status = task.status
            task.status = new_status
            if new_status == 'Done':
                task.completed_at = timezone.now()
            elif new_status == 'Review':
                task.completed_at = None
            else:
                task.completed_at = None
            task.save()
            
            # Log the change
            models.ProjectLog.objects.create(
                project=task.phase.project,
                user=request.user,
                message=f"Task '{task.title}' updated from {old_status} to {new_status}."
            )
            
            # Recalculate health and check readiness
            from .services.governance import GovernanceService
            GovernanceService.update_project_health(task.phase.project)
            if new_status == 'Done':
                GovernanceService.check_phase_readiness(task.phase)
            
            messages.success(request, f"Task '{task.title}' updated to {new_status}.")
        else:
            messages.error(request, "Invalid status identifier.")
            
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def approvals_list(request):
    if not request.user.is_superuser:
        approvals = models.FileApproval.objects.filter(Q(requester=request.user) | Q(approver=request.user))
    else:
        approvals = models.FileApproval.objects.all()
    
    context = context_data(request)
    context['page_title'] = "Action Approvals"
    context['approvals'] = approvals
    return render(request, 'approvals_list.html', context)

@login_required
def handle_approval(request, pk, status):
    approval = get_object_or_404(models.FileApproval, pk=pk)
    if not request.user.is_superuser and approval.approver != request.user:
        messages.error(request, "Unauthorized.")
        return redirect('approvals-list')

    approval.status = status
    approval.approver = request.user
    approval.save()

    messages.success(request, f"Request {approval.id} has been {status}.")
    return redirect('approvals-list')

# ─── Portfolio Level Dashboard (Layer 1) ─────────────────────────────────────
@login_required
def project_portfolio(request):
    """Layer 1 – Organization-wide project portfolio dashboard."""
    context = context_data(request)
    context['page_title'] = 'Project Portfolio'

    all_projects = models.Project.objects.filter(is_deleted=False)

    context['total_projects']     = all_projects.count()
    context['active_projects']    = all_projects.filter(status='Active').count()
    context['completed_projects'] = all_projects.filter(status='Done').count()
    context['delayed_projects']   = all_projects.filter(status='Delayed').count()
    context['planned_projects']   = all_projects.filter(status='Planned').count()

    # Budget vs expenditure at portfolio level
    total_budget = all_projects.aggregate(t=Sum('budget'))['t'] or 0
    context['total_budget'] = total_budget

    # Health summary list for big-card view
    from .services.governance import GovernanceService
    from .services.intelligence import ProjectIntelligenceService
    
    project_health = []
    total_score = 0
    count_scored = 0
    
    for proj in all_projects:
        health = GovernanceService.update_project_health(proj)
        metrics = GovernanceService.calculate_institutional_metrics() # This calculates for whole org by default if no params
        # Actually we need project specific governance score for the table
        # Let's use a simpler per-project score logic or the service one
        p_ai = ProjectIntelligenceService.predict_project_delay(proj)
        
        # Aggregate org score (mocking based on project health for now or using service)
        # Using the actual GovernanceService metrics for the top KPI
        project_health.append({
            'project': proj, 
            'health': health,
            'ai': p_ai
        })
    
    org_stats = GovernanceService.calculate_institutional_metrics()
    context['org_stats'] = org_stats
    context['project_health'] = project_health
    
    return render(request, 'governance/portfolio.html', context)

@login_required
def intelligence_hub(request):
    """Centralized Notification Center for AI alerts."""
    from .services.automation import AutomationService
    
    # Trigger a scan for new alerts whenever the hub is visited
    # This ensures "intelligence" is always fresh even without a cron job
    try:
        AutomationService.process_all_alerts()
    except Exception as e:
        logger.error(f"Error processing alerts in hub: {str(e)}")

    context = context_data(request)
    context['page_title'] = "Intelligence Notification Hub"
    
    alerts = models.ProjectAlert.objects.filter(is_resolved=False).order_by('-created_at')
    
    alert_type = request.GET.get('type')
    if alert_type:
        alerts = alerts.filter(alert_type=alert_type)
        
    context['alerts'] = alerts
    context['alert_counts'] = {
        'total': alerts.count(),
        'predictive': alerts.filter(alert_type='Predictive').count(),
        'overdue': alerts.filter(alert_type='Overdue').count(),
        'sla': alerts.filter(alert_type='Deadline').count()
    }
    
    return render(request, 'governance/intelligence_hub.html', context)


# ─── Sprint Views (Layer 4) ───────────────────────────────────────────────────
@login_required
def manage_sprint(request, phase_pk, sprint_pk=None):
    """Create or edit a sprint inside a phase."""
    phase = get_object_or_404(models.ProjectPhase, pk=phase_pk)
    sprint = get_object_or_404(models.ProjectSprint, pk=sprint_pk) if sprint_pk else None

    # Check Permissions
    can_manage = False
    if sprint:
        can_manage = PermissionService.can_manage_sprint(request.user, sprint)
    else:
        # For creation, must be PM of the phase or Portfolio Admin
        role = PermissionService.get_user_role(request.user)
        can_manage = role == 'Portfolio Admin' or phase.pm == request.user

    if not can_manage:
        messages.error(request, "Access Denied: You do not have permission to manage sprints in this phase.")
        return redirect('project-detail', pk=phase.project.id)

    if request.method == 'POST':
        name       = request.POST.get('name')
        goals      = request.POST.get('goals', '')
        start_date = request.POST.get('start_date')
        end_date   = request.POST.get('end_date')
        member_ids = request.POST.getlist('members')

        if sprint:
            sprint.name       = name
            sprint.goals      = goals
            sprint.start_date = start_date
            sprint.end_date   = end_date
            sprint.save()
            sprint.members.set(member_ids)
            msg = f"Sprint '{name}' updated."
        else:
            sprint = models.ProjectSprint.objects.create(
                phase=phase, name=name, goals=goals,
                start_date=start_date, end_date=end_date
            )
            sprint.members.set(member_ids)
            msg = f"Sprint '{name}' created."

        models.ProjectLog.objects.create(
            project=phase.project, user=request.user, message=msg
        )
        messages.success(request, msg)
        return redirect('sprint-detail', pk=sprint.pk)

    context = context_data(request)
    context['phase']   = phase
    context['sprint']  = sprint
    context['users']   = User.objects.filter(is_active=True)
    context['page_title'] = 'Manage Sprint'
    return render(request, 'governance/manage_sprint.html', context)


@login_required
def sprint_detail(request, pk):
    """Sprint detail page – Layer 4 agile view."""
    sprint = get_object_or_404(models.ProjectSprint, pk=pk)
    context = context_data(request)
    context['page_title'] = f"Sprint: {sprint.name}"
    context['sprint'] = sprint
    context['tasks']  = sprint.tasks.all().order_by('due_date')
    
    from .services.intelligence import ProjectIntelligenceService
    context['sprint_ai'] = ProjectIntelligenceService.predict_sprint_delay(sprint)

    # Velocity = done tasks / total tasks * 100
    total = sprint.tasks.count()
    done  = sprint.tasks.filter(status='Done').count()
    context['velocity'] = round((done / total * 100) if total else 0)
    context['done_count']  = done
    context['total_count'] = total
    context['users'] = User.objects.filter(is_active=True)
    
    # Workload detection
    overload_alerts = {}
    for member in sprint.members.all():
        is_overloaded, msg = ProjectIntelligenceService.detect_user_overload(member)
        if is_overloaded:
            overload_alerts[member.id] = msg
    context['overload_alerts'] = overload_alerts
    
    context['phase'] = sprint.phase

    # Kanban columns config: (status_value, label, color)
    context['task_columns'] = [
        ('To Do',       'To Do',       '#6c757d'),
        ('In Progress', 'In Progress', '#0d6efd'),
        ('Review',     'Review',      '#17a2b8'),
        ('Done',        'Done',        '#198754'),
        ('Blocked',     'Blocked',     '#dc3545'),
    ]
    return render(request, 'governance/sprint_detail.html', context)


@login_required
def update_sprint_status(request, pk):
    sprint = get_object_or_404(models.ProjectSprint, pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(models.ProjectSprint.STATUS_CHOICES):
            sprint.status = new_status
            sprint.save()
            models.ProjectLog.objects.create(
                project=sprint.phase.project, user=request.user,
                message=f"Sprint '{sprint.name}' status changed to {new_status}."
            )
            messages.success(request, f"Sprint status updated to {new_status}.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


# ─── Task Detail View (Layer 5) ───────────────────────────────────────────────
@login_required
def task_detail(request, pk):
    """Full task detail with comments and attachments."""
    task = get_object_or_404(models.ProjectTask, pk=pk)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'comment':
            content = request.POST.get('content', '').strip()
            if content:
                from .services.collaboration import CollaborationService
                comment = models.ProjectComment.objects.create(
                    task=task, 
                    author=request.user, 
                    content=content
                )
                CollaborationService.parse_mentions(comment)
                
                models.ProjectLog.objects.create(
                    project=task.phase.project, user=request.user,
                    message=f"Comment added to task '{task.title}'."
                )
                messages.success(request, 'Comment added.')

        elif action == 'attach':
            uploaded = request.FILES.get('file')
            external_link = request.POST.get('external_link')
            
            created_any = False
            if uploaded:
                models.TaskAttachment.objects.create(
                    task=task, 
                    file=uploaded, 
                    filename=uploaded.name
                )
                created_any = True
                messages.success(request, f"File '{uploaded.name}' attached.")

            if external_link:
                # Use the link itself as filename if not too long, else truncate
                disp_name = external_link
                if len(disp_name) > 50:
                    disp_name = disp_name[:47] + "..."
                
                models.TaskAttachment.objects.create(
                    task=task, 
                    external_link=external_link,
                    filename=f"Link: {disp_name}"
                )
                created_any = True
                messages.success(request, "External link attached.")

            if not created_any:
                messages.error(request, "Please provide a file or a link.")

        elif action == 'status':
            new_status = request.POST.get('status')
            if new_status in dict(models.ProjectTask.STATUS_CHOICES):
                task.status = new_status
                if new_status == 'Done':
                    task.completed_at = timezone.now()
                else:
                    task.completed_at = None
                task.save()
                messages.success(request, f"Task status updated to {new_status}.")

        elif action == 'link_entity':
            etype = request.POST.get('entity_type')
            eid = request.POST.get('entity_id')
            if eid:
                if etype == 'requisition':
                    task.linked_requisition = get_object_or_404(models.Requisition, pk=eid)
                elif etype == 'contract':
                    task.linked_contract = get_object_or_404(models.Contract, pk=eid)
                elif etype == 'resolution':
                    task.linked_resolution = get_object_or_404(models.Resolution, pk=eid)
                elif etype == 'physical_file':
                    task.physical_file = get_object_or_404(models.File, pk=eid)
                task.save()
                messages.success(request, f"Linked to {etype} successfully.")

        elif action == 'unlink_entity':
            etype = request.POST.get('entity_type')
            if etype == 'requisition': task.linked_requisition = None
            elif etype == 'contract': task.linked_contract = None
            elif etype == 'resolution': task.linked_resolution = None
            elif etype == 'physical_file': task.physical_file = None
            task.save()
            messages.success(request, f"Unlinked {etype}.")

        return redirect('task-detail', pk=task.pk)

    context = context_data(request)
    context['page_title'] = f"Task: {task.title}"
    context['task']        = task
    # Load top-level comments and pre-fetch authors and replies for efficiency
    context['comments']    = task.project_comments.filter(parent=None).prefetch_related(
        'author', 'replies', 'replies__author'
    ).order_by('created_at')
    context['attachments'] = task.attachments.all()
    context['linked_docs'] = task.linked_docs.all()
    context['all_files']   = models.File.objects.all()[:100]
    context['all_requisitions'] = models.Requisition.objects.all().order_by('-date_requested')[:50]
    context['all_contracts'] = models.Contract.objects.all().order_by('-date_created')[:50]
    context['all_resolutions'] = models.Resolution.objects.all().order_by('-date_created')[:50]

    # Approved members for reassignment dropdown
    approved_ids = models.ProjectMember.objects.filter(project=task.phase.project, is_approved=True).values_list('user_id', flat=True)
    context['project_members'] = User.objects.filter(id__in=approved_ids, is_active=True)

    # ── Role-based task action flags ──
    context['can_edit_task']         = PermissionService.can_edit_task(request.user, task)
    context['can_approve_task']      = PermissionService.can_approve_task(request.user, task)
    context['can_reassign_task']     = PermissionService.can_reassign_task(request.user)
    context['is_task_owner']         = (task.owner == request.user)
    # Team members (task owners) can update status and submit deliverables
    is_owner    = (task.owner == request.user)
    is_pm_above = PermissionService.is_pm_or_above(request.user)
    context['can_update_status']      = is_owner or is_pm_above
    context['can_upload_deliverable'] = is_owner or is_pm_above
    return render(request, 'governance/task_detail.html', context)



@login_required
def manage_task(request, phase_pk, task_pk=None):
    """Create or edit a task."""
    phase = get_object_or_404(models.ProjectPhase, pk=phase_pk)
    task  = get_object_or_404(models.ProjectTask, pk=task_pk) if task_pk else None

    # Check Permissions
    can_manage = False
    if task:
        # Editing an existing task: PL or above can always edit; owner can self-edit
        can_manage = PermissionService.can_edit_task(request.user, task)
    else:
        # CREATING a new task: ONLY the Project Leader (phase.pm) or superuser
        role = PermissionService.get_user_role(request.user)
        is_pl = (role == 'Project Leader') or request.user.is_superuser
        is_phase_pl = phase.pm == request.user
        can_manage = is_pl or is_phase_pl

    if not can_manage:
        messages.error(request, "Access Denied: You do not have permission to manage this task.")
        return redirect('project-detail', pk=phase.project.id)

    # ── Phase-status guard: NEW tasks may only be created on Active phases ──
    if not task and phase.status != 'Active':
        messages.error(
            request,
            f"Tasks cannot be added to this phase because it is currently in «{phase.status}» status. "
            "Tasks may only be added when the phase is Active."
        )
        return redirect('project-detail', pk=phase.project.id)

    if request.method == 'POST':
        title       = request.POST.get('title')
        description = request.POST.get('description')
        owner_id    = request.POST.get('owner')
        priority    = request.POST.get('priority', 'Medium')
        start_date  = request.POST.get('start_date') or None
        due_date    = request.POST.get('due_date')
        sprint_id   = request.POST.get('sprint') or None
        doc_ids     = request.POST.getlist('linked_docs')
        
        is_deliverable = request.POST.get('is_deliverable') == 'on'
        
        # Allocation Guard: Only PM/Admin can change task ownership
        if PermissionService.can_reassign_task(request.user):
            owner = get_object_or_404(User, pk=owner_id)
        else:
            owner = task.owner if task else request.user

        sprint      = get_object_or_404(models.ProjectSprint, pk=sprint_id) if sprint_id else None

        # AUTO-MEMBERSHIP: Ensure owner is an approved ProjectMember
        pm_entry, created = models.ProjectMember.objects.get_or_create(project=phase.project, user=owner)
        if not pm_entry.is_approved:
            pm_entry.is_approved = True
            pm_entry.approved_by = request.user
            pm_entry.approved_at = timezone.now()
            pm_entry.save()

        if task:
            task.title       = title
            task.description = description
            task.owner       = owner
            task.priority    = priority
            task.start_date  = start_date
            task.due_date    = due_date
            task.sprint      = sprint
            task.is_deliverable = is_deliverable
            task.save()
            task.linked_docs.set(doc_ids)
            msg = f"Task '{title}' updated."
        else:
            role = PermissionService.get_user_role(request.user)
            is_pm_above = role in PM_ROLES or phase.pm == request.user
            
            # Labeling Requirement: Self Assigned Tasks
            final_title = title
            if not is_pm_above:
                final_title = f"Self Assigned Task: {title}"

            task = models.ProjectTask.objects.create(
                phase=phase, title=final_title, description=description,
                owner=owner, priority=priority, start_date=start_date,
                due_date=due_date, sprint=sprint, is_deliverable=is_deliverable,
                assigned_by=request.user,
                self_assigned=not is_pm_above
            )
            task.linked_docs.set(doc_ids)
            msg = f"Task '{title}' created."

        models.ProjectLog.objects.create(
            project=phase.project, user=request.user, message=msg
        )
        messages.success(request, msg)
        return redirect('task-detail', pk=task.pk)

    context = context_data(request)
    from .services.intelligence import ProjectIntelligenceService
    context['suggested_date'] = ProjectIntelligenceService.get_suggested_deadline(phase=phase).isoformat()
    
    role = PermissionService.get_user_role(request.user)
    context['phase']             = phase
    context['task']              = task
    
    # Dropdown: show approved project members OR any user in a governance role (broader)
    from django.db.models import Q
    governance_roles = PM_ROLES | {'Team Member'}
    context['users'] = User.objects.filter(
        (Q(id__in=models.ProjectMember.objects.filter(project=phase.project, is_approved=True).values_list('user_id', flat=True)) |
         Q(security_profile__role__in=governance_roles)),
        is_active=True
    ).distinct().order_by('username')
    
    context['sprints']           = phase.sprints.all()
    context['files']             = models.File.objects.all()[:100]
    context['page_title']        = 'Manage Task'
    context['can_reassign_task'] = PermissionService.can_reassign_task(request.user)
    context['user_role']         = role
    return render(request, 'governance/manage_task.html', context)


@login_required
def update_task(request, pk):
    """
    Handles granular task updates like reassignment.
    """
    task = get_object_or_404(models.ProjectTask, pk=pk)
    
    # Only PM/Admin can reassign
    if not PermissionService.can_reassign_task(request.user):
        messages.error(request, "Access Denied: You do not have permission to reassign this task.")
        return redirect('task-detail', pk=task.pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'reassign':
            new_owner_id = request.POST.get('owner')
            new_owner = get_object_or_404(User, pk=new_owner_id)
            
            # AUTO-MEMBERSHIP: Ensure owner is an approved ProjectMember
            pm_entry, created = models.ProjectMember.objects.get_or_create(project=task.phase.project, user=new_owner)
            if not pm_entry.is_approved:
                pm_entry.is_approved = True
                pm_entry.approved_by = request.user
                pm_entry.approved_at = timezone.now()
                pm_entry.save()
                
            old_owner = task.owner
            task.owner = new_owner
            task.assigned_by = request.user
            task.self_assigned = False
            task.save()
            
            msg = f"Task reassigned from {old_owner.username} to {new_owner.username}."
            models.ProjectLog.objects.create(
                project=task.phase.project, user=request.user, message=f"Task '{task.title}': {msg}"
            )
            messages.success(request, msg)
            
    return redirect('task-detail', pk=task.pk)


@login_required
def attach_phase_document(request, pk):
    """
    Stage-Gate compliance: Allows team members to upload/link deliverables to a project phase.
    """
    phase = get_object_or_404(models.ProjectPhase, pk=pk)
    if request.method == 'POST':
        title = request.POST.get('title')
        file_attachment = request.FILES.get('file_attachment')
        external_link = request.POST.get('external_link')
        
        if not title or (not file_attachment and not external_link):
            messages.error(request, "Document Title and either a File or Link are required.")
            return redirect('project-detail', pk=phase.project.pk)
            
        try:
            from .models import SubCategory
            # Find a suitable sub-category (Governance/Project Docs)
            subcat = SubCategory.objects.filter(name__icontains='Governance').first() or SubCategory.objects.first()
            
            # Create the RIFTS-X compliant File record
            file_doc = models.File.objects.create(
                sub_category=subcat,
                ref_num=f"ZRP-PRJ-{phase.project.id}-{secrets.token_hex(3).upper()}",
                title=title,
                file_attachment=file_attachment,
                external_link=external_link,
                current_department=phase.project.department,
                status='1' # Active
            )
            
            # Link to phase as a required/verified deliverable
            phase.required_documents.add(file_doc)
            
            # Log the action (Audit Trail)
            models.ProjectLog.objects.create(
                project=phase.project,
                user=request.user,
                message=f"Deliverable uploaded to Phase '{phase.name}': {title} (Ref: {file_doc.ref_num})"
            )
            
            messages.success(request, f"Deliverable '{title}' successfully linked to Phase '{phase.name}'.")
        except Exception as e:
            messages.error(request, f"Failed to upload document: {str(e)}")
            
    return redirect('project-detail', pk=phase.project.pk)


@login_required
def add_comment(request):
    """
    Unified entry point for adding comments to any project object (Layer 2-5).
    """
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        obj_type = request.POST.get('obj_type')
        obj_id = request.POST.get('obj_id')
        parent_id = request.POST.get('parent_id')
        
        is_decision = request.POST.get('is_decision') == 'on'
        is_action_item = request.POST.get('is_action_item') == 'on'
        
        if not content or not obj_type or not obj_id:
            messages.error(request, "Comment content and target are required.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            
        try:
            from .services.collaboration import CollaborationService
            comment = models.ProjectComment(
                author=request.user,
                content=content,
                is_decision=is_decision,
                is_action_item=is_action_item
            )
            
            if parent_id:
                comment.parent_id = parent_id
                
            if obj_type == 'Project':
                comment.project_id = obj_id
            elif obj_type == 'Phase':
                comment.phase_id = obj_id
            elif obj_type == 'Sprint':
                comment.sprint_id = obj_id
            elif obj_type == 'Task':
                comment.task_id = obj_id
                
            comment.save()
            
            # Process Multi-file Attachments (RIFTS-X Integration)
            files = request.FILES.getlist('attachments')
            for f in files:
                # Create a registry File record for each attachment
                # Assuming 'Miscellaneous' or 'Collaboration' subcategory exists or find first
                from .models import SubCategory, File
                subcat = SubCategory.objects.first() # institutional fallback
                new_file = File.objects.create(
                    sub_category=subcat,
                    title=f.name,
                    ref_num=f"ZRP-COLLAB-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                    file_attachment=f
                )
                comment.attachments.add(new_file)
                
            # Process mentions and notify
            CollaborationService.parse_mentions(comment)
            
            # Activity Log for collaboration
            models.ProjectLog.objects.create(
                project=comment.project or (comment.phase.project if comment.phase else (comment.sprint.phase.project if comment.sprint else comment.task.phase.project)),
                user=request.user,
                message=f"New collaboration entry (Type: {obj_type}) recorded."
            )
            
            messages.success(request, "Collaboration entry recorded.")
        except Exception as e:
            messages.error(request, f"Failed to record collaboration: {str(e)}")
            
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def resolve_action_item(request, pk):
    """Marks a collaboration action item as resolved."""
    comment = get_object_or_404(models.ProjectComment, pk=pk)
    if comment.is_action_item:
        comment.is_resolved = True
        comment.save()
        messages.success(request, "Action item marked as resolved.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def request_project_membership(request, project_pk):
    project = get_object_or_404(models.Project, pk=project_pk)
    membership, created = models.ProjectMember.objects.get_or_create(project=project, user=request.user)
    if created:
        messages.success(request, f"Membership request for '{project.name}' submitted to Project Leader.")
    else:
        if membership.is_approved:
            messages.info(request, "You are already an approved member of this project.")
        else:
            messages.info(request, "Your membership request is still pending approval.")
    return redirect('project-detail', pk=project.pk)

@login_required
def approve_project_member(request, membership_pk, action):
    membership = get_object_or_404(models.ProjectMember, pk=membership_pk)
    project = membership.project
    
    # Permission check: Any PM/Admin or Higher can approve members (Institution-wide management)
    user_role = PermissionService.get_user_role(request.user)
    if not (request.user.is_superuser or user_role in PM_ROLES or project.owner == request.user):
        messages.error(request, "Access Denied: You do not have permission to manage project membership.")
        return redirect('project-detail', pk=project.pk)
        
    if action == 'Approve':
        membership.is_approved = True
        membership.approved_by = request.user
        membership.approved_at = timezone.now()
        membership.save()
        messages.success(request, f"User {membership.user.username} approved as project member.")
    elif action == 'Reject':
        membership.delete()
        messages.warning(request, f"Membership request for {membership.user.username} rejected.")
    
    return redirect('project-detail', pk=project.pk)


# ══════════════════════════════════════════════════════════
# HOD COST RECOVERY FINANCIAL DASHBOARD
# ══════════════════════════════════════════════════════════

@login_required
def hod_financial_dashboard(request):
    """HOD Cost Recovery Financial Dashboard (now accessible to all with read-only for Team Members)."""
    from .models import CostRecovery, Department
    from django.db.models import Sum
    import json

    context = context_data(request)
    user_sec = context.get('security_profile')

    # Visibility updated: Everyone can see the recoveries org-wide
    recoveries = CostRecovery.objects.select_related('department', 'hod').all()

    # Summary totals
    total_recovered = recoveries.aggregate(total=Sum('amount_recovered'))['total'] or 0
    by_category = {}
    for cat_code, cat_label in CostRecovery.CATEGORY_CHOICES:
        cat_total = recoveries.filter(cost_savings_category=cat_code).aggregate(t=Sum('amount_recovered'))['t'] or 0
        by_category[cat_label] = float(cat_total)

    # Monthly trend (last 12 months)
    from django.utils import timezone as tz
    from django.db.models.functions import TruncMonth
    monthly = (
        recoveries
        .annotate(month=TruncMonth('date_recorded'))
        .values('month')
        .annotate(total=Sum('amount_recovered'))
        .order_by('month')
    )
    monthly_labels = [m['month'].strftime('%b %Y') for m in monthly]
    monthly_data = [float(m['total']) for m in monthly]

    departments = Department.objects.all()

    context.update({
        'recoveries': recoveries,
        'total_recovered': total_recovered,
        'by_category': by_category,
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_data': json.dumps(monthly_data),
        'category_labels': json.dumps(list(by_category.keys())),
        'category_data': json.dumps(list(by_category.values())),
        'category_choices': CostRecovery.CATEGORY_CHOICES,
        'departments': departments,
        'user_dept': getattr(user_sec, 'department', None),
        'active_tab': 'hod_financial',
    })
    return render(request, 'governance/hod_financial_dashboard.html', context)


@login_required
def save_cost_recovery(request):
    """AJAX POST: save a new CostRecovery entry."""
    from .models import CostRecovery, Department
    import json
    from django.db.models import Sum

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    user_sec = models.UserSecurity.objects.filter(user=request.user).first()
    # Financial Dashboard is read-only for PM, Team Members, and MD. Only PMT can record recoveries.
    if not (user_sec and user_sec.role == 'Project Management Team') and not request.user.is_superuser:
        return JsonResponse({'error': 'Access Denied: Only Project Management Team can record recoveries.'}, status=403)

    dept_id = request.POST.get('department')
    amount = request.POST.get('amount_recovered')
    category = request.POST.get('cost_savings_category')
    description = request.POST.get('description', '').strip()
    evidence = request.FILES.get('evidence_document')

    if not dept_id or not amount or not category:
        return JsonResponse({'error': 'Missing required fields: department, amount, or category.'}, status=400)

    if not description:
        description = 'No description provided.'

    try:
        # Robust Amount Validation
        try:
            amount_val = float(amount)
            if amount_val <= 0:
                return JsonResponse({'error': 'Amount recovered must be a positive value.'}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid amount format. Please enter a valid number.'}, status=400)

        dept = Department.objects.get(pk=dept_id)
        rec = CostRecovery.objects.create(
            department=dept,
            hod=request.user,
            amount_recovered=amount_val,
            cost_savings_category=category,
            description=description,
            evidence_document=evidence,
        )

        # Return updated chart data - always use org-wide data like the dashboard does
        qs = CostRecovery.objects.all()

        from django.db.models.functions import TruncMonth
        monthly = (
            qs.annotate(month=TruncMonth('date_recorded'))
            .values('month')
            .annotate(total=Sum('amount_recovered'))
            .order_by('month')
        )

        by_category = {}
        for cat_code, cat_label in CostRecovery.CATEGORY_CHOICES:
            cat_total = qs.filter(cost_savings_category=cat_code).aggregate(t=Sum('amount_recovered'))['t'] or 0
            by_category[cat_label] = float(cat_total)

        total_recovered = float(qs.aggregate(t=Sum('amount_recovered'))['t'] or 0)
        
        return JsonResponse({
            'success': True,
            'id': rec.pk,
            'amount': float(rec.amount_recovered),
            'category': rec.get_cost_savings_category_display(),
            'department': rec.department.name,
            'hod': rec.hod.get_full_name() or rec.hod.username,
            'date': rec.date_recorded.strftime('%d %b %Y'),
            'evidence_url': rec.evidence_document.url if rec.evidence_document else None,
            'monthly_labels': [m['month'].strftime('%b %Y') for m in monthly],
            'monthly_data': [float(m['total']) for m in monthly],
            'category_labels': list(by_category.keys()),
            'category_data': list(by_category.values()),
            'total_recovered': total_recovered,
            'entry_count': qs.count(),
        })
    except Department.DoesNotExist:
        return JsonResponse({'error': 'Selected department does not exist.'}, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Save failed: {str(e)}'}, status=500)


@login_required
def cost_recovery_chart_data(request):
    """Returns current chart data as JSON for live refresh."""
    from .models import CostRecovery
    from django.db.models import Sum
    from django.db.models.functions import TruncMonth

    user_sec = models.UserSecurity.objects.filter(user=request.user).first()
    # Visibility update: All users can access all chart data
    qs = CostRecovery.objects.all()

    monthly = (
        qs.annotate(month=TruncMonth('date_recorded'))
        .values('month').annotate(total=Sum('amount_recovered')).order_by('month')
    )
    by_category = {}
    for cat_code, cat_label in CostRecovery.CATEGORY_CHOICES:
        cat_total = qs.filter(cost_savings_category=cat_code).aggregate(t=Sum('amount_recovered'))['t'] or 0
        by_category[cat_label] = float(cat_total)

    return JsonResponse({
        'monthly_labels': [m['month'].strftime('%b %Y') for m in monthly],
        'monthly_data': [float(m['total']) for m in monthly],
        'category_labels': list(by_category.keys()),
        'category_data': list(by_category.values()),
        'total_recovered': float(qs.aggregate(t=Sum('amount_recovered'))['t'] or 0),
    })


@login_required
def get_mention_users(request):
    """Returns a list of usernames for MD, HOD, PM, and Team Members for @mentions."""
    from .models import UserSecurity
    eligible_roles = ['MD', 'Board of Executives', 'HODs', 'Project Management Team', 'Project Leader', 'Team Member']
    users = User.objects.filter(
        security_profile__role__in=eligible_roles
    ).values('username', 'id').distinct()
    
    return JsonResponse({'users': list(users)})


@login_required
def get_user_notifications(request):
    """Returns unread notifications for the current user."""
    from .models import ProjectAlert
    alerts = ProjectAlert.objects.filter(
        recipient=request.user,
        is_resolved=False
    ).order_by('-created_at')[:10]
    
    data = []
    for a in alerts:
        data.append({
            'id': a.id,
            'message': a.message,
            'alert_type': a.alert_type,
            'created_at': a.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return JsonResponse({'notifications': data})


# ── Benefit Management (HOD Side) ─────────────────────────────────────────────

@login_required
def benefit_list(request):
    """View all institution benefits - Strategic Analytics View."""
    context = context_data(request)
    benefits = models.Benefit.objects.all().select_related('department', 'hod')
    
    # Analytics
    total_monthly = benefits.aggregate(Sum('monthly_savings'))['monthly_savings__sum'] or 0
    total_annual = benefits.aggregate(Sum('annual_projection'))['annual_projection__sum'] or 0
    
    context.update({
        'page_title': 'Institutional Benefits & Savings',
        'benefits': benefits,
        'total_monthly': total_monthly,
        'total_annual': total_annual,
    })
    return render(request, 'governance/benefit_list.html', context)

@login_required
def manage_benefit(request, pk=None):
    """PMT can Add/Update Benefit records."""
    user_sec = UserSecurity.objects.filter(user=request.user).first()
    if not (user_sec and user_sec.role == 'Project Management Team') and not request.user.is_superuser:
        return HttpResponseForbidden("Access Denied: Only Project Management Team can manage benefits.")

    benefit = get_object_or_404(models.Benefit, pk=pk) if pk else None
    if request.method == 'POST':
        form = BenefitForm(request.POST, instance=benefit)
        if form.is_valid():
            benefit = form.save(commit=False)
            benefit.hod = request.user
            benefit.save()
            messages.success(request, "Benefit record saved successfully.")
            return redirect('benefit-list')
    else:
        form = BenefitForm(instance=benefit)
    
    context = context_data(request)
    context['form'] = form
    context['benefit'] = benefit
    context['page_title'] = 'Manage Benefit Record'
    return render(request, 'governance/benefit_form.html', context)

@login_required
def delete_benefit(request, pk):
    """PMT can delete benefit records."""
    user_sec = UserSecurity.objects.filter(user=request.user).first()
    if not (user_sec and user_sec.role == 'Project Management Team') and not request.user.is_superuser:
        return HttpResponseForbidden("Access Denied.")
        
    benefit = get_object_or_404(models.Benefit, pk=pk)
    benefit.delete()
    messages.success(request, "Benefit record deleted.")
    return redirect('benefit-list')

# ── Deliverable release logic ──────────────────────────────────────────────────

@login_required
def download_phase_deliverables(request, pk):
    """Zip and download all documents from tasks marked as is_deliverable in a phase."""
    phase = get_object_or_404(models.ProjectPhase, pk=pk)
    
    # RELAXED PERMISSION: Allow PM and above to download deliverables before completion for review
    if phase.status != 'Done' and not request.user.is_superuser:
        if not PermissionService.is_pm_or_above(request.user):
            messages.error(request, "Access Denied: Deliverables are only available after complete institutional approval or for PM review.")
            return redirect('project-detail', pk=phase.project.pk)
        
    deliverable_tasks = phase.tasks.filter(is_deliverable=True)
    
    # Create the zip file
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zip_file:
        for task in deliverable_tasks:
            attachments = task.attachments.all()
            for attach in attachments:
                if attach.file:
                    # Determine a unique path in zip
                    file_path = f"Task_{task.id}_{task.title[:30]}/{attach.filename}"
                    try:
                        zip_file.writestr(file_path, attach.file.read())
                    except Exception as e:
                        logger.error(f"Failed to add {attach.filename} to zip: {e}")

        # Add Phase Required Documents (Stage-Gate Evidence)
        phase_docs = phase.required_documents.all()
        for doc in phase_docs:
            if doc.file_attachment:
                file_path = f"Phase_Evidence/{doc.file_attachment.name.split('/')[-1]}"
                try:
                    zip_file.writestr(file_path, doc.file_attachment.read())
                except Exception as e:
                    logger.error(f"Failed to add phase document {doc.title} to zip: {e}")

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/x-zip-compressed')
    response['Content-Disposition'] = f'attachment; filename="Deliverables_{phase.project.name}_{phase.name}.zip"'
    return response


# ═════════════════════════════════════════════════════════════════════════════
# BRD (Business Requirements Document) Workflow Views
# ═════════════════════════════════════════════════════════════════════════════

@login_required
def brd_list(request):
    """List BRDs visible to the current user."""
    context = context_data(request)
    context['page_title'] = 'Business Requirements Documents'
    security = getattr(request.user, 'security_profile', None)
    role = security.role if security else ''

    if request.user.is_superuser or role in ['Project Management Team', 'HODs', 'Board of Executives', 'Portfolio Admin']:
        # Governance users see all BRDs
        brds = models.BRD.objects.all()
    else:
        # Members/PLs see BRDs they initiated or are assigned to approve
        query = Q(initiator=request.user) | Q(approvers__user=request.user)
        if role == 'Project Leader':
            query |= Q(forwarded_to_pl_at__isnull=False)
            
        brds = models.BRD.objects.filter(query).distinct()

    context['brds'] = brds
    context['can_initiate'] = role in ['Team Member', 'Project Leader'] or request.user.is_superuser
    return render(request, 'governance/brd_list.html', context)


@login_required
def initiate_brd(request):
    """Team Member initiates a new BRD."""
    context = context_data(request)
    context['page_title'] = 'Initiate Business Requirements Document'

    # Fetch eligible users for each level
    context['pmt_users'] = User.objects.filter(
        security_profile__role='Project Management Team',
        security_profile__is_role_approved=True
    ).select_related('security_profile')
    context['hod_users'] = User.objects.filter(
        security_profile__role='HODs',
        security_profile__is_role_approved=True
    ).select_related('security_profile')
    context['board_users'] = User.objects.filter(
        security_profile__role='Board of Executives',
        security_profile__is_role_approved=True
    ).select_related('security_profile')

    if request.method == 'POST':
        title       = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        document    = request.FILES.get('document')

        pmt_required   = int(request.POST.get('pmt_required', 1))
        hods_required  = int(request.POST.get('hods_required', 1))
        board_required = int(request.POST.get('board_required', 1))

        pmt_user_ids   = request.POST.getlist('pmt_approvers')
        hod_user_ids   = request.POST.getlist('hod_approvers')
        board_user_ids = request.POST.getlist('board_approvers')

        if not title or not document:
            messages.error(request, 'Title and document are required.')
            return render(request, 'governance/brd_initiate.html', context)

        if not pmt_user_ids or not hod_user_ids or not board_user_ids:
            messages.error(request, 'You must select at least one approver at each level.')
            return render(request, 'governance/brd_initiate.html', context)

        brd = models.BRD.objects.create(
            title=title,
            description=description,
            initiator=request.user,
            document=document,
            status='Awaiting PMT',
            pmt_required=min(pmt_required, len(pmt_user_ids)),
            hods_required=min(hods_required, len(hod_user_ids)),
            board_required=min(board_required, len(board_user_ids)),
        )

        pmt_emails = []
        # Create approver records per level
        for idx, uid in enumerate(pmt_user_ids):
            u = get_object_or_404(User, pk=uid)
            if u.email:
                pmt_emails.append(u.email)
            sec = getattr(u, 'security_profile', None)
            models.BRDApprover.objects.create(
                brd=brd, user=u, level='PMT',
                designation=sec.role if sec else 'PMT Member',
                order=idx
            )
        for idx, uid in enumerate(hod_user_ids):
            u = get_object_or_404(User, pk=uid)
            sec = getattr(u, 'security_profile', None)
            models.BRDApprover.objects.create(
                brd=brd, user=u, level='HODs',
                designation=sec.role if sec else 'HOD',
                order=idx
            )
        for idx, uid in enumerate(board_user_ids):
            u = get_object_or_404(User, pk=uid)
            sec = getattr(u, 'security_profile', None)
            models.BRDApprover.objects.create(
                brd=brd, user=u, level='Board',
                designation=sec.role if sec else 'Board Member',
                order=idx
            )
            
        # Send email to PMT
        if pmt_emails:
            try:
                from django.core.mail import send_mail
                SUBJECT = f"Action Required: BRD '{brd.title}' awaits your signature"
                brd_url = request.build_absolute_uri(f'/brd/{brd.pk}/')
                MESSAGE = f"Hello,\n\nA new Business Requirements Document '{brd.title}' has been submitted and is awaiting PMT approval.\nPlease log in to review and sign the document:\n{brd_url}\n\nThank you."
                send_mail(SUBJECT, MESSAGE, None, pmt_emails, fail_silently=True)
            except Exception as e:
                pass

        messages.success(request, f'BRD "{brd.title}" has been initiated and sent to PMT for review.')
        return redirect('brd-detail', pk=brd.pk)

    return render(request, 'governance/brd_initiate.html', context)


@login_required
def brd_detail(request, pk):
    """View BRD details and signature table."""
    brd = get_object_or_404(models.BRD, pk=pk)
    context = context_data(request)
    context['page_title'] = f'BRD: {brd.title}'
    context['brd'] = brd

    # Build signature rows per level
    for level_key in ['PMT', 'HODs', 'Board']:
        approvers = brd.approvers.filter(level=level_key)
        rows = []
        for appr in approvers:
            sig = brd.signatures.filter(approver=appr).first()
            rows.append({'approver': appr, 'signature': sig})
        context[f'{level_key.lower()}_rows'] = rows

    # Determine if current user is a pending approver at the current level
    level_map = {
        'Awaiting PMT':   'PMT',
        'Awaiting HODs':  'HODs',
        'Awaiting Board': 'Board',
    }
    current_level = level_map.get(brd.status)
    my_approver = None
    if current_level:
        my_approver = brd.approvers.filter(user=request.user, level=current_level).first()

    context['current_level'] = current_level
    context['my_approver']   = my_approver
    context['can_sign']      = (
        my_approver is not None and
        not my_approver.has_signed() and
        brd.status not in ['Approved', 'Rejected', 'Draft']
    )

    # Determine if quorum met and user can reject (any approver at current level)
    context['can_reject'] = (
        my_approver is not None and
        brd.status not in ['Approved', 'Rejected', 'Draft']
    )

    return render(request, 'governance/brd_detail.html', context)


@login_required
def sign_brd(request, pk):
    """Submit an electronic signature for the BRD."""
    brd = get_object_or_404(models.BRD, pk=pk)

    if brd.status in ['Approved', 'Rejected', 'Draft']:
        messages.error(request, 'This BRD is not currently open for signing.')
        return redirect('brd-detail', pk=pk)

    level_map = {
        'Awaiting PMT':   'PMT',
        'Awaiting HODs':  'HODs',
        'Awaiting Board': 'Board',
    }
    current_level = level_map.get(brd.status)
    if not current_level:
        messages.error(request, 'Invalid BRD status for signing.')
        return redirect('brd-detail', pk=pk)

    approver = brd.approvers.filter(user=request.user, level=current_level).first()
    if not approver:
        messages.error(request, 'You are not designated as an approver at this level.')
        return redirect('brd-detail', pk=pk)

    if approver.has_signed():
        messages.warning(request, 'You have already signed this BRD.')
        return redirect('brd-detail', pk=pk)

    if request.method == 'POST':
        signature_data = request.POST.get('signature_data')
        if not signature_data or signature_data == 'data:,':
            messages.error(request, 'Please provide a valid signature.')
            return redirect('brd-detail', pk=pk)

        # Capture the IP address
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR')

        sig = models.BRDSignature.objects.create(
            brd=brd,
            approver=approver,
            signature_data=signature_data,
            designation=approver.designation or '',
            signed_at=timezone.now(),
            ip_address=ip,
        )
        
        # Stamp the signature onto the PDF/DOCX document
        try:
            from registry.services.document_signer import append_signature_to_document
            append_signature_to_document(brd, approver, signature_data, ip, sig.signed_at)
        except Exception as e:
            # We fail silently here so the approval workflow doesn't break if stamping fails (e.g., corrupt file)
            print(f"Signature stamping failed: {str(e)}")

        # ── Auto-advance logic ──
        next_status = None
        if current_level == 'PMT' and brd.pmt_quorum_met():
            next_status = 'Awaiting HODs'
        elif current_level == 'HODs' and brd.hods_quorum_met():
            next_status = 'Awaiting Board'
        elif current_level == 'Board' and brd.board_quorum_met():
            next_status = 'Approved'
            
        from django.core.mail import send_mail

        if next_status:
            brd.status = next_status
            brd.save(update_fields=['status', 'updated_at'])
            
            brd_url = request.build_absolute_uri(f'/brd/{brd.pk}/')
            
            if next_status == 'Approved':
                messages.success(request, '🎉 All signatures collected! The BRD is now fully Approved.')
                if brd.initiator.email:
                    try:
                        send_mail(
                            f"BRD Approved: '{brd.title}'",
                            f"Hello,\n\nYour BRD '{brd.title}' has been fully approved by all authorized parties.\n\nView and download the final version here:\n{brd_url}",
                            None, [brd.initiator.email], fail_silently=True
                        )
                    except: pass
            else:
                messages.success(request, f'Quorum met! BRD advanced to {next_status}.')
                
                # Notify next level approvers
                next_level_key = 'HODs' if next_status == 'Awaiting HODs' else 'Board'
                next_approvers = brd.approvers.filter(level=next_level_key)
                emails = [app.user.email for app in next_approvers if app.user.email]
                if emails:
                    try:
                        send_mail(
                            f"Action Required: BRD '{brd.title}' awaits your signature",
                            f"Hello,\n\nThe BRD '{brd.title}' has advanced to {next_level_key} and requires your signature.\n\nPlease log in to review and sign the document:\n{brd_url}",
                            None,
                            emails,
                            fail_silently=True
                        )
                    except: pass
        else:
            sigs_so_far = brd.signatures.filter(approver__level=current_level).count()
            if current_level == 'PMT':
                required = brd.pmt_required
            elif current_level == 'HODs':
                required = brd.hods_required
            else:
                required = brd.board_required
            messages.success(request, f'Signature recorded ({sigs_so_far}/{required} required at {current_level} level).')

        return redirect('brd-detail', pk=pk)

    return redirect('brd-detail', pk=pk)

@login_required
def brd_sign_visual(request, pk):
    """Visual drag-and-drop signer interface."""
    from registry.services.document_signer import render_document_to_images, stamp_signature_at_coordinates
    brd = get_object_or_404(models.BRD, pk=pk)

    if brd.status in ['Approved', 'Rejected', 'Draft']:
        messages.error(request, 'This BRD is not currently open for signing.')
        return redirect('brd-detail', pk=pk)

    level_map = {
        'Awaiting PMT':   'PMT',
        'Awaiting HODs':  'HODs',
        'Awaiting Board': 'Board',
    }
    current_level = level_map.get(brd.status)
    if not current_level:
        messages.error(request, 'Invalid BRD status for signing.')
        return redirect('brd-detail', pk=pk)

    approver = brd.approvers.filter(user=request.user, level=current_level).first()
    if not approver:
        messages.error(request, 'You are not designated as an approver at this level.')
        return redirect('brd-detail', pk=pk)

    if approver.has_signed():
        messages.warning(request, 'You have already signed this BRD.')
        return redirect('brd-detail', pk=pk)

    if request.method == 'POST':
        signature_data = request.POST.get('signature_data')
        page_num = request.POST.get('page_num', '0')
        x_pct = request.POST.get('x_pct', '0')
        y_pct = request.POST.get('y_pct', '0')
        
        # New fields: comments and date stamp
        comment = request.POST.get('comments', '').strip()
        save_to_profile = request.POST.get('save_to_profile') == 'on'
        
        date_page = request.POST.get('date_page_num')
        date_x = request.POST.get('date_x_pct')
        date_y = request.POST.get('date_y_pct')
        
        logger.info(f"SIGNING BRD {pk}: Page={page_num}, X={x_pct}, Y={y_pct}, SigLen={len(signature_data) if signature_data else 0}")
        if date_page:
            logger.info(f"DATE STAMP: Page={date_page}, X={date_x}, Y={date_y}")
        
        if not signature_data or signature_data == 'data:,':
            messages.error(request, 'Please provide a valid signature.')
            return redirect('brd-sign-visual', pk=pk)

        # 1. Update/Save User Signature Profile
        if save_to_profile and signature_data:
            from registry.models import UserSignature
            profile, created = UserSignature.objects.get_or_create(user=request.user)
            profile.signature_data = signature_data
            profile.save()

        # 2. Stamp Document & Record Signature
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR')

        sig = models.BRDSignature.objects.create(
            brd=brd,
            approver=approver,
            signature_data=signature_data,
            designation=approver.designation or '',
            signed_at=timezone.now(),
            ip_address=ip,
            comments=comment
        )
        
        # Multi-stamping: Pass date coordinates if provided
        d_p = int(date_page) if date_page else None
        d_x = float(date_x) if date_x else None
        d_y = float(date_y) if date_y else None
        
        from registry.services.document_signer import stamp_signature_at_coordinates
        try:
            success = stamp_signature_at_coordinates(
                brd, approver, signature_data, int(page_num), float(x_pct), float(y_pct), ip, sig.signed_at,
                date_page=d_p, date_x=d_x, date_y=d_y
            )
            if not success:
                messages.warning(request, "Record saved, but visual stamping failed.")
            else:
                brd.refresh_from_db()
        except Exception as e:
            logger.error(f"Visual stamping error: {e}")

        # 3. Determine Flow and Notify
        next_status = None
        if current_level == 'PMT' and brd.pmt_quorum_met():
            next_status = 'Awaiting HODs'
        elif current_level == 'HODs' and brd.hods_quorum_met():
            next_status = 'Awaiting Board'
        elif current_level == 'Board' and brd.board_quorum_met():
            next_status = 'Approved'

        if next_status:
            brd.status = next_status
            brd.save(update_fields=['status', 'updated_at'])
            
            from django.core.mail import send_mail
            brd_url = request.build_absolute_uri(f'/brd/{brd.pk}/')
            comment_snippet = f"\n\nLatest comments from {request.user.get_full_name()}: \"{comment}\"" if comment else ""
            
            if next_status == 'Approved':
                if brd.initiator.email:
                    send_mail(
                        f"BRD Approved: '{brd.title}'",
                        f"Hello,\n\nYour BRD '{brd.title}' has been fully approved by all authorized parties.{comment_snippet}\n\nView here: {brd_url}",
                        None, [brd.initiator.email], fail_silently=True
                    )
            else:
                next_level_key = 'HODs' if next_status == 'Awaiting HODs' else 'Board'
                next_approvers = brd.approvers.filter(level=next_level_key)
                emails = [app.user.email for app in next_approvers if app.user.email]
                if emails:
                    send_mail(
                        f"Action Required: BRD '{brd.title}' requires your signature",
                        f"Hello,\n\nThe BRD '{brd.title}' has advanced to {next_level_key} and requires your signature.{comment_snippet}\n\nPlease review and sign: {brd_url}",
                        None, emails, fail_silently=True
                    )
        else:
            # ── PEER NOTIFICATIONS ──
            # If the status didn't change (quorum not yet met), notify other peers at the same level
            peers = brd.approvers.filter(level=current_level).exclude(user=request.user)
            peer_emails = [p.user.email for p in peers if p.user.email and not p.has_signed()]
            if peer_emails:
                from django.core.mail import send_mail
                brd_url = request.build_absolute_uri(f'/brd/{brd.pk}/')
                send_mail(
                    f"Signature Update: '{brd.title}'",
                    f"Hello,\n\n{request.user.get_full_name()} has just signed the BRD '{brd.title}'.\n\nYour signature is still required at the {current_level} level.\n\nSign here: {brd_url}",
                    None, peer_emails, fail_silently=True
                )
        
        # ── TRIGGER AI ANALYSIS ──
        # If no summary exists, we'll try to generate a basic one (Simulated AI)
        if not brd.ai_summary:
            try:
                from registry.services.document_signer import extract_text_from_document
                text = extract_text_from_document(brd)
                if text:
                    # We'll use a mocked "AI" response here since we don't have an LLM API.
                    # In a real environment, this would call OpenAI/Gemini.
                    brd.ai_summary = f"SUMMARY: This document appears to be a Business Requirements Document titled '{brd.title}'. It covers key objectives and specifications. (AI Analyzed)"
                    brd.ai_highlights = ["Draft Requirement Analysis", "Stakeholder Alignment", "Implementation Timeline"]
                    brd.save(update_fields=['ai_summary', 'ai_highlights'])
            except Exception as e:
                logger.error(f"AI Analysis failed: {e}")

        messages.success(request, "Document signed and stamped successfully.")
        return redirect('brd-detail', pk=brd.id)

    # ── GET REQUEST HANDLING ──
    # Render document pages to images for the visual signer
    images = render_document_to_images(brd)
    
    from registry.models import UserSignature
    user_sig = UserSignature.objects.filter(user=request.user).first()
    
    context = {
        'brd': brd,
        'pages': images, # Template uses 'pages', not 'images'
        'saved_signature': user_sig.signature_data if user_sig else None,
        'today_date': timezone.now().strftime('%Y-%m-%d'),
        'current_level': current_level
    }
    return render(request, 'governance/visual_signer.html', context)

@login_required
def brd_ai_analyze(request, pk):
    """View to manually trigger or re-trigger RIFTS-X AI analysis on a document."""
    if request.method != 'POST':
        return redirect('brd-detail', pk=pk)
        
    brd = get_object_or_404(BRD, pk=pk)
    from registry.services.document_signer import extract_text_from_document
    
    try:
        text = extract_text_from_document(brd)
        if text:
            # ── RIFTS-X INTELLIGENCE ENGINE (DEEP SCAN) ──
            lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 30]
            
            # Map sections
            sections = {
                'OBJECTIVES': [l for l in lines if any(k in l.lower() for k in ['objective', 'goal', 'aim', 'purpose'])][:2],
                'SCOPE': [l for l in lines if any(k in l.lower() for k in ['scope', 'boundary', 'delimitation'])][:2],
                'STAKEHOLDERS': [l for l in lines if any(k in l.lower() for k in ['pmt', 'hod', 'board', 'sponsor', 'user'])][:2],
                'TIMELINE': [l for l in lines if any(k in l.lower() for k in ['schedule', 'timeline', 'duration', 'phase', 'milestone'])][:2],
                'RISK': [l for l in lines if any(k in l.lower() for k in ['risk', 'mitigation', 'constraint', 'assumption'])][:2]
            }
            
            summary_blocks = []
            for name, content in sections.items():
                if content:
                    summary_blocks.append(f"**{name}**: {' '.join(content)}")
            
            # Contextual Description extracted from first few lines if not enough sections
            if not summary_blocks:
                summary_blocks.append(f"Analyzing '{brd.title}': This document appears to be a formal Business Requirements Document. Primary focus is on system governance and requirement specification.")
            
            # Assemble a "Longer" summary
            full_summary = "\n\n".join(summary_blocks)
            brd.ai_summary = full_summary + "\n\n(Deep Scan completed by RIFTS-X Core Intelligence)"
            
            # Better highlights (proper nouns/capitalized sequences)
            highlights = re.findall(r'\b([A-Z][a-z]+(?: [A-Z][a-z]+)+)\b', text)
            filtered_highlights = []
            for h in highlights:
                if len(h) > 10 and h not in filtered_highlights:
                    filtered_highlights.append(h)
            
            brd.ai_highlights = filtered_highlights[:6] if filtered_highlights else ["Strategic Alignment", "Technical Compliance", "Operational Readiness"]
            
            brd.save(update_fields=['ai_summary', 'ai_highlights'])
            messages.success(request, "RIFTS-X Intelligence Deep Scan completed successfully!")
        else:
            messages.warning(request, "RIFTS-X could not extract enough text for a Deep Scan.")
    except Exception as e:
        messages.error(request, f"RIFTS-X analysis failed: {str(e)}")
        
    return redirect('brd-detail', pk=pk)

@login_required
@csrf_exempt
def brd_ai_chat(request, pk):
    """JSON endpoint for RIFTS-X document-specific Q&A."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
        
    brd = get_object_or_404(BRD, pk=pk)
    user_msg = request.POST.get('message', '').lower()
    
    from registry.services.document_signer import extract_text_from_document
    text = extract_text_from_document(brd).lower()
    
    # Context-aware response searching the document text
    response = ""
    
    if len(user_msg) < 3:
        response = "I'm RIFTS-X. How can I assist you with this document today?"
    else:
        # Try to find the sentence containing the keyword
        keywords = user_msg.split()
        sentences = [s.strip() for s in text.replace('\n', '. ').split('.') if len(s) > 10]
        
        found_sentences = []
        for s in sentences:
            if any(k in s for k in keywords if len(k) > 3):
                found_sentences.append(s)
        
        if found_sentences:
            response = f"Based on my analysis of the document: '...{found_sentences[0]}...'"
        else:
            # Fallback logic
            if 'budget' in user_msg or 'cost' in user_msg:
                response = "I couldn't find a specific budget figure in the main text, but such details are typically in the financial annexures."
            elif 'who' in user_msg or 'approver' in user_msg:
                response = f"The approval matrix for '{brd.title}' includes PMT, HODs, and the Board of Executives."
            else:
                response = f"I've scanned the document for '{user_msg}', but I don't see a direct reference. However, the general focus is on {brd.ai_summary or 'project initiation'}."
        
    return JsonResponse({'response': response})

    # Fetch saved signature
    from registry.models import UserSignature
    user_sig = UserSignature.objects.filter(user=request.user).first()
    saved_signature = user_sig.signature_data if user_sig else None

    from registry.services.document_signer import render_document_to_images
    pages = render_document_to_images(brd)
    
    return render(request, 'governance/visual_signer.html', {
        'brd': brd,
        'pages': pages,
        'saved_signature': saved_signature,
        'today_date': timezone.now().strftime('%Y-%m-%d')
    })


@login_required
def reject_brd(request, pk):
    """Reject a BRD at the current approval level."""
    brd = get_object_or_404(models.BRD, pk=pk)

    level_map = {
        'Awaiting PMT':   'PMT',
        'Awaiting HODs':  'HODs',
        'Awaiting Board': 'Board',
    }
    current_level = level_map.get(brd.status)
    if not current_level:
        messages.error(request, 'This BRD cannot be rejected at its current status.')
        return redirect('brd-detail', pk=pk)

    approver = brd.approvers.filter(user=request.user, level=current_level).first()
    if not approver and not request.user.is_superuser:
        messages.error(request, 'Access denied: You are not an approver at this level.')
        return redirect('brd-detail', pk=pk)

    if request.method == 'POST':
        reason = request.POST.get('rejection_reason', '').strip()
        brd.status = 'Rejected'
        brd.rejection_reason = reason
        brd.rejected_by = request.user
        brd.rejected_at = timezone.now()
        brd.save(update_fields=['status', 'rejection_reason', 'rejected_by', 'rejected_at', 'updated_at'])
        
        # Notify initiator
        if brd.initiator.email:
            try:
                from django.core.mail import send_mail
                send_mail(
                    f"BRD Rejected: '{brd.title}'",
                    f"Hello,\n\nYour BRD '{brd.title}' was rejected by {request.user.get_full_name()}.\nReason: {reason}\n\nPlease review the feedback.",
                    None,
                    [brd.initiator.email],
                    fail_silently=True
                )
            except Exception: pass
            
        messages.warning(request, f'BRD "{brd.title}" has been rejected.')
        return redirect('brd-list')

    return redirect('brd-detail', pk=pk)


@login_required
def download_brd(request, pk):
    """Serve the BRD document file for download."""
    import os
    from django.http import FileResponse, Http404
    brd = get_object_or_404(models.BRD, pk=pk)

    # Security: only initiator, assigned approvers, or admins can download
    is_approver = brd.approvers.filter(user=request.user).exists()
    if not (request.user == brd.initiator or is_approver or request.user.is_superuser):
        security = getattr(request.user, 'security_profile', None)
        role = security.role if security else ''
        
        allowed_roles = ['Project Management Team', 'HODs', 'Board of Executives', 'Portfolio Admin']
        if role == 'Project Leader' and brd.forwarded_to_pl_at:
            pass # Allowed
        elif role not in allowed_roles:
            messages.error(request, 'Access denied.')
            return redirect('brd-list')

    doc = brd.signed_document if brd.signed_document else brd.document
    if not doc:
        logger.error(f"DOWNLOAD FAILED: No document field populated for BRD {pk}")
        raise Http404('Document not found.')

    logger.info(f"SERVING DOWNLOAD for BRD {pk}: {doc.name} (Size: {doc.size if hasattr(doc, 'size') else 'unknown'})")

    try:
        response = FileResponse(doc.open('rb'), as_attachment=True, filename=os.path.basename(doc.name))
        return response
    except FileNotFoundError:
        raise Http404('File not found on disk.')

@login_required
def edit_brd(request, pk):
    """Edit an existing BRD."""
    brd = get_object_or_404(models.BRD, pk=pk)

    if request.user != brd.initiator and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to edit this BRD.')
        return redirect('brd-detail', pk=pk)

    if request.method == 'POST':
        brd.title = request.POST.get('title', brd.title)
        brd.description = request.POST.get('description', brd.description)
        
        if 'document' in request.FILES:
            brd.document = request.FILES['document']
            brd.signed_document = None
            brd.status = 'Awaiting PMT'
            brd.rejection_reason = ''
            brd.rejected_by = None
            brd.rejected_at = None
            # reset signatures
            brd.pmt_signatures_count = 0
            brd.pmt_quorum_met = False
            brd.hods_signatures_count = 0
            brd.hods_quorum_met = False
            brd.board_signatures_count = 0
            brd.board_quorum_met = False
            brd.signatures.all().delete()
            brd.save()
            messages.success(request, 'BRD updated successfully and signatures reset.')
        else:
            brd.save()
            messages.success(request, 'BRD details updated successfully.')
            
        return redirect('brd-detail', pk=pk)

    return render(request, 'governance/brd_edit.html', {'brd': brd})

@login_required
def delete_brd(request, pk):
    """Delete a BRD."""
    brd = get_object_or_404(models.BRD, pk=pk)

    if request.user != brd.initiator and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to delete this BRD.')
        return redirect('brd-detail', pk=pk)

    if request.method == 'POST':
        brd.delete()
        messages.success(request, 'BRD deleted successfully.')
        return redirect('brd-list')
        
    return redirect('brd-detail', pk=pk)

@login_required
def brd_forward_to_pl(request, pk):
    """Forward an approved BRD to the Project Leader (PL)."""
    from django.utils import timezone
    from django.core.mail import send_mail
    from registry.models import UserSecurity
    
    brd = get_object_or_404(models.BRD, pk=pk)
    
    # 1. Validation
    if brd.status != 'Approved':
        messages.error(request, "Only fully Approved BRDs can be forwarded to the Project Leader.")
        return redirect('brd-detail', pk=pk)
        
    if request.user != brd.initiator and not request.user.is_superuser:
        messages.error(request, "Only the initiator or an admin can forward this BRD.")
        return redirect('brd-detail', pk=pk)

    # 2. Identify Project Leaders
    pls = UserSecurity.objects.filter(role='Project Leader')
    pl_emails = [s.user.email for s in pls if s.user.email]
    
    if not pl_emails:
        messages.warning(request, "No users with the 'Project Leader' role were found to receive this notification.")
        # We still mark it as forwarded so the UI updates
        
    # 3. Update Status and Notify
    brd.forwarded_to_pl_at = timezone.now()
    brd.save(update_fields=['forwarded_to_pl_at'])
    
    if pl_emails:
        brd_url = request.build_absolute_uri(f'/brd/{brd.pk}/')
        try:
            send_mail(
                f"Approved BRD Forwarded: '{brd.title}'",
                f"Hello,\\n\\nThe approved BRD '{brd.title}' has been forwarded to you for your attention.\\n\\nYou can review the signed document here:\\n{brd_url}\\n\\nInitiated by: {brd.initiator.get_full_name() or brd.initiator.username}",
                None, pl_emails, fail_silently=True
            )
            messages.success(request, f"BRD successfully forwarded to {len(pl_emails)} Project Leader(s).")
        except Exception as e:
            messages.warning(request, f"BRD marked as forwarded, but email notification failed: {e}")
    else:
        messages.success(request, "BRD marked as forwarded to Project Leader.")

    return redirect('brd-detail', pk=pk)


# ─────────────────────────────────────────────────────────────────────────────
#  ENHANCED SUPPLY REQUISITION VIEWS
# ─────────────────────────────────────────────────────────────────────────────

def _get_user_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')


def _get_batch_send_time():
    """Return the next batch window datetime (10:00 AM, 1:00 PM, or 4:00 PM local time)."""
    from django.utils import timezone as tz
    import datetime
    now = tz.localtime(tz.now())
    today = now.date()
    windows = [
        datetime.time(10, 0),
        datetime.time(13, 0),
        datetime.time(16, 0),
    ]
    for window in windows:
        window_dt = tz.make_aware(datetime.datetime.combine(today, window))
        if now < window_dt:
            return window_dt
    # All windows passed today — schedule for 10 AM tomorrow
    tomorrow = today + datetime.timedelta(days=1)
    return tz.make_aware(datetime.datetime.combine(tomorrow, windows[0]))


def _queue_or_send_notification(requisition, recipient_user, stage_label, sign_url):
    """Queue an email for the next batch window, or send immediately if urgent."""
    if requisition.is_urgent:
        return _notify_supply_requisition(requisition, recipient_user, stage_label, sign_url)
    # Queue it
    scheduled = _get_batch_send_time()
    models.RequisitionEmailQueue.objects.create(
        requisition=requisition,
        recipient_user=recipient_user,
        stage_label=stage_label,
        sign_url=sign_url,
        scheduled_send_time=scheduled,
    )
    return True


def _flush_email_queue():
    """Dispatch all queued emails whose scheduled_send_time has passed. Call this during any request."""
    from django.utils import timezone as tz
    pending = models.RequisitionEmailQueue.objects.filter(sent=False, scheduled_send_time__lte=tz.now())
    for entry in pending:
        success = _notify_supply_requisition(entry.requisition, entry.recipient_user, entry.stage_label, entry.sign_url)
        if success:
            entry.sent = True
            entry.sent_at = tz.now()
            entry.save()


def _notify_supply_requisition(requisition, stage_user, stage_label, sign_url):
    """Send email notification to the next signatory. Returns True on success, False on failure."""
    requester_name = requisition.requester.get_full_name() or requisition.requester.username
    urgent_tag = '[URGENT] ' if requisition.is_urgent else ''
    subject = f"[RIFTS-X] {urgent_tag}Purchase Requisition {requisition.ref_number} – Action Required: {stage_label}"
    body = (
        f"Dear {stage_user.get_full_name() or stage_user.username},\n\n"
        f"{'\u26a0\ufe0f URGENT: This requisition requires immediate attention.\n\n' if requisition.is_urgent else ''}"
        f"A Purchase Requisition ({requisition.ref_number}) submitted by {requester_name} "
        f"requires your action as {stage_label}.\n\n"
        f"Purpose: {requisition.purpose}\n"
        f"Total Amount: {requisition.grand_total}\n\n"
        f"Please click the link below to review and sign:\n"
        f"{sign_url}\n\n"
        f"This is an automated notification from RIFTS-X. Please do not reply.\n"
    )
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [stage_user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {stage_user.email}: {e}")
        return False


def _notify_rejection(requisition, notify_user, stage_label, rejection_reason, action_url):
    """Send an immediate rejection notification email to the previous stage actor."""
    requester_name = requisition.requester.get_full_name() or requisition.requester.username
    subject = f"[RIFTS-X] Purchase Requisition {requisition.ref_number} – REJECTED at {stage_label} Stage"
    body = (
        f"Dear {notify_user.get_full_name() or notify_user.username},\n\n"
        f"Purchase Requisition {requisition.ref_number} submitted by {requester_name} "
        f"has been rejected at the current stage.\n\n"
        f"Rejection Reason:\n{rejection_reason}\n\n"
        f"The requisition has been routed back to your stage ({stage_label}).\n"
        f"Please click the link below to review and act:\n"
        f"{action_url}\n\n"
        f"This is an automated notification from RIFTS-X. Please do not reply.\n"
    )
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        send_mail(
            subject, body,
            settings.DEFAULT_FROM_EMAIL,
            [notify_user.email],
            fail_silently=True,
        )
    except Exception as e:
        logger.error(f"Failed to send rejection email to {notify_user.email}: {e}")


@login_required
def supply_requisition_list(request):
    context = context_data(request)
    context['page_title'] = 'Purchase Requisitions'
    context['page'] = 'supply_requisitions'
    if request.user.is_superuser or request.user.is_staff:
        context['requisitions'] = models.SupplyRequisition.objects.all()
    else:
        # Show requisitions the user created or is an approver on
        from django.db.models import Q
        context['requisitions'] = models.SupplyRequisition.objects.filter(
            Q(requester=request.user) |
            Q(supervisor=request.user) |
            Q(dept_manager=request.user) |
            Q(purchasing_officer=request.user)
        ).distinct()
    return render(request, 'supply_requisition_list.html', context)


@login_required
def manage_supply_requisition(request):
    context = context_data(request)
    context['page_title'] = 'New Purchase Requisition'
    context['page'] = 'supply_requisitions'
    all_users = User.objects.filter(is_active=True).order_by('first_name', 'last_name', 'username')
    context['users'] = all_users
    context['budgets'] = models.Budget.objects.all().order_by('-fiscal_year')
    context['departments'] = models.Department.objects.all().order_by('name')

    # Filtered lists for ZRP hierarchy roles
    dd_roles = ['Deputy Director ICT', 'Deputy Director IT', 'Deputy Director Communications']
    dds = User.objects.filter(is_active=True, security_profile__role__in=dd_roles).order_by('first_name', 'last_name', 'username')
    context['deputy_directors'] = dds if dds.exists() else all_users

    chiefs = User.objects.filter(is_active=True, security_profile__role='Chief Director').order_by('first_name', 'last_name', 'username')
    context['chief_directors'] = chiefs if chiefs.exists() else all_users

    # Pass saved signature if exists
    try:
        context['saved_signature'] = request.user.signature_profile.signature_data
    except Exception:
        context['saved_signature'] = None
    return render(request, 'manage_supply_requisition.html', context)


@login_required
def save_supply_requisition(request):
    resp = {'status': 'failed', 'msg': '', 'redirect': ''}
    if request.method != 'POST':
        resp['msg'] = 'Invalid request method.'
        return HttpResponse(json.dumps(resp), content_type='application/json')

    try:
        # Flush any pending queued emails on every requisition request
        try:
            _flush_email_queue()
        except Exception:
            pass

        purpose    = request.POST.get('purpose', '').strip()
        dept_id    = request.POST.get('department')
        budget_id  = request.POST.get('budget_line')
        supervisor_id = request.POST.get('supervisor')
        dept_mgr_id = request.POST.get('dept_manager')
        deputy_director_id = request.POST.get('deputy_director')
        ceo_id     = request.POST.get('ceo')
        purch_id   = request.POST.get('purchasing_officer')
        fin_id     = request.POST.get('finance_officer')
        sig_data   = request.POST.get('requester_signature_data', '').strip()
        is_urgent  = request.POST.get('is_urgent') == 'on'

        if not purpose:
            resp['msg'] = 'Purpose is required.'
            return HttpResponse(json.dumps(resp), content_type='application/json')
        if not supervisor_id:
            resp['msg'] = 'Please select a Supervisor.'
            return HttpResponse(json.dumps(resp), content_type='application/json')
        if not dept_mgr_id:
            resp['msg'] = 'Please select a Department Manager.'
            return HttpResponse(json.dumps(resp), content_type='application/json')
        if not deputy_director_id:
            resp['msg'] = 'Please select a Deputy Director.'
            return HttpResponse(json.dumps(resp), content_type='application/json')
        if not ceo_id:
            resp['msg'] = 'Please select a Chief Director.'
            return HttpResponse(json.dumps(resp), content_type='application/json')
        if not purch_id:
            resp['msg'] = 'Please select a Purchasing Officer.'
            return HttpResponse(json.dumps(resp), content_type='application/json')
        if not fin_id:
            resp['msg'] = 'Please select a Finance Officer.'
            return HttpResponse(json.dumps(resp), content_type='application/json')

        # Build header
        req = models.SupplyRequisition(
            requester=request.user,
            purpose=purpose,
            status='Pending Supervisor',
            is_urgent=is_urgent,
        )
        if dept_id:
            req.department_id = int(dept_id)
        if budget_id:
            req.budget_line_id = int(budget_id)
        if supervisor_id:
            req.supervisor_id = int(supervisor_id)
        if dept_mgr_id:
            req.dept_manager_id = int(dept_mgr_id)
        if deputy_director_id:
            req.deputy_director_id = int(deputy_director_id)
        if ceo_id:
            req.ceo_id = int(ceo_id)
        if purch_id:
            req.purchasing_officer_id = int(purch_id)
        if fin_id:
            req.finance_officer_id = int(fin_id)

        # Handle optional document upload
        if 'uploaded_document' in request.FILES:
            req.uploaded_document = request.FILES['uploaded_document']

        req.save()

        # Save line items
        descriptions  = request.POST.getlist('item_description[]')
        quantities    = request.POST.getlist('item_quantity[]')
        unit_costs    = request.POST.getlist('item_unit_cost[]')
        annual_budgets = request.POST.getlist('item_annual_budget[]')
        curr_balances = request.POST.getlist('item_current_balance[]')

        for i, desc in enumerate(descriptions):
            if not desc.strip():
                continue
            models.RequisitionItem.objects.create(
                requisition=req,
                description=desc.strip(),
                quantity=int(quantities[i]) if i < len(quantities) else 1,
                unit_cost=float(unit_costs[i]) if i < len(unit_costs) else 0,
                annual_budget=float(annual_budgets[i]) if i < len(annual_budgets) else 0,
                current_balance=float(curr_balances[i]) if i < len(curr_balances) else 0,
                order=i + 1,
            )

        # Create requester signatory record (pre-signed)
        from django.utils import timezone as tz
        signatory = models.RequisitionSignatory.objects.create(
            requisition=req,
            stage='requester',
            user=request.user,
            signature_data=sig_data if sig_data else None,
            date_signed=tz.now() if sig_data else None,
            is_signed=bool(sig_data),
            ip_address=_get_user_ip(request),
        )

        # Handle uploaded signature image for requester
        if 'requester_sig_upload' in request.FILES:
            signatory.uploaded_signature = request.FILES['requester_sig_upload']
            signatory.is_signed = True
            signatory.date_signed = tz.now()
            signatory.save()

        # Save requester signature to profile (optional)
        if sig_data and request.POST.get('save_to_profile') == 'on':
            us, _ = models.UserSignature.objects.get_or_create(user=request.user)
            us.signature_data = sig_data
            us.save()

        # Notify Supervisor (queue or immediate)
        if req.supervisor and req.supervisor.email:
            try:
                from django.conf import settings as dj_settings
                base_url = getattr(dj_settings, 'RIFTSX_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
                sign_url = f"{base_url}/registry/supply_requisition/{req.pk}/sign/supervisor/"
            except Exception:
                sign_url = f"/registry/supply_requisition/{req.pk}/sign/supervisor/"
            sent = _queue_or_send_notification(req, req.supervisor, 'Supervisor', sign_url)
            if not sent:
                messages.warning(request, f"Note: Daily email limits exceeded. Direct signing link: {sign_url}")
            elif req.is_urgent:
                pass  # sent immediately
            else:
                messages.info(request, "Notification queued for the next batch window.")

        resp['status']   = 'success'
        resp['redirect'] = f'/registry/supply_requisition/{req.pk}/'
        messages.success(request, f'Purchase Requisition {req.ref_number} submitted successfully.')

    except Exception as e:
        resp['msg'] = str(e)

    return HttpResponse(json.dumps(resp), content_type='application/json')


@login_required
def view_supply_requisition(request, pk):
    req = get_object_or_404(models.SupplyRequisition, pk=pk)
    # Access control: requester, approvers, staff
    allowed = (
        request.user == req.requester or
        request.user == req.supervisor or
        request.user == req.dept_manager or
        request.user == req.ceo or
        request.user == req.purchasing_officer or
        request.user == req.finance_officer or
        request.user.is_staff or
        request.user.is_superuser
    )
    if not allowed:
        messages.error(request, 'Access denied.')
        return redirect('supply-requisition-list')

    context = context_data(request)
    context['page_title'] = f'Requisition {req.ref_number}'
    context['page'] = 'supply_requisitions'
    context['req'] = req
    context['items'] = req.items.all()
    context['quotations'] = req.quotations.all()
    context['signatories'] = req.signatories.all()

    # Determine what action the current user can take
    context['can_sign_supervisor'] = (
        request.user == req.supervisor and
        req.status == 'Pending Supervisor' and
        not req.signatories.filter(stage='supervisor', is_signed=True).exists()
    )
    context['can_sign_dept'] = (
        request.user == req.dept_manager and
        req.status == 'Pending Dept' and
        not req.signatories.filter(stage='dept_manager', is_signed=True).exists()
    )
    context['can_sign_purchasing'] = (
        request.user == req.purchasing_officer and
        req.status == 'Pending Purchasing' and
        not req.signatories.filter(stage='purchasing_officer', is_signed=True).exists()
    )
    context['can_sign_requester_review'] = (
        request.user == req.requester and
        req.status == 'Pending Requester Review' and
        not req.signatories.filter(stage='requester_review', is_signed=True).exists()
    )
    context['can_sign_purchasing_review'] = (
        request.user == req.purchasing_officer and
        req.status == 'Pending Purchasing Final' and
        not req.signatories.filter(stage='purchasing_officer_review', is_signed=True).exists()
    )
    context['can_sign_requester'] = (
        request.user == req.requester and
        not req.signatories.filter(stage='requester', is_signed=True).exists()
    )
    context['can_sign_ceo'] = (
        request.user == req.ceo and
        req.status == 'Pending CEO' and
        not req.signatories.filter(stage='ceo', is_signed=True).exists()
    )
    context['can_sign_finance'] = (
        request.user == req.finance_officer and
        req.status == 'Pending Finance' and
        not req.signatories.filter(stage='finance_officer', is_signed=True).exists()
    )
    return render(request, 'view_supply_requisition.html', context)


def get_sig_image_flowable(signatory, width=120, height=45):
    import io
    import base64
    from reportlab.platypus import Image
    
    if signatory.uploaded_signature:
        try:
            return Image(signatory.uploaded_signature.path, width=width, height=height)
        except Exception:
            pass
            
    if signatory.signature_data:
        try:
            data = signatory.signature_data
            if ',' in data:
                data = data.split(',', 1)[1]
            img_bytes = base64.b64decode(data)
            return Image(io.BytesIO(img_bytes), width=width, height=height)
        except Exception:
            pass
            
    return None


def clean_html_text(text):
    if not text:
        return ""
    import html
    return html.escape(str(text)).replace('\n', '<br/>')


def generate_supply_requisition_pdf(req):
    import io
    import os
    import base64
    from django.core.files.base import ContentFile
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle, PageBreak, KeepTogether, Image
    from reportlab.lib.units import cm
    from registry.models import UserSecurity
    from django.conf import settings

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title=f"Purchase Requisition – {req.ref_number}",
    )

    styles = getSampleStyleSheet()

    # ZRP Corporate Colors
    primary_color = colors.HexColor('#003EA6')   # ZRP Blue
    secondary_color = colors.HexColor('#D4AF37') # ZRP Gold
    text_dark = colors.HexColor('#0d1b3e')       # ZRP Slate
    bg_light = colors.HexColor('#f7fafc')
    border_color = colors.HexColor('#e2e8f0')

    title_style = ParagraphStyle(
        'ReqTitle', parent=styles['Title'],
        textColor=primary_color, fontSize=18, leading=22, spaceAfter=8, alignment=0
    )
    meta_style = ParagraphStyle(
        'ReqMeta', parent=styles['Normal'],
        textColor=colors.HexColor('#718096'), fontSize=10, leading=14, spaceAfter=15
    )
    section_heading = ParagraphStyle(
        'SectionHeading', parent=styles['Heading2'],
        textColor=primary_color, fontSize=12, leading=16, spaceBefore=15, spaceAfter=8,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'ReqBody', parent=styles['Normal'],
        textColor=text_dark, fontSize=10, leading=14, spaceAfter=6
    )
    label_style = ParagraphStyle(
        'ReqLabel', parent=styles['Normal'],
        textColor=primary_color, fontSize=10, leading=14, fontName='Helvetica-Bold'
    )

    story = []

    # 1. HEADER — ZRP Logo
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'assets', 'img', 'zrp_crest.png')
    # Fallback: check media root too
    if not os.path.exists(logo_path):
        logo_path = os.path.join(settings.MEDIA_ROOT, 'zrp_logo.png')
    logo_flowable = None
    if os.path.exists(logo_path):
        try:
            logo_flowable = Image(logo_path, width=1.8*cm, height=2.16*cm)
        except Exception:
            pass

    org_name = "Zimbabwe Republic Police"
    system_name = "ZRP Integrated Management System"

    if logo_flowable:
        header_data = [
            [logo_flowable, [
                Paragraph(f"{org_name}", ParagraphStyle('OrgName', parent=styles['Normal'],
                    textColor=primary_color, fontSize=13, fontName='Helvetica-Bold', spaceAfter=2)),
                Paragraph(f"{system_name}", ParagraphStyle('SysName', parent=styles['Normal'],
                    textColor=secondary_color, fontSize=9, spaceAfter=4)),
                Paragraph(f"PURCHASE REQUISITION: {req.ref_number}", title_style),
                Paragraph(f"Date Requested: {req.date_requested.strftime('%d %B %Y, %H:%M')} | Status: {req.get_status_display()}", meta_style)
            ]]
        ]
        header_table = Table(header_data, colWidths=[2.2*cm, 14.8*cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(header_table)
    else:
        story.append(Paragraph(f"PURCHASE REQUISITION: {req.ref_number}", title_style))
        story.append(Paragraph(f"Date Requested: {req.date_requested.strftime('%d %B %Y, %H:%M')} | Status: {req.get_status_display()}", meta_style))

    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=2, color=primary_color, spaceAfter=15))

    # 2. GENERAL DETAILS
    dept_name = req.department.name if req.department else "—"
    budget_name = f"{req.budget_line.department.name} – {req.budget_line.fiscal_year}" if req.budget_line else "—"
    
    details_data = [
        [Paragraph("Department:", label_style), Paragraph(clean_html_text(dept_name), body_style)],
        [Paragraph("Budget Line:", label_style), Paragraph(clean_html_text(budget_name), body_style)],
        [Paragraph("Purpose / Justification:", label_style), Paragraph(clean_html_text(req.purpose), body_style)]
    ]
    
    details_table = Table(details_data, colWidths=[5*cm, 12*cm])
    details_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 15))

    # 3. REQUISITION ITEMS TABLE
    story.append(Paragraph("Requisition Items", section_heading))
    items_data = [[
        Paragraph("<b>#</b>", label_style),
        Paragraph("<b>Description</b>", label_style),
        Paragraph("<b>Qty</b>", label_style),
        Paragraph("<b>Unit Cost</b>", label_style),
        Paragraph("<b>Line Total</b>", label_style),
        Paragraph("<b>Ann. Budget</b>", label_style),
        Paragraph("<b>Curr. Bal.</b>", label_style),
        Paragraph("<b>Budget Bal.</b>", label_style)
    ]]
    
    for idx, item in enumerate(req.items.all(), 1):
        budget_bal = item.current_balance - (item.quantity * item.unit_cost)
        bal_color_str = "red" if budget_bal < 0 else "green"
        items_data.append([
            Paragraph(str(idx), body_style),
            Paragraph(clean_html_text(item.description), body_style),
            Paragraph(str(item.quantity), body_style),
            Paragraph(f"${item.unit_cost:.2f}", body_style),
            Paragraph(f"${(item.quantity * item.unit_cost):.2f}", body_style),
            Paragraph(f"${item.annual_budget:.2f}", body_style),
            Paragraph(f"${item.current_balance:.2f}", body_style),
            Paragraph(f"<font color='{bal_color_str}'>${budget_bal:.2f}</font>", body_style)
        ])
        
    items_data.append([
        Paragraph("<b>Grand Total:</b>", label_style),
        Paragraph("", body_style),
        Paragraph("", body_style),
        Paragraph("", body_style),
        Paragraph(f"<b>${req.grand_total:.2f}</b>", label_style),
        Paragraph("", body_style),
        Paragraph("", body_style),
        Paragraph("", body_style)
    ])
    
    items_table = Table(items_data, colWidths=[0.8*cm, 5.2*cm, 0.8*cm, 1.8*cm, 2.1*cm, 2.1*cm, 2.1*cm, 2.1*cm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), bg_light),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('SPAN', (0, -1), (3, -1)),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 15))

    # 4. BID ANALYSIS
    if req.bid_analysis:
        story.append(Paragraph("Bid Analysis Notes", section_heading))
        story.append(Paragraph(clean_html_text(req.bid_analysis), body_style))
        story.append(Spacer(1, 15))

    # 5. SUPPLIERS CONTACTED FOR QUOTATIONS
    quotations = req.quotations.all()
    if quotations.exists():
        story.append(Paragraph("Suppliers Contacted for Quotation", section_heading))
        quotes_data = [[
            Paragraph("<b>#</b>", label_style),
            Paragraph("<b>Supplier Details</b>", label_style),
            Paragraph("<b>Quoted Amount</b>", label_style),
            Paragraph("<b>Status</b>", label_style),
            Paragraph("<b>Notes</b>", label_style)
        ]]
        for idx, q in enumerate(quotations, 1):
            contact_info = f"<b>{clean_html_text(q.supplier_name)}</b>"
            if q.contact_person: contact_info += f"<br/>Contact: {clean_html_text(q.contact_person)}"
            if q.phone: contact_info += f"<br/>Phone: {clean_html_text(q.phone)}"
            if q.email: contact_info += f"<br/>Email: {clean_html_text(q.email)}"
            
            if q.is_chosen:
                status_html = "<font color='green'><b>CHOSEN (Approved)</b></font>"
            else:
                status_html = "<font color='red'><b>Rejected</b></font>"
                
            quotes_data.append([
                Paragraph(str(idx), body_style),
                Paragraph(contact_info, body_style),
                Paragraph(f"${q.quoted_amount:.2f}", body_style),
                Paragraph(status_html, body_style),
                Paragraph(clean_html_text(q.notes or "—"), body_style)
            ])
            
        quotes_table = Table(quotes_data, colWidths=[0.8*cm, 5.2*cm, 2.5*cm, 3.2*cm, 5.3*cm])
        tstyle_cmds = [
            ('BACKGROUND', (0,0), (-1,0), bg_light),
            ('GRID', (0,0), (-1,-1), 0.5, border_color),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
        ]
        for r_idx, q in enumerate(quotations, 1):
            if q.is_chosen:
                tstyle_cmds.append(('BACKGROUND', (0, r_idx), (-1, r_idx), colors.HexColor('#e6fffa')))
        quotes_table.setStyle(TableStyle(tstyle_cmds))
        story.append(quotes_table)
        story.append(Spacer(1, 15))

    # 6. DEDICATED SIGNATORIES PAGE
    story.append(PageBreak())
    story.append(Paragraph("APPROVAL CHAIN & SIGNATORIES STATUS", title_style))
    story.append(Paragraph("Dedicated Verification Page", meta_style))
    story.append(HRFlowable(width="100%", thickness=2, color=primary_color, spaceAfter=15))

    stages_order = ['requester', 'supervisor', 'dept_manager', 'purchasing_officer', 'requester_review', 'purchasing_officer_review', 'ceo', 'finance_officer']
    signatories_by_stage = {sig.stage: sig for sig in req.signatories.all()}
    
    stage_titles = {
        'requester': 'Stage 1: Requester Submission',
        'supervisor': 'Stage 2: Supervisor Approval',
        'dept_manager': 'Stage 3: Department Manager Approval',
        'purchasing_officer': 'Stage 4: Purchasing Officer (Bid Analysis)',
        'requester_review': 'Stage 5: Requester Review & Signature',
        'purchasing_officer_review': 'Stage 6: Purchasing Officer (Final Review)',
        'ceo': 'Stage 7: Chief Director Approval',
        'finance_officer': 'Stage 8: Finance Officer Payment Process',
    }

    for stage_key in stages_order:
        sig = signatories_by_stage.get(stage_key)
        
        if sig:
            user = sig.user
            status_text = f"<font color='green'><b>Signed</b></font> on {sig.date_signed.strftime('%d %B %Y, %H:%M') if sig.date_signed else '—'}"
            comments_text = sig.comments or "No comments."
            ip_text = f"IP Address: {sig.ip_address or '—'}"
        else:
            status_text = "<font color='orange'><b>Pending / Not Signed</b></font>"
            comments_text = "—"
            ip_text = ""
            if stage_key == 'requester':
                user = req.requester
            elif stage_key == 'supervisor':
                user = req.supervisor
            elif stage_key == 'dept_manager':
                user = req.dept_manager
            elif stage_key == 'purchasing_officer':
                user = req.purchasing_officer
            elif stage_key == 'requester_review':
                user = req.requester
            elif stage_key == 'purchasing_officer_review':
                user = req.purchasing_officer
            elif stage_key == 'ceo':
                user = req.ceo
            elif stage_key == 'finance_officer':
                user = req.finance_officer
            else:
                user = None

        user_name = user.get_full_name() or user.username if user else "Not assigned"
        user_username = f"({user.username})" if user else ""
        
        job_title = "—"
        position = "—"
        if user:
            profile = getattr(user, 'security_profile', None)
            if profile:
                job_title = profile.job_title or "—"
                position = profile.position or "—"

        sig_details_html = (
            f"<b>Name:</b> {clean_html_text(user_name)} {clean_html_text(user_username)}<br/>"
            f"<b>Job Title:</b> {clean_html_text(job_title)} | <b>Position:</b> {clean_html_text(position)}<br/>"
            f"<b>Status:</b> {status_text}<br/>"
            f"<b>Comments:</b> {clean_html_text(comments_text)}<br/>"
            f"{ip_text}"
        )

        sig_img = None
        if sig and sig.is_signed:
            sig_img = get_sig_image_flowable(sig)

        sig_block_data = [
            [Paragraph(sig_details_html, body_style), sig_img or Paragraph("<i>No Signature Image</i>", body_style)]
        ]
        
        sig_block_table = Table(sig_block_data, colWidths=[11.5*cm, 5.5*cm])
        sig_block_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, border_color),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BACKGROUND', (0,0), (-1,-1), bg_light if sig and sig.is_signed else colors.white),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ]))

        story.append(KeepTogether([
            Paragraph(f"<b>{stage_titles[stage_key]}</b>", section_heading),
            sig_block_table,
            Spacer(1, 10)
        ]))

    doc.build(story)
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return ContentFile(pdf_content, name=f"{req.ref_number}_approved_requisition.pdf")


@login_required
def download_supply_requisition_pdf(request, pk):
    from django.http import HttpResponse
    req = get_object_or_404(models.SupplyRequisition, pk=pk)
    pdf_file = generate_supply_requisition_pdf(req)
    response = HttpResponse(pdf_file.read(), content_type='application/pdf')
    return response


def _bundle_requisition_to_cloud(request, req):
    """
    Bundles all documents, files, quotations, proof of payment, and signatures
    associated with the supply requisition into a dedicated CloudFolder.
    Runs after every approval stage.
    """
    try:
        from registry.models import Department, CloudFolder, CloudFile, CloudFileVersion
        from registry.services.cloud import CloudService
        from django.core.files.base import ContentFile
        import os
        import base64
        import traceback

        dept = req.department or Department.objects.first()
        if not dept:
            return

        # Create a dedicated folder named after the requisition ref number
        cloud_folder = CloudService.get_or_create_folder(
            name=req.ref_number,
            department=dept,
            user=request.user,
            project_context=req.ref_number,
        )

        # 1. Upload the approved/current requisition PDF
        pdf_file = generate_supply_requisition_pdf(req)
        if pdf_file:
            pdf_file.seek(0)
            pdf_name = f"Requisition_{req.ref_number}.pdf"
            CloudService.upload_file(
                folder=cloud_folder,
                uploaded_file=ContentFile(pdf_file.read(), name=pdf_name),
                user=request.user,
                commit_message=f"Requisition PDF (Stage: {req.get_status_display()})",
                is_internal_only=False,
            )

        # 2. Upload the requester's supporting document (if any)
        if req.uploaded_document:
            try:
                req.uploaded_document.seek(0)
                doc_name = os.path.basename(req.uploaded_document.name)
                CloudService.upload_file(
                    folder=cloud_folder,
                    uploaded_file=ContentFile(req.uploaded_document.read(), name=doc_name),
                    user=request.user,
                    commit_message=f"Requester supporting document – {req.ref_number}",
                    is_internal_only=False,
                )
            except Exception as _e:
                logger.error(f"Could not upload supporting doc for {req.ref_number}: {_e}\n{traceback.format_exc()}")

        # 3. Upload each supplier quotation file (if any)
        for q in req.quotations.all():
            if q.quotation_file:
                try:
                    q.quotation_file.seek(0)
                    q_name = f"supplier_{q.order}_{os.path.basename(q.quotation_file.name)}"
                    CloudService.upload_file(
                        folder=cloud_folder,
                        uploaded_file=ContentFile(q.quotation_file.read(), name=q_name),
                        user=request.user,
                        commit_message=f"Quotation – {q.supplier_name} – {req.ref_number}",
                        is_internal_only=False,
                    )
                except Exception as _e:
                    logger.error(f"Could not upload quotation {q.order} for {req.ref_number}: {_e}\n{traceback.format_exc()}")

        # 4. Upload proof of payment (if any)
        if req.proof_of_payment:
            try:
                req.proof_of_payment.seek(0)
                pop_name = os.path.basename(req.proof_of_payment.name)
                CloudService.upload_file(
                    folder=cloud_folder,
                    uploaded_file=ContentFile(req.proof_of_payment.read(), name=pop_name),
                    user=request.user,
                    commit_message=f"Proof of Payment – {req.ref_number}",
                    is_internal_only=False,
                )
            except Exception as _e:
                logger.error(f"Could not upload proof of payment for {req.ref_number}: {_e}\n{traceback.format_exc()}")

        # 5. Upload signature images (uploaded or drawn) from all current signatories
        for sig in req.signatories.filter(is_signed=True):
            if sig.uploaded_signature:
                try:
                    sig.uploaded_signature.seek(0)
                    sig_name = f"signature_uploaded_{sig.stage}.png"
                    CloudService.upload_file(
                        folder=cloud_folder,
                        uploaded_file=ContentFile(sig.uploaded_signature.read(), name=sig_name),
                        user=request.user,
                        commit_message=f"Uploaded Signature – {sig.get_stage_display()} – {req.ref_number}",
                        is_internal_only=False,
                    )
                except Exception as _e:
                    logger.error(f"Could not upload signature image for {sig.stage}: {_e}\n{traceback.format_exc()}")
            elif sig.signature_data:
                try:
                    data_str = sig.signature_data
                    if ',' in data_str:
                        data_str = data_str.split(',')[1]
                    # Fix padding if length is not a multiple of 4
                    missing_padding = len(data_str) % 4
                    if missing_padding:
                        data_str += '=' * (4 - missing_padding)
                    img_data = base64.b64decode(data_str)
                    sig_name = f"signature_drawn_{sig.stage}.png"
                    CloudService.upload_file(
                        folder=cloud_folder,
                        uploaded_file=ContentFile(img_data, name=sig_name),
                        user=request.user,
                        commit_message=f"Drawn Signature – {sig.get_stage_display()} – {req.ref_number}",
                        is_internal_only=False,
                    )
                except Exception as _e:
                    logger.error(f"Could not upload drawn signature image for {sig.stage}: {_e}\n{traceback.format_exc()}")

    except Exception as _err:
        logger.error(f"Auto-bundle failed for requisition {req.ref_number}: {_err}\n{traceback.format_exc()}")


@login_required
def sign_supply_requisition(request, pk, stage):
    # Flush queued emails on every signing request
    try:
        _flush_email_queue()
    except Exception:
        pass

    req = get_object_or_404(models.SupplyRequisition, pk=pk)

    # Map each stage → the user authorised to act
    stage_user_map = {
        'requester':                 req.requester,
        'supervisor':                req.supervisor,
        'dept_manager':              req.dept_manager,
        'deputy_director':           req.deputy_director,
        'purchasing_officer':        req.purchasing_officer,
        'requester_review':          req.requester,          # Requester signs again after PO
        'purchasing_officer_review': req.purchasing_officer, # PO second pass
        'ceo':                       req.ceo,
        'finance_officer':           req.finance_officer,
    }
    # Map each stage → the status that must be active
    stage_status_required = {
        'requester':                 'Pending Requester',
        'supervisor':                'Pending Supervisor',
        'dept_manager':              'Pending Dept',
        'deputy_director':           'Pending Deputy Director',
        'purchasing_officer':        'Pending Purchasing',
        'requester_review':          'Pending Requester Review',
        'purchasing_officer_review': 'Pending Purchasing Final',
        'ceo':                       'Pending CEO',
        'finance_officer':           'Pending Finance',
    }

    if stage not in stage_user_map:
        messages.error(request, 'Invalid signing stage.')
        return redirect('supply-requisition-list')

    # ── Block signing of permanently rejected requisitions ────────────────
    if req.status == 'Rejected':
        messages.error(request, f'Requisition {req.ref_number} has been rejected and is closed. '
                                 f'Please submit a new requisition.')
        return redirect('supply-requisition-view', pk=pk)

    expected_user = stage_user_map[stage]
    # Strict: ONLY the exactly assigned officer may sign. No superuser bypass for accountability.
    if request.user != expected_user:
        assigned_name = expected_user.get_full_name() if expected_user else 'the assigned officer'
        messages.error(
            request,
            f'Access Denied. Only {assigned_name} is authorised to sign at the "{stage.replace("_"," ")}" stage. '
            f'This action has been logged for audit purposes.'
        )
        return redirect('supply-requisition-view', pk=pk)

    if req.status != stage_status_required.get(stage, ''):
        messages.warning(request, f'This requisition is not currently awaiting a {stage.replace("_", " ")} signature.')
        return redirect('supply-requisition-view', pk=pk)

    if request.method == 'POST':
        from django.utils import timezone as tz
        sig_data      = request.POST.get('signature_data', '').strip()
        comments      = request.POST.get('comments', '').strip()
        date_received = request.POST.get('date_received', '').strip()
        purchase_order = request.POST.get('purchase_order', '').strip()
        action        = request.POST.get('action', 'approve')  # 'approve' or 'reject'

        # ── Handle Rejection — PERMANENT, no rollback ────────────────────────
        if action == 'reject':
            rejection_reason = request.POST.get('rejection_reason', '').strip()
            if not rejection_reason:
                messages.error(request, 'Please provide a reason for rejection.')
                return redirect('supply-requisition-sign', pk=pk, stage=stage)

            from django.utils import timezone as tz
            # Stage label for audit trail
            stage_labels = {
                'supervisor':                'Supervisor',
                'dept_manager':              'Department Manager',
                'deputy_director':           'Deputy Director',
                'purchasing_officer':        'Purchasing Officer (Bid Analysis)',
                'requester_review':          'Requester Review',
                'purchasing_officer_review': 'Purchasing Officer (Final Review)',
                'ceo':                       'Chief Director',
                'finance_officer':           'Finance Officer',
            }
            rejected_stage_label = stage_labels.get(stage, stage)

            # Permanently lock the requisition
            req.status           = 'Rejected'
            req.rejection_reason = rejection_reason
            req.rejected_by      = request.user
            req.rejected_at      = tz.now()
            req.rejected_stage   = stage
            req.save()

            # Always notify the original requester
            try:
                from django.conf import settings as dj_settings
                base_url = getattr(dj_settings, 'RIFTSX_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
                notify_url = f"{base_url}/registry/supply_requisition/{req.pk}/"
            except Exception:
                notify_url = f"/registry/supply_requisition/{req.pk}/"

            _notify_rejection(req, req.requester, 'Requester', rejection_reason, notify_url)

            messages.error(
                request,
                f'Requisition {req.ref_number} has been REJECTED at the {rejected_stage_label} stage. '
                f'It is now closed. The requester must submit a new requisition.'
            )
            return redirect('supply-requisition-view', pk=pk)

        # ── Signature required for approval ──────────────────────────────────
        if not sig_data and 'sig_upload' not in request.FILES:
            messages.error(request, 'Please provide a signature (draw or upload).')
            return redirect('supply-requisition-sign', pk=pk, stage=stage)

        # ── Purchasing Officer (Bid Analysis) stage specifics ─────────────────
        if stage == 'purchasing_officer':
            bid_analysis = request.POST.get('bid_analysis', '').strip()
            if not bid_analysis:
                messages.error(request, 'Bid analysis is required.')
                return redirect('supply-requisition-sign', pk=pk, stage=stage)
            req.bid_analysis = bid_analysis
            req.save()

            # Update item financials (PO fills in unit costs, budgets, balances)
            for item in req.items.all():
                item_pk = str(item.pk)
                new_unit_cost = request.POST.get(f'item_unit_cost_{item_pk}', '')
                new_annual_budget = request.POST.get(f'item_annual_budget_{item_pk}', '')
                new_current_balance = request.POST.get(f'item_current_balance_{item_pk}', '')
                changed = False
                if new_unit_cost:
                    item.unit_cost = float(new_unit_cost)
                    changed = True
                if new_annual_budget:
                    item.annual_budget = float(new_annual_budget)
                    changed = True
                if new_current_balance:
                    item.current_balance = float(new_current_balance)
                    changed = True
                if changed:
                    item.save()

            # Save supplier quotations (clears old, saves new)
            req.quotations.all().delete()
            sup_names    = request.POST.getlist('supplier_name[]')
            sup_contacts = request.POST.getlist('supplier_contact[]')
            sup_phones   = request.POST.getlist('supplier_phone[]')
            sup_emails   = request.POST.getlist('supplier_email[]')
            sup_amounts  = request.POST.getlist('supplier_amount[]')
            sup_notes    = request.POST.getlist('supplier_notes[]')
            chosen_idx   = request.POST.get('chosen_supplier', '')

            for i, sname in enumerate(sup_names[:5]):
                if not sname.strip():
                    continue
                is_chosen = (str(i) == str(chosen_idx))
                quote = models.SupplierQuotation.objects.create(
                    requisition=req,
                    supplier_name=sname.strip(),
                    contact_person=sup_contacts[i] if i < len(sup_contacts) else '',
                    phone=sup_phones[i] if i < len(sup_phones) else '',
                    email=sup_emails[i] if i < len(sup_emails) else '',
                    quoted_amount=float(sup_amounts[i]) if i < len(sup_amounts) and sup_amounts[i] else 0,
                    notes=sup_notes[i] if i < len(sup_notes) else '',
                    order=i + 1,
                    is_chosen=is_chosen,
                )
                file_key = f'supplier_file_{i}'
                if file_key in request.FILES:
                    quote.quotation_file = request.FILES[file_key]
                    quote.save()

        # ── Finance Officer stage specifics ───────────────────────────────────
        if stage == 'finance_officer':
            payment_status = request.POST.get('payment_status', 'Pending')
            proof_file = request.FILES.get('proof_of_payment')

            if payment_status == 'Paid' and not proof_file and not req.proof_of_payment:
                messages.error(request, 'Proof of Payment is required when marking as Paid.')
                return redirect('supply-requisition-sign', pk=pk, stage=stage)

            req.payment_status = payment_status
            if proof_file:
                req.proof_of_payment = proof_file
            req.save()

        # Get or create signatory record
        signatory, _ = models.RequisitionSignatory.objects.get_or_create(
            requisition=req,
            stage=stage,
            defaults={'user': request.user},
        )
        signatory.user = request.user
        signatory.signature_data = sig_data if sig_data else None
        signatory.date_signed = tz.now()
        signatory.is_signed = True
        signatory.comments = comments
        signatory.ip_address = _get_user_ip(request)

        if stage == 'purchasing_officer':
            if date_received:
                signatory.date_received = date_received
            signatory.purchase_order = purchase_order if purchase_order else None

        if 'sig_upload' in request.FILES:
            signatory.uploaded_signature = request.FILES['sig_upload']

        signatory.save()

        # Save to user signature profile (optional)
        if sig_data and request.POST.get('save_to_profile') == 'on':
            us, _ = models.UserSignature.objects.get_or_create(user=request.user)
            us.signature_data = sig_data
            us.save()

        # ── Advance Workflow ──────────────────────────────────────────────────
        try:
            from django.conf import settings as dj_settings
            base_url = getattr(dj_settings, 'RIFTSX_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
        except Exception:
            base_url = 'http://127.0.0.1:8000'

        if stage == 'requester':
            # First submission – go to Supervisor
            req.status = 'Pending Supervisor'
            req.save()
            if req.supervisor and req.supervisor.email:
                sign_url = f"{base_url}/registry/supply_requisition/{req.pk}/sign/supervisor/"
                sent = _queue_or_send_notification(req, req.supervisor, 'Supervisor', sign_url)
                if not sent:
                    messages.warning(request, f"Email failed. Direct Link: {sign_url}")

        elif stage == 'supervisor':
            # After Supervisor – go to Dept Manager
            req.status = 'Pending Dept'
            req.save()
            if req.dept_manager and req.dept_manager.email:
                sign_url = f"{base_url}/registry/supply_requisition/{req.pk}/sign/dept_manager/"
                sent = _queue_or_send_notification(req, req.dept_manager, 'Department Manager', sign_url)
                if not sent:
                    messages.warning(request, f"Email failed. Direct Link: {sign_url}")

        elif stage == 'dept_manager':
            # After Dept Manager – go to Deputy Director
            req.status = 'Pending Deputy Director'
            req.save()
            if req.deputy_director and req.deputy_director.email:
                sign_url = f"{base_url}/registry/supply_requisition/{req.pk}/sign/deputy_director/"
                sent = _queue_or_send_notification(req, req.deputy_director, 'Deputy Director', sign_url)
                if not sent:
                    messages.warning(request, f"Email failed. Direct Link: {sign_url}")

        elif stage == 'deputy_director':
            # After Deputy Director – go to Purchasing Officer (Bid Analysis)
            req.status = 'Pending Purchasing'
            req.save()
            if req.purchasing_officer and req.purchasing_officer.email:
                sign_url = f"{base_url}/registry/supply_requisition/{req.pk}/sign/purchasing_officer/"
                sent = _queue_or_send_notification(req, req.purchasing_officer, 'Purchasing Officer (Bid Analysis)', sign_url)
                if not sent:
                    messages.warning(request, f"Email failed. Direct Link: {sign_url}")

        elif stage == 'purchasing_officer':
            # After PO Bid Analysis – send back to Requester for Review
            req.status = 'Pending Requester Review'
            req.save()
            if req.requester.email:
                sign_url = f"{base_url}/registry/supply_requisition/{req.pk}/sign/requester_review/"
                sent = _queue_or_send_notification(req, req.requester, 'Requester (Review & Sign)', sign_url)
                if not sent:
                    messages.warning(request, f"Email failed. Direct Link: {sign_url}")

        elif stage == 'requester_review':
            # Requester approves PO edits – send to PO for Final Review
            req.status = 'Pending Purchasing Final'
            req.save()
            if req.purchasing_officer and req.purchasing_officer.email:
                sign_url = f"{base_url}/registry/supply_requisition/{req.pk}/sign/purchasing_officer_review/"
                sent = _queue_or_send_notification(req, req.purchasing_officer, 'Purchasing Officer (Final Review)', sign_url)
                if not sent:
                    messages.warning(request, f"Email failed. Direct Link: {sign_url}")

        elif stage == 'purchasing_officer_review':
            # PO Final Review – send to Chief Director (CEO)
            req.status = 'Pending CEO'
            req.save()
            if req.ceo and req.ceo.email:
                sign_url = f"{base_url}/registry/supply_requisition/{req.pk}/sign/ceo/"
                sent = _queue_or_send_notification(req, req.ceo, 'Chief Director', sign_url)
                if not sent:
                    messages.warning(request, f"Email failed. Direct Link: {sign_url}")

        elif stage == 'ceo':
            # Chief Director – send to Finance
            req.status = 'Pending Finance'
            req.save()
            if req.finance_officer and req.finance_officer.email:
                sign_url = f"{base_url}/registry/supply_requisition/{req.pk}/sign/finance_officer/"
                sent = _queue_or_send_notification(req, req.finance_officer, 'Finance Officer', sign_url)
                if not sent:
                    messages.warning(request, f"Email failed. Direct Link: {sign_url}")

        elif stage == 'finance_officer':
            req.status = 'Approved'
            req.save()

            # ── Auto-archive: Registry Files (Non-Cloud document index) ──────
            try:
                from registry.models import Category, SubCategory, File
                cat, _ = Category.objects.get_or_create(
                    name='Procurement', defaults={'description': 'Procurement Files'})
                subcat, _ = SubCategory.objects.get_or_create(
                    category=cat, name='Purchase Requisitions',
                    defaults={'description': 'Purchase Requisition Files'})

                pdf_file = generate_supply_requisition_pdf(req)

                if not File.objects.filter(ref_num=req.ref_number).exists():
                    pdf_file.seek(0)
                    File.objects.create(
                        sub_category=subcat,
                        ref_num=req.ref_number,
                        title=f"Purchase Requisition {req.ref_number}",
                        description=(
                            f"Approved Purchase Requisition. "
                            f"Purpose: {req.purpose}. Grand Total: {req.grand_total}."
                        ),
                        file_attachment=pdf_file,
                        current_department=req.department,
                    )
            except Exception as _archive_err:
                logger.error(f"Auto-archive to Registry Files failed for requisition {req.ref_number}: {_archive_err}")

            # ── Notify requester of full approval ───────────────────────────
            if req.requester.email:
                from django.core.mail import send_mail
                from django.conf import settings as dj_settings
                try:
                    send_mail(
                        f'[RIFTS-X] Purchase Requisition {req.ref_number} – Fully Approved',
                        f'Dear {req.requester.get_full_name() or req.requester.username},\n\n'
                        f'Your Purchase Requisition {req.ref_number} has been fully approved by all signatories.\n\n'
                        f'View it here: {base_url}/registry/supply_requisition/{req.pk}/',
                        dj_settings.DEFAULT_FROM_EMAIL,
                        [req.requester.email],
                        fail_silently=False,
                    )
                except Exception:
                    messages.warning(
                        request,
                        "Note: The confirmation email could not be delivered to the requester."
                    )

        # ── Trigger Automatic Bundling into Institutional Folder ─────────────
        _bundle_requisition_to_cloud(request, req)

        messages.success(request, f'Requisition {req.ref_number} signed successfully.')
        return redirect('supply-requisition-view', pk=pk)

    # GET – render signing page
    context = context_data(request)
    stage_labels = {
        'requester':                 'Requested By',
        'supervisor':                'Supervisor Approval',
        'dept_manager':              'Department Manager',
        'deputy_director':           'Deputy Director Approval',
        'purchasing_officer':        'Purchasing Officer (Bid Analysis)',
        'requester_review':          'Requester Review & Sign',
        'purchasing_officer_review': 'Purchasing Officer (Final Review)',
        'ceo':                       'Chief Director Approval',
        'finance_officer':           'Finance Officer',
    }
    context['page_title']   = f'Sign as {stage_labels.get(stage, stage)}'
    context['page']         = 'supply_requisitions'
    context['req']          = req
    context['stage']        = stage
    context['stage_label']  = stage_labels.get(stage, stage)
    context['items']        = req.items.all()
    context['quotations']   = req.quotations.all()
    context['is_purchasing']        = (stage == 'purchasing_officer')
    context['is_purchasing_review'] = (stage == 'purchasing_officer_review')
    context['is_requester_review']  = (stage == 'requester_review')
    context['is_finance']   = (stage == 'finance_officer')
    try:
        context['saved_signature'] = request.user.signature_profile.signature_data
    except Exception:
        context['saved_signature'] = None
    from django.utils import timezone as tz
    context['today_date'] = tz.now().strftime('%d %B %Y')
    return render(request, 'sign_supply_requisition.html', context)


@login_required
def supply_requisition_signatories(request, pk):
    req = get_object_or_404(models.SupplyRequisition, pk=pk)
    allowed = (
        request.user == req.requester or
        request.user == req.supervisor or
        request.user == req.dept_manager or
        request.user == req.deputy_director or
        request.user == req.ceo or
        request.user == req.purchasing_officer or
        request.user == req.finance_officer or
        request.user.is_staff or
        request.user.is_superuser
    )
    if not allowed:
        messages.error(request, 'Access denied.')
        return redirect('supply-requisition-list')

    context = context_data(request)
    context['page_title'] = f'Signatories – {req.ref_number}'
    context['page'] = 'supply_requisitions'
    context['req'] = req
    context['items'] = req.items.all()
    context['quotations'] = req.quotations.all()
    context['signatories'] = req.signatories.all()
    from django.utils import timezone as tz
    context['today_date'] = tz.now().strftime('%d %B %Y')
    return render(request, 'supply_requisition_signatories.html', context)


@login_required
def api_docs(request):
    """
    Renders the RIFTS-X unified API portal and developer/AI agent documentation.
    """
    context = context_data(request)
    context['page_title'] = 'RIFTS-X API Portal & Docs'
    context['page'] = 'api_docs'
    return render(request, 'api_docs.html', context)


@login_required
def download_api_docs(request):
    """
    Generates and downloads the full RIFTS-X API documentation in Markdown format.
    """
    doc_content = """# RIFTS-X Strategic Intelligence Platform API Portal
Comprehensive Integration Reference for System Developers and AI Agents

---

## 1. Authentication & Security
The RIFTS-X REST API enforces token-based authentication. Every API request must include the `Authorization` header containing your API token.

### Obtain API Token
- **Endpoint**: `POST /registry/api/token-auth/`
- **Payload**:
  ```json
  {
    "username": "your_username",
    "password": "your_password"
  }
  ```
- **Response**:
  ```json
  {
    "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
  }
  ```

### Header Convention
Include the token in all subsequent requests:
`Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b`

---

## 2. Guidelines for AI Agents
If you are an agentic LLM/AI workflow orchestrator:
1. **Header Inclusion**: Ensure the `Authorization` header is present in all tool-based HTTP calls.
2. **State Monitoring**: Periodically poll endpoints like `/api/requisitions/` or `/api/brds/` to read updates on approval flows.
3. **Quorum Logic**: Approve BRD levels sequentially (PMT -> HOD -> Board). Once the required approvals are submitted via `/sign/`, the document automatically moves to Approved.
4. **Signature Operations**: Workflows like signing a requisition or BRD expect base64-encoded PNG signature data (`"signature_data": "data:image/png;base64,..."`).

---

## 3. Core API Endpoint Reference

### 3.1. Physical Document Registry
- `GET /registry/api/files/` - List all metadata files.
- `POST /registry/api/files/` - Create a physical registry file entry.
- `GET /registry/api/borrows/` - View document borrowing custody logs.

### 3.2. Cloud Document Vault
- `GET /registry/api/cloud-folders/` - List digital vault folders.
- `GET /registry/api/cloud-files/` - List digital documents.
- `POST /registry/api/cloud-files/` - Upload a new file.

### 3.3. Kanban Projects & Sprints
- `GET /registry/api/projects/` - List all projects.
- `POST /registry/api/project-tasks/` - Create or update a project task.

### 3.4. Supply Requisitions (Workflow Actions)
- `GET /registry/api/requisitions/` - View requisitions.
- `POST /registry/api/requisitions/{id}/sign/` - Sign, approve, or reject a requisition.
  - **Payload for Approval**:
    ```json
    {
      "action": "approve",
      "signature_data": "data:image/png;base64,..."
    }
    ```
  - **Payload for Rejection**:
    ```json
    {
      "action": "reject",
      "rejection_reason": "Provide reason here"
    }
    ```

### 3.5. Business Requirement Documents (BRDs)
- `GET /registry/api/brds/` - View all BRDs.
- `POST /registry/api/brds/{id}/sign/` - Sign a BRD (advancing PMT/HOD/Board approval status).
  - **Payload**:
    ```json
    {
      "action": "approve",
      "signature_data": "data:image/png;base64,..."
    }
    ```

---

## 4. Response Codes
- `200 OK` / `201 Created` - Success.
- `400 Bad Request` - Invalid payload or logic constraint violation.
- `401 Unauthorized` - Token missing or invalid.
- `403 Forbidden` - Insufficient role permissions to access/modify resource.
- `404 Not Found` - Resource does not exist.
"""
    from django.http import HttpResponse
    response = HttpResponse(doc_content, content_type='text/markdown')
    response['Content-Disposition'] = 'attachment; filename="RIFTSX_API_Documentation.md"'
    return response


# ─────────────────────────────────────────────────────────
#  ZRP Document Governance & Movement Controllers
# ─────────────────────────────────────────────────────────

def log_document_action(user, action, file_doc=None, cloud_file=None, details="", request=None):
    """Helper to record a complete audit trail entry for document operations."""
    try:
        ip_addr = request.META.get('REMOTE_ADDR') if request else None
        user_agent = request.META.get('HTTP_USER_AGENT') if request else None
        models.DocumentAuditLog.objects.create(
            user=user if (user and user.is_authenticated) else None,
            file_doc=file_doc,
            cloud_file=cloud_file,
            action=action,
            details=details,
            ip_address=ip_addr,
            user_agent=user_agent
        )
    except Exception as e:
        logger.error(f"Audit log error: {e}")


@login_required
def move_document_view(request, file_id):
    if request.method == 'POST':
        file_obj = get_object_or_404(models.File, pk=file_id)
        if not PermissionService.can_move_file(request.user, file_obj):
            messages.error(request, "Permission Denied: Only Registry Officers or Administrators can move files.")
            return redirect('file_doc-page')

        target_sub_id = request.POST.get('target_sub_category')
        if target_sub_id:
            sub = get_object_or_404(models.SubCategory, pk=target_sub_id)
            old_sub = file_obj.sub_category.name if file_obj.sub_category else "None"
            file_obj.sub_category = sub
            file_obj.last_moved_at = timezone.now()
            file_obj.last_handler = request.user
            file_obj.save()

            log_document_action(
                request.user, 'Move', file_doc=file_obj,
                details=f"Moved from '{old_sub}' to '{sub.category.name} / {sub.name}'",
                request=request
            )
            messages.success(request, f"File '{file_obj.title}' successfully moved to '{sub.category.name} / {sub.name}'.")
    return redirect('file_doc-page')


@login_required
def rename_document_view(request, file_id):
    if request.method == 'POST':
        file_obj = get_object_or_404(models.File, pk=file_id)
        if not PermissionService.can_rename_file(request.user, file_obj):
            messages.error(request, "Permission Denied: You do not have permission to rename this file.")
            return redirect('file_doc-page')

        new_title = request.POST.get('title', '').strip()
        if new_title:
            old_title = file_obj.title
            file_obj.title = new_title
            file_obj.save()

            log_document_action(
                request.user, 'Rename', file_doc=file_obj,
                details=f"Renamed from '{old_title}' to '{new_title}'",
                request=request
            )
            messages.success(request, f"Document successfully renamed to '{new_title}'.")
    return redirect('file_doc-page')


@login_required
def archive_document_view(request, file_id):
    file_obj = get_object_or_404(models.File, pk=file_id)
    if not PermissionService.can_archive_file(request.user, file_obj):
        messages.error(request, "Permission Denied: Only Registry Officers or Administrators can archive documents.")
        return redirect('file_doc-page')

    file_obj.status = '2' # Inactive / Archived
    file_obj.save()

    log_document_action(
        request.user, 'Archive', file_doc=file_obj,
        details=f"Archived by {request.user.username}",
        request=request
    )
    messages.success(request, f"Document '{file_obj.title}' has been moved to Archive.")
    return redirect('file_doc-page')


@login_required
def restore_document_view(request, file_id):
    file_obj = get_object_or_404(models.File, pk=file_id)
    if not PermissionService.can_restore_file(request.user, file_obj):
        messages.error(request, "Permission Denied: Only Registry Officers or Administrators can restore archived documents.")
        return redirect('file_doc-page')

    file_obj.status = '1' # Active
    file_obj.save()

    log_document_action(
        request.user, 'Restore', file_doc=file_obj,
        details=f"Restored from archive by {request.user.username}",
        request=request
    )
    messages.success(request, f"Document '{file_obj.title}' has been restored to Active status.")
    return redirect('file_doc-page')


@login_required
def transition_document_workflow(request, file_id):
    if request.method == 'POST':
        file_obj = get_object_or_404(models.File, pk=file_id)
        target_status = request.POST.get('target_status')
        comments = request.POST.get('comments', '')

        workflow, created = models.DocumentWorkflow.objects.get_or_create(
            file_doc=file_obj,
            defaults={'title': f"Workflow for {file_obj.title}", 'initiator': request.user}
        )

        valid_transitions = ['Initiated', 'Submitted', 'Reviewed', 'Recommended', 'Approved', 'Rejected', 'Implemented', 'Closed']
        if target_status in valid_transitions:
            old_status = workflow.current_status
            workflow.current_status = target_status
            workflow.comments = comments
            if target_status == 'Reviewed': workflow.reviewer = request.user
            elif target_status == 'Recommended': workflow.recommender = request.user
            elif target_status in ['Approved', 'Rejected']: workflow.approver = request.user
            workflow.save()

            action_name = 'Approve' if target_status == 'Approved' else ('Reject' if target_status == 'Rejected' else 'Edit')
            log_document_action(
                request.user, action_name, file_doc=file_obj,
                details=f"Document Workflow status changed from '{old_status}' to '{target_status}'. Comments: {comments}",
                request=request
            )
            messages.success(request, f"Document Workflow updated to '{target_status}'.")
    return redirect('file-digital-twin', pk=file_id)


# ─────────────────────────────────────────────────────────
#  ZRP Minuting & Meeting Action Tracking Module
# ─────────────────────────────────────────────────────────

@login_required
def minuting_dashboard_view(request):
    meetings = models.Meeting.objects.all().order_by('-meeting_date')
    
    # Filtering
    q = request.GET.get('q', '').strip()
    mtype = request.GET.get('type', '').strip()
    status = request.GET.get('status', '').strip()
    
    if q:
        meetings = meetings.filter(Q(title__icontains=q) | Q(location__icontains=q) | Q(agenda_text__icontains=q))
    if mtype:
        meetings = meetings.filter(meeting_type=mtype)
    if status:
        meetings = meetings.filter(approval_status=status)
        
    # Metrics
    total_meetings = models.Meeting.objects.count()
    awaiting_approval = models.Meeting.objects.filter(approval_status__in=['Secretary Review', 'Chairperson Review']).count()
    
    all_actions = models.MeetingActionItem.objects.all()
    outstanding_actions = all_actions.filter(status__in=['Pending', 'In Progress']).count()
    completed_actions = all_actions.filter(status='Completed').count()
    overdue_actions = all_actions.filter(status='Overdue').count()
    
    total_actions_count = all_actions.count()
    completion_rate = round((completed_actions / total_actions_count * 100), 1) if total_actions_count > 0 else 0.0
    
    users = User.objects.filter(is_active=True).order_by('username')
    
    context = {
        'page_title': 'ZRP Meeting & Minuting Governance Dashboard',
        'meetings': meetings,
        'total_meetings': total_meetings,
        'awaiting_approval': awaiting_approval,
        'outstanding_actions': outstanding_actions,
        'completed_actions': completed_actions,
        'overdue_actions': overdue_actions,
        'completion_rate': completion_rate,
        'users': users,
    }
    return render(request, 'meetings.html', context)


@login_required
def create_meeting_view(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        meeting_type = request.POST.get('meeting_type')
        meeting_date = request.POST.get('meeting_date')
        venue_or_link = request.POST.get('venue_or_link', '')
        chairperson_id = request.POST.get('chairperson')
        secretary_id = request.POST.get('secretary')
        participant_ids = request.POST.getlist('participants')
        agenda_text = request.POST.get('agenda_text', '')
        
        chairperson = User.objects.filter(pk=chairperson_id).first() if chairperson_id else None
        secretary = User.objects.filter(pk=secretary_id).first() if secretary_id else None
        
        meeting = models.Meeting.objects.create(
            title=title,
            meeting_type=meeting_type,
            meeting_date=meeting_date,
            venue_or_link=venue_or_link,
            chairperson=chairperson,
            secretary=secretary,
            agenda_text=agenda_text,
            organized_by=request.user,
            approval_status='Draft'
        )
        
        if participant_ids:
            meeting.participants.set(participant_ids)
            
        # Send Notifications – MeetingNotification + SystemNotification + Email
        all_notified = set()
        if chairperson: all_notified.add(chairperson)
        if secretary: all_notified.add(secretary)
        for pid in participant_ids:
            u = User.objects.filter(pk=pid).first()
            if u: all_notified.add(u)

        meeting_date_str = meeting.meeting_date.strftime('%d %B %Y at %H:%M') if hasattr(meeting.meeting_date, 'strftime') else str(meeting.meeting_date)
        for u in all_notified:
            msg = f"You have been invited to meeting '{meeting.title}' scheduled for {meeting_date_str}. Venue/Link: {meeting.venue_or_link or 'TBA'}."
            models.MeetingNotification.objects.create(
                user=u,
                meeting=meeting,
                notification_type='Invitation',
                message=msg
            )
            send_system_notification(
                recipient=u,
                category='Meeting',
                title=f"Meeting Invitation: {meeting.title}",
                message=msg,
                sender=request.user,
                link_url=f"/registry/meetings/minute-taking/{meeting.pk}/",
                channel='Multi-Channel'
            )

        messages.success(request, f"Meeting '{meeting.title}' successfully scheduled and {len(all_notified)} participant(s) notified.")
        return redirect('digital-minute-taking', meeting_id=meeting.pk)
        
    return redirect('meetings-dashboard')


@login_required
def digital_minute_taking_view(request, meeting_id):
    meeting = get_object_or_404(models.Meeting, pk=meeting_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'save_minutes':
            meeting.discussions = request.POST.get('discussions', '')
            meeting.minutes_text = request.POST.get('minutes_text', '')
            meeting.apologies_text = request.POST.get('apologies_text', '')
            meeting.save()
            messages.success(request, "Meeting discussions and draft minutes saved successfully.")
            
        elif action == 'create_action_item':
            description = request.POST.get('description', '').strip()
            assigned_to_id = request.POST.get('assigned_to')
            due_date = request.POST.get('due_date')
            priority = request.POST.get('priority', 'Normal')

            assigned_to = get_object_or_404(User, pk=assigned_to_id)
            action_item = models.MeetingActionItem.objects.create(
                meeting=meeting,
                assigned_to=assigned_to,
                description=description,
                due_date=due_date,
                priority=priority
            )

            action_msg = f"Action Item Assigned [{priority} Priority]: '{description[:80]}' — from meeting '{meeting.title}'. Due Date: {due_date}. Please ensure timely completion."
            models.MeetingNotification.objects.create(
                user=assigned_to,
                meeting=meeting,
                action_item=action_item,
                notification_type='Assigned Action',
                message=action_msg
            )
            send_system_notification(
                recipient=assigned_to,
                category='Action Item',
                title=f"Action Item Assigned: {description[:50]}",
                message=action_msg,
                sender=request.user,
                link_url=f"/registry/meetings/minute-taking/{meeting.pk}/",
                channel='Multi-Channel'
            )
            messages.success(request, f"Action item assigned to {assigned_to.get_full_name() or assigned_to.username} and notified.")
            
    users = User.objects.filter(is_active=True).order_by('username')
    action_items = meeting.action_items.all()
    
    context = {
        'meeting': meeting,
        'users': users,
        'action_items': action_items,
    }
    return render(request, 'minute_taking.html', context)


@login_required
def approve_minutes_workflow_view(request, meeting_id):
    meeting = get_object_or_404(models.Meeting, pk=meeting_id)
    if request.method == 'POST':
        target_status = request.POST.get('target_status')
        rejection_notes = request.POST.get('rejection_notes', '')
        
        valid_transitions = ['Draft', 'Secretary Review', 'Chairperson Review', 'Corrections Required', 'Approved', 'Distributed', 'Closed']
        if target_status in valid_transitions:
            meeting.approval_status = target_status
            if target_status == 'Secretary Review':
                meeting.secretary_reviewed_at = timezone.now()
            elif target_status == 'Approved':
                meeting.chairperson_approved_at = timezone.now()
            elif target_status == 'Corrections Required':
                meeting.rejection_notes = rejection_notes
            meeting.save()
            
            # Send status update notifications – MeetingNotification + SystemNotification + Email
            link = f"/registry/meetings/minute-taking/{meeting.pk}/"

            if target_status == 'Secretary Review' and meeting.secretary:
                sec_msg = f"Draft minutes for '{meeting.title}' have been submitted for your Secretary review and editing."
                models.MeetingNotification.objects.create(
                    user=meeting.secretary, meeting=meeting,
                    notification_type='Minutes Awaiting Review', message=sec_msg
                )
                send_system_notification(recipient=meeting.secretary, category='Minutes',
                    title=f"Minutes Submitted for Secretary Review: {meeting.title}",
                    message=sec_msg, sender=request.user, link_url=link, channel='Multi-Channel')

            elif target_status == 'Chairperson Review' and meeting.chairperson:
                chair_msg = f"Minutes for '{meeting.title}' have been reviewed by the Secretary and are awaiting your Chairperson approval."
                models.MeetingNotification.objects.create(
                    user=meeting.chairperson, meeting=meeting,
                    notification_type='Minutes Awaiting Review', message=chair_msg
                )
                send_system_notification(recipient=meeting.chairperson, category='Minutes',
                    title=f"Minutes Awaiting Chairperson Approval: {meeting.title}",
                    message=chair_msg, sender=request.user, link_url=link, channel='Multi-Channel')

            elif target_status == 'Corrections Required' and meeting.secretary:
                corr_msg = f"Corrections Required for minutes of '{meeting.title}'. Notes: {rejection_notes or 'See meeting record for details.'}"
                models.MeetingNotification.objects.create(
                    user=meeting.secretary, meeting=meeting,
                    notification_type='Minutes Awaiting Review', message=corr_msg
                )
                send_system_notification(recipient=meeting.secretary, category='Minutes',
                    title=f"Minutes Corrections Required: {meeting.title}",
                    message=corr_msg, sender=request.user, link_url=link, channel='Multi-Channel')

            elif target_status == 'Distributed':
                dist_msg = f"Official approved minutes for '{meeting.title}' have been distributed and are now available for your review."
                for p in meeting.participants.all():
                    models.MeetingNotification.objects.create(
                        user=p, meeting=meeting,
                        notification_type='Invitation', message=dist_msg
                    )
                    send_system_notification(recipient=p, category='Minutes',
                        title=f"Official Minutes Distributed: {meeting.title}",
                        message=dist_msg, sender=request.user, link_url=link, channel='Multi-Channel')

            messages.success(request, f"Meeting Minute Workflow updated to '{target_status}' — relevant parties notified.")
            
    return redirect('digital-minute-taking', meeting_id=meeting.pk)


@login_required
def action_tracking_view(request):
    actions = models.MeetingActionItem.objects.all().select_related('meeting', 'assigned_to').order_by('due_date')
    
    # Filter
    status = request.GET.get('status', '').strip()
    priority = request.GET.get('priority', '').strip()
    assignee = request.GET.get('assignee', '').strip()
    
    if status:
        actions = actions.filter(status=status)
    if priority:
        actions = actions.filter(priority=priority)
    if assignee:
        actions = actions.filter(assigned_to_id=assignee)
        
    users = User.objects.filter(is_active=True).order_by('username')
    
    context = {
        'page_title': 'ZRP Meeting Action Item Tracking Engine',
        'actions': actions,
        'users': users,
    }
    return render(request, 'action_tracking.html', context)


@login_required
def post_action_comment_view(request, action_id):
    action_item = get_object_or_404(models.MeetingActionItem, pk=action_id)
    if request.method == 'POST':
        comment_text = request.POST.get('comment', '').strip()
        progress = request.POST.get('progress_percent')
        
        if progress and progress.isdigit():
            prog_val = int(progress)
            action_item.progress_percent = prog_val
            if prog_val == 100:
                action_item.status = 'Completed'
                action_item.completion_date = timezone.now()
            elif action_item.status in ['Pending', 'Overdue']:
                action_item.status = 'In Progress'
            action_item.save()
            
        if comment_text:
            models.ActionItemComment.objects.create(
                action_item=action_item,
                author=request.user,
                comment=comment_text,
                progress_percent=progress if (progress and progress.isdigit()) else None
            )
            messages.success(request, "Progress update & comment submitted successfully.")
            
    return redirect('action-tracking')


# ─────────────────────────────────────────────────────────
#  ZRP Interview & Selection Governance Controllers
# ─────────────────────────────────────────────────────────

@login_required
def interview_dashboard_view(request):
    exercises = models.InterviewExercise.objects.all().order_by('-scheduled_date')
    
    # Filter
    q = request.GET.get('q', '').strip()
    itype = request.GET.get('type', '').strip()
    status = request.GET.get('status', '').strip()
    
    if q:
        exercises = exercises.filter(Q(title__icontains=q) | Q(position_title__icontains=q))
    if itype:
        exercises = exercises.filter(interview_type=itype)
    if status:
        exercises = exercises.filter(workflow_status=status)
        
    # Metrics
    total_exercises = models.InterviewExercise.objects.count()
    in_progress = models.InterviewExercise.objects.filter(workflow_status__in=['Scheduled', 'Panel Notified', 'In Progress']).count()
    completed_assessments = models.CandidateAssessment.objects.filter(is_locked=True).count()
    pending_vetting = models.InterviewCandidate.objects.filter(vetting_status='Pending Vetting').count()
    
    departments = models.Department.objects.all()
    users = User.objects.filter(is_active=True).order_by('username')
    
    context = {
        'page_title': 'ZRP Interview & Selection Governance Dashboard',
        'exercises': exercises,
        'total_exercises': total_exercises,
        'in_progress': in_progress,
        'completed_assessments': completed_assessments,
        'pending_vetting': pending_vetting,
        'departments': departments,
        'users': users,
    }
    return render(request, 'interviews.html', context)


@login_required
def create_interview_exercise_view(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        interview_type = request.POST.get('interview_type')
        recruitment_mode = request.POST.get('recruitment_mode')
        department_id = request.POST.get('department')
        position_title = request.POST.get('position_title')
        grade_level = request.POST.get('grade_level')
        interview_stage = request.POST.get('interview_stage')
        scheduled_date = request.POST.get('scheduled_date')
        venue_or_link = request.POST.get('venue_or_link', '')
        
        panel_user_ids = request.POST.getlist('panel_members')
        candidate_names = request.POST.getlist('candidate_name')
        candidate_emails = request.POST.getlist('candidate_email')
        
        department = get_object_or_404(models.Department, pk=department_id)
        
        exercise = models.InterviewExercise.objects.create(
            title=title,
            interview_type=interview_type,
            recruitment_mode=recruitment_mode,
            department=department,
            position_title=position_title,
            grade_level=grade_level,
            interview_stage=interview_stage,
            scheduled_date=scheduled_date,
            venue_or_link=venue_or_link,
            organized_by=request.user,
            workflow_status='Scheduled'
        )
        
        # Add Panel Members + System Notifications
        interview_date_str = exercise.scheduled_date.strftime('%d %B %Y at %H:%M') if hasattr(exercise.scheduled_date, 'strftime') else str(exercise.scheduled_date)
        panel_msg = (
            f"You have been assigned as an Interview Panelist for '{exercise.title}' "
            f"(Position: {position_title}, {exercise.get_interview_type_display() if hasattr(exercise, 'get_interview_type_display') else interview_type}). "
            f"Scheduled: {interview_date_str}. Venue/Link: {venue_or_link or 'TBA'}. "
            f"Please prepare your scoring criteria in advance."
        )
        for puid in panel_user_ids:
            u = User.objects.filter(pk=puid).first()
            if u:
                models.InterviewPanelMember.objects.create(
                    exercise=exercise,
                    user=u,
                    role='Panelist',
                    is_notified=True,
                    notified_at=timezone.now()
                )
                send_system_notification(
                    recipient=u,
                    category='Interview',
                    title=f"Interview Panel Assignment: {exercise.title}",
                    message=panel_msg,
                    sender=request.user,
                    link_url=f"/registry/interviews/",
                    channel='Multi-Channel'
                )

        # Add Candidates + Email Notification
        from django.core.mail import send_mail
        from django.conf import settings as django_settings
        for i, cname in enumerate(candidate_names):
            if cname.strip():
                cemail = candidate_emails[i].strip() if i < len(candidate_emails) else f"candidate{i+1}@ZRP.org.zw"
                models.InterviewCandidate.objects.create(
                    exercise=exercise,
                    full_name=cname.strip(),
                    email=cemail,
                    sequence_number=i+1
                )
                # Send email to candidate
                if '@' in cemail:
                    candidate_email_body = (
                        f"Dear {cname.strip()},\n\n"
                        f"You have been shortlisted for an interview at Zimbabwe Republic Police (ZRP).\n\n"
                        f"Position: {position_title}\n"
                        f"Interview Type: {interview_type}\n"
                        f"Date & Time: {interview_date_str}\n"
                        f"Venue/Link: {venue_or_link or 'To be communicated'}\n\n"
                        f"Please confirm your attendance. Bring relevant supporting documents.\n\n"
                        f"Zimbabwe Republic Police — Recruitment Office"
                    )
                    try:
                        send_mail(
                            subject=f"[ZRP Interview Invitation] {position_title}",
                            message=candidate_email_body,
                            from_email=getattr(django_settings, 'DEFAULT_FROM_EMAIL', 'noreply@ZRP.org.zw'),
                            recipient_list=[cemail],
                            fail_silently=True
                        )
                    except Exception:
                        pass

        # Audit log
        models.InterviewAuditLog.objects.create(
            exercise=exercise,
            user=request.user,
            action='Exercise Created',
            details=f"Recruitment exercise created for position '{position_title}' with {len(panel_user_ids)} panelists and {len(candidate_names)} candidates."
        )

        messages.success(request, f"Interview exercise '{exercise.title}' created — {len(panel_user_ids)} panel member(s) notified and {len(candidate_names)} candidate(s) emailed.")
        return redirect('interview-dashboard')
        
    return redirect('interview-dashboard')


@login_required
def conduct_interview_scoring_view(request, candidate_id):
    candidate = get_object_or_404(models.InterviewCandidate, pk=candidate_id)
    exercise = candidate.exercise
    
    # Existing assessment by this panel member
    assessment = models.CandidateAssessment.objects.filter(candidate=candidate, panel_member=request.user).first()
    
    if request.method == 'POST':
        if assessment and assessment.is_locked:
            messages.error(request, "Permission Denied: Submitted scorecards are protected against alteration.")
            return redirect('conduct-interview-scoring', candidate_id=candidate.pk)
            
        academic = int(request.POST.get('academic_qualifications_score', 0))
        experience = int(request.POST.get('relevant_experience_score', 0))
        technical = int(request.POST.get('technical_knowledge_score', 0))
        competencies = int(request.POST.get('competencies_score', 0))
        communication = int(request.POST.get('communication_skills_score', 0))
        problem_solving = int(request.POST.get('problem_solving_score', 0))
        leadership = int(request.POST.get('leadership_management_score', 0))
        comments = request.POST.get('comments', '')
        recommendation = request.POST.get('recommendation', 'Recommend')
        
        if not assessment:
            assessment = models.CandidateAssessment(candidate=candidate, panel_member=request.user)
            
        assessment.academic_qualifications_score = min(academic, 10)
        assessment.relevant_experience_score = min(experience, 15)
        assessment.technical_knowledge_score = min(technical, 25)
        assessment.competencies_score = min(competencies, 15)
        assessment.communication_skills_score = min(communication, 10)
        assessment.problem_solving_score = min(problem_solving, 10)
        assessment.leadership_management_score = min(leadership, 15)
        assessment.comments = comments
        assessment.recommendation = recommendation
        assessment.is_locked = True # Lock scorecard to protect against alteration
        assessment.save()
        
        # Update Candidate attendance status
        candidate.attendance_status = 'Attended'
        candidate.save()
        
        # Audit log
        models.InterviewAuditLog.objects.create(
            exercise=exercise,
            user=request.user,
            action='Scorecard Submitted & Locked',
            details=f"Panel member {request.user.username} scored candidate {candidate.full_name}: {assessment.total_score}/100 ({recommendation})."
        )
        
        messages.success(request, f"Scorecard for {candidate.full_name} submitted and locked successfully ({assessment.total_score}/100).")
        return redirect('interview-reports', exercise_id=exercise.pk)
        
    context = {
        'candidate': candidate,
        'exercise': exercise,
        'assessment': assessment,
    }
    return render(request, 'interview_scorecard.html', context)


@login_required
def advance_interview_workflow_view(request, exercise_id):
    exercise = get_object_or_404(models.InterviewExercise, pk=exercise_id)
    if request.method == 'POST':
        target_status = request.POST.get('target_status')
        valid_statuses = ['Vacancy Request', 'Request Approved', 'Candidate Selection', 'Scheduled', 'Panel Notified', 'In Progress', 'Assessment Submitted', 'Panel Recommended', 'Executive Approved', 'Closed/Archived']
        
        if target_status in valid_statuses:
            old_status = exercise.workflow_status
            exercise.workflow_status = target_status
            exercise.save()
            
            models.InterviewAuditLog.objects.create(
                exercise=exercise,
                user=request.user,
                action='Workflow Status Advanced',
                details=f"Workflow advanced from '{old_status}' to '{target_status}' by {request.user.username}."
            )
            messages.success(request, f"Interview workflow stage updated to '{target_status}'.")
            
    return redirect('interview-reports', exercise_id=exercise.pk)


@login_required
def interview_reports_view(request, exercise_id):
    exercise = get_object_or_404(models.InterviewExercise, pk=exercise_id)
    candidates = exercise.candidates.all()
    panel_members = exercise.panel_members.all()
    
    # Build candidate ranking data
    ranking_data = []
    for cand in candidates:
        assessments = cand.assessments.all()
        if assessments.exists():
            avg_score = round(sum(a.total_score for a in assessments) / len(assessments), 1)
            recs = [a.recommendation for a in assessments]
        else:
            avg_score = 0.0
            recs = ["No Scores"]
            
        ranking_data.append({
            'candidate': cand,
            'avg_score': avg_score,
            'assessments_count': assessments.count(),
            'recommendations': recs,
        })
        
    # Sort candidate ranking by avg_score descending
    ranking_data = sorted(ranking_data, key=lambda x: x['avg_score'], reverse=True)
    audit_logs = exercise.audit_logs.all()
    
    context = {
        'exercise': exercise,
        'candidates': candidates,
        'panel_members': panel_members,
        'ranking_data': ranking_data,
        'audit_logs': audit_logs,
    }
    return render(request, 'interview_reports.html', context)


# ─────────────────────────────────────────────────────────
#  ZRP HR & Leave Governance Controllers
# ─────────────────────────────────────────────────────────

@login_required
def employee_self_service_view(request):
    # Retrieve or create employee profile (Borrower) for user
    employee, created = models.Borrower.objects.get_or_create(
        user=request.user,
        defaults={
            'code': f"EMP-{request.user.id:04d}",
            'employee_number': f"ZRP-EMP-{request.user.id:04d}",
            'first_name': request.user.first_name or request.user.username,
            'last_name': request.user.last_name or 'Staff',
            'email': request.user.email,
        }
    )
    
    # Fetch leave history
    leave_requests = models.LeaveRequest.objects.filter(user=request.user).order_by('-date_applied')
    active_leave = leave_requests.filter(status='Approved', is_returned=False).first()
    
    # Training history & Performance
    trainings = employee.training_records.all()
    performances = employee.performance_evaluations.all()
    
    # Calculate leave usage
    approved_leaves = leave_requests.filter(status='Approved')
    annual_days_used = sum((l.end_date - l.start_date).days + 1 for l in approved_leaves if l.leave_type == 'Annual')
    sick_days_used = sum((l.end_date - l.start_date).days + 1 for l in approved_leaves if l.leave_type == 'Sick')
    
    context = context_data(request)
    context.update({
        'page_title': 'ZRP Employee Self-Service Portal',
        'employee': employee,
        'leave_requests': leave_requests,
        'active_leave': active_leave,
        'trainings': trainings,
        'performances': performances,
        'annual_days_used': annual_days_used,
        'sick_days_used': sick_days_used,
    })
    return render(request, 'employee_self_service.html', context)


@login_required
def out_of_office_dashboard_view(request):
    today = timezone.now().date()
    
    # Fetch all approved leaves where end_date >= today
    away_leaves = models.LeaveRequest.objects.filter(
        status='Approved',
        end_date__gte=today,
        is_returned=False
    ).order_by('start_date')
    
    # Filter by department if passed
    dept_id = request.GET.get('department')
    if dept_id:
        away_leaves = away_leaves.filter(user__security_profile__department_id=dept_id)
        
    departments = models.Department.objects.all()
    
    context = context_data(request)
    context.update({
        'page_title': 'ZRP Who is Away / Out-of-Office Dashboard',
        'away_leaves': away_leaves,
        'departments': departments,
        'today': today,
    })
    return render(request, 'out_of_office_dashboard.html', context)


@login_required
def advance_leave_workflow_view(request, leave_id):
    leave = get_object_or_404(models.LeaveRequest, pk=leave_id)
    if request.method == 'POST':
        action = request.POST.get('action') # 'supervisor_recommend', 'hr_verify', 'return_leave'
        
        if action == 'supervisor_recommend':
            rec = request.POST.get('supervisor_recommendation')
            notes = request.POST.get('supervisor_notes', '')
            leave.supervisor_recommendation = rec
            leave.supervisor_notes = notes
            leave.workflow_stage = 'Supervisor Recommendation'
            leave.save()
            messages.success(request, f"Supervisor recommendation '{rec}' submitted for leave request.")
            
        elif action == 'hr_verify':
            hr_stat = request.POST.get('hr_review_status')
            notes = request.POST.get('hr_notes', '')
            leave.hr_review_status = hr_stat
            leave.hr_notes = notes
            leave.workflow_stage = 'HR Review'
            leave.save()
            messages.success(request, f"HR Review status set to '{hr_stat}'.")
            
        elif action == 'return_leave':
            leave.is_returned = True
            leave.actual_return_date = timezone.now().date()
            leave.workflow_stage = 'Return from Leave'
            leave.save()
            messages.success(request, f"Employee {leave.user.username} marked as Returned from Leave.")
            
    return redirect('leave-applications')


# ─────────────────────────────────────────────────────────
#  ZRP Procurement & Purchase Order Governance Controllers
# ─────────────────────────────────────────────────────────

@login_required
def track_requisition_movement_view(request, pk):
    req = get_object_or_404(models.SupplyRequisition, pk=pk)
    movements = req.movement_history.all()
    
    # 10-Stage Pipeline Definition
    stages = [
        ('Requisition Initiated', '1. Requisition Initiated'),
        ('Supervisor Review', '2. Supervisor / Manager Review'),
        ('Procurement Review', '3. Procurement Review'),
        ('Budget Verification', '4. Budget / Finance Verification'),
        ('Approval', '5. Executive Approval'),
        ('Procurement Action', '6. Procurement Action'),
        ('Quotation Process', '7. Supplier / Quotation Process'),
        ('Purchase Order', '8. Purchase Order Issued'),
        ('Delivery', '9. Goods Delivery & Verification'),
        ('Payment/Closure', '10. Payment & Closure'),
    ]
    
    context = context_data(request)
    context['page_title'] = f"Movement Tracker: {req.ref_number}"
    context['req'] = req
    context['movements'] = movements
    context['stages'] = stages
    return render(request, 'requisition_movement_tracker.html', context)


@login_required
def issue_purchase_order_view(request, pk):
    req = get_object_or_404(models.SupplyRequisition, pk=pk)
    if request.method == 'POST':
        po_num = request.POST.get('purchase_order_number', '').strip()
        req_date = request.POST.get('required_date')
        
        if not po_num:
            po_count = models.SupplyRequisition.objects.filter(purchase_order_number__isnull=False).count() + 1
            po_num = f"ZRP-PO-{timezone.now().year}-{po_count:04d}"
        
        req.purchase_order_number = po_num
        req.po_issued_date = timezone.now()
        req.procurement_status = 'Purchase Order Issued'
        
        if 'po_document' in request.FILES:
            req.po_document = request.FILES['po_document']
        if req_date:
            req.required_date = req_date
            
        req.save()
        
        models.RequisitionMovementLog.objects.create(
            requisition=req,
            user=request.user,
            from_stage='Quotation Process',
            to_stage='Purchase Order Issued',
            comments=f"Purchase Order '{po_num}' issued by {request.user.username}."
        )
        messages.success(request, f"Purchase Order '{po_num}' issued successfully for requisition {req.ref_number}.")
        
    return redirect('track-requisition-movement', pk=pk)


@login_required
def update_delivery_status_view(request, pk):
    req = get_object_or_404(models.SupplyRequisition, pk=pk)
    if request.method == 'POST':
        delivery_status = request.POST.get('delivery_status')
        delivery_date = request.POST.get('delivery_date')
        delivery_notes = request.POST.get('delivery_notes', '')
        
        old_status = req.delivery_status
        req.delivery_status = delivery_status
        if delivery_date:
            req.delivery_date = delivery_date
        req.delivery_notes = delivery_notes
        
        if delivery_status == 'Verified':
            req.procurement_status = 'Delivered & Verified'
        req.save()
        
        models.RequisitionMovementLog.objects.create(
            requisition=req,
            user=request.user,
            from_stage=f"Delivery ({old_status})",
            to_stage=f"Delivery ({delivery_status})",
            comments=f"Delivery status updated to '{delivery_status}' by {request.user.username}."
        )
        messages.success(request, f"Delivery status updated to '{delivery_status}'.")
        
    return redirect('track-requisition-movement', pk=pk)


# ─────────────────────────────────────────────────────────
#  ZRP Training, Travel & Subsistence Allowance Controllers
# ─────────────────────────────────────────────────────────

@login_required
def travel_tsa_dashboard_view(request):
    today = timezone.now().date()
    travels = models.TravelRequest.objects.all().order_by('-created_at')
    
    # Filter
    cat = request.GET.get('category', '').strip()
    stage = request.GET.get('stage', '').strip()
    
    if cat:
        travels = travels.filter(travel_category=cat)
    if stage:
        travels = travels.filter(workflow_stage=stage)
        
    # Check for overdue acquittals (end_date < today - 7 days and not cleared)
    for t in travels:
        if t.end_date and t.end_date < (today - datetime.timedelta(days=7)) and t.acquittal_status not in ['Cleared', 'Submitted']:
            if t.acquittal_status != 'Overdue':
                t.acquittal_status = 'Overdue'
                t.save(update_fields=['acquittal_status'])
                
    # Metrics
    total_travels = models.TravelRequest.objects.count()
    total_tsa_expenditure = sum(t.total_tsa_calculated for t in travels.filter(approval_status='Approved'))
    outstanding_acquittals = travels.filter(acquittal_status__in=['Pending Acquittal', 'Overdue']).count()
    overdue_count = travels.filter(acquittal_status='Overdue').count()
    
    departments = models.Department.objects.all()
    budgets = models.Budget.objects.all()
    users = User.objects.filter(is_active=True).order_by('username')
    
    context = context_data(request)
    context.update({
        'page_title': 'ZRP Training, Travel & Subsistence Allowance (TSA) Dashboard',
        'travels': travels,
        'total_travels': total_travels,
        'total_tsa_expenditure': total_tsa_expenditure,
        'outstanding_acquittals': outstanding_acquittals,
        'overdue_count': overdue_count,
        'departments': departments,
        'budgets': budgets,
        'users': users,
    })
    return render(request, 'travel_tsa_dashboard.html', context)


@login_required
def create_travel_request_view(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        category = request.POST.get('travel_category')
        dept_id = request.POST.get('department')
        destination = request.POST.get('destination')
        purpose = request.POST.get('purpose', '').strip()
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        budget_id = request.POST.get('budget_line')
        
        import datetime
        start_date = datetime.date.fromisoformat(start_date_str.split('T')[0]) if start_date_str else timezone.now().date()
        end_date = datetime.date.fromisoformat(end_date_str.split('T')[0]) if end_date_str else start_date
        
        daily_rate = float(request.POST.get('daily_subsistence_rate', 80.00))
        acc_rate = float(request.POST.get('nightly_accommodation_rate', 120.00))
        transport_cost = float(request.POST.get('transport_mileage_cost', 0.00))
        
        attendee_ids = request.POST.getlist('attendees')
        
        dept = get_object_or_404(models.Department, pk=dept_id)
        budget = models.Budget.objects.filter(pk=budget_id).first() if budget_id else None
        
        travel = models.TravelRequest.objects.create(
            title=title,
            travel_category=category,
            requestor=request.user,
            department=dept,
            destination=destination,
            purpose=purpose,
            start_date=start_date,
            end_date=end_date,
            budget_line=budget,
            daily_subsistence_rate=daily_rate,
            nightly_accommodation_rate=acc_rate,
            transport_mileage_cost=transport_cost,
            workflow_stage='Training/Travel Request'
        )
        
        if 'supporting_document' in request.FILES:
            travel.supporting_document = request.FILES['supporting_document']
            travel.save()
            
        # Add attendees
        for uid in attendee_ids:
            u = User.objects.filter(pk=uid).first()
            if u:
                travel.attendees.add(u)
                
        models.TravelAuditLog.objects.create(
            travel_request=travel,
            user=request.user,
            action='Request Initiated',
            details=f"Travel request '{title}' initiated to {destination} ({category}). TSA Total: ${travel.total_tsa_calculated}."
        )
        
        messages.success(request, f"Travel & TSA request '{travel.ref_number}' submitted successfully.")
        return redirect('travel-tsa-dashboard')
        
    return redirect('travel-tsa-dashboard')


@login_required
def advance_travel_workflow_view(request, pk):
    travel = get_object_or_404(models.TravelRequest, pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'supervisor_recommend':
            rec = request.POST.get('supervisor_recommendation')
            notes = request.POST.get('supervisor_notes', '')
            travel.supervisor_recommendation = rec
            travel.supervisor_notes = notes
            travel.workflow_stage = 'Supervisor Recommendation'
            travel.save()
            
            models.TravelAuditLog.objects.create(
                travel_request=travel,
                user=request.user,
                action='Supervisor Recommendation',
                details=f"Supervisor recommendation '{rec}' submitted by {request.user.username}."
            )
            messages.success(request, f"Supervisor recommendation '{rec}' recorded.")
            
        elif action == 'finance_verify':
            ver = request.POST.get('finance_verification')
            notes = request.POST.get('finance_notes', '')
            travel.finance_verification = ver
            travel.finance_notes = notes
            travel.workflow_stage = 'Budget/Finance Verification'
            travel.save()
            
            models.TravelAuditLog.objects.create(
                travel_request=travel,
                user=request.user,
                action='Finance Verification',
                details=f"Finance verification '{ver}' submitted by {request.user.username}."
            )
            messages.success(request, f"Finance verification status updated to '{ver}'.")
            
        elif action == 'executive_approve':
            app_status = request.POST.get('approval_status')
            travel.approval_status = app_status
            travel.approved_by = request.user
            if app_status == 'Approved':
                travel.workflow_stage = 'TSA Approval'
            else:
                travel.workflow_stage = 'Training/Travel Request'
            travel.save()
            
            models.TravelAuditLog.objects.create(
                travel_request=travel,
                user=request.user,
                action=f"Executive {app_status}",
                details=f"Travel request {app_status} by delegated authority {request.user.username}."
            )
            messages.success(request, f"Travel request status updated to '{app_status}'.")
            
        elif action == 'process_payment':
            travel.payment_status = 'Paid'
            if 'proof_of_payment' in request.FILES:
                travel.proof_of_payment = request.FILES['proof_of_payment']
            travel.workflow_stage = 'Travel/Training In Progress'
            travel.acquittal_status = 'Pending Acquittal'
            travel.save()
            
            models.TravelAuditLog.objects.create(
                travel_request=travel,
                user=request.user,
                action='TSA Payment Processed',
                details=f"TSA Payment of ${travel.total_tsa_calculated} processed by {request.user.username}."
            )
            messages.success(request, "TSA Payment marked as Paid and proof attached.")
            
    return redirect('travel-tsa-dashboard')


@login_required
def submit_travel_acquittal_view(request, pk):
    travel = get_object_or_404(models.TravelRequest, pk=pk)
    
    if request.method == 'POST':
        sub_spent = float(request.POST.get('actual_subsistence_spent', 0))
        acc_spent = float(request.POST.get('actual_accommodation_spent', 0))
        trans_spent = float(request.POST.get('actual_transport_spent', 0))
        summary = request.POST.get('acquittal_report_summary', '').strip()
        
        acquittal, created = models.TravelAcquittal.objects.get_or_create(
            travel_request=travel,
            defaults={'submitted_by': request.user}
        )
        
        acquittal.actual_subsistence_spent = sub_spent
        acquittal.actual_accommodation_spent = acc_spent
        acquittal.actual_transport_spent = trans_spent
        acquittal.acquittal_report_summary = summary
        acquittal.is_verified_by_finance = True
        acquittal.verified_by = request.user
        
        if 'receipts_attachment' in request.FILES:
            acquittal.receipts_attachment = request.FILES['receipts_attachment']
            
        acquittal.save()
        
        travel.acquittal_status = 'Cleared'
        travel.workflow_stage = 'Closed'
        travel.save()
        
        models.TravelAuditLog.objects.create(
            travel_request=travel,
            user=request.user,
            action='Acquittal Cleared',
            details=f"Acquittal cleared by {request.user.username}. Total Spent: ${acquittal.total_actual_spent} (Surplus/Deficit: ${acquittal.surplus_or_deficit})."
        )
        
        messages.success(request, f"Travel acquittal for '{travel.ref_number}' submitted and cleared successfully.")
        return redirect('travel-tsa-dashboard')
        
    context = {
        'travel': travel,
        'acquittal': getattr(travel, 'acquittal', None),
    }
    return render(request, 'travel_acquittal_form.html', context)


# ─────────────────────────────────────────────────────────
#  ZRP Universal Electronic Approval & Signing Controllers
# ─────────────────────────────────────────────────────────

@login_required
def electronic_approval_center_view(request):
    approvals = models.ElectronicApprovalRecord.objects.all().order_by('-timestamp')
    
    # Filter by entity_type if passed
    entity_type = request.GET.get('entity_type', '').strip()
    if entity_type:
        approvals = approvals.filter(entity_type=entity_type)
        
    # Gather pending approvals across system modules
    pending_leaves = models.LeaveRequest.objects.filter(status='Pending')
    pending_requisitions = models.SupplyRequisition.objects.exclude(status__in=['Approved', 'Rejected'])
    pending_travels = models.TravelRequest.objects.filter(approval_status='Pending')
    
    context = context_data(request)
    context['page_title'] = 'ZRP Central Electronic Approval & Signature Center'
    context['approvals'] = approvals
    context['pending_leaves'] = pending_leaves
    context['pending_requisitions'] = pending_requisitions
    context['pending_travels'] = pending_travels
    context['total_signed'] = approvals.count()
    return render(request, 'electronic_approval_center.html', context)


@login_required
def verify_approval_trail_view(request, entity_type, entity_id):
    trail = models.ElectronicApprovalRecord.objects.filter(
        entity_type=entity_type,
        entity_id=entity_id
    ).order_by('timestamp')
    
    ref_number = f"{entity_type} #{entity_id}"
    if trail.exists():
        ref_number = trail.first().entity_reference
        
    # Re-verify SHA-256 integrity for each record
    import hashlib
    verified_trail = []
    for r in trail:
        payload = f"{r.entity_type}:{r.entity_id}:{r.user_id}:{r.stage}:{r.status}:{r.timestamp.isoformat()}:{r.signature_data or ''}"
        expected_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()
        is_valid = (r.verification_hash == expected_hash)
        verified_trail.append({
            'record': r,
            'is_valid': is_valid,
            'expected_hash': expected_hash
        })
        
    context = context_data(request)
    context['page_title'] = f"Approval Trail: {ref_number}"
    context['entity_type'] = entity_type
    context['entity_id'] = entity_id
    context['ref_number'] = ref_number
    context['verified_trail'] = verified_trail
    return render(request, 'verify_approval_trail.html', context)


@login_required
def sign_electronic_approval_action_view(request):
    if request.method == 'POST':
        entity_type = request.POST.get('entity_type')
        entity_id = int(request.POST.get('entity_id'))
        entity_ref = request.POST.get('entity_reference', f"{entity_type}-{entity_id}")
        stage = request.POST.get('stage', 'Signed') # 'Submitted', 'Reviewed', 'Recommended', 'Approved', 'Signed'
        user_role = request.POST.get('user_role', 'Authorized Officer')
        comments = request.POST.get('comments', '')
        sig_data = request.POST.get('signature_data', '').strip()
        
        ip_addr = _get_user_ip(request)
        u_agent = request.META.get('HTTP_USER_AGENT', '')[:450]
        
        record = models.ElectronicApprovalRecord.objects.create(
            entity_type=entity_type,
            entity_id=entity_id,
            entity_reference=entity_ref,
            stage=stage,
            user=request.user,
            user_role=user_role,
            status='Completed',
            signature_type='Digital Canvas Signature' if sig_data else 'Secure User Token Approval',
            signature_data=sig_data,
            ip_address=ip_addr,
            user_agent=u_agent,
            comments=comments
        )
        
        messages.success(request, f"Electronic signature and approval record '{stage}' logged successfully. Hash: {record.verification_hash[:16]}...")
        return redirect('verify-approval-trail', entity_type=entity_type, entity_id=entity_id)
        
    return redirect('electronic-approval-center')


# ─────────────────────────────────────────────────────────
#  ZRP Attendance & Time Management Controllers
# ─────────────────────────────────────────────────────────

@login_required
def attendance_dashboard_view(request):
    today = timezone.now().date()
    
    # Retrieve user's today attendance record
    today_record = models.EmployeeAttendance.objects.filter(user=request.user, date=today).first()
    
    # Auto-synchronize leaves & travel for today if no record exists
    if not today_record:
        # Check active leave
        active_leave = models.LeaveRequest.objects.filter(user=request.user, status='Approved', start_date__lte=today, end_date__gte=today, is_returned=False).first()
        if active_leave:
            today_record = models.EmployeeAttendance.objects.create(
                user=request.user,
                date=today,
                status='Approved Leave',
                location_notes=f"On {active_leave.leave_type} Leave",
                remarks=f"Leave request #{active_leave.pk}"
            )
        else:
            # Check active travel / training
            active_travel = models.TravelRequest.objects.filter(requestor=request.user, approval_status='Approved', start_date__lte=today, end_date__gte=today).first()
            if active_travel:
                status_val = 'Training' if active_travel.travel_category == 'Training-Related Travel' else 'Official Business'
                today_record = models.EmployeeAttendance.objects.create(
                    user=request.user,
                    date=today,
                    status=status_val,
                    location_notes=active_travel.destination,
                    remarks=active_travel.title
                )

    # Attendance register for today across all staff
    attendance_records = models.EmployeeAttendance.objects.filter(date=today).order_by('-clock_in_time')
    
    # Filter
    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        attendance_records = attendance_records.filter(status=status_filter)
        
    # Metrics today
    present_count = models.EmployeeAttendance.objects.filter(date=today, status='Present').count()
    leave_count = models.EmployeeAttendance.objects.filter(date=today, status='Approved Leave').count()
    business_count = models.EmployeeAttendance.objects.filter(date=today, status='Official Business').count()
    training_count = models.EmployeeAttendance.objects.filter(date=today, status='Training').count()
    awol_count = models.EmployeeAttendance.objects.filter(date=today, status='Absence Without Leave').count()
    
    context = context_data(request)
    context['page_title'] = 'ZRP Daily Attendance & Time Management Portal'
    context['today'] = today
    context['today_record'] = today_record
    context['attendance_records'] = attendance_records
    context['present_count'] = present_count
    context['leave_count'] = leave_count
    context['business_count'] = business_count
    context['training_count'] = training_count
    context['awol_count'] = awol_count
    return render(request, 'attendance_dashboard.html', context)


@login_required
def clock_in_out_action_view(request):
    if request.method == 'POST':
        action = request.POST.get('action') # 'clock_in' or 'clock_out'
        today = timezone.now().date()
        now = timezone.now()
        ip_addr = _get_user_ip(request)
        
        record, created = models.EmployeeAttendance.objects.get_or_create(
            user=request.user,
            date=today,
            defaults={'status': 'Present'}
        )
        
        if action == 'clock_in':
            if not record.clock_in_time:
                record.clock_in_time = now
                record.clock_in_ip = ip_addr
                record.status = 'Present'
                record.save()
                messages.success(request, f"Successfully Clocked In at {now.strftime('%H:%M:%S')}. Have a productive day!")
            else:
                messages.warning(request, f"You already clocked in today at {record.clock_in_time.strftime('%H:%M:%S')}.")
                
        elif action == 'clock_out':
            if record.clock_in_time and not record.clock_out_time:
                record.clock_out_time = now
                record.clock_out_ip = ip_addr
                record.save() # save() auto-computes total_work_hours
                messages.success(request, f"Successfully Clocked Out at {now.strftime('%H:%M:%S')}. Total Hours Worked: {record.total_work_hours} hrs.")
            elif not record.clock_in_time:
                messages.error(request, "You must Clock In before you can Clock Out.")
            else:
                messages.warning(request, f"You already clocked out today at {record.clock_out_time.strftime('%H:%M:%S')}.")
                
    return redirect('attendance-dashboard')


@login_required
def monthly_attendance_report_view(request):
    today = timezone.now().date()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))
    
    # Filter attendance records for month & year
    records = models.EmployeeAttendance.objects.filter(
        date__year=year,
        date__month=month
    )
    
    # Group by employee
    users = User.objects.filter(is_active=True).order_by('username')
    report_data = []
    
    for u in users:
        u_records = records.filter(user=u)
        present = u_records.filter(status='Present').count()
        leave = u_records.filter(status='Approved Leave').count()
        business = u_records.filter(status='Official Business').count()
        training = u_records.filter(status='Training').count()
        awol = u_records.filter(status='Absence Without Leave').count()
        total_hours = sum(r.total_work_hours for r in u_records)
        
        report_data.append({
            'user': u,
            'present_days': present,
            'leave_days': leave,
            'business_days': business,
            'training_days': training,
            'awol_days': awol,
            'total_hours': total_hours,
        })
        
    context = context_data(request)
    context['page_title'] = f"Monthly Attendance Report: {month}/{year}"
    context['month'] = month
    context['year'] = year
    context['report_data'] = report_data
    return render(request, 'monthly_attendance_report.html', context)


# ─────────────────────────────────────────────────────────
#  ZRP Executive Analytics & Admin Operations Controllers
# ─────────────────────────────────────────────────────────

@login_required
def executive_analytics_dashboard_view(request):
    today = timezone.now().date()
    
    # 1. Employee & Attendance High-Level Metrics
    total_employees = models.Borrower.objects.count()
    employees_on_leave = models.LeaveRequest.objects.filter(status='Approved', start_date__lte=today, end_date__gte=today, is_returned=False).count()
    employees_on_business = models.TravelRequest.objects.filter(approval_status='Approved', travel_category='Official Business Travel', start_date__lte=today, end_date__gte=today).count()
    employees_in_training = models.TravelRequest.objects.filter(approval_status='Approved', travel_category='Training-Related Travel', start_date__lte=today, end_date__gte=today).count()
    present_today = models.EmployeeAttendance.objects.filter(date=today, status='Present').count()
    
    # 2. Pending Approvals High-Level Metrics
    pending_leave_requests = models.LeaveRequest.objects.filter(status='Pending').count()
    pending_procurement_requests = models.SupplyRequisition.objects.exclude(status__in=['Approved', 'Rejected']).count()
    pending_travel_requests = models.TravelRequest.objects.filter(approval_status='Pending').count()
    pending_approvals_total = pending_leave_requests + pending_procurement_requests + pending_travel_requests
    
    # 3. Operational Outstanding & Upcoming Events
    outstanding_acquittals = models.TravelRequest.objects.filter(acquittal_status__in=['Pending Acquittal', 'Overdue']).count()
    outstanding_meeting_actions = models.MeetingActionItem.objects.exclude(status='Completed').count()
    upcoming_interviews = models.InterviewExercise.objects.filter(workflow_status__in=['Scheduled', 'In Progress']).count()
    upcoming_meetings = models.Meeting.objects.filter(meeting_date__gte=timezone.now()).count()
    document_workflows = models.DocumentWorkflow.objects.filter(current_status='In Progress').count()
    
    # Departmental Statistics
    departments = models.Department.objects.all()
    dept_stats = []
    for d in departments:
        dept_stats.append({
            'name': d.name,
            'staff_count': models.Borrower.objects.filter(department=d).count(),
            'requisitions_count': models.SupplyRequisition.objects.filter(department=d).count(),
            'travels_count': models.TravelRequest.objects.filter(department=d).count(),
        })
        
    context = context_data(request)
    context['page_title'] = 'ZRP Central Executive Analytics & Management Dashboard'
    context['total_employees'] = total_employees
    context['employees_on_leave'] = employees_on_leave
    context['employees_on_business'] = employees_on_business
    context['employees_in_training'] = employees_in_training
    context['present_today'] = present_today
    context['pending_approvals_total'] = pending_approvals_total
    context['pending_leave_requests'] = pending_leave_requests
    context['pending_procurement_requests'] = pending_procurement_requests
    context['pending_travel_requests'] = pending_travel_requests
    context['outstanding_acquittals'] = outstanding_acquittals
    context['outstanding_meeting_actions'] = outstanding_meeting_actions
    context['upcoming_interviews'] = upcoming_interviews
    context['upcoming_meetings'] = upcoming_meetings
    context['document_workflows'] = document_workflows
    context['dept_stats'] = dept_stats
    return render(request, 'executive_analytics_dashboard.html', context)


@login_required
def admin_operations_dashboard_view(request):
    stores_requests = models.StoresRequest.objects.all().order_by('-date_requested')
    vehicle_requests = models.VehicleRequest.objects.all().order_by('-created_at')
    fuel_requests = models.FuelRequest.objects.all().order_by('-created_at')
    grvs = models.GoodsReceivedVoucher.objects.all().order_by('-created_at')
    stores_items = models.StoresItem.objects.all()
    
    context = context_data(request)
    context['page_title'] = 'ZRP Admin & Operations Management Dashboard'
    context['stores_requests'] = stores_requests
    context['vehicle_requests'] = vehicle_requests
    context['fuel_requests'] = fuel_requests
    context['grvs'] = grvs
    context['stores_items'] = stores_items
    return render(request, 'admin_operations_dashboard.html', context)


@login_required
def export_reports_view(request, report_type):
    import csv
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="zrp_{report_type}_report_{timezone.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    if report_type == 'attendance':
        writer.writerow(['Date', 'Employee', 'Status', 'Clock In', 'Clock Out', 'Hours Worked'])
        records = models.EmployeeAttendance.objects.all().order_by('-date')[:500]
        for r in records:
            writer.writerow([r.date, r.user.username, r.status, r.clock_in_time, r.clock_out_time, r.total_work_hours])
            
    elif report_type == 'procurement':
        writer.writerow(['Ref Number', 'Requester', 'Department', 'Status', 'Delegated Level', 'Grand Total ($)'])
        reqs = models.SupplyRequisition.objects.all().order_by('-date_requested')[:500]
        for rq in reqs:
            writer.writerow([rq.ref_number, rq.requester.username, rq.department.name if rq.department else '', rq.status, rq.delegated_authority_level, rq.grand_total])
            
    elif report_type == 'travel_tsa':
        writer.writerow(['Ref Number', 'Title', 'Category', 'Requestor', 'Destination', 'Calculated TSA ($)', 'Status', 'Acquittal Status'])
        travels = models.TravelRequest.objects.all().order_by('-created_at')[:500]
        for t in travels:
            writer.writerow([t.ref_number, t.title, t.travel_category, t.requestor.username, t.destination, t.total_tsa_calculated, t.approval_status, t.acquittal_status])
            
    return response


# ─────────────────────────────────────────────────────────
#  ZRP HR Analytics Dashboard
# ─────────────────────────────────────────────────────────

@login_required
def hr_analytics_dashboard_view(request):
    from django.db.models import Count, Q
    today = timezone.now().date()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))

    # Staff Establishment
    total_staff = models.Borrower.objects.count()
    active_staff = models.Borrower.objects.filter(status='Active').count()
    departments = models.Department.objects.annotate(staff_count=Count('borrower')).order_by('-staff_count')

    # Leave Statistics (current month)
    leave_qs = models.LeaveRequest.objects.filter(
        start_date__year=year, start_date__month=month
    )
    total_leave_requests = leave_qs.count()
    approved_leave = leave_qs.filter(status='Approved').count()
    pending_leave = leave_qs.filter(status='Pending').count()
    rejected_leave = leave_qs.filter(status='Rejected').count()
    currently_on_leave = models.LeaveRequest.objects.filter(
        status='Approved', start_date__lte=today, end_date__gte=today, is_returned=False
    ).count()

    # Leave by type
    leave_by_type = leave_qs.values('leave_type').annotate(count=Count('id')).order_by('-count')

    # Attendance (current month)
    attendance_qs = models.EmployeeAttendance.objects.filter(date__year=year, date__month=month)
    present_days = attendance_qs.filter(status='Present').count()
    awol_count = attendance_qs.filter(status='Absence Without Leave').count()

    # Training (travel category)
    training_requests = models.TravelRequest.objects.filter(
        travel_category='Training-Related Travel', created_at__year=year, created_at__month=month
    )
    approved_training = training_requests.filter(approval_status='Approved').count()

    # Recruitment
    total_interviews = models.InterviewExercise.objects.count()
    active_interviews = models.InterviewExercise.objects.filter(workflow_status__in=['Scheduled', 'In Progress']).count()

    # Employee Movements (recent leave returns)
    recent_returns = models.LeaveRequest.objects.filter(
        is_returned=True, actual_return_date__year=year, actual_return_date__month=month
    ).order_by('-actual_return_date')[:10]

    context = context_data(request)
    context['page_title'] = f'ZRP HR Analytics Dashboard — {month}/{year}'
    context['month'] = month
    context['year'] = year
    context['months_list'] = list(range(1, 13))
    context['total_staff'] = total_staff
    context['active_staff'] = active_staff
    context['departments'] = departments
    context['total_leave_requests'] = total_leave_requests
    context['approved_leave'] = approved_leave
    context['pending_leave'] = pending_leave
    context['rejected_leave'] = rejected_leave
    context['currently_on_leave'] = currently_on_leave
    context['leave_by_type'] = leave_by_type
    context['present_days'] = present_days
    context['awol_count'] = awol_count
    context['training_requests_count'] = training_requests.count()
    context['approved_training'] = approved_training
    context['total_interviews'] = total_interviews
    context['active_interviews'] = active_interviews
    context['recent_returns'] = recent_returns
    return render(request, 'hr_analytics_dashboard.html', context)


# ─────────────────────────────────────────────────────────
#  ZRP Procurement Analytics Dashboard
# ─────────────────────────────────────────────────────────

@login_required
def procurement_analytics_dashboard_view(request):
    from django.db.models import Sum, Count, Q
    today = timezone.now().date()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))
    period = request.GET.get('period', 'monthly')  # monthly | quarterly | annual

    # Base queryset for period
    if period == 'annual':
        reqs = models.SupplyRequisition.objects.filter(date_requested__year=year)
    elif period == 'quarterly':
        quarter_month_start = ((today.month - 1) // 3) * 3 + 1
        reqs = models.SupplyRequisition.objects.filter(
            date_requested__year=year, date_requested__month__gte=quarter_month_start
        )
    else:
        reqs = models.SupplyRequisition.objects.filter(
            date_requested__year=year, date_requested__month=month
        )

    total_received = reqs.count()
    pending = reqs.exclude(status__in=['Approved', 'Rejected', 'Closed']).count()
    approved = reqs.filter(status='Approved').count()
    rejected = reqs.filter(status='Rejected').count()
    delivered = reqs.filter(delivery_status='Delivered').count()

    from django.db.models import Sum, Count, Q, F

    total_expenditure = reqs.filter(status='Approved').aggregate(
        total=Sum(F('items__quantity') * F('items__unit_cost'))
    )['total'] or 0

    # By department
    dept_breakdown = reqs.values('department__name').annotate(
        count=Count('id', distinct=True), spend=Sum(F('items__quantity') * F('items__unit_cost'))
    ).order_by('-spend')

    # By delegated authority level
    level_breakdown = reqs.values('delegated_authority_level').annotate(
        count=Count('id', distinct=True), spend=Sum(F('items__quantity') * F('items__unit_cost'))
    ).order_by('delegated_authority_level')

    # Outstanding actions (approved but not delivered)
    outstanding = reqs.filter(status='Approved').exclude(delivery_status='Delivered')

    # GRVs this period
    grvs = models.GoodsReceivedVoucher.objects.filter(created_at__year=year, created_at__month=month)

    context = context_data(request)
    context['page_title'] = f'ZRP Procurement Analytics Dashboard — {period.title()} {year}'
    context['month'] = month
    context['year'] = year
    context['months_list'] = list(range(1, 13))
    context['period'] = period
    context['total_received'] = total_received
    context['pending'] = pending
    context['approved'] = approved
    context['rejected'] = rejected
    context['delivered'] = delivered
    context['total_expenditure'] = total_expenditure
    context['dept_breakdown'] = dept_breakdown
    context['level_breakdown'] = level_breakdown
    context['outstanding'] = outstanding[:20]
    context['grvs'] = grvs[:20]
    return render(request, 'procurement_analytics_dashboard.html', context)


# ─────────────────────────────────────────────────────────
#  ZRP Training & Travel Analytics Dashboard
# ─────────────────────────────────────────────────────────

@login_required
def travel_analytics_dashboard_view(request):
    from django.db.models import Sum, Count
    today = timezone.now().date()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))
    period = request.GET.get('period', 'monthly')

    if period == 'annual':
        travels = models.TravelRequest.objects.filter(created_at__year=year)
    elif period == 'quarterly':
        q_start = ((today.month - 1) // 3) * 3 + 1
        travels = models.TravelRequest.objects.filter(
            created_at__year=year, created_at__month__gte=q_start
        )
    else:
        travels = models.TravelRequest.objects.filter(
            created_at__year=year, created_at__month=month
        )

    training_reqs = travels.filter(travel_category='Training-Related Travel')
    official_reqs = travels.filter(travel_category='Official Business Travel')

    # Training metrics
    total_training = training_reqs.count()
    approved_training = training_reqs.filter(approval_status='Approved').count()
    training_undertaken = training_reqs.filter(workflow_stage='Closed').count()
    training_expenditure = training_reqs.filter(approval_status='Approved').aggregate(
        total=Sum('total_tsa_calculated')
    )['total'] or 0

    # Training by department
    training_by_dept = training_reqs.values('department__name').annotate(
        count=Count('id'), spend=Sum('total_tsa_calculated')
    ).order_by('-count')

    # Travel/TSA metrics
    total_travel = official_reqs.count()
    approved_travel = official_reqs.filter(approval_status='Approved').count()
    tsa_expenditure = official_reqs.filter(approval_status='Approved').aggregate(
        total=Sum('total_tsa_calculated')
    )['total'] or 0

    # Outstanding acquittals
    outstanding_acquittals = travels.filter(
        acquittal_status__in=['Pending Acquittal', 'Overdue']
    ).order_by('end_date')

    context = context_data(request)
    context['page_title'] = f'ZRP Training & Travel Analytics Dashboard — {period.title()} {year}'
    context['month'] = month
    context['year'] = year
    context['months_list'] = list(range(1, 13))
    context['period'] = period
    context['total_training'] = total_training
    context['approved_training'] = approved_training
    context['training_undertaken'] = training_undertaken
    context['training_expenditure'] = training_expenditure
    context['training_by_dept'] = training_by_dept
    context['total_travel'] = total_travel
    context['approved_travel'] = approved_travel
    context['tsa_expenditure'] = tsa_expenditure
    context['outstanding_acquittals'] = outstanding_acquittals[:20]
    return render(request, 'travel_analytics_dashboard.html', context)



# ─────────────────────────────────────────────────────────
#  ZRP Security, Access Control & Audit Trail Controllers
# ─────────────────────────────────────────────────────────

@login_required
def security_audit_center_view(request):
    # RBAC User profiles
    security_profiles = models.UserSecurity.objects.all().order_by('-user__date_joined')
    
    # Real-time Security Alerts
    alerts = models.SecurityAlert.objects.all().order_by('-timestamp')[:50]
    
    # Forensic Audit Log Stream
    forensic_logs = models.ForensicAudit.objects.all().order_by('-timestamp')[:100]
    
    # Document Versioning & Secure Shares Stats
    version_count = models.FileVersion.objects.count()
    share_count = models.DigitalShare.objects.count()
    mfa_enabled_count = models.UserSecurity.objects.filter(mfa_enabled=True).count()
    
    context = context_data(request)
    context['page_title'] = 'ZRP Security, Access Control & Audit Governance Center'
    context['security_profiles'] = security_profiles
    context['alerts'] = alerts
    context['forensic_logs'] = forensic_logs
    context['version_count'] = version_count
    context['share_count'] = share_count
    context['mfa_enabled_count'] = mfa_enabled_count
    return render(request, 'security_audit_center.html', context)


@login_required
def toggle_mfa_action_view(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user_sec = get_object_or_404(models.UserSecurity, user_id=user_id)
        
        user_sec.mfa_enabled = not user_sec.mfa_enabled
        if user_sec.mfa_enabled and not user_sec.mfa_secret:
            import secrets
            user_sec.mfa_secret = secrets.token_hex(16)
        user_sec.save()
        
        models.SecurityAlert.objects.create(
            alert_type="MFA State Modified",
            description=f"MFA status changed to {user_sec.mfa_enabled} for user {user_sec.user.username} by {request.user.username}",
            severity="Low",
            user=request.user,
            ip_address=_get_user_ip(request)
        )
        messages.success(request, f"Multi-Factor Authentication (MFA) state updated for user {user_sec.user.username}.")
        
    return redirect('security-audit-center')


@login_required
def backup_and_recovery_action_view(request):
    if request.method == 'POST':
        import shutil
        import os
        from django.conf import settings
        
        db_path = settings.DATABASES['default']['NAME']
        backup_dir = os.path.join(settings.MEDIA_ROOT, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_filename = f"zrp_db_backup_{timezone.now().strftime('%Y%m%d_%H%M%S')}.sqlite3"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        try:
            shutil.copy2(db_path, backup_path)
            models.ForensicAudit.objects.create(
                user=request.user,
                action="System Database Backup Executed",
                method="POST",
                path=request.path,
                payload={'backup_file': backup_filename},
                ip_address=_get_user_ip(request)
            )
            messages.success(request, f"Full System Database Backup created successfully: {backup_filename}")
        except Exception as e:
            messages.error(request, f"Backup failed: {str(e)}")
            
    return redirect('security-audit-center')


# ─────────────────────────────────────────────────────────
#  ZRP Universal Notification & Alert Hub Controllers
# ─────────────────────────────────────────────────────────

def send_system_notification(recipient, category, title, message, sender=None, link_url=None, channel='Multi-Channel'):
    """Helper to log system notification and send email notification"""
    notif = models.SystemNotification.objects.create(
        recipient=recipient,
        sender=sender,
        category=category,
        title=title,
        message=message,
        link_url=link_url,
        channel=channel
    )
    
    # Attempt email dispatch
    if recipient.email and channel in ['Email', 'Multi-Channel']:
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            send_mail(
                subject=f"[ZRP Alert - {category}] {title}",
                message=f"Dear {recipient.get_full_name() or recipient.username},\n\n{message}\n\nAccess ZRP Portal: {link_url or 'http://localhost:8000/'}\n\nZimbabwe Republic Police (ZRP) System Notification",
                from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@ZRP.org.zw',
                recipient_list=[recipient.email],
                fail_silently=True
            )
            notif.email_sent = True
            notif.save()
        except Exception as e:
            pass
            
    return notif


@login_required
def notifications_center_view(request):
    notifications = models.SystemNotification.objects.filter(recipient=request.user).order_by('-created_at')
    
    # Category Filter
    category = request.GET.get('category', '').strip()
    if category:
        notifications = notifications.filter(category=category)
        
    unread_count = notifications.filter(is_read=False).count()
    
    context = context_data(request)
    context['page_title'] = 'ZRP Notifications & Alerts Center'
    context['notifications'] = notifications
    context['unread_count'] = unread_count
    context['current_category'] = category
    return render(request, 'notifications_center.html', context)


@login_required
def mark_notification_read_view(request, pk):
    notif = get_object_or_404(models.SystemNotification, pk=pk, recipient=request.user)
    notif.is_read = True
    notif.save()
    
    if notif.link_url:
        return redirect(notif.link_url)
    return redirect('notifications-center')


@login_required
def mark_all_notifications_read_view(request):
    models.SystemNotification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect('notifications-center')


# ─────────────────────────────────────────────────────────
#  ZRP Requirement 13: Unified Platform Command Portal
# ─────────────────────────────────────────────────────────

@login_required
def zrp_unified_platform_view(request):
    today = timezone.now().date()
    
    # 13 Modules Operational Summary
    modules_status = [
        {'name': 'Executive Dashboard', 'icon': 'fas fa-chart-line', 'url': '/registry/analytics/executive/', 'badge': 'Operational'},
        {'name': 'Employee Self-Service', 'icon': 'fas fa-id-card-clip', 'url': '/registry/employee-self-service/', 'badge': f"{models.Borrower.objects.count()} Staff"},
        {'name': 'HR & Leave Management', 'icon': 'fas fa-umbrella-beach', 'url': '/registry/leave-list/', 'badge': f"{models.LeaveRequest.objects.filter(status='Pending').count()} Pending"},
        {'name': 'Attendance & Out-of-Office', 'icon': 'fas fa-clock', 'url': '/registry/attendance/', 'badge': f"{models.EmployeeAttendance.objects.filter(date=today, status='Present').count()} Present"},
        {'name': 'Document & Smart Ingestion', 'icon': 'fas fa-folder-closed', 'url': '/registry/scanned-docs/', 'badge': f"{models.File.objects.count()} Docs"},
        {'name': 'Procurement Management', 'icon': 'fas fa-cart-shopping', 'url': '/registry/procurement/requisitions/', 'badge': f"{models.SupplyRequisition.objects.exclude(status__in=['Approved','Rejected']).count()} Pending"},
        {'name': 'Training, Travel & TSA', 'icon': 'fas fa-plane-slant', 'url': '/registry/travel-tsa/', 'badge': f"{models.TravelRequest.objects.filter(approval_status='Pending').count()} Pending"},
        {'name': 'Acquittals Tracker', 'icon': 'fas fa-hand-holding-dollar', 'url': '/registry/travel-tsa/', 'badge': f"{models.TravelRequest.objects.filter(acquittal_status='Pending Acquittal').count()} Outstanding"},
        {'name': 'Meetings & Minuting', 'icon': 'fas fa-handshake-simple', 'url': '/registry/meetings/', 'badge': f"{models.Meeting.objects.count()} Meetings"},
        {'name': 'Interview Management', 'icon': 'fas fa-user-tie', 'url': '/registry/interviews/', 'badge': f"{models.InterviewExercise.objects.count()} Exercises"},
        {'name': 'Electronic Signatures', 'icon': 'fas fa-file-signature', 'url': '/registry/approvals/center/', 'badge': f"{models.ElectronicApprovalRecord.objects.count()} Signed"},
        {'name': 'Reports & Analytics', 'icon': 'fas fa-chart-pie', 'url': '/registry/analytics/executive/', 'badge': 'Monthly/Quarterly/Annual'},
        {'name': 'Security & Administration', 'icon': 'fas fa-shield-halved', 'url': '/registry/security/center/', 'badge': 'RBAC & Forensic Stream'},
    ]
    
    context = context_data(request)
    context['page_title'] = 'ZRP Unified Integrated Platform Architecture'
    context['modules_status'] = modules_status
    return render(request, 'zrp_unified_platform.html', context)


# ─────────────────────────────────────────────────────────
#  ZRP Requirement 14: Institutional Documentation Library
# ─────────────────────────────────────────────────────────

@login_required
def zrp_institutional_library_view(request):
    templates = models.ZrpDocumentTemplate.objects.all().order_by('category')
    policies = models.InstitutionalPolicyDocument.objects.all().order_by('policy_type')
    
    # Delegated Authority Matrix
    authority_matrix = [
        {'level': 'Officer Level', 'threshold': 'Up to $500.00', 'approver': 'Department Officer / Line Supervisor'},
        {'level': 'Manager Level', 'threshold': '$500.01 – $5,000.00', 'approver': 'Head of Department / Manager'},
        {'level': 'Director / Finance Level', 'threshold': '$5,000.01 – $20,000.00', 'approver': 'Director of Finance & Admin'},
        {'level': 'Chief Director Level', 'threshold': 'Above $20,000.00', 'approver': 'Chief Director (Executive Oversight)'},
    ]
    
    context = context_data(request)
    context['page_title'] = 'ZRP Institutional Documentation & Templates Hub'
    context['templates'] = templates
    context['policies'] = policies
    context['authority_matrix'] = authority_matrix
    return render(request, 'zrp_institutional_library.html', context)


# ─────────────────────────────────────────────────────────
#  ZRP Template Builder — Create / Edit / Delete / Preview
# ─────────────────────────────────────────────────────────

@login_required
def manage_document_template(request, pk=None):
    """Create or edit a ZRP document template with a WYSIWYG body."""
    if pk:
        template = get_object_or_404(models.ZrpDocumentTemplate, pk=pk)
    else:
        template = None

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        category = request.POST.get('category', '').strip() or 'General'
        version = request.POST.get('version', '1.0').strip()
        description = request.POST.get('description', '').strip()
        template_body = request.POST.get('template_body', '').strip()
        is_active = request.POST.get('is_active') == 'on'

        if not title:
            messages.error(request, 'Template title is required.')
            context = context_data(request)
            context['page_title'] = 'Edit Template' if template else 'New Template'
            context['tmpl'] = template
            return render(request, 'manage_template.html', context)

        if template is None:
            template = models.ZrpDocumentTemplate()
            template.created_by = request.user

        template.title = title
        template.category = category
        template.version = version
        template.description = description
        template.template_body = template_body
        template.is_active = is_active
        template.requires_approvals = request.POST.get('requires_approvals') == 'on' or request.POST.get('requires_approvals') == 'true'
        template.approvers_json = request.POST.get('approvers_json', '[]')

        # Optional file upload
        if request.FILES.get('template_file'):
            template.template_file = request.FILES['template_file']

        template.save()

        # Support AJAX quick-save without losing work
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('ajax') == '1':
            return JsonResponse({
                'status': 'success',
                'message': f'Template "{template.title}" updated successfully.',
                'pk': template.pk,
                'version': template.version,
                'title': template.title,
                'updated_at': template.updated_at.strftime('%H:%M:%S')
            })

        messages.success(request, f'Template "{template.title}" saved successfully.')
        return redirect('ZRP-institutional-library')

    context = context_data(request)
    context['page_title'] = 'Edit Template' if template else 'New Template'
    context['tmpl'] = template
    context['approvers_json'] = template.approvers_json if template else '[]'
    context['existing_categories'] = list(
        models.ZrpDocumentTemplate.objects.values_list('category', flat=True).distinct().order_by('category')
    )
    return render(request, 'manage_template.html', context)


@login_required
def delete_document_template(request, pk):
    """Soft-delete (deactivate) or hard-delete a template. Supports AJAX and normal POST."""
    template = get_object_or_404(models.ZrpDocumentTemplate, pk=pk)
    if request.method == 'POST':
        name = template.title
        template.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return HttpResponse(json.dumps({'status': 'success', 'msg': f'"{name}" deleted.'}), content_type='application/json')
        messages.success(request, f'Template "{name}" deleted.')
    return redirect('ZRP-institutional-library')


@login_required
def preview_document_template(request, pk):
    """Render the template body in a clean print-ready ZRP-letterhead view with optional signatories block."""
    template = get_object_or_404(models.ZrpDocumentTemplate, pk=pk)
    approvers = []
    if template.requires_approvals and template.approvers_json:
        try:
            approvers = json.loads(template.approvers_json)
        except Exception:
            approvers = []

    context = context_data(request)
    context['tmpl'] = template
    context['approvers'] = approvers
    context['page_title'] = f'Preview — {template.title}'
    return render(request, 'preview_template.html', context)









# ─────────────────────────────────────────────────────────
#  Offline / Server-Side Audio Transcription Endpoint
# ─────────────────────────────────────────────────────────

@login_required
def transcribe_audio_view(request):
    """
    Accepts an audio blob (WebM/WAV/OGG) from MediaRecorder,
    converts to WAV, runs Vosk (offline) or SpeechRecognition (online),
    and returns the transcript as JSON.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'text': '', 'message': 'POST method required.'})
    import os, tempfile, json as _json

    audio_file = request.FILES.get('audio')
    if not audio_file:
        return JsonResponse({'status': 'error', 'text': '', 'message': 'No audio received.'})

    # Save to temp file
    suffix = '.webm'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_in:
        for chunk in audio_file.chunks():
            tmp_in.write(chunk)
        tmp_in_path = tmp_in.name

    wav_path = tmp_in_path.replace('.webm', '.wav')
    target_lang = request.POST.get('language', 'sho-nglish').strip().lower()
    selected_speaker = request.POST.get('speaker', 'auto').strip()
    previous_speaker = request.POST.get('previous_speaker', '').strip()
    transcript = ''
    method_used = ''

    try:
        # ── Step 1: Handle WAV input ──
        if tmp_in_path.endswith('.wav') or audio_file.name.endswith('.wav'):
            wav_path = tmp_in_path
        else:
            try:
                from pydub import AudioSegment
                audio_seg = AudioSegment.from_file(tmp_in_path)
                audio_seg = audio_seg.set_channels(1).set_frame_rate(16000)
                audio_seg.export(wav_path, format='wav')
            except Exception:
                wav_path = tmp_in_path

        # ── Step 2: Voice Acoustic Detection & Speaker Identification (Diarization) ──
        detected_speaker_tag = ''
        if selected_speaker != 'auto' and selected_speaker:
            detected_speaker_tag = selected_speaker
        else:
            # Estimate speaker voice profile using pitch & RMS energy frequency analysis
            try:
                import wave, audioop
                wf = wave.open(wav_path, 'rb')
                n_frames = wf.getnframes()
                framerate = wf.getframerate()
                bytes_per_sample = wf.getsampwidth()
                frames = wf.readframes(n_frames)
                wf.close()

                if n_frames > 0 and bytes_per_sample > 0:
                    rms = audioop.rms(frames, bytes_per_sample)
                    zcr = audioop.crossrate(frames, bytes_per_sample, n_frames)

                    # Only filter pure digital zero/empty audio (rms < 40), never cutting off soft speech or quiet voices
                    if rms < 40:
                        return JsonResponse({
                            'status': 'silence',
                            'text': '',
                            'raw_text': '',
                            'speaker': 'Speaker 1',
                            'is_same_speaker': True,
                            'message': 'Silence detected.'
                        })
                    
                    # Group into distinct speaker voice profiles based on pitch frequency estimate (ZCR/2)
                    pitch_freq = (zcr * framerate) / (2.0 * max(n_frames, 1))
                    
                    if pitch_freq > 180:
                        detected_speaker_tag = "Speaker 1 (High Pitch)"
                    elif pitch_freq > 110:
                        detected_speaker_tag = "Speaker 2 (Mid Pitch)"
                    else:
                        detected_speaker_tag = "Speaker 3 (Deep Voice)"
                else:
                    detected_speaker_tag = "Speaker 1"
            except Exception:
                detected_speaker_tag = "Speaker 1"

        # ── Step 3: High-Accuracy Server-side SpeechRecognition ──
        if not transcript:
            try:
                import speech_recognition as sr
                r = sr.Recognizer()
                r.energy_threshold = 300
                r.dynamic_energy_threshold = True

                with sr.AudioFile(wav_path) as source:
                    r.adjust_for_ambient_noise(source, duration=0.2)
                    audio_data = r.record(source)

                # Accurate language targeting:
                # sn-ZW natively transcribes ChiShona and common English loanwords used in Zimbabwe
                if target_lang == 'sho-nglish':
                    lang_list = ['sn-ZW', 'en-ZA']
                elif target_lang in ['sn-zw', 'sn', 'shona']:
                    lang_list = ['sn-ZW']
                elif target_lang in ['nd-zw', 'nd', 'ndebele']:
                    lang_list = ['nd-ZW', 'zu-ZA']
                elif target_lang in ['zu-za', 'zulu']:
                    lang_list = ['zu-ZA']
                elif target_lang in ['en-zw']:
                    lang_list = ['en-ZA', 'en-US']
                else:
                    lang_list = ['en-US']

                # Fast speech recognition loop
                for lang in lang_list:
                    try:
                        res = r.recognize_google(audio_data, language=lang)
                        if res and len(res.strip()) > 0:
                            transcript = res
                            lang_names = {
                                'sn-ZW': 'Shona (Sho-Nglish)', 'nd-ZW': 'Ndebele', 'zu-ZA': 'Ndebele/Zulu',
                                'en-ZA': 'Sho-Nglish / Southern African English',
                                'en-ZW': 'Zimbabwe English', 'en-US': 'US English'
                            }
                            method_used = f"Google Speech ({lang_names.get(lang, lang)})"
                            break
                    except sr.UnknownValueError:
                        continue
                    except Exception:
                        continue

            except Exception as sr_err:
                return JsonResponse({
                    'status': 'error',
                    'text': '',
                    'message': f'Speech recognition error: {sr_err}'
                })

        if not transcript:
            return JsonResponse({
                'status': 'error',
                'text': '',
                'message': 'No clear speech detected. Please speak clearly into your microphone.'
            })

        is_same_speaker = bool(previous_speaker and detected_speaker_tag == previous_speaker)
        # In conversational mode, only prefix speaker tag when speaker changes or new turn starts
        if is_same_speaker:
            formatted_transcript = transcript
        else:
            formatted_transcript = f"[{detected_speaker_tag}]: {transcript}"

        return JsonResponse({
            'status': 'success',
            'text': formatted_transcript,
            'raw_text': transcript,
            'speaker': detected_speaker_tag,
            'is_same_speaker': is_same_speaker,
            'method': method_used
        })

    finally:
        # Clean up temp files
        for p in [tmp_in_path, wav_path]:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass



# ─────────────────────────────────────────────────────────────
# SYSTEMS MANAGER EQUIPMENT REGISTER VIEWS
# ─────────────────────────────────────────────────────────────

SM_ROLES = ['Systems Manager', 'System Manager', 'Supt ICT', 'Chief Tech',
            'Deputy Director ICT', 'Deputy Director Communications', 'Deputy Director IT',
            'Chief Director']


def _is_sm_role(user):
    """Returns True if the user has a Systems Manager or above role."""
    if user.is_superuser:
        return True
    try:
        return user.security_profile.role in SM_ROLES
    except Exception:
        return False


@login_required
def sm_equipment_register_list(request):
    if not _is_sm_role(request.user):
        messages.error(request, "Access Denied: This register is for Systems Managers only.")
        return redirect('asset-list')

    entries = models.SystemsManagerEquipmentRegister.objects.all().order_by('-created_at')
    issues = models.SystemsManagerIssue.objects.all().order_by('-date_issued')

    context = {
        'page_title': 'Systems Manager Equipment Register',
        'entries': entries,
        'recent_issues': issues[:20],
        'total_entries': entries.count(),
        'total_issued': entries.filter(status='Issued').count(),
        'total_serviceable': entries.filter(status='Serviceable').count(),
        'total_issues': issues.count(),
    }
    return render(request, 'sm_equipment_register.html', context)


@login_required
def manage_sm_equipment(request, pk=None):
    if not _is_sm_role(request.user):
        messages.error(request, "Access Denied: This register is for Systems Managers only.")
        return redirect('asset-list')

    entry = get_object_or_404(models.SystemsManagerEquipmentRegister, pk=pk) if pk else None
    assets = models.Asset.objects.all().order_by('name')
    users = User.objects.filter(is_active=True).order_by('first_name')
    context = {
        'page_title': 'SM Equipment Entry',
        'entry': entry,
        'assets': assets,
        'users': users,
        'status_choices': models.SystemsManagerEquipmentRegister.STATUS_CHOICES,
    }
    return render(request, 'manage_sm_equipment.html', context)


@login_required
def save_sm_equipment(request):
    if not _is_sm_role(request.user):
        return JsonResponse({'status': 'failed', 'msg': 'Access Denied.'})
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        pk = request.POST.get('id')
        try:
            if pk:
                entry = get_object_or_404(models.SystemsManagerEquipmentRegister, pk=pk)
            else:
                entry = models.SystemsManagerEquipmentRegister()
                entry.created_by = request.user

            entry.equipment_name  = request.POST.get('equipment_name', '').strip()
            entry.serial_number   = request.POST.get('serial_number', '').strip()
            entry.location        = request.POST.get('location', '').strip()
            entry.status          = request.POST.get('status', 'In Store')
            entry.comments        = request.POST.get('comments', '').strip()
            entry.cross_reference = request.POST.get('cross_reference', '').strip()
            entry.assigned_user_name = request.POST.get('assigned_user_name', '').strip()

            uid = request.POST.get('assigned_user')
            entry.assigned_user = User.objects.filter(pk=uid).first() if uid else None

            lid = request.POST.get('linked_asset')
            entry.linked_asset = models.Asset.objects.filter(pk=lid).first() if lid else None

            if not entry.equipment_name:
                resp['msg'] = 'Equipment name is required.'
                return JsonResponse(resp)

            entry.save()
            resp['status'] = 'success'
            resp['msg'] = 'Equipment entry saved successfully.'
            resp['pk'] = entry.pk
        except Exception as e:
            resp['msg'] = str(e)
    return JsonResponse(resp)


@login_required
def delete_sm_equipment(request, pk):
    if not _is_sm_role(request.user):
        return JsonResponse({'status': 'failed', 'msg': 'Access Denied.'})
    entry = get_object_or_404(models.SystemsManagerEquipmentRegister, pk=pk)
    entry.delete()
    messages.success(request, "Equipment register entry deleted.")
    return redirect('sm-equipment-register')


# ─────────────────────────────────────────────────────────────
# SYSTEMS MANAGER ISSUES REGISTER VIEWS
# ─────────────────────────────────────────────────────────────

@login_required
def sm_issues_register_list(request):
    if not _is_sm_role(request.user):
        messages.error(request, "Access Denied: This register is for Systems Managers only.")
        return redirect('asset-list')

    issues = models.SystemsManagerIssue.objects.all().order_by('-date_issued')
    context = {
        'page_title': 'Systems Manager Issues Register',
        'issues': issues,
        'total_issued': issues.filter(status='Issued').count(),
        'total_returned': issues.filter(status='Returned').count(),
        'total_lost': issues.filter(status='Lost').count(),
    }
    return render(request, 'sm_issues_register.html', context)


@login_required
def manage_sm_issue(request, pk=None):
    if not _is_sm_role(request.user):
        messages.error(request, "Access Denied: This register is for Systems Managers only.")
        return redirect('asset-list')

    issue = get_object_or_404(models.SystemsManagerIssue, pk=pk) if pk else None
    equipment_qs = models.SystemsManagerEquipmentRegister.objects.all().order_by('equipment_name')
    users = User.objects.filter(is_active=True).order_by('first_name')
    context = {
        'page_title': 'Record Equipment Issue',
        'issue': issue,
        'equipment_qs': equipment_qs,
        'users': users,
        'status_choices': models.SystemsManagerIssue.STATUS_CHOICES,
    }
    return render(request, 'manage_sm_issue.html', context)


@login_required
def save_sm_issue(request):
    if not _is_sm_role(request.user):
        return JsonResponse({'status': 'failed', 'msg': 'Access Denied.'})
    resp = {'status': 'failed', 'msg': ''}
    if request.method == 'POST':
        pk = request.POST.get('id')
        try:
            if pk:
                issue = get_object_or_404(models.SystemsManagerIssue, pk=pk)
            else:
                issue = models.SystemsManagerIssue()

            equip_id = request.POST.get('equipment')
            if not equip_id:
                resp['msg'] = 'Equipment is required.'
                return JsonResponse(resp)
            issue.equipment = get_object_or_404(models.SystemsManagerEquipmentRegister, pk=equip_id)

            issue.issued_to_name    = request.POST.get('issued_to_name', '').strip()
            issue.issued_to_station = request.POST.get('issued_to_station', '').strip()
            issue.qty               = int(request.POST.get('qty', 1))
            issue.status            = request.POST.get('status', 'Issued')
            issue.remarks           = request.POST.get('remarks', '').strip()
            issue.return_remarks    = request.POST.get('return_remarks', '').strip()

            date_issued_str = request.POST.get('date_issued')
            if date_issued_str:
                from datetime import date as dt_date
                issue.date_issued = dt_date.fromisoformat(date_issued_str)

            date_returned_str = request.POST.get('date_returned')
            issue.date_returned = dt_date.fromisoformat(date_returned_str) if date_returned_str else None

            uid = request.POST.get('issued_to_user')
            issue.issued_to_user = User.objects.filter(pk=uid).first() if uid else None
            issue.issued_by = request.user

            issue.save()

            # Update equipment status if issued/returned
            if issue.status == 'Issued':
                issue.equipment.status = 'Issued'
                issue.equipment.save(update_fields=['status'])
            elif issue.status == 'Returned':
                issue.equipment.status = 'Serviceable'
                issue.equipment.save(update_fields=['status'])

            resp['status'] = 'success'
            resp['msg'] = 'Issue record saved successfully.'
            resp['pk'] = issue.pk
        except Exception as e:
            resp['msg'] = str(e)
    return JsonResponse(resp)


@login_required
def delete_sm_issue(request, pk):
    if not _is_sm_role(request.user):
        return JsonResponse({'status': 'failed', 'msg': 'Access Denied.'})
    issue = get_object_or_404(models.SystemsManagerIssue, pk=pk)
    issue.delete()
    messages.success(request, "Issue record deleted.")
    return redirect('sm-issues-register')
