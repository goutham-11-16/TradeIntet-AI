"""
automation/schema.py — Workflow DSL Schema
==========================================
Pydantic models for the structured workflow representation.
Supports: TRIGGER, CONDITION, ACTION, DELAY, BRANCH, APPROVAL, NOTIFICATION, END
"""

from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator
import uuid


# ─── Enums ──────────────────────────────────────────────────────────

class NodeType(str, Enum):
    TRIGGER = "trigger"
    CONDITION = "condition"
    ACTION = "action"
    DELAY = "delay"
    BRANCH = "branch"
    APPROVAL = "approval"
    NOTIFICATION = "notification"
    END = "end"


class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED_FOR_APPROVAL = "paused_for_approval"
    CANCELLED = "cancelled"
    SIMULATED = "simulated"


class ExecutionMode(str, Enum):
    SIMULATION = "simulation"
    LIVE = "live"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING_APPROVAL = "waiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"


class ConflictType(str, Enum):
    DUPLICATE = "duplicate"
    TRIGGER_COLLISION = "trigger_collision"
    CONTRADICTORY_ACTIONS = "contradictory_actions"
    CIRCULAR = "circular"
    INFINITE_LOOP = "infinite_loop"
    APPROVAL_BYPASS = "approval_bypass"
    RACE_CONDITION = "race_condition"
    IMPOSSIBLE_CONDITION = "impossible_condition"
    UNREACHABLE_NODE = "unreachable_node"
    INVALID_STATE_TRANSITION = "invalid_state_transition"


class ConflictSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Operator(str, Enum):
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    EQ = "=="
    NEQ = "!="
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    BETWEEN = "between"


# ─── Trigger Definitions ───────────────────────────────────────────

class TriggerType(str, Enum):
    SHIPMENT_RISK_UPDATED = "shipment_risk_updated"
    SHIPMENT_STATUS_CHANGED = "shipment_status_changed"
    SHIPMENT_DELAYED = "shipment_delayed"
    SHIPMENT_CREATED = "shipment_created"
    ETA_CHANGED = "eta_changed"
    CUSTOMS_STATUS_CHANGED = "customs_status_changed"
    GEOPOLITICAL_EVENT = "geopolitical_event"
    CARRIER_DISRUPTION = "carrier_disruption"
    RISK_THRESHOLD_EXCEEDED = "risk_threshold_exceeded"
    SHIPMENT_DELIVERED = "shipment_delivered"
    APPROVAL_RECEIVED = "approval_received"
    SCHEDULED = "scheduled"
    MANUAL = "manual"


# ─── Core Node Models ──────────────────────────────────────────────

class Condition(BaseModel):
    """A single condition expression."""
    field: str = Field(..., description="Data field to evaluate, e.g. 'risk_score', 'expected_delay', 'product_value'")
    operator: Operator = Field(..., description="Comparison operator")
    value: Any = Field(..., description="Threshold value to compare against")
    unit: Optional[str] = Field(None, description="Unit for the value, e.g. 'days', 'INR', 'percent'")

    @field_validator("operator", mode="before")
    @classmethod
    def normalize_operator(cls, v):
        if isinstance(v, Operator):
            return v
        if isinstance(v, str):
            mapping = {
                "gte": Operator.GTE, ">=": Operator.GTE,
                "gt": Operator.GT, ">": Operator.GT,
                "lte": Operator.LTE, "<=": Operator.LTE,
                "lt": Operator.LT, "<": Operator.LT,
                "eq": Operator.EQ, "==": Operator.EQ, "=": Operator.EQ,
                "neq": Operator.NEQ, "!=": Operator.NEQ, "<>": Operator.NEQ,
                "in": Operator.IN, "not_in": Operator.NOT_IN,
                "contains": Operator.CONTAINS, "between": Operator.BETWEEN
            }
            norm = v.strip().lower()
            if norm in mapping:
                return mapping[norm]
            if v in mapping:
                return mapping[v]
        return v


class WorkflowTrigger(BaseModel):
    """Workflow trigger definition."""
    type: TriggerType
    description: str = ""
    config: dict[str, Any] = Field(default_factory=dict, description="Additional trigger configuration")

    @field_validator("type", mode="before")
    @classmethod
    def normalize_trigger_type(cls, v):
        if isinstance(v, TriggerType):
            return v
        if isinstance(v, str):
            clean = v.strip().lower().replace(" ", "_").replace("-", "_")
            for t in TriggerType:
                if t.value == clean or t.name.lower() == clean:
                    return t
            if "delay" in clean:
                return TriggerType.SHIPMENT_DELAYED
            if "status" in clean:
                return TriggerType.SHIPMENT_STATUS_CHANGED
            if "risk" in clean:
                return TriggerType.SHIPMENT_RISK_UPDATED
            if "custom" in clean:
                return TriggerType.CUSTOMS_STATUS_CHANGED
            return TriggerType.MANUAL
        return v


