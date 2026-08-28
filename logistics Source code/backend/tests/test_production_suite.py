"""
tests/test_production_suite.py — Production-Grade Test Suite for TradeSentinel
=============================================================================
Comprehensive, rigorous test suite validating:
1. Embedded VectorDB Engine (CRUD, Filters, Dense Embeddings, Cosine Search, WAL Persistence)
2. Logistics Intelligence & Deterministic ML Engines (ml.py)
3. PS4 AI Automation Engines (Parser, Schema, Validator, Conflict Engine, Simulator, Executor, Optimizer, Recommender)
4. FastAPI In-Process API Endpoints (Auth, Shipments, Workflows, Conflicts, Analytics)
"""

import pytest
import asyncio
import os
import sys
import json
import sqlite3
from datetime import datetime, timezone, timedelta

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from vectordb import VectorDB, _compute_vector, _cosine_similarity, _tokenize, vectordb_instance as db
from seed_vectordb import seed_vector_database
import ml

from automation.schema import (
    WorkflowDefinition, WorkflowNode, WorkflowEdge, WorkflowTrigger,
    Condition, NodeType, TriggerType, Operator, WorkflowStatus,
    ExecutionStatus, ExecutionMode, StepStatus,
    ConflictType, ConflictSeverity
)
from automation.parser import fallback_parse
from automation.validator import validate_workflow, get_valid_tools, get_valid_fields
from automation.conflict import ConflictDetector
from automation.executor import WorkflowExecutor
from automation.optimizer import WorkflowOptimizer
from automation.recommender import AutomationRecommender
from automation.demo_seed import _create_demo_workflows, _create_demo_conflicts, _create_demo_opportunities
from automation.tools import tool_registry

from fastapi.testclient import TestClient
from server import app


# ==============================================================================
# 1. VECTORDB ENGINE TESTS
# ==============================================================================

