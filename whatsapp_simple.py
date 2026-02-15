#!/usr/bin/env python3
"""
WhatsApp Monitor - Working version with OpenRouter AI
======================================================
Run: python whatsapp_simple.py
"""

import os
import json
import asyncio
import urllib.request
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configuration
VAULT_PATH = Path("demo_vault/Needs_Action/WhatsApp")
VAULT_PATH.mkdir(parents=True, exist_ok=True)

KEYWORDS = ['urgent', 'help', 'asap', 'meeting', 'invoice', 'payment', 'order', 'support', 'need']
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY') or os.getenv('OPENROUTER_API_KEY')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://openrouter.ai/api/v1')

processed = set()


def analyze_with_ai(sender: str, message: str) -> dict:
    """Analyze message using OpenRouter AI."""
    if not OPENAI_API_KEY:
        return {'intent': 'No AI configured', 'priority': 'normal', 'summary': message, 'suggested_reply': 'Configure OPENAI_API_KEY'}

    try:
        headers = {'Authorization': f'Bearer {OPENAI_API_KEY}', 'Content-Type': 'application/json'}
        prompt = f"""Analyze this WhatsApp message and respond with JSON only:

From: {sender}
Message: {message}

JSON format: {{"intent": "what they want", "priority": "urgent/high/normal/low", "summary": "brief summary", "suggested_reply": "professional response"}}"""

        data = json.dumps({
            'model': 'openai/gpt-3.5-turbo',
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': 300
        }).encode()

        req = urllib.request.Request(f'{OPENAI_BASE_URL}/chat/completions', data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            ai_text = result['choices'][0]['message']['content'].strip()

            # Extract JSON from response
            if '{' in ai_text:
                json_str = ai_text[ai_text.find('{'):ai_text.rfind('}')+1]
                return json.loads(json_str)
            return {'intent': ai_text[:100], 'priority': 'normal', 'summary': ai_text, 'suggested_reply': 'Review manually'}
    except Exception as e:
        print(f"      ⚠️ AI Error: {e}")
        return {'intent': 'Error', 'priority': 'normal', 'summary': str(e), 'suggested_reply': 'AI unavailable'}


def save_message(sender: str, message: str, analysis: dict) -> str:
    """Save processed message to vault."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"whatsapp_{timestamp}.md"
    filepath = VAULT_PATH / filename

    content = f"""---
type: whatsapp-message
sender: {sender}
timestamp: {datetime.now().isoformat()}
priority: {analysis.get('priority', 'normal')}
---

# WhatsApp Message

**From:** {sender}
**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Priority:** {analysis.get('priority', 'normal')}

## Original Message
{message}

## AI Analysis
| Field | Value |
|-------|-------|
| Intent | {analysis.get('intent', 'Unknown')} |
| Priority | {analysis.get('priority', 'normal')} |
| Summary | {analysis.get('summary', '')} |

## Suggested Reply
{analysis.get('suggested_reply', 'No suggestion')}

## Actions
- [ ] Review message
- [ ] Send reply
- [ ] Mark complete
"""
    filepath.write_text(content, encoding='utf-8')
    return filename


def process_message(sender: str, message: str) -> str | None:
    """Process a message if it matches keywords."""
    # Skip if already processed
    msg_hash = hash(f"{message}")
    if msg_hash in processed:
        return None

    # Check for keywords
    message_lower = message.lower()
    matched_keywords = [kw for kw in KEYWORDS if kw in message_lower]

    if not matched_keywords:
        return None

    # Mark as processed
    processed.add(msg_hash)

    print(f"\n{'='*55}")
    print(f"  📩 NEW MESSAGE DETECTED!")
    print(f"{'='*55}")
    print(f"  From: {sender}")
    print(f"  Message: {message[:100]}{'...' if len(message) > 100 else ''}")
    print(f"  Keywords: {', '.join(matched_keywords)}")
    print(f"\n  🤖 Analyzing with AI...")

    # Analyze with AI
    analysis = analyze_with_ai(sender, message)

    # Save to vault
    filename = save_message(sender, message, analysis)

    print(f"\n  ✅ PROCESSED SUCCESSFULLY!")
    print(f"  📁 File: {filename}")
    print(f"  🎯 Intent: {analysis.get('intent', 'Unknown')}")
    print(f"  ⚡ Priority: {analysis.get('priority', 'normal')}")
    print(f"  💬 Reply: {analysis.get('suggested_reply', 'N/A')[:80]}...")
    print(f"{'='*55}\n")

    return filename


async def get_current_chat_name(page) -> str:
    """Get the name of currently open chat."""
    try:
        # Try header title
        header = await page.query_selector('header span[title]')
        if header:
            return await header.get_attribute('title') or "Unknown"

        # Try header text
        header = await page.query_selector('header')
        if header:
            text = await header.inner_text()
            lines = text.strip().split('\n')
            if lines:
                return lines[0][:30]
    except:
        pass
    return "WhatsApp Contact"


async def monitor_whatsapp():
    """Main monitoring function."""
    from playwright.async_api import async_playwright

    print("\n" + "="*55)
    print("   🟢 WHATSAPP MONITOR - OpenRouter AI")
    print("="*55)
    print(f"   Keywords: {', '.join(KEYWORDS)}")
    print(f"   AI: {'✅ Connected' if OPENAI_API_KEY else '❌ Not configured'}")
    print(f"   Save to: {VAULT_PATH}")
    print("="*55)

    async with async_playwright() as p:
        print("\n   🚀 Starting browser...")

        browser = await p.chromium.launch_persistent_context(
            user_data_dir="whatsapp_session",
            headless=False,
            viewport={'width': 1200, 'height': 800}
        )

        page = browser.pages[0] if browser.pages else await browser.new_page()

        print("   🌐 Opening WhatsApp Web...")
        await page.goto("https://web.whatsapp.com")

        print("   ⏳ Waiting for WhatsApp to load (15s)...")
        print("   📱 Scan QR code if needed\n")
        await asyncio.sleep(15)

        print("="*55)
        print("   👀 MONITORING ACTIVE - Waiting for messages...")
        print("   Press Ctrl+C to stop")
        print("="*55 + "\n")

        check_count = 0

        while True:
            try:
                check_count += 1

                # Get current chat name
                sender = await get_current_chat_name(page)

                # Get all visible messages using working selector from debug
                all_spans = await page.query_selector_all('span.selectable-text span')

                for span in all_spans:
                    try:
                        text = await span.inner_text()
                        if text and len(text.strip()) > 2:
                            process_message(sender, text.strip())
                    except:
                        pass

                # Status update every 10 checks
                if check_count % 10 == 0:
                    print(f"   [Check #{check_count}] Monitoring... ({len(all_spans)} elements found)")

                await asyncio.sleep(3)

            except KeyboardInterrupt:
                print("\n\n   👋 Stopping WhatsApp Monitor...")
                break
            except Exception as e:
                print(f"   ⚠️ Error: {e}")
                await asyncio.sleep(5)

        await browser.close()
        print("   ✅ Done. Goodbye!\n")


if __name__ == '__main__':
    try:
        asyncio.run(monitor_whatsapp())
    except KeyboardInterrupt:
        print("\n   👋 Goodbye!")