class WorkflowNode(BaseModel):
    """A single node in the workflow graph."""
    id: str = Field(default_factory=lambda: f"node_{uuid.uuid4().hex[:8]}")
    type: NodeType
    label: str = ""
    description: str = ""

    # Condition node fields
    conditions: list[Condition] = Field(default_factory=list)
    logic: str = Field("AND", description="Logic operator for multiple conditions: AND / OR")

    # Action node fields
    tool: Optional[str] = Field(None, description="Registered tool name to execute")
    tool_params: dict[str, Any] = Field(default_factory=dict, description="Parameters for the tool")

    # Delay node fields
    delay_seconds: Optional[int] = Field(None, description="Delay in seconds before proceeding")

    # Approval node fields
    approver_role: Optional[str] = Field(None, description="Role required for approval: admin / manager")
    approval_message: Optional[str] = Field(None, description="Message shown to approver")

    # Notification node fields
    notification_type: Optional[str] = Field(None, description="Type: email / alert / sms")
    notification_target: Optional[str] = Field(None, description="Target: manager / customer / admin")
    notification_template: Optional[str] = Field(None, description="Message template")

    # Position for visual rendering
    position_x: float = 0
    position_y: float = 0

    @field_validator("type", mode="before")
    @classmethod
    def normalize_node_type(cls, v):
        if isinstance(v, NodeType):
            return v
        if isinstance(v, str):
            clean = v.strip().lower()
            for nt in NodeType:
                if nt.value == clean or nt.name.lower() == clean:
                    return nt
            return NodeType.ACTION
        return v


class WorkflowEdge(BaseModel):
    """A directed edge connecting two nodes."""
    id: str = Field(default_factory=lambda: f"edge_{uuid.uuid4().hex[:8]}")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    label: str = Field("", description="Edge label: 'true', 'false', 'default', 'timeout'")
    condition_branch: Optional[str] = Field(None, description="For condition nodes: 'true' or 'false'")


# ─── Workflow Definition ───────────────────────────────────────────

class WorkflowDefinition(BaseModel):
    """Complete workflow definition — the DSL document stored in VectorDB."""
    id: str = Field(default_factory=lambda: f"wf_{uuid.uuid4().hex[:12]}")
    name: str
    description: str = ""
    natural_language: str = Field("", description="Original natural-language requirement")
    trigger: WorkflowTrigger
    nodes: list[WorkflowNode] = Field(default_factory=list)
    edges: list[WorkflowEdge] = Field(default_factory=list)
    version: int = 1
    status: WorkflowStatus = WorkflowStatus.DRAFT
    created_by: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, v):
        if isinstance(v, WorkflowStatus):
            return v
        if isinstance(v, str):
            clean = v.strip().lower()
            for s in WorkflowStatus:
                if s.value == clean or s.name.lower() == clean:
                    return s
            return WorkflowStatus.DRAFT
        return v


# ─── Workflow Execution Models ─────────────────────────────────────

class ExecutionStep(BaseModel):
    """A single step in a workflow execution."""
    node_id: str
    node_type: NodeType
    node_label: str = ""
    tool: Optional[str] = None
    input_data: dict[str, Any] = Field(default_factory=dict)
    output_data: dict[str, Any] = Field(default_factory=dict)
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    error: Optional[str] = None
    approval_status: Optional[str] = None
    approval_by: Optional[str] = None


class WorkflowExecution(BaseModel):
    """A single execution run of a workflow."""
    id: str = Field(default_factory=lambda: f"run_{uuid.uuid4().hex[:12]}")
    workflow_id: str
    workflow_name: str = ""
    mode: ExecutionMode = ExecutionMode.SIMULATION
    status: ExecutionStatus = ExecutionStatus.PENDING
    triggered_by: str = ""
    trigger_data: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict, description="Runtime data passed between nodes")
    steps: list[ExecutionStep] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    error: Optional[str] = None

    # Simulation results
    simulation_summary: Optional[dict[str, Any]] = None


# ─── AI Parser Output ──────────────────────────────────────────────

class ParsedWorkflowResult(BaseModel):
    """Output of the AI workflow parser."""
    workflow: WorkflowDefinition
    detected_trigger: dict[str, Any] = Field(default_factory=dict)
    detected_conditions: list[dict[str, Any]] = Field(default_factory=list)
    detected_actions: list[dict[str, Any]] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    ai_explanation: str = ""


# ─── Validation Models ─────────────────────────────────────────────

class ValidationError(BaseModel):
    """A single validation issue."""
    severity: str = "error"  # error, warning, info
    node_id: Optional[str] = None
    message: str
    code: str  # e.g. "MISSING_TRIGGER", "UNREACHABLE_NODE"


class ValidationResult(BaseModel):
    """Result of workflow validation."""
    valid: bool
    errors: list[ValidationError] = Field(default_factory=list)
    warnings: list[ValidationError] = Field(default_factory=list)


