# Research Summary: Phase 2 - Functional Assistant (Silver Tier)

## Overview
This research document covers the key decisions and findings for implementing the Silver Tier functionality of the Personal AI Employee, building upon the Phase 1 Foundation.

## Decision: MCP Server Selection
**Rationale**: Need to select a single MCP server for external actions that is secure, approval-gated, and follows best practices for human-in-the-loop validation.
**Chosen Solution**: Email MCP server using Gmail API for sending emails as this aligns with existing email watcher infrastructure and provides a clear external action type.
**Alternatives considered**:
- WhatsApp message sender (requires more complex setup)
- File system writer (less useful for external communication)
- Calendar event creator (requires additional dependencies)

## Decision: Second Watcher Type
**Rationale**: Need to add a second watcher alongside the existing email watcher to meet the minimum two watchers requirement.
**Chosen Solution**: Filesystem watcher monitoring a designated folder for new files or changes, as this provides a different input source type than email and is relatively simple to implement.
**Alternatives considered**:
- WhatsApp watcher (requires browser automation, more complex)
- Database watcher (overkill for Silver Tier)

## Decision: Plan.md Generation Approach
**Rationale**: Claude Code needs to generate structured Plan.md files that define objectives, contain ordered steps, and mark approval requirements.
**Chosen Solution**: Template-based approach where Claude fills in a predefined Plan.md structure with objectives, steps, and approval markers.
**Alternatives considered**:
- Freeform generation (less structured, harder to parse)
- Separate file format (adds complexity)

## Decision: Approval Workflow Implementation
**Rationale**: Need to implement file-based approval workflow with /Pending_Approval, /Approved, /Rejected directories.
**Chosen Solution**: File movement system where files are moved between directories based on human approval status, with metadata tracking approval status.
**Alternatives considered**:
- Database tracking (overkill for Silver Tier)
- In-file status markers (less clear separation)

## Decision: Scheduling Mechanism
**Rationale**: Need to implement basic scheduling without creating autonomous loops.
**Chosen Solution**: Python schedule library for cross-platform compatibility with simple interval-based triggers that initiate Claude execution then return to idle state.
**Alternatives considered**:
- OS-level cron/Task Scheduler (more complex to manage from Python)
- Custom timer implementation (unnecessary reinvention)

## Technology Stack Confirmation
- **Backend**: Python 3.11 (consistent with Phase 1)
- **Watchers**: Built-in libraries (imaplib for email, watchdog for filesystem)
- **MCP Server**: FastMCP framework for standardized integration
- **Scheduling**: schedule library for cross-platform compatibility
- **Vault Interface**: Direct file system operations with pathlib