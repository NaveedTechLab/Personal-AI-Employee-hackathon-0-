#!/usr/bin/env python3
"""
FinanceWatcher - Monitor banking transactions from CSV files and APIs.

Extends BaseWatcher to detect new CSV imports, parse transactions,
identify subscriptions, and flag large or unusual transactions.
"""

import csv
import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from pathlib import Path
import sys
import json

# Add base-watcher-framework to path
BASE_WATCHER_PATH = Path(__file__).parent.parent.parent / "base-watcher-framework" / "scripts"
if BASE_WATCHER_PATH.exists():
    sys.path.insert(0, str(BASE_WATCHER_PATH))

from base_watcher import BaseWatcher, WatcherConfig, WatcherEvent, EventType

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


# Subscription detection patterns (from hackathon doc)
SUBSCRIPTION_PATTERNS = {
    'netflix.com': 'Netflix',
    'netflix': 'Netflix',
    'spotify.com': 'Spotify',
    'spotify': 'Spotify',
    'adobe.com': 'Adobe Creative Cloud',
    'adobe': 'Adobe Creative Cloud',
    'notion.so': 'Notion',
    'notion': 'Notion',
    'slack.com': 'Slack',
    'slack': 'Slack',
    'github.com': 'GitHub',
    'github': 'GitHub',
    'aws.amazon': 'AWS',
    'amazon web': 'AWS',
    'google storage': 'Google Cloud',
    'digitalocean': 'DigitalOcean',
    'heroku': 'Heroku',
    'openai': 'OpenAI',
    'anthropic': 'Anthropic',
    'microsoft 365': 'Microsoft 365',
    'office 365': 'Microsoft 365',
    'zoom.us': 'Zoom',
    'zoom': 'Zoom',
    'dropbox': 'Dropbox',
    'canva': 'Canva',
    'figma': 'Figma',
    'vercel': 'Vercel',
}

# Transaction categorization patterns
CATEGORY_PATTERNS = {
    'subscription': ['netflix', 'spotify', 'adobe', 'notion', 'slack', 'github', 'aws', 'heroku', 'zoom', 'dropbox'],
    'food': ['restaurant', 'cafe', 'coffee', 'uber eats', 'doordash', 'grubhub', 'mcdonald', 'starbucks'],
    'transport': ['uber', 'lyft', 'gas station', 'fuel', 'parking', 'transit'],
    'utilities': ['electric', 'water', 'internet', 'phone', 'mobile', 'verizon', 'at&t', 't-mobile'],
    'shopping': ['amazon', 'walmart', 'target', 'ebay', 'shopify'],
    'finance': ['invoice', 'payment', 'transfer', 'wire', 'payroll', 'salary', 'deposit'],
    'health': ['pharmacy', 'hospital', 'doctor', 'dental', 'medical', 'insurance'],
    'entertainment': ['steam', 'playstation', 'xbox', 'cinema', 'theater', 'concert'],
}


@dataclass
class TransactionData:
    """Parsed transaction data structure."""
    transaction_id: str
    date: datetime
    description: str
    amount: float
    currency: str
    category: str
    account: str
    balance_after: float
    is_debit: bool
    raw_data: dict


@dataclass
class FinanceWatcherConfig(WatcherConfig):
    """
    Configuration for FinanceWatcher.

    Attributes:
        csv_watch_dir: Directory to watch for new CSV files
        bank_api_url: Optional banking API endpoint
        bank_api_token: Optional API authentication token
        alert_threshold: Flag transactions above this amount
        subscription_patterns: Pattern-to-name mapping for subscriptions
        transaction_categories: Description-to-category mapping
        processed_state_file: File to track processed transactions
    """
    csv_watch_dir: str = "./imports"
    bank_api_url: Optional[str] = None
    bank_api_token: Optional[str] = None
    alert_threshold: float = 500.0
    subscription_patterns: dict = field(default_factory=lambda: dict(SUBSCRIPTION_PATTERNS))
    transaction_categories: dict = field(default_factory=lambda: dict(CATEGORY_PATTERNS))
    processed_state_file: str = ".finance_watcher_state.json"
    poll_interval: float = 300.0
    currency: str = "USD"
    account_name: str = "primary"


