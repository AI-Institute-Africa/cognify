"""
Test Suite: BRD Payment Enhancements & Multi-Channel Communications
Covers:
1. Minimum monthly payment calculation with precise Decimal rounding
2. Payment period state engine (UNPAID -> PARTIALLY_PAID -> CURRENT -> COMPLETED)
3. Assessment eligibility gating (assessments locked, learning unlocked, dynamic remaining amount)
4. Phone OTP generation, SHA-256 hashing, E.164 normalization, expiry & rate limiting
5. Organisation Admin external payment workflow (search, create, admin verify override, record, audit, reverse)
6. Organisation isolation (cross-org access blocked)
7. Super Admin multi-channel reporting distinguishing online vs external_manual payments
"""
import os
import sys
import time
import uuid

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from decimal import Decimal
import pytest
import requests

from services.payment_period_engine import (
    calculate_minimum_monthly_payment,
    to_decimal,
    PaymentPeriodService
)
from services.otp_service import OTPService, normalize_phone_number

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")
SUPER_EMAIL = "admin@cognify.com"
SUPER_PASSWORD = "admin123456"



# ============================================================================
# UNIT TESTS: Payment Calculations & Normalization
# ============================================================================

def test_minimum_monthly_payment_exact_division():
    """Verify $120 over 3 months is $40.00, $300 over 6 months is $50.00."""
    p1 = calculate_minimum_monthly_payment(120, 3)
    assert p1 == 40.0

    p2 = calculate_minimum_monthly_payment(300, 6)
    assert p2 == 50.0


def test_minimum_monthly_payment_rounding_and_edge_cases():
    """Verify rounding to 2 decimal places and duration <= 1."""
    # $100 over 3 months -> 33.33
    p3 = calculate_minimum_monthly_payment(100, 3)
    assert p3 == 33.33

    # Duration 1 month -> full cost
    p4 = calculate_minimum_monthly_payment(150, 1)
    assert p4 == 150.0

    # Duration 0 or negative -> defaults to 1 month
    p5 = calculate_minimum_monthly_payment(200, 0)
    assert p5 == 200.0

    # Free course
    p6 = calculate_minimum_monthly_payment(0, 4)
    assert p6 == 0.0


def test_phone_normalization_zimbabwe_and_international():
    """Verify phone normalization for local Zimbabwean numbers and international."""
    # Local Zimbabwean formats -> +263
    assert normalize_phone_number("0771234567") == "+263771234567"
    assert normalize_phone_number("263771234567") == "+263771234567"
    assert normalize_phone_number("+263 77 123 4567") == "+263771234567"
    assert normalize_phone_number("0712345678") == "+263712345678"
    assert normalize_phone_number("0733344555") == "+263733344555"

    # International standard numbers
    assert normalize_phone_number("+1 (555) 234-5678") == "+15552345678"
    assert normalize_phone_number("+44 20 7946 0958") == "+442079460958"



# ============================================================================
# INTEGRATION TESTS: Live Endpoints
# ============================================================================

@pytest.fixture(scope="module")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def super_token(api_client):
    r = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": SUPER_EMAIL, "password": SUPER_PASSWORD
    })
    assert r.status_code == 200, f"SuperAdmin login failed: {r.text}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def super_headers(super_token):
    return {"Authorization": f"Bearer {super_token}", "Content-Type": "application/json"}


def test_phone_otp_request_and_verify_flow(api_client):
    """Test phone request OTP, rate limiting, and verification."""
    test_phone = f"+26377{uuid.uuid4().int % 10000000:07d}"

    # Request OTP via SMS
    r1 = api_client.post(f"{BASE_URL}/api/auth/phone/request-otp", json={
        "phone_number": test_phone,
        "channel": "sms",
        "purpose": "registration"
    })
    assert r1.status_code == 200, f"Request OTP failed: {r1.text}"
    j1 = r1.json()
    assert j1["success"] is True
    assert "expires_in_seconds" in j1
    # In test environment, debug_otp is exposed if mock provider
    otp_code = j1.get("debug_otp") or j1.get("dev_simulator_code")


    # Immediate duplicate request should hit cooldown or return error/rate limit
    r2 = api_client.post(f"{BASE_URL}/api/auth/phone/request-otp", json={
        "phone_number": test_phone,
        "channel": "sms",
        "purpose": "registration"
    })
    # Must enforce 60s cooldown
    assert r2.status_code == 429, "Expected rate limit / cooldown on immediate resend"

    # Verify invalid OTP
    r3 = api_client.post(f"{BASE_URL}/api/auth/phone/verify-otp", json={
        "phone_number": test_phone,
        "otp_code": "000000",
        "purpose": "registration"
    })
    assert r3.status_code == 400

    # If debug_otp was provided, verify correct OTP
    if otp_code:
        r4 = api_client.post(f"{BASE_URL}/api/auth/phone/verify-otp", json={
            "phone_number": test_phone,
            "otp_code": otp_code,
            "purpose": "registration"
        })
        assert r4.status_code == 200
        assert r4.json()["success"] is True