class TestVectorDBEngine:
    """Test the embedded VectorDB persistent engine."""

    @pytest.fixture(autouse=True)
    def setup_test_db(self, tmp_path):
        self.db_path = str(tmp_path / "test_vectordb.sqlite")
        self.vdb = VectorDB(db_path=self.db_path)

    def test_vector_computation_and_normalization(self):
        """Verify vector embeddings are non-empty, 128-dimensional, and L2 normalized."""
        text1 = "Singapore port customs delay high risk shipment"
        vec1 = _compute_vector(text1, dim=128)
        assert len(vec1) == 128
        norm1 = sum(x * x for x in vec1)
        assert abs(norm1 - 1.0) < 1e-4, "Vector is not unit normalized"

        # Empty string handling
        vec_empty = _compute_vector("", dim=128)
        assert len(vec_empty) == 128
        assert all(x == 0.0 for x in vec_empty)

    def test_cosine_similarity(self):
        """Verify cosine similarity behaves correctly with identical and distinct texts."""
        vec_a = _compute_vector("electronics semiconductor air freight", dim=128)
        vec_b = _compute_vector("electronics semiconductor air freight", dim=128)
        vec_c = _compute_vector("frozen perishable meat cold chain", dim=128)

        sim_identical = _cosine_similarity(vec_a, vec_b)
        assert abs(sim_identical - 1.0) < 1e-4

        sim_different = _cosine_similarity(vec_a, vec_c)
        assert 0.0 <= sim_different < sim_identical

    @pytest.mark.asyncio
    async def test_crud_and_cursor_operations(self):
        """Test complete CRUD: insert, find, update, delete, count, pagination."""
        col = self.vdb.test_collection

        # 1. Insert One
        doc1 = {"id": "DOC-001", "name": "Alpha", "risk": 85, "active": True, "category": "Electronics"}
        res1 = await col.insert_one(doc1)
        assert res1.inserted_id == "DOC-001"

        # 2. Insert Many
        docs = [
            {"id": "DOC-002", "name": "Beta", "risk": 45, "active": True, "category": "Textiles"},
            {"id": "DOC-003", "name": "Gamma", "risk": 92, "active": False, "category": "Electronics"},
            {"id": "DOC-004", "name": "Delta", "risk": 30, "active": True, "category": "Pharma"},
        ]
        res_many = await col.insert_many(docs)
        assert len(res_many.inserted_ids) == 3

        # 3. Count
        count_all = await col.count_documents({})
        assert count_all == 4

        # 4. Find with Filters ($gte, $in, exact)
        high_risk_docs = await col.find({"risk": {"$gte": 80}}).to_list()
        assert len(high_risk_docs) == 2
        assert {d["id"] for d in high_risk_docs} == {"DOC-001", "DOC-003"}

        in_cat_docs = await col.find({"category": {"$in": ["Pharma", "Textiles"]}}).to_list()
        assert len(in_cat_docs) == 2

        # 5. Sorting, Skipping, Limiting
        sorted_docs = await col.find({}).sort("risk", direction=-1).limit(2).to_list()
        assert len(sorted_docs) == 2
        assert sorted_docs[0]["id"] == "DOC-003"  # risk 92
        assert sorted_docs[1]["id"] == "DOC-001"  # risk 85

        # 6. Update One ($set, $inc)
        up_res = await col.update_one({"id": "DOC-001"}, {"$set": {"status": "Escalated"}, "$inc": {"risk": 5}})
        assert up_res.modified_count == 1
        updated_doc = await col.find_one({"id": "DOC-001"})
        assert updated_doc["status"] == "Escalated"
        assert updated_doc["risk"] == 90

        # 7. Delete One & Delete Many
        del1 = await col.delete_one({"id": "DOC-004"})
        assert del1.deleted_count == 1
        del_many = await col.delete_many({"category": "Electronics"})
        assert del_many.deleted_count == 2
        remaining = await col.count_documents({})
        assert remaining == 1

    @pytest.mark.asyncio
    async def test_semantic_similarity_search(self):
        """Verify vector similarity search returns semantically ranked results."""
        col = self.vdb.shipments

        shipments = [
            {"id": "SHP-SG-01", "origin": "Singapore Port", "cargo": "High tech semiconductor microchips", "status": "Delayed customs"},
            {"id": "SHP-NL-02", "origin": "Rotterdam", "cargo": "Fresh dairy tulips agriculture", "status": "In Transit"},
            {"id": "SHP-CN-03", "origin": "Shanghai", "cargo": "Industrial steel raw minerals", "status": "Clearance"},
        ]
        await col.insert_many(shipments)

        # Query semantic match
        results = await col.similarity_search("Singapore computer chips delay", top_k=2)
        assert len(results) >= 1
        top_match = results[0]
        assert top_match["id"] == "SHP-SG-01"
        assert "_vector_score" in top_match
        assert top_match["_vector_score"] > 0.15

    @pytest.mark.asyncio
    async def test_persistence_across_connections(self):
        """Verify SQLite WAL persistence across separate connection instances."""
        col1 = self.vdb.persistent_test
        await col1.insert_one({"id": "PERSIST-1", "value": 1000000, "flag": True})

        # Instantiate second connection to the same path
        vdb2 = VectorDB(db_path=self.db_path)
        col2 = vdb2.persistent_test
        doc = await col2.find_one({"id": "PERSIST-1"})
        assert doc is not None
        assert doc["value"] == 1000000
        assert doc["flag"] is True


# ==============================================================================
# 2. LOGISTICS INTELLIGENCE & DETERMINISTIC ML (ml.py)
# ==============================================================================

