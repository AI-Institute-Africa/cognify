"""
Iteration 37 - Course Analytics Dashboard + Send Message E2E
- GET /api/analytics/course-dashboard (org_admin, teacher scope)
- POST /api/messages + GET /api/messages/conversation/{user_id}
"""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://knowledge-sync-9.preview.emergentagent.com').rstrip('/')

ORG_ADMIN = {"email": "test.orgadmin@cognify.edu", "password": "admin123"}
TEACHER = {"email": "demo.teacher@eduos.edu", "password": "demo123"}
STUDENT = {"email": "demo.student@cognify.edu", "password": "demo123"}


def _login(creds):
    r = requests.post(f"{BASE_URL}/api/auth/login", json=creds, timeout=30)
    assert r.status_code == 200, f"Login failed for {creds['email']}: {r.status_code} {r.text}"
    body = r.json()
    return body["access_token"], body["user"]


@pytest.fixture(scope="module")
def org_admin_session():
    token, user = _login(ORG_ADMIN)
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return s, user


@pytest.fixture(scope="module")
def teacher_session():
    token, user = _login(TEACHER)
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return s, user


@pytest.fixture(scope="module")
def student_session():
    token, user = _login(STUDENT)
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    return s, user


# ---------- Course Analytics Dashboard ----------

class TestCourseAnalyticsDashboard:
    def test_endpoint_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/analytics/course-dashboard", timeout=30)
        assert r.status_code in (401, 403)

    def test_org_admin_scope(self, org_admin_session):
        s, _ = org_admin_session
        r = s.get(f"{BASE_URL}/api/analytics/course-dashboard", timeout=60)
        assert r.status_code == 200, r.text
        data = r.json()
        # Shape
        assert data["scope"] == "organization"
        for k in ("summary", "per_course", "at_risk", "top_students", "engagement_trend"):
            assert k in data, f"Missing key: {k}"
        summary = data["summary"]
        for sk in ("total_courses", "total_enrolled", "total_completed", "completion_rate",
                   "avg_grade", "pass_rate", "at_risk_count", "active_students"):
            assert sk in summary, f"Missing summary key: {sk}"
        # types
        assert isinstance(data["per_course"], list)
        assert isinstance(data["at_risk"], list)
        assert isinstance(data["top_students"], list)
        assert isinstance(data["engagement_trend"], list)
        # engagement_trend - 14 buckets
        assert len(data["engagement_trend"]) == 14, f"Expected 14 buckets, got {len(data['engagement_trend'])}"
        for bucket in data["engagement_trend"]:
            assert "date" in bucket and "attempts" in bucket and "passes" in bucket

    def test_teacher_scope(self, teacher_session):
        s, _ = teacher_session
        r = s.get(f"{BASE_URL}/api/analytics/course-dashboard", timeout=60)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["scope"] == "teacher"
        assert "summary" in data and "per_course" in data
        assert len(data["engagement_trend"]) == 14

    def test_student_forbidden(self, student_session):
        s, _ = student_session
        r = s.get(f"{BASE_URL}/api/analytics/course-dashboard", timeout=30)
        assert r.status_code == 403

    def test_per_course_fields(self, org_admin_session):
        s, _ = org_admin_session
        r = s.get(f"{BASE_URL}/api/analytics/course-dashboard", timeout=60)
        assert r.status_code == 200
        data = r.json()
        if data["per_course"]:
            row = data["per_course"][0]
            for k in ("course_id", "course_name", "enrolled", "completed",
                      "completion_rate", "pass_rate", "avg_grade", "quiz_attempts"):
                assert k in row, f"Missing per_course key: {k}"


# ---------- Messaging E2E ----------

class TestMessagingE2E:
    def test_send_message_and_fetch_conversation(self, org_admin_session, student_session):
        org_s, org_user = org_admin_session
        stu_s, stu_user = student_session

        content = "TEST_iteration37 hello from org_admin"
        payload = {
            "recipient_id": stu_user["id"],
            "content": content,
            "message_type": "text",
        }
        r = org_s.post(f"{BASE_URL}/api/messages", json=payload, timeout=30)
        assert r.status_code in (200, 201), f"Send failed: {r.status_code} {r.text}"
        body = r.json()
        assert "id" in body, f"Missing message id: {body}"
        msg_id = body["id"]

        # Fetch conversation from org_admin perspective
        r2 = org_s.get(f"{BASE_URL}/api/messages/conversation/{stu_user['id']}", timeout=30)
        assert r2.status_code == 200, r2.text
        conv = r2.json()
        assert isinstance(conv, list)
        ids = [m.get("id") for m in conv]
        contents = [m.get("content") for m in conv]
        assert msg_id in ids, f"Sent message id not in conversation. ids={ids}"
        assert content in contents

        # Fetch conversation from student side
        r3 = stu_s.get(f"{BASE_URL}/api/messages/conversation/{org_user['id']}", timeout=30)
        assert r3.status_code == 200, r3.text
        conv2 = r3.json()
        assert any(m.get("id") == msg_id for m in conv2), "Student cannot see the message"

    def test_send_to_invalid_recipient(self, org_admin_session):
        org_s, _ = org_admin_session
        payload = {"recipient_id": "nonexistent-user-id-xyz", "content": "hi", "message_type": "text"}
        r = org_s.post(f"{BASE_URL}/api/messages", json=payload, timeout=30)
        assert r.status_code == 404
