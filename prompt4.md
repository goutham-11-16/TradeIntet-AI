Now implement the **Workflow Conflict Detection Engine**.

This is a major PS4 feature and should be treated as a first-class backend capability.

The system must analyze all active workflows and detect conflicts before deployment and during workflow execution.

## Detect at least these conflict types

### 1. Duplicate workflows

Example:

Workflow A:
Shipment delayed > 2 hours → Notify customer

Workflow B:
Shipment delayed > 2 hours → Notify customer

Detect duplicate/near-duplicate logic.

### 2. Trigger collision

Multiple workflows activate from the same event and affect the same entity/action.

### 3. Contradictory actions

Example:

Workflow A:
Vehicle breakdown → Assign replacement vehicle

Workflow B:
Vehicle breakdown → Cancel shipment

Flag as contradictory.

### 4. Circular workflows

Example:

A → B → C → A

Detect graph cycles.

### 5. Infinite loops

Example:

Shipment updated → update shipment → shipment updated → ...

Detect self-triggering workflows.

### 6. Approval bypass

Example:

Workflow A:
High-value shipment → Manager approval → Reroute

Workflow B:
High-risk shipment → Reroute automatically

If a shipment can satisfy both conditions, flag that Workflow B may bypass the approval requirement.

### 7. Race conditions

Two workflows simultaneously modify the same shipment/order/customer state.

### 8. Impossible conditions

Example:

risk_score > 90 AND risk_score < 40

Detect logically impossible conditions.

### 9. Unreachable nodes

Detect workflow branches that can never be executed.

### 10. Conflicting state transitions

Example:

Shipment status:
DELIVERED → CANCELLED

when that transition is invalid according to business rules.

## Conflict severity

Classify as:

CRITICAL
HIGH
MEDIUM
LOW
INFO

## Conflict result

Every conflict must contain:

* conflict type
* workflows involved
* affected node
* explanation
* potential impact
* confidence
* recommended fix

Example:

CRITICAL

"Potential infinite loop detected between Workflow 4 and Workflow 7."

## UI integration

The Conflict Center should allow:

[View Workflow]

[Fix Automatically]

[Ignore]

[Disable Workflow]

[Compare Workflows]

Do not automatically modify an active workflow without user confirmation.

## Testing

Create test cases for every conflict type.

Make the conflict engine deterministic wherever possible.

Use the AI only where semantic interpretation is useful. Use normal graph/rule algorithms for deterministic conflict detection.
