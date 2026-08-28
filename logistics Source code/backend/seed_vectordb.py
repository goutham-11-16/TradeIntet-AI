"""
backend/seed_vectordb.py — Vector Database Initializer & Seeder
===============================================================
Seeds all operational logistics collections into the VectorDB with precomputed
vector embeddings for instant semantic search and zero external dependencies.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from vectordb import vectordb_instance as db
from auth import hash_password
from seed import PORTS, CARRIERS, _carrier_stats, _gen_shipments, _gen_events, _gen_alerts, _gen_recommendations, _gen_predictions
from automation.demo_seed import seed_demo_data

logger = logging.getLogger("tradeintel.seed_vectordb")


async def seed_vector_database(force: bool = False):
    """Populates VectorDB with complete logistics datasets if empty."""
    shipments_count = await db.shipments.count_documents({})
    if shipments_count > 0 and not force:
        logger.info(f"VectorDB already seeded with {shipments_count} shipments.")
        return

    logger.info("Seeding VectorDB collections with semantic embeddings...")

    # 1. Users
    admin_user = {
        "id": "usr_admin",
        "name": "Administrator",
        "email": "admin",
        "role": "admin",
        "organization": "TradeIntel AI Global",
        "phone": "+1 555-0100",
        "password_hash": hash_password("admin123"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.users.insert_one(admin_user)
    await db.users.insert_one({**admin_user, "id": "usr_admin_email", "email": "admin@tradeintel.ai"})

    # 2. Ports
    port_docs = [{**p, "id": p["code"], "risk_score": round(p["congestion"] * 0.7 + 10, 1)} for p in PORTS]
    await db.ports.insert_many(port_docs)

    # 3. Carriers
    carriers_data = _carrier_stats()
    await db.carriers.insert_many(carriers_data)

    # 4. Shipments
    shipments_data = _gen_shipments(carriers_data)
    await db.shipments.insert_many(shipments_data)

    # 5. Geopolitical Events
    events_data = _gen_events()
    await db.geopolitical_events.insert_many(events_data)

    # 6. Alerts
    alerts_data = _gen_alerts(shipments_data)
    await db.alerts.insert_many(alerts_data)

    # 7. Recovery Recommendations
    recommendations_data = _gen_recommendations(shipments_data)
    await db.recovery_recommendations.insert_many(recommendations_data)

    # 8. Historical Predictions
    predictions_data = _gen_predictions(shipments_data)
    await db.predictions.insert_many(predictions_data)

    # 9. Workflows
    try:
        await seed_demo_data(db)
    except Exception as e:
        logger.warning(f"Demo workflows seeding notice: {e}")

    # 10. Compliance Documents
    compliance_docs = [
        {
            "id": "DOC-COMP-001",
            "title": "US Customs & Border Protection 24-Hour Advanced Manifest Rule",
            "category": "Customs Regulation",
            "region": "United States",
            "summary": "Mandates sea carriers to submit cargo declaration 24 hours before loading at foreign port.",
            "status": "Active",
            "penalty_risk": "High",
        },
        {
            "id": "DOC-COMP-002",
            "title": "EU Import Control System 2 (ICS2) Release 3 Maritime Entry Summary",
            "category": "Safety & Security",
            "region": "European Union",
            "summary": "Full Entry Summary Declaration (ENS) data required prior to maritime loading.",
            "status": "Active",
            "penalty_risk": "Critical",
        },
        {
            "id": "DOC-COMP-003",
            "title": "IMO Carbon Intensity Indicator (CII) & MARPOL Annex VI Guidelines",
            "category": "Environmental & Maritime",
            "region": "Global",
            "summary": "Vessel operational carbon emission reduction grading and routing compliance.",
            "status": "Active",
            "penalty_risk": "Medium",
        },
        {
            "id": "DOC-COMP-004",
            "title": "Dual-Use Technology Export Control & Sanctions Screening Protocol",
            "category": "Trade Sanctions",
            "region": "Cross-Border / APAC",
            "summary": "Automated End-User Statement (EUS) and denied party watchlist screening for electronics.",
            "status": "Active",
            "penalty_risk": "Critical",
        },
    ]
    await db.compliance_documents.insert_many(compliance_docs)

    logger.info(f"VectorDB seeding complete. Total shipments indexed: {len(shipments_data)}.")


if __name__ == "__main__":
    asyncio.run(seed_vector_database(force=True))
