"""
automation/parser.py — Natural Language to Workflow Parser
===========================================================
Converts user natural-language requirements into structured WorkflowDefinitions.
Uses Claude Sonnet 4.6 via emergentintegrations when available, with a
robust rule-based keyword parser fallback.
"""

from __future__ import annotations
import json
import os
import re
import uuid
import logging
from typing import Any, Optional

from automation.schema import (
    WorkflowDefinition, WorkflowNode, WorkflowEdge, WorkflowTrigger,
    Condition, NodeType, TriggerType, Operator, ParsedWorkflowResult,
    WorkflowStatus,
)

logger = logging.getLogger(__name__)

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
MODEL = ("anthropic", "claude-sonnet-4-6")


async def _call_llm(system: str, user: str) -> Optional[str]:
    """Call LLM safely with fallback if library or key is missing."""
    if not EMERGENT_LLM_KEY:
        return None
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        chat_client = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"wf_parse_{uuid.uuid4().hex[:6]}",
            system_message=system
        ).with_model(*MODEL)
        resp = await chat_client.send_message(UserMessage(text=user))
        return resp if isinstance(resp, str) else str(resp)
    except Exception as e:
        logger.warning(f"Workflow LLM parsing call failed: {e}")
        return None


def _extract_json(text: str) -> Optional[dict]:
    """Extract JSON object from string response."""
    try:
        # Strip potential markdown backticks
        clean = text.strip()
        if clean.startswith("```json"):
            clean = clean[7:]
        elif clean.startswith("```"):
            clean = clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        clean = clean.strip()

        start = clean.find("{")
        end = clean.rfind("}")
        if start != -1 and end != -1:
            return json.loads(clean[start:end + 1])
    except Exception:
        pass
    return None


async def parse_natural_language(text: str) -> ParsedWorkflowResult:
    """
    Convert a natural-language workflow requirement into a structured WorkflowDefinition.
    Attempts LLM extraction first, falling back to rule-based parser.
    """
    try:
        system_prompt = (
            "You are an expert AI logistics automation assistant. Convert the user's natural-language "
            "business workflow requirement into a structured JSON workflow definition.\n\n"
            "AVAILABLE TRIGGERS:\n"
            "- shipment_risk_updated (risk changes)\n"
            "- shipment_status_changed (status changes)\n"
            "- shipment_delayed (delay detected)\n"
            "- shipment_created (new shipment)\n"
            "- eta_changed (ETA updated)\n"
            "- customs_status_changed (customs hold/clearance)\n"
            "- geopolitical_event (strikes, weather, port closures)\n"
            "- carrier_disruption (carrier breakdown)\n"
            "- risk_threshold_exceeded (risk passes threshold)\n"
            "- shipment_delivered (delivery completed)\n"
            "- manual (user triggered)\n\n"
            "AVAILABLE TOOLS FOR ACTIONS:\n"
            "- get_shipment, calculate_risk, predict_eta, predict_customs_delay, optimize_route, "
            "analyze_root_cause, calculate_impact, calculate_financial_impact, run_simulation, "
            "create_alert, notify_manager, request_approval, update_shipment_status\n\n"
            "NODE TYPES: trigger, condition, action, delay, branch, approval, notification, end\n\n"
            "Respond ONLY with valid JSON in this structure:\n"
            "{\n"
            '  "workflow_name": "Short Name",\n'
            '  "workflow_description": "Clear explanation",\n'
            '  "trigger_type": "one_of_above",\n'
            '  "trigger_description": "...",\n'
            '  "detected_trigger": {"type": "...", "description": "..."},\n'
            '  "detected_conditions": [{"field": "risk_score|expected_delay|product_value", "operator": ">|>=|<|<=|==|!=", "value": 70, "unit": "days|INR"}],\n'
            '  "detected_actions": [{"tool": "...", "label": "..."}],\n'
            '  "entities": ["Shipments", "Logistics Manager"],\n'
            '  "assumptions": ["..."],\n'
            '  "warnings": ["..."],\n'
            '  "ai_explanation": "2-3 sentences explaining why this workflow was generated"\n'
            "}"
        )

        raw_response = await _call_llm(system_prompt, text)
        if raw_response:
            parsed_json = _extract_json(raw_response)
            if parsed_json and "workflow_name" in parsed_json:
                return _build_workflow_from_llm_json(parsed_json, text)
    except Exception as exc:
        logger.warning(f"LLM parsing attempt failed, using fallback: {exc}")

    # Fallback to rule-based parsing
    return fallback_parse(text)


