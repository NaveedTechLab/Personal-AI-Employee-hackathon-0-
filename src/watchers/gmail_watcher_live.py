#!/usr/bin/env python3
"""
Live Gmail IMAP Watcher - Smart Email Filter + Auto Reply Draft
Polls Gmail every 60s, filters spam/ads/newsletters, creates vault action files
with auto-drafted replies for important emails.
"""

import imaplib
import email
import re
import time
import signal
import sys
import json
import os
from email.header import decode_header
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Config
IMAP_SERVER = os.getenv("EMAIL_IMAP_SERVER", "imap.gmail.com")
USERNAME = os.getenv("EMAIL_USERNAME")
PASSWORD = os.getenv("EMAIL_PASSWORD")
VAULT_DIR = Path(os.getenv("VAULT_DIR", "./demo_vault"))
POLL_INTERVAL = int(os.getenv("GMAIL_CHECK_INTERVAL", "60"))
NEEDS_ACTION = VAULT_DIR / "Needs_Action" / "Gmail"
IGNORED_DIR = VAULT_DIR / "Logs" / "ignored_emails"
LOGS_DIR = VAULT_DIR / "Logs"

# Priority keywords
HIGH_PRIORITY_KEYWORDS = ["payment", "invoice", "urgent", "critical", "overdue",
                          "deadline", "contract", "proposal", "budget", "milestone"]
NORMAL_PRIORITY_KEYWORDS = ["meeting", "schedule", "update", "review", "project",
                            "task", "follow up", "feedback", "question"]

# ============================================================
# SMART EMAIL FILTER - IGNORE LIST
# ============================================================

# No-reply senders (exact match on sender patterns)
NOREPLY_PATTERNS = [
    "noreply@", "no-reply@", "no_reply@", "donotreply@", "do-not-reply@",
    "mailer-daemon@", "postmaster@", "notifications@", "notification@",
    "alerts@", "alert@", "info@", "support@", "news@", "newsletter@",
    "marketing@", "promo@", "promotions@", "updates@", "digest@",
    "bounce@", "automated@", "auto-reply@", "system@", "admin@",
    "billing-noreply@", "accounts@", "service@",
]

# Known advertisement/newsletter domains to IGNORE
IGNORE_DOMAINS = [
    "linkedin.com", "facebookmail.com", "twitter.com", "x.com",
    "medium.com", "substack.com", "mailchimp.com", "sendgrid.net",
    "constantcontact.com", "hubspot.com", "salesforce.com",
    "amazonaws.com", "google.com", "youtube.com", "apple.com",
    "microsoft.com", "github.com", "gitlab.com", "bitbucket.org",
    "stackoverflow.com", "quora.com", "reddit.com",
    "udemy.com", "coursera.org", "skillshare.com",
    "zoom.us", "calendly.com", "eventbrite.com",
    "shopify.com", "amazon.com", "aliexpress.com",
    "paypal.com", "stripe.com",  # transactional, usually no-reply
    "notion.so", "slack.com", "trello.com", "asana.com",
    "canva.com", "figma.com", "adobe.com",
    "grammarly.com", "dropbox.com", "drive.google.com",
]

# Subject patterns to IGNORE (newsletters, promos, ads)
IGNORE_SUBJECT_PATTERNS = [
    r"unsubscribe",
    r"newsletter",
    r"weekly digest",
    r"daily digest",
    r"your .* summary",
    r"new sign-in",
    r"security alert",
    r"verify your",
    r"confirm your",
    r"reset your password",
    r"welcome to",
    r"getting started",
    r"thank you for signing up",
    r"subscription confirmed",
    r"order confirmation",
    r"shipping notification",
    r"delivery update",
    r"tracking number",
    r"your receipt",
    r"your order",
    r"promotional",
    r"limited time",
    r"% off",
    r"flash sale",
    r"exclusive offer",
    r"don.t miss",
    r"act now",
    r"last chance",
    r"free trial",
    r"upgrade your",
    r"you.re invited",
    r"webinar",
    r"join us",
    r"event reminder",
    r"daily report",
    r"automated report",
    r"notification:",
    r"alert:",
]

# Body patterns indicating auto-generated / no-reply email
IGNORE_BODY_PATTERNS = [
    "unsubscribe", "opt out", "opt-out", "manage preferences",
    "email preferences", "update your preferences",
    "this is an automated", "this is an automatic",
    "do not reply to this email", "please do not reply",
    "this email was sent by", "you are receiving this",
    "you received this email because", "this is a notification",
    "view in browser", "view online", "view this email",
    "add us to your address book",
]

# ============================================================
# WHITELIST - Always process these (override ignore)
# ============================================================
WHITELIST_DOMAINS = [
    # Add your client domains here
    # "clientcompany.com",
    # "importantpartner.com",
]

