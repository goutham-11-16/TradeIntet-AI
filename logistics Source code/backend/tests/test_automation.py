"""
tests/test_automation.py — Test Suite for AI Business Automation Copilot
========================================================================
Validates the entire automation engine: schema, parser, validator,
conflict detection, execution simulation, tool registry, recommender, and optimizer.
"""

import pytest
import asyncio
from datetime import datetime

from automation.schema import (
    WorkflowDefinition, WorkflowNode, WorkflowEdge, WorkflowTrigger,
    Condition, NodeType, TriggerType, Operator, WorkflowStatus,
    ExecutionStatus, ExecutionMode, StepStatus,
    ConflictType, ConflictSeverity
)
from automation.parser import fallback_parse
from automation.validator import validate_workflow, get_valid_tools, get_valid_fields
from automation.conflict import ConflictDetector
from automation.optimizer import WorkflowOptimizer
from automation.demo_seed import _create_demo_workflows, _create_demo_conflicts, _create_demo_opportunities
from automation.tools import tool_registry


def test_schema_models():
    """Test creating and validating core workflow DSL models."""
    cond = Condition(field="risk_score", operator=Operator.GTE, value=70)
    assert cond.field == "risk_score"
    assert cond.operator == Operator.GTE
    assert cond.value == 70

    trig_node = WorkflowNode(type=NodeType.TRIGGER, label="Risk Updated")
    act_node = WorkflowNode(type=NodeType.ACTION, label="Optimize Route", tool="optimize_route")
    end_node = WorkflowNode(type=NodeType.END, label="End")

    edge1 = WorkflowEdge(source=trig_node.id, target=act_node.id)
    edge2 = WorkflowEdge(source=act_node.id, target=end_node.id)

    wf = WorkflowDefinition(
        name="Test Workflow",
        trigger=WorkflowTrigger(type=TriggerType.SHIPMENT_RISK_UPDATED),
        nodes=[trig_node, act_node, end_node],
        edges=[edge1, edge2],
    )
    assert wf.name == "Test Workflow"
    assert len(wf.nodes) == 3
    assert len(wf.edges) == 2


def test_validator_valid_workflow():
    """Test validation of a well-formed workflow."""
    workflows = _create_demo_workflows()
    for wf in workflows:
        result = validate_workflow(wf)
        assert result.valid is True, f"Workflow '{wf.name}' failed validation: {[e.message for e in result.errors]}"


def test_validator_detects_errors():
    """Test validator catches invalid tools and empty workflows."""
    # Empty workflow
    empty_wf = WorkflowDefinition(
        name="Empty",
        trigger=WorkflowTrigger(type=TriggerType.MANUAL),
        nodes=[],
        edges=[],
    )
    res = validate_workflow(empty_wf)
    assert res.valid is False
    assert any(e.code == "EMPTY_WORKFLOW" for e in res.errors)

    # Invalid tool
    bad_node = WorkflowNode(type=NodeType.ACTION, label="Bad Action", tool="non_existent_tool_123")
    bad_wf = WorkflowDefinition(
        name="Bad Tool",
        trigger=WorkflowTrigger(type=TriggerType.MANUAL),
        nodes=[bad_node],
        edges=[],
    )
    res_bad = validate_workflow(bad_wf)
    assert res_bad.valid is False
    assert any(e.code == "INVALID_ACTION" for e in res_bad.errors)


def test_natural_language_parser():
    """Test parsing natural language into executable workflows."""
    text = "When a shipment becomes high risk and expected delay is more than 2 days, find an alternative route. If shipment value is above ₹10 lakh, ask for manager approval."
    parsed = fallback_parse(text)

    assert parsed.workflow is not None
    assert len(parsed.workflow.nodes) >= 4
    assert any(n.type == NodeType.TRIGGER for n in parsed.workflow.nodes)
    assert any(n.type == NodeType.CONDITION for n in parsed.workflow.nodes)
    assert any(n.type == NodeType.ACTION for n in parsed.workflow.nodes)
    assert any(n.type == NodeType.APPROVAL for n in parsed.workflow.nodes)
    assert len(parsed.detected_conditions) >= 1
    assert len(parsed.detected_actions) >= 1


