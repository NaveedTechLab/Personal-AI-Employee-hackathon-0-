"""
Vault Integrator Module for Phase 3 - Autonomous Employee (Gold Tier)
Handles integration with existing vault structure from Phase 1 and extends
it to support cross-domain reasoning capabilities.
"""

import os
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import yaml
from datetime import datetime


class VaultIntegrator:
    """
    Class responsible for integrating with the existing vault structure
    and extending it to support cross-domain reasoning capabilities.
    """

    def __init__(self, vault_path: str = "./vault"):
        """
        Initialize the VaultIntegrator with the vault path.

        Args:
            vault_path: Path to the vault directory
        """
        self.vault_path = Path(vault_path)
        self.phase_1_vault_path = self.vault_path
        self.phase_3_extension_path = Path("./phase-3/vault")

        # Ensure the Phase 3 vault directory exists
        self.phase_3_extension_path.mkdir(parents=True, exist_ok=True)

    def read_phase_1_data(self) -> Dict[str, Any]:
        """
        Read data from the Phase 1 vault structure.

        Returns:
            Dictionary containing Phase 1 vault data
        """
        phase_1_data = {}

        # Look for common Phase 1 data directories/files
        for dirpath, dirnames, filenames in os.walk(self.phase_1_vault_path):
            for filename in filenames:
                if filename.endswith(('.md', '.json', '.txt', '.yaml', '.yml')):
                    filepath = Path(dirpath) / filename
                    try:
                        if filename.endswith('.json'):
                            with open(filepath, 'r', encoding='utf-8') as f:
                                content = json.load(f)
                        elif filename.endswith(('.yaml', '.yml')):
                            with open(filepath, 'r', encoding='utf-8') as f:
                                content = yaml.safe_load(f)
                        else:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                content = f.read()

                        # Store content with relative path as key
                        relative_path = filepath.relative_to(self.phase_1_vault_path)
                        phase_1_data[str(relative_path)] = content
                    except Exception as e:
                        print(f"Error reading {filepath}: {str(e)}")

        return phase_1_data

    def read_cross_domain_data(self) -> Dict[str, Any]:
        """
        Read cross-domain data from the extended Phase 3 vault structure.

        Returns:
            Dictionary containing cross-domain data
        """
        cross_domain_data = {}

        # Include Phase 1 data
        cross_domain_data.update(self.read_phase_1_data())

        # Add Phase 3 specific data
        for dirpath, dirnames, filenames in os.walk(self.phase_3_extension_path):
            for filename in filenames:
                if filename.endswith(('.md', '.json', '.txt', '.yaml', '.yml')):
                    filepath = Path(dirpath) / filename
                    try:
                        if filename.endswith('.json'):
                            with open(filepath, 'r', encoding='utf-8') as f:
                                content = json.load(f)
                        elif filename.endswith(('.yaml', '.yml')):
                            with open(filepath, 'r', encoding='utf-8') as f:
                                content = yaml.safe_load(f)
                        else:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                content = f.read()

                        # Store content with relative path as key
                        relative_path = filepath.relative_to(self.phase_3_extension_path)
                        cross_domain_data[f"phase_3/{relative_path}"] = content
                    except Exception as e:
                        print(f"Error reading {filepath}: {str(e)}")

        return cross_domain_data

    def extend_vault_structure(self, new_data: Dict[str, Any], category: str = "general"):
        """
        Extend the vault structure with new data from Phase 3 operations.

        Args:
            new_data: Dictionary containing new data to store
            category: Category for organizing the new data
        """
        category_path = self.phase_3_extension_path / category
        category_path.mkdir(parents=True, exist_ok=True)

        # Save each item in new_data as a separate file
        for key, value in new_data.items():
            # Sanitize the key to create a valid filename
            sanitized_key = "".join(c for c in key if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()

            # Determine file extension based on data type
            if isinstance(value, dict) or isinstance(value, list):
                file_ext = ".json"
                content = json.dumps(value, indent=2, default=str)
            else:
                file_ext = ".txt"
                content = str(value)

            # Create the file path
            file_path = category_path / f"{sanitized_key}{file_ext}"

            # Write the content to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

    def get_communications_data(self) -> List[Dict[str, Any]]:
        """
        Retrieve communications data from the vault.

        Returns:
            List of communication records
        """
        communications = []
        cross_domain_data = self.read_cross_domain_data()

        for path, content in cross_domain_data.items():
            if 'communication' in path.lower() or 'email' in path.lower() or 'message' in path.lower():
                if isinstance(content, dict):
                    communications.append({
                        'source': path,
                        'data': content,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    communications.append({
                        'source': path,
                        'data': {'content': content},
                        'timestamp': datetime.now().isoformat()
                    })

        return communications

    def get_task_artifacts(self) -> List[Dict[str, Any]]:
        """
        Retrieve task artifacts from the vault.

        Returns:
            List of task artifact records
        """
        tasks = []
        cross_domain_data = self.read_cross_domain_data()

        for path, content in cross_domain_data.items():
            if 'task' in path.lower() or 'todo' in path.lower() or 'action' in path.lower():
                if isinstance(content, dict):
                    tasks.append({
                        'source': path,
                        'data': content,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    tasks.append({
                        'source': path,
                        'data': {'content': content},
                        'timestamp': datetime.now().isoformat()
                    })

        return tasks

    def get_business_goals(self) -> List[Dict[str, Any]]:
        """
        Retrieve business goals from the vault.

        Returns:
            List of business goal records
        """
        goals = []
        cross_domain_data = self.read_cross_domain_data()

        for path, content in cross_domain_data.items():
            if 'goal' in path.lower() or 'objective' in path.lower() or 'target' in path.lower():
                if isinstance(content, dict):
                    goals.append({
                        'source': path,
                        'data': content,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    goals.append({
                        'source': path,
                        'data': {'content': content},
                        'timestamp': datetime.now().isoformat()
                    })

        return goals

    def get_transaction_logs(self) -> List[Dict[str, Any]]:
        """
        Retrieve transaction logs from the vault.

        Returns:
            List of transaction log records
        """
        transactions = []
        cross_domain_data = self.read_cross_domain_data()

        for path, content in cross_domain_data.items():
            if 'transaction' in path.lower() or 'finance' in path.lower() or 'log' in path.lower():
                if isinstance(content, dict):
                    transactions.append({
                        'source': path,
                        'data': content,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    transactions.append({
                        'source': path,
                        'data': {'content': content},
                        'timestamp': datetime.now().isoformat()
                    })

        return transactions


def get_vault_integrator_instance() -> VaultIntegrator:
    """
    Factory function to get a VaultIntegrator instance.

    Returns:
        VaultIntegrator instance
    """
    return VaultIntegrator()


if __name__ == "__main__":
    # Example usage
    vault_integrator = get_vault_integrator_instance()

    # Read cross-domain data
    cross_domain_data = vault_integrator.read_cross_domain_data()
    print(f"Found {len(cross_domain_data)} items in cross-domain data")

    # Get specific data types
    communications = vault_integrator.get_communications_data()
    tasks = vault_integrator.get_task_artifacts()
    goals = vault_integrator.get_business_goals()
    transactions = vault_integrator.get_transaction_logs()

    print(f"Communications: {len(communications)}")
    print(f"Tasks: {len(tasks)}")
    print(f"Goals: {len(goals)}")
    print(f"Transactions: {len(transactions)}")