WHITELIST_SENDERS = [
    # Add specific important sender emails here
    # "boss@company.com",
    # "client@business.com",
]

# Track seen message IDs
SEEN_FILE = VAULT_DIR / ".gmail_seen_ids.json"
seen_ids = set()
running = True

# Stats
stats = {"total": 0, "important": 0, "normal": 0, "ignored": 0}


def signal_handler(sig, frame):
    global running
    print("\n[Gmail Watcher] Shutting down gracefully...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def load_seen_ids():
    global seen_ids
    if SEEN_FILE.exists():
        try:
            seen_ids = set(json.loads(SEEN_FILE.read_text(encoding="utf-8")))
        except Exception:
            seen_ids = set()


def save_seen_ids():
    trimmed = list(seen_ids)[-1000:]
    SEEN_FILE.write_text(json.dumps(trimmed), encoding="utf-8")


def decode_header_value(value):
    if value is None:
        return ""
    decoded_parts = decode_header(value)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or "utf-8", errors="ignore"))
        else:
            result.append(part)
    return " ".join(result)


def extract_email_address(sender_str):
    """Extract just the email address from sender string."""
    match = re.search(r'<([^>]+)>', sender_str)
    if match:
        return match.group(1).lower()
    # Might be just an email without angle brackets
    match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', sender_str)
    if match:
        return match.group(0).lower()
    return sender_str.lower()


def extract_sender_name(sender_str):
    """Extract display name from sender."""
    match = re.match(r'^"?([^"<]+)"?\s*<', sender_str)
    if match:
        return match.group(1).strip()
    return sender_str.split("@")[0]


def get_sender_domain(email_addr):
    """Get domain from email address."""
    parts = email_addr.split("@")
    return parts[1] if len(parts) > 1 else ""


# ============================================================
# SMART FILTER ENGINE
# ============================================================

def classify_email(sender, subject, body):
    """
    Classify email into: IMPORTANT, NORMAL, or IGNORE
    Returns: (classification, reason)
    """
    email_addr = extract_email_address(sender)
    domain = get_sender_domain(email_addr)
    subject_lower = subject.lower()
    body_lower = body.lower()

    # --- WHITELIST CHECK (always process) ---
    if email_addr in [w.lower() for w in WHITELIST_SENDERS]:
        return "IMPORTANT", "whitelisted_sender"

    if domain in WHITELIST_DOMAINS:
        return "IMPORTANT", "whitelisted_domain"

    # --- NO-REPLY CHECK ---
    for pattern in NOREPLY_PATTERNS:
        if pattern in email_addr:
            return "IGNORE", f"noreply_sender ({pattern})"

    # --- DOMAIN IGNORE CHECK ---
    if domain in IGNORE_DOMAINS:
        return "IGNORE", f"ignored_domain ({domain})"

    # --- SUBJECT PATTERN IGNORE ---
    for pattern in IGNORE_SUBJECT_PATTERNS:
        if re.search(pattern, subject_lower):
            return "IGNORE", f"subject_pattern ({pattern})"

    # --- BODY PATTERN IGNORE ---
    ignore_score = 0
    for pattern in IGNORE_BODY_PATTERNS:
        if pattern in body_lower:
            ignore_score += 1
    if ignore_score >= 2:
        return "IGNORE", f"body_patterns (score={ignore_score})"

    # --- PRIORITY KEYWORDS (HIGH) ---
    for kw in HIGH_PRIORITY_KEYWORDS:
        if kw in subject_lower or kw in body_lower:
            return "IMPORTANT", f"high_priority_keyword ({kw})"

    # --- NORMAL KEYWORDS ---
    for kw in NORMAL_PRIORITY_KEYWORDS:
        if kw in subject_lower or kw in body_lower:
            return "NORMAL", f"normal_keyword ({kw})"

    # --- DEFAULT: If it passed all ignore filters, it's probably a real person ---
    # Check if it looks like a personal email (short subject, no unsubscribe)
    if len(subject) < 100 and "unsubscribe" not in body_lower:
        return "NORMAL", "personal_email"

    return "IGNORE", "default_filter"


def get_priority(classification, subject, sender):
    """Get display priority based on classification."""
    if classification == "IMPORTANT":
        return "HIGH"
    text = (subject + " " + sender).lower()
    for kw in HIGH_PRIORITY_KEYWORDS:
        if kw in text:
            return "HIGH"
    return "normal"


# ============================================================
# AUTO REPLY DRAFT GENERATOR
# ============================================================

