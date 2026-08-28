"""TradeSentinel statistical prediction & analytics engines.

These are deterministic, explainable models seeded from historical demo data.
They are designed to be swapped for trained ML models later (same interface).
All outputs include a confidence score. Predictions are estimates, never guarantees.
"""
import hashlib
from datetime import datetime, timedelta, timezone

# ---- reference tables (would come from a trained model / real datasets) ----

BASE_CUSTOMS_DAYS = {  # normal clearance time by destination country
    "USA": 2.6, "China": 3.4, "India": 3.8, "Germany": 2.2, "UK": 2.4,
    "Netherlands": 2.0, "UAE": 2.8, "Singapore": 1.8, "Brazil": 4.6,
    "Japan": 2.3, "Australia": 2.9, "France": 2.5, "Canada": 2.7,
}

CATEGORY_RISK = {  # customs scrutiny multiplier by product category
    "Electronics": 1.35, "Pharmaceuticals": 1.6, "Textiles": 1.1,
    "Automotive": 1.25, "Food & Beverage": 1.45, "Machinery": 1.2,
    "Chemicals": 1.55, "Consumer Goods": 1.0, "Luxury": 1.4,
}

SEASON_FACTOR = {"Peak": 1.4, "Holiday": 1.5, "Normal": 1.0, "Off-Peak": 0.85}


def _seed(*parts) -> float:
    """Deterministic pseudo-random 0..1 from string parts (reproducible)."""
    h = hashlib.md5("|".join(str(p) for p in parts).encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def _clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, v))


# --------------------------------------------------------------------------
# Unified risk scoring
# --------------------------------------------------------------------------
DEFAULT_RISK_WEIGHTS = {
    "port": 0.22, "customs": 0.20, "geopolitical": 0.22,
    "carrier": 0.16, "route": 0.12, "weather": 0.08,
}


def compute_risk(factors: dict, weights: dict | None = None) -> dict:
    """factors: each 0..100. Returns unified score 0..100 + explainability."""
    w = weights or DEFAULT_RISK_WEIGHTS
    contributions = {}
    total = 0.0
    for k, weight in w.items():
        f = float(factors.get(k, 0))
        contrib = f * weight
        contributions[k] = round(contrib, 1)
        total += contrib
    score = round(_clamp(total), 1)
    if score >= 75:
        category = "Critical"
    elif score >= 55:
        category = "High"
    elif score >= 35:
        category = "Moderate"
    else:
        category = "Low"
    return {
        "score": score,
        "category": category,
        "factors": {k: round(float(factors.get(k, 0)), 1) for k in w},
        "contributions": contributions,
        "weights": w,
    }


# --------------------------------------------------------------------------
# Customs delay prediction
# --------------------------------------------------------------------------
def predict_customs(payload: dict) -> dict:
    dest = payload.get("destination_country", "USA")
    category = payload.get("product_category", "Consumer Goods")
    value = float(payload.get("shipment_value", 1000) or 0)
    congestion = float(payload.get("current_congestion", 40) or 0)  # 0..100
    season = payload.get("season", "Normal")
    docs = payload.get("documentation_status", "Complete")

    normal = BASE_CUSTOMS_DAYS.get(dest, 3.0)
    cat_mult = CATEGORY_RISK.get(category, 1.0)
    season_mult = SEASON_FACTOR.get(season, 1.0)
    doc_penalty = {"Complete": 0.0, "Incomplete": 1.6, "Missing": 3.0}.get(docs, 0.5)
    value_penalty = 0.9 if value > 50000 else (0.4 if value > 10000 else 0.0)
    congestion_days = (congestion / 100.0) * 2.4

    predicted = normal * cat_mult * season_mult + doc_penalty + value_penalty + congestion_days
    predicted = round(predicted, 1)
    delay = round(max(0.0, predicted - normal), 1)
    delay_prob = round(_clamp(20 + congestion * 0.5 + doc_penalty * 12 + (cat_mult - 1) * 60), 0)
    # confidence higher when inputs complete & congestion known
    confidence = round(_clamp(92 - doc_penalty * 6 - abs(congestion - 50) * 0.05, 55, 96), 0)
    if delay_prob >= 65:
        risk_cat = "High"
    elif delay_prob >= 40:
        risk_cat = "Moderate"
    else:
        risk_cat = "Low"
    return {
        "normal_clearance_days": round(normal, 1),
        "predicted_clearance_days": predicted,
        "expected_delay_days": delay,
        "delay_probability": delay_prob,
        "confidence": confidence,
        "risk_category": risk_cat,
        "drivers": {
            "congestion_days": round(congestion_days, 1),
            "documentation_penalty": doc_penalty,
            "category_multiplier": cat_mult,
            "season_multiplier": season_mult,
            "value_penalty": value_penalty,
        },
    }


