Now implement the **core AI workflow engine** identified in the previous analysis.

Do NOT rebuild TradeSentinel.

Do NOT remove existing features.

Do NOT create a separate disconnected application.

The new workflow system must integrate with the existing TradeSentinel backend and logistics intelligence.

## Goal

A business user should be able to type:

"Whenever a shipment becomes high risk, check the expected delay. If the delay is more than 2 days, find an alternative route. If the shipment value is above ₹10 lakh, ask the operations manager for approval before rerouting."

The system must convert this natural-language requirement into a structured executable workflow.

## Build these components

### 1. Workflow schema

Create a controlled workflow representation supporting:

* TRIGGER
* CONDITION
* ACTION
* DELAY
* BRANCH
* APPROVAL
* NOTIFICATION
* END

Use structured JSON/Pydantic models rather than allowing the LLM to directly execute arbitrary instructions.

Each workflow should contain:

* id
* name
* description
* trigger
* nodes
* edges
* conditions
* actions
* version
* status
* created_at
* updated_at

### 2. Natural-language workflow parser

Create an AI service that converts user requirements into the workflow schema.

It must extract:

* trigger
* entities
* conditions
* thresholds
* actions
* branches
* delays
* approvals

Example:

User:
"When shipment risk exceeds 70 and expected delay is more than 2 days, optimize the route. If shipment value exceeds ₹10 lakh, require manager approval."

Output should represent:

TRIGGER:
shipment risk updated

CONDITION:
risk_score > 70

CONDITION:
expected_delay > 2 days

ACTION:
route_optimization

CONDITION:
shipment_value > 1000000

ACTION:
manager_approval

ACTION:
reroute

### 3. Workflow validator

Before a workflow can execute, validate:

* missing trigger
* invalid condition
* invalid action
* unreachable nodes
* missing branches
* malformed expressions
* missing required parameters
* circular dependency
* unsupported action

Return clear validation errors.

### 4. Tool registry

Create a reusable tool registry.

Expose existing TradeSentinel functionality as controlled tools.

Examples:

* get_shipment
* get_customer
* calculate_risk
* predict_eta
* predict_customs_delay
* optimize_route
* analyze_root_cause
* calculate_impact
* calculate_financial_impact
* create_alert
* notify_manager
* request_approval
* run_simulation

Reuse existing implementations wherever possible.

### 5. Workflow executor

Build an execution engine that processes the workflow graph.

It should:

1. Load workflow
2. Evaluate trigger
3. Evaluate conditions
4. Execute actions
5. Handle branches
6. Pause for approval when required
7. Record every execution step
8. Continue after approval
9. Mark workflow success/failure

Every execution must create an execution log.

### 6. Simulation mode

Create two modes:

SIMULATION
REAL EXECUTION

Simulation must NEVER send real notifications or modify production data.

Example:

"Simulate this workflow against the current shipments."

Show:

* shipments evaluated
* trigger matches
* conditions passed/failed
* actions that would execute
* approvals required
* estimated impact
* estimated time saved

### 7. Audit trail

Record:

* workflow
* execution ID
* node
* tool
* input
* output
* timestamp
* status
* error
* approval status

### 8. API endpoints

Add clean APIs for:

POST /workflows/generate
POST /workflows/validate
POST /workflows/simulate
POST /workflows/execute
GET /workflows
GET /workflows/{id}
GET /workflows/{id}/runs
GET /workflow-runs/{id}

Adapt the endpoint naming to the existing project's architecture if necessary.

### 9. Testing

Create tests for:

* simple workflow
* condition workflow
* branching workflow
* approval workflow
* invalid workflow
* failed action
* simulation mode
* workflow execution logging

At the end, run the existing project tests and the new workflow tests.

IMPORTANT:
Keep all existing TradeSentinel functionality working.
