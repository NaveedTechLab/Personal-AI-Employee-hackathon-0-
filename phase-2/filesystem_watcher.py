"""
Filesystem Watcher for Phase 2 - Functional Assistant (Silver Tier)

Monitors a specified directory for file changes and creates action items based on triggers.
"""

import time
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from watchfiles import watch, Change
from datetime import datetime
from base_watcher import BaseWatcher


class FilesystemWatcher(BaseWatcher):
    """
    Filesystem watcher that monitors a directory for file changes and creates action items
    """

    def __init__(self, watched_directory: Optional[str] = None, poll_interval: int = 30):
        """
        Initialize the filesystem watcher.

        Args:
            watched_directory: Directory to watch (uses config default if None)
            poll_interval: Polling interval in seconds (used by watchfiles)
        """
        super().__init__(name="filesystem", poll_interval=poll_interval)

        if watched_directory is None:
            from .config import WATCHED_FOLDER_PATH
            self.watched_directory = Path(WATCHED_FOLDER_PATH)
        else:
            self.watched_directory = Path(watched_directory)

        # Create the watched directory if it doesn't exist
        self.watched_directory.mkdir(parents=True, exist_ok=True)

        # Track files to prevent duplicate processing
        self.processed_files = set()
        self.last_change_times = {}

    def check_for_updates(self) -> list:
        """
        Check the watched directory for file changes.
        In this implementation, we'll use a blocking watch call for demonstration.

        Returns:
            List of file change items that need processing
        """
        # This method is designed to work with the base class run cycle
        # For a real implementation with watchfiles, we'd use a different approach
        # Here we'll simulate detecting changes by comparing current files to previously seen files

        try:
            current_files = set(self.watched_directory.rglob("*"))
            new_or_modified_files = []

            for file_path in current_files:
                if file_path.is_file():
                    mod_time = file_path.stat().st_mtime

                    # Check if this file is new or has been modified since last check
                    if (str(file_path) not in self.last_change_times or
                        self.last_change_times[str(file_path)] != mod_time):

                        # Only add if we haven't processed this specific change before
                        change_identifier = f"{file_path}_{mod_time}"
                        if change_identifier not in self.processed_files:
                            new_or_modified_files.append({
                                'file_path': file_path,
                                'change_type': 'modified' if str(file_path) in self.last_change_times else 'created',
                                'timestamp': datetime.fromtimestamp(mod_time)
                            })

                            # Update tracking
                            self.last_change_times[str(file_path)] = mod_time
                            self.processed_files.add(change_identifier)

            return new_or_modified_files

        except Exception as e:
            print(f"Error checking for filesystem updates: {e}")
            return []

    def process_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single file change item and convert it to a standardized format.

        Args:
            item: Raw file change item dictionary

        Returns:
            Dictionary with standardized format
        """
        file_path = item['file_path']
        change_type = item['change_type']
        timestamp = item['timestamp']

        # Read file content preview (first 200 characters)
        content_preview = ""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content_preview = f.read(200)
        except:
            content_preview = "[Binary file or unable to read content]"

        # Determine priority based on file type or content
        priority = self._determine_priority(file_path, content_preview)

        # Create standardized output
        processed_item = {
            'title': f"File {change_type.title()}: {file_path.name}",
            'description': f"A file was {change_type} in the watched directory.\n\nFile: {file_path}\nSize: {file_path.stat().st_size} bytes\nModified: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\nContent preview: {content_preview[:150]}{'...' if len(content_preview) > 150 else ''}",
            'priority': priority,
            'source': 'filesystem_monitor',
            'action_required': f'Review the {change_type} file and determine if action is needed.'
        }

        return processed_item

    def _determine_priority(self, file_path: Path, content_preview: str) -> str:
        """
        Determine the priority of a file change based on file type and content.

        Args:
            file_path: Path of the changed file
            content_preview: Preview of the file content

        Returns:
            Priority level ('low', 'normal', 'high')
        """
        # High priority extensions
        high_priority_extensions = ['.xls', '.xlsx', '.doc', '.docx', '.pdf', '.csv', '.json', '.xml']
        high_priority_keywords = ['urgent', 'important', 'invoice', 'contract', 'agreement', 'report']

        # Check file extension
        if file_path.suffix.lower() in high_priority_extensions:
            return 'high'

        # Check content for keywords
        content_lower = content_preview.lower()
        if any(keyword in content_lower for keyword in high_priority_keywords):
            return 'high'

        # Default to normal for most files
        return 'normal'

    def start_monitoring(self, recursive: bool = True):
        """
        Start monitoring the directory for changes using watchfiles.

        Args:
            recursive: Whether to monitor subdirectories recursively
        """
        print(f"Starting filesystem monitoring for: {self.watched_directory}")
        print(f"Poll interval: {self.poll_interval}s")

        try:
            # Use watchfiles to monitor for changes
            for changes in watch(self.watched_directory, recursive=recursive,
                               debounce=1000, yield_on_timeout=True):

                if changes:  # If there are changes to process
                    for change in changes:
                        change_type, file_path_str = change
                        file_path = Path(file_path_str)

                        # Skip temporary/hidden files
                        if file_path.name.startswith('.') or any(part.startswith('.') for part in file_path.parts):
                            continue

                        # Process the change
                        change_item = {
                            'file_path': file_path,
                            'change_type': str(change_type).split('.')[-1].lower(),  # Convert Change.ADDED to 'added'
                            'timestamp': datetime.now()
                        }

                        # Create action item
                        processed_item = self.process_item(change_item)

                        # Create action item in vault
                        self.create_action_item(
                            title=processed_item.get('title', 'File Change'),
                            description=processed_item.get('description', ''),
                            priority=processed_item.get('priority', 'normal'),
                            source=processed_item.get('source', 'filesystem'),
                            action_required=processed_item.get('action_required', 'Please review this file change.')
                        )

                        print(f"Processed file change: {file_path.name}")

        except KeyboardInterrupt:
            print(f"Stopping filesystem monitoring for: {self.watched_directory}")
        except Exception as e:
            print(f"Error in filesystem monitoring: {e}")

    def run_demo(self):
        """
        Run a demonstration of the filesystem watcher functionality
        """
        print("Filesystem Watcher - Demo Mode")
        print("==============================")
        print(f"Monitoring directory: {self.watched_directory}")

        # Create some test files to trigger the watcher
        test_files = [
            self.watched_directory / "test_document.txt",
            self.watched_directory / "urgent_report.pdf",
            self.watched_directory / "normal_file.docx"
        ]

        print(f"\nCreating test files in {self.watched_directory}...")
        for test_file in test_files:
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(f"This is a test file created at {datetime.now()}\n")
                f.write("This file will trigger the filesystem watcher.\n")
                if 'urgent' in test_file.name.lower():
                    f.write("URGENT: Please review this document immediately.\n")

        print("Files created. The watcher would detect these changes and create action items.")
        print(f"Check the {self.watched_directory} directory and the Needs_Action folder.")


def main():
    """
    Main function to demonstrate the filesystem watcher functionality
    """
    # Create the watcher
    watcher = FilesystemWatcher()

    # Run the demo
    watcher.run_demo()


if __name__ == "__main__":
    main()