# --------------------------------------------------------------------------
# ETA forecasting (best / likely / worst)
# --------------------------------------------------------------------------
def predict_eta(shipment: dict, base_date: datetime | None = None) -> dict:
    base = base_date or datetime.now(timezone.utc)
    risk = float(shipment.get("risk_score", 40) or 40)
    method = shipment.get("shipping_method", "Sea")
    transit = {"Air": 4, "Express": 3, "Sea": 22, "Rail": 14, "Road": 9}.get(method, 15)
    seed = _seed(shipment.get("shipment_id", "x"), method)

    likely_offset = transit + (risk / 100.0) * transit * 0.5
    best_offset = transit * (0.9 - risk / 500.0)
    worst_offset = likely_offset + transit * (0.35 + risk / 200.0) + seed * 2

    best = base + timedelta(days=round(best_offset))
    likely = base + timedelta(days=round(likely_offset))
    worst = base + timedelta(days=round(worst_offset))
    delay_prob = round(_clamp(risk * 0.9 + seed * 10), 0)
    confidence = round(_clamp(90 - risk * 0.25 - seed * 8, 58, 95), 0)
    return {
        "best_case": best.date().isoformat(),
        "most_likely": likely.date().isoformat(),
        "worst_case": worst.date().isoformat(),
        "delay_probability": delay_prob,
        "confidence": confidence,
        "predicted_transit_days": round(likely_offset, 1),
        "baseline_transit_days": transit,
    }


# --------------------------------------------------------------------------
# Route optimization (weighted scoring)
# --------------------------------------------------------------------------
def optimize_routes(routes: list[dict], priority: str = "balanced") -> dict:
    """routes: list of {name, eta_days, cost, risk, resilience}
    priority: minimize_cost | minimize_time | minimize_risk | maximize_resilience | balanced
    Returns scored + sorted routes (higher score = better)."""
    weight_map = {
        "minimize_cost": {"cost": 0.5, "eta": 0.2, "risk": 0.2, "resilience": 0.1},
        "minimize_time": {"cost": 0.15, "eta": 0.5, "risk": 0.2, "resilience": 0.15},
        "minimize_risk": {"cost": 0.15, "eta": 0.15, "risk": 0.5, "resilience": 0.2},
        "maximize_resilience": {"cost": 0.15, "eta": 0.15, "risk": 0.2, "resilience": 0.5},
        "balanced": {"cost": 0.25, "eta": 0.25, "risk": 0.3, "resilience": 0.2},
    }
    w = weight_map.get(priority, weight_map["balanced"])
    if not routes:
        return {"routes": [], "recommended": None, "priority": priority, "weights": w}

    max_cost = max(r["cost"] for r in routes) or 1
    max_eta = max(r["eta_days"] for r in routes) or 1
    scored = []
    for r in routes:
        cost_s = (1 - r["cost"] / max_cost) * 100
        eta_s = (1 - r["eta_days"] / max_eta) * 100
        risk_s = 100 - float(r["risk"])
        res_s = float(r["resilience"])
        score = round(cost_s * w["cost"] + eta_s * w["eta"] + risk_s * w["risk"] + res_s * w["resilience"], 1)
        scored.append({**r, "score": score})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return {"routes": scored, "recommended": scored[0], "priority": priority, "weights": w}


# --------------------------------------------------------------------------
# Impact analysis
# --------------------------------------------------------------------------
def analyze_impact(shipments: list[dict], disruption: dict) -> dict:
    """Identify shipments affected by a disruption (location/route/carrier match)."""
    loc = (disruption.get("location") or "").lower()
    region = (disruption.get("affected_region") or "").lower()
    severity = disruption.get("severity", "High")
    sev_mult = {"Low": 0.4, "Moderate": 0.7, "High": 1.0, "Critical": 1.35}.get(severity, 1.0)

    affected, high, med, low = [], 0, 0, 0
    total_value = 0.0
    for s in shipments:
        hay = " ".join([
            str(s.get("origin", "")), str(s.get("destination", "")),
            str(s.get("current_location", "")), str(s.get("carrier", "")),
            " ".join(s.get("route", []) if isinstance(s.get("route"), list) else []),
        ]).lower()
        if (loc and loc in hay) or (region and region in hay):
            r = float(s.get("risk_score", 40)) * sev_mult
            total_value += float(s.get("product_value", 0) or 0)
            if r >= 65:
                high += 1
                tier = "High"
            elif r >= 40:
                med += 1
                tier = "Medium"
            else:
                low += 1
                tier = "Low"
            affected.append({
                "shipment_id": s.get("shipment_id"), "route": f'{s.get("origin")} → {s.get("destination")}',
                "carrier": s.get("carrier"), "risk_tier": tier,
                "risk_score": round(r, 0), "value": s.get("product_value", 0),
            })
    est_delay = round(2.2 * sev_mult + len(affected) * 0.01, 1)
    cost_exposure = round(total_value * 0.06 * sev_mult, 0)
    return {
        "disruption": disruption,
        "affected_count": len(affected),
        "high_risk": high, "medium_risk": med, "low_risk": low,
        "expected_delay_days": est_delay,
        "estimated_cost_exposure": cost_exposure,
        "affected_shipments": affected[:100],
    }