# ─── Conflict Models ──────────────────────────────────────────────

class ConflictResult(BaseModel):
    """A detected workflow conflict."""
    id: str = Field(default_factory=lambda: f"conflict_{uuid.uuid4().hex[:8]}")
    type: ConflictType
    severity: ConflictSeverity
    workflows_involved: list[str] = Field(default_factory=list, description="Workflow IDs")
    workflow_names: list[str] = Field(default_factory=list)
    affected_nodes: list[str] = Field(default_factory=list, description="Node IDs")
    explanation: str
    potential_impact: str = ""
    confidence: float = Field(0.0, ge=0, le=1)
    recommended_fix: str = ""
    status: str = "active"  # active, ignored, resolved
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─── Automation Opportunity Models ─────────────────────────────────

class AutomationOpportunity(BaseModel):
    """An AI-detected automation opportunity."""
    id: str = Field(default_factory=lambda: f"opp_{uuid.uuid4().hex[:8]}")
    title: str
    description: str
    detected_pattern: str
    pattern_steps: list[str] = Field(default_factory=list)

    # Scoring
    impact_score: float = Field(0.0, ge=0, le=100)
    complexity_score: float = Field(0.0, ge=0, le=100)
    readiness_score: float = Field(0.0, ge=0, le=100)
    confidence: float = Field(0.0, ge=0, le=1)

    # Impact estimates
    frequency: int = 0
    estimated_hours_saved: float = 0.0
    estimated_cost_savings: float = 0.0
    estimated_delay_reduction_days: float = 0.0

    # Associated workflows
    related_workflow_id: Optional[str] = None
    suggested_trigger: Optional[str] = None
    suggested_actions: list[str] = Field(default_factory=list)
    draft_workflow: Optional[dict[str, Any]] = None

    status: str = "discovered"  # discovered, converted, dismissed
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ─── Optimization Models ──────────────────────────────────────────

class WorkflowHealthScore(BaseModel):
    """Health scores for a workflow."""
    efficiency: float = Field(0, ge=0, le=100)
    reliability: float = Field(0, ge=0, le=100)
    cost: float = Field(0, ge=0, le=100)
    latency: float = Field(0, ge=0, le=100)
    automation_level: float = Field(0, ge=0, le=100)
    overall: float = Field(0, ge=0, le=100)


class OptimizationSuggestion(BaseModel):
    """An AI-generated workflow optimization suggestion."""
    id: str = Field(default_factory=lambda: f"opt_{uuid.uuid4().hex[:8]}")
    workflow_id: str
    workflow_name: str = ""
    current_description: str = ""
    proposed_description: str = ""
    reason: str = ""
    expected_improvement: str = ""
    risk: str = ""
    confidence: float = Field(0, ge=0, le=1)
    proposed_changes: dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"  # pending, applied, rejected
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class WorkflowAnalytics(BaseModel):
    """Aggregated workflow performance analytics."""
    total_workflows: int = 0
    active_workflows: int = 0
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    success_rate: float = 0.0
    failure_rate: float = 0.0
    avg_execution_time_ms: float = 0.0
    total_manual_tasks_avoided: int = 0
    estimated_hours_saved: float = 0.0
    estimated_financial_impact: float = 0.0
    approval_frequency: float = 0.0
    most_used_workflows: list[dict[str, Any]] = Field(default_factory=list)
    bottlenecks: list[dict[str, Any]] = Field(default_factory=list)
    health_scores: dict[str, WorkflowHealthScore] = Field(default_factory=dict)


# ─── API Request/Response Models ───────────────────────────────────

class GenerateWorkflowRequest(BaseModel):
    """Request to generate a workflow from natural language."""
    natural_language: str = Field(..., min_length=10, description="Natural language workflow requirement")
    domain: str = Field("logistics", description="Business domain context")


class SimulateWorkflowRequest(BaseModel):
    """Request to simulate a workflow."""
    workflow_id: Optional[str] = None
    workflow: Optional[dict[str, Any]] = None
    sample_size: int = Field(50, ge=1, le=500, description="Number of shipments to simulate against")


class ExecuteWorkflowRequest(BaseModel):
    """Request to execute a workflow."""
    workflow_id: Optional[str] = None
    workflow: Optional[dict[str, Any]] = None
    trigger_data: dict[str, Any] = Field(default_factory=dict)
    mode: ExecutionMode = ExecutionMode.SIMULATION


class ApproveStepRequest(BaseModel):
    """Request to approve/reject a pending workflow step."""
    run_id: str
    node_id: str
    decision: str = Field(..., description="'approve' or 'reject'")
    reason: str = ""


class DetectConflictsRequest(BaseModel):
    """Request to detect conflicts for a specific workflow."""
    workflow_id: Optional[str] = None
    check_all: bool = False
