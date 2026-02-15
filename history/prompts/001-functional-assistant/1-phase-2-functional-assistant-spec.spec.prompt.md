---
id: 1
title: phase-2-functional-assistant-spec
stage: spec
date_iso: 2026-01-14
surface: agent
model: claude-sonnet-4-5-20250929
feature: 001-functional-assistant
branch: 001-functional-assistant
user: claude
command: /sp.specify
labels:
  - specification
  - silver-tier
  - functional-assistant
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files_yaml: |
  - specs/001-functional-assistant/spec.md
  - specs/001-functional-assistant/checklists/requirements.md
tests_yaml: |
  - spec validation
  - requirement completeness check
prompt_text: |
  Phase: Phase 2 — Functional Assistant (Silver Tier)

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

  Specification is sufficient to plan without interpretation
response_text: |
  Created complete specification for Phase 2 - Functional Assistant (Silver Tier) including:
  - User scenarios with priorities (P1-P3)
  - Functional requirements (FR-001 to FR-014)
  - Key entities definitions
  - Success criteria (SC-001 to SC-008)
  - Edge cases consideration
  - Quality validation checklist
outcome: |
  Specification successfully created for Silver Tier with multiple watchers,
  MCP server integration, approval workflow, and planning capabilities.
evaluation: |
  The specification is complete, unambiguous, and ready for planning phase.
  All Silver Tier requirements are clearly defined with measurable outcomes.
---