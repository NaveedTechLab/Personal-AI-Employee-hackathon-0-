---
id: 3
title: phase-2-tasks
stage: tasks
date_iso: 2026-01-14
surface: agent
model: claude-sonnet-4-5-20250929
feature: 001-functional-assistant
branch: 001-functional-assistant
user: claude
command: /sp.tasks
labels:
  - tasks
  - silver-tier
  - functional-assistant
  - implementation
links:
  spec: specs/001-functional-assistant/spec.md
  plan: specs/001-functional-assistant/plan.md
  ticket: null
  adr: null
  pr: null
files_yaml: |
  - specs/001-functional-assistant/tasks.md
tests_yaml: |
  - task completeness validation
  - dependency mapping
  - parallel execution identification
prompt_text: |
  Phase: Phase 2 — Functional Assistant (Silver Tier)

  Input Contract:

  Tasks are derived strictly from the approved Phase 2 Plan

  No new requirements, no scope expansion

  All tasks apply only to /phase-2/

  Phase 1 outputs are dependencies and must not be modified

  Task Design Rules:

  Tasks must be small, atomic, and verifiable

  Each task must have a clear completion condition

  No task may introduce future-phase functionality

  No task may contain code or pseudo-code

  TASK LIST

  Add Second Watcher

  Select and confirm the second watcher type

  Verify it emits .md files into /Needs_Action

  Confirm schema consistency with existing watcher output

  Validate Multi-Watcher Coexistence

  Confirm both watchers can run without conflict

  Verify no duplicate or overwritten files

  Define Plans Folder

  Create and verify the dedicated plans location

  Confirm Claude Code read/write access

  Enable Plan.md Generation

  Validate Claude creates Plan.md files from /Needs_Action

  Confirm checklist format and objective section exist

  Mark Approval-Required Steps

  Validate Plan.md clearly labels steps requiring approval

  Confirm no implicit or automatic approval

  Introduce Approval Folders

  Create /Pending_Approval

  Create /Approved

  Create /Rejected

  Approval Request File Creation

  Validate Claude generates approval request files

  Confirm correct placement in /Pending_Approval

  Human Approval Flow Validation

  Manually move one file to /Approved

  Manually move one file to /Rejected

  Confirm Claude responds correctly to each case

  Integrate Single MCP Server

  Connect exactly one MCP server

  Verify Claude can invoke it only after approval

  MCP Action Verification

  Execute one approved MCP action

  Confirm no action occurs without approval

  Scheduling Setup

  Configure one scheduled trigger

  Confirm it only triggers Claude execution

  Verify no autonomous loops are created

  End-to-End Silver Tier Dry Run

  Trigger watcher input

  Generate Plan.md

  Require approval

  Execute approved MCP action

  Manually close the workflow

  Exit Criteria:

  All tasks completed and manually verified

  HITL enforced at all sensitive steps

  Only one MCP server used

  System remains non-autonomous
response_text: |
  Created comprehensive task breakdown for Phase 2 Functional Assistant (Silver Tier) with:
  - 59 specific, atomic tasks organized across 6 phases
  - Phase 1: Setup tasks for directory structure and dependencies
  - Phase 2: Foundational tasks for core components
  - Phase 3: User Story 1 (Multi-Source Monitoring with Human Approval) - Priority 1
  - Phase 4: User Story 2 (Automated Planning and Execution) - Priority 2
  - Phase 5: User Story 3 (Scheduled Recurring Execution) - Priority 3
  - Phase 6: Cross-cutting integration and validation tasks
  - Each task follows the required checklist format with IDs, labels, and file paths
  - Parallel execution opportunities identified with [P] markers
  - Dependencies mapped between user stories
  - Independent test criteria for each user story
  - All tasks derived strictly from approved Phase 2 Plan with no scope expansion
outcome: |
  Complete task breakdown created with 59 atomic tasks that map directly to Phase 2 requirements.
  Tasks are organized by user story priority and follow the required format.
  Ready for implementation phase with clear completion criteria.
evaluation: |
  The task breakdown successfully translates the Phase 2 plan into specific,
  verifiable tasks that maintain HITL safety and follow all constitutional requirements.
---