# Quickstart Guide: Phase 3 - Autonomous Employee (Gold Tier)

## Overview
This guide provides instructions for setting up and running the Gold Tier functionality of the Personal AI Employee, building upon the Phase 1 and Phase 2 foundations.

## Prerequisites
- Python 3.11 or higher
- Pip package manager
- Access to Phase 1 and Phase 2 outputs (vault structure, MCP servers)
- Basic understanding of Obsidian vault structure
- Appropriate credentials for MCP server integrations

## Installation
1. Navigate to the project root directory
2. Install required dependencies:
   ```
   pip install -r phase-3/requirements.txt
   ```
3. Ensure Phase 1 and Phase 2 vault structures are in place

## Configuration
1. Set up configuration file in `phase-3/config.py`:
   - MCP server connection settings for communication, browser, and scheduling servers
   - Cross-domain permission boundaries
   - Audit logging settings
   - Weekly audit schedule timing
   - CEO briefing generation timing
   - Error handling parameters

2. Configure the extended vault structure with additional directories:
   - `/phase-3/audits/` - For weekly audit reports
   - `/phase-3/briefings/` - For CEO briefings
   - `/phase-3/logs/` - For audit logs

## Running the System

### Starting Cross-Domain Reasoning
1. Run the cross-domain reasoner:
   ```
   python phase-3/cross_domain_reasoner.py
   ```
2. The system will correlate information across personal and business domains

### Managing MCP Servers
1. Start the MCP manager to coordinate all MCP servers:
   ```
   python phase-3/mcp_manager.py
   ```
2. Individual MCP servers (communication, browser, scheduling) will be managed automatically

### Running Weekly Audits
1. The system will automatically run weekly audits based on configured schedule
2. Audit reports will be generated in the `/phase-3/audits/` directory

### Generating CEO Briefings
1. CEO briefings will be generated automatically on the configured schedule (typically Monday mornings)
2. Briefings will be placed in the `/phase-3/briefings/` directory

### Audit Logging
1. All actions are automatically logged to the `/phase-3/logs/` directory
2. Logs contain timestamp, action type, target, approval status, and result

### Error Handling
1. The error handler monitors for different error categories
2. Recovery procedures are applied based on error type
3. Appropriate notifications are sent according to escalation procedures

## Safety and Oversight
1. All financial actions require explicit approval
2. Permission boundaries are enforced by the safety enforcer
3. Human-in-the-loop requirements are maintained for critical actions

## Testing
Run the test suite to verify functionality:
```
pytest tests/
```

## Troubleshooting
- If cross-domain reasoning isn't working, verify domain permission settings
- If MCP servers aren't responding, check network connectivity and authentication
- If audits aren't running, verify schedule configuration
- If error handling isn't working, check error category mappings