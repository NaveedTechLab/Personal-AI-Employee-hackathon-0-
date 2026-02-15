# Tasks: Phase 2 - Functional Assistant (Silver Tier)

**Feature**: Phase 2 - Functional Assistant (Silver Tier)
**Branch**: 001-functional-assistant
**Created**: 2026-01-14
**Based on**: spec.md, plan.md, data-model.md

## Implementation Strategy

This implementation will follow an incremental delivery approach focusing on delivering a working system early with the core functionality. The strategy is:
1. **MVP First**: Complete User Story 1 (Multi-Source Monitoring with Human Approval) as the minimal viable product
2. **Incremental Delivery**: Add subsequent user stories in priority order
3. **Parallel Execution**: Where possible, tasks are marked with [P] for parallel execution
4. **Independent Testing**: Each user story can be tested independently

## Phase 1: Setup Tasks

- [X] T001 Create /phase-2/ directory structure
- [X] T002 Create /phase-2/vault/ directory with subdirectories: /Pending_Approval, /Approved, /Rejected
- [X] T003 Create /phase-2/plans/ directory for Plan.md files
- [X] T004 Create /phase-2/config/ directory for configuration files
- [X] T005 Initialize requirements.txt with dependencies: imaplib, watchfiles, fastmcp, schedule, playwright, obsidian
- [X] T006 Create base configuration file at /phase-2/config.py

## Phase 2: Foundational Tasks

- [X] T010 [P] Create vault_manager.py to handle file system operations for the vault
- [X] T011 [P] Create base watcher class template in /phase-2/base_watcher.py
- [X] T012 [P] Create approval_workflow.py to handle approval processes
- [X] T013 [P] Create schema validation for .md files in /phase-2/schema_validator.py
- [X] T014 [P] Create utility functions in /phase-2/utils.py

## Phase 3: User Story 1 - Multi-Source Monitoring with Human Approval (Priority: P1)

**Goal**: Enable monitoring of multiple external sources (Gmail and Filesystem) with human approval workflow for sensitive actions.

**Independent Test**: Can be fully tested by configuring two watchers (email and filesystem), sending test triggers to both sources, verifying that structured .md files are created in /Needs_Action, and confirming that actions requiring approval are properly routed through the approval workflow.

**Tasks**:

- [X] T020 [P] [US1] Enhance email_watcher.py from Phase 1 to output consistent schema
- [X] T021 [P] [US1] Create filesystem_watcher.py using watchfiles library
- [X] T022 [P] [US1] Verify both watchers can run without conflict
- [X] T023 [US1] Create test to verify no duplicate or overwritten files
- [X] T024 [P] [US1] Validate that both watchers emit .md files into /Needs_Action with consistent schema
- [X] T025 [P] [US1] Create MCP server integration module in /phase-2/mcp_client.py
- [X] T026 [US1] Create test triggers for both watchers to verify functionality
- [X] T027 [US1] Implement approval request file creation in /Pending_Approval
- [X] T028 [US1] Verify Claude pauses execution until human approval occurs
- [X] T029 [US1] Test that external actions execute via MCP server after approval

## Phase 4: User Story 2 - Automated Planning and Execution (Priority: P2)

**Goal**: Enable Claude Code to generate structured Plan.md files that define objectives, contain ordered checklist steps, and explicitly mark steps requiring approval.

**Independent Test**: Can be tested by providing a complex task to Claude, verifying that it generates a Plan.md file with clear objectives, ordered steps, and properly marked approval requirements, then confirming execution follows the planned sequence.

**Tasks**:

- [X] T030 [P] [US2] Create plan_generator.py to generate structured Plan.md files
- [X] T031 [P] [US2] Implement objective definition in Plan.md files
- [X] T032 [P] [US2] Create ordered checklist steps in Plan.md format
- [X] T033 [US2] Implement approval marker identification in Plan.md files
- [X] T034 [US2] Validate Plan.md files are written to /phase-2/plans/ directory
- [X] T035 [US2] Test Claude's ability to create Plan.md from /Needs_Action items
- [X] T036 [US2] Verify Plan.md contains clear objectives and ordered steps
- [X] T037 [US2] Confirm Plan.md explicitly marks steps requiring approval
- [X] T038 [US2] Test execution flow respects approval gates in Plan.md

## Phase 5: User Story 3 - Scheduled Recurring Execution (Priority: P3)

**Goal**: Implement periodic execution based on schedule (cron/Task Scheduler) to check for new items and process existing ones, without creating background autonomous loops.

**Independent Test**: Can be tested by setting up a schedule, verifying that Claude execution is triggered at scheduled intervals, and confirming that the system processes items without creating autonomous background processes.

**Tasks**:

- [X] T040 [P] [US3] Create scheduler.py using schedule library
- [X] T041 [P] [US3] Configure scheduled trigger intervals
- [X] T042 [US3] Verify scheduler only triggers Claude execution
- [X] T043 [US3] Confirm system returns to idle state after execution
- [X] T044 [US3] Test that no autonomous loops are created
- [X] T045 [US3] Verify scheduled execution processes items appropriately
- [X] T046 [US3] Test overlap handling between scheduled and manual execution

## Phase 6: Cross-Cutting and Integration Tasks

- [X] T050 [P] Create end-to-end test for watcher input → Plan generation → Approval → MCP action
- [X] T051 [P] Validate all sensitive actions require human approval
- [X] T052 [P] Confirm only one MCP server is used as specified
- [X] T053 [P] Verify system remains non-autonomous during all operations
- [X] T054 [P] Create comprehensive test for file-based approval workflow
- [X] T055 [P] Validate Claude Code read/write access to all required directories
- [X] T056 [P] Test all state transitions in approval workflow
- [X] T057 [P] Verify all edge cases from spec are handled appropriately
- [X] T058 [P] Create manual approval flow validation test
- [X] T059 [P] Execute end-to-end Silver Tier dry run scenario

## Dependencies

- User Story 1 (P1) must be completed before User Story 2 (P2) can begin effectively
- User Story 2 (P2) provides Plan.md capability needed for User Story 3 (P3) scheduling
- User Story 3 (P3) integrates with all previous functionality

## Parallel Execution Opportunities

- Watcher implementations can run in parallel (T020, T021)
- Utility and foundational modules can be developed in parallel (T010-T014)
- Different aspects of Plan.md generation can run in parallel (T030-T032)
- MCP integration and approval workflow can develop in parallel (T025, T012)