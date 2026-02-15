#!/usr/bin/env python3
"""CLI for Finance Watcher skill."""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from finance_watcher import FinanceWatcher, FinanceWatcherConfig, watch_finances, SUBSCRIPTION_PATTERNS
from transaction_emitter import TransactionEmitter


def cmd_watch(args):
    """Start watching for new CSV files."""
    watcher = watch_finances(
        csv_watch_dir=args.csv_dir,
        alert_threshold=args.threshold,
        poll_interval=args.interval
    )
    emitter = TransactionEmitter(args.output)
    watcher.on_event(emitter.emit)

    print(f"Watching {args.csv_dir} for new CSV files...")
    print(f"Alert threshold: ${args.threshold:.2f}")
    print(f"Output: {args.output}")

    asyncio.run(_run_watcher(watcher))


async def _run_watcher(watcher):
    await watcher.start()
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await watcher.stop()
        print("\nWatcher stopped.")


def cmd_import_csv(args):
    """Import a specific CSV file."""
    config = FinanceWatcherConfig(
        name="import",
        csv_watch_dir=str(Path(args.file).parent)
    )
    watcher = FinanceWatcher(config)
    transactions = watcher._parse_csv(Path(args.file))

    emitter = TransactionEmitter(args.output)
    print(f"Parsed {len(transactions)} transactions from {args.file}")

    for tx in transactions:
        event = watcher._create_transaction_event(tx)
        emitter.emit(event)

        sub = watcher._detect_subscription(tx.description)
        if sub:
            from base_watcher import EventType
            sub_event = watcher._create_event(
                EventType.INFO,
                data={**event.data, "subscription_name": sub, "event_subtype": "subscription_detected"},
                source=f"finance:subscription:{tx.transaction_id}"
            )
            emitter.emit(sub_event)

        if watcher._check_alerts(tx):
            from base_watcher import EventType
            alert_event = watcher._create_event(
                EventType.WARNING,
                data={**event.data, "alert_reason": f"Amount exceeds threshold", "event_subtype": "large_transaction"},
                source=f"finance:alert:{tx.transaction_id}"
            )
            emitter.emit(alert_event)

    print(f"Written to {args.output}/Accounting/")


def cmd_analyze(args):
    """Analyze recent transactions."""
    accounting_dir = Path(args.accounting_dir)
    if not accounting_dir.exists():
        print(f"Accounting directory not found: {accounting_dir}")
        return

    print(f"Analyzing transactions in {accounting_dir}...")
    # Read all CSV files and provide summary
    total_income = 0.0
    total_expenses = 0.0
    categories = {}

    config = FinanceWatcherConfig(name="analyze", csv_watch_dir=str(accounting_dir / "imports"))
    watcher = FinanceWatcher(config)

    for csv_file in (accounting_dir / "imports").glob("*.csv"):
        for tx in watcher._parse_csv(csv_file):
            if tx.amount >= 0:
                total_income += tx.amount
            else:
                total_expenses += abs(tx.amount)
            categories[tx.category] = categories.get(tx.category, 0) + abs(tx.amount)

    print(f"\n--- Financial Summary ---")
    print(f"Total Income:   ${total_income:,.2f}")
    print(f"Total Expenses: ${total_expenses:,.2f}")
    print(f"Net:            ${total_income - total_expenses:,.2f}")
    print(f"\nBy Category:")
    for cat, amount in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"  {cat:20s} ${amount:,.2f}")


def cmd_audit_subscriptions(args):
    """Audit detected subscriptions."""
    print("Subscription Audit")
    print("=" * 50)
    print(f"\nKnown subscription patterns: {len(SUBSCRIPTION_PATTERNS)}")
    print(f"\n{'Pattern':<25} {'Service':<25}")
    print("-" * 50)
    for pattern, service in sorted(SUBSCRIPTION_PATTERNS.items()):
        print(f"{pattern:<25} {service:<25}")


def main():
    parser = argparse.ArgumentParser(description="Finance Watcher - Banking transaction monitor")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Watch command
    watch_parser = subparsers.add_parser("watch", help="Watch for new CSV files")
    watch_parser.add_argument("--csv-dir", default="./imports", help="CSV watch directory")
    watch_parser.add_argument("--output", default="./vault", help="Vault output directory")
    watch_parser.add_argument("--threshold", type=float, default=500.0, help="Alert threshold")
    watch_parser.add_argument("--interval", type=float, default=300.0, help="Poll interval (seconds)")

    # Import command
    import_parser = subparsers.add_parser("import-csv", help="Import a CSV file")
    import_parser.add_argument("--file", required=True, help="CSV file path")
    import_parser.add_argument("--output", default="./vault", help="Vault output directory")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze transactions")
    analyze_parser.add_argument("--accounting-dir", default="./vault/Accounting", help="Accounting directory")
    analyze_parser.add_argument("--days", type=int, default=30, help="Days to analyze")

    # Audit subscriptions
    audit_parser = subparsers.add_parser("audit-subscriptions", help="Audit detected subscriptions")
    audit_parser.add_argument("--accounting-dir", default="./vault/Accounting", help="Accounting directory")

    args = parser.parse_args()

    if args.command == "watch":
        cmd_watch(args)
    elif args.command == "import-csv":
        cmd_import_csv(args)
    elif args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "audit-subscriptions":
        cmd_audit_subscriptions(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