class FinanceWatcher(BaseWatcher):
    """
    Watcher that monitors banking transactions from CSV files.

    Extends BaseWatcher to integrate with WatcherRegistry and emitters.
    Parses CSV bank exports, detects subscriptions, and flags large transactions.

    Example:
        config = FinanceWatcherConfig(
            name="finance-watcher",
            csv_watch_dir="./bank_imports",
            alert_threshold=500.0,
            poll_interval=300.0
        )

        watcher = FinanceWatcher(config)
        watcher.on_event(lambda e: print(f"Transaction: {e.data['description']}"))

        await watcher.start()
    """

    def __init__(self, config: FinanceWatcherConfig):
        super().__init__(config)
        self.finance_config = config
        self._processed_files: set = set()
        self._processed_tx_ids: set = set()
        self._state_path: Optional[Path] = None

    async def _setup(self) -> None:
        """Initialize CSV directory watching and load state."""
        csv_dir = Path(self.finance_config.csv_watch_dir)
        csv_dir.mkdir(parents=True, exist_ok=True)

        # Load processed state
        self._state_path = csv_dir / self.finance_config.processed_state_file
        if self._state_path.exists():
            try:
                state = json.loads(self._state_path.read_text())
                self._processed_files = set(state.get("files", []))
                self._processed_tx_ids = set(state.get("transaction_ids", []))
            except (json.JSONDecodeError, KeyError):
                self._processed_files = set()
                self._processed_tx_ids = set()

    async def _teardown(self) -> None:
        """Save state on shutdown."""
        self._save_state()

    async def _poll(self) -> list[WatcherEvent]:
        """Poll for new CSV files and parse transactions."""
        events = []
        csv_dir = Path(self.finance_config.csv_watch_dir)

        if not csv_dir.exists():
            return events

        # Find new CSV files
        for csv_file in sorted(csv_dir.glob("*.csv")):
            file_key = f"{csv_file.name}:{csv_file.stat().st_mtime}"
            if file_key in self._processed_files:
                continue

            try:
                transactions = self._parse_csv(csv_file)
                for tx in transactions:
                    if tx.transaction_id in self._processed_tx_ids:
                        continue

                    # Create event for each new transaction
                    event = self._create_transaction_event(tx)
                    events.append(event)

                    # Check for subscription
                    sub_name = self._detect_subscription(tx.description)
                    if sub_name:
                        events.append(self._create_event(
                            EventType.INFO,
                            data={
                                **event.data,
                                "subscription_name": sub_name,
                                "event_subtype": "subscription_detected"
                            },
                            source=f"finance:subscription:{tx.transaction_id}"
                        ))

                    # Check for alert threshold
                    if self._check_alerts(tx):
                        events.append(self._create_event(
                            EventType.WARNING,
                            data={
                                **event.data,
                                "alert_reason": f"Amount ${abs(tx.amount):.2f} exceeds threshold ${self.finance_config.alert_threshold:.2f}",
                                "event_subtype": "large_transaction"
                            },
                            source=f"finance:alert:{tx.transaction_id}"
                        ))

                    self._processed_tx_ids.add(tx.transaction_id)

                self._processed_files.add(file_key)

            except Exception as e:
                events.append(self._create_event(
                    EventType.ERROR,
                    data={"error": str(e), "file": str(csv_file)},
                    source=f"finance:error:{csv_file.name}"
                ))

        # Save state after processing
        self._save_state()
        return events

    def _parse_csv(self, csv_path: Path) -> list[TransactionData]:
        """Parse a bank CSV file into TransactionData objects."""
        transactions = []

        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            if not reader.fieldnames:
                return transactions

            # Normalize column names
            col_map = self._detect_columns(reader.fieldnames)

            for row_num, row in enumerate(reader):
                try:
                    # Parse date
                    date_str = row.get(col_map.get('date', ''), '').strip()
                    tx_date = self._parse_date(date_str)

                    # Parse amount
                    amount_str = row.get(col_map.get('amount', ''), '0').strip()
                    amount = self._parse_amount(amount_str)

                    # Parse description
                    description = row.get(col_map.get('description', ''), '').strip()

                    # Parse balance
                    balance_str = row.get(col_map.get('balance', ''), '0').strip()
                    balance = self._parse_amount(balance_str)

                    # Generate transaction ID
                    tx_id = hashlib.md5(
                        f"{date_str}:{description}:{amount}:{row_num}".encode()
                    ).hexdigest()[:12]

                    # Categorize
                    category = self._categorize_transaction(description)

                    transactions.append(TransactionData(
                        transaction_id=tx_id,
                        date=tx_date,
                        description=description,
                        amount=amount,
                        currency=self.finance_config.currency,
                        category=category,
                        account=self.finance_config.account_name,
                        balance_after=balance,
                        is_debit=amount < 0,
                        raw_data=dict(row)
                    ))

                except (ValueError, KeyError) as e:
                    continue  # Skip malformed rows

        return transactions

    def _detect_columns(self, fieldnames: list) -> dict:
        """Auto-detect CSV column mapping."""
        col_map = {}
        normalized = {f.lower().strip(): f for f in fieldnames}

        # Date column
        for key in ['date', 'transaction date', 'trans date', 'posted date', 'booking date']:
            if key in normalized:
                col_map['date'] = normalized[key]
                break

        # Description column
        for key in ['description', 'memo', 'narrative', 'details', 'transaction description', 'payee']:
            if key in normalized:
                col_map['description'] = normalized[key]
                break

        # Amount column
        for key in ['amount', 'transaction amount', 'value', 'debit/credit']:
            if key in normalized:
                col_map['amount'] = normalized[key]
                break

        # Balance column
        for key in ['balance', 'running balance', 'available balance', 'closing balance']:
            if key in normalized:
                col_map['balance'] = normalized[key]
                break

        return col_map

    def _parse_date(self, date_str: str) -> datetime:
        """Parse various date formats."""
        formats = [
            '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y',
            '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M',
            '%d-%m-%Y', '%d %b %Y', '%b %d, %Y',
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return datetime.now()

    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string, handling various formats."""
        if not amount_str:
            return 0.0
        # Remove currency symbols and whitespace
        cleaned = re.sub(r'[£$€¥₹,\s]', '', amount_str)
        # Handle parentheses as negative
        if cleaned.startswith('(') and cleaned.endswith(')'):
            cleaned = '-' + cleaned[1:-1]
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def _categorize_transaction(self, description: str) -> str:
        """Categorize transaction based on description patterns."""
        desc_lower = description.lower()

        # Check subscription patterns first
        for pattern in self.finance_config.subscription_patterns:
            if pattern.lower() in desc_lower:
                return "subscription"

        # Check category patterns
        for category, patterns in self.finance_config.transaction_categories.items():
            for pattern in patterns:
                if pattern.lower() in desc_lower:
                    return category

        return "uncategorized"

    def _detect_subscription(self, description: str) -> Optional[str]:
        """Detect if transaction is a subscription. Returns service name or None."""
        desc_lower = description.lower()
        for pattern, name in self.finance_config.subscription_patterns.items():
            if pattern.lower() in desc_lower:
                return name
        return None

    def _check_alerts(self, tx: TransactionData) -> bool:
        """Check if transaction should trigger an alert."""
        return abs(tx.amount) >= self.finance_config.alert_threshold

    def _create_transaction_event(self, tx: TransactionData) -> WatcherEvent:
        """Create event from transaction data."""
        priority = "normal"
        if abs(tx.amount) >= self.finance_config.alert_threshold:
            priority = "high"
        if abs(tx.amount) >= self.finance_config.alert_threshold * 2:
            priority = "urgent"

        return self._create_event(
            EventType.CREATED,
            data={
                "transaction_id": tx.transaction_id,
                "date": tx.date.isoformat(),
                "description": tx.description,
                "amount": tx.amount,
                "currency": tx.currency,
                "category": tx.category,
                "account": tx.account,
                "balance_after": tx.balance_after,
                "is_debit": tx.is_debit,
                "priority": priority,
                "event_subtype": "transaction"
            },
            source=f"finance:{tx.transaction_id}",
            priority=priority
        )

    def _save_state(self) -> None:
        """Persist processed state to disk."""
        if self._state_path:
            state = {
                "files": list(self._processed_files),
                "transaction_ids": list(self._processed_tx_ids),
                "last_updated": datetime.now().isoformat()
            }
            self._state_path.write_text(json.dumps(state, indent=2))


def analyze_transaction(transaction: dict) -> Optional[dict]:
    """
    Analyze a single transaction for subscription patterns.
    From hackathon doc specification.
    """
    for pattern, name in SUBSCRIPTION_PATTERNS.items():
        if pattern in transaction.get('description', '').lower():
            return {
                'type': 'subscription',
                'name': name,
                'amount': transaction.get('amount'),
                'date': transaction.get('date')
            }
    return None


def watch_finances(
    csv_watch_dir: str = "./imports",
    alert_threshold: float = 500.0,
    poll_interval: float = 300.0
) -> FinanceWatcher:
    """
    Create a FinanceWatcher with common defaults.

    Args:
        csv_watch_dir: Directory to monitor for CSV bank exports
        alert_threshold: Flag transactions above this amount
        poll_interval: Seconds between polls

    Returns:
        Configured FinanceWatcher instance
    """
    config = FinanceWatcherConfig(
        name="finance-watcher",
        csv_watch_dir=csv_watch_dir,
        alert_threshold=alert_threshold,
        poll_interval=poll_interval
    )
    return FinanceWatcher(config)
