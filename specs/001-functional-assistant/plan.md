# Implementation Plan: Phase 2 - Functional Assistant (Silver Tier)

**Branch**: `001-functional-assistant` | **Date**: 2026-01-14 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-functional-assistant/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implementation of Phase 2 Functional Assistant (Silver Tier) expanding from Phase 1 Foundation. This includes introducing multiple watchers (minimum two), Claude Code Plan.md generation, MCP server integration for controlled external actions, human-in-the-loop approval workflow, and basic scheduling without autonomous loops. The system builds upon stable Phase 1 outputs while maintaining strict human oversight and safety controls.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: imaplib, playwright, watchfiles, fastmcp, schedule, obsidian, pathlib, datetime
**Storage**: File-based (Obsidian vault structure)
**Testing**: pytest for unit/integration tests
**Target Platform**: Windows/Linux/Mac cross-platform
**Project Type**: Multi-component system with external integrations
**Performance Goals**: Sub-second response for watcher triggers, scheduled execution within 10 seconds of trigger time
**Constraints**: All sensitive actions require human approval, no autonomous loops, MCP-mediated external actions only
**Scale/Scope**: Up to 2 concurrent watchers, 1 MCP server, scheduled execution intervals of 1 minute or greater

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- ✅ **Phase Sequentiality**: Building on completed Phase 1 Foundation (Bronze Tier)
- ✅ **Scope Compliance**: Limited to Silver Tier requirements only
- ✅ **Architecture Compliance**: MCP server integration as specified
- ✅ **Safety Compliance**: Human-in-the-loop approval for sensitive actions
- ✅ **Prohibition Compliance**: No scope expansion beyond hackathon document
- ✅ **Constitution Adherence**: Following immutable constitution rules

## Project Structure

### Documentation (this feature)

```text
specs/001-functional-assistant/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
phase-2/
├── email_watcher.py          # Enhanced email watcher from Phase 1
├── whatsapp_watcher.py       # New WhatsApp watcher
├── filesystem_watcher.py     # New filesystem watcher
├── plan_generator.py         # Claude Code Plan.md generator
├── mcp_server.py             # MCP server for external actions
├── approval_workflow.py      # HITL approval system
├── scheduler.py              # Basic scheduling system
├── vault_manager.py          # Interface with Obsidian vault
└── config.py                 # Configuration management

tests/
├── integration/
│   ├── test_watchers.py
│   ├── test_plan_generation.py
│   ├── test_mcp_integration.py
│   └── test_approval_workflow.py
└── unit/
    ├── test_watcher_schema.py
    ├── test_plan_format.py
    └── test_scheduler.py
```

**Structure Decision**: Single project structure chosen to maintain consistency with Phase 1 while adding the required Silver Tier functionality. The modular approach allows for separate components for each watcher, planning, MCP integration, approval workflow, and scheduling.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Multiple watchers | Silver Tier requirement for multi-source monitoring | Single watcher insufficient for Phase 2 objectives |
| MCP server integration | Required for safe external action execution | Direct external actions prohibited by safety rules |
