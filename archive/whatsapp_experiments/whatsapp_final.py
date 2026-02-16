#!/usr/bin/env python3
"""
WhatsApp Monitor - Final Working Version
=========================================
Run: python whatsapp_final.py
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

KEYWORDS = ['urgent', 'help', 'asap', 'meeting', 'invoice', 'payment', 'need', 'important']
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY') or os.getenv('OPENROUTER_API_KEY')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://openrouter.ai/api/v1')

processed = set()


def analyze_with_ai(sender: str, message: str) -> dict:
    if not OPENAI_API_KEY:
        return {'intent': 'No AI', 'priority': 'normal', 'summary': message, 'suggested_reply': 'N/A'}
    try:
        headers = {'Authorization': f'Bearer {OPENAI_API_KEY}', 'Content-Type': 'application/json'}
        data = json.dumps({
            'model': 'openai/gpt-3.5-turbo',
            'messages': [{'role': 'user', 'content': f'Analyze WhatsApp message from {sender}: "{message}". Reply JSON only: {{"intent":"","priority":"urgent/high/normal/low","summary":"","suggested_reply":""}}'}],
            'max_tokens': 250
        }).encode()
        req = urllib.request.Request(f'{OPENAI_BASE_URL}/chat/completions', data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as r:
            txt = json.loads(r.read().decode())['choices'][0]['message']['content']
            if '{' in txt:
                return json.loads(txt[txt.find('{'):txt.rfind('}')+1])
    except Exception as e:
        print(f"      AI Error: {e}")
    return {'intent': 'Unknown', 'priority': 'normal', 'summary': message[:100], 'suggested_reply': 'Review manually'}


def save_message(sender: str, message: str, analysis: dict) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fn = f"wa_{ts}.md"
    (VAULT_PATH / fn).write_text(f"""---
type: whatsapp
sender: {sender}
time: {datetime.now().isoformat()}
priority: {analysis.get('priority', 'normal')}
---

# WhatsApp: {sender}

## Message
{message}

## AI Analysis
- **Intent:** {analysis.get('intent', '')}
- **Priority:** {analysis.get('priority', 'normal')}
- **Summary:** {analysis.get('summary', '')}

## Suggested Reply
{analysis.get('suggested_reply', '')}

---
- [ ] Reply sent
- [ ] Done
""", encoding='utf-8')
    return fn


async def main():
    from playwright.async_api import async_playwright

    print("\n" + "="*60)
    print("   WHATSAPP MONITOR - FINAL VERSION")
    print("="*60)
    print(f"   Keywords: {', '.join(KEYWORDS)}")
    print(f"   AI: {'YES' if OPENAI_API_KEY else 'NO'}")
    print("="*60)

    async with async_playwright() as p:
        print("\n[1] Starting browser...")

        browser = await p.chromium.launch_persistent_context(
            user_data_dir="whatsapp_session",
            headless=False,
            viewport={'width': 1280, 'height': 900}
        )

        page = browser.pages[0] if browser.pages else await browser.new_page()

        print("[2] Opening WhatsApp Web...")
        await page.goto("https://web.whatsapp.com")

        print("[3] Waiting 10 seconds for load...")
        await asyncio.sleep(10)

        print("\n" + "="*60)
        print("   👀 MONITORING STARTED")
        print("   ➡️  OPEN A CHAT to monitor messages")
        print("   Press Ctrl+C to stop")
        print("="*60 + "\n")

        count = 0

        while True:
            try:
                count += 1
                found_any = False

                # Try MULTIPLE selectors (WhatsApp changes these)
                selectors = [
                    'span.selectable-text span',
                    'div.copyable-text span',
                    'span[dir="ltr"]',
                    'div[data-pre-plain-text] span',
                    'div.message-in span.selectable-text',
                    'div._akbu span',  # WhatsApp class
                    'div[role="row"] span[dir]',
                ]

                all_texts = []

                for selector in selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        for el in elements:
                            try:
                                text = await el.inner_text()
                                if text and len(text.strip()) > 2 and text.strip() not in all_texts:
                                    all_texts.append(text.strip())
                            except:
                                pass
                    except:
                        pass

                # Also try getting text from message containers
                try:
                    messages = await page.evaluate('''() => {
                        const msgs = [];
                        document.querySelectorAll('[data-pre-plain-text]').forEach(el => {
                            const text = el.innerText;
                            if(text && text.length > 2) msgs.push(text);
                        });
                        return msgs;
                    }''')
                    for m in messages:
                        if m.strip() not in all_texts:
                            all_texts.append(m.strip())
                except:
                    pass

                if all_texts:
                    found_any = True

                # Process messages with keywords
                for text in all_texts:
                    text_lower = text.lower()
                    if any(kw in text_lower for kw in KEYWORDS):
                        msg_hash = hash(text)
                        if msg_hash not in processed:
                            processed.add(msg_hash)

                            # Get sender name
                            sender = "WhatsApp"
                            try:
                                header = await page.query_selector('header span[title]')
                                if header:
                                    sender = await header.get_attribute('title') or "WhatsApp"
                            except:
                                pass

                            print(f"\n{'*'*55}")
                            print(f"   📩 MESSAGE DETECTED!")
                            print(f"   From: {sender}")
                            print(f"   Text: {text[:80]}...")
                            print(f"   🤖 Analyzing...")

                            analysis = analyze_with_ai(sender, text)
                            filename = save_message(sender, text, analysis)

                            print(f"   ✅ Saved: {filename}")
                            print(f"   Priority: {analysis.get('priority')}")
                            print(f"   Intent: {analysis.get('intent')}")
                            print(f"{'*'*55}\n")

                # Status every 20 checks
                if count % 20 == 0:
                    status = "Found messages" if found_any else "No messages (open a chat!)"
                    print(f"   [#{count}] {status} - {len(all_texts)} texts")

                await asyncio.sleep(2)

            except KeyboardInterrupt:
                print("\n\nStopping...")
                break
            except Exception as e:
                print(f"Error: {e}")
                await asyncio.sleep(3)

        await browser.close()
        print("Done!")


if __name__ == '__main__':
    asyncio.run(main())