def _build_workflow_from_llm_json(data: dict, original_text: str) -> ParsedWorkflowResult:
    """Build a complete ParsedWorkflowResult from LLM JSON output."""
    wf_id = f"wf_{uuid.uuid4().hex[:12]}"
    name = data.get("workflow_name", "Automated Logistics Workflow")
    description = data.get("workflow_description", original_text[:120])
    
    # Resolve trigger
    trigger_str = data.get("trigger_type", "shipment_risk_updated").lower()
    trigger_type = TriggerType.SHIPMENT_RISK_UPDATED
    for t in TriggerType:
        if t.value == trigger_str:
            trigger_type = t
            break

    trigger = WorkflowTrigger(
        type=trigger_type,
        description=data.get("trigger_description", f"Triggered on {trigger_type.value}"),
    )

    nodes: list[WorkflowNode] = []
    edges: list[WorkflowEdge] = []
    y_pos = 0

    # 1. Trigger Node
    trigger_node_id = f"node_{uuid.uuid4().hex[:8]}"
    trigger_node = WorkflowNode(
        id=trigger_node_id,
        type=NodeType.TRIGGER,
        label=trigger.description or "Workflow Trigger",
        description=f"Starts when {trigger_type.value} event occurs",
        position_x=250,
        position_y=y_pos,
    )
    nodes.append(trigger_node)
    prev_node_id = trigger_node_id
    y_pos += 120

    # 2. Add Conditions if any
    conditions_data = data.get("detected_conditions", [])
    for cond_dict in conditions_data:
        op_str = cond_dict.get("operator", ">")
        op = Operator.GT
        for o in Operator:
            if o.value == op_str:
                op = o
                break

        cond_obj = Condition(
            field=cond_dict.get("field", "risk_score"),
            operator=op,
            value=cond_dict.get("value", 50),
            unit=cond_dict.get("unit"),
        )
        cond_node_id = f"node_{uuid.uuid4().hex[:8]}"
        cond_node = WorkflowNode(
            id=cond_node_id,
            type=NodeType.CONDITION,
            label=f"{cond_obj.field} {cond_obj.operator.value} {cond_obj.value}{(' ' + cond_obj.unit) if cond_obj.unit else ''}?",
            conditions=[cond_obj],
            position_x=250,
            position_y=y_pos,
        )
        nodes.append(cond_node)
        edges.append(WorkflowEdge(source=prev_node_id, target=cond_node_id, label="default"))
        prev_node_id = cond_node_id
        y_pos += 120

    # 3. Add Actions
    actions_data = data.get("detected_actions", [])
    if not actions_data:
        # Default action
        actions_data = [{"tool": "optimize_route", "label": "Optimize Route"}]

    for action_dict in actions_data:
        tool_name = action_dict.get("tool", "optimize_route")
        label = action_dict.get("label", tool_name.replace("_", " ").title())
        
        # Check if this action is an approval
        if "approval" in tool_name or "approval" in label.lower():
            act_node_id = f"node_{uuid.uuid4().hex[:8]}"
            act_node = WorkflowNode(
                id=act_node_id,
                type=NodeType.APPROVAL,
                label=label,
                approver_role="manager",
                approval_message="Manager approval required for automated action",
                position_x=250,
                position_y=y_pos,
            )
        elif "notify" in tool_name or "alert" in tool_name:
            act_node_id = f"node_{uuid.uuid4().hex[:8]}"
            act_node = WorkflowNode(
                id=act_node_id,
                type=NodeType.NOTIFICATION,
                label=label,
                notification_type="alert",
                notification_target="manager",
                notification_template=f"Automated notification from {name}",
                position_x=250,
                position_y=y_pos,
            )
        else:
            act_node_id = f"node_{uuid.uuid4().hex[:8]}"
            act_node = WorkflowNode(
                id=act_node_id,
                type=NodeType.ACTION,
                label=label,
                tool=tool_name,
                position_x=250,
                position_y=y_pos,
            )

        nodes.append(act_node)
        edges.append(WorkflowEdge(source=prev_node_id, target=act_node_id, label="true" if "cond" in prev_node_id else "default"))
        prev_node_id = act_node_id
        y_pos += 120

    # 4. End Node
    end_node_id = f"node_{uuid.uuid4().hex[:8]}"
    end_node = WorkflowNode(
        id=end_node_id,
        type=NodeType.END,
        label="Complete",
        position_x=250,
        position_y=y_pos,
    )
    nodes.append(end_node)
    edges.append(WorkflowEdge(source=prev_node_id, target=end_node_id, label="default"))

    workflow = WorkflowDefinition(
        id=wf_id,
        name=name,
        description=description,
        natural_language=original_text,
        trigger=trigger,
        nodes=nodes,
        edges=edges,
        version=1,
        status=WorkflowStatus.ACTIVE,
        tags=["ai-generated", "logistics"],
    )

    return ParsedWorkflowResult(
        workflow=workflow,
        detected_trigger=data.get("detected_trigger", {"type": trigger_type.value, "description": trigger.description}),
        detected_conditions=data.get("detected_conditions", []),
        detected_actions=data.get("detected_actions", []),
        entities=data.get("entities", ["Shipment", "Operations Team"]),
        assumptions=data.get("assumptions", ["Assumes standard operational thresholds apply."]),
        warnings=data.get("warnings", []),
        ai_explanation=data.get("ai_explanation", f"Generated an automated pipeline to handle {trigger_type.value} events."),
    )


