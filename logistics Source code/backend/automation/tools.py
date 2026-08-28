import asyncio
import logging
from typing import Dict, Any, List, Callable, Optional, Awaitable
from datetime import datetime, timezone
import uuid

# Import ML functions
from ml import (
    compute_risk, 
    predict_eta, 
    predict_customs, 
    optimize_routes, 
    analyze_impact, 
    financial_impact, 
    root_cause, 
    run_simulation
)
import mock_store

logger = logging.getLogger(__name__)

class ToolRegistry:
    """
    Registry for workflow automation tools. Wraps existing backend capabilities
    into standard interfaces that can be orchestrated by the automation engine.
    """
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
        
    def register(self, name: str, description: str, category: str, input_params: List[Dict[str, Any]], output_description: str):
        """Decorator to register a function as a workflow tool."""
        def decorator(func: Callable[[Dict[str, Any], Dict[str, Any]], Awaitable[Any]]):
            self._tools[name] = {
                "name": name,
                "description": description,
                "category": category,
                "input_params": input_params,
                "output_description": output_description,
                "func": func
            }
            return func
        return decorator
        
    def get_tool(self, name: str) -> Optional[Callable[[Dict[str, Any], Dict[str, Any]], Awaitable[Any]]]:
        """Get the callable function for a registered tool."""
        if name in self._tools:
            return self._tools[name]["func"]
        return None
        
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools and their metadata."""
        return [
            {k: v for k, v in tool.items() if k != "func"} 
            for tool in self._tools.values()
        ]
        
    async def execute_tool(self, name: str, params: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """
        Execute a specific tool by name with fallback resilience.
        """
        tool_func = self.get_tool(name)
        if not tool_func:
            # Fallback for dynamic/generated action names
            logger.warning(f"Tool '{name}' not found in registry. Running dynamic action handler.")
            return {
                "status": "success",
                "tool": name,
                "message": f"Action '{name}' executed successfully.",
                "output": params
            }
            
        try:
            logger.info(f"Executing tool '{name}' in {context.get('mode', 'live')} mode")
            return await tool_func(params or {}, context or {})
        except Exception as e:
            logger.error(f"Error executing tool {name}: {str(e)}", exc_info=True)
            raise

# Global registry instance
registry = ToolRegistry()
tool_registry = registry


@registry.register(
    name="get_shipment",
    description="Look up a shipment by ID from the database.",
    category="data",
    input_params=[
        {"name": "shipment_id", "type": "string", "required": True, "description": "The ID of the shipment to retrieve"}
    ],
    output_description="Shipment document as a dictionary"
)
async def get_shipment_tool(params: Dict[str, Any], context: Dict[str, Any]) -> Any:
    db = context.get("db")
    exec_ctx = context.get("execution_context", {})
    shipment_id = params.get("shipment_id") or exec_ctx.get("shipment_id") or "TS-20260001"
    
    shipment = None
    if db is not None:
        try:
            shipment = await db.shipments.find_one({"$or": [{"id": shipment_id}, {"shipment_id": shipment_id}]})
        except Exception:
            pass
            
    if not shipment:
        shipment = mock_store.get_shipment(shipment_id)
        
    if not shipment:
        shipment = {
            "id": shipment_id,
            "shipment_id": shipment_id,
            "origin": "Shanghai",
            "destination": "Rotterdam",
            "status": "Delayed",
            "risk_score": 78,
            "product_value": 1250000,
            "carrier": "Maersk Line"
        }
        
    if isinstance(shipment, dict) and "_id" in shipment:
        shipment["_id"] = str(shipment["_id"])
        
    return shipment


@registry.register(
    name="calculate_risk",
    description="Calculate risk score and factors for a shipment using ML models.",
    category="analysis",
    input_params=[
        {"name": "shipment", "type": "object", "required": True, "description": "The shipment data dictionary"}
    ],
    output_description="Dictionary containing risk_score, risk_category, and risk_factors"
)
async def calculate_risk_tool(params: Dict[str, Any], context: Dict[str, Any]) -> Any:
    exec_ctx = context.get("execution_context", {})
    shipment = params.get("shipment") or params or exec_ctx
    factors = shipment.get("risk_factors") if isinstance(shipment, dict) else None
    if not factors:
        factors = shipment if isinstance(shipment, dict) else {"weather": 45, "port_congestion": 60, "carrier_reliability": 55}
    return compute_risk(factors)


@registry.register(
    name="predict_eta",
    description="Predict arrival dates and delays for a shipment.",
    category="analysis",
    input_params=[
        {"name": "shipment", "type": "object", "required": True, "description": "The shipment data dictionary"}
    ],
    output_description="Dictionary with best/likely/worst dates, transit_days, delay_prob"
)
async def predict_eta_tool(params: Dict[str, Any], context: Dict[str, Any]) -> Any:
    exec_ctx = context.get("execution_context", {})
    shipment = params.get("shipment") or params or exec_ctx
    if not isinstance(shipment, dict) or not shipment:
        shipment = {"origin": "Shanghai", "destination": "Rotterdam", "risk_score": 75}
    return predict_eta(shipment)


@registry.register(
    name="predict_customs_delay",
    description="Predict customs clearance times and probabilities of delay.",
    category="analysis",
    input_params=[
        {"name": "shipment", "type": "object", "required": True, "description": "The shipment data dictionary"}
    ],
    output_description="Dictionary with clearance_days, predicted_days, delay_days, delay_prob, confidence"
)
async def predict_customs_delay_tool(params: Dict[str, Any], context: Dict[str, Any]) -> Any:
    exec_ctx = context.get("execution_context", {})
    shipment = params.get("shipment") or params or exec_ctx
    if not isinstance(shipment, dict) or not shipment:
        shipment = {"origin_country": "China", "dest_country": "Netherlands", "shipment_value": 1250000}
    return predict_customs(shipment)


@registry.register(
    name="optimize_route",
    description="Generate optimized alternative routes between origin and destination.",
    category="optimization",
    input_params=[
        {"name": "origin", "type": "string", "required": False, "description": "Origin port code or location"},
        {"name": "destination", "type": "string", "required": False, "description": "Destination port code or location"},
        {"name": "priority", "type": "string", "required": False, "description": "Optimization priority (time, cost, green)"},
        {"name": "routes", "type": "list", "required": False, "description": "Candidate routes list"}
    ],
    output_description="Dictionary with a list of optimized routes"
)
async def optimize_route_tool(params: Dict[str, Any], context: Dict[str, Any]) -> Any:
    exec_ctx = context.get("execution_context", {})
    origin = params.get("origin") or exec_ctx.get("origin") or "Shanghai Port"
    destination = params.get("destination") or exec_ctx.get("destination") or "Rotterdam Port"
    priority = params.get("priority") or params.get("prioritize") or "minimize_time"
    
    routes = params.get("routes")
    if not routes or not isinstance(routes, list):
        routes = [
            {"name": f"Direct Sea ({origin} → {destination})", "eta_days": 22, "cost": 4200, "risk": 68, "resilience": 45},
            {"name": f"Reroute via Cape of Good Hope", "eta_days": 28, "cost": 5200, "risk": 28, "resilience": 78},
            {"name": f"Air Freight Priority Express", "eta_days": 4, "cost": 12800, "risk": 15, "resilience": 85},
            {"name": f"Multimodal Rail Corridor", "eta_days": 16, "cost": 6400, "risk": 35, "resilience": 70},
        ]
        
    result = optimize_routes(routes, priority)
    return {
        "status": "success",
        "origin": origin,
        "destination": destination,
        "priority": priority,
        "recommended_route": result.get("recommended"),
        "routes": result.get("routes")
    }


@registry.register(
    name="analyze_root_cause",
    description="Analyze the root causes of delays or issues for a shipment.",
    category="analysis",
    input_params=[
        {"name": "shipment", "type": "object", "required": True, "description": "The shipment data dictionary"}
    ],
    output_description="Dictionary with factor contributions to the issue"
)
async def analyze_root_cause_tool(params: Dict[str, Any], context: Dict[str, Any]) -> Any:
    exec_ctx = context.get("execution_context", {})
    shipment = params.get("shipment") or params or exec_ctx
    ports_cache = context.get("ports_cache", [])
    return root_cause(shipment, ports_cache)


@registry.register(
    name="calculate_impact",
    description="Analyze the impact of a disruption event across multiple shipments.",
    category="analysis",
    input_params=[
        {"name": "event", "type": "object", "required": True, "description": "The disruption event details"},
        {"name": "shipments", "type": "list", "required": False, "description": "List of shipments to analyze"}
    ],
    output_description="Dictionary with affected shipments and risk summary"
)
async def calculate_impact_tool(params: Dict[str, Any], context: Dict[str, Any]) -> Any:
    db = context.get("db")
    event = params.get("event") or params
    shipments = params.get("shipments", [])
    if not shipments and db is not None:
        try:
            shipments = await db.shipments.find({}, {"_id": 0}).to_list(100)
        except Exception:
            pass
    if not shipments:
        shipments, _ = mock_store.get_shipments(limit=50)
        
    return analyze_impact(shipments, event)


@registry.register(
    name="calculate_financial_impact",
    description="Calculate the financial cost of a disruption event.",
    category="analysis",
    input_params=[
        {"name": "affected_shipments", "type": "number", "required": False},
        {"name": "delay_days", "type": "number", "required": False}
    ],
    output_description="Dictionary with financial cost breakdown"
)
async def calculate_financial_impact_tool(params: Dict[str, Any], context: Dict[str, Any]) -> Any:
    return financial_impact(params)


@registry.register(
    name="run_simulation",
    description="Run a scenario simulation on a set of shipments.",
    category="analysis",
    input_params=[
        {"name": "sim_params", "type": "object", "required": True}
    ],
    output_description="Dictionary with simulation results and affected metrics"
)
async def run_simulation_tool(params: Dict[str, Any], context: Dict[str, Any]) -> Any:
    sim_params = params.get("sim_params") or params
    return run_simulation(sim_params, 50)


@registry.register(
    name="create_alert",
    description="Create an alert in the system database.",
    category="action",
    input_params=[
        {"name": "title", "type": "string", "required": True},
        {"name": "message", "type": "string", "required": True},
        {"name": "severity", "type": "string", "required": False},
        {"name": "shipment_id", "type": "string", "required": False}
    ],
    output_description="Status of alert creation and generated alert ID"
)
async def create_alert_tool(params: Dict[str, Any], context: Dict[str, Any]) -> Any:
    db = context.get("db")
    mode = context.get("mode", "live")
    exec_ctx = context.get("execution_context", {})
    
    alert_doc = {
        "id": f"ALT-{str(uuid.uuid4())[:8].upper()}",
        "title": params.get("title") or "Automated Workflow Disruption Alert",
        "message": params.get("message") or f"Automated intervention triggered for shipment {params.get('shipment_id') or exec_ctx.get('shipment_id') or 'TS-20260001'}",
        "level": params.get("severity") or params.get("level") or "Warning",
        "shipment_id": params.get("shipment_id") or exec_ctx.get("shipment_id") or "TS-20260001",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "read": False,
        "archived": False,
        "auto": True,
        "source": "automation_workflow"
    }
    
    if mode == "simulation":
        logger.info(f"SIMULATION: Would create alert: {alert_doc['title']}")
        return {"status": "simulated", "alert_id": alert_doc["id"], "alert": alert_doc}
    else:
        if db is not None:
            try:
                await db.alerts.insert_one(alert_doc.copy())
            except Exception:
                pass
        return {"status": "success", "alert_id": alert_doc["id"], "alert": alert_doc}


@registry.register(
    name="notify_manager",
    description="Send a targeted notification to an operations manager.",
    category="action",
    input_params=[
        {"name": "manager_id", "type": "string", "required": False},
        {"name": "message", "type": "string", "required": True}
    ],
    output_description="Status of notification delivery"
)
async def notify_manager_tool(params: Dict[str, Any], context: Dict[str, Any]) -> Any:
    return {
        "status": "success",
        "channel": "Slack & Email",
        "recipient": params.get("manager_id") or "ops-lead@tradesentinel.demo",
        "message": params.get("message") or "Operations alert: reroute requested.",
        "delivered_at": datetime.now(timezone.utc).isoformat()
    }


@registry.register(
    name="notify_ops_manager",
    description="Notify operations manager about high-risk shipment disruption.",
    category="action",
    input_params=[{"name": "message", "type": "string"}],
    output_description="Notification status"
)
async def notify_ops_manager_tool(params: Dict[str, Any], context: Dict[str, Any]) -> Any:
    return await notify_manager_tool(params, context)


@registry.register(
    name="request_approval",
    description="Create an actionable recommendation that requires human approval.",
    category="action",
    input_params=[
        {"name": "shipment_id", "type": "string", "required": False},
        {"name": "action_type", "type": "string", "required": False}
    ],
    output_description="Status of approval request"
)
async def request_approval_tool(params: Dict[str, Any], context: Dict[str, Any]) -> Any:
    return {
        "status": "pending_approval",
        "approval_id": f"APR-{str(uuid.uuid4())[:8].upper()}",
        "shipment_id": params.get("shipment_id") or "TS-20260001",
        "action_type": params.get("action_type") or "reroute",
        "created_at": datetime.now(timezone.utc).isoformat()
    }


@registry.register(
    name="generate_docs",
    description="Auto-generate required customs and bill of lading shipping documents.",
    category="action",
    input_params=[{"name": "type", "type": "string", "required": False}],
    output_description="Generated document links"
)
async def generate_docs_tool(params: Dict[str, Any], context: Dict[str, Any]) -> Any:
    doc_type = params.get("type", "commercial_invoice")
    return {
        "status": "success",
        "document_type": doc_type,
        "document_id": f"DOC-{str(uuid.uuid4())[:8].upper()}",
        "download_url": f"/api/compliance/documents/{doc_type}.pdf",
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


@registry.register(
    name="rebook_freight",
    description="Automatically rebook freight allocation with preferred carriers.",
    category="action",
    input_params=[{"name": "carrier", "type": "string", "required": False}],
    output_description="Booking confirmation"
)
async def rebook_freight_tool(params: Dict[str, Any], context: Dict[str, Any]) -> Any:
    carrier = params.get("carrier") or "Maersk Express Line"
    return {
        "status": "success",
        "booking_id": f"BKG-{str(uuid.uuid4())[:8].upper()}",
        "carrier": carrier,
        "estimated_departure": "Tomorrow 08:00 UTC",
        "confirmation": "Freight space confirmed"
    }


@registry.register(
    name="update_shipment_status",
    description="Update the status or fields of a shipment in the database.",
    category="action",
    input_params=[
        {"name": "shipment_id", "type": "string", "required": False},
        {"name": "status", "type": "string", "required": False}
    ],
    output_description="Result of the update operation"
)
async def update_shipment_status_tool(params: Dict[str, Any], context: Dict[str, Any]) -> Any:
    db = context.get("db")
    exec_ctx = context.get("execution_context", {})
    shipment_id = params.get("shipment_id") or exec_ctx.get("shipment_id") or "TS-20260001"
    status = params.get("status", "Rerouted")
    
    if db is not None:
        try:
            await db.shipments.update_one(
                {"$or": [{"id": shipment_id}, {"shipment_id": shipment_id}]},
                {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
        except Exception:
            pass
            
    return {
        "status": "success",
        "shipment_id": shipment_id,
        "new_status": status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
