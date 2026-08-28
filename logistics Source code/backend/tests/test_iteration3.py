"""Iteration 3: tests for 4 new features - Auto Email, Model Learning, Branded PDF Cover, Demo Reset.

Ordering matters: auto-email tests run BEFORE reset-demo (which wipes operational data).
"""
import os
import time
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
def admin_token():
    return _login("admin@tradesentinel.demo", "Admin@123")


@pytest.fixture(scope="module")
def viewer_token():
    return _login("viewer@tradesentinel.demo", "Viewer@123")


# --- Feature 3: Auto Email Rules (RUN FIRST before reset) ---
class TestAutoEmail:
    def test_create_at_risk_shipment_triggers_auto_alert_and_email(self, manager_token, admin_token):
        payload = {
            "origin": "Port of Los Angeles",
            "destination": "Port of Mumbai",
            "carrier": "MSC",
            "product_category": "Pharmaceuticals",
            "product_value": 85000,
            "shipping_method": "Sea",
            "documentation_status": "Missing",
            "status": "At Risk",
        }
        r = requests.post(f"{API}/shipments", headers={"Authorization": f"Bearer {manager_token}"},
                          json=payload, timeout=60)
        assert r.status_code in (200, 201), f"create shipment failed: {r.status_code} {r.text[:300]}"
        ship = r.json()
        sid = ship.get("id") or ship.get("shipment_id") or ship.get("_id")
        assert sid, f"no shipment id in response: {ship}"

        # Allow background processing
        time.sleep(3)

        # Check alerts for auto=true entry for this shipment
        ar = requests.get(f"{API}/alerts?level=High",
                          headers={"Authorization": f"Bearer {manager_token}"}, timeout=30)
        assert ar.status_code == 200
        alerts = ar.json().get("alerts", ar.json() if isinstance(ar.json(), list) else [])
        matching = [a for a in alerts if a.get("shipment_id") == sid and a.get("auto") is True]
        assert matching, f"no auto=true alert found for shipment {sid}. alerts sample: {[{'sid':a.get('shipment_id'),'auto':a.get('auto'),'level':a.get('level')} for a in alerts[:8]]}"

        # Check admin audit logs for auto_email entry
        au = requests.get(f"{API}/admin/audit-logs",
                          headers={"Authorization": f"Bearer {admin_token}"}, timeout=30)
        assert au.status_code == 200
        logs = au.json().get("logs", au.json() if isinstance(au.json(), list) else [])
        auto_email_logs = [l for l in logs if
                           (l.get("action") == "auto_email" or "auto_email" in str(l.get("action", "")))
                           and sid in str(l)]
        assert auto_email_logs, f"no auto_email audit entry for shipment {sid}. Sample actions: {[l.get('action') for l in logs[:15]]}"


# --- Feature 4: Model Learning / Predictions Performance ---
class TestPredictionsPerformance:
    def test_predictions_performance(self, manager_token):
        r = requests.get(f"{API}/predictions/performance",
                         headers={"Authorization": f"Bearer {manager_token}"}, timeout=30)
        assert r.status_code == 200, f"perf failed: {r.status_code} {r.text[:200]}"
        d = r.json()
        for k in ("count", "mae", "accuracy_pct", "within_1_day_pct", "series", "error_buckets", "predictions"):
            assert k in d, f"missing key {k}. got keys: {list(d.keys())}"
        assert isinstance(d["count"], int) and d["count"] >= 0
        assert isinstance(d["series"], list)
        assert isinstance(d["error_buckets"], list)
        assert isinstance(d["predictions"], list)


# --- Feature 2: Branded PDF Cover ---
class TestBrandedPdf:
    REPORT_TYPES = ["shipment-risk", "disruption", "cost-impact",
                    "carrier-performance", "customs", "executive-summary"]

    @pytest.mark.parametrize("rtype", REPORT_TYPES)
    def test_pdf_with_cover(self, manager_token, rtype):
        r = requests.get(f"{API}/reports/{rtype}/pdf",
                         headers={"Authorization": f"Bearer {manager_token}"}, timeout=60)
        assert r.status_code == 200, f"{rtype}: {r.status_code}"
        assert "application/pdf" in r.headers.get("content-type", "")
        assert r.content[:5] == b"%PDF-"
        # Branded cover should push size above simple table PDF baseline
        assert len(r.content) > 3000, f"{rtype} PDF too small ({len(r.content)}b), cover likely missing"


# --- Feature 1: Demo Reset (RUN LAST since it wipes data) ---
class TestDemoReset:
    def test_viewer_forbidden(self, viewer_token):
        r = requests.post(f"{API}/admin/reset-demo",
                          headers={"Authorization": f"Bearer {viewer_token}"}, timeout=30)
        assert r.status_code == 403, f"expected 403 for viewer, got {r.status_code}"

    def test_manager_can_reset_and_reseeds_126(self, manager_token):
        r = requests.post(f"{API}/admin/reset-demo",
                          headers={"Authorization": f"Bearer {manager_token}"}, timeout=120)
        assert r.status_code == 200, f"reset failed: {r.status_code} {r.text[:300]}"
        d = r.json()
        assert "message" in d
        assert d.get("shipments") == 126, f"expected 126 shipments seeded, got {d.get('shipments')}"

        # Verify shipments list still loads
        s = requests.get(f"{API}/shipments",
                         headers={"Authorization": f"Bearer {manager_token}"}, timeout=30)
        assert s.status_code == 200
        body = s.json()
        items = body.get("shipments", body if isinstance(body, list) else [])
        assert len(items) >= 100, f"expected ~126 shipments after reseed, got {len(items)}"
