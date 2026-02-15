"""
Schema Validator for Phase 2 - Functional Assistant (Silver Tier)

Validates the structure and content of .md files to ensure consistency.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import yaml
from datetime import datetime


class SchemaValidator:
    """Validates the schema of markdown files for consistency."""

    def __init__(self):
        """Initialize the schema validator."""
        self.required_frontmatter_fields = ['title', 'created', 'source', 'priority', 'status']
        self.valid_priorities = ['low', 'normal', 'high', 'urgent']
        self.valid_statuses = ['pending', 'in_progress', 'completed', 'rejected', 'approved']

    def validate_markdown_file(self, filepath: Path) -> Tuple[bool, List[str]]:
        """
        Validate a markdown file against the required schema.

        Args:
            filepath: Path to the markdown file to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return False, [f"Could not read file: {e}"]

        # Split frontmatter and content
        parts = self._extract_frontmatter(content)

        if parts is None:
            return False, ["File does not have valid YAML frontmatter"]

        frontmatter, body = parts

        # Validate frontmatter
        frontmatter_valid, frontmatter_errors = self._validate_frontmatter(frontmatter)
        errors.extend(frontmatter_errors)

        # Validate body structure
        body_valid, body_errors = self._validate_body(body)
        errors.extend(body_errors)

        return len(errors) == 0, errors

    def _extract_frontmatter(self, content: str) -> Optional[Tuple[Dict, str]]:
        """
        Extract YAML frontmatter from markdown content.

        Args:
            content: Full markdown content

        Returns:
            Tuple of (frontmatter_dict, body_content) or None if no valid frontmatter
        """
        lines = content.split('\n')

        if len(lines) < 3:
            return None

        # Check if the file starts with frontmatter
        if lines[0].strip() != '---':
            return None

        # Find the end of frontmatter
        frontmatter_end_idx = -1
        for i in range(1, len(lines)):
            if lines[i].strip() == '---' and i > 0:
                frontmatter_end_idx = i
                break

        if frontmatter_end_idx == -1:
            return None

        # Parse frontmatter
        try:
            frontmatter_str = '\n'.join(lines[1:frontmatter_end_idx])
            frontmatter = yaml.safe_load(frontmatter_str)
            if not isinstance(frontmatter, dict):
                return None
        except yaml.YAMLError:
            return None

        # Get body content
        body = '\n'.join(lines[frontmatter_end_idx + 1:])

        return frontmatter, body

    def _validate_frontmatter(self, frontmatter: Dict) -> Tuple[bool, List[str]]:
        """
        Validate the frontmatter of a markdown file.

        Args:
            frontmatter: Dictionary of frontmatter fields

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check for required fields
        for field in self.required_frontmatter_fields:
            if field not in frontmatter:
                errors.append(f"Missing required frontmatter field: {field}")

        # Validate priority
        if 'priority' in frontmatter:
            if frontmatter['priority'] not in self.valid_priorities:
                errors.append(f"Invalid priority value: {frontmatter['priority']}. Must be one of {self.valid_priorities}")

        # Validate status
        if 'status' in frontmatter:
            if frontmatter['status'] not in self.valid_statuses:
                errors.append(f"Invalid status value: {frontmatter['status']}. Must be one of {self.valid_statuses}")

        # Validate created timestamp
        if 'created' in frontmatter:
            try:
                # Try to parse the created timestamp
                datetime.fromisoformat(frontmatter['created'].replace('Z', '+00:00'))
            except ValueError:
                errors.append(f"Invalid created timestamp format: {frontmatter['created']}")

        return len(errors) == 0, errors

    def _validate_body(self, body: str) -> Tuple[bool, List[str]]:
        """
        Validate the body of a markdown file.

        Args:
            body: Markdown body content

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check for required sections
        required_sections = ['Description', 'Source Information', 'Action Required']
        body_lower = body.lower()

        for section in required_sections:
            if f'## {section.lower()}' not in body_lower and f'# {section.lower()}' not in body_lower:
                errors.append(f"Missing required section: {section}")

        # Check for proper markdown structure
        if not body.strip():
            errors.append("Body is empty")

        return len(errors) == 0, errors

    def validate_action_item_schema(self, filepath: Path) -> Tuple[bool, List[str]]:
        """
        Specifically validate an action item file.

        Args:
            filepath: Path to the action item file

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        is_valid, errors = self.validate_markdown_file(filepath)

        # Additional checks for action items
        if is_valid:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check if it has the right structure for an action item
                if '# Action Required' not in content:
                    errors.append("Action item missing 'Action Required' section")
                if 'Please review this item' not in content:
                    errors.append("Action item missing standard review instruction")

            except Exception as e:
                errors.append(f"Error checking action item structure: {e}")
                is_valid = False

        return is_valid, errors

    def validate_plan_schema(self, filepath: Path) -> Tuple[bool, List[str]]:
        """
        Specifically validate a Plan.md file.

        Args:
            filepath: Path to the Plan.md file

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        is_valid, errors = self.validate_markdown_file(filepath)

        # Additional checks for Plan.md files
        if is_valid:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check if it has the right structure for a plan
                if '# Objectives' not in content and '## Objectives' not in content:
                    errors.append("Plan file missing 'Objectives' section")
                if '## Steps' not in content and '# Steps' not in content:
                    errors.append("Plan file missing 'Steps' section")
                if 'approval' not in content.lower():
                    errors.append("Plan file should contain approval markers")

            except Exception as e:
                errors.append(f"Error checking plan structure: {e}")
                is_valid = False

        return is_valid, errors

    def validate_approval_request_schema(self, filepath: Path) -> Tuple[bool, List[str]]:
        """
        Specifically validate an approval request file.

        Args:
            filepath: Path to the approval request file

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        is_valid, errors = self.validate_markdown_file(filepath)

        # Additional checks for approval requests
        if is_valid:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check if it has the right structure for an approval request
                if '## Action Type' not in content:
                    errors.append("Approval request missing 'Action Type' section")
                if '## Description' not in content:
                    errors.append("Approval request missing 'Description' section")
                if '## Approval Required' not in content:
                    errors.append("Approval request missing 'Approval Required' section")

            except Exception as e:
                errors.append(f"Error checking approval request structure: {e}")
                is_valid = False

        return is_valid, errors


# Singleton instance
schema_validator = SchemaValidator()