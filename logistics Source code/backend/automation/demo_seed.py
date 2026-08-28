"""
automation/demo_seed.py — Demo Workflow Data Seeder
====================================================
Creates 4 preconfigured demo workflows, 3 intentional conflicts,
and sample execution history for hackathon demonstration.
"""

from __future__ import annotations
from datetime import datetime, timedelta
import random

from automation.schema import (
    WorkflowDefinition, WorkflowNode, WorkflowEdge, WorkflowTrigger,
    WorkflowExecution, ExecutionStep, Condition,
    NodeType, TriggerType, Operator, WorkflowStatus,
    ExecutionStatus, ExecutionMode, StepStatus,
    ConflictResult, ConflictType, ConflictSeverity,
    AutomationOpportunity,
)


async def seed_demo_data(db) -> dict:
    """Seed complete demo data for the automation copilot."""
    # Clear existing demo data
    await db.workflows.delete_many({})
    await db.workflow_runs.delete_many({})
    await db.workflow_conflicts.delete_many({})
    await db.automation_opportunities.delete_many({})

    workflows = _create_demo_workflows()
    runs = _create_demo_executions(workflows)
    conflicts = _create_demo_conflicts(workflows)
    opportunities = _create_demo_opportunities()

    # Insert workflows
    for wf in workflows:
        doc = wf.model_dump(mode="json")
        await db.workflows.insert_one(doc)

    # Insert runs
    for run in runs:
        doc = run.model_dump(mode="json")
        await db.workflow_runs.insert_one(doc)

    # Insert conflicts
    for conflict in conflicts:
        doc = conflict.model_dump(mode="json")
        await db.workflow_conflicts.insert_one(doc)

    # Insert opportunities
    for opp in opportunities:
        doc = opp.model_dump(mode="json")
        await db.automation_opportunities.insert_one(doc)

    return {
        "seeded": True,
        "workflows": len(workflows),
        "executions": len(runs),
        "conflicts": len(conflicts),
        "opportunities": len(opportunities),
    }


