"""
Vault Manager for Phase 2 - Functional Assistant (Silver Tier)

Handles file system operations for the Obsidian vault structure.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import shutil

class VaultManager:
    """Manages file operations within the Obsidian vault structure."""

    def __init__(self, vault_path: Optional[Path] = None):
        """Initialize the vault manager with the vault path."""
        if vault_path is None:
            from config import VAULT_DIR
            self.vault_path = VAULT_DIR
        else:
            self.vault_path = Path(vault_path)

        self.inbox_dir = self.vault_path / "Inbox"
        self.needs_action_dir = self.vault_path / "Needs_Action"
        self.done_dir = self.vault_path / "Done"
        self.pending_approval_dir = self.vault_path / "Pending_Approval"
        self.approved_dir = self.vault_path / "Approved"
        self.rejected_dir = self.vault_path / "Rejected"

        self._ensure_directories_exist()

    def _ensure_directories_exist(self):
        """Ensure all required vault directories exist."""
        dirs_to_create = [
            self.inbox_dir,
            self.needs_action_dir,
            self.done_dir,
            self.pending_approval_dir,
            self.approved_dir,
            self.rejected_dir
        ]

        for directory in dirs_to_create:
            directory.mkdir(parents=True, exist_ok=True)

    def create_action_item(self, title: str, content: str, priority: str = "normal",
                          source: str = "system", status: str = "pending") -> Path:
        """Create a structured action item in the Needs_Action directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"action_{timestamp}_{self._sanitize_filename(title)}.md"
        filepath = self.needs_action_dir / filename

        # Create frontmatter
        frontmatter = f"""---
title: {title}
created: {datetime.now().isoformat()}
source: {source}
priority: {priority}
status: {status}
---
"""

        # Combine frontmatter and content
        full_content = frontmatter + f"\n# {title}\n\n{content}"

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_content)

        return filepath

    def move_to_pending_approval(self, filepath: Path) -> Path:
        """Move a file from Needs_Action to Pending_Approval."""
        if not filepath.exists():
            raise FileNotFoundError(f"File {filepath} does not exist")

        filename = filepath.name
        destination = self.pending_approval_dir / filename
        shutil.move(str(filepath), str(destination))
        return destination

    def move_to_approved(self, filepath: Path) -> Path:
        """Move a file from Pending_Approval to Approved."""
        if not filepath.exists():
            raise FileNotFoundError(f"File {filepath} does not exist")

        filename = filepath.name
        destination = self.approved_dir / filename
        shutil.move(str(filepath), str(destination))
        return destination

    def move_to_rejected(self, filepath: Path) -> Path:
        """Move a file from Pending_Approval to Rejected."""
        if not filepath.exists():
            raise FileNotFoundError(f"File {filepath} does not exist")

        filename = filepath.name
        destination = self.rejected_dir / filename
        shutil.move(str(filepath), str(destination))
        return destination

    def move_to_done(self, filepath: Path) -> Path:
        """Move a file to Done directory."""
        if not filepath.exists():
            raise FileNotFoundError(f"File {filepath} does not exist")

        filename = filepath.name
        destination = self.done_dir / filename
        shutil.move(str(filepath), str(destination))
        return destination

    def list_needs_action_items(self) -> List[Path]:
        """List all items in the Needs_Action directory."""
        return list(self.needs_action_dir.glob("*.md"))

    def list_pending_approval_items(self) -> List[Path]:
        """List all items in the Pending_Approval directory."""
        return list(self.pending_approval_dir.glob("*.md"))

    def list_approved_items(self) -> List[Path]:
        """List all items in the Approved directory."""
        return list(self.approved_dir.glob("*.md"))

    def list_rejected_items(self) -> List[Path]:
        """List all items in the Rejected directory."""
        return list(self.rejected_dir.glob("*.md"))

    def read_file_content(self, filepath: Path) -> str:
        """Read the content of a file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to remove invalid characters."""
        # Replace invalid characters for file names
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        # Also replace spaces with underscores for consistency
        filename = filename.replace(' ', '_')
        return filename.lower()


# Singleton instance
vault_manager = VaultManager()