"""TradeSentinel backend E2E tests.

Uses the public preview URL for realism. Roles: admin/manager/viewer with seed accounts.
"""
import io
import os
import time
import pytest
import requests
from dotenv import dotenv_values

frontend_env = dotenv_values("/app/frontend/.env")
BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or frontend_env.get("REACT_APP_BACKEND_URL") or "http://localhost:8001").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = {"email": "admin@tradesentinel.demo", "password": "Admin@123"}
MANAGER = {"email": "manager@tradesentinel.demo", "password": "Manager@123"}
VIEWER = {"email": "viewer@tradesentinel.demo", "password": "Viewer@123"}


def _login(creds):
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json=creds, timeout=30)
    assert r.status_code == 200, f"login failed for {creds['email']}: {r.status_code} {r.text[:200]}"
    tok = r.json().get("access_token")
    assert tok
    s.headers.update({"Authorization": f"Bearer {tok}"})
    return s, r.json()


@pytest.fixture(scope="session")
def admin_client():
    s, u = _login(ADMIN)
    return s, u


@pytest.fixture(scope="session")
def manager_client():
    s, u = _login(MANAGER)
    return s, u


@pytest.fixture(scope="session")
def viewer_client():
    s, u = _login(VIEWER)
    return s, u


# ---------- Auth ----------
class TestAuth:
    def test_root(self):
        r = requests.get(f"{API}/", timeout=15)
        assert r.status_code == 200
        assert r.json().get("status") == "ok"

    def test_login_manager(self):
        r = requests.post(f"{API}/auth/login", json=MANAGER, timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["role"] == "manager"
        assert d["access_token"]

    def test_login_invalid(self):
        r = requests.post(f"{API}/auth/login", json={"email": "nobody@x.com", "password": "wrong"}, timeout=15)
        assert r.status_code == 401

    def test_me(self, manager_client):
        s, _ = manager_client
        r = s.get(f"{API}/auth/me", timeout=15)
        assert r.status_code == 200
        assert r.json()["email"] == MANAGER["email"]

    def test_protected_no_auth(self):
        r = requests.get(f"{API}/dashboard/overview", timeout=15)
        assert r.status_code in (401, 403)

    def test_register_and_forgot_reset(self):
        email = f"TEST_{int(time.time())}@example.com"
        r = requests.post(f"{API}/auth/register", json={
            "name": "T User", "organization": "TestOrg", "email": email, "phone": "1",
            "password": "Passw0rd!", "role": "viewer"}, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json()["role"] == "viewer"
        # forgot
        r2 = requests.post(f"{API}/auth/forgot-password", json={"email": email}, timeout=15)
        assert r2.status_code == 200
        token = r2.json().get("debug_token")
        assert token
        # reset
        r3 = requests.post(f"{API}/auth/reset-password", json={"token": token, "password": "NewPass1!"}, timeout=15)
        assert r3.status_code == 200
        # login with new
        r4 = requests.post(f"{API}/auth/login", json={"email": email, "password": "NewPass1!"}, timeout=15)
        assert r4.status_code == 200


# ---------- Dashboard / Analytics ----------
class TestDashboard:
    def test_dashboard_overview(self, manager_client):
        s, _ = manager_client
        r = s.get(f"{API}/dashboard/overview", timeout=30)
        assert r.status_code == 200
        d = r.json()
        for k in ("kpis", "risk_overview", "disruptions", "map_shipments", "ports", "prediction_chart"):
            assert k in d
        assert d["kpis"]["total_active"] > 0
        assert len(d["prediction_chart"]) == 7
        assert len(d["map_shipments"]) > 0

    def test_analytics_overview(self, manager_client):
        s, _ = manager_client
        r = s.get(f"{API}/analytics/overview", timeout=30)
        assert r.status_code == 200
        d = r.json()
        for k in ("delay_trend", "status_distribution", "risk_distribution",
                  "cost_by_category", "carrier_performance", "disruption_frequency", "model_performance"):
            assert k in d
        assert len(d["carrier_performance"]) > 0


# ---------- Shipments ----------
class TestShipments:
    created_ids = []

    def test_list_seeded(self, manager_client):
        s, _ = manager_client
        r = s.get(f"{API}/shipments", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["total"] >= 100, f"expected 100+ seeded shipments, got {d['total']}"
        # no _id
        assert all("_id" not in x for x in d["shipments"])

    def test_search_filter(self, manager_client):
        s, _ = manager_client
        r = s.get(f"{API}/shipments", params={"status": "In Transit"}, timeout=30)
        assert r.status_code == 200
        assert all(x["status"] == "In Transit" for x in r.json()["shipments"])
        r = s.get(f"{API}/shipments", params={"risk": "High"}, timeout=30)
        assert r.status_code == 200
        assert all(x["risk_category"] == "High" for x in r.json()["shipments"])

    def test_create_get_update_delete(self, manager_client):
        s, _ = manager_client
        payload = {"origin": "Shanghai", "destination": "Los Angeles", "carrier": "Maersk Line",
                   "product_category": "Electronics", "product_value": 25000, "weight_kg": 500,
                   "shipping_method": "Sea", "status": "Preparing",
                   "customer_name": "TEST_Customer"}
        r = s.post(f"{API}/shipments", json=payload, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["shipment_id"].startswith("TS-2026")
        assert "risk_score" in d
        sid = d["shipment_id"]
        TestShipments.created_ids.append(sid)

        # GET detail
        r2 = s.get(f"{API}/shipments/{sid}", timeout=30)
        assert r2.status_code == 200
        detail = r2.json()
        assert detail["shipment"]["shipment_id"] == sid
        eta = detail["eta_prediction"]
        for k in ("best_case", "most_likely", "worst_case", "confidence"):
            assert k in eta, f"missing {k} in eta_prediction: {eta}"
        assert len(detail["timeline"]) >= 5
        assert "root_cause" in detail

        # PUT update
        payload["customer_name"] = "TEST_Updated"
        r3 = s.put(f"{API}/shipments/{sid}", json=payload, timeout=30)
        assert r3.status_code == 200
        assert r3.json()["customer_name"] == "TEST_Updated"

        # DELETE
        r4 = s.delete(f"{API}/shipments/{sid}", timeout=30)
        assert r4.status_code == 200
        TestShipments.created_ids.remove(sid)
        r5 = s.get(f"{API}/shipments/{sid}", timeout=30)
        assert r5.status_code == 404

    def test_export_csv(self, manager_client):
        s, _ = manager_client
        r = s.get(f"{API}/shipments/export/csv", timeout=30)
        assert r.status_code == 200
        assert "shipment_id" in r.text.splitlines()[0]

    def test_import_csv(self, manager_client):
        s, _ = manager_client
        csv_data = (b"origin,destination,carrier,product_category,product_value,weight_kg\n"
                    b"Shanghai,Rotterdam,DHL,TEST_Imported,1500,120\n")
        # Use a new session without the JSON content-type header
        files = {"file": ("import.csv", io.BytesIO(csv_data), "text/csv")}
        # requests session preserves headers; pass headers=None won't override. Remove Content-Type.
        headers = {k: v for k, v in s.headers.items() if k.lower() != "content-type"}
        r = requests.post(f"{API}/shipments/import/csv", files=files, headers=headers, timeout=30)
        assert r.status_code == 200, r.text
        assert r.json()["imported"] >= 1

    def test_viewer_cannot_create(self, viewer_client):
        s, _ = viewer_client
        r = s.post(f"{API}/shipments", json={"origin": "A", "destination": "B", "carrier": "X",
                                             "product_category": "Y"}, timeout=15)
        assert r.status_code == 403

    @classmethod
    def teardown_class(cls):
        # best-effort cleanup
        try:
            s, _ = _login(MANAGER)
            for sid in list(cls.created_ids):
                s.delete(f"{API}/shipments/{sid}", timeout=15)
        except Exception:
            pass


# ---------- Predictions / Risk ----------
class TestPredictions:
    def test_customs(self, manager_client):
        s, _ = manager_client
        r = s.post(f"{API}/predictions/customs",
                   json={"destination_country": "USA", "product_category": "Electronics",
                         "shipment_value": 25000, "current_congestion": 60,
                         "season": "Normal", "documentation_status": "Complete"}, timeout=30)
        assert r.status_code == 200
        d = r.json()
        for k in ("predicted_clearance_days", "delay_probability", "confidence"):
            assert k in d, f"missing {k} in customs prediction: {d}"

    def test_eta(self, manager_client):
        s, _ = manager_client
        r = s.post(f"{API}/predictions/eta", json={"origin": "Shanghai", "destination": "Los Angeles",
                                                    "carrier": "Maersk Line", "shipping_method": "Sea"}, timeout=30)
        assert r.status_code == 200
        assert "best_case" in r.json()

    def test_risks(self, manager_client):
        s, _ = manager_client
        r = s.get(f"{API}/risks", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert len(d["top_risk_shipments"]) > 0


# ---------- Geopolitical / Impact / Simulation / Routes / Financial ----------
class TestOpsIntel:
    def test_geo_events(self, manager_client):
        s, _ = manager_client
        r = s.get(f"{API}/geopolitical/events", timeout=30)
        assert r.status_code == 200
        assert len(r.json()["events"]) >= 1

    def test_classify(self, manager_client):
        s, _ = manager_client
        r = s.post(f"{API}/geopolitical/classify",
                   json={"text": "Port workers in Rotterdam announced a 3-day strike affecting container traffic."},
                   timeout=60)
        assert r.status_code == 200, r.text
        assert "event" in r.json()

    def test_viewer_cannot_classify(self, viewer_client):
        s, _ = viewer_client
        r = s.post(f"{API}/geopolitical/classify", json={"text": "x"}, timeout=15)
        assert r.status_code == 403

    def test_impact(self, manager_client):
        s, _ = manager_client
        ev = s.get(f"{API}/geopolitical/events", timeout=15).json()["events"][0]
        r = s.post(f"{API}/impact/analyze", json={"disruption": ev}, timeout=30)
        assert r.status_code == 200
        d = r.json()
        for k in ("affected_count", "cascade"):
            assert k in d, f"missing {k}: {d}"

    def test_simulation(self, manager_client):
        s, _ = manager_client
        r = s.post(f"{API}/simulation/run",
                   json={"params": {"scenario_type": "Port Closure", "duration_days": 7, "severity": "High"}},
                   timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert "affected" in d or "affected_shipments" in d

    def test_simulation_compare(self, manager_client):
        s, _ = manager_client
        r = s.post(f"{API}/simulation/run", json={"scenarios": [
            {"name": "A", "duration_days": 3, "severity": "Low"},
            {"name": "B", "duration_days": 7, "severity": "High"}]}, timeout=30)
        assert r.status_code == 200
        assert "comparison" in r.json()

    def test_route_optimize(self, manager_client):
        s, _ = manager_client
        r = s.post(f"{API}/routes/optimize", json={"origin": "Shanghai", "destination": "Rotterdam",
                                                    "priority": "balanced"}, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert "recommended" in d or "routes" in d

    def test_financial(self, manager_client):
        s, _ = manager_client
        r = s.post(f"{API}/financial/impact", json={"shipment_value": 100000, "delay_days": 5}, timeout=15)
        assert r.status_code == 200


# ---------- Recovery ----------
class TestRecovery:
    def test_list_and_decide(self, manager_client):
        s, _ = manager_client
        r = s.get(f"{API}/recovery/recommendations", timeout=15)
        assert r.status_code == 200
        recs = r.json()["recommendations"]
        assert len(recs) > 0
        pending = [r for r in recs if r["status"] == "pending"]
        assert len(pending) > 0, "expected some pending recommendations from seed"
        rid = pending[0]["id"]
        r2 = s.post(f"{API}/recovery/{rid}/approve", json={"reason": "TEST_approve"}, timeout=15)
        assert r2.status_code == 200
        # verify
        r3 = s.get(f"{API}/recovery/recommendations", params={"status": "approved"}, timeout=15)
        assert any(x["id"] == rid for x in r3.json()["recommendations"])


# ---------- Alerts ----------
class TestAlerts:
    def test_flow(self, manager_client):
        s, _ = manager_client
        r = s.get(f"{API}/alerts", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert len(d["alerts"]) > 0
        aid = d["alerts"][0]["id"]
        r2 = s.post(f"{API}/alerts/{aid}/read", timeout=15)
        assert r2.status_code == 200
        r3 = s.post(f"{API}/alerts/{aid}/archive", timeout=15)
        assert r3.status_code == 200
        r4 = s.post(f"{API}/alerts/read-all", timeout=15)
        assert r4.status_code == 200


# ---------- Compliance ----------
class TestCompliance:
    def test_upload(self, manager_client):
        s, _ = manager_client
        content = b"Commercial Invoice\nProduct: Widget\nQty: 100\nValue: 5000\nCountry: China\nHS: 1234.56\n"
        files = {"file": ("test.txt", io.BytesIO(content), "text/plain")}
        headers = {k: v for k, v in s.headers.items() if k.lower() != "content-type"}
        r = requests.post(f"{API}/compliance/analyze", files=files, headers=headers, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()["result"]
        assert "checks" in d and "extracted" in d and "overall" in d


# ---------- Reports ----------
class TestReports:
    @pytest.mark.parametrize("rt", ["shipment-risk", "carrier-performance", "disruption",
                                    "cost-impact", "customs", "summary"])
    def test_report(self, manager_client, rt):
        s, _ = manager_client
        r = s.get(f"{API}/reports/{rt}", timeout=15)
        assert r.status_code == 200
        assert "rows" in r.json()

    def test_export(self, manager_client):
        s, _ = manager_client
        r = s.get(f"{API}/reports/shipment-risk/export", timeout=15)
        assert r.status_code == 200
        assert "Shipment" in r.text.splitlines()[0] if r.text else True


# ---------- Integrations ----------
class TestIntegrations:
    def test_toggle(self, manager_client):
        s, _ = manager_client
        r = s.get(f"{API}/integrations", timeout=15)
        assert r.status_code == 200
        assert len(r.json()["integrations"]) == 9
        r2 = s.post(f"{API}/integrations/shopify/toggle", timeout=15)
        assert r2.status_code == 200
        state = r2.json()["connected"]
        r3 = s.post(f"{API}/integrations/shopify/toggle", timeout=15)
        assert r3.json()["connected"] != state


# ---------- Settings / Admin ----------
class TestSettingsAdmin:
    def test_profile_prefs(self, manager_client):
        s, _ = manager_client
        r = s.put(f"{API}/settings/profile", json={"phone": "+1-555-TEST"}, timeout=15)
        assert r.status_code == 200
        r2 = s.put(f"{API}/settings/preferences", json={"risk_threshold": 60, "email_alerts": True}, timeout=15)
        assert r2.status_code == 200
        r3 = s.get(f"{API}/settings/preferences", timeout=15)
        assert r3.status_code == 200
        assert r3.json()["risk_threshold"] == 60

    def test_admin_users(self, admin_client):
        s, _ = admin_client
        r = s.get(f"{API}/admin/users", timeout=15)
        assert r.status_code == 200
        assert len(r.json()["users"]) >= 3

    def test_admin_audit_logs(self, admin_client):
        s, _ = admin_client
        r = s.get(f"{API}/admin/audit-logs", timeout=15)
        assert r.status_code == 200
        assert len(r.json()["logs"]) > 0

    def test_manager_cannot_admin(self, manager_client):
        s, _ = manager_client
        r = s.get(f"{API}/admin/users", timeout=15)
        assert r.status_code == 403


# ---------- Customer notification / Recovery generate ----------
class TestLLMFeatures:
    def test_recovery_generate_and_notify(self, manager_client):
        s, _ = manager_client
        ships = s.get(f"{API}/shipments", timeout=30).json()["shipments"]
        sid = ships[0]["shipment_id"]
        r = s.post(f"{API}/recovery/generate", json={"shipment_id": sid}, timeout=60)
        assert r.status_code == 200
        rec = r.json()["recommendation"]
        assert rec["id"].startswith("REC-")
        r2 = s.post(f"{API}/notifications/customer",
                    json={"shipment_id": sid, "eta_window": "Aug 18-20"}, timeout=60)
        assert r2.status_code == 200
        assert "message" in r2.json()