def _create_demo_workflows() -> list[WorkflowDefinition]:
    """Create 4 preconfigured demo workflows."""
    workflows = []

    # ─── Workflow 1: Shipment Delay Escalation ──────────────────
    wf1_nodes = [
        WorkflowNode(
            id="wf1_trigger", type=NodeType.TRIGGER,
            label="Shipment Delayed", description="Triggered when a shipment is delayed",
            position_x=250, position_y=0,
        ),
        WorkflowNode(
            id="wf1_cond1", type=NodeType.CONDITION,
            label="Delay > 2 days?",
            conditions=[Condition(field="expected_delay", operator=Operator.GT, value=2, unit="days")],
            position_x=250, position_y=120,
        ),
        WorkflowNode(
            id="wf1_action1", type=NodeType.ACTION,
            label="Analyze Risk", tool="calculate_risk",
            position_x=250, position_y=240,
        ),
        WorkflowNode(
            id="wf1_action2", type=NodeType.ACTION,
            label="Predict New ETA", tool="predict_eta",
            position_x=250, position_y=360,
        ),
        WorkflowNode(
            id="wf1_notify", type=NodeType.NOTIFICATION,
            label="Notify Manager", notification_type="alert",
            notification_target="manager",
            notification_template="Shipment {shipment_id} delayed by {expected_delay} days. Risk: {risk_score}",
            position_x=250, position_y=480,
        ),
        WorkflowNode(
            id="wf1_end", type=NodeType.END,
            label="End", position_x=250, position_y=600,
        ),
        WorkflowNode(
            id="wf1_end_skip", type=NodeType.END,
            label="No Action Needed", position_x=500, position_y=240,
        ),
    ]
    wf1_edges = [
        WorkflowEdge(source="wf1_trigger", target="wf1_cond1", label="default"),
        WorkflowEdge(source="wf1_cond1", target="wf1_action1", label="true", condition_branch="true"),
        WorkflowEdge(source="wf1_cond1", target="wf1_end_skip", label="false", condition_branch="false"),
        WorkflowEdge(source="wf1_action1", target="wf1_action2", label="default"),
        WorkflowEdge(source="wf1_action2", target="wf1_notify", label="default"),
        WorkflowEdge(source="wf1_notify", target="wf1_end", label="default"),
    ]
    wf1 = WorkflowDefinition(
        id="wf_demo_001", name="Shipment Delay Escalation",
        description="Automatically escalate shipment delays: analyze risk, predict new ETA, and notify manager when delay exceeds 2 days.",
        natural_language="When a shipment is delayed by more than 2 days, analyze the risk, predict the new ETA, and notify the logistics manager.",
        trigger=WorkflowTrigger(type=TriggerType.SHIPMENT_DELAYED, description="Shipment delay detected"),
        nodes=wf1_nodes, edges=wf1_edges,
        version=1, status=WorkflowStatus.ACTIVE,
        created_by="admin@tradeintel.ai",
        created_at=datetime.utcnow() - timedelta(days=14),
        tags=["delay", "escalation", "notification"],
    )
    workflows.append(wf1)

    # ─── Workflow 2: High-Risk Shipment Recovery ────────────────
    wf2_nodes = [
        WorkflowNode(
            id="wf2_trigger", type=NodeType.TRIGGER,
            label="Risk Threshold Exceeded", position_x=250, position_y=0,
        ),
        WorkflowNode(
            id="wf2_cond1", type=NodeType.CONDITION,
            label="Risk >= 70?",
            conditions=[Condition(field="risk_score", operator=Operator.GTE, value=70)],
            position_x=250, position_y=120,
        ),
        WorkflowNode(
            id="wf2_action1", type=NodeType.ACTION,
            label="Root Cause Analysis", tool="analyze_root_cause",
            position_x=250, position_y=240,
        ),
        WorkflowNode(
            id="wf2_action2", type=NodeType.ACTION,
            label="Optimize Route", tool="optimize_route",
            position_x=250, position_y=360,
        ),
        WorkflowNode(
            id="wf2_cond2", type=NodeType.CONDITION,
            label="Value > ₹10L?",
            conditions=[Condition(field="product_value", operator=Operator.GT, value=1000000, unit="INR")],
            position_x=250, position_y=480,
        ),
        WorkflowNode(
            id="wf2_approval", type=NodeType.APPROVAL,
            label="Manager Approval",
            approver_role="manager",
            approval_message="High-value shipment rerouting requires manager approval. Shipment value exceeds ₹10 lakh.",
            position_x=100, position_y=600,
        ),
        WorkflowNode(
            id="wf2_action3", type=NodeType.ACTION,
            label="Execute Reroute", tool="update_shipment_status",
            tool_params={"new_status": "In Transit", "action": "rerouted"},
            position_x=250, position_y=720,
        ),
        WorkflowNode(
            id="wf2_notify", type=NodeType.NOTIFICATION,
            label="Notify Team", notification_type="alert", notification_target="manager",
            position_x=250, position_y=840,
        ),
        WorkflowNode(
            id="wf2_end", type=NodeType.END,
            label="End", position_x=250, position_y=960,
        ),
        WorkflowNode(
            id="wf2_end_low", type=NodeType.END,
            label="Risk Acceptable", position_x=500, position_y=240,
        ),
    ]
    wf2_edges = [
        WorkflowEdge(source="wf2_trigger", target="wf2_cond1"),
        WorkflowEdge(source="wf2_cond1", target="wf2_action1", condition_branch="true", label="true"),
        WorkflowEdge(source="wf2_cond1", target="wf2_end_low", condition_branch="false", label="false"),
        WorkflowEdge(source="wf2_action1", target="wf2_action2"),
        WorkflowEdge(source="wf2_action2", target="wf2_cond2"),
        WorkflowEdge(source="wf2_cond2", target="wf2_approval", condition_branch="true", label="true"),
        WorkflowEdge(source="wf2_cond2", target="wf2_action3", condition_branch="false", label="false"),
        WorkflowEdge(source="wf2_approval", target="wf2_action3"),
        WorkflowEdge(source="wf2_action3", target="wf2_notify"),
        WorkflowEdge(source="wf2_notify", target="wf2_end"),
    ]
    wf2 = WorkflowDefinition(
        id="wf_demo_002", name="High-Risk Shipment Recovery",
        description="When risk exceeds 70, analyze root cause, optimize route. High-value shipments (>₹10L) require manager approval before rerouting.",
        natural_language="When a shipment's risk score exceeds 70, analyze the root cause and optimize the route. If the shipment value is above ₹10 lakh, require manager approval before rerouting.",
        trigger=WorkflowTrigger(type=TriggerType.RISK_THRESHOLD_EXCEEDED, config={"threshold": 70}),
        nodes=wf2_nodes, edges=wf2_edges,
        version=2, status=WorkflowStatus.ACTIVE,
        created_by="admin@tradeintel.ai",
        created_at=datetime.utcnow() - timedelta(days=10),
        tags=["risk", "recovery", "approval", "reroute"],
    )
    workflows.append(wf2)

    # ─── Workflow 3: Vehicle Breakdown Reassignment ─────────────
    wf3_nodes = [
        WorkflowNode(
            id="wf3_trigger", type=NodeType.TRIGGER,
            label="Carrier Disruption", position_x=250, position_y=0,
        ),
        WorkflowNode(
            id="wf3_action1", type=NodeType.ACTION,
            label="Calculate Impact", tool="calculate_impact",
            position_x=250, position_y=120,
        ),
        WorkflowNode(
            id="wf3_action2", type=NodeType.ACTION,
            label="Find Alternate Route", tool="optimize_route",
            tool_params={"priority": "minimize_time"},
            position_x=250, position_y=240,
        ),
        WorkflowNode(
            id="wf3_action3", type=NodeType.ACTION,
            label="Reassign Shipment", tool="update_shipment_status",
            tool_params={"new_status": "In Transit", "action": "carrier_reassigned"},
            position_x=250, position_y=360,
        ),
        WorkflowNode(
            id="wf3_notify", type=NodeType.NOTIFICATION,
            label="Alert Operations", notification_type="alert", notification_target="manager",
            notification_template="Carrier disruption handled. Shipment reassigned to alternate route.",
            position_x=250, position_y=480,
        ),
        WorkflowNode(
            id="wf3_end", type=NodeType.END,
            label="End", position_x=250, position_y=600,
        ),
    ]
    wf3_edges = [
        WorkflowEdge(source="wf3_trigger", target="wf3_action1"),
        WorkflowEdge(source="wf3_action1", target="wf3_action2"),
        WorkflowEdge(source="wf3_action2", target="wf3_action3"),
        WorkflowEdge(source="wf3_action3", target="wf3_notify"),
        WorkflowEdge(source="wf3_notify", target="wf3_end"),
    ]
    wf3 = WorkflowDefinition(
        id="wf_demo_003", name="Vehicle Breakdown Reassignment",
        description="Automatically handle carrier disruptions: assess impact, find alternate route, and reassign shipment.",
        natural_language="When a carrier disruption occurs, calculate the impact, find an alternate route, reassign the shipment, and notify operations.",
        trigger=WorkflowTrigger(type=TriggerType.CARRIER_DISRUPTION),
        nodes=wf3_nodes, edges=wf3_edges,
        version=1, status=WorkflowStatus.ACTIVE,
        created_by="manager@tradesentinel.demo",
        created_at=datetime.utcnow() - timedelta(days=7),
        tags=["carrier", "disruption", "reassignment"],
    )
    workflows.append(wf3)

    # ─── Workflow 4: Delivery → Invoice → Notify Customer ──────
    wf4_nodes = [
        WorkflowNode(
            id="wf4_trigger", type=NodeType.TRIGGER,
            label="Shipment Delivered", position_x=250, position_y=0,
        ),
        WorkflowNode(
            id="wf4_action1", type=NodeType.ACTION,
            label="Calculate Financial Impact", tool="calculate_financial_impact",
            position_x=250, position_y=120,
        ),
        WorkflowNode(
            id="wf4_notify1", type=NodeType.NOTIFICATION,
            label="Notify Customer", notification_type="email", notification_target="customer",
            notification_template="Your shipment {shipment_id} has been delivered successfully.",
            position_x=250, position_y=240,
        ),
        WorkflowNode(
            id="wf4_notify2", type=NodeType.NOTIFICATION,
            label="Update Operations", notification_type="alert", notification_target="manager",
            position_x=250, position_y=360,
        ),
        WorkflowNode(
            id="wf4_end", type=NodeType.END,
            label="End", position_x=250, position_y=480,
        ),
    ]
    wf4_edges = [
        WorkflowEdge(source="wf4_trigger", target="wf4_action1"),
        WorkflowEdge(source="wf4_action1", target="wf4_notify1"),
        WorkflowEdge(source="wf4_notify1", target="wf4_notify2"),
        WorkflowEdge(source="wf4_notify2", target="wf4_end"),
    ]
    wf4 = WorkflowDefinition(
        id="wf_demo_004", name="Delivery Completion Flow",
        description="When a shipment is delivered: calculate financial summary, notify customer, and update operations team.",
        natural_language="When a shipment is delivered, calculate the financial impact, send a delivery confirmation to the customer, and notify the operations team.",
        trigger=WorkflowTrigger(type=TriggerType.SHIPMENT_DELIVERED),
        nodes=wf4_nodes, edges=wf4_edges,
        version=1, status=WorkflowStatus.ACTIVE,
        created_by="manager@tradesentinel.demo",
        created_at=datetime.utcnow() - timedelta(days=5),
        tags=["delivery", "invoice", "customer"],
    )
    workflows.append(wf4)

    return workflows


