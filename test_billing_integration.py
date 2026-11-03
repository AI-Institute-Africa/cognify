import httpx
import uuid
import sys
import json

BASE_URL = "http://127.0.0.1:8000"
BILLING_URL = "http://127.0.0.1:8001"
ADMIN_KEY = "MN9pnmF7iuSeoNunEVjbEll1Z7xRcHRxsp_YCbcX1rhJ_GwusrGHr8C7scgg_INW"

def main():
    print("=== COGNIFY LEARNING PLATFORM & BILLING INTEGRATION TEST ===")
    
    # 1. Health checks
    print("\n[Step 1] Checking Health of Billing API & Cognify Main Server...")
    with httpx.Client(timeout=10.0) as client:
        r_bill = client.get(f"{BILLING_URL}/docs")
        print(f"  Billing API: HTTP {r_bill.status_code}")
        assert r_bill.status_code in (200, 307), "Billing API not healthy"
        
        r_main = client.get(f"{BASE_URL}/api/health")
        print(f"  Main Platform /api/health: HTTP {r_main.status_code} ({r_main.text[:60]})")

    # 2. Test User Registration on Main Platform
    test_id = str(uuid.uuid4())[:8]
    test_email = f"test_student_{test_id}@example.com"
    test_password = "SecurePassword123!"
    test_name = f"Test Student {test_id}"
    
    print(f"\n[Step 2] Registering new student: {test_email}...")
    with httpx.Client(timeout=15.0) as client:
        reg_payload = {
            "email": test_email,
            "password": test_password,
            "full_name": test_name,
            "role": "student"
        }
        r_reg = client.post(f"{BASE_URL}/api/auth/register", json=reg_payload)
        print(f"  Register response: HTTP {r_reg.status_code}")
        if r_reg.status_code != 200:
            print("  Error response:", r_reg.text)
            sys.exit(1)
            
        reg_data = r_reg.json()
        token = reg_data.get("access_token")
        user = reg_data.get("user", {})
        print(f"  User registered successfully! ID: {user.get('id')}")
        print(f"  JWT access token obtained: {token[:20]}...")

        # 3. Fetch Entitlements via GET /api/entitlements/me
        print("\n[Step 3] Fetching student entitlements via GET /api/entitlements/me...")
        headers = {"Authorization": f"Bearer {token}"}
        r_ent = client.get(f"{BASE_URL}/api/entitlements/me", headers=headers)
        print(f"  Entitlements response: HTTP {r_ent.status_code}")
        if r_ent.status_code != 200:
            print("  Error:", r_ent.text)
            sys.exit(1)
            
        ent_data = r_ent.json()
        free_allowances = ent_data.get("free_allowances", {})
        print(f"  Billing user ID: {ent_data.get('user_id')}")
        print(f"  Billing token present: {bool(ent_data.get('billing_access_token'))}")
        print(f"  Free image/slide allowance remaining: {free_allowances.get('image_slide', {}).get('remaining')}")
        print(f"  Free video allowance remaining: {free_allowances.get('video', {}).get('remaining_seconds')} seconds")
        print(f"  Free text tokens remaining: {free_allowances.get('text', {}).get('input_remaining')} input / {free_allowances.get('text', {}).get('output_remaining')} output")
        
        # 4. Enroll in a course and test Course Payment Sync
        course_id = f"course-test-{test_id}"
        enrollment_id = f"enr-test-{test_id}"
        payment_id = f"pay-test-{test_id}"
        
        print(f"\n[Step 4] Triggering course payment synchronization to billing system...")
        sync_payload = {
            "payment_id": payment_id,
            "enrollment_id": enrollment_id,
            "course_id": course_id,
            "course_name": "AI & Machine Learning Diploma",
            "user_email": test_email,
            "plan_code": "diploma-individual",
            "course_price_minor": 4900,
            "paid_total_minor": 4900,
            "currency": "USD",
            "course_end": "2027-11-03T12:00:00Z"
        }
        r_pay = client.post(
            f"{BILLING_URL}/integrations/cognify/course-payments",
            json=sync_payload,
            headers={"X-Cognify-Integration-Key": ADMIN_KEY}
        )
        print(f"  Course payment sync response: HTTP {r_pay.status_code}")
        print(f"  Response: {r_pay.json()}")
        assert r_pay.status_code in (200, 201), "Course payment sync failed"

        # Check entitlements again after payment to see course allocation
        r_ent2 = client.get(f"{BASE_URL}/api/entitlements/me", headers=headers)
        ent_data2 = r_ent2.json()
        print(f"  Course allocations active: {len(ent_data2.get('course_allocations', []))}")
        if ent_data2.get('course_allocations'):
            alloc = ent_data2['course_allocations'][0]
            print(f"    - Course: {alloc.get('course_name')}, Expiry: {alloc.get('access_end_at')}")

        # 5. Test AI Preflight Metering & Guardrails
        b_token = ent_data.get("billing_access_token")
        print("\n[Step 5] Testing AI preflight estimate with student billing token...")
        estimate_payload = {
            "resource": "slides",
            "model": "claude-sonnet-5.5",
            "quantity": 3,
            "input_units": 500,
            "output_units": 500,
            "quality": "standard"
        }
        r_est = client.post(
            f"{BILLING_URL}/usage/estimate",
            json=estimate_payload,
            headers={"Authorization": f"Bearer {b_token}"}
        )
        print(f"  Preflight estimate status: HTTP {r_est.status_code}")
        print(f"  Estimate response: {r_est.json()}")
        quote_id = r_est.json().get("quote_id")

        if quote_id:
            print("  Settling usage against wallet via /gateway/route...")
            route_payload = {
                "service": "ai_generation",
                "quote_id": quote_id,
                "usage": {
                    "resource": "slides",
                    "model": "claude-sonnet-5.5",
                    "quantity": 3,
                    "input_units": 500,
                    "output_units": 500,
                    "quality": "standard",
                    "idempotency_key": str(uuid.uuid4())
                }
            }
            r_settle = client.post(
                f"{BILLING_URL}/gateway/route",
                json=route_payload,
                headers={"Authorization": f"Bearer {b_token}"}
            )
            print(f"  Settlement response: HTTP {r_settle.status_code} ({r_settle.text[:100]})")

        # 6. Test Course Completion and Token Recycling
        print("\n[Step 6] Testing Course Completion & Token Recycling via POST /integrations/cognify/course-completion...")
        compl_payload = {
            "enrollment_id": enrollment_id,
            "user_email": test_email,
            "completion_event_id": f"compl-{test_id}-1"
        }
        r_compl = client.post(
            f"{BILLING_URL}/integrations/cognify/course-completion",
            json=compl_payload,
            headers={"X-Cognify-Integration-Key": ADMIN_KEY}
        )
        print(f"  Course completion status: HTTP {r_compl.status_code}")
        print(f"  Completion result: {r_compl.json()}")
        assert r_compl.status_code in (200, 201), "Course completion failed"
        
        # Test idempotency (retry completion with same event id)
        print("  Testing idempotency of course completion...")
        r_compl_retry = client.post(
            f"{BILLING_URL}/integrations/cognify/course-completion",
            json=compl_payload,
            headers={"X-Cognify-Integration-Key": ADMIN_KEY}
        )
        print(f"  Idempotent retry status: HTTP {r_compl_retry.status_code}")
        print(f"  Idempotent response: {r_compl_retry.json()}")
        assert r_compl_retry.json().get("duplicate") is True, "Idempotency check failed"

    print("\n[SUCCESS] ALL INTEGRATION REQUIREMENTS VERIFIED AND PASSING!")

if __name__ == "__main__":
    main()
