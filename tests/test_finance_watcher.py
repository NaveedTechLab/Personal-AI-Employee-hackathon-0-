#!/usr/bin/env python3
"""Tests for Finance/Banking Watcher skill."""

import pytest
import json
import tempfile
import csv
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock
import sys

# Add skills to path
SKILLS_PATH = Path(__file__).parent / ".claude" / "skills"
sys.path.insert(0, str(SKILLS_PATH / "base-watcher-framework" / "scripts"))
sys.path.insert(0, str(SKILLS_PATH / "finance-watcher" / "scripts"))


class TestTransactionData:
    """Test TransactionData dataclass."""

    def test_create_transaction(self):
        from finance_watcher import TransactionData
        tx = TransactionData(
            transaction_id="TX001",
            date=datetime.now(),
            description="Netflix Monthly",
            amount=-15.99,
            currency="USD",
            category="subscription",
            account="checking",
            balance_after=1500.00,
            is_debit=True,
            raw_data={}
        )
        assert tx.transaction_id == "TX001"
        assert tx.is_debit is True
        assert tx.amount == -15.99

    def test_transaction_fields(self):
        from finance_watcher import TransactionData
        tx = TransactionData(
            transaction_id="TX002",
            date=datetime.now(),
            description="Client Payment",
            amount=2500.00,
            currency="USD",
            category="income",
            account="business",
            balance_after=5000.00,
            is_debit=False,
            raw_data={"ref": "INV-001"}
        )
        assert tx.amount > 0
        assert tx.is_debit is False
        assert tx.category == "income"


class TestFinanceWatcherConfig:
    """Test FinanceWatcherConfig."""

    def test_default_config(self):
        from finance_watcher import FinanceWatcherConfig
        config = FinanceWatcherConfig(name="test-finance")
        assert config.alert_threshold == 500.0
        assert config.poll_interval == 300.0
        assert isinstance(config.subscription_patterns, dict)

    def test_custom_config(self):
        from finance_watcher import FinanceWatcherConfig
        config = FinanceWatcherConfig(
            name="test-finance",
            alert_threshold=1000.0,
            poll_interval=60.0,
            csv_watch_dir="/tmp/bank_imports"
        )
        assert config.alert_threshold == 1000.0
        assert config.csv_watch_dir == "/tmp/bank_imports"


class TestSubscriptionDetection:
    """Test subscription pattern matching."""

    def test_detect_netflix(self):
        from finance_watcher import SUBSCRIPTION_PATTERNS
        assert "netflix.com" in SUBSCRIPTION_PATTERNS or "netflix" in str(SUBSCRIPTION_PATTERNS).lower()

    def test_detect_spotify(self):
        from finance_watcher import SUBSCRIPTION_PATTERNS
        assert "spotify" in str(SUBSCRIPTION_PATTERNS).lower()

    def test_detect_adobe(self):
        from finance_watcher import SUBSCRIPTION_PATTERNS
        assert "adobe" in str(SUBSCRIPTION_PATTERNS).lower()


class TestCSVParsing:
    """Test CSV file parsing."""

    def test_parse_basic_csv(self):
        from finance_watcher import FinanceWatcher, FinanceWatcherConfig
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Description", "Amount", "Balance"])
            writer.writerow(["2026-01-15", "Netflix Monthly", "-15.99", "1500.00"])
            writer.writerow(["2026-01-14", "Salary Deposit", "5000.00", "1515.99"])
            f.flush()

            config = FinanceWatcherConfig(
                name="test",
                csv_watch_dir=str(Path(f.name).parent)
            )
            watcher = FinanceWatcher(config)
            transactions = watcher._parse_csv(Path(f.name))

            assert len(transactions) == 2
            assert transactions[0].description == "Netflix Monthly"
            assert transactions[0].amount == -15.99

    def test_empty_csv(self):
        from finance_watcher import FinanceWatcher, FinanceWatcherConfig
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Description", "Amount", "Balance"])
            f.flush()

            config = FinanceWatcherConfig(name="test", csv_watch_dir=str(Path(f.name).parent))
            watcher = FinanceWatcher(config)
            transactions = watcher._parse_csv(Path(f.name))
            assert len(transactions) == 0


class TestAlertThresholds:
    """Test transaction alert logic."""

    def test_large_transaction_flagged(self):
        from finance_watcher import FinanceWatcher, FinanceWatcherConfig, TransactionData
        config = FinanceWatcherConfig(name="test", alert_threshold=500.0)
        watcher = FinanceWatcher(config)
        tx = TransactionData(
            transaction_id="TX003",
            date=datetime.now(),
            description="Large Purchase",
            amount=-750.00,
            currency="USD",
            category="uncategorized",
            account="checking",
            balance_after=500.00,
            is_debit=True,
            raw_data={}
        )
        assert watcher._check_alerts(tx) is True

    def test_small_transaction_not_flagged(self):
        from finance_watcher import FinanceWatcher, FinanceWatcherConfig, TransactionData
        config = FinanceWatcherConfig(name="test", alert_threshold=500.0)
        watcher = FinanceWatcher(config)
        tx = TransactionData(
            transaction_id="TX004",
            date=datetime.now(),
            description="Coffee",
            amount=-4.50,
            currency="USD",
            category="food",
            account="checking",
            balance_after=1500.00,
            is_debit=True,
            raw_data={}
        )
        assert watcher._check_alerts(tx) is False


class TestTransactionCategorization:
    """Test auto-categorization."""

    def test_categorize_subscription(self):
        from finance_watcher import FinanceWatcher, FinanceWatcherConfig
        config = FinanceWatcherConfig(name="test")
        watcher = FinanceWatcher(config)
        category = watcher._categorize_transaction("NETFLIX.COM Monthly Charge")
        assert category == "subscription"

    def test_categorize_unknown(self):
        from finance_watcher import FinanceWatcher, FinanceWatcherConfig
        config = FinanceWatcherConfig(name="test")
        watcher = FinanceWatcher(config)
        category = watcher._categorize_transaction("Random Store Purchase XYZ123")
        assert category == "uncategorized"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
