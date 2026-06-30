"""Iteration 46 — Cognify Payment Management Platform (Pre-Paynow Live)
Tests cover:
  - /api/payments/status fail-open contract
  - Super-admin login
  - Dashboard, Providers list + configure + test + enable/disable
  - Products CRUD (Create -> List -> Delete)
  - Settings GET/PUT
  - Generic CRUD: pricing-plans, coupons, taxes, currencies, email-templates
  - Logs (payment, webhook, audit), Revenue timeseries
  - Subscriptions list
  - Activity: online/usage/external
"""
import os, uuid, pytest, requests

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
SA_EMAIL = "takuechakanyuka@gmail.com"
SA_PASS = "SuperAdmin@2026!"


@pytest.fixture(scope="session")
def token():
    r = requests.post(f"{BASE}/api/auth/login",
                      json={"email": SA_EMAIL, "password": SA_PASS}, timeout=30)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    data = r.json()
    tok = data.get("access_token") or data.get("token")
    assert tok, "No token returned"
    return tok


@pytest.fixture(scope="session")
def H(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ---------- Public fail-open ------------------------------------------------
def test_public_payment_status_fail_open():
    r = requests.get(f"{BASE}/api/payments/status", timeout=15)
    assert r.status_code == 200
    j = r.json()
    assert j["available"] is False
    assert j["fail_open"] is True
    assert isinstance(j.get("message"), str) and len(j["message"]) > 0
    assert j.get("provider") in (None, "")


# ---------- Dashboard --------------------------------------------------------
def test_dashboard(H):
    r = requests.get(f"{BASE}/api/super-admin/payments/dashboard", headers=H, timeout=30)
    assert r.status_code == 200, r.text
    j = r.json()
    for k in ("revenue", "transactions", "subscriptions", "recent_transactions",
             "recent_errors", "top_products"):
        assert k in j, f"missing key {k}"
    for k in ("today", "week", "month", "year"):
        assert k in j["revenue"]


# ---------- Providers --------------------------------------------------------
def test_providers_seeded_5(H):
    r = requests.get(f"{BASE}/api/super-admin/payments/providers", headers=H, timeout=30)
    assert r.status_code == 200
    provs = r.json()["providers"]
    slugs = {p["slug"] for p in provs}
    expected = {"paynow", "stripe", "flutterwave", "pesepay", "paypal"}
    assert expected.issubset(slugs), f"missing providers: {expected - slugs}"
    # secrets must be masked (no raw key field returned)
    for p in provs:
        for k in ("integration_key", "secret_key", "client_secret", "webhook_secret",
                  "encryption_key", "api_key"):
            assert p.get(k) in (None, "", "********"), f"{p['slug']}: secret {k} leaked: {p.get(k)!r}"


def test_provider_configure_persist_and_test_connection(H):
    payload = {"integration_id": "TEST_INTG_ID_46", "integration_key": "TEST_KEY_46",
               "merchant_email": "TEST_46@example.com", "environment": "sandbox"}
    r = requests.put(f"{BASE}/api/super-admin/payments/providers/paynow",
                     headers=H, json=payload, timeout=30)
    assert r.status_code == 200, r.text
    # verify persistence via list
    r2 = requests.get(f"{BASE}/api/super-admin/payments/providers", headers=H, timeout=30)
    paynow = next(p for p in r2.json()["providers"] if p["slug"] == "paynow")
    assert paynow.get("integration_id") == "TEST_INTG_ID_46"
    assert paynow.get("merchant_email") == "TEST_46@example.com"
    # test connection (should succeed structurally — provider must implement test_connection)
    r3 = requests.post(f"{BASE}/api/super-admin/payments/providers/paynow/test",
                       headers=H, timeout=30)
    assert r3.status_code == 200, r3.text
    assert "ok" in r3.json()


def test_provider_enable_disable(H):
    r1 = requests.post(f"{BASE}/api/super-admin/payments/providers/stripe/enable",
                       headers=H, timeout=15)
    assert r1.status_code == 200 and r1.json()["ok"] is True
    r2 = requests.post(f"{BASE}/api/super-admin/payments/providers/stripe/disable",
                       headers=H, timeout=15)
    assert r2.status_code == 200 and r2.json()["ok"] is True


# ---------- Products CRUD ---------------------------------------------------
def test_products_crud(H):
    title = f"TEST_PRODUCT_{uuid.uuid4().hex[:6]}"
    body = {"title": title, "description": "ix46", "price": 9.99, "currency": "USD"}
    r = requests.post(f"{BASE}/api/super-admin/payments/products",
                      headers=H, json=body, timeout=30)
    assert r.status_code == 200, r.text
    created = r.json()
    assert created["title"] == title and created["price"] == 9.99
    pid = created["id"]
    # list
    rl = requests.get(f"{BASE}/api/super-admin/payments/products", headers=H, timeout=30)
    assert rl.status_code == 200
    ids = [p["id"] for p in rl.json()["products"]]
    assert pid in ids
    # delete (soft)
    rd = requests.delete(f"{BASE}/api/super-admin/payments/products/{pid}",
                         headers=H, timeout=30)
    assert rd.status_code == 200 and rd.json()["ok"] is True
    # confirm gone from list
    rl2 = requests.get(f"{BASE}/api/super-admin/payments/products", headers=H, timeout=30)
    ids2 = [p["id"] for p in rl2.json()["products"]]
    assert pid not in ids2


# ---------- Settings --------------------------------------------------------
def test_settings_get_and_update(H):
    r = requests.get(f"{BASE}/api/super-admin/payments/settings", headers=H, timeout=15)
    assert r.status_code == 200
    s = r.json()
    assert "fail_open" in s
    new_msg = f"TEST_MSG_{uuid.uuid4().hex[:6]}"
    r2 = requests.put(f"{BASE}/api/super-admin/payments/settings",
                      headers=H, json={"service_unavailable_message": new_msg,
                                       "fail_open": True}, timeout=15)
    assert r2.status_code == 200, r2.text
    r3 = requests.get(f"{BASE}/api/super-admin/payments/settings", headers=H, timeout=15)
    assert r3.json().get("service_unavailable_message") == new_msg


# ---------- Generic CRUD modules -------------------------------------------
@pytest.mark.parametrize("module", ["pricing-plans", "coupons", "taxes",
                                    "currencies", "email-templates"])
def test_generic_crud(H, module):
    r = requests.get(f"{BASE}/api/super-admin/payments/{module}", headers=H, timeout=15)
    assert r.status_code == 200, f"{module}: {r.text}"
    assert "items" in r.json()
    body = {"name": f"TEST_{module}_{uuid.uuid4().hex[:5]}", "value": "x"}
    r2 = requests.post(f"{BASE}/api/super-admin/payments/{module}",
                       headers=H, json=body, timeout=15)
    assert r2.status_code == 200, f"{module}: {r2.text}"
    created = r2.json()
    assert "id" in created
    rd = requests.delete(f"{BASE}/api/super-admin/payments/{module}/{created['id']}",
                         headers=H, timeout=15)
    assert rd.status_code == 200 and rd.json()["ok"] is True


# ---------- Subscriptions, Transactions, Invoices, Receipts, Refunds -------
@pytest.mark.parametrize("path", ["subscriptions", "transactions", "invoices",
                                  "receipts", "refunds"])
def test_list_endpoints(H, path):
    r = requests.get(f"{BASE}/api/super-admin/payments/{path}", headers=H, timeout=15)
    assert r.status_code == 200, r.text
    j = r.json()
    # subscriptions returns {subscriptions}, others {items,total,offset,limit}
    assert ("items" in j) or ("subscriptions" in j)


# ---------- Logs + revenue --------------------------------------------------
@pytest.mark.parametrize("path", ["payment-logs", "webhook-logs", "audit-logs"])
def test_logs(H, path):
    r = requests.get(f"{BASE}/api/super-admin/payments/{path}", headers=H, timeout=15)
    assert r.status_code == 200
    assert "items" in r.json()


def test_revenue_timeseries(H):
    r = requests.get(f"{BASE}/api/super-admin/payments/revenue/timeseries?days=30",
                     headers=H, timeout=15)
    assert r.status_code == 200
    assert "series" in r.json() and isinstance(r.json()["series"], list)


# ---------- Activity --------------------------------------------------------
def test_activity_online(H):
    r = requests.get(f"{BASE}/api/super-admin/activity/online", headers=H, timeout=15)
    assert r.status_code == 200
    j = r.json()
    assert "users" in j and "count" in j
    # the super admin who just made the call should be present in online list
    emails = [u.get("email") for u in j["users"]]
    assert SA_EMAIL in emails, f"super admin not online; emails={emails}"


def test_activity_usage(H):
    r = requests.get(f"{BASE}/api/super-admin/activity/usage", headers=H, timeout=15)
    assert r.status_code == 200
    j = r.json()
    assert "users" in j
    if j["users"]:
        assert "total_hours" in j["users"][0]


def test_activity_external(H):
    r = requests.get(f"{BASE}/api/super-admin/activity/external", headers=H, timeout=15)
    assert r.status_code == 200
    j = r.json()
    assert "anonymous_visitors" in j and "external_referred_users" in j


# ---------- Auth gate -------------------------------------------------------
def test_super_admin_endpoint_requires_auth():
    r = requests.get(f"{BASE}/api/super-admin/payments/dashboard", timeout=15)
    assert r.status_code in (401, 403)
