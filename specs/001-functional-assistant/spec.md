# Feature Specification: Phase 2 - Functional Assistant (Silver Tier)

**Feature Branch**: `001-functional-assistant`
**Created**: 2026-01-14
**Status**: Draft
**Input**: User description: "Phase: Phase 2 — Functional Assistant (Silver Tier)

Scope (STRICT):

Limit all work to /phase-2/

Follow the approved Project Constitution

Build strictly on top of completed Phase 1 outputs

Implement Silver Tier requirements only

Objectives:

Introduce multiple Watchers (minimum two)

Enable Claude Code to generate structured Plan.md files

Introduce one MCP server for real external action

Implement Human-in-the-Loop (HITL) approval workflow

Enable basic scheduling for recurring execution

In-Scope Deliverables:

1. Watchers (Perception Layer)

Minimum of two Watchers (e.g., Gmail + WhatsApp OR Gmail + Filesystem)

Each watcher must:

Monitor its source

Emit structured .md files into /Needs_Action

Follow a consistent schema

Watchers must not take actions directly

2. Planning Output (Reasoning Layer)

Claude Code must generate Plan.md files that:

Define objectives

Contain ordered checklist steps

Explicitly mark steps requiring approval

Plans must be written to a dedicated plans location (as specified)

3. MCP-Based Action (Action Layer)

Exactly one MCP server introduced

MCP server must support a single action type (e.g., send email)

MCP usage must be:

Explicit

Logged

Approval-gated

4. Human-in-the-Loop Approval Workflow

File-based approval mechanism:

/Pending_Approval

/Approved

/Rejected

Claude must:

Generate approval request files

Pause action until human approval occurs

No auto-approval allowed

5. Scheduling

Basic scheduled execution:

Cron (Mac/Linux) or Task Scheduler (Windows)

Scheduling triggers Claude execution only

No background autonomous loops

Out of Scope (Explicit):

Business audits

CEO briefings

Financial actions

Error recovery systems

Watchdog/process supervisors

Multiple MCP servers

Cross-domain autonomy

Constraints:

Sensitive actions must always require approval

No direct external actions without MCP

No deviation from Silver Tier scope

No code or task breakdown in this spec

Exit Criteria:

Phase 2 behavior is fully specified and unambiguous

HITL safety is enforced by design

Specification is sufficient to plan without interpretation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Multi-Source Monitoring with Human Approval (Priority: P1)

User needs to monitor multiple external sources (Gmail and WhatsApp/Filesystem) for incoming items that require attention. The system must detect relevant triggers from these sources and create structured action items that go through a human approval process before any external actions are taken.

**Why this priority**: This is the core functionality of the Silver Tier - enabling the assistant to perceive inputs from multiple sources and handle them with appropriate approval workflows before taking any external actions.

**Independent Test**: Can be fully tested by configuring two watchers (e.g., Gmail and WhatsApp), sending test triggers to both sources, verifying that structured .md files are created in /Needs_Action, and confirming that actions requiring approval are properly routed through the approval workflow.

**Acceptance Scenarios**:

1. **Given** user has configured Gmail and WhatsApp watchers, **When** relevant triggers arrive in either source, **Then** structured .md files are created in /Needs_Action with consistent schema
2. **Given** action items requiring external execution exist, **When** Claude generates approval requests, **Then** files are placed in /Pending_Approval and system waits for human approval before proceeding
3. **Given** an item in /Pending_Approval, **When** human approves it, **Then** the item moves to /Approved and external action is executed via MCP server

---

### User Story 2 - Automated Planning and Execution (Priority: P2)

User wants Claude Code to generate structured Plan.md files that define objectives, contain ordered checklist steps, and explicitly mark steps requiring approval. The system should execute these plans while respecting approval gates.

**Why this priority**: This enables intelligent planning and execution capabilities that differentiate Silver Tier from Bronze Tier, allowing for more complex multi-step workflows.

**Independent Test**: Can be tested by providing a complex task to Claude, verifying that it generates a Plan.md file with clear objectives, ordered steps, and properly marked approval requirements, then confirming execution follows the planned sequence.

