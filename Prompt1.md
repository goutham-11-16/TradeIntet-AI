You are working on an existing project called **TradeSentinel**, a logistics intelligence platform.

I already have the complete source code. DO NOT rebuild the project from scratch and DO NOT replace existing functionality.

Your first task is to deeply inspect the entire existing codebase and understand how it currently works.

The target hackathon problem statement is:

**PS4 — AI-Powered Business Automation Copilot**

Problem:
SMBs and enterprises rely on repetitive workflows across sales, finance, HR, and customer support. Business users understand what they want automated but lack the technical expertise to create workflows.

Expected solution:

1. Accept workflow requirements in natural language
2. Identify triggers and conditions
3. Generate workflow logic
4. Recommend automation opportunities
5. Create executable/simulated workflows
6. Detect workflow conflicts
7. Provide workflow performance insights

Our chosen business domain is **Logistics**.

The existing TradeSentinel project already contains logistics intelligence such as shipment management, risk analysis, ETA prediction, route optimization, disruption analysis, recovery recommendations, simulations, alerts, analytics, financial impact analysis, and human approval/recovery functionality.

IMPORTANT:
The goal is to transform TradeSentinel into an **AI Business Automation Copilot for Logistics**, while preserving all existing working functionality.

Do the following first:

### 1. Codebase audit

Inspect:

* frontend architecture
* backend architecture
* APIs
* database/models
* existing logistics functions
* existing AI/ML functionality
* existing simulation functionality
* existing recovery functionality
* existing notifications
* existing analytics
* existing authentication
* existing integrations
* existing UI pages/components

Identify what can be reused as workflow tools.

### 2. Map existing functionality to PS4

Create a clear mapping:

Existing TradeSentinel functionality → PS4 requirement

For example:

* risk engine → workflow condition/tool
* ETA prediction → workflow condition
* route optimizer → workflow action
* simulation → workflow simulation engine
* recovery approval → human-in-the-loop action
* alerts → workflow notification action
* analytics → workflow performance insights

### 3. Identify missing components

Determine exactly what needs to be added for PS4.

Expected missing architecture should include, where appropriate:

* AI Copilot
* natural-language workflow parser
* workflow schema / DSL
* trigger extraction
* condition extraction
* action extraction
* workflow generator
* workflow validator
* workflow executor
* workflow simulator
* workflow conflict detector
* automation opportunity detector
* workflow analytics
* workflow optimizer
* audit trail
* human approval mechanism

Do not blindly create these if equivalent functionality already exists. Reuse existing code whenever possible.

### 4. Architecture proposal

Design the minimum architecture required to extend the current project.

The desired conceptual flow is:

User natural language
→ AI understanding
→ trigger/condition/action extraction
→ structured workflow
→ validation
→ conflict detection
→ simulation
→ execution
→ performance tracking
→ optimization

### 5. Existing code reuse

Explicitly identify the existing functions/APIs that can become workflow tools.

For example:

risk analysis
ETA prediction
route optimization
root cause analysis
impact analysis
financial impact
shipment lookup
customer lookup
alerts
notifications
recovery actions
simulation

Do not duplicate these functions.

### 6. Final output

Before changing code, provide:

A. Existing architecture summary
B. Existing useful modules
C. Missing PS4 features
D. Proposed architecture
E. Files that should be created
F. Files that should be modified
G. Existing files that should NOT be touched
H. Implementation order
I. Potential technical risks

DO NOT implement anything yet.

Wait for my next instruction.
