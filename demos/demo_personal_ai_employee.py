#!/usr/bin/env python3
"""
Personal AI Employee - Full Demo Script
========================================

This script demonstrates the complete Personal AI Employee workflow:
1. Event Detection (simulated watchers)
2. Claude AI Processing
3. Vault File Creation (Obsidian markdown)
4. Human-in-the-Loop Approval Workflow
5. Cross-Domain Reasoning

Tiers demonstrated:
- Bronze: Basic vault + 1 watcher
- Silver: Multiple watchers + MCP + HITL approval
- Gold: Full cross-domain integration + business audits

Usage:
    python demo_personal_ai_employee.py

Environment Variables:
    ANTHROPIC_API_KEY - Your Claude API key (optional for demo mode)
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("PersonalAIEmployee")

# Add project paths
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "phase-3"))

# Try to import Anthropic
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("anthropic not installed. Running in demo mode without AI processing.")


@dataclass
class SimulatedEvent:
    """Represents a simulated watcher event."""
    source: str  # gmail, whatsapp, filesystem
    event_type: str  # message, file_drop, etc.
    content: str
    sender: str
    timestamp: datetime = field(default_factory=datetime.now)
    priority: str = "normal"
    metadata: Dict[str, Any] = field(default_factory=dict)


class VaultManager:
    """Manages the Obsidian vault for the Personal AI Employee."""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self._ensure_directories()

    def _ensure_directories(self):
        """Create required vault directories."""
        directories = [
            "Inbox",
            "Needs_Action",
            "Needs_Action/Gmail",
            "Needs_Action/WhatsApp",
            "Needs_Action/Filesystem",
            "Done",
            "Pending_Approval",
            "Approved",
            "Rejected",
            "Plans",
            "Briefings",
        ]
        for dir_name in directories:
            (self.vault_path / dir_name).mkdir(parents=True, exist_ok=True)

    def create_action_file(self, event: SimulatedEvent, analysis: Optional[Dict] = None) -> Path:
        """Create an action file in the vault."""
        timestamp = event.timestamp.strftime("%Y-%m-%d_%H%M")
        safe_sender = "".join(c if c.isalnum() else "_" for c in event.sender)
        filename = f"{safe_sender}_{timestamp}.md"

        # Determine output directory based on source
        output_dir = self.vault_path / "Needs_Action" / event.source.capitalize()
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / filename

        # Create markdown content
        content = self._format_action_file(event, analysis)
        filepath.write_text(content, encoding="utf-8")

        logger.info(f"Created action file: {filepath}")
        return filepath

    def _format_action_file(self, event: SimulatedEvent, analysis: Optional[Dict]) -> str:
        """Format the action file content."""
        analysis = analysis or {}

        return f"""---
source: {event.source}
sender: {event.sender}
timestamp: {event.timestamp.isoformat()}
priority: {analysis.get('priority', event.priority)}
status: needs_action
intent: {analysis.get('intent', 'Unknown')}
tags:
  - {event.source}
  - action-required
---

# Message from {event.sender}

**Source:** {event.source.capitalize()}
**Received:** {event.timestamp.strftime("%Y-%m-%d %H:%M:%S")}
**Priority:** {analysis.get('priority', event.priority).upper()}

## Original Content

{event.content}

## AI Analysis

**Summary:** {analysis.get('summary', 'No analysis available')}

**Intent:** {analysis.get('intent', 'Unknown')}

**Recommended Action:** {analysis.get('recommended_action', 'Review manually')}

## Suggested Response

{analysis.get('suggested_reply', 'No suggested reply generated.')}

---

## Actions

- [ ] Review message
- [ ] Take recommended action
- [ ] Send response (if applicable)
- [ ] Move to Done when complete
"""

    def create_approval_request(self, action_type: str, details: Dict) -> Path:
        """Create an approval request file."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"approval_{action_type}_{timestamp}.md"
        filepath = self.vault_path / "Pending_Approval" / filename

        content = f"""---
action_type: {action_type}
status: pending
created: {datetime.now().isoformat()}
requires_approval: true
---

# Approval Request: {action_type.replace('_', ' ').title()}

## Details

{json.dumps(details, indent=2)}

## Approval Actions

- [ ] **APPROVE** - Move this file to `/Approved/` folder
- [ ] **REJECT** - Move this file to `/Rejected/` folder

---

*This action requires human approval before execution.*
"""
        filepath.write_text(content, encoding="utf-8")
        logger.info(f"Created approval request: {filepath}")
        return filepath

    def check_approvals(self) -> List[Dict]:
        """Check for approved actions."""
        approved_dir = self.vault_path / "Approved"
        approved = []

        for filepath in approved_dir.glob("*.md"):
            content = filepath.read_text(encoding="utf-8")
            approved.append({
                "file": filepath.name,
                "path": str(filepath),
                "approved_at": datetime.now().isoformat()
            })

        return approved