def _create_demo_executions(workflows: list[WorkflowDefinition]) -> list[WorkflowExecution]:
    """Create sample execution history for demo workflows."""
    runs = []
    now = datetime.utcnow()

    for i, wf in enumerate(workflows):
        num_runs = random.randint(15, 40)
        for j in range(num_runs):
            started = now - timedelta(days=random.randint(0, 14), hours=random.randint(0, 23))
            duration = random.uniform(500, 300000)  # 0.5s to 5min
            status = random.choices(
                [ExecutionStatus.COMPLETED, ExecutionStatus.SIMULATED, ExecutionStatus.FAILED],
                weights=[70, 20, 10], k=1
            )[0]

            steps = []
            for node in wf.nodes[:random.randint(3, len(wf.nodes))]:
                step_status = StepStatus.COMPLETED
                if status == ExecutionStatus.FAILED and node == wf.nodes[-1]:
                    step_status = StepStatus.FAILED

                step = ExecutionStep(
                    node_id=node.id,
                    node_type=node.type,
                    node_label=node.label,
                    tool=node.tool,
                    input_data={"shipment_id": f"SHP-{random.randint(1000, 9999)}"},
                    output_data={"result": True, "simulated": True},
                    status=step_status,
                    started_at=started + timedelta(milliseconds=len(steps) * 500),
                    completed_at=started + timedelta(milliseconds=(len(steps) + 1) * 500),
                    duration_ms=random.uniform(100, 5000),
                )
                if node.type == NodeType.APPROVAL:
                    step.approval_status = random.choice(["approved", "approved", "approved", "rejected"])
                steps.append(step)

            run = WorkflowExecution(
                id=f"run_demo_{i}_{j:03d}",
                workflow_id=wf.id,
                workflow_name=wf.name,
                mode=random.choice([ExecutionMode.SIMULATION, ExecutionMode.LIVE]),
                status=status,
                triggered_by=random.choice(["admin@tradesentinel.demo", "manager@tradesentinel.demo", "system"]),
                trigger_data={
                    "shipment_id": f"SHP-{random.randint(1000, 9999)}",
                    "risk_score": random.randint(20, 95),
                    "expected_delay": round(random.uniform(0, 7), 1),
                    "product_value": random.randint(50000, 2000000),
                },
                context={},
                steps=steps,
                started_at=started,
                completed_at=started + timedelta(milliseconds=duration),
                duration_ms=duration,
            )
            runs.append(run)

    return runs


