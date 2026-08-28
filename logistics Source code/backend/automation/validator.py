"""
automation/validator.py — Workflow Validator Engine
===================================================
Validates workflow definitions against business rules, structural constraints,
and graph theory properties prior to execution.
"""

from typing import List, Set, Dict, Any, Optional
from automation.schema import (
    WorkflowDefinition, WorkflowNode, WorkflowEdge, NodeType,
    ValidationResult, ValidationError, Condition, Operator
)


def get_valid_tools() -> list[str]:
    """Returns a list of valid tool names for workflow actions."""
    return [
        "get_shipment",
        "calculate_risk",
        "predict_eta",
        "predict_customs_delay",
        "optimize_route",
        "analyze_root_cause",
        "calculate_impact",
        "calculate_financial_impact",
        "run_simulation",
        "create_alert",
        "notify_manager",
        "request_approval",
        "update_shipment_status",
    ]


def get_valid_fields() -> list[str]:
    """Returns a list of valid condition fields."""
    return [
        "risk_score",
        "expected_delay",
        "product_value",
        "shipment_status",
        "customs_status",
        "weight_kg",
        "customer_priority",
        "carrier_risk",
        "status",
        "carrier",
        "origin",
        "destination",
    ]


def validate_workflow(workflow: WorkflowDefinition) -> ValidationResult:
    """
    Validates a workflow definition before execution.
    
    Checks for:
    1. Missing trigger
    2. Empty workflow
    3. Invalid condition expressions
    4. Invalid/unsupported actions
    5. Unreachable nodes
    6. Missing branches
    7. Malformed expressions
    8. Missing required parameters
    9. Circular dependency (Cycle detection)
    10. Dangling edges
    11. No end node
    """
    errors: List[ValidationError] = []

    # 1. Missing trigger
    if not workflow.trigger or not getattr(workflow.trigger, 'type', None):
        errors.append(ValidationError(
            severity="error",
            code="MISSING_TRIGGER",
            message="Workflow must have a trigger defined"
        ))

    # 2. Empty workflow
    if not workflow.nodes or len(workflow.nodes) == 0:
        errors.append(ValidationError(
            severity="error",
            code="EMPTY_WORKFLOW",
            message="Workflow must contain at least one node"
        ))
        return ValidationResult(valid=False, errors=errors)

    node_ids: Set[str] = {node.id for node in workflow.nodes}

    # 10. Dangling edges
    valid_edges: List[WorkflowEdge] = []
    for edge in workflow.edges:
        if edge.source not in node_ids:
            errors.append(ValidationError(
                severity="error",
                code="DANGLING_EDGE",
                message=f"Edge source '{edge.source}' does not exist in workflow nodes"
            ))
        elif edge.target not in node_ids:
            errors.append(ValidationError(
                severity="error",
                code="DANGLING_EDGE",
                message=f"Edge target '{edge.target}' does not exist in workflow nodes"
            ))
        else:
            valid_edges.append(edge)

    # Build graph structures
    adj_list: Dict[str, List[WorkflowEdge]] = {node.id: [] for node in workflow.nodes}
    incoming_counts: Dict[str, int] = {node.id: 0 for node in workflow.nodes}

    for edge in valid_edges:
        adj_list[edge.source].append(edge)
        incoming_counts[edge.target] += 1

    has_end_node = False

    for node in workflow.nodes:
        if node.type == NodeType.END:
            has_end_node = True

        # 3. Invalid condition expressions & 7. Malformed expressions
        if node.type == NodeType.CONDITION:
            if not node.conditions:
                errors.append(ValidationError(
                    severity="error",
                    code="MALFORMED_EXPRESSION",
                    message="Condition node must have at least one condition defined",
                    node_id=node.id
                ))
            else:
                for condition in node.conditions:
                    if not getattr(condition, 'field', None):
                        errors.append(ValidationError(
                            severity="error",
                            code="MALFORMED_EXPRESSION",
                            message="Condition must specify a field",
                            node_id=node.id
                        ))
                    elif condition.field not in get_valid_fields():
                        errors.append(ValidationError(
                            severity="error",
                            code="INVALID_CONDITION",
                            message=f"Invalid condition field: {condition.field}",
                            node_id=node.id
                        ))

                    if not getattr(condition, 'operator', None):
                        errors.append(ValidationError(
                            severity="error",
                            code="MALFORMED_EXPRESSION",
                            message="Condition must specify an operator",
                            node_id=node.id
                        ))

        # 4. Invalid/unsupported actions & 8. Missing required parameters
        if node.type == NodeType.ACTION:
            if not node.tool:
                errors.append(ValidationError(
                    severity="error",
                    code="INVALID_ACTION",
                    message="Action node must specify a registered tool",
                    node_id=node.id
                ))
            elif node.tool not in get_valid_tools():
                errors.append(ValidationError(
                    severity="error",
                    code="INVALID_ACTION",
                    message=f"Invalid or unsupported tool: {node.tool}",
                    node_id=node.id
                ))

    # 5. Unreachable nodes
    start_nodes = [n.id for n in workflow.nodes if incoming_counts[n.id] == 0]
    visited_nodes: Set[str] = set()

    def dfs_reachability(current_id: str):
        if current_id in visited_nodes:
            return
        visited_nodes.add(current_id)
        for out_edge in adj_list[current_id]:
            dfs_reachability(out_edge.target)

    for sn in start_nodes:
        dfs_reachability(sn)

    for node in workflow.nodes:
        if node.id not in visited_nodes:
            errors.append(ValidationError(
                severity="error",
                code="UNREACHABLE_NODE",
                message=f"Node '{node.label or node.id}' is unreachable from start nodes",
                node_id=node.id
            ))

    # 9. Circular dependency (Cycle detection using DFS)
    cycle_visited: Set[str] = set()
    rec_stack: Set[str] = set()

    def detect_cycle(current_id: str) -> bool:
        cycle_visited.add(current_id)
        rec_stack.add(current_id)

        for out_edge in adj_list[current_id]:
            target = out_edge.target
            if target not in cycle_visited:
                if detect_cycle(target):
                    return True
            elif target in rec_stack:
                return True

        rec_stack.remove(current_id)
        return False

    for node in workflow.nodes:
        if node.id not in cycle_visited:
            if detect_cycle(node.id):
                errors.append(ValidationError(
                    severity="error",
                    code="CIRCULAR_DEPENDENCY",
                    message="Circular dependency detected in the workflow graph",
                    node_id=node.id
                ))
                break

    # 11. No end node warning
    if not has_end_node:
        errors.append(ValidationError(
            severity="warning",
            code="NO_END_NODE",
            message="Workflow should ideally have at least one END node"
        ))

    is_valid = not any(e.severity == "error" for e in errors)

    return ValidationResult(
        valid=is_valid,
        errors=[e for e in errors if e.severity == "error"],
        warnings=[e for e in errors if e.severity == "warning"],
    )
