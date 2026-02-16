#!/usr/bin/env python3
"""
WhatsApp Monitor - Simple WhatsApp Web monitoring with OpenRouter AI
=====================================================================
Monitors WhatsApp Web for messages and processes them with AI.

Run: python whatsapp_monitor.py
"""

import os
import json
import time
import asyncio
import urllib.request
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuration
VAULT_PATH = Path("demo_vault/Needs_Action/WhatsApp")
VAULT_PATH.mkdir(parents=True, exist_ok=True)

KEYWORDS = os.getenv('WHATSAPP_KEYWORDS', 'urgent,help,asap,meeting,invoice').split(',')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY') or os.getenv('OPENROUTER_API_KEY')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://openrouter.ai/api/v1')


def analyze_with_ai(sender: str, message: str) -> dict:
    """Analyze message using OpenRouter AI."""
    if not OPENAI_API_KEY:
        return {'intent': 'Unknown', 'priority': 'normal', 'summary': message[:100], 'suggested_reply': 'AI not configured'}

    prompt = f"""Analyze this WhatsApp message and provide a JSON response:

Sender: {sender}
Message: {message}

Respond with ONLY valid JSON (no markdown):
{{"intent": "brief intent description", "priority": "urgent/high/normal/low", "summary": "1-2 sentence summary", "suggested_reply": "professional response to send back"}}"""

    try:
        headers = {
            'Authorization': f'Bearer {OPENAI_API_KEY}',
            'Content-Type': 'application/json',
        }
        data = json.dumps({
            'model': 'openai/gpt-3.5-turbo',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 300
        }).encode('utf-8')

        req = urllib.request.Request(f'{OPENAI_BASE_URL}/chat/completions', data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            ai_text = result['choices'][0]['message']['content'].strip()
            try:
                return json.loads(ai_text)
            except:
                return {'intent': 'Analysis complete', 'priority': 'normal', 'summary': ai_text[:200], 'suggested_reply': 'Please review manually.'}
    except Exception as e:
        return {'intent': 'Error', 'priority': 'normal', 'summary': f'AI Error: {str(e)}', 'suggested_reply': 'Unable to generate suggestion'}


def save_message(sender: str, message: str, ai_analysis: dict):
    """Save processed message to vault."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    filename = f"{sender.replace(' ', '_').replace(':', '')}_{timestamp}.md"
    filepath = VAULT_PATH / filename

    content = f"""---
type: whatsapp-message
sender: {sender}
timestamp: {datetime.now().isoformat()}
priority: {ai_analysis.get('priority', 'normal')}
---

# WhatsApp Message from {sender}

## Original Message
{message}

## AI Analysis
**Intent:** {ai_analysis.get('intent', 'Unknown')}
**Priority:** {ai_analysis.get('priority', 'normal')}
**Summary:** {ai_analysis.get('summary', message[:100])}

## Suggested Response
{ai_analysis.get('suggested_reply', 'No suggestion available')}

## Action Required
- [ ] Review message
- [ ] Respond to sender
- [ ] Mark as done
"""
    filepath.write_text(content, encoding='utf-8')
    return filename


async def monitor_whatsapp():
    """Monitor WhatsApp Web for new messages."""
    from playwright.async_api import async_playwright

    print("=" * 60)
    print("  WhatsApp Monitor - OpenRouter AI")
    print("=" * 60)
    print(f"\n  Keywords: {', '.join(KEYWORDS)}")
    print(f"  AI: {'Connected' if OPENAI_API_KEY else 'Not configured'}")
    print(f"  Vault: {VAULT_PATH}")
    print("\n  Starting browser...")
    print("=" * 60)

    async with async_playwright() as p:
        # Launch browser with persistent context for session
        session_path = Path("whatsapp_session")
        session_path.mkdir(exist_ok=True)

        browser = await p.chromium.launch_persistent_context(
            user_data_dir=str(session_path),
            headless=False,
            args=['--start-maximized']
        )

        page = browser.pages[0] if browser.pages else await browser.new_page()

        print("\n  Opening WhatsApp Web...")
        await page.goto("https://web.whatsapp.com")

        print("\n  ⏳ Waiting for WhatsApp to load...")
        print("  📱 Scan QR code with your phone if needed")
        print("     (WhatsApp > Linked Devices > Link a Device)\n")

        # Wait for WhatsApp to fully load (chat list visible)
        try:
            await page.wait_for_selector('[data-testid="chat-list"]', timeout=120000)
            print("  ✅ WhatsApp loaded successfully!\n")
        except:
            print("  ⚠️ Timeout waiting for WhatsApp. Make sure to scan QR code.\n")

        print("  👀 Monitoring for messages...")
        print("  Press Ctrl+C to stop\n")
        print("-" * 60)

        processed_messages = set()

        while True:
            try:
                # Find unread message indicators
                unread_chats = await page.query_selector_all('[data-testid="icon-unread-count"]')

                for unread in unread_chats:
                    try:
                        # Get parent chat element
                        chat = await unread.evaluate_handle('el => el.closest("[data-testid=\\"cell-frame-container\\"]")')
                        if not chat:
                            continue

                        # Click to open chat
                        await chat.click()
                        await asyncio.sleep(1)

                        # Get chat name
                        header = await page.query_selector('[data-testid="conversation-header"]')
                        sender = "Unknown"
                        if header:
                            name_el = await header.query_selector('span[dir="auto"]')
                            if name_el:
                                sender = await name_el.inner_text()

                        # Get latest messages
                        messages = await page.query_selector_all('[data-testid="msg-container"]')

                        for msg in messages[-5:]:  # Check last 5 messages
                            try:
                                # Get message text
                                text_el = await msg.query_selector('[data-testid="balloon-template"] span.selectable-text')
                                if not text_el:
                                    continue

                                message_text = await text_el.inner_text()

                                # Create unique ID
                                msg_id = f"{sender}:{message_text[:50]}"
                                if msg_id in processed_messages:
                                    continue

                                # Check keywords
                                message_lower = message_text.lower()
                                matched = any(kw.strip().lower() in message_lower for kw in KEYWORDS if kw.strip())

                                if matched or '*' in KEYWORDS:
                                    print(f"\n  📩 New message from: {sender}")
                                    print(f"  📝 Message: {message_text[:100]}...")

                                    # Analyze with AI
                                    print("  🤖 Analyzing with AI...")
                                    analysis = analyze_with_ai(sender, message_text)

                                    # Save to vault
                                    filename = save_message(sender, message_text, analysis)
                                    print(f"  ✅ Saved: {filename}")
                                    print(f"  📊 Priority: {analysis.get('priority', 'normal')}")
                                    print(f"  💡 Intent: {analysis.get('intent', 'Unknown')}")

                                    processed_messages.add(msg_id)

                            except Exception as e:
                                pass

                    except Exception as e:
                        pass

                await asyncio.sleep(5)  # Check every 5 seconds

            except KeyboardInterrupt:
                print("\n\n  👋 Stopping WhatsApp Monitor...")
                break
            except Exception as e:
                print(f"  ⚠️ Error: {e}")
                await asyncio.sleep(5)

        await browser.close()


def main():
    try:
        asyncio.run(monitor_whatsapp())
    except KeyboardInterrupt:
        print("\n  Goodbye!")


if __name__ == '__main__':
    main()
