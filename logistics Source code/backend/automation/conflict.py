"""
automation/conflict.py — Workflow Conflict Detection Engine
============================================================
Detects 10 major conflict categories among active and proposed workflows:
1. DUPLICATE: Near-duplicate workflow logic
2. TRIGGER_COLLISION: Multiple workflows reacting to identical trigger events
3. CONTRADICTORY_ACTIONS: Workflows performing opposing actions (reroute vs cancel)
4. CIRCULAR: Graph cycles within a single workflow
5. INFINITE_LOOP: Cross-workflow cyclical triggers and self-triggering loops
6. APPROVAL_BYPASS: Uncontrolled execution bypassing human-in-the-loop gates
7. RACE_CONDITION: Concurrent state modifications on the same entity
8. IMPOSSIBLE_CONDITION: Logically contradictory condition chains
9. UNREACHABLE_NODE: Dead-code nodes unreachable from start
10. INVALID_STATE_TRANSITION: Business rule violations in state changes
"""

from __future__ import annotations
import os
import uuid
import logging
from datetime import datetime
from typing import Optional, List, Dict, Set

from automation.schema import (
    WorkflowDefinition, WorkflowNode, WorkflowEdge, NodeType, TriggerType,
    ConflictResult, ConflictType, ConflictSeverity, Condition, Operator
)

logger = logging.getLogger(__name__)
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")


