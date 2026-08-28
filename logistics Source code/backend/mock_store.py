"""
backend/mock_store.py — In-Memory Resilient Data Store
======================================================
Provides complete, deterministic in-memory operational data for all endpoints
when VectorDB is offline or initializing, ensuring the application is 100% functional
out of the box.
"""

from __future__ import annotations
import random
from datetime import datetime, timezone, timedelta
import ml
from seed import PORTS, CARRIERS, CATEGORIES, METHODS, STATUSES, PRIORITIES, CUSTOMERS, _carrier_stats, _gen_shipments, _gen_events, _gen_alerts, _gen_recommendations, _gen_predictions

# Initialize in-memory cache
_carriers = _carrier_stats()
_shipments = _gen_shipments(_carriers)
_events = _gen_events()
_alerts = _gen_alerts(_shipments)
_recommendations = _gen_recommendations(_shipments)
_predictions = _gen_predictions(_shipments)


def get_ports():
    return [{**p, "id": p["code"], "risk_score": round(p["congestion"] * 0.7 + random.uniform(5, 20), 1)} for p in PORTS]


def get_carriers():
    return _carriers


def get_shipments(skip=0, limit=50, status=None, risk_category=None, search=None):
    res = _shipments
    if status:
        res = [s for s in res if s.get("status") == status]
    if risk_category:
        res = [s for s in res if s.get("risk_category") == risk_category]
    if search:
        s_low = search.lower()
        res = [s for s in res if s_low in s.get("shipment_id", "").lower() or s_low in s.get("origin", "").lower() or s_low in s.get("destination", "").lower()]
    return res[skip:skip + limit], len(res)


def get_shipment_by_id(sid):
    for s in _shipments:
        if s.get("id") == sid or s.get("shipment_id") == sid:
            return s
    return None


def get_alerts(unread_only=False):
    if unread_only:
        return [a for a in _alerts if not a.get("read")]
    return _alerts


def get_events():
    return _events


def get_recommendations(status=None):
    if status:
        return [r for r in _recommendations if r.get("status") == status]
    return _recommendations


def get_dashboard_overview():
    total = len(_shipments)
    active = [s for s in _shipments if s["status"] not in ("Delivered", "Cancelled")]
    delayed = [s for s in _shipments if s["status"] == "Delayed"]
    at_risk = [s for s in _shipments if s["status"] == "At Risk"]
    high_risk = [s for s in _shipments if s.get("risk_score", 0) >= 70]
    critical_events = [e for e in _events if e.get("severity") in ("Critical", "High")]

    # Breakdown by category
    cats = {}
    for s in _shipments:
        c = s.get("risk_category", "Low")
        cats[c] = cats.get(c, 0) + 1

    # Route risk averages
    route_risks = [
        {"route": "Asia → North America", "risk": 74.2, "volume": 42},
        {"route": "Asia → Europe", "risk": 68.5, "volume": 38},
        {"route": "Europe → North America", "risk": 41.0, "volume": 24},
        {"route": "Intra-Asia", "risk": 52.8, "volume": 22},
    ]

    return {
        "total_shipments": total,
        "active_shipments": len(active),
        "delayed_shipments": len(delayed),
        "at_risk_shipments": len(at_risk),
        "high_risk_count": len(high_risk),
        "avg_risk_score": round(sum(s.get("risk_score", 0) for s in _shipments) / max(total, 1), 1),
        "active_events_count": len(critical_events),
        "unread_alerts_count": len([a for a in _alerts if not a.get("read")]),
        "pending_recommendations_count": len([r for r in _recommendations if r.get("status") == "pending"]),
        "risk_distribution": cats,
        "top_routes": route_risks,
        "recent_alerts": _alerts[:5],
        "recent_events": _events[:5],
        "high_risk_shipments": high_risk[:8],
    }
