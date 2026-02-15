---
id: 4
title: phase-2-implementation
stage: tasks
date_iso: 2026-01-14
surface: agent
model: claude-sonnet-4-5-20250929
feature: 001-functional-assistant
branch: 001-functional-assistant
user: claude
command: /sp.implement
labels:
  - implementation
  - silver-tier
  - functional-assistant
  - watchers
  - mcp
  - approval-workflow
links:
  spec: specs/001-functional-assistant/spec.md
  plan: specs/001-functional-assistant/plan.md
  tasks: specs/001-functional-assistant/tasks.md
  ticket: null
  adr: null
  pr: null
files_yaml: |
  - phase-2/config.py
  - phase-2/vault_manager.py
  - phase-2/base_watcher.py
  - phase-2/approval_workflow.py
  - phase-2/schema_validator.py
  - phase-2/utils.py
  - phase-2/email_watcher.py
  - phase-2/filesystem_watcher.py
  - phase-2/mcp_client.py
  - phase-2/plan_generator.py
  - phase-2/scheduler.py
  - phase-2/coordinator.py
  - phase-2/main.py
  - phase-2/test_e2e.py
  - phase-2/requirements.txt
tests_yaml: |
  - end-to-end functionality test
  - multi-watcher coexistence test
  - approval workflow validation
  - plan generation verification
  - mcp integration test
  - scheduling functionality test
prompt_text: |
  Phase: Phase 2 — Functional Assistant (Silver Tier)

  Authority:

  Implement only the approved Phase 2 tasks

  No scope expansion

  No future-phase preparation

  Do not modify Phase 1 artifacts except where explicitly required

  Do not touch SpecifyPlus internal folders

  Implementation Scope (STRICT):

  Second Watcher Implementation

  Add and validate the selected second watcher

  Ensure consistent .md output into /Needs_Action

  Multi-Watcher Validation

  Run both watchers concurrently

  Confirm stable coexistence and file integrity

  Plans Infrastructure

  Create plans directory

  Enable Claude Code to write Plan.md files

  Plan Generation Logic

  Ensure plans include:

  Objective

  Ordered checklist

  Explicit approval markers

  Approval Folder Setup

  Create:

  /Pending_Approval

  /Approved

  /Rejected

  Approval Request Handling

  Generate approval request files

  Enforce pause until human action

  Single MCP Server Integration

  Connect exactly one MCP server

  Restrict its capabilities to approved action only

  Approval-Gated MCP Execution

  Verify no MCP action runs without approval

  Execute exactly one approved action

  Scheduling

  Configure one scheduled trigger

  Ensure it only triggers Claude execution

  End-to-End Validation

  Watcher → Plan → Approval → MCP Action → Manual Closure

  Hard Stops:

  No additional MCP servers

  No automation loops

  No business audits

  No error recovery or watchdogs

  No financial actions

  Completion Conditions:

  All Phase 2 tasks completed and verified

  HITL enforced without exception

  Silver Tier functionality achieved

  System remains semi-autonomous only
response_text: |
  Successfully implemented Phase 2 - Functional Assistant (Silver Tier) with:

  - Created complete directory structure (/phase-2/, vault subdirs, plans, config)
  - Implemented dual watcher system (enhanced email_watcher + new filesystem_watcher)
  - Created base_watcher.py with abstract interface for all watchers
  - Implemented approval workflow with file-based system (/Pending_Approval, /Approved, /Rejected)
  - Created MCP client for external action integration with approval gating
  - Implemented plan_generator.py for structured Plan.md creation with approval markers
  - Created scheduler.py for periodic execution without autonomous loops
  - Built vault_manager.py for file system operations in Obsidian vault
  - Created schema_validator.py for consistent .md file validation
  - Added utility functions in utils.py
  - Built coordinator.py to tie all components together
  - Created main.py as entry point with comprehensive demo/test functionality
  - All 59 tasks completed successfully across all 6 phases
  - End-to-end validation completed successfully
  - Human-in-the-loop (HITL) enforced at all sensitive steps
  - Only one MCP server used as specified
  - System remains non-autonomous with manual closure required
outcome: |
  Phase 2 Silver Tier functionality fully implemented with multi-source monitoring,
  plan generation, approval workflow, MCP integration, and scheduling. All tasks
  completed and verified, HITL enforced, and system operates semi-autonomously as required.
evaluation: |
  The implementation successfully delivers all Phase 2 requirements while maintaining
  safety controls and human oversight. The modular architecture allows for easy maintenance
  and follows the specified constraints without scope creep.
---