Now build the frontend experience for the new **AI Business Automation Copilot** using the existing TradeSentinel design system.

Do not redesign the entire existing application.

Integrate the new functionality naturally into the existing navigation and UI.

## 1. Add AI Copilot

Create a page called:

**Automation Copilot**

The primary interface should allow the user to describe a workflow in natural language.

Example:

"Whenever a shipment becomes high risk, check the expected delay. If it exceeds 2 days, find an alternative route. If the shipment is worth more than ₹10 lakh, request manager approval."

Provide:

[ Generate Workflow ]

After generation, show:

* detected trigger
* detected conditions
* detected actions
* entities
* assumptions
* warnings

## 2. Workflow Studio

Create a visual workflow editor using the technology already present in the project.

If no workflow visualization exists, use React Flow or an equivalent stable library.

Nodes should visually represent:

🟢 Trigger
🔵 Condition
🟣 Action
🟠 Approval
🟡 Delay
🔴 Error
⚫ End

Users should be able to inspect each node.

## 3. AI explanation

For every generated workflow show:

"Why did AI create this?"

Example:

Trigger:
Shipment risk updated

Reason:
Risk changes can indicate a new operational threat.

Condition:
Risk > 70

Reason:
This matches the configured critical-risk threshold.

## 4. Workflow simulation

Add:

[ Run Simulation ]

Show an execution animation/timeline.

Example:

✓ Trigger detected
✓ 83 shipments matched
✓ Risk condition passed for 47
✓ Route optimization executed for 47
⚠ 12 require approval
✓ 35 can be automatically processed

Show estimated:

* delay reduction
* cost impact
* shipments affected
* manual work avoided

## 5. Workflow execution

Allow:

[ Execute Workflow ]

Before executing potentially risky actions, display approval requirements.

Never hide high-risk actions from the user.

## 6. Automation Opportunities

Create:

**Automation Opportunities**

The page should show AI-discovered repetitive logistics processes.

Example:

"Shipment delay escalation is performed manually 184 times per month."

Show:

* detected pattern
* frequency
* estimated manual effort
* estimated time savings
* suggested workflow
* confidence
* [Create Workflow]

## 7. Conflict Center

Create:

**Workflow Conflicts**

Display:

* duplicate workflows
* contradictory actions
* trigger collisions
* circular workflows
* unreachable conditions
* race conditions
* approval bypasses

Each conflict should show:

WHAT
WHY
IMPACT
RECOMMENDATION

Example:

"Workflow A automatically reroutes high-risk shipments, while Workflow B requires manager approval for shipments above ₹10 lakh. Workflow A may bypass Workflow B."

## 8. Workflow Analytics

Create:

**Automation Insights**

Show:

* total executions
* success rate
* failure rate
* average execution time
* manual tasks avoided
* estimated hours saved
* estimated financial impact
* approval frequency
* most-used workflows
* bottlenecks

Include AI-generated recommendations.

Example:

"63% of execution delays occur at the manager approval step."

## 9. Existing TradeSentinel integration

Use existing:

* shipment data
* risk data
* route data
* simulation data
* recovery data
* analytics
* alerts
* existing UI components

Do not create duplicate mock systems if real project data already exists.

## 10. UX quality

The UI must feel like a serious enterprise product.

Prioritize:

* clean dashboard
* clear hierarchy
* responsive design
* loading states
* empty states
* error handling
* execution progress
* confirmation dialogs
* approval dialogs
* explainability

Do not fill the UI with meaningless cards.

Every displayed metric should come from real backend data or clearly labeled simulation data.
