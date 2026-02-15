# Quickstart Guide: Phase 2 - Functional Assistant (Silver Tier)

## Overview
This guide provides instructions for setting up and running the Silver Tier functionality of the Personal AI Employee.

## Prerequisites
- Python 3.11 or higher
- Pip package manager
- Access to email account (for email watcher)
- Designated folder for filesystem monitoring
- Basic understanding of Obsidian vault structure

## Installation
1. Navigate to the project root directory
2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Ensure Phase 1 vault structure is in place (from phase-1/)

## Configuration
1. Set up configuration file in `phase-2/config.py`:
   - Email credentials for IMAP access
   - Filesystem watch directory path
   - MCP server settings
   - Scheduling intervals

2. Configure the Obsidian vault structure with additional directories:
   - `/Pending_Approval/`
   - `/Approved/`
   - `/Rejected/`

## Running the System

### Starting Watchers
1. Run the email watcher:
   ```
   python phase-2/email_watcher.py
   ```
2. Run the filesystem watcher:
   ```
   python phase-2/filesystem_watcher.py
   ```

### Generating Plans
1. Place trigger files or send emails to monitored accounts
2. Claude Code will generate Plan.md files in the `/plans/` directory

### Processing Approval Workflow
1. Check `/Needs_Action/` for new items requiring review
2. Move items to `/Pending_Approval/` when ready for approval
3. Review items in `/Pending_Approval/` and move to `/Approved/` or `/Rejected/`

### Running with Scheduling
1. Start the scheduler:
   ```
   python phase-2/scheduler.py
   ```
2. The system will execute according to configured intervals

## MCP Server Integration
1. Start the MCP server before attempting external actions:
   ```
   python phase-2/mcp_server.py
   ```
2. The server will listen for approval-gated actions

## Testing
Run the test suite to verify functionality:
```
pytest tests/
```

## Troubleshooting
- If watchers don't detect changes, verify configuration and permissions
- If MCP server isn't responding, check network connectivity and authentication
- If scheduling isn't working, verify interval settings in config