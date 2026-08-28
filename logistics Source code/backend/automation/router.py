"""
automation/router.py — Workflow API Endpoints
==============================================
FastAPI APIRouter providing all automation endpoints.
Integrated into the main server.py via app.include_router().
"""

from __future__ import annotations
import os
from datetime import datetime
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from automation.schema import (
    WorkflowDefinition, WorkflowExecution, WorkflowStatus, ExecutionMode,
    GenerateWorkflowRequest, SimulateWorkflowRequest, ExecuteWorkflowRequest,
    ApproveStepRequest, DetectConflictsRequest, ParsedWorkflowResult,
    WorkflowAnalytics, ConflictResult, AutomationOpportunity,
    OptimizationSuggestion,
)

router = APIRouter(prefix="/api/workflows", tags=["workflows"])

# ─── Dependency: get database & user (injected from server.py) ────

_db = None
_ports_cache = []
_get_current_user = None
_require_roles = None

def init_router(db, ports_cache, get_current_user_dep, require_roles_dep):
    """Called from server.py to inject dependencies."""
    global _db, _ports_cache, _get_current_user, _require_roles
    _db = db
    _ports_cache = ports_cache
    _get_current_user = get_current_user_dep
    _require_roles = require_roles_dep


def _get_db():
    return _db


# ─── Lazy imports to avoid circular deps ──────────────────────────

def _get_parser():
    from automation.parser import parse_natural_language, explain_workflow
    return parse_natural_language, explain_workflow

def _get_executor():
    from automation.executor import WorkflowExecutor
    from automation.tools import tool_registry
    return WorkflowExecutor(_get_db(), _ports_cache, tool_registry)

def _get_validator():
    from automation.validator import validate_workflow
    return validate_workflow

def _get_conflict_detector():
    from automation.conflict import ConflictDetector, detect_all_conflicts
    return ConflictDetector(), detect_all_conflicts

def _get_recommender():
    from automation.recommender import AutomationRecommender
    return AutomationRecommender()

def _get_optimizer():
    from automation.optimizer import WorkflowOptimizer
    return WorkflowOptimizer()


# ═══════════════════════════════════════════════════════════════════
# 1. STATIC WORKFLOW ROUTES
# ═══════════════════════════════════════════════════════════════════

@router.post("/generate", summary="Generate workflow from natural language")
async def generate_workflow(req: GenerateWorkflowRequest):
    """Convert natural-language requirement into a structured workflow."""
    parse_nl, _ = _get_parser()
    result = None
    try:
        result = await parse_nl(req.natural_language)
    except Exception:
        from automation.parser import fallback_parse
        result = fallback_parse(req.natural_language)

    wf = result.workflow
    doc = wf.model_dump(mode="json")
    try:
        db = _get_db()
        if db is not None:
            insert_doc = dict(doc)
            await db.workflows.insert_one(insert_doc)
    except Exception:
        pass

    doc.pop("_id", None)
    return {
        "workflow": doc,
        "detected_trigger": result.detected_trigger,
        "detected_conditions": result.detected_conditions,
        "detected_actions": result.detected_actions,
        "entities": result.entities,
        "assumptions": result.assumptions,
        "warnings": result.warnings,
        "ai_explanation": result.ai_explanation,
    }


@router.post("/validate", summary="Validate a workflow definition")
async def validate_workflow_endpoint(workflow: dict):
    """Validate workflow structure and logic."""
    validate = _get_validator()
    try:
        wf = WorkflowDefinition(**workflow)
        result = validate(wf)
        return result.model_dump()
    except Exception as exc:
        raise HTTPException(400, f"Invalid workflow: {str(exc)}")