@pytest.mark.asyncio
async def test_conflict_detector_approval_bypass():
    """Test detecting approval bypass conflict."""
    detector = ConflictDetector()

    wf_controlled = WorkflowDefinition(
        id="wf_ctrl",
        name="Controlled Flow",
        trigger=WorkflowTrigger(type=TriggerType.SHIPMENT_RISK_UPDATED),
        nodes=[
            WorkflowNode(type=NodeType.TRIGGER, label="Risk Updated"),
            WorkflowNode(type=NodeType.APPROVAL, label="Manager Approval"),
            WorkflowNode(type=NodeType.ACTION, label="Reroute", tool="optimize_route"),
        ],
        edges=[],
    )

    wf_bypass = WorkflowDefinition(
        id="wf_byp",
        name="Bypass Flow",
        trigger=WorkflowTrigger(type=TriggerType.SHIPMENT_RISK_UPDATED),
        nodes=[
            WorkflowNode(type=NodeType.TRIGGER, label="Risk Updated"),
            WorkflowNode(type=NodeType.ACTION, label="Reroute Directly", tool="optimize_route"),
        ],
        edges=[],
    )

    conflicts = await detector.detect_conflicts([wf_controlled, wf_bypass])
    assert any(c.type == ConflictType.APPROVAL_BYPASS for c in conflicts)


@pytest.mark.asyncio
async def test_conflict_detector_circular_and_impossible():
    """Test detecting circular cycle and impossible conditions."""
    detector = ConflictDetector()

    # Circular
    n1 = WorkflowNode(id="n1", type=NodeType.ACTION, label="A")
    n2 = WorkflowNode(id="n2", type=NodeType.ACTION, label="B")
    wf_circ = WorkflowDefinition(
        id="wf_c",
        name="Circular Flow",
        trigger=WorkflowTrigger(type=TriggerType.MANUAL),
        nodes=[n1, n2],
        edges=[WorkflowEdge(source="n1", target="n2"), WorkflowEdge(source="n2", target="n1")],
    )
    conflicts_circ = await detector.detect_conflicts([wf_circ])
    assert any(c.type == ConflictType.CIRCULAR for c in conflicts_circ)

    # Impossible condition (risk > 90 AND risk < 40)
    cond_node = WorkflowNode(
        id="c1",
        type=NodeType.CONDITION,
        label="Impossible Risk Check",
        logic="AND",
        conditions=[
            Condition(field="risk_score", operator=Operator.GT, value=90),
            Condition(field="risk_score", operator=Operator.LT, value=40),
        ]
    )
    wf_impos = WorkflowDefinition(
        id="wf_i",
        name="Impossible Condition Flow",
        trigger=WorkflowTrigger(type=TriggerType.MANUAL),
        nodes=[cond_node],
        edges=[],
    )
    conflicts_impos = await detector.detect_conflicts([wf_impos])
    assert any(c.type == ConflictType.IMPOSSIBLE_CONDITION for c in conflicts_impos)


def test_tool_registry():
    """Test tool registry lists and contains all required logistics tools."""
    tools = tool_registry.list_tools()
    tool_names = {t["name"] for t in tools}

    expected = {
        "get_shipment", "calculate_risk", "predict_eta", "predict_customs_delay",
        "optimize_route", "analyze_root_cause", "calculate_impact",
        "calculate_financial_impact", "run_simulation", "create_alert",
        "notify_manager", "request_approval", "update_shipment_status"
    }
    for e in expected:
        assert e in tool_names, f"Expected tool '{e}' missing from registry"


def test_demo_data_generator():
    """Test demo data creation helper generates 4 workflows, 3 conflicts, 3 opportunities."""
    workflows = _create_demo_workflows()
    assert len(workflows) == 4

    conflicts = _create_demo_conflicts(workflows)
    assert len(conflicts) == 3
    assert any(c.type == ConflictType.APPROVAL_BYPASS for c in conflicts)
    assert any(c.type == ConflictType.TRIGGER_COLLISION for c in conflicts)
    assert any(c.type == ConflictType.RACE_CONDITION for c in conflicts)

    opps = _create_demo_opportunities()
    assert len(opps) == 3
    assert opps[0].frequency >= 100


if __name__ == "__main__":
    pytest.main(["-v", __file__])