def cascade_analysis(disruption: dict, affected_count: int) -> dict:
    """Network-style cascading disruption chain."""
    sev = disruption.get("severity", "High")
    mult = {"Low": 0.3, "Moderate": 0.55, "High": 0.8, "Critical": 1.0}.get(sev, 0.8)
    primary = disruption.get("title", "Primary disruption")
    loc = disruption.get("location", "affected port")
    secondary = int(affected_count * 0.45 * mult)
    tertiary = int(affected_count * 0.22 * mult)
    return {
        "levels": [
            {"level": 1, "label": "Primary Disruption", "event": primary,
             "detail": f"{loc} directly impacted", "affected": affected_count},
            {"level": 2, "label": "Secondary Effects", "event": "Rerouting congestion at alternate ports",
             "detail": "Vessels diverted increase load on backup ports", "affected": secondary},
            {"level": 3, "label": "Tertiary Effects", "event": "Customs & inland processing slowdown",
             "detail": "Backlog propagates to customs and last-mile delivery", "affected": tertiary},
        ],
        "total_estimated_affected": affected_count + secondary + tertiary,
    }


# --------------------------------------------------------------------------
# What-if simulation
# --------------------------------------------------------------------------
def run_simulation(params: dict, shipment_count: int = 120) -> dict:
    duration = float(params.get("disruption_duration_days", 7) or 0)
    port_closed = bool(params.get("port_closure", False))
    customs_delay = float(params.get("customs_delay_days", 0) or 0)
    carrier_unavail = bool(params.get("carrier_unavailable", False))
    fuel = float(params.get("fuel_cost_change_pct", 0) or 0)
    mode = params.get("shipping_mode", "Sea")

    base_affected = int(shipment_count * (0.35 if port_closed else 0.15))
    if carrier_unavail:
        base_affected = int(base_affected * 1.4)
    avg_delay = round(duration * (0.6 if port_closed else 0.3) + customs_delay, 1)
    mode_cost = {"Air": 3.2, "Express": 4.0, "Sea": 1.0, "Rail": 1.4, "Road": 1.8}.get(mode, 1.0)
    add_cost = round(base_affected * 850 * mode_cost * (1 + fuel / 100.0) + duration * 4200, 0)
    customer_impact = int(base_affected * 0.7)
    risk_level = "Critical" if (port_closed and duration >= 7) else ("High" if base_affected > shipment_count * 0.2 else "Moderate")
    return {
        "params": params,
        "affected_shipments": base_affected,
        "average_delay_days": avg_delay,
        "additional_cost": add_cost,
        "customers_impacted": customer_impact,
        "risk_level": risk_level,
    }


def compare_scenarios(scenarios: list[dict]) -> list[dict]:
    out = []
    for sc in scenarios:
        res = run_simulation(sc.get("params", {}), sc.get("shipment_count", 120))
        out.append({"name": sc.get("name"), "description": sc.get("description"), **res})
    return out


# --------------------------------------------------------------------------
# Financial impact
# --------------------------------------------------------------------------
def financial_impact(payload: dict) -> dict:
    affected = int(payload.get("affected_shipments", 100) or 0)
    avg_value = float(payload.get("avg_shipment_value", 4200) or 0)
    delay_days = float(payload.get("delay_days", 3) or 0)
    transport = affected * 620
    storage = affected * delay_days * 45
    rerouting = affected * 380
    holding = affected * avg_value * 0.004 * delay_days
    carrier_change = affected * 210
    late_exposure = affected * avg_value * 0.02
    current = round(transport + storage + rerouting + holding + carrier_change + late_exposure, 0)
    after_recovery = round(current * 0.58, 0)
    return {
        "estimated_current_exposure": current,
        "estimated_exposure_after_recovery": after_recovery,
        "potential_cost_avoided": round(current - after_recovery, 0),
        "breakdown": {
            "transportation": round(transport, 0), "storage": round(storage, 0),
            "rerouting": round(rerouting, 0), "inventory_holding": round(holding, 0),
            "carrier_change": round(carrier_change, 0), "late_delivery_exposure": round(late_exposure, 0),
        },
        "note": "Model estimate for planning purposes only. Not a financial guarantee.",
    }


# --------------------------------------------------------------------------
# Root cause analysis
# --------------------------------------------------------------------------
def root_cause(shipment: dict) -> list[dict]:
    risk = float(shipment.get("risk_score", 50))
    seed = _seed(shipment.get("shipment_id", "x"))
    causes = [
        ("Port congestion", 0.42 + seed * 0.1),
        ("Customs backlog", 0.27 - seed * 0.05),
        ("Carrier delay", 0.18),
        ("Geopolitical risk", 0.13 + (risk - 50) / 400.0),
    ]
    total = sum(max(0.01, c[1]) for c in causes)
    return [{"cause": c, "contribution": round(max(0.01, v) / total * 100, 0)} for c, v in causes]