def _create_demo_conflicts(workflows: list[WorkflowDefinition]) -> list[ConflictResult]:
    """Create 3 intentional demo conflicts."""
    return [
        ConflictResult(
            id="conflict_demo_001",
            type=ConflictType.APPROVAL_BYPASS,
            severity=ConflictSeverity.CRITICAL,
            workflows_involved=["wf_demo_002", "wf_demo_003"],
            workflow_names=["High-Risk Shipment Recovery", "Vehicle Breakdown Reassignment"],
            affected_nodes=["wf2_approval", "wf3_action3"],
            explanation="Workflow 'High-Risk Shipment Recovery' requires manager approval before rerouting high-value shipments (>₹10L). However, 'Vehicle Breakdown Reassignment' automatically reroutes shipments without approval. A high-value shipment affected by both a risk threshold AND carrier disruption could bypass the approval requirement.",
            potential_impact="High-value shipments may be rerouted without required manager oversight, potentially leading to unauthorized route changes worth ₹10L+.",
            confidence=0.87,
            recommended_fix="Add a value check condition to 'Vehicle Breakdown Reassignment' that requires approval for shipments above ₹10L, or add a priority rule where the risk workflow takes precedence.",
        ),
        ConflictResult(
            id="conflict_demo_002",
            type=ConflictType.TRIGGER_COLLISION,
            severity=ConflictSeverity.HIGH,
            workflows_involved=["wf_demo_001", "wf_demo_002"],
            workflow_names=["Shipment Delay Escalation", "High-Risk Shipment Recovery"],
            affected_nodes=["wf1_trigger", "wf2_trigger"],
            explanation="Both workflows can trigger simultaneously for the same shipment. A delayed high-risk shipment would activate 'Shipment Delay Escalation' (delay > 2 days) AND 'High-Risk Shipment Recovery' (risk ≥ 70). Both workflows may attempt to optimize routes and send duplicate notifications.",
            potential_impact="Duplicate route optimizations and notification spam. The shipment may receive conflicting route recommendations from two parallel workflows.",
            confidence=0.92,
            recommended_fix="Add mutual exclusion: if the high-risk recovery workflow is already handling a shipment, skip the delay escalation for that shipment, or merge both workflows into a unified escalation pipeline.",
        ),
        ConflictResult(
            id="conflict_demo_003",
            type=ConflictType.RACE_CONDITION,
            severity=ConflictSeverity.HIGH,
            workflows_involved=["wf_demo_002", "wf_demo_003"],
            workflow_names=["High-Risk Shipment Recovery", "Vehicle Breakdown Reassignment"],
            affected_nodes=["wf2_action3", "wf3_action3"],
            explanation="Both workflows can modify shipment status simultaneously. If a high-risk shipment also experiences a carrier disruption, both 'Execute Reroute' (from risk recovery) and 'Reassign Shipment' (from breakdown) may try to update the shipment status concurrently, causing a race condition.",
            potential_impact="Unpredictable shipment state — one workflow's changes may overwrite the other's, leading to incorrect routing or status.",
            confidence=0.79,
            recommended_fix="Implement a shipment lock mechanism: when one workflow starts modifying a shipment, other workflows should queue their changes or skip the already-in-progress shipment.",
        ),
    ]


