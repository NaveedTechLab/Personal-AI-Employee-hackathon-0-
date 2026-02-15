"""
Base Watcher Class Template for Phase 2 - Functional Assistant (Silver Tier)

Defines the common interface and functionality for all watchers.
"""

import abc
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from vault_manager import vault_manager


class BaseWatcher(abc.ABC):
    """Abstract base class for all watchers in the system."""

    def __init__(self, name: str, poll_interval: int = 60):
        """
        Initialize the watcher.

        Args:
            name: Name of the watcher (e.g., 'email', 'filesystem')
            poll_interval: Interval in seconds between checks
        """
        self.name = name
        self.poll_interval = poll_interval
        self.last_check = None
        self.is_running = False

    @abc.abstractmethod
    def check_for_updates(self) -> list:
        """
        Check the source for new items.

        Returns:
            List of items that need processing
        """
        pass

    @abc.abstractmethod
    def process_item(self, item: Any) -> Dict[str, Any]:
        """
        Process a single item and convert it to a standardized format.

        Args:
            item: Raw item from the source

        Returns:
            Dictionary with standardized format
        """
        pass

    def create_action_item(self, title: str, description: str, priority: str = "normal",
                          source: str = None, action_required: str = "Please review this item and take appropriate action.") -> Path:
        """
        Create a structured action item in the Needs_Action directory.

        Args:
            title: Title for the action item
            description: Description of the item
            priority: Priority level (normal, high, urgent)
            source: Source of the item
            action_required: Description of required action

        Returns:
            Path to the created file
        """
        if source is None:
            source = self.name

        content = f"""## Description
{description}

## Source Information
- **Source**: {source}
- **Detected**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Priority**: {priority}

## Action Required
{action_required}

## Related Links
- [[../Dashboard]]
- [[../Company_Handbook]]

## Notes
Add any notes or comments here during review.
"""

        return vault_manager.create_action_item(
            title=title,
            content=content,
            priority=priority,
            source=source
        )

    def run_once(self):
        """Run a single cycle of the watcher."""
        items = self.check_for_updates()
        processed_count = 0

        for item in items:
            try:
                processed_item = self.process_item(item)
                # Create action item in vault
                self.create_action_item(
                    title=processed_item.get('title', 'Untitled'),
                    description=processed_item.get('description', ''),
                    priority=processed_item.get('priority', 'normal'),
                    source=processed_item.get('source', self.name),
                    action_required=processed_item.get('action_required', 'Please review this item and take appropriate action.')
                )
                processed_count += 1
            except Exception as e:
                print(f"Error processing item in {self.name} watcher: {e}")

        self.last_check = datetime.now()
        return processed_count

    def run_continuous(self):
        """Run the watcher continuously with the specified poll interval."""
        self.is_running = True
        print(f"Starting {self.name} watcher...")

        while self.is_running:
            try:
                processed_count = self.run_once()
                if processed_count > 0:
                    print(f"{self.name} watcher processed {processed_count} items")
                time.sleep(self.poll_interval)
            except KeyboardInterrupt:
                print(f"Stopping {self.name} watcher...")
                self.is_running = False
                break
            except Exception as e:
                print(f"Error in {self.name} watcher: {e}")
                time.sleep(self.poll_interval)

    def stop(self):
        """Stop the continuous running of the watcher."""
        self.is_running = False
        print(f"{self.name} watcher stopped")


class WatcherManager:
    """Manages multiple watchers to ensure they don't conflict."""

    def __init__(self):
        self.watchers = {}

    def register_watcher(self, watcher: BaseWatcher):
        """Register a watcher with the manager."""
        self.watchers[watcher.name] = watcher

    def run_all_once(self):
        """Run all registered watchers once."""
        results = {}
        for name, watcher in self.watchers.items():
            try:
                results[name] = watcher.run_once()
            except Exception as e:
                print(f"Error running {name} watcher: {e}")
                results[name] = 0
        return results

    def run_all_continuous(self):
        """Run all watchers continuously (each in their own thread if needed)."""
        import threading

        threads = []
        for name, watcher in self.watchers.items():
            thread = threading.Thread(target=watcher.run_continuous)
            thread.daemon = True
            threads.append((thread, name))
            thread.start()

        try:
            # Keep the main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping all watchers...")
            for watcher in self.watchers.values():
                watcher.stop()
            for thread, name in threads:
                thread.join(timeout=2)  # Wait up to 2 seconds for each thread to finish