"""LLM helpers using Emergent Universal Key (Claude Sonnet 4.6).

Used for: explainable recovery recommendations, geopolitical NLP event
classification, and safe customer notification drafting. All calls have a
deterministic template fallback so the app works even if the LLM is unavailable.
"""
import os
import json
import logging

logger = logging.getLogger(__name__)

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
MODEL = ("anthropic", "claude-sonnet-4-6")


async def _chat(system: str, user: str, session: str) -> str:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id=session, system_message=system).with_model(*MODEL)
    resp = await chat.send_message(UserMessage(text=user))
    return resp if isinstance(resp, str) else str(resp)


def _extract_json(text: str):
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return json.loads(text[start:end + 1])
    except Exception:
        pass
    return None


# --------------------------------------------------------------------------
async def classify_event(text: str) -> dict:
    """NLP: classify free text into a structured geopolitical risk event."""
    types = ["Strike", "Port Closure", "Sanction", "Border Closure", "Conflict",
             "Regulation", "Weather", "Carrier Disruption"]
    system = (
        "You are a logistics risk analyst. Classify the news text into a structured "
        "risk event. Respond ONLY with JSON: {\"event_type\": one of "
        f"{types}, \"severity\": one of [Low,Moderate,High,Critical], "
        "\"title\": short title, \"location\": place, \"affected_region\": region, "
        "\"estimated_duration\": e.g. '3-5 days', \"summary\": one sentence}."
    )
    try:
        raw = await _chat(system, text, "classify")
        data = _extract_json(raw)
        if data and data.get("event_type") in types:
            return data
    except Exception as e:
        logger.warning(f"classify_event LLM failed: {e}")
    # fallback keyword classifier
    low = text.lower()
    mapping = [("strike", "Strike"), ("closed", "Port Closure"), ("closure", "Port Closure"),
               ("sanction", "Sanction"), ("border", "Border Closure"), ("war", "Conflict"),
               ("conflict", "Conflict"), ("regulation", "Regulation"), ("storm", "Weather"),
               ("typhoon", "Weather"), ("weather", "Weather"), ("carrier", "Carrier Disruption")]
    etype = next((v for k, v in mapping if k in low), "Regulation")
    sev = "Critical" if any(w in low for w in ["shutdown", "war", "closed indefinitely"]) else "High"
    return {"event_type": etype, "severity": sev, "title": text[:60],
            "location": "Unknown", "affected_region": "Global",
            "estimated_duration": "Unknown", "summary": text[:140]}


async def recovery_recommendation(context: dict) -> dict:
    """Generate explainable recovery recommendation for a shipment/disruption."""
    system = (
        "You are TradeSentinel's recovery advisor for logistics managers. Given the "
        "shipment risk context, recommend ONE concrete recovery action. Respond ONLY "
        "with JSON: {\"action\": short imperative title, \"reasons\": [3 short bullet "
        "strings], \"expected_outcome\": {\"eta\": 'down'|'up'|'flat', \"risk\": "
        "'down'|'up'|'flat', \"cost\": 'down'|'up'|'flat'}, \"explanation\": 2 sentences}. "
        "Never guarantee outcomes."
    )
    try:
        raw = await _chat(system, json.dumps(context), "recovery")
        data = _extract_json(raw)
        if data and data.get("action"):
            return data
    except Exception as e:
        logger.warning(f"recovery_recommendation LLM failed: {e}")
    return {
        "action": f'Reroute high-risk shipments via alternative corridor',
        "reasons": [
            "Current route shows elevated disruption risk",
            "Alternative route has lower assessed risk and comparable ETA",
            "Additional cost is within acceptable tolerance",
        ],
        "expected_outcome": {"eta": "down", "risk": "down", "cost": "up"},
        "explanation": "Rerouting reduces exposure to the active disruption while keeping delivery within the most-likely ETA window. Cost increases slightly due to the alternative carrier lane.",
    }


async def customer_message(context: dict) -> str:
    """Draft a safe, non-committal customer notification for an ETA change."""
    system = (
        "You draft brief, empathetic, professional shipment-delay notifications for "
        "customers. Do NOT promise exact dates; give a delivery window. 2-3 sentences. "
        "Return plain text only."
    )
    try:
        raw = await _chat(system, json.dumps(context), "custmsg")
        if raw and len(raw.strip()) > 10:
            return raw.strip()
    except Exception as e:
        logger.warning(f"customer_message LLM failed: {e}")
    window = context.get("eta_window", "the coming days")
    return (
        "Your shipment has been affected by an unexpected logistics disruption. "
        f"We have adjusted the route and currently estimate delivery within {window}. "
        "We are actively monitoring the situation and will keep you updated."
    )