class ClaudeProcessor:
    """Processes events using Claude AI."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = None

        if ANTHROPIC_AVAILABLE and self.api_key and self.api_key != "your_anthropic_api_key_here":
            self.client = anthropic.Anthropic(api_key=self.api_key)
            logger.info("Claude AI processor initialized")
        else:
            logger.info("Running in demo mode (no Claude API)")

    async def analyze_event(self, event: SimulatedEvent) -> Dict[str, Any]:
        """Analyze an event using Claude AI."""
        if not self.client:
            return self._demo_analysis(event)

        try:
            prompt = f"""Analyze this message and provide a structured response:

Source: {event.source}
Sender: {event.sender}
Content: {event.content}

Provide your analysis in JSON format with these fields:
- summary: Brief summary of the message
- intent: The purpose/intent of the message
- priority: low, normal, high, or urgent
- recommended_action: What action should be taken
- suggested_reply: A professional reply to send back
- should_reply: true or false
"""

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text

            # Parse JSON response
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content

            return json.loads(json_str)

        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return self._demo_analysis(event)

    def _demo_analysis(self, event: SimulatedEvent) -> Dict[str, Any]:
        """Generate demo analysis without Claude API."""
        # Simple keyword-based analysis for demo
        content_lower = event.content.lower()

        priority = "normal"
        if any(w in content_lower for w in ["urgent", "asap", "immediately", "emergency"]):
            priority = "urgent"
        elif any(w in content_lower for w in ["important", "priority", "deadline"]):
            priority = "high"

        intent = "General Message"
        if any(w in content_lower for w in ["meeting", "schedule", "call"]):
            intent = "Meeting Request"
        elif any(w in content_lower for w in ["help", "support", "issue", "problem"]):
            intent = "Support Request"
        elif any(w in content_lower for w in ["invoice", "payment", "money"]):
            intent = "Financial Matter"

        return {
            "summary": f"Message from {event.sender} via {event.source}",
            "intent": intent,
            "priority": priority,
            "recommended_action": "Review and respond as appropriate",
            "suggested_reply": f"Thank you for your message. I have received your {intent.lower()} and will respond shortly.",
            "should_reply": True
        }


class CrossDomainReasoner:
    """Performs cross-domain reasoning on signals from multiple sources."""

    def __init__(self):
        self.signals: List[SimulatedEvent] = []

    def add_signal(self, event: SimulatedEvent):
        """Add a signal for correlation."""
        self.signals.append(event)

    def correlate(self) -> List[Dict]:
        """Find correlations between signals."""
        correlations = []

        # Group by sender
        by_sender = {}
        for signal in self.signals:
            if signal.sender not in by_sender:
                by_sender[signal.sender] = []
            by_sender[signal.sender].append(signal)

        # Find multi-channel contacts
        for sender, events in by_sender.items():
            if len(events) > 1:
                sources = list(set(e.source for e in events))
                if len(sources) > 1:
                    correlations.append({
                        "type": "multi_channel_contact",
                        "sender": sender,
                        "channels": sources,
                        "message_count": len(events),
                        "insight": f"{sender} is contacting through multiple channels. May indicate urgency."
                    })

        # Find urgent patterns
        urgent_signals = [s for s in self.signals if s.priority == "urgent"]
        if len(urgent_signals) >= 2:
            correlations.append({
                "type": "urgency_cluster",
                "count": len(urgent_signals),
                "senders": list(set(s.sender for s in urgent_signals)),
                "insight": "Multiple urgent messages detected. Prioritize review."
            })

        return correlations


class PersonalAIEmployee:
    """Main orchestrator for the Personal AI Employee demo."""

    def __init__(self, vault_path: Optional[Path] = None):
        self.vault_path = vault_path or PROJECT_ROOT / "demo_vault"
        self.vault = VaultManager(self.vault_path)
        self.processor = ClaudeProcessor()
        self.reasoner = CrossDomainReasoner()

        logger.info(f"Personal AI Employee initialized")
        logger.info(f"Vault path: {self.vault_path}")

    async def process_event(self, event: SimulatedEvent) -> Dict[str, Any]:
        """Process a single event through the full pipeline."""
        logger.info(f"Processing event from {event.source}: {event.sender}")

        # 1. Analyze with Claude
        analysis = await self.processor.analyze_event(event)
        logger.info(f"Analysis complete - Intent: {analysis.get('intent')}, Priority: {analysis.get('priority')}")

        # 2. Create action file in vault
        action_file = self.vault.create_action_file(event, analysis)

        # 3. Add to cross-domain reasoner
        self.reasoner.add_signal(event)

        # 4. Check if approval is required
        if analysis.get("priority") == "urgent" or "financial" in analysis.get("intent", "").lower():
            self.vault.create_approval_request(
                action_type="auto_response",
                details={
                    "sender": event.sender,
                    "suggested_reply": analysis.get("suggested_reply"),
                    "reason": "High-priority or financial message requires approval"
                }
            )

        return {
            "event": event,
            "analysis": analysis,
            "action_file": str(action_file),
            "approval_required": analysis.get("priority") == "urgent"
        }

    async def run_demo(self):
        """Run the full demo with simulated events."""
        print("\n" + "="*60)
        print("  PERSONAL AI EMPLOYEE - DEMO")
        print("  Autonomous Digital FTE Demonstration")
        print("="*60 + "\n")

        # Simulated events from different sources
        demo_events = [
            SimulatedEvent(
                source="gmail",
                event_type="message",
                sender="client@example.com",
                content="Hi, I need to schedule an urgent meeting about the project deadline. Can we talk today?",
                priority="high"
            ),
            SimulatedEvent(
                source="whatsapp",
                event_type="message",
                sender="Manager",
                content="Please review the Q4 budget proposal and send your feedback by EOD.",
                priority="normal"
            ),
            SimulatedEvent(
                source="filesystem",
                event_type="file_drop",
                sender="System",
                content="New file detected: /Dropbox/Invoices/invoice_2026_001.pdf - Requires processing",
                priority="normal",
                metadata={"file_path": "/Dropbox/Invoices/invoice_2026_001.pdf"}
            ),
            SimulatedEvent(
                source="whatsapp",
                event_type="message",
                sender="client@example.com",
                content="URGENT: Haven't heard back about the meeting. This is critical for the launch!",
                priority="urgent"
            ),
        ]

        print("Processing incoming events...\n")

        # Process each event
        results = []
        for i, event in enumerate(demo_events, 1):
            print(f"[{i}/{len(demo_events)}] Processing {event.source} event from {event.sender}...")
            result = await self.process_event(event)
            results.append(result)
            print(f"    ✓ Created: {Path(result['action_file']).name}")
            print(f"    ✓ Priority: {result['analysis'].get('priority', 'normal').upper()}")
            print()

        # Run cross-domain correlation
        print("\n" + "-"*40)
        print("Cross-Domain Reasoning:")
        print("-"*40)

        correlations = self.reasoner.correlate()
        if correlations:
            for corr in correlations:
                print(f"\n  [{corr['type'].upper()}]")
                print(f"  Insight: {corr['insight']}")
        else:
            print("  No cross-domain correlations detected.")

        # Summary
        print("\n" + "="*60)
        print("DEMO SUMMARY")
        print("="*60)
        print(f"\n  Events Processed: {len(results)}")
        print(f"  Action Files Created: {len(results)}")
        print(f"  Approval Requests: {sum(1 for r in results if r['approval_required'])}")
        print(f"  Correlations Found: {len(correlations)}")
        print(f"\n  Vault Location: {self.vault_path}")
        print("\n  Next Steps:")
        print("    1. Review action files in Needs_Action/")
        print("    2. Approve/Reject items in Pending_Approval/")
        print("    3. Move completed items to Done/")
        print("\n" + "="*60)

        return results


async def main():
    """Main entry point."""
    print("\n" + "="*60)
    print("  Personal AI Employee - Hackathon Demo")
    print("  Building Autonomous FTEs in 2026")
    print("="*60)

    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key and api_key != "your_anthropic_api_key_here":
        print("\n  ✓ Claude API key detected - Full AI processing enabled")
    else:
        print("\n  ⚠ No Claude API key - Running in demo mode")
        print("    Set ANTHROPIC_API_KEY environment variable for full AI processing")

    print("\nStarting demonstration...\n")

    # Create and run demo
    employee = PersonalAIEmployee()
    await employee.run_demo()

    print("\nDemo complete! Check the demo_vault/ folder for generated files.\n")


if __name__ == "__main__":
    asyncio.run(main())