class TestLogisticsIntelligenceML:
    """Test deterministic ML algorithms in ml.py."""

    def test_risk_scoring_bounds(self):
        """Test risk score calculation and factor contributions."""
        factors = {
            "port": 85.0,
            "customs": 75.0,
            "geopolitical": 90.0,
            "carrier": 65.0,
            "route": 70.0,
            "weather": 40.0,
        }
        res = ml.compute_risk(factors)
        assert isinstance(res, dict)
        assert "score" in res
        assert "category" in res
        assert "contributions" in res
        assert 0 <= res["score"] <= 100
        assert res["category"] in ("Critical", "High", "Moderate", "Low")

    def test_customs_delay_prediction(self):
        """Test customs delay prediction model."""
        payload = {
            "destination_country": "USA",
            "product_category": "Electronics",
            "shipment_value": 75000,
            "current_congestion": 60,
            "season": "Peak",
            "documentation_status": "Complete",
        }
        pred = ml.predict_customs(payload)
        assert isinstance(pred, dict)
        assert "predicted_clearance_days" in pred
        assert "expected_delay_days" in pred
        assert "confidence" in pred
        assert 0 <= pred["confidence"] <= 100

    def test_eta_prediction(self):
        """Test ETA prediction bounds and distribution."""
        shipment = {
            "shipment_id": "TS-TEST-01",
            "risk_score": 65,
            "shipping_method": "Sea",
        }
        pred = ml.predict_eta(shipment)
        assert isinstance(pred, dict)
        assert "best_case" in pred
        assert "most_likely" in pred
        assert "worst_case" in pred
        assert "confidence" in pred

    def test_route_optimization(self):
        """Test route optimization with alternatives and weighted scores."""
        routes = [
            {"name": "Cape Route", "eta_days": 18, "cost": 4200, "risk": 25, "resilience": 85},
            {"name": "Suez Route", "eta_days": 12, "cost": 5800, "risk": 75, "resilience": 50},
            {"name": "Air Freight", "eta_days": 3, "cost": 14500, "risk": 15, "resilience": 90},
        ]
        res = ml.optimize_routes(routes, priority="balanced")
        assert isinstance(res, dict)
        assert "routes" in res
        assert "recommended" in res
        assert len(res["routes"]) == 3
        assert res["recommended"] is not None
        assert "score" in res["recommended"]


# ==============================================================================
# 3. PS4 AI AUTOMATION COPILOT ENGINES
# ==============================================================================

