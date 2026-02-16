#!/usr/bin/env python3
"""
Claude WhatsApp Integration - Connect WhatsApp messages to Anthropic Claude AI service.

This module integrates the WhatsApp watcher with the Claude AI service to automatically
process incoming WhatsApp messages and generate intelligent responses.
"""

import asyncio
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import sys
import json

# Add paths for the watcher framework
sys.path.insert(0, str(Path(__file__).parent / ".claude" / "skills" / "base-watcher-framework" / "scripts"))
sys.path.insert(0, str(Path(__file__).parent / ".claude" / "skills" / "whatsapp-watcher" / "scripts"))

from base_watcher import WatcherEvent
from whatsapp_watcher import WhatsAppWatcher, WhatsAppWatcherConfig, TriggerRule
from whatsapp_emitter import WhatsAppActionEmitter, WhatsAppEmitterConfig

# Import Anthropic for Claude API
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("Warning: anthropic not installed. Install with: pip install anthropic")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


class ClaudeWhatsAppIntegrator:
    """
    Integrates WhatsApp watcher with Claude AI service for automated message processing.

    This class listens to WhatsApp events and processes them through Claude AI to
    generate intelligent responses or perform automated actions based on the content.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize the Claude WhatsApp integrator.

        Args:
            api_key: Anthropic Claude API key. If not provided, will use ANTHROPIC_API_KEY env var.
            model: Claude model to use (default: claude-sonnet-4-20250514)
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic required for Claude integration. Install with:\n"
                "pip install anthropic"
            )

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Claude API key not provided. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model
        self._response_callbacks = []
        self._reply_callbacks = []

    def on_response(self, callback):
        """
        Register a callback for Claude responses.

        Args:
            callback: Function called with response data when Claude processes a message
        """
        self._response_callbacks.append(callback)
        return self

    def on_reply_generated(self, callback):
        """
        Register a callback for when Claude generates a reply that can be sent back to WhatsApp.

        Args:
            callback: Function called with reply content and original message data
        """
        self._reply_callbacks.append(callback)
        return self

    async def process_whatsapp_event(self, event: WatcherEvent) -> Optional[Dict[str, Any]]:
        """
        Process a WhatsApp event through Claude AI.

        Args:
            event: WatcherEvent from WhatsApp watcher

        Returns:
            Response from Claude AI or None if not applicable
        """
        # Only process WhatsApp message events
        if event.metadata.get('message_type') != 'whatsapp':
            return None

        if event.event_type.value != 'CREATED':  # Only process new messages
            return None

        data = event.data
        message_text = data.get('text', '')

        if not message_text.strip():
            return None

        logger.info(f"Processing WhatsApp message with Claude: {message_text[:50]}...")

        # Prepare context for Claude
        context = self._prepare_context(data)

        try:
            # Call Claude API
            response = await self._call_claude_api(context)

            if response:
                # Execute response callbacks
                for callback in self._response_callbacks:
                    try:
                        callback(response, data)
                    except Exception as e:
                        logger.error(f"Error in response callback: {e}")

                # If Claude generated a reply, execute reply callbacks
                if response.get('success') and response.get('parsed_content'):
                    reply_content = response['parsed_content'].get('suggested_reply')
                    if reply_content:
                        for callback in self._reply_callbacks:
                            try:
                                callback(reply_content, data)
                            except Exception as e:
                                logger.error(f"Error in reply callback: {e}")

                return response

        except Exception as e:
            logger.error(f"Error processing message with Claude: {e}")
            return None

    def _prepare_context(self, message_data: Dict[str, Any]) -> str:
        """
        Prepare context for Claude API call.

        Args:
            message_data: WhatsApp message data from event

        Returns:
            Formatted context string for Claude
        """
        context = f"""WhatsApp Message Analysis and Response Generation Request:

Message Details:
- Chat: {message_data.get('chat_name', 'Unknown')}
- Sender: {message_data.get('sender', 'Unknown')}
- Chat Type: {message_data.get('chat_type', 'Unknown')}
- Timestamp: {message_data.get('timestamp', '')}
- Priority: {message_data.get('priority', 'normal')}
- Triggers: {', '.join(message_data.get('matched_triggers', []))}

Message Content:
{message_data.get('text', '')}

Instructions:
Analyze this WhatsApp message and provide:
1. A brief summary of the message content
2. The intent or purpose of the message
3. Recommended action to take
4. Priority assessment (low, medium, high, urgent)
5. Any important details or deadlines mentioned
6. A suggested reply to send back to the sender (if appropriate)
7. Whether a reply should be sent (true/false)