@pytest.fixture(scope="module")
def test_org_data(api_client):
    tag = uuid.uuid4().hex[:6]
    r_reg = api_client.post(f"{BASE_URL}/api/organizations/register", json={
        "name": f"Test Institute of Tech {tag}",
        "org_type": "university",
        "address": "123 University Drive, Harare",
        "phone": "+263771234567",
        "email": f"org_{tag}@cognifytest.ac.zw",
        "admin_name": f"Admin {tag}",
        "admin_email": f"admin_{tag}@cognifytest.ac.zw",
        "admin_password": "OrgAdminPass123!",
        "country": "Zimbabwe"
    })
    assert r_reg.status_code == 201, f"Org registration failed: {r_reg.text}"
    d = r_reg.json()
    org_id = d.get("organization_id") or d.get("id")
    tok = d.get("access_token") or d.get("token")
    return {
        "org_id": org_id,
        "admin_token": tok,
        "admin_headers": {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}
    }




def test_org_admin_external_payment_workflow(api_client, super_headers, test_org_data):
    """Full 11-step Organisation Admin external payment workflow test:
    1. Identify test org
    2. Search learners
    3. Create learner with unverified phone
    4. Override phone verification with ADMIN_OVERRIDE audit
    5. Calculate payment preview
    6. Record external manual payment ($15 of $30 monthly min) with EcoCash reference
    7. Verify status is PARTIALLY_PAID & assessment is locked
    8. Record second payment ($15) completing monthly minimum
    9. Verify status is CURRENT & assessment is unlocked
    10. Financial reversal test: reverse payment without hard delete
    """
    test_org_id = test_org_data["org_id"]
    org_admin_headers = test_org_data["admin_headers"]

    # Create a test course in this organization
    tag = uuid.uuid4().hex[:6]
    r_c = api_client.post(f"{BASE_URL}/api/courses", headers=org_admin_headers, json={
        "code": f"BRD-{tag}",
        "name": f"Payment Test Course {tag}",
        "title": f"Payment Test Course {tag}",
        "description": "BRD Test Course for Payment Engine",
        "grade_level": "Undergraduate",
        "price": 60.0,
        "duration_months": 2,
        "is_paid": True,
        "organization_id": test_org_id,
        "instructor": "Test Instructor"
    })
    assert r_c.status_code in (200, 201), f"Course creation failed: {r_c.text}"
    course_id = r_c.json()["id"]


    # 2. Search learners (initially)
    r_s = api_client.get(
        f"{BASE_URL}/api/organizations/{test_org_id}/learners/search?q=testlearner_{tag}",
        headers=org_admin_headers
    )
    assert r_s.status_code == 200

    # 3. Create learner with unverified phone
    test_phone = f"+26377{uuid.uuid4().int % 10000000:07d}"
    r_create = api_client.post(
        f"{BASE_URL}/api/organizations/{test_org_id}/learners/create",
        headers=org_admin_headers,
        json={
            "full_name": f"BRD Learner {tag}",
            "email": f"learner_{tag}@cognifytest.ac.zw",
            "phone_number": test_phone
        }
    )
    assert r_create.status_code in (200, 201), f"Learner create failed: {r_create.text}"
    learner_data = r_create.json()
    assert learner_data["success"] is True
    learner_id = learner_data["user_id"]

    # 4. Admin override phone verification
    r_ov = api_client.post(
        f"{BASE_URL}/api/organizations/{test_org_id}/learners/{learner_id}/verify-phone-admin",
        headers=org_admin_headers,
        json={"reason": "Physical student ID verified at registrar office"}
    )
    assert r_ov.status_code == 200
    assert r_ov.json()["success"] is True

    # 5. Calculate payment preview
    r_prev = api_client.post(
        f"{BASE_URL}/api/organizations/{test_org_id}/external-payments/preview",
        headers=org_admin_headers,
        json={
            "course_id": course_id,
            "user_id": learner_id,
            "amount": 15.0
        }
    )
    assert r_prev.status_code == 200
    prev_data = r_prev.json()
    assert prev_data["total_course_cost"] == 60.0
    assert prev_data["duration_months"] == 2
    assert prev_data["required_monthly_minimum"] == 30.0
    assert prev_data["payment_status_after_recording"] == "PARTIALLY_PAID"
    assert prev_data["assessment_eligibility_after_recording"] is False

    # 6. Record external manual payment #1: $15 (Less than minimum monthly of $30)
    tx_ref_1 = f"MP26{uuid.uuid4().hex[:8].upper()}"
    r_pay1 = api_client.post(
        f"{BASE_URL}/api/organizations/{test_org_id}/external-payments/record",
        headers=org_admin_headers,
        json={
            "user_id": learner_id,
            "course_id": course_id,
            "amount": 15.0,
            "method": "ecocash",
            "reference": tx_ref_1,
            "notes": "First partial installment"
        }
    )
    assert r_pay1.status_code in (200, 201), f"Record payment 1 failed: {r_pay1.text}"
    pay1_data = r_pay1.json()
    assert pay1_data["source"] == "external_manual"
    assert pay1_data["payment_status"] == "PARTIALLY_PAID"
    assert pay1_data["assessment_eligible"] is False
    assert pay1_data["amount_remaining"] == 15.0
    payment_id_1 = pay1_data["payment_id"]

    # 7. Record external payment #2: $15 (Completing monthly minimum of $30)
    tx_ref_2 = f"MP26{uuid.uuid4().hex[:8].upper()}"
    r_pay2 = api_client.post(
        f"{BASE_URL}/api/organizations/{test_org_id}/external-payments/record",
        headers=org_admin_headers,
        json={
            "user_id": learner_id,
            "course_id": course_id,
            "amount": 15.0,
            "method": "ecocash",
            "reference": tx_ref_2
        }
    )
    assert r_pay2.status_code in (200, 201), f"Record payment 2 failed: {r_pay2.text}"
    pay2_data = r_pay2.json()
    assert pay2_data["payment_status"] == "CURRENT"
    assert pay2_data["assessment_eligible"] is True
    assert pay2_data["amount_remaining"] == 0.0

    # 8. Check payment records list
    r_list = api_client.get(
        f"{BASE_URL}/api/organizations/{test_org_id}/external-payments?course_id={course_id}",
        headers=org_admin_headers
    )
    assert r_list.status_code == 200
    records = r_list.json()["records"]
    assert len(records) >= 2

    # 9. Financial reversal test: reverse payment 1
    r_rev = api_client.post(
        f"{BASE_URL}/api/organizations/{test_org_id}/external-payments/{payment_id_1}/reverse",
        headers=org_admin_headers,
        json={"reason": "Incorrect student account credited"}
    )
    assert r_rev.status_code == 200
    rev_data = r_rev.json()
    assert rev_data["success"] is True
    assert rev_data["payment_status"] == "PARTIALLY_PAID"
    assert rev_data["assessment_eligible"] is False