def generate_reply_draft(subject, sender, body, classification):
    """Generate a smart reply draft based on email content."""
    sender_name = extract_sender_name(sender)
    subject_lower = subject.lower()
    body_lower = body.lower()

    # Detect email type and generate appropriate reply
    if "invoice" in subject_lower or "invoice" in body_lower:
        reply = f"""Dear {sender_name},

Thank you for sending the invoice. I have received it and will review the details.

I will process the payment within the standard payment terms. If there are any discrepancies, I will reach out to you directly.

Best regards"""

    elif "payment" in subject_lower or "payment" in body_lower:
        reply = f"""Dear {sender_name},

Thank you for the payment notification. I have noted this and will verify it against our records.

I will confirm receipt once the payment has been reconciled.

Best regards"""

    elif "meeting" in subject_lower or "schedule" in body_lower or "calendar" in body_lower:
        reply = f"""Dear {sender_name},

Thank you for reaching out regarding the meeting. Let me check my availability and I will confirm the schedule shortly.

Best regards"""

    elif "proposal" in subject_lower or "proposal" in body_lower:
        reply = f"""Dear {sender_name},

Thank you for the proposal. I have received it and will review the details carefully.

I will get back to you with my feedback within the next few business days.

Best regards"""

    elif "urgent" in subject_lower or "asap" in subject_lower or "critical" in body_lower:
        reply = f"""Dear {sender_name},

Thank you for flagging this as urgent. I have received your message and will prioritize this matter.

I will respond with a detailed update as soon as possible.

Best regards"""

    elif "project" in subject_lower or "milestone" in body_lower or "deadline" in body_lower:
        reply = f"""Dear {sender_name},

Thank you for the project update. I have reviewed the information provided.

I will follow up with any questions or next steps shortly.

Best regards"""

    elif "question" in subject_lower or "?" in subject:
        reply = f"""Dear {sender_name},

Thank you for your question. I have received your email and will look into this.

I will get back to you with a detailed response shortly.

Best regards"""

    elif "follow" in subject_lower or "following up" in body_lower:
        reply = f"""Dear {sender_name},

Thank you for following up. I appreciate your patience.

I am reviewing this and will provide an update shortly.

Best regards"""

    else:
        reply = f"""Dear {sender_name},

Thank you for your email. I have received your message and will review it.

I will get back to you shortly.

Best regards"""

    return reply


# ============================================================
# VAULT FILE CREATOR
# ============================================================

def get_body_preview(msg, max_len=500):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                except Exception:
                    pass
                break
    else:
        try:
            body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
        except Exception:
            pass
    body = body.strip()
    if len(body) > max_len:
        body = body[:max_len] + "..."
    return body


def create_vault_file(subject, sender, date_str, body, priority, msg_id,
                      classification, reason, reply_draft=""):
    """Create action file with smart classification and reply draft."""
    safe_subject = re.sub(r"[^a-zA-Z0-9 ]", "", subject)[:40].strip().replace(" ", "_")
    if not safe_subject:
        safe_subject = "no_subject"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"EMAIL_{timestamp}_{safe_subject}.md"

    content = f"""---
type: email_action
source: gmail
priority: {priority}
classification: {classification}
filter_reason: {reason}
status: needs_action
message_id: "{msg_id}"
created: {datetime.now().isoformat()}
---

# Email: {subject}

| Field | Value |
|-------|-------|
| **From** | {sender} |
| **Subject** | {subject} |
| **Date** | {date_str} |
| **Priority** | {priority} |
| **Classification** | {classification} |

## Email Body
{body[:800] if body else "(No body)"}

## Draft Reply
> Review and edit this draft before approving. Move to `Approved/` to send.

```
{reply_draft}
```

## Actions
- [ ] Review email content
- [ ] Edit draft reply if needed
- [ ] Move to `Approved/` to send reply
- [ ] Or move to `Done/` if no reply needed

> Detected by Gmail Watcher at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> Filter: {classification} ({reason})
"""

    filepath = NEEDS_ACTION / filename
    filepath.write_text(content, encoding="utf-8")
    return filepath


def log_ignored_email(subject, sender, reason):
    """Log ignored emails for audit purposes."""
    IGNORED_DIR.mkdir(parents=True, exist_ok=True)
    log_file = IGNORED_DIR / f"ignored_{datetime.now().strftime('%Y%m%d')}.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] IGNORED | {reason} | {sender} | {subject}\n")


def log_activity(action, details=""):
    log_file = LOGS_DIR / f"gmail_watcher_{datetime.now().strftime('%Y%m%d')}.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {action}: {details}\n")