Response format: Please structure your response in JSON format with keys: summary, intent, recommended_action, priority, details, suggested_reply, should_reply.
"""
        return context

    async def _call_claude_api(self, context: str) -> Optional[Dict[str, Any]]:
        """
        Call Claude API with the prepared context.

        Args:
            context: Context string for Claude

        Returns:
            Parsed response from Claude or None on error
        """
        try:
            # Use asyncio to run the synchronous API call
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    system="You are an intelligent assistant that analyzes WhatsApp messages and provides structured responses. Always respond in JSON format with the requested fields. Be helpful but cautious about sending replies automatically.",
                    messages=[
                        {
                            "role": "user",
                            "content": context
                        }
                    ]
                )
            )

            if response and response.content:
                content = response.content[0].text

                # Try to parse JSON response
                try:
                    # Extract JSON from response (Claude might wrap it in markdown code blocks)
                    json_content = content
                    if "```json" in content:
                        json_content = content.split("```json")[1].split("```")[0].strip()
                    elif "```" in content:
                        json_content = content.split("```")[1].split("```")[0].strip()

                    parsed_content = json.loads(json_content)
                    return {
                        'raw_response': response,
                        'parsed_content': parsed_content,
                        'success': True
                    }
                except json.JSONDecodeError:
                    # If JSON parsing fails, return the raw content
                    return {
                        'raw_response': response,
                        'raw_content': content,
                        'success': False,
                        'error': 'Failed to parse JSON response'
                    }
            else:
                logger.error("Claude API returned empty response")
                return {
                    'success': False,
                    'error': "Empty response from API"
                }

        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            return {
                'success': False,
                'error': f"API error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class WhatsAppWithClaude:
    """
    High-level class that combines WhatsApp watcher with Claude AI integration.

    This provides a simple interface to start a WhatsApp watcher that automatically
    processes messages through Claude AI.
    """

    def __init__(self,
                 claude_api_key: Optional[str] = None,
                 claude_model: str = "claude-sonnet-4-20250514",
                 whatsapp_triggers: Optional[list] = None,
                 output_path: str = "./Needs_Action/WhatsApp",
                 auto_reply_enabled: bool = False):
        """
        Initialize the integrated WhatsApp + Claude system.

        Args:
            claude_api_key: Claude API key
            claude_model: Claude model to use
            whatsapp_triggers: Custom triggers for WhatsApp watcher
            output_path: Path for action files
            auto_reply_enabled: Whether to automatically send replies back to WhatsApp (default: False)
        """
        self.claude_integrator = ClaudeWhatsAppIntegrator(claude_api_key, claude_model)
        self.whatsapp_triggers = whatsapp_triggers or [
            {"pattern": "urgent", "priority": "urgent", "name": "urgent-keyword"},
            {"pattern": "asap", "priority": "urgent", "name": "asap-keyword"},
            {"pattern": "@task", "priority": "high", "name": "task-mention"},
            {"pattern": "please", "priority": "normal", "name": "please-keyword"},
        ]
        self.output_path = output_path
        self.auto_reply_enabled = auto_reply_enabled  # Controls whether to auto-send replies
        self.watcher: Optional[WhatsAppWatcher] = None
        self.emitter: Optional[WhatsAppActionEmitter] = None

    def setup_handlers(self):
        """Setup event handlers for the integration."""
        # Create emitter for action files
        emitter_config = WhatsAppEmitterConfig(output_path=self.output_path)
        self.emitter = WhatsAppActionEmitter(emitter_config)

        # Setup Claude response handler
        def handle_claude_response(response, message_data):
            logger.info(f"Claude analysis completed for message from {message_data.get('sender')}")
            if response.get('success'):
                parsed = response['parsed_content']
                logger.info(f"Intent: {parsed.get('intent', 'Unknown')}")
                logger.info(f"Recommended action: {parsed.get('recommended_action', 'None')}")
                logger.info(f"Priority: {parsed.get('priority', 'Unknown')}")

                # Log if a reply was suggested
                if parsed.get('should_reply'):
                    suggested_reply = parsed.get('suggested_reply', '')
                    if suggested_reply:
                        logger.info(f"Suggested reply: {suggested_reply[:100]}...")
            else:
                logger.warning(f"Claude analysis had issues: {response.get('error')}")

        # Setup Claude reply handler
        def handle_claude_reply(reply_content, message_data):
            logger.info(f"Claude generated reply for {message_data.get('sender')}: {reply_content[:100]}...")

            if self.auto_reply_enabled:
                # In a real implementation, we would send the reply back to WhatsApp
                # For now, we'll just log it as a placeholder
                logger.info(f"AUTO-REPLY WOULD BE SENT to {message_data.get('chat_name')}: {reply_content}")
                # TODO: Implement actual reply sending via WhatsApp Web automation
            else:
                logger.info("Auto-reply disabled - would need manual approval to send reply")

        self.claude_integrator.on_response(handle_claude_response)
        self.claude_integrator.on_reply_generated(handle_claude_reply)

    async def start(self, session_path: str = "./whatsapp_session", headless: bool = False):
        """
        Start the integrated WhatsApp + Claude system.

        Args:
            session_path: Path for WhatsApp session storage
            headless: Whether to run WhatsApp in headless mode
        """
        if not self.emitter:
            self.setup_handlers()

        # Create WhatsApp watcher config
        watcher_config = WhatsAppWatcherConfig(
            name="whatsapp-claude-integration",
            session_path=session_path,
            headless=headless,
            triggers=[TriggerRule(**t) for t in self.whatsapp_triggers],
            poll_interval=5.0
        )

        # Create watcher
        self.watcher = WhatsAppWatcher(watcher_config)

        # Setup event handlers
        def handle_whatsapp_event(event):
            # First emit to action file
            filepath = self.emitter.emit(event)
            if filepath:
                logger.info(f"Created action file: {filepath}")

            # Then process with Claude
            asyncio.create_task(self._process_with_claude(event))

        def handle_qr(msg):
            logger.info(f"QR Code: {msg}")
            print("\n" + "="*50)
            print("SCAN QR CODE IN BROWSER WINDOW")
            print("="*50 + "\n")

        self.watcher.on_event(handle_whatsapp_event)
        self.watcher.on_error(lambda e: logger.error(f"Watcher error: {e}"))
        self.watcher.on_qr_code(handle_qr)

        logger.info("Starting WhatsApp + Claude integration...")
        logger.info(f"Auto-reply enabled: {self.auto_reply_enabled}")
        await self.watcher.start()

    async def _process_with_claude(self, event: WatcherEvent):
        """Process event with Claude in the background."""
        try:
            await self.claude_integrator.process_whatsapp_event(event)
        except Exception as e:
            logger.error(f"Error processing event with Claude: {e}")

    async def stop(self):
        """Stop the integrated system."""
        if self.watcher:
            await self.watcher.stop()


# Convenience function
def run_whatsapp_claude_integration(
    claude_api_key: Optional[str] = None,
    session_path: str = "./whatsapp_session",
    output_path: str = "./Needs_Action/WhatsApp",
    headless: bool = False,
    auto_reply: bool = False
):
    """
    Convenience function to run the WhatsApp + Claude integration.

    Args:
        claude_api_key: Claude API key (defaults to ANTHROPIC_API_KEY env var)
        session_path: WhatsApp session storage path
        output_path: Path for action files
        headless: Run in headless mode (after initial QR scan)
        auto_reply: Enable auto-reply to WhatsApp messages (default: False)
    """
    integrator = WhatsAppWithClaude(
        claude_api_key=claude_api_key,
        output_path=output_path,
        auto_reply_enabled=auto_reply
    )

    async def run():
        try:
            await integrator.start(session_path, headless)
            # Keep running until interrupted
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            await integrator.stop()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Integration stopped by user")


def send_reply_to_whatsapp(reply_content: str, chat_name: str, whatsapp_instance=None):
    """
    Helper function to send a reply back to WhatsApp.

    Note: This is a placeholder implementation. A full implementation would require
    using the same Playwright automation used by the WhatsAppWatcher to send messages.

    Args:
        reply_content: The content to send as a reply
        chat_name: The name of the chat to send the reply to
        whatsapp_instance: Optional WhatsAppWatcher instance to use for sending
    """
    logger.info(f"Attempting to send reply to {chat_name}: {reply_content}")

    # In a complete implementation, this would:
    # 1. Find the correct chat in the WhatsApp Web interface
    # 2. Type the reply content into the message input field
    # 3. Send the message

    # Placeholder for future implementation
    print(f"[PLACEHOLDER] Reply would be sent to '{chat_name}': {reply_content}")
    print("To implement this functionality, extend the WhatsAppWatcher class with a send_message method.")


if __name__ == "__main__":
    # Example usage
    print("Claude WhatsApp Integration")
    print("This script integrates WhatsApp message monitoring with Claude AI analysis.")
    print()
    print("Usage:")
    print("  python claude_whatsapp_integration.py")
    print()
    print("Environment variables:")
    print("  ANTHROPIC_API_KEY - Your Anthropic Claude API key")
    print()
    print("Make sure you have:")
    print("  1. Installed anthropic: pip install anthropic")
    print("  2. Set your ANTHROPIC_API_KEY environment variable")
    print("  3. Installed playwright: pip install playwright && playwright install chromium")
    print()
    print("Features:")
    print("  - Monitors WhatsApp messages based on trigger keywords")
    print("  - Analyzes messages using Claude AI")
    print("  - Creates action files in Obsidian format")
    print("  - Generates intelligent responses (manual or automatic)")
    print("  - Supports priority-based organization")
    print()

    # Run the integration if API key is available
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        print("Starting integration with available API key...")
        # By default, run with auto-reply disabled for safety
        run_whatsapp_claude_integration(auto_reply=False)
    else:
        print("ANTHROPIC_API_KEY not found. Please set the environment variable.")
        print()
        print("To run with auto-reply enabled (USE WITH CAUTION):")
        print("  ANTHROPIC_API_KEY=your_key_here python claude_whatsapp_integration.py")