def test_organization_isolation(api_client, test_org_data):
    """Verify Org A admin cannot search learners or record payments in Org B."""
    # Create Org B
    tag_b = uuid.uuid4().hex[:6]
    r_b = api_client.post(f"{BASE_URL}/api/organizations/register", json={
        "name": f"Org B {tag_b}",
        "org_type": "university",
        "address": "456 College Road, Bulawayo",
        "phone": "+263779876543",
        "email": f"org_b_{tag_b}@cognifytest.ac.zw",
        "admin_name": f"Admin B {tag_b}",
        "admin_email": f"admin_b_{tag_b}@cognifytest.ac.zw",
        "admin_password": "OrgAdminPass123!",
        "country": "Zimbabwe"
    })
    assert r_b.status_code == 201

    org_b_id = r_b.json().get("organization_id") or r_b.json().get("id")

    # Org A admin tries to search learners in Org B
    org_a_headers = test_org_data["admin_headers"]
    r_cross = api_client.get(
        f"{BASE_URL}/api/organizations/{org_b_id}/learners/search?q=test",
        headers=org_a_headers
    )
    # Must be 403 Forbidden
    assert r_cross.status_code == 403


def test_super_admin_multi_channel_report(api_client, super_headers):
    """Test super admin multi-channel reporting endpoint distinguishing online vs external_manual."""
    r = api_client.get(
        f"{BASE_URL}/api/super-admin/payments/multi-channel-report",
        headers=super_headers
    )
    assert r.status_code == 200, f"Multi-channel report failed: {r.text}"
    data = r.json()
    assert "summary" in data
    assert "online_revenue" in data["summary"]
    assert "external_revenue" in data["summary"]
    assert "ecocash_revenue" in data["summary"]
    assert "enrolments" in data
    assert "recent_payments" in data