def _create_demo_opportunities() -> list[AutomationOpportunity]:
    """Create demo automation opportunities."""
    return [
        AutomationOpportunity(
            id="opp_demo_001",
            title="Shipment Delay Escalation Automation",
            description="Detected repetitive manual delay handling process",
            detected_pattern="Shipment delayed → Employee checks risk → Employee checks ETA → Employee optimizes route → Employee notifies manager",
            pattern_steps=[
                "1. Shipment flagged as delayed",
                "2. Employee manually opens shipment details",
                "3. Employee checks risk score and root cause",
                "4. Employee runs route optimizer",
                "5. Employee sends notification to manager",
            ],
            frequency=184,
            frequency_score=92,
            manual_effort_hours=46,
            manual_effort_score=88,
            business_impact_score=85,
            automation_feasibility_score=95,
            confidence_score=91,
            overall_score=90,
            suggested_workflow={
                "name": "Auto Delay Escalation",
                "trigger": "shipment_delayed",
                "steps": ["analyze_risk", "predict_eta", "optimize_route", "notify_manager"],
            },
            ai_explanation="This pattern was observed 184 times in the past month, consuming approximately 46 hours of manual effort. Each instance follows the same 5-step sequence, making it highly automatable. The existing tools (risk analysis, ETA prediction, route optimization, and notification) can fully replace the manual process. Automating this would reduce response time from ~15 minutes to under 30 seconds per incident.",
            risks=["Route optimization without human review may select suboptimal routes in edge cases", "Over-notification if threshold is too sensitive"],
        ),
        AutomationOpportunity(
            id="opp_demo_002",
            title="High-Value Shipment Approval Fast-Track",
            description="92% of shipment rerouting approvals for values under ₹5L are approved",
            detected_pattern="Reroute request → Manager approval request → Manager reviews → Manager approves (92% approval rate for <₹5L)",
            pattern_steps=[
                "1. System recommends rerouting",
                "2. Approval request sent to manager",
                "3. Manager reviews (avg 2.3 hours wait)",
                "4. Manager approves (92% of the time for <₹5L)",
            ],
            frequency=214,
            frequency_score=85,
            manual_effort_hours=38,
            manual_effort_score=78,
            business_impact_score=82,
            automation_feasibility_score=90,
            confidence_score=88,
            overall_score=85,
            suggested_workflow={
                "name": "Auto-Approve Low-Value Reroutes",
                "trigger": "risk_threshold_exceeded",
                "condition": "product_value < 500000",
                "steps": ["optimize_route", "auto_approve", "execute_reroute"],
            },
            ai_explanation="Analysis of 214 approval requests shows that 92% of rerouting approvals for shipments valued under ₹5 lakh are approved by managers. The average approval wait time is 2.3 hours, during which shipment delays accumulate. Auto-approving reroutes for low-value shipments would eliminate this bottleneck while maintaining approval gates for high-value shipments.",
            risks=["Removing human oversight for any rerouting decision", "Edge cases where low-value shipments have other risk factors"],
        ),
        AutomationOpportunity(
            id="opp_demo_003",
            title="Customs Status Monitoring Automation",
            description="Repeated manual customs status checks for shipments in review",
            detected_pattern="Customs status 'Under Review' → Employee checks daily → Employee runs customs prediction → Employee creates follow-up alert",
            pattern_steps=[
                "1. Shipment enters 'Under Review' customs status",
                "2. Employee manually checks customs status daily",
                "3. Employee runs customs delay prediction",
                "4. If predicted delay > 3 days, creates alert",
            ],
            frequency=96,
            frequency_score=72,
            manual_effort_hours=24,
            manual_effort_score=68,
            business_impact_score=75,
            automation_feasibility_score=92,
            confidence_score=82,
            overall_score=78,
            suggested_workflow={
                "name": "Auto Customs Monitor",
                "trigger": "customs_status_changed",
                "condition": "customs_status == Under Review",
                "steps": ["predict_customs_delay", "check_delay_threshold", "create_alert"],
            },
            ai_explanation="Employees spend approximately 24 hours per month manually monitoring customs statuses. This monitoring follows a predictable pattern that can be fully automated using the existing customs prediction engine. Automated monitoring would provide real-time alerts instead of daily manual checks, improving response time from 24 hours to minutes.",
            risks=["Customs prediction model accuracy in edge cases", "Alert fatigue if too many automated alerts are generated"],
        ),
    ]