**Acceptance Scenarios**:

1. **Given** a complex task requiring multiple steps, **When** Claude processes the request, **Then** a structured Plan.md file is generated with objectives and ordered checklist steps
2. **Given** a Plan.md with mixed approval-required and approval-not-required steps, **When** execution begins, **Then** steps proceed automatically until reaching an approval gate where execution pauses

---

### User Story 3 - Scheduled Recurring Execution (Priority: P3)

User wants the system to execute periodically based on a schedule (cron/Task Scheduler) to check for new items and process existing ones, without creating background autonomous loops.

**Why this priority**: This adds automation capabilities while maintaining human oversight, enabling the system to operate consistently without constant manual intervention.

**Independent Test**: Can be tested by setting up a schedule, verifying that Claude execution is triggered at scheduled intervals, and confirming that the system processes items without creating autonomous background processes.

**Acceptance Scenarios**:

1. **Given** a configured schedule, **When** scheduled time arrives, **Then** Claude execution is triggered to process items in the system
2. **Given** scheduled execution, **When** processing completes, **Then** system returns to idle state without creating background loops

---

### Edge Cases

- What happens when multiple watchers detect triggers simultaneously and create many action items rapidly?
- How does the system handle approval requests when the MCP server is unavailable?
- What occurs when scheduled execution overlaps with manual execution?
- How does the system handle malformed or incomplete Plan.md files?
- What happens when a watcher encounters a connection error to its monitored source?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support at least two different watchers (e.g., Gmail + WhatsApp OR Gmail + Filesystem) monitoring their respective sources
- **FR-002**: Each watcher MUST emit structured .md files into /Needs_Action following a consistent schema
- **FR-003**: Watchers MUST NOT take actions directly - only create action items for human review
- **FR-004**: Claude Code MUST generate Plan.md files that define clear objectives and contain ordered checklist steps
- **FR-005**: Plan.md files MUST explicitly mark which steps require human approval before execution
- **FR-006**: System MUST include exactly one MCP server that supports a single action type (e.g., send email)
- **FR-007**: MCP usage MUST be explicit, logged, and approval-gated before execution
- **FR-008**: System MUST implement file-based approval workflow with /Pending_Approval, /Approved, and /Rejected directories
- **FR-009**: Claude MUST generate approval request files and pause execution until human approval occurs
- **FR-010**: System MUST support basic scheduling using Cron (Mac/Linux) or Task Scheduler (Windows)
- **FR-011**: Scheduling MUST trigger Claude execution only and NOT create background autonomous loops
- **FR-012**: All sensitive actions MUST require human approval before execution via MCP server
- **FR-013**: System MUST NOT perform direct external actions without MCP server mediation
- **FR-014**: All functionality MUST be limited to Silver Tier scope without deviation

### Key Entities

- **Watcher**: A monitoring component that observes external sources (Gmail, WhatsApp, Filesystem) and creates structured action items in /Needs_Action
- **Plan.md**: A structured document containing objectives, ordered steps, and approval markers that guide execution workflows
- **MCP Server**: An external action gateway that enables controlled execution of sensitive operations with explicit approval and logging
- **Approval Workflow**: A file-based system managing items through /Pending_Approval, /Approved, and /Rejected states

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System successfully monitors at least two different sources simultaneously without conflicts
- **SC-002**: At least 95% of watcher triggers result in properly structured .md files in /Needs_Action with consistent schema
- **SC-003**: All external actions are executed through MCP server with proper approval gating and logging
- **SC-004**: Plan.md files contain clear objectives, ordered steps, and explicit approval markers as required
- **SC-005**: Approval workflow correctly manages all items through the required file-based directory system
- **SC-006**: Scheduling system triggers Claude execution at specified intervals without creating autonomous loops
- **SC-007**: 100% of sensitive actions require human approval before execution via MCP server
- **SC-008**: System operates within Silver Tier scope without implementing out-of-scope features
