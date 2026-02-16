#!/usr/bin/env python3
"""
WhatsApp Debug Monitor - See exactly what's happening
======================================================
Run: python whatsapp_debug.py
"""

import os
import json
import asyncio
import urllib.request
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

VAULT_PATH = Path("demo_vault/Needs_Action/WhatsApp")
VAULT_PATH.mkdir(parents=True, exist_ok=True)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY') or os.getenv('OPENROUTER_API_KEY')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://openrouter.ai/api/v1')

processed = set()


def analyze_ai(sender, message):
    if not OPENAI_API_KEY:
        return {'intent': 'No AI', 'priority': 'normal', 'summary': message, 'suggested_reply': 'Configure AI'}

    try:
        headers = {'Authorization': f'Bearer {OPENAI_API_KEY}', 'Content-Type': 'application/json'}
        data = json.dumps({
            'model': 'openai/gpt-3.5-turbo',
            'messages': [{'role': 'user', 'content': f'Analyze: From {sender}: "{message}". Reply JSON: {{"intent":"","priority":"","summary":"","suggested_reply":""}}'}],
            'max_tokens': 200
        }).encode()
        req = urllib.request.Request(f'{OPENAI_BASE_URL}/chat/completions', data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read().decode())
            txt = result['choices'][0]['message']['content']
            if '{' in txt:
                return json.loads(txt[txt.find('{'):txt.rfind('}')+1])
    except Exception as e:
        print(f"      AI Error: {e}")
    return {'intent': 'Unknown', 'priority': 'normal', 'summary': message, 'suggested_reply': 'N/A'}


def save_msg(sender, message, analysis):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fn = f"wa_{ts}.md"
    (VAULT_PATH / fn).write_text(f"""# WhatsApp: {sender}
**Time:** {datetime.now()}
**Priority:** {analysis.get('priority','normal')}

## Message
{message}

## AI Analysis
- Intent: {analysis.get('intent','')}
- Summary: {analysis.get('summary','')}
- Reply: {analysis.get('suggested_reply','')}
""", encoding='utf-8')
    return fn


async def main():
    from playwright.async_api import async_playwright

    print("\n" + "="*60)
    print("   WHATSAPP DEBUG MONITOR")
    print("="*60)

    async with async_playwright() as p:
        print("\n[1] Launching browser...")

        browser = await p.chromium.launch_persistent_context(
            user_data_dir="whatsapp_session",
            headless=False,
            viewport={'width': 1200, 'height': 800}
        )

        page = browser.pages[0] if browser.pages else await browser.new_page()

        print("[2] Opening WhatsApp Web...")
        await page.goto("https://web.whatsapp.com")

        print("[3] Waiting 15 seconds for WhatsApp to load...")
        await asyncio.sleep(15)

        print("[4] Starting message monitor loop...\n")
        print("="*60)
        print("   MONITORING - Send a message to test!")
        print("="*60)

        loop_count = 0

        while True:
            try:
                loop_count += 1
                print(f"\n--- Check #{loop_count} ---")

                # Get ALL text from page to see what's there
                all_spans = await page.query_selector_all('span.selectable-text span')
                print(f"[DEBUG] Found {len(all_spans)} text elements")

                # Show last 5 messages found
                messages_found = []
                for span in all_spans[-10:]:
                    try:
                        text = await span.inner_text()
                        if text and len(text.strip()) > 1:
                            messages_found.append(text.strip())
                    except:
                        pass

                if messages_found:
                    print(f"[DEBUG] Recent texts found:")
                    for i, m in enumerate(messages_found[-5:]):
                        print(f"        {i+1}. {m[:60]}...")

                        # Process if contains keywords
                        m_lower = m.lower()
                        if any(kw in m_lower for kw in ['help', 'urgent', 'need', 'asap']):
                            msg_hash = hash(m)
                            if msg_hash not in processed:
                                processed.add(msg_hash)
                                print(f"\n{'*'*50}")
                                print(f"   KEYWORD MATCH FOUND!")
                                print(f"   Message: {m}")
                                print(f"   Analyzing with AI...")

                                analysis = analyze_ai("WhatsApp User", m)
                                filename = save_msg("WhatsApp User", m, analysis)

                                print(f"   SAVED: {filename}")
                                print(f"   Intent: {analysis.get('intent')}")
                                print(f"   Priority: {analysis.get('priority')}")
                                print(f"{'*'*50}\n")
                else:
                    print("[DEBUG] No text messages found on screen")

                # Check for unread badge
                unread = await page.query_selector_all('[data-icon="unread-count"]')
                print(f"[DEBUG] Unread badges: {len(unread)}")

                # Check which chat is open
                try:
                    header = await page.query_selector('header')
                    if header:
                        header_text = await header.inner_text()
                        print(f"[DEBUG] Current chat header: {header_text[:50]}...")
                except:
                    print("[DEBUG] No chat open")

                print(f"[DEBUG] Waiting 5 seconds before next check...")
                await asyncio.sleep(5)

            except KeyboardInterrupt:
                print("\n\nStopping...")
                break
            except Exception as e:
                print(f"[ERROR] {e}")
                await asyncio.sleep(5)

        await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
