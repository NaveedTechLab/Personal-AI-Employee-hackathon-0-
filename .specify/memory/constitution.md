<!--
Sync Impact Report:
- Version change: N/A (initial version) → 1.0.0
- Modified principles: N/A (new constitution)
- Added sections: Core Principles, Global Governance Rules, Project Structure, Phase Definitions, Phase Execution Rules, Safety & Control Enforcement, Prohibitions
- Removed sections: N/A
- Templates requiring updates: ⚠ pending (.specify/templates/plan-template.md, .specify/templates/spec-template.md, .specify/templates/tasks-template.md)
- Follow-up TODOs: None
-->
# Personal AI Employee (Digital FTE) — Hackathon 0 Constitution

## Core Principles

### Global Governance Rules
This constitution is created once and only once for the entire project. This constitution is immutable after approval. All future work must comply with this constitution and the hackathon document. Specs are contracts; plans and tasks must not exceed approved specs. Work must proceed one phase at a time. No phase may start before the previous phase is explicitly closed. No steps (spec → plan → tasks → implement) may be skipped or merged. SpecifyPlus internal folders, metadata, and system files must never be modified. All AI functionality must be implemented as Agent Skills, not ad-hoc scripts. No requirements may be invented beyond the hackathon document.

### Project Structure (Enforced)
Root contains three phase directories: /phase-1/, /phase-2/, /phase-3/. Shared resources include Obsidian Vault (local, markdown-based), MCP servers (external processes), and Claude Code runtime. Each phase folder may only contain artifacts relevant to that phase. Shared resources are referenced but not modified by specs unless explicitly allowed.

### Phase 1 - Foundation (Bronze Tier)
Scope includes Obsidian vault structure and core markdown files, single working Watcher, Claude Code read/write integration, and basic folders: Inbox / Needs_Action / Done. Manual triggering and validation are required. Constraints: No MCP-based external actions and no automation without human review.

### Phase 2 - Functional Assistant (Silver Tier)
Scope includes multiple Watchers (e.g., Gmail + WhatsApp), Plan.md generation by Claude, at least one MCP server for action, human-in-the-loop approval workflow, and scheduling via cron or task scheduler. Constraints: Sensitive actions must require approval and external actions limited to defined MCP capabilities.

### Phase 3 - Autonomous Employee (Gold Tier)
Scope includes cross-domain integration (personal + business), multiple MCP servers, weekly business audit and CEO briefing, error handling, recovery, and audit logging, full documentation and lessons learned. Constraints: Strict permission boundaries and comprehensive logging and safety enforcement.

### Phase Execution Rules
For each phase: /sp.specify must target only that phase's folder. /sp.plan must be derived strictly from the approved spec. /sp.tasks must be small, verifiable, and non-expansive. /sp.implement must implement only approved tasks. Phase completion requires explicit user confirmation.

### Safety & Control Enforcement
Human-in-the-loop is mandatory for sensitive actions. Credentials must never be stored in plaintext or vault files. DRY_RUN and DEV_MODE must be supported where applicable. All actions must generate audit logs. Failures must degrade gracefully without silent execution.

### Prohibitions
No auto-starting next phases, no re-creating or altering this constitution, no direct implementation without tasks, no touching SpecifyPlus internal architecture, no scope expansion beyond the hackathon document.

## Global Governance Rules

This constitution is created once and only once for the entire project.

This constitution is immutable after approval.

All future work must comply with this constitution and the hackathon document.

Specs are contracts; plans and tasks must not exceed approved specs.

Work must proceed one phase at a time.

No phase may start before the previous phase is explicitly closed.

No steps (spec → plan → tasks → implement) may be skipped or merged.

SpecifyPlus internal folders, metadata, and system files must never be modified.

All AI functionality must be implemented as Agent Skills, not ad-hoc scripts.

No requirements may be invented beyond the hackathon document.

## Project Structure (Enforced)

Root:

/phase-1/

/phase-2/

/phase-3/

Shared (referenced but not modified by specs unless explicitly allowed):

Obsidian Vault (local, markdown-based)

MCP servers (external processes)

Claude Code runtime

Each phase folder may only contain artifacts relevant to that phase.

## Phase Definitions

### Phase 1 — Foundation (Bronze Tier)
Scope:

Obsidian vault structure and core markdown files

Single working Watcher

Claude Code read/write integration

Basic folders: Inbox / Needs_Action / Done

Manual triggering and validation
Constraints:

No MCP-based external actions

No automation without human review

### Phase 2 — Functional Assistant (Silver Tier)
Scope:

Multiple Watchers (e.g., Gmail + WhatsApp)

Plan.md generation by Claude

At least one MCP server for action

Human-in-the-loop approval workflow

Scheduling via cron or task scheduler
Constraints:

Sensitive actions must require approval

External actions limited to defined MCP capabilities

### Phase 3 — Autonomous Employee (Gold Tier)
Scope:

Cross-domain integration (personal + business)

Multiple MCP servers

Weekly business audit and CEO briefing

Error handling, recovery, and audit logging

Full documentation and lessons learned
Constraints:

Strict permission boundaries

Comprehensive logging and safety enforcement

## Phase Execution Rules
For each phase:

/sp.specify must target only that phase's folder.

/sp.plan must be derived strictly from the approved spec.

/sp.tasks must be small, verifiable, and non-expansive.

/sp.implement must implement only approved tasks.

Phase completion requires explicit user confirmation.

## Safety & Control Enforcement

Human-in-the-loop is mandatory for sensitive actions.

Credentials must never be stored in plaintext or vault files.

DRY_RUN and DEV_MODE must be supported where applicable.

All actions must generate audit logs.

Failures must degrade gracefully without silent execution.

## Prohibitions

No auto-starting next phases

No re-creating or altering this constitution

No direct implementation without tasks

No touching SpecifyPlus internal architecture

No scope expansion beyond the hackathon document

## Governance

This constitution establishes the foundational rules for the Personal AI Employee (Digital FTE) — Hackathon 0 project. All project activities must comply with these governance rules. Any amendments to this constitution require explicit approval from project leadership and must be documented with clear justification. Regular compliance reviews should be conducted to ensure adherence to these principles throughout the project lifecycle.

**Version**: 1.0.0 | **Ratified**: 2026-01-14 | **Last Amended**: 2026-01-14