class ConflictDetector:
    """Deterministic and semantic conflict detection engine."""

    async def detect_conflicts(
        self,
        workflows: list[WorkflowDefinition],
        target_workflow: Optional[WorkflowDefinition] = None,
        db=None
    ) -> list[ConflictResult]:
        """Detect all conflicts across the given set of workflows."""
        all_wfs = list(workflows)
        if target_workflow and target_workflow not in all_wfs:
            all_wfs.append(target_workflow)

        conflicts: list[ConflictResult] = []

        # 1. DUPLICATE
        conflicts.extend(self._check_duplicates(all_wfs))

        # 2. TRIGGER_COLLISION
        conflicts.extend(self._check_trigger_collisions(all_wfs))

        # 3. CONTRADICTORY_ACTIONS
        conflicts.extend(self._check_contradictory_actions(all_wfs))

        # 4. CIRCULAR (within single workflow)
        for wf in all_wfs:
            conflicts.extend(self._check_circular(wf))

        # 5. INFINITE_LOOP
        conflicts.extend(self._check_infinite_loops(all_wfs))

        # 6. APPROVAL_BYPASS
        conflicts.extend(self._check_approval_bypass(all_wfs))

        # 7. RACE_CONDITION
        conflicts.extend(self._check_race_conditions(all_wfs))

        # 8. IMPOSSIBLE_CONDITION
        for wf in all_wfs:
            conflicts.extend(self._check_impossible_conditions(wf))

        # 9. UNREACHABLE_NODE
        for wf in all_wfs:
            conflicts.extend(self._check_unreachable_nodes(wf))

        # 10. INVALID_STATE_TRANSITION
        for wf in all_wfs:
            conflicts.extend(self._check_invalid_transitions(wf))

        # Filter for target workflow if provided
        if target_workflow:
            conflicts = [
                c for c in conflicts
                if target_workflow.id in c.workflows_involved
            ]

        return conflicts

    # ─── 1. Duplicate Workflows ───────────────────────────────────

    def _check_duplicates(self, workflows: list[WorkflowDefinition]) -> list[ConflictResult]:
        conflicts = []
        n = len(workflows)
        for i in range(n):
            for j in range(i + 1, n):
                w1, w2 = workflows[i], workflows[j]
                if w1.trigger.type == w2.trigger.type:
                    tools1 = self._extract_action_tools(w1)
                    tools2 = self._extract_action_tools(w2)
                    if tools1 and tools1 == tools2:
                        conflicts.append(ConflictResult(
                            id=f"conf_dup_{uuid.uuid4().hex[:8]}",
                            type=ConflictType.DUPLICATE,
                            severity=ConflictSeverity.MEDIUM,
                            workflows_involved=[w1.id, w2.id],
                            workflow_names=[w1.name, w2.name],
                            affected_nodes=[],
                            explanation=f"Workflows '{w1.name}' and '{w2.name}' share identical trigger '{w1.trigger.type.value}' and execute the exact same tool set: {list(tools1)}.",
                            potential_impact="Redundant background processing, duplicate alerts, and wasted compute resources.",
                            confidence=0.95,
                            recommended_fix="Consolidate duplicate workflows or adjust conditions to differentiate their execution scopes.",
                        ))
        return conflicts

    # ─── 2. Trigger Collision ─────────────────────────────────────

    def _check_trigger_collisions(self, workflows: list[WorkflowDefinition]) -> list[ConflictResult]:
        conflicts = []
        by_trigger: dict[str, list[WorkflowDefinition]] = {}
        for wf in workflows:
            t_key = wf.trigger.type.value if hasattr(wf.trigger.type, "value") else str(wf.trigger.type)
            by_trigger.setdefault(t_key, []).append(wf)

        for trig, wfs in by_trigger.items():
            if len(wfs) > 1:
                names = [w.name for w in wfs]
                ids = [w.id for w in wfs]
                conflicts.append(ConflictResult(
                    id=f"conf_trig_{uuid.uuid4().hex[:8]}",
                    type=ConflictType.TRIGGER_COLLISION,
                    severity=ConflictSeverity.HIGH,
                    workflows_involved=ids,
                    workflow_names=names,
                    affected_nodes=[w.nodes[0].id for w in wfs if w.nodes],
                    explanation=f"{len(wfs)} workflows ({', '.join(names)}) activate on the same event '{trig}'.",
                    potential_impact="Potential concurrent execution collisions and notification floods for identical logistics incidents.",
                    confidence=0.88,
                    recommended_fix="Specify more restrictive trigger condition criteria or assign execution priority rules.",
                ))
        return conflicts

    # ─── 3. Contradictory Actions ─────────────────────────────────

    def _check_contradictory_actions(self, workflows: list[WorkflowDefinition]) -> list[ConflictResult]:
        conflicts = []
        n = len(workflows)
        for i in range(n):
            for j in range(i + 1, n):
                w1, w2 = workflows[i], workflows[j]
                if w1.trigger.type == w2.trigger.type:
                    tools1 = self._extract_action_tools(w1)
                    tools2 = self._extract_action_tools(w2)
                    
                    # Contradiction: Reroute vs Cancel
                    if "optimize_route" in tools1 and "update_shipment_status" in tools2:
                        w2_cancels = any(
                            n.tool_params.get("new_status") in ("Cancelled", "Held")
                            for n in w2.nodes if n.tool == "update_shipment_status"
                        )
                        if w2_cancels:
                            conflicts.append(ConflictResult(
                                id=f"conf_contra_{uuid.uuid4().hex[:8]}",
                                type=ConflictType.CONTRADICTORY_ACTIONS,
                                severity=ConflictSeverity.CRITICAL,
                                workflows_involved=[w1.id, w2.id],
                                workflow_names=[w1.name, w2.name],
                                affected_nodes=[],
                                explanation=f"Contradictory operational directives: '{w1.name}' attempts route optimization while '{w2.name}' flags shipment cancellation on the same event.",
                                potential_impact="Inconsistent logistics state, disrupted transport carrier bookings, and operational confusion.",
                                confidence=0.91,
                                recommended_fix="Define explicit mutual exclusion rules or a clear priority escalation hierarchy.",
                            ))
        return conflicts

    # ─── 4. Circular Workflows (Single Graph Cycles) ──────────────

    def _check_circular(self, wf: WorkflowDefinition) -> list[ConflictResult]:
        adj: dict[str, list[str]] = {}
        for edge in wf.edges:
            adj.setdefault(edge.source, []).append(edge.target)

        visited: set[str] = set()
        rec_stack: set[str] = set()
        cycle_nodes: list[str] = []

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            for neighbor in adj.get(node_id, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        cycle_nodes.append(neighbor)
                        return True
                elif neighbor in rec_stack:
                    cycle_nodes.append(neighbor)
                    return True
            rec_stack.remove(node_id)
            return False

        for node in wf.nodes:
            if node.id not in visited:
                if dfs(node.id):
                    return [ConflictResult(
                        id=f"conf_circ_{uuid.uuid4().hex[:8]}",
                        type=ConflictType.CIRCULAR,
                        severity=ConflictSeverity.CRITICAL,
                        workflows_involved=[wf.id],
                        workflow_names=[wf.name],
                        affected_nodes=cycle_nodes,
                        explanation=f"Circular execution cycle detected in workflow '{wf.name}' involving nodes: {cycle_nodes}.",
                        potential_impact="Execution deadlocks and infinite loops during runtime evaluation.",
                        confidence=1.0,
                        recommended_fix="Remove cycle-forming edges and structure execution as a Directed Acyclic Graph (DAG).",
                    )]
        return []

    # ─── 5. Infinite Loops (Cross-Workflow & Self-Triggering) ─────

    def _check_infinite_loops(self, workflows: list[WorkflowDefinition]) -> list[ConflictResult]:
        conflicts = []
        for wf in workflows:
            trig_type = wf.trigger.type.value if hasattr(wf.trigger.type, "value") else str(wf.trigger.type)
            tools = self._extract_action_tools(wf)
            if trig_type == "shipment_status_changed" and "update_shipment_status" in tools:
                conflicts.append(ConflictResult(
                    id=f"conf_inf_{uuid.uuid4().hex[:8]}",
                    type=ConflictType.INFINITE_LOOP,
                    severity=ConflictSeverity.CRITICAL,
                    workflows_involved=[wf.id],
                    workflow_names=[wf.name],
                    affected_nodes=[n.id for n in wf.nodes if n.tool == "update_shipment_status"],
                    explanation=f"Workflow '{wf.name}' triggers on 'shipment_status_changed' and executes 'update_shipment_status', creating a potential self-triggering infinite execution loop.",
                    potential_impact="Rapid cascade of redundant trigger invocations and backend resource exhaustion.",
                    confidence=0.85,
                    recommended_fix="Add specific state condition filters (e.g., status == 'At Risk') or break recursion with terminal state guards.",
                ))
        return conflicts

    # ─── 6. Approval Bypass ───────────────────────────────────────

    def _check_approval_bypass(self, workflows: list[WorkflowDefinition]) -> list[ConflictResult]:
        conflicts = []
        n = len(workflows)
        for i in range(n):
            for j in range(i + 1, n):
                w1, w2 = workflows[i], workflows[j]
                if w1.trigger.type == w2.trigger.type:
                    has_approval1 = any(node.type == NodeType.APPROVAL for node in w1.nodes)
                    has_approval2 = any(node.type == NodeType.APPROVAL for node in w2.nodes)
                    
                    if has_approval1 != has_approval2:
                        controlled_wf = w1 if has_approval1 else w2
                        bypass_wf = w2 if has_approval1 else w1
                        conflicts.append(ConflictResult(
                            id=f"conf_bypass_{uuid.uuid4().hex[:8]}",
                            type=ConflictType.APPROVAL_BYPASS,
                            severity=ConflictSeverity.HIGH,
                            workflows_involved=[controlled_wf.id, bypass_wf.id],
                            workflow_names=[controlled_wf.name, bypass_wf.name],
                            affected_nodes=[],
                            explanation=f"'{controlled_wf.name}' mandates human manager approval before taking action, but '{bypass_wf.name}' automates similar actions on the same event without approval.",
                            potential_impact="Automated workflow may bypass required compliance and manager authorization gates.",
                            confidence=0.84,
                            recommended_fix="Align governance policies: add required approval nodes to the automated workflow or narrow its activation criteria.",
                        ))
        return conflicts

    # ─── 7. Race Conditions ───────────────────────────────────────

    def _check_race_conditions(self, workflows: list[WorkflowDefinition]) -> list[ConflictResult]:
        conflicts = []
        n = len(workflows)
        for i in range(n):
            for j in range(i + 1, n):
                w1, w2 = workflows[i], workflows[j]
                if w1.trigger.type == w2.trigger.type:
                    tools1 = self._extract_action_tools(w1)
                    tools2 = self._extract_action_tools(w2)
                    mutating = {"update_shipment_status", "optimize_route"}
                    if tools1.intersection(mutating) and tools2.intersection(mutating):
                        conflicts.append(ConflictResult(
                            id=f"conf_race_{uuid.uuid4().hex[:8]}",
                            type=ConflictType.RACE_CONDITION,
                            severity=ConflictSeverity.HIGH,
                            workflows_involved=[w1.id, w2.id],
                            workflow_names=[w1.name, w2.name],
                            affected_nodes=[],
                            explanation=f"Workflows '{w1.name}' and '{w2.name}' simultaneously mutate shipment state upon receiving '{w1.trigger.type.value}'.",
                            potential_impact="Non-deterministic state overwrites and transport booking race conditions.",
                            confidence=0.82,
                            recommended_fix="Implement shipment entity locking or serialize workflow execution order.",
                        ))
        return conflicts

    # ─── 8. Impossible Conditions ─────────────────────────────────

    def _check_impossible_conditions(self, wf: WorkflowDefinition) -> list[ConflictResult]:
        conflicts = []
        for node in wf.nodes:
            if node.type == NodeType.CONDITION and len(node.conditions) > 1 and node.logic == "AND":
                # Check for contradiction on same field
                field_bounds: dict[str, dict[str, float]] = {}
                for cond in node.conditions:
                    try:
                        val = float(cond.value)
                        f = cond.field
                        field_bounds.setdefault(f, {})
                        if cond.operator in (Operator.GT, Operator.GTE):
                            field_bounds[f]["min"] = max(field_bounds[f].get("min", float("-inf")), val)
                        elif cond.operator in (Operator.LT, Operator.LTE):
                            field_bounds[f]["max"] = min(field_bounds[f].get("max", float("inf")), val)
                    except (ValueError, TypeError):
                        pass

                for f, bounds in field_bounds.items():
                    if "min" in bounds and "max" in bounds and bounds["min"] > bounds["max"]:
                        conflicts.append(ConflictResult(
                            id=f"conf_impos_{uuid.uuid4().hex[:8]}",
                            type=ConflictType.IMPOSSIBLE_CONDITION,
                            severity=ConflictSeverity.MEDIUM,
                            workflows_involved=[wf.id],
                            workflow_names=[wf.name],
                            affected_nodes=[node.id],
                            explanation=f"Impossible condition in workflow '{wf.name}' at node '{node.label}': requires {f} > {bounds['min']} AND {f} < {bounds['max']}.",
                            potential_impact="This branch will evaluate to FALSE 100% of the time, starving subsequent actions.",
                            confidence=1.0,
                            recommended_fix="Review and correct mathematical inequality bounds in condition expression.",
                        ))
        return conflicts

    # ─── 9. Unreachable Nodes ─────────────────────────────────────

    def _check_unreachable_nodes(self, wf: WorkflowDefinition) -> list[ConflictResult]:
        if not wf.nodes:
            return []

        adj: dict[str, list[str]] = {}
        for edge in wf.edges:
            adj.setdefault(edge.source, []).append(edge.target)

        # Trigger or start nodes
        incoming = {e.target for e in wf.edges}
        start_nodes = [n.id for n in wf.nodes if n.id not in incoming]
        if not start_nodes and wf.nodes:
            start_nodes = [wf.nodes[0].id]

        reachable: set[str] = set()
        queue = list(start_nodes)
        while queue:
            curr = queue.pop(0)
            if curr not in reachable:
                reachable.add(curr)
                queue.extend(adj.get(curr, []))

        unreachable = [n.id for n in wf.nodes if n.id not in reachable]
        if unreachable:
            return [ConflictResult(
                id=f"conf_unreach_{uuid.uuid4().hex[:8]}",
                type=ConflictType.UNREACHABLE_NODE,
                severity=ConflictSeverity.LOW,
                workflows_involved=[wf.id],
                workflow_names=[wf.name],
                affected_nodes=unreachable,
                explanation=f"Unreachable dead-code node(s) {unreachable} detected in '{wf.name}'.",
                potential_impact="Nodes exist in graph but will never execute under any path.",
                confidence=1.0,
                recommended_fix="Connect missing incoming edges to these nodes or remove them from the workflow canvas.",
            )]
        return []

    # ─── 10. Invalid State Transitions ────────────────────────────

    def _check_invalid_transitions(self, wf: WorkflowDefinition) -> list[ConflictResult]:
        conflicts = []
        for node in wf.nodes:
            if node.tool == "update_shipment_status":
                new_status = node.tool_params.get("new_status")
                # Check if trying to transition a terminal delivered shipment
                if new_status in ("Delayed", "At Risk", "Customs", "Preparing"):
                    # If this workflow triggers on shipment_delivered, it's invalid
                    if wf.trigger.type == TriggerType.SHIPMENT_DELIVERED:
                        conflicts.append(ConflictResult(
                            id=f"conf_trans_{uuid.uuid4().hex[:8]}",
                            type=ConflictType.INVALID_STATE_TRANSITION,
                            severity=ConflictSeverity.HIGH,
                            workflows_involved=[wf.id],
                            workflow_names=[wf.name],
                            affected_nodes=[node.id],
                            explanation=f"Workflow '{wf.name}' attempts invalid state transition: moving Delivered shipment back to '{new_status}'.",
                            potential_impact="Breaches audit compliance and corrupts terminal shipment lifecycle history.",
                            confidence=0.95,
                            recommended_fix="Disallow state modifications once a shipment is flagged in terminal 'Delivered' status.",
                        ))
        return conflicts

    # ─── Helper Methods ───────────────────────────────────────────

    def _extract_action_tools(self, wf: WorkflowDefinition) -> set[str]:
        """Get the set of tool names executed by action nodes."""
        return {n.tool for n in wf.nodes if n.type == NodeType.ACTION and n.tool}


async def detect_all_conflicts(db) -> list[ConflictResult]:
    """Load all active workflows from database and run full conflict detection."""
    docs = await db.workflows.find({"status": {"$in": ["active", "draft"]}}, {"_id": 0}).to_list(100)
    workflows = [WorkflowDefinition(**d) for d in docs]
    detector = ConflictDetector()
    return await detector.detect_conflicts(workflows, db=db)
