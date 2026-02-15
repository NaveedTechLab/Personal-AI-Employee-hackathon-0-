# Claude WhatsApp Integration

This project integrates WhatsApp message monitoring with Anthropic's Claude AI service to provide intelligent message analysis and automated responses.

## Features

- **WhatsApp Monitoring**: Uses Playwright to monitor WhatsApp Web for messages containing trigger keywords
- **AI Analysis**: Leverages Claude AI to analyze messages and extract intent, summarize content, and assess priority
- **Automated Responses**: Generates intelligent responses based on message content (optional auto-reply feature)
- **Action Files**: Creates structured Markdown action files in Obsidian format for important messages
- **Priority Management**: Organizes messages by priority level (urgent, high, normal, low)

## Prerequisites

1. **Python 3.8+**
2. **Anthropic Account** with Claude API access
3. **WhatsApp Account** with access to WhatsApp Web

## Installation

```bash
# Install required packages
pip install anthropic playwright
playwright install chromium

# Clone or download this repository
git clone <repository-url>
cd Personal-AI-Employee
```

## Configuration

### 1. Set up Claude API Access

Get your API key from [Anthropic Console](https://console.anthropic.com/) and set it as an environment variable:

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

On Windows:
```cmd
set ANTHROPIC_API_KEY=your-api-key-here
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt  # if available
# Or manually install:
pip install anthropic playwright pyyaml
playwright install chromium
```

## Usage

### Basic Usage

```bash
python claude_whatsapp_integration.py
```

This will:
1. Start WhatsApp Web monitoring
2. Look for messages matching predefined triggers
3. Analyze matching messages with Claude AI
4. Create action files in `./Needs_Action/WhatsApp/`
5. Generate intelligent responses (but not auto-send them by default)

### With Auto-Reply Enabled (Use with Caution!)

```bash
ANTHROPIC_API_KEY=your-key-here python claude_whatsapp_integration.py --auto-reply
```

### Custom Configuration

You can customize the integration with various parameters:

```python
from claude_whatsapp_integration import WhatsAppWithClaude

# Create custom configuration
integrator = WhatsAppWithClaude(
    claude_api_key="your-api-key",  # Or leave None to use ANTHROPIC_API_KEY env var
    claude_model="claude-sonnet-4-20250514",  # Other options: claude-3-haiku, claude-3-opus
    whatsapp_triggers=[           # Custom trigger patterns
        {"pattern": "urgent", "priority": "urgent", "name": "urgent-keyword"},
        {"pattern": "meeting", "priority": "high", "name": "meeting-request"},
        {"pattern": r"order.*\d+", "is_regex": True, "priority": "normal", "name": "order-reference"}
    ],
    output_path="./custom-actions",     # Where to save action files
    auto_reply_enabled=False           # Whether to auto-send replies
)

# Setup and start
integrator.setup_handlers()
await integrator.start(session_path="./custom_session", headless=False)
```

## How It Works

1. **Monitoring Phase**: The system continuously monitors WhatsApp Web for new messages
2. **Trigger Detection**: Messages containing configured trigger keywords are flagged
3. **AI Analysis**: Flagged messages are sent to Claude AI for analysis
4. **Response Generation**: Claude AI generates summaries, intent classification, and suggested responses
5. **Action Creation**: Structured action files are created in Obsidian format
6. **Reply Handling**: If auto-reply is enabled, responses are sent back to WhatsApp

## Security Considerations

- **API Keys**: Store API keys securely and never commit them to version control
- **Auto-Reply**: Use auto-reply feature with caution as AI-generated responses may not always be appropriate
- **Privacy**: Be aware that message content is sent to Anthropic's Claude API for analysis

## Troubleshooting

### Common Issues

1. **WhatsApp Login Problems**:
   - Make sure you scan the QR code with your phone during the initial setup
   - Session data is stored in `./whatsapp_session/` to persist login state

2. **API Key Issues**:
   - Verify your ANTHROPIC_API_KEY is set correctly
   - Check that your Anthropic account has API access enabled

3. **Playwright/Chromium Issues**:
   - Make sure Chromium is installed: `playwright install chromium`
   - Check that your system meets Playwright requirements

### Logs

The system logs activity to help with debugging:

```
2026-01-21 10:30:00 [INFO] claude_whatsapp_integration: Processing WhatsApp message with Claude: Hi, can you help me...
2026-01-21 10:30:05 [INFO] claude_whatsapp_integration: Claude analysis completed for message from John Doe
2026-01-21 10:30:05 [INFO] claude_whatsapp_integration: Intent: Support Request
2026-01-21 10:30:05 [INFO] claude_whatsapp_integration: Created action file: ./Needs_Action/WhatsApp/03_Normal/test_contact_2026-01-21_1030_msg.md
```

## Files Created

- `./Needs_Action/WhatsApp/`: Default output directory for action files
- `./whatsapp_session/`: WhatsApp session data for persistent login
- Action files in Obsidian Markdown format with YAML frontmatter

## Customization

### Adding New Triggers

Modify the triggers in your configuration:

```python
triggers = [
    # Exact match trigger
    {"pattern": "help", "priority": "high", "name": "help-request"},

    # Regex trigger
    {"pattern": r"urgent|asap|immediately", "is_regex": True, "priority": "urgent", "name": "urgency-words"},

    # Case-sensitive trigger
    {"pattern": "CONFIDENTIAL", "case_sensitive": True, "priority": "urgent", "name": "confidential-message"}
]
```

### Custom Action Templates

The system creates action files using a default template. You can customize this by modifying the WhatsAppActionEmitter configuration.

## Project Architecture

This project is part of the **Personal AI Employee Hackathon 0** - Building Autonomous FTEs (Full-Time Equivalent) in 2026.

### Components:
- **Brain**: Claude Code (reasoning engine)
- **Memory/GUI**: Obsidian vault (local markdown)
- **Senses (Watchers)**: Python scripts monitoring Gmail, WhatsApp, filesystem
- **Hands (MCP)**: Model Context Protocol servers for external actions

### Tiers:
- **Bronze**: Basic vault + 1 watcher
- **Silver**: Multiple watchers + MCP + HITL approval
- **Gold**: Full cross-domain integration + business audits
- **Platinum**: 24/7 cloud deployment ✓ COMPLETE

The **Platinum tier** is now fully implemented with:
- Containerized deployment (Docker)
- Kubernetes orchestration
- Health monitoring and alerting
- Process supervision and auto-restart
- Metrics collection and monitoring (Prometheus)
- CI/CD pipeline for automated deployment
- Production security and resource management
- 24/7 operation capability

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
# Personal-AI-Employee-hackathon-0-