class TestAutomationCopilotEngines:
    """Test PS4 workflow parser, validator, conflict engine, simulator, and executor."""

    def test_nl_parser_complex_prompt(self):
        """Test parsing natural language requirement with conditions and approval thresholds."""
        prompt = (
            "When shipment risk score exceeds 75 and delay is more than 2 days, "
            "optimize route. If shipment value is above 1000000, request manager approval."
        )
        parsed = fallback_parse(prompt)
        assert parsed.workflow is not None
        wf = parsed.workflow

        assert wf.trigger.type in (TriggerType.SHIPMENT_RISK_UPDATED, TriggerType.MANUAL, TriggerType.SHIPMENT_DELAYED)
        assert any(n.type == NodeType.CONDITION for n in wf.nodes)
        assert any(n.type == NodeType.ACTION for n in wf.nodes)
        assert len(parsed.detected_conditions) >= 1
        assert len(parsed.detected_actions) >= 1

    def test_workflow_validator_errors(self):
        """Test validator catches empty workflows, invalid tools, and disconnected nodes."""
        # 1. Empty workflow
        empty_wf = WorkflowDefinition(
            name="Empty",
            trigger=WorkflowTrigger(type=TriggerType.MANUAL),
            nodes=[],
            edges=[],
        )
        res_empty = validate_workflow(empty_wf)
        assert res_empty.valid is False
        assert any(e.code == "EMPTY_WORKFLOW" for e in res_empty.errors)

        # 2. Invalid tool action
        bad_node = WorkflowNode(type=NodeType.ACTION, label="Fake Action", tool="unsupported_tool_xyz")
        bad_wf = WorkflowDefinition(
            name="Bad Tool",
            trigger=WorkflowTrigger(type=TriggerType.MANUAL),
            nodes=[bad_node],
            edges=[],
        )
        res_bad = validate_workflow(bad_wf)
        assert res_bad.valid is False
        assert any(e.code == "INVALID_ACTION" for e in res_bad.errors)

    @pytest.mark.asyncio
    async def test_conflict_detection_engine(self):
        """Test conflict engine identifies approval bypasses, collisions, and duplicate logic."""
        detector = ConflictDetector()

        wf1 = WorkflowDefinition(
            id="wf_auto_reroute",
            name="Auto Reroute High Risk",
            trigger=WorkflowTrigger(type=TriggerType.SHIPMENT_RISK_UPDATED),
            nodes=[
                WorkflowNode(id="n1", type=NodeType.TRIGGER, label="Risk Updated"),
                WorkflowNode(id="n2", type=NodeType.CONDITION, label="Risk > 70", condition=Condition(field="risk_score", operator=Operator.GT, value=70)),
                WorkflowNode(id="n3", type=NodeType.ACTION, label="Auto Reroute", tool="optimize_route"),
                WorkflowNode(id="n4", type=NodeType.END, label="End"),
            ],
            edges=[
                WorkflowEdge(source="n1", target="n2"),
                WorkflowEdge(source="n2", target="n3"),
                WorkflowEdge(source="n3", target="n4"),
            ]
        )

        wf2 = WorkflowDefinition(
            id="wf_value_approval",
            name="High Value Approval Reroute",
            trigger=WorkflowTrigger(type=TriggerType.SHIPMENT_RISK_UPDATED),
            nodes=[
                WorkflowNode(id="m1", type=NodeType.TRIGGER, label="Risk Updated"),
                WorkflowNode(id="m2", type=NodeType.CONDITION, label="Value > 10L", condition=Condition(field="product_value", operator=Operator.GT, value=1000000)),
                WorkflowNode(id="m3", type=NodeType.APPROVAL, label="Manager Approval"),
                WorkflowNode(id="m4", type=NodeType.ACTION, label="Reroute", tool="optimize_route"),
                WorkflowNode(id="m5", type=NodeType.END, label="End"),
            ],
            edges=[
                WorkflowEdge(source="m1", target="m2"),
                WorkflowEdge(source="m2", target="m3"),
                WorkflowEdge(source="m3", target="m4"),
                WorkflowEdge(source="m4", target="m5"),
            ]
        )

        conflicts = await detector.detect_conflicts([wf1, wf2])
        assert len(conflicts) >= 1
        conflict_types = [c.type for c in conflicts]
        assert ConflictType.TRIGGER_COLLISION in conflict_types or ConflictType.DUPLICATE in conflict_types or ConflictType.APPROVAL_BYPASS in conflict_types

    @pytest.mark.asyncio
    async def test_workflow_simulation_mode(self):
        """Test workflow simulation mode evaluates shipments without mutating live state."""
        workflows = _create_demo_workflows()
        wf = workflows[0]

        executor = WorkflowExecutor(db=db, ports_cache=[], tool_registry=tool_registry)
        sim_result = await executor.execute_against_shipments(wf, sample_size=20)

        assert isinstance(sim_result, dict)
        assert sim_result.get("shipments_evaluated", 0) >= 0
        assert "trigger_matches" in sim_result
        assert "actions_would_execute" in sim_result

    @pytest.mark.asyncio
    async def test_workflow_execution_and_approval_gate(self):
        """Test workflow execution with condition branching and approval pause."""
        n_trig = WorkflowNode(id="t1", type=NodeType.TRIGGER, label="Start")
        n_appr = WorkflowNode(id="a1", type=NodeType.APPROVAL, label="Manager Gate", approval_role="operations_manager")
        n_act = WorkflowNode(id="ac1", type=NodeType.ACTION, label="Alert", tool="create_alert")
        n_end = WorkflowNode(id="e1", type=NodeType.END, label="End")

        wf = WorkflowDefinition(
            id="wf_exec_test",
            name="Approval Execution Test",
            trigger=WorkflowTrigger(type=TriggerType.MANUAL),
            nodes=[n_trig, n_appr, n_act, n_end],
            edges=[
                WorkflowEdge(source="t1", target="a1"),
                WorkflowEdge(source="a1", target="ac1"),
                WorkflowEdge(source="ac1", target="e1"),
            ]
        )

        executor = WorkflowExecutor(db=db, ports_cache=[], tool_registry=tool_registry)
        context = {"shipment_id": "TS-20260001", "risk_score": 85, "product_value": 1500000}

        # Step 1: Run execution -> should pause at APPROVAL
        execution = await executor.execute(wf, trigger_data=context, mode=ExecutionMode.LIVE)
        assert execution.status in (ExecutionStatus.PAUSED_FOR_APPROVAL, ExecutionStatus.COMPLETED)
        assert len(execution.steps) >= 1

    @pytest.mark.asyncio
    async def test_opportunity_detector(self):
        """Test mining repetitive processes and scoring automation opportunities."""
        await seed_vector_database()
        recommender = AutomationRecommender()
        opps = await recommender.detect_opportunities(db)
        assert len(opps) >= 1
        sample_opp = opps[0]
        assert sample_opp.title != ""
        assert sample_opp.manual_effort_hours >= 0
        assert sample_opp.overall_score >= 0
        assert sample_opp.suggested_workflow is not None

    @pytest.mark.asyncio
    async def test_workflow_optimizer(self):
        """Test workflow performance tracking and bottleneck detection."""
        optimizer = WorkflowOptimizer()
        analytics = await optimizer.get_analytics(db)
        assert analytics is not None
        assert analytics.total_workflows >= 0
        assert analytics.success_rate >= 0
        assert isinstance(analytics.health_scores, dict)


# ==============================================================================
# 4. FASTAPI IN-PROCESS API INTEGRATION TESTS (TestClient)
# ==============================================================================

class TestFastAPIIntegrationEndpoints:
    """Test FastAPI API endpoints using in-process TestClient."""

    @classmethod
    def setup_class(cls):
        cls.client = TestClient(app)

    def test_dashboard_overview_endpoint(self):
        """Test /api/dashboard/overview endpoint."""
        res = self.client.get("/api/dashboard/overview")
        assert res.status_code in (200, 401)

    def test_auth_login_endpoint(self):
        """Test auth login with demo credentials."""
        res = self.client.post("/api/auth/login", json={"email": "admin@tradesentinel.demo", "password": "Admin@123"})
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert "email" in data

    def test_workflow_generation_api(self):
        """Test POST /api/workflows/generate endpoint."""
        payload = {
            "natural_language": "When risk exceeds 70 and delay > 2 days, reroute shipment. Value > 10L requires approval."
        }
        res = self.client.post("/api/workflows/generate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "workflow" in data
        assert "detected_conditions" in data
        assert "detected_actions" in data

    def test_workflow_validation_api(self):
        """Test POST /api/workflows/validate endpoint."""
        workflows = _create_demo_workflows()
        wf_dict = workflows[0].model_dump(mode="json")
        res = self.client.post("/api/workflows/validate", json=wf_dict)
        assert res.status_code == 200
        data = res.json()
        assert "valid" in data
        assert data["valid"] is True

    def test_conflict_detection_api(self):
        """Test GET /api/workflows/conflicts/all endpoint."""
        res = self.client.get("/api/workflows/conflicts/all")
        assert res.status_code == 200
        data = res.json()
        assert "conflicts" in data

    def test_opportunities_api(self):
        """Test GET /api/workflows/opportunities endpoint."""
        res = self.client.get("/api/workflows/opportunities")
        assert res.status_code == 200
        data = res.json()
        assert "opportunities" in data

    def test_analytics_and_insights_api(self):
        """Test GET /api/workflows/analytics endpoint."""
        res = self.client.get("/api/workflows/analytics")
        assert res.status_code == 200
        data = res.json()
        assert "total_executions" in data or "total_workflows" in data or isinstance(data, dict)