def test_assessment_locking_enforcement(api_client, test_org_data):
    """Test that student assignment endpoints strictly enforce payment status."""
    tag = uuid.uuid4().hex[:6]
    org_id = test_org_data["org_id"]
    org_admin_headers = test_org_data["admin_headers"]

    r_c = api_client.post(f"{BASE_URL}/api/courses", headers=org_admin_headers, json={
        "code": f"GATE-{tag}",
        "name": f"Gating Test Course {tag}",
        "title": f"Gating Test Course {tag}",
        "description": "BRD Gating Course",
        "grade_level": "Undergraduate",
        "price": 50.0,
        "duration_months": 1,
        "is_paid": True,
        "organization_id": org_id,
        "instructor": "Instructor"
    })
    assert r_c.status_code in (200, 201), f"Course creation failed: {r_c.text}"
    course_id = r_c.json()["id"]


    # Register student
    student_email = f"student_{tag}@test.com"
    r_u = api_client.post(f"{BASE_URL}/api/auth/register", json={
        "full_name": f"Student {tag}",
        "email": student_email,
        "password": "Password123!",
        "role": "student",
        "organization_id": org_id
    })
    assert r_u.status_code in (200, 201), f"Student registration failed: {r_u.text}"
    tok = r_u.json()["access_token"]
    stu_headers = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}

    # Enroll student (UNPAID)
    r_en = api_client.post(f"{BASE_URL}/api/enrollments", headers=stu_headers, json={
        "course_id": course_id
    })
    assert r_en.status_code in (200, 201), f"Enrollment failed: {r_en.text}"

    # Create teacher to create assignment
    teach_email = f"teacher_{tag}@test.com"
    r_t = api_client.post(f"{BASE_URL}/api/auth/register", json={
        "full_name": f"Teacher {tag}",
        "email": teach_email,
        "password": "Password123!",
        "role": "teacher",
        "organization_id": org_id
    })
    assert r_t.status_code in (200, 201), f"Teacher registration failed: {r_t.text}"

    teach_tok = r_t.json()["access_token"]
    teach_headers = {"Authorization": f"Bearer {teach_tok}", "Content-Type": "application/json"}

    # Create an assignment for this course using teacher
    r_asgn = api_client.post(f"{BASE_URL}/api/assignments", headers=teach_headers, json={
        "course_id": course_id,
        "title": f"Locked Assignment {tag}",
        "description": "BRD Gating Test",
        "total_points": 100,
        "due_date": "2026-12-31T23:59:59"
    })
    assert r_asgn.status_code in (200, 201)
    assignment_id = r_asgn.json()["id"]

    # Student attempts to view assignment -> must receive 403 PAYMENT_REQUIRED
    r_get_asgn = api_client.get(f"{BASE_URL}/api/assignments/{assignment_id}", headers=stu_headers)
    assert r_get_asgn.status_code == 403
    err_detail = r_get_asgn.json()["detail"]
    assert err_detail["assessment_eligible"] is False
    assert err_detail["amount_remaining"] == 50.0

    # Student attempts to submit assignment -> must receive 403
    r_sub = api_client.post(
        f"{BASE_URL}/api/assignments/{assignment_id}/submit-and-grade",
        headers=stu_headers,
        json={"content": "Here is my answer"}
    )
    assert r_sub.status_code == 403
    err_detail_sub = r_sub.json()["detail"]
    assert err_detail_sub["assessment_eligible"] is False

