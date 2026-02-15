#!/usr/bin/env python3
"""
CEO Monday Morning Briefing Generator
Reads Business_Goals, Done folder, and Bank_Transactions to generate weekly briefing.
Runs automatically Sunday night or on-demand.
"""

import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

VAULT_DIR = Path(os.getenv("VAULT_DIR", "./demo_vault"))
BRIEFINGS_DIR = VAULT_DIR / "Briefings"
DONE_DIR = VAULT_DIR / "Done"
LOGS_DIR = VAULT_DIR / "Logs"

SUBSCRIPTION_PATTERNS = {
    "netflix.com": "Netflix",
    "spotify.com": "Spotify",
    "adobe.com": "Adobe Creative Cloud",
    "notion.so": "Notion",
    "slack.com": "Slack",
    "github.com": "GitHub",
    "openrouter.ai": "OpenRouter",
    "digitalocean.com": "DigitalOcean",
    "canva.com": "Canva",
    "grammarly.com": "Grammarly",
    "pictory.ai": "Pictory",
}


def read_vault_file(path):
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def get_done_tasks():
    tasks = []
    if DONE_DIR.exists():
        for f in sorted(DONE_DIR.glob("*.md")):
            tasks.append(f.stem)
    return tasks


def parse_transactions():
    content = read_vault_file(VAULT_DIR / "Accounting" / "Bank_Transactions.md")
    income = 0.0
    expenses = 0.0
    subscriptions = []

    for line in content.split("\n"):
        if "|" in line and "$" in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 4:
                try:
                    amount_str = parts[2].replace(",", "").replace("$", "").replace("+", "")
                    amount = float(amount_str)
                    desc = parts[1].lower()

                    if amount > 0:
                        income += amount
                    else:
                        expenses += abs(amount)

                    # Check subscriptions
                    for pattern, name in SUBSCRIPTION_PATTERNS.items():
                        if pattern in desc or name.lower() in desc:
                            subscriptions.append({
                                "name": name,
                                "amount": abs(amount),
                                "date": parts[0]
                            })
                except (ValueError, IndexError):
                    continue

    return income, expenses, subscriptions


def parse_business_goals():
    content = read_vault_file(VAULT_DIR / "Business_Goals.md")
    monthly_target = 10000.0
    current_mtd = 0.0

    match = re.search(r"Monthly goal: \$([0-9,]+)", content)
    if match:
        monthly_target = float(match.group(1).replace(",", ""))

    match = re.search(r"Current MTD: \$([0-9,]+)", content)
    if match:
        current_mtd = float(match.group(1).replace(",", ""))

    return monthly_target, current_mtd


def detect_unused_subscriptions(subscriptions):
    """Flag subscriptions that might be unused (for suggestion)."""
    suggestions = []
    # Simple heuristic: if subscription exists but no login signals
    known_unused = ["Notion", "Pictory", "Canva"]  # Example
    for sub in subscriptions:
        if sub["name"] in known_unused:
            suggestions.append(sub)
    return suggestions


def get_needs_action_count():
    count = 0
    needs = VAULT_DIR / "Needs_Action"
    if needs.exists():
        for subdir in needs.iterdir():
            if subdir.is_dir():
                count += len(list(subdir.glob("*.md")))
    return count


def get_log_errors():
    errors = []
    if LOGS_DIR.exists():
        for log_file in sorted(LOGS_DIR.glob("*.log"))[-7:]:  # Last 7 days
            content = log_file.read_text(encoding="utf-8")
            for line in content.split("\n"):
                if "ERROR" in line or "FATAL" in line:
                    errors.append(line.strip()[:100])
    return errors[-5:]  # Last 5 errors


def generate_briefing():
    BRIEFINGS_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    week_start = now - timedelta(days=7)
    period = f"{week_start.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}"

    # Gather data
    income, expenses, subscriptions = parse_transactions()
    monthly_target, current_mtd = parse_business_goals()
    done_tasks = get_done_tasks()
    needs_action_count = get_needs_action_count()
    unused_subs = detect_unused_subscriptions(subscriptions)
    errors = get_log_errors()

    # Revenue progress
    if monthly_target > 0:
        progress_pct = (income / monthly_target) * 100
    else:
        progress_pct = 0

    if progress_pct >= 80:
        trend = "On track"
    elif progress_pct >= 50:
        trend = "Needs attention"
    else:
        trend = "Behind target"

    # Build briefing
    filename = f"{now.strftime('%Y-%m-%d')}_Monday_Briefing.md"

    done_list = "\n".join([f"- [x] {t}" for t in done_tasks[-10:]]) if done_tasks else "- No completed tasks this week"

    sub_table = ""
    for sub in subscriptions:
        sub_table += f"| {sub['name']} | ${sub['amount']:.2f} | {sub['date']} |\n"

    suggestion_text = ""
    if unused_subs:
        suggestion_text = "\n### Cost Optimization\n"
        for sub in unused_subs:
            suggestion_text += f"- **{sub['name']}**: Low/no activity detected. Cost: ${sub['amount']:.2f}/month.\n"
            suggestion_text += f"  - [ACTION] Cancel subscription? Move to /Pending_Approval\n"

    error_text = ""
    if errors:
        error_text = "\n### System Issues\n"
        for err in errors:
            error_text += f"- {err}\n"

    content = f"""---
generated: {now.isoformat()}
period: {period}
type: ceo_briefing
---

# Monday Morning CEO Briefing

## Executive Summary
Weekly review for {period}. {trend} with revenue at {progress_pct:.0f}% of target.

## Revenue
- **This Week**: ${income:,.2f}
- **MTD**: ${current_mtd:,.2f} ({(current_mtd/monthly_target*100):.0f}% of ${monthly_target:,.2f} target)
- **Trend**: {trend}

## Expenses
- **This Week**: ${expenses:,.2f}
- **Subscriptions**: ${sum(s['amount'] for s in subscriptions):,.2f}

## Completed Tasks
{done_list}

## Pending Items
- **Needs Action**: {needs_action_count} items in queue
- **Review Required**: Check [[Needs_Action]] folder

## Subscription Audit

| Service | Cost | Last Charged |
|---------|------|-------------|
{sub_table if sub_table else "| No subscriptions detected | - | - |"}

## Proactive Suggestions
{suggestion_text if suggestion_text else "No cost optimization suggestions this week."}
{error_text}
## Upcoming Deadlines
- Review [[Business_Goals]] for project deadlines
- Monthly invoice cycle: end of month
- Quarterly tax prep: check dates

---
*Generated by AI Employee at {now.strftime('%Y-%m-%d %H:%M:%S')}*
"""

    filepath = BRIEFINGS_DIR / filename
    filepath.write_text(content, encoding="utf-8")
    print(f"CEO Briefing generated: {filepath}")

    # Log
    log_file = LOGS_DIR / f"briefing_{now.strftime('%Y%m%d')}.log"
    log_file.write_text(
        f"[{now.isoformat()}] CEO Briefing generated: {filename}\n"
        f"Revenue: ${income:,.2f}, Expenses: ${expenses:,.2f}, "
        f"Subscriptions: {len(subscriptions)}, Done tasks: {len(done_tasks)}\n",
        encoding="utf-8"
    )

    return filepath


if __name__ == "__main__":
    print("=" * 60)
    print("  CEO Monday Morning Briefing Generator")
    print("=" * 60)
    generate_briefing()
    print("Done!")