def fallback_parse(text: str) -> ParsedWorkflowResult:
    """Rule-based keyword parser when LLM is offline."""
    low = text.lower()
    wf_id = f"wf_{uuid.uuid4().hex[:12]}"
    
    # 1. Detect Trigger
    trigger_type = TriggerType.SHIPMENT_RISK_UPDATED
    trigger_desc = "Shipment Risk Updated"
    
    if any(k in low for k in ["delay", "late", "behind schedule"]):
        trigger_type = TriggerType.SHIPMENT_DELAYED
        trigger_desc = "Shipment Delayed"
    elif any(k in low for k in ["customs", "clearance", "held"]):
        trigger_type = TriggerType.CUSTOMS_STATUS_CHANGED
        trigger_desc = "Customs Status Changed"
    elif any(k in low for k in ["strike", "port closure", "weather", "geopolitical"]):
        trigger_type = TriggerType.GEOPOLITICAL_EVENT
        trigger_desc = "Geopolitical Disruption Event"
    elif any(k in low for k in ["carrier", "breakdown", "vehicle"]):
        trigger_type = TriggerType.CARRIER_DISRUPTION
        trigger_desc = "Carrier Disruption"
    elif any(k in low for k in ["delivered", "arrived", "completed"]):
        trigger_type = TriggerType.SHIPMENT_DELIVERED
        trigger_desc = "Shipment Delivered"
    elif any(k in low for k in ["create", "new shipment", "booked"]):
        trigger_type = TriggerType.SHIPMENT_CREATED
        trigger_desc = "New Shipment Created"
    elif any(k in low for k in ["risk", "threshold", "critical", "high risk"]):
        trigger_type = TriggerType.RISK_THRESHOLD_EXCEEDED
        trigger_desc = "Risk Threshold Exceeded"

    trigger = WorkflowTrigger(type=trigger_type, description=trigger_desc)

    # 2. Detect Conditions
    detected_conditions = []
    
    # Risk condition
    risk_match = re.search(r"risk(?:\s*score)?\s*(?:>|>=|above|exceeds?|greater than)\s*(\d+)", low)
    if risk_match:
        val = float(risk_match.group(1))
        detected_conditions.append({"field": "risk_score", "operator": ">=", "value": val, "unit": "score"})
    elif "high risk" in low or "critical" in low:
        detected_conditions.append({"field": "risk_score", "operator": ">=", "value": 70, "unit": "score"})

    # Delay condition
    delay_match = re.search(r"delay(?:\s*is)?\s*(?:>|>=|above|exceeds?|more than)\s*(\d+(?:\.\d+)?)\s*(?:days?|d|hrs?)?", low)
    if delay_match:
        val = float(delay_match.group(1))
        detected_conditions.append({"field": "expected_delay", "operator": ">", "value": val, "unit": "days"})

    # Value condition
    val_match = re.search(r"(?:value|worth|cost)\s*(?:is)?\s*(?:>|>=|above|exceeds?|more than)\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(lakh|l|k|cr)?", low)
    if val_match:
        num = float(val_match.group(1))
        multiplier = val_match.group(2)
        if multiplier in ("lakh", "l"):
            num = num * 100000
        elif multiplier == "cr":
            num = num * 10000000
        elif multiplier == "k":
            num = num * 1000
        detected_conditions.append({"field": "product_value", "operator": ">", "value": num, "unit": "INR"})
    elif "10 lakh" in low or "10l" in low:
        detected_conditions.append({"field": "product_value", "operator": ">", "value": 1000000, "unit": "INR"})

    # 3. Detect Actions
    detected_actions = []
    if any(k in low for k in ["reroute", "route", "alternate route", "optimize"]):
        detected_actions.append({"tool": "optimize_route", "label": "Optimize Route"})
    if any(k in low for k in ["root cause", "cause", "analyze why"]):
        detected_actions.append({"tool": "analyze_root_cause", "label": "Root Cause Analysis"})
    if any(k in low for k in ["eta", "predict arrival"]):
        detected_actions.append({"tool": "predict_eta", "label": "Predict New ETA"})
    if any(k in low for k in ["customs prediction", "clearance time"]):
        detected_actions.append({"tool": "predict_customs_delay", "label": "Predict Customs Delay"})
    if any(k in low for k in ["financial", "cost impact", "invoice"]):
        detected_actions.append({"tool": "calculate_financial_impact", "label": "Calculate Financial Impact"})
    if any(k in low for k in ["notify", "alert", "email", "message"]):
        target = "customer" if "customer" in low else "manager"
        detected_actions.append({"tool": "notify_manager" if target == "manager" else "create_alert", "label": f"Notify {target.title()}"})

    if not detected_actions:
        detected_actions.append({"tool": "calculate_risk", "label": "Analyze Shipment Risk"})
        detected_actions.append({"tool": "optimize_route", "label": "Optimize Route"})

    # Needs approval?
    has_approval = any(k in low for k in ["approval", "approve", "ask", "permission", "manager approval", "review"])

    # 4. Build Nodes & Edges
    nodes: list[WorkflowNode] = []
    edges: list[WorkflowEdge] = []
    y_pos = 0

    # Trigger Node
    trig_id = f"node_{uuid.uuid4().hex[:8]}"
    nodes.append(WorkflowNode(
        id=trig_id,
        type=NodeType.TRIGGER,
        label=trigger_desc,
        description=f"Triggered by {trigger_type.value}",
        position_x=250,
        position_y=y_pos,
    ))
    prev_id = trig_id
    y_pos += 120

    # Condition Node(s)
    for c in detected_conditions:
        op = Operator.GTE if c["operator"] == ">=" else Operator.GT
        cond_node_id = f"node_{uuid.uuid4().hex[:8]}"
        nodes.append(WorkflowNode(
            id=cond_node_id,
            type=NodeType.CONDITION,
            label=f"{c['field']} {c['operator']} {c['value']}{(' ' + c['unit']) if c.get('unit') else ''}?",
            conditions=[Condition(field=c["field"], operator=op, value=c["value"], unit=c.get("unit"))],
            position_x=250,
            position_y=y_pos,
        ))
        edges.append(WorkflowEdge(source=prev_id, target=cond_node_id, label="default"))
        prev_id = cond_node_id
        y_pos += 120

    # Action Nodes
    for act in detected_actions:
        act_id = f"node_{uuid.uuid4().hex[:8]}"
        nodes.append(WorkflowNode(
            id=act_id,
            type=NodeType.ACTION,
            label=act["label"],
            tool=act["tool"],
            position_x=250,
            position_y=y_pos,
        ))
        edges.append(WorkflowEdge(source=prev_id, target=act_id, label="true" if "cond" in prev_id else "default"))
        prev_id = act_id
        y_pos += 120

    # Approval Node if requested
    if has_approval:
        app_id = f"node_{uuid.uuid4().hex[:8]}"
        nodes.append(WorkflowNode(
            id=app_id,
            type=NodeType.APPROVAL,
            label="Manager Approval Required",
            approver_role="manager",
            approval_message="High-impact automation step requires manager confirmation.",
            position_x=250,
            position_y=y_pos,
        ))
        edges.append(WorkflowEdge(source=prev_id, target=app_id, label="default"))
        prev_id = app_id
        y_pos += 120

    # End Node
    end_id = f"node_{uuid.uuid4().hex[:8]}"
    nodes.append(WorkflowNode(
        id=end_id,
        type=NodeType.END,
        label="Execution Complete",
        position_x=250,
        position_y=y_pos,
    ))
    edges.append(WorkflowEdge(source=prev_id, target=end_id, label="default"))

    # Generate Name
    name = f"Auto {trigger_desc.replace('Trigger', '').strip()}"
    if detected_actions:
        name += f" -> {detected_actions[0]['label']}"

    wf = WorkflowDefinition(
        id=wf_id,
        name=name,
        description=f"Rule-parsed automation workflow for: {text[:100]}",
        natural_language=text,
        trigger=trigger,
        nodes=nodes,
        edges=edges,
        version=1,
        status=WorkflowStatus.ACTIVE,
        tags=["rule-generated", "logistics"],
    )

    return ParsedWorkflowResult(
        workflow=wf,
        detected_trigger={"type": trigger_type.value, "description": trigger_desc},
        detected_conditions=detected_conditions,
        detected_actions=detected_actions,
        entities=["Shipment", "Carrier", "Logistics Operations"],
        assumptions=["Standard logistics operating thresholds applied."],
        warnings=["Using deterministic rule parsing. Verify condition thresholds before deploying."] if not EMERGENT_LLM_KEY else [],
        ai_explanation=f"Identified trigger '{trigger_desc}', evaluated {len(detected_conditions)} condition(s), and orchestrated {len(detected_actions)} automated action(s) with human-in-the-loop approval as needed.",
    )


async def explain_workflow(workflow: WorkflowDefinition) -> str:
    """Generate a plain-English explanation of what a workflow does."""
    node_summary = ", ".join([n.label for n in workflow.nodes if n.label])
    prompt = (
        f"Explain what this logistics automation workflow does in 2 concise sentences:\n"
        f"Workflow Name: {workflow.name}\n"
        f"Trigger: {workflow.trigger.type.value}\n"
        f"Steps: {node_summary}\n"
    )
    res = await _call_llm("You are a logistics automation advisor. Explain the workflow concisely.", prompt)
    if res and len(res.strip()) > 15:
        return res.strip()
    return (
        f"Workflow '{workflow.name}' triggers on '{workflow.trigger.type.value}' events. "
        f"It sequentially evaluates conditions, executes registered recovery actions, and routes decisions to operations managers when required."
    )