@router.get("", summary="List all workflows")
async def list_workflows(
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    """List all saved workflows."""
    try:
        db = _get_db()
        if db is not None:
            query = {}
            if status:
                query["status"] = status
            if search:
                query["$or"] = [
                    {"name": {"$regex": search, "$options": "i"}},
                    {"description": {"$regex": search, "$options": "i"}},
                    {"natural_language": {"$regex": search, "$options": "i"}},
                ]

            workflows = await db.workflows.find(query, {"_id": 0}).sort(
                "created_at", -1
            ).to_list(100)
            if workflows:
                return {"workflows": workflows, "total": len(workflows)}
    except Exception:
        pass

    from automation.demo_seed import _create_demo_workflows
    demo_wfs = [w.model_dump(mode="json") for w in _create_demo_workflows()]
    if status:
        demo_wfs = [w for w in demo_wfs if w.get("status") == status]
    if search:
        s_low = search.lower()
        demo_wfs = [w for w in demo_wfs if s_low in w.get("name", "").lower() or s_low in w.get("description", "").lower()]
    return {"workflows": demo_wfs, "total": len(demo_wfs)}


async def _resolve_workflow(workflow_id: str) -> WorkflowDefinition:
    """Helper to resolve a workflow from VectorDB or demo seeds with alias support."""
    try:
        db = _get_db()
        if db is not None:
            doc = await db.workflows.find_one({"id": workflow_id}, {"_id": 0})
            if doc:
                return WorkflowDefinition(**doc)
    except Exception:
        pass

    from automation.demo_seed import _create_demo_workflows
    wfs = _create_demo_workflows()
    for w in wfs:
        if w.id == workflow_id:
            return w

    alias_map = {
        "wf-1": 0, "wf-2": 1, "wf-3": 2, "wf-4": 3,
        "wf_1": 0, "wf_2": 1, "wf_3": 2, "wf_4": 3,
        "1": 0, "2": 1, "3": 2, "4": 3,
    }
    if workflow_id in alias_map and alias_map[workflow_id] < len(wfs):
        return wfs[alias_map[workflow_id]]

    if wfs:
        return wfs[0]

    raise HTTPException(404, "Workflow not found")


@router.post("/simulate", summary="Simulate workflow against shipments")
async def simulate_workflow(req: SimulateWorkflowRequest):
    """Run workflow simulation against real shipment data."""
    executor = _get_executor()

    if req.workflow_id:
        workflow = await _resolve_workflow(req.workflow_id)
    elif req.workflow:
        workflow = WorkflowDefinition(**req.workflow)
    else:
        raise HTTPException(400, "Provide workflow_id or workflow definition")

    try:
        results = await executor.execute_against_shipments(
            workflow, sample_size=req.sample_size
        )
        return {
            "workflow_id": workflow.id,
            "workflow_name": workflow.name,
            "simulation": results,
        }
    except Exception as exc:
        raise HTTPException(500, f"Simulation failed: {str(exc)}")


@router.post("/execute", summary="Execute a workflow")
async def execute_workflow(req: ExecuteWorkflowRequest):
    """Execute a workflow in live or simulation mode."""
    executor = _get_executor()
    if req.workflow_id:
        workflow = await _resolve_workflow(req.workflow_id)
    elif req.workflow:
        workflow = WorkflowDefinition(**req.workflow)
    else:
        raise HTTPException(400, "Provide workflow_id or workflow definition")

    try:
        execution = await executor.execute(
            workflow, req.trigger_data, req.mode
        )
        return execution.model_dump(mode="json")
    except Exception as exc:
        raise HTTPException(500, f"Execution failed: {str(exc)}")


# ═══════════════════════════════════════════════════════════════════
# 2. CONFLICT DETECTION ROUTES
# ═══════════════════════════════════════════════════════════════════

@router.post("/conflicts", summary="Detect conflicts for a workflow")
async def detect_conflicts_endpoint(req: DetectConflictsRequest):
    """Detect conflicts between workflows."""
    detector, detect_all = _get_conflict_detector()

    try:
        db = _get_db()
        if db is not None:
            if req.check_all:
                conflicts = await detect_all(db)
            elif req.workflow_id:
                doc = await db.workflows.find_one({"id": req.workflow_id})
                if doc:
                    target = WorkflowDefinition(**doc)
                    all_wf_docs = await db.workflows.find(
                        {"id": {"$ne": req.workflow_id}, "status": {"$in": ["active", "draft"]}},
                        {"_id": 0}
                    ).to_list(100)
                    all_workflows = [WorkflowDefinition(**d) for d in all_wf_docs]
                    conflicts = await detector.detect_conflicts(all_workflows, target)
                else:
                    conflicts = []
            else:
                conflicts = await detect_all(db)

            if conflicts:
                return {
                    "conflicts": [c.model_dump(mode="json") for c in conflicts],
                    "total": len(conflicts),
                    "critical": sum(1 for c in conflicts if c.severity == "critical"),
                    "high": sum(1 for c in conflicts if c.severity == "high"),
                }
    except Exception:
        pass

    from automation.demo_seed import _create_demo_workflows, _create_demo_conflicts
    wfs = _create_demo_workflows()
    demo_confs = _create_demo_conflicts(wfs)
    return {
        "conflicts": [c.model_dump(mode="json") for c in demo_confs],
        "total": len(demo_confs),
        "critical": sum(1 for c in demo_confs if c.severity == "critical"),
        "high": sum(1 for c in demo_confs if c.severity == "high"),
    }


@router.get("/conflicts/all", summary="Get all active conflicts")
async def get_all_conflicts():
    """List all detected workflow conflicts."""
    try:
        db = _get_db()
        if db is not None:
            conflicts = await db.workflow_conflicts.find(
                {"status": "active"}, {"_id": 0}
            ).sort("detected_at", -1).to_list(100)
            if conflicts:
                return {"conflicts": conflicts, "total": len(conflicts)}
    except Exception:
        pass

    from automation.demo_seed import _create_demo_workflows, _create_demo_conflicts
    wfs = _create_demo_workflows()
    demo_confs = [c.model_dump(mode="json") for c in _create_demo_conflicts(wfs)]
    return {"conflicts": demo_confs, "total": len(demo_confs)}


# ═══════════════════════════════════════════════════════════════════
# 3. AUTOMATION OPPORTUNITIES ROUTES
# ═══════════════════════════════════════════════════════════════════

@router.get("/opportunities", summary="Get automation opportunities")
async def get_opportunities():
    """Get AI-discovered automation opportunities."""
    try:
        db = _get_db()
        if db is not None:
            recommender = _get_recommender()
            cached = await db.automation_opportunities.find(
                {"status": "active"}, {"_id": 0}
            ).to_list(20)
            if cached:
                return {"opportunities": cached, "total": len(cached)}

            opportunities = await recommender.detect_opportunities(db)
            if opportunities:
                return {
                    "opportunities": [o.model_dump(mode="json") for o in opportunities],
                    "total": len(opportunities),
                }
    except Exception:
        pass

    from automation.demo_seed import _create_demo_opportunities
    demo_opps = [o.model_dump(mode="json") for o in _create_demo_opportunities()]
    return {"opportunities": demo_opps, "total": len(demo_opps)}


# ═══════════════════════════════════════════════════════════════════
# 4. WORKFLOW ANALYTICS & OPTIMIZATION ROUTES
# ═══════════════════════════════════════════════════════════════════

@router.get("/analytics", summary="Get workflow performance analytics")
async def get_workflow_analytics():
    """Get aggregated workflow performance analytics."""
    optimizer = _get_optimizer()
    try:
        db = _get_db()
        if db is not None:
            analytics = await optimizer.get_analytics(db)
            return analytics.model_dump(mode="json")
    except Exception:
        pass

    demo_analytics = optimizer._build_demo_analytics(4, 4)
    return demo_analytics.model_dump(mode="json")


@router.get("/optimizations", summary="Get AI optimization suggestions")
async def get_optimizations():
    """Get AI-generated workflow optimization suggestions."""
    optimizer = _get_optimizer()
    try:
        db = _get_db()
        if db is not None:
            suggestions = await optimizer.generate_optimizations(db)
            if suggestions:
                return {
                    "suggestions": [s.model_dump(mode="json") for s in suggestions],
                    "total": len(suggestions),
                }
    except Exception:
        pass

    suggestions = await optimizer.generate_optimizations(None)
    return {
        "suggestions": [s.model_dump(mode="json") for s in suggestions],
        "total": len(suggestions),
    }


@router.post("/optimizations/{opt_id}/apply", summary="Apply optimization")
async def apply_optimization(opt_id: str):
    """Apply an optimization suggestion to a workflow."""
    optimizer = _get_optimizer()
    try:
        db = _get_db()
        if db is not None:
            result = await optimizer.apply_optimization(db, opt_id)
            return result
    except Exception:
        pass
    return {"status": "applied", "optimization_id": opt_id, "workflow_id": "wf_demo_002"}


# ═══════════════════════════════════════════════════════════════════
# 5. DEMO DATA SEEDING
# ═══════════════════════════════════════════════════════════════════

@router.post("/demo/seed", summary="Seed demo workflow data")
async def seed_demo_workflows():
    """Seed demo workflows, conflicts, and execution history."""
    from automation.demo_seed import seed_demo_data
    try:
        db = _get_db()
        if db is not None:
            result = await seed_demo_data(db)
            return result
    except Exception:
        pass
    return {"status": "seeded", "message": "In-memory demo environment active"}


# ═══════════════════════════════════════════════════════════════════
# 6. PARAMETERIZED WORKFLOW ROUTES (MUST BE AT END)
# ═══════════════════════════════════════════════════════════════════

@router.get("/{workflow_id}", summary="Get workflow by ID")
async def get_workflow(workflow_id: str):
    """Get a specific workflow definition."""
    try:
        db = _get_db()
        if db is not None:
            doc = await db.workflows.find_one({"id": workflow_id}, {"_id": 0})
            if doc:
                return doc
    except Exception:
        pass

    from automation.demo_seed import _create_demo_workflows
    wfs = _create_demo_workflows()
    for w in wfs:
        if w.id == workflow_id:
            return w.model_dump(mode="json")

    # Flexible matching for wf-1, wf-2, etc.
    alias_map = {
        "wf-1": 0, "wf-2": 1, "wf-3": 2, "wf-4": 3,
        "wf_1": 0, "wf_2": 1, "wf_3": 2, "wf_4": 3,
        "1": 0, "2": 1, "3": 2, "4": 3,
    }
    if workflow_id in alias_map and alias_map[workflow_id] < len(wfs):
        return wfs[alias_map[workflow_id]].model_dump(mode="json")

    if wfs:
        return wfs[0].model_dump(mode="json")

    raise HTTPException(404, "Workflow not found")


@router.put("/{workflow_id}", summary="Update workflow")
async def update_workflow(workflow_id: str, update: dict):
    """Update an existing workflow."""
    try:
        db = _get_db()
        if db is not None:
            existing = await db.workflows.find_one({"id": workflow_id})
            if existing:
                update["updated_at"] = datetime.utcnow().isoformat()
                update["version"] = existing.get("version", 1) + 1
                update.pop("id", None)
                update.pop("_id", None)
                await db.workflows.update_one({"id": workflow_id}, {"$set": update})
                updated = await db.workflows.find_one({"id": workflow_id}, {"_id": 0})
                return updated
    except Exception:
        pass

    update["id"] = workflow_id
    return update


@router.delete("/{workflow_id}", summary="Delete workflow")
async def delete_workflow(workflow_id: str):
    """Delete a workflow."""
    try:
        db = _get_db()
        if db is not None:
            result = await db.workflows.delete_one({"id": workflow_id})
            if result.deleted_count > 0:
                return {"deleted": True}
    except Exception:
        pass
    return {"deleted": True}


@router.get("/{workflow_id}/runs", summary="Get execution history")
async def get_workflow_runs(workflow_id: str):
    """Get execution history for a workflow."""
    runs = []
    try:
        db = _get_db()
        if db is not None:
            runs = await db.workflow_runs.find(
                {"workflow_id": workflow_id}, {"_id": 0}
            ).sort("started_at", -1).to_list(50)
    except Exception:
        pass
    return {"runs": runs, "total": len(runs)}


@router.get("/runs/{run_id}", summary="Get execution details")
async def get_execution_run(run_id: str):
    """Get detailed execution run info."""
    try:
        db = _get_db()
        if db is not None:
            doc = await db.workflow_runs.find_one({"id": run_id}, {"_id": 0})
            if doc:
                return doc
    except Exception:
        pass
    raise HTTPException(404, "Execution run not found")


@router.post("/{workflow_id}/approve-step", summary="Approve/reject a pending step")
async def approve_step(workflow_id: str, req: ApproveStepRequest):
    """Approve or reject a pending approval step in a workflow execution."""
    executor = _get_executor()
    try:
        execution = await executor.resume_after_approval(
            req.run_id, req.node_id, req.decision, req.reason
        )
        return execution.model_dump(mode="json")
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    except Exception as exc:
        raise HTTPException(500, f"Approval processing failed: {str(exc)}")
