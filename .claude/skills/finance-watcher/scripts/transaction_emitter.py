#!/usr/bin/env python3
"""
TransactionEmitter - Write transaction events to Obsidian vault.

Creates and updates accounting files in the vault:
- /Accounting/Current_Month.md - Running transaction log
- /Accounting/Subscriptions.md - Detected subscriptions
- /Needs_Action/ - Flagged transactions requiring attention
"""

from datetime import datetime
from pathlib import Path
from typing import Optional
import json
import sys

BASE_WATCHER_PATH = Path(__file__).parent.parent.parent / "base-watcher-framework" / "scripts"
if BASE_WATCHER_PATH.exists():
    sys.path.insert(0, str(BASE_WATCHER_PATH))

from base_watcher import WatcherEvent, EventType


class TransactionEmitter:
    """Emit transaction events to Obsidian vault structure."""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.accounting_dir = self.vault_path / "Accounting"
        self.needs_action = self.vault_path / "Needs_Action"
        self.accounting_dir.mkdir(parents=True, exist_ok=True)
        self.needs_action.mkdir(parents=True, exist_ok=True)

    def emit(self, event: WatcherEvent) -> Optional[Path]:
        """Process a transaction event and write to vault."""
        data = event.data
        subtype = data.get("event_subtype", "transaction")

        if event.event_type == EventType.CREATED and subtype == "transaction":
            return self._write_to_monthly_log(data)
        elif event.event_type == EventType.INFO and subtype == "subscription_detected":
            return self._write_subscription(data)
        elif event.event_type == EventType.WARNING and subtype == "large_transaction":
            return self._write_alert(data)
        elif event.event_type == EventType.ERROR:
            return self._write_error(data)
        return None

    def _write_to_monthly_log(self, data: dict) -> Path:
        """Append transaction to Current_Month.md."""
        now = datetime.now()
        month_file = self.accounting_dir / f"{now.strftime('%Y-%m')}_Transactions.md"

        # Create file with header if new
        if not month_file.exists():
            header = f"""---
type: monthly-transactions
month: {now.strftime('%Y-%m')}
last_updated: {now.isoformat()}
---

# Transactions - {now.strftime('%B %Y')}

| Date | Description | Amount | Category | Balance |
|------|-------------|--------|----------|---------|
"""
            month_file.write_text(header)

        # Append transaction row
        amount = data.get('amount', 0)
        amount_str = f"${amount:,.2f}" if amount >= 0 else f"-${abs(amount):,.2f}"
        balance = data.get('balance_after', 0)
        row = f"| {data.get('date', '')[:10]} | {data.get('description', '')} | {amount_str} | {data.get('category', '')} | ${balance:,.2f} |\n"

        with open(month_file, 'a') as f:
            f.write(row)

        # Also update Current_Month.md symlink-style summary
        self._update_current_month_summary(data)

        return month_file

    def _update_current_month_summary(self, data: dict) -> None:
        """Update the Current_Month.md summary file."""
        summary_file = self.accounting_dir / "Current_Month.md"
        now = datetime.now()

        if not summary_file.exists():
            content = f"""---
type: monthly-summary
month: {now.strftime('%Y-%m')}
last_updated: {now.isoformat()}
---

# Current Month Summary - {now.strftime('%B %Y')}

## Recent Transactions

| Date | Description | Amount | Category |
|------|-------------|--------|----------|
"""
            summary_file.write_text(content)

        amount = data.get('amount', 0)
        amount_str = f"${amount:,.2f}" if amount >= 0 else f"-${abs(amount):,.2f}"
        row = f"| {data.get('date', '')[:10]} | {data.get('description', '')} | {amount_str} | {data.get('category', '')} |\n"

        with open(summary_file, 'a') as f:
            f.write(row)

    def _write_subscription(self, data: dict) -> Path:
        """Track detected subscription in Subscriptions.md."""
        sub_file = self.accounting_dir / "Subscriptions.md"

        if not sub_file.exists():
            header = """---
type: subscription-tracker
last_updated: {now}
---

# Detected Subscriptions

| Service | Amount | Last Seen | Frequency |
|---------|--------|-----------|-----------|
""".format(now=datetime.now().isoformat())
            sub_file.write_text(header)

        amount = data.get('amount', 0)
        row = f"| {data.get('subscription_name', 'Unknown')} | ${abs(amount):,.2f} | {data.get('date', '')[:10]} | Monthly |\n"

        with open(sub_file, 'a') as f:
            f.write(row)

        return sub_file

    def _write_alert(self, data: dict) -> Path:
        """Create action file for flagged transaction."""
        tx_id = data.get('transaction_id', 'unknown')
        amount = data.get('amount', 0)
        filepath = self.needs_action / f"FINANCE_alert_{tx_id}.md"

        content = f"""---
type: finance-alert
transaction_id: {tx_id}
amount: {amount}
description: {data.get('description', '')}
date: {data.get('date', '')}
category: {data.get('category', '')}
priority: {data.get('priority', 'high')}
status: pending
created: {datetime.now().isoformat()}
---

# Finance Alert: Large Transaction

## Transaction Details

| Field | Value |
|-------|-------|
| **Amount** | ${abs(amount):,.2f} |
| **Description** | {data.get('description', '')} |
| **Date** | {data.get('date', '')[:10]} |
| **Account** | {data.get('account', '')} |
| **Category** | {data.get('category', '')} |

## Alert Reason

{data.get('alert_reason', 'Transaction exceeds threshold')}

## Required Actions

- [ ] Review transaction
- [ ] Verify this is legitimate
- [ ] Mark as reviewed when complete
"""
        filepath.write_text(content)
        return filepath

    def _write_error(self, data: dict) -> Path:
        """Log processing error."""
        error_file = self.accounting_dir / "errors.log"
        entry = f"[{datetime.now().isoformat()}] ERROR: {data.get('error', 'Unknown')} - File: {data.get('file', 'N/A')}\n"

        with open(error_file, 'a') as f:
            f.write(entry)

        return error_file
