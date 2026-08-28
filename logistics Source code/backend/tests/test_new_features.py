"""Tests for 3 new features: PDF Reports, Live Demo, Email Alerts."""
import os
import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL") or "http://localhost:8001").rstrip("/")
API = f"{BASE_URL}/api"


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=30)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text[:200]}"
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def manager_token():
    return _login("manager@tradesentinel.demo", "Manager@123")


@pytest.fixture(scope="module")
def viewer_token():
    return _login("viewer@tradesentinel.demo", "Viewer@123")


@pytest.fixture(scope="module")
def admin_token():
    return _login("admin@tradesentinel.demo", "Admin@123")


# --- Feature 1: PDF Reports ---
class TestPdfReports:
    REPORT_TYPES = ["shipment-risk", "disruption", "cost-impact",
                    "carrier-performance", "customs", "executive-summary"]

    @pytest.mark.parametrize("rtype", REPORT_TYPES)
    def test_pdf_report(self, manager_token, rtype):
        r = requests.get(f"{API}/reports/{rtype}/pdf",
                         headers={"Authorization": f"Bearer {manager_token}"}, timeout=60)
        assert r.status_code == 200, f"{rtype} PDF status {r.status_code}: {r.text[:200]}"
        assert "application/pdf" in r.headers.get("content-type", ""), \
            f"{rtype} wrong content-type: {r.headers.get('content-type')}"
        assert r.content[:5] == b"%PDF-", f"{rtype} not a valid PDF (first bytes: {r.content[:10]})"
        assert len(r.content) > 500, f"{rtype} PDF too small: {len(r.content)} bytes"


# --- Feature 2: Live Demo (port-strike) ---
class TestLiveDemo:
    def test_port_strike_full_flow(self, manager_token):
        r = requests.post(f"{API}/demo/port-strike",
                          headers={"Authorization": f"Bearer {manager_token}"}, timeout=60)
        assert r.status_code == 200, f"Demo failed: {r.status_code} {r.text[:300]}"
        data = r.json()
        # 1) detect
        assert "detect" in data
        detect = data["detect"]
        assert detect.get("event_type") == "Strike" or "strike" in (detect.get("title", "").lower())
        # 2) predict
        assert "predict" in data
        eta = data["predict"]["eta"]
        for k in ("best_case", "most_likely", "worst_case"):
            assert k in eta, f"eta missing {k}: {eta.keys()}"
        assert "confidence" in eta
        assert "customs" in data["predict"]
        # 3) impact
        impact = data["impact"]
        assert "affected_count" in impact
        assert "cascade" in impact
        assert "financial" in data
        # 4) recover
        rec = data["recover"]
        assert rec.get("id", "").startswith("REC-DEMO-")
        assert rec.get("status") == "pending"
        # Approve the recommendation
        rid = rec["id"]
        ar = requests.post(f"{API}/recovery/{rid}/approve",
                           headers={"Authorization": f"Bearer {manager_token}"},
                           json={"reason": "test approval"}, timeout=30)
        assert ar.status_code == 200, f"Approve failed: {ar.status_code} {ar.text[:200]}"
        # Verify persistence: fetch recovery recommendations
        lr = requests.get(f"{API}/recovery/recommendations",
                          headers={"Authorization": f"Bearer {manager_token}"}, timeout=30)
        if lr.status_code == 200:
            recs = lr.json().get("recommendations", lr.json() if isinstance(lr.json(), list) else [])
            found = [x for x in recs if x.get("id") == rid]
            if found:
                assert found[0].get("status") == "approved"


# --- Feature 3: Email Alerts ---
class TestEmailAlerts:
    def test_notify_alert_manager(self, manager_token):
        # Fetch a High/Critical alert id
        r = requests.get(f"{API}/alerts", headers={"Authorization": f"Bearer {manager_token}"}, timeout=30)
        assert r.status_code == 200
        alerts = r.json().get("alerts", [])
        target = next((a for a in alerts if a.get("level") in ("High", "Critical")), alerts[0] if alerts else None)
        assert target, "no alerts available"
        aid = target["id"]
        rr = requests.post(f"{API}/alerts/{aid}/notify",
                           headers={"Authorization": f"Bearer {manager_token}"}, timeout=60)
        assert rr.status_code == 200, f"notify failed: {rr.status_code} {rr.text[:300]}"
        body = rr.json()
        assert "recipient" in body and body["recipient"]
        assert "email_id" in body and body["email_id"]

    def test_notify_alert_viewer_forbidden(self, viewer_token, manager_token):
        r = requests.get(f"{API}/alerts", headers={"Authorization": f"Bearer {manager_token}"}, timeout=30)
        aid = r.json()["alerts"][0]["id"]
        rr = requests.post(f"{API}/alerts/{aid}/notify",
                           headers={"Authorization": f"Bearer {viewer_token}"}, timeout=30)
        assert rr.status_code in (401, 403), f"viewer should be forbidden, got {rr.status_code}"

    def test_test_email_endpoint(self, manager_token):
        rr = requests.post(f"{API}/notifications/test-email",
                           headers={"Authorization": f"Bearer {manager_token}"}, timeout=60)
        assert rr.status_code == 200, f"test-email failed: {rr.status_code} {rr.text[:300]}"
        body = rr.json()
        assert body.get("recipient")
        assert body.get("email_id")

    def test_test_email_default_recipient(self, admin_token):
        # Default should resolve to ALERT_RECIPIENT_EMAIL when no pref set
        rr = requests.post(f"{API}/notifications/test-email",
                           headers={"Authorization": f"Bearer {admin_token}"}, timeout=60)
        assert rr.status_code == 200
        # Not strictly asserting value (prefs may be set); just ensure returned
        assert "@" in rr.json().get("recipient", "")