def update_dashboard_email_count(count):
    """Update Dashboard.md with latest email count."""
    dashboard = VAULT_DIR / "Dashboard.md"
    if dashboard.exists():
        content = dashboard.read_text(encoding="utf-8")
        icon = "🔴" if count > 0 else "✅"
        new_line = f"- {icon} {count} unread important emails in [[Needs_Action/Gmail]]"
        content = re.sub(
            r"- [🔴✅🟡] \d+ unread important emails in \[\[Needs_Action/Gmail\]\]",
            new_line,
            content
        )
        content = re.sub(
            r"- Last checked: .*",
            f"- Last checked: {datetime.now().strftime('%H:%M:%S')}",
            content
        )
        dashboard.write_text(content, encoding="utf-8")


# ============================================================
# MAIN POLL LOOP
# ============================================================

def poll_gmail():
    global seen_ids
    new_count = 0
    ignored_count = 0

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(USERNAME, PASSWORD)
        mail.select("inbox")

        # Get unread emails
        status, messages = mail.search(None, "UNSEEN")
        if status != "OK":
            log_activity("ERROR", "Failed to search inbox")
            return 0, 0

        email_ids = messages[0].split()

        for eid in email_ids:
            eid_str = eid.decode()
            if eid_str in seen_ids:
                continue

            status, msg_data = mail.fetch(eid, "(RFC822)")
            if status != "OK":
                continue

            msg = email.message_from_bytes(msg_data[0][1])
            subject = decode_header_value(msg["Subject"])
            sender = decode_header_value(msg["From"])
            date_str = msg.get("Date", "")
            msg_id = msg.get("Message-ID", eid_str)
            body = get_body_preview(msg)

            # SMART FILTER
            classification, reason = classify_email(sender, subject, body)
            stats["total"] += 1

            if classification == "IGNORE":
                # Skip this email - just log it
                stats["ignored"] += 1
                ignored_count += 1
                log_ignored_email(subject, sender, reason)
                log_activity("IGNORED", f"{reason} | {sender} | {subject[:50]}")
                print(f"  [SKIP] {sender[:30]} - {subject[:40]} ({reason})")
                seen_ids.add(eid_str)
                continue

            # IMPORTANT or NORMAL - process it
            priority = get_priority(classification, subject, sender)

            if classification == "IMPORTANT":
                stats["important"] += 1
            else:
                stats["normal"] += 1

            # Generate reply draft
            reply_draft = generate_reply_draft(subject, sender, body, classification)

            filepath = create_vault_file(
                subject, sender, date_str, body, priority,
                msg_id, classification, reason, reply_draft
            )
            seen_ids.add(eid_str)
            new_count += 1

            icon = "🔴" if classification == "IMPORTANT" else "📧"
            print(f"  {icon} [{classification}] {sender[:30]} - {subject[:50]}")
            log_activity("NEW_EMAIL", f"[{classification}] {sender} - {subject}")

        mail.logout()

        # Update dashboard
        gmail_files = list(NEEDS_ACTION.glob("EMAIL_*.md"))
        update_dashboard_email_count(len(gmail_files))

        return new_count, ignored_count

    except imaplib.IMAP4.error as e:
        log_activity("IMAP_ERROR", str(e))
        print(f"  [ERROR] IMAP: {e}")
        return 0, 0
    except Exception as e:
        log_activity("ERROR", str(e))
        print(f"  [ERROR] {e}")
        return 0, 0


def main():
    # Ensure directories
    NEEDS_ACTION.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    IGNORED_DIR.mkdir(parents=True, exist_ok=True)

    load_seen_ids()

    print("=" * 60)
    print("  Gmail Watcher - SMART FILTER MODE")
    print(f"  Account: {USERNAME}")
    print(f"  Poll Interval: {POLL_INTERVAL}s")
    print(f"  Vault: {VAULT_DIR}")
    print(f"  Ignore Domains: {len(IGNORE_DOMAINS)}")
    print(f"  Ignore Subject Patterns: {len(IGNORE_SUBJECT_PATTERNS)}")
    print(f"  No-Reply Patterns: {len(NOREPLY_PATTERNS)}")
    print("  Filter: IMPORTANT/NORMAL = process + draft reply")
    print("  Filter: IGNORE = skip (logged in Logs/ignored_emails/)")
    print("=" * 60)
    print()

    cycle = 0
    while running:
        cycle += 1
        now = datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] Poll #{cycle}...", end=" ")

        new, ignored = poll_gmail()
        save_seen_ids()

        if new > 0 or ignored > 0:
            print(f"=> {new} actionable, {ignored} ignored "
                  f"(total: {stats['important']} important, "
                  f"{stats['normal']} normal, {stats['ignored']} ignored)")
        else:
            print("=> No new emails")

        # Wait for next poll
        for _ in range(POLL_INTERVAL):
            if not running:
                break
            time.sleep(1)

    save_seen_ids()
    print(f"\n[Gmail Watcher] Final Stats: {stats}")
    print("[Gmail Watcher] Stopped.")


if __name__ == "__main__":
    main()
