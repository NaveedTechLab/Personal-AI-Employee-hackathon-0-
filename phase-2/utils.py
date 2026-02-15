"""
Utility Functions for Phase 2 - Functional Assistant (Silver Tier)

Provides common utility functions for the system.
"""

import re
import os
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional
import json


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing or replacing invalid characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Replace invalid characters for file names
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')

    # Also replace spaces with underscores for consistency
    filename = filename.replace(' ', '_')

    # Remove any double underscores that may have been created
    while '__' in filename:
        filename = filename.replace('__', '_')

    return filename.lower().strip('_')


def generate_unique_id(content: str = "", length: int = 8) -> str:
    """
    Generate a unique ID based on content or current time.

    Args:
        content: Content to base the ID on
        length: Length of the ID to generate

    Returns:
        Unique identifier string
    """
    if not content:
        content = str(datetime.now())

    # Create hash of the content
    hash_object = hashlib.sha256(content.encode())
    hex_dig = hash_object.hexdigest()

    return hex_dig[:length]


def format_timestamp(timestamp: Optional[datetime] = None) -> str:
    """
    Format a timestamp in ISO format.

    Args:
        timestamp: Datetime object to format (uses current time if None)

    Returns:
        Formatted timestamp string
    """
    if timestamp is None:
        timestamp = datetime.now()

    return timestamp.isoformat()


def ensure_directory_exists(path: Path) -> bool:
    """
    Ensure that a directory exists, creating it if necessary.

    Args:
        path: Path to the directory

    Returns:
        True if directory exists or was created, False otherwise
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {path}: {e}")
        return False


def read_file_safely(filepath: Path, default: str = "") -> str:
    """
    Safely read a file, returning a default value if it doesn't exist.

    Args:
        filepath: Path to the file
        default: Default value to return if file doesn't exist

    Returns:
        File content or default value
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return default
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        return default


def write_file_safely(filepath: Path, content: str) -> bool:
    """
    Safely write content to a file.

    Args:
        filepath: Path to the file
        content: Content to write

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        ensure_directory_exists(filepath.parent)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing file {filepath}: {e}")
        return False


def find_files_by_extension(directory: Path, extension: str) -> List[Path]:
    """
    Find all files in a directory with a specific extension.

    Args:
        directory: Directory to search
        extension: File extension to look for (with or without dot)

    Returns:
        List of matching file paths
    """
    if not extension.startswith('.'):
        extension = '.' + extension

    return list(directory.rglob(f"*{extension}"))


def load_json_safely(filepath: Path, default: Dict = None) -> Dict:
    """
    Safely load a JSON file, returning a default if it doesn't exist or is invalid.

    Args:
        filepath: Path to the JSON file
        default: Default dictionary to return

    Returns:
        Loaded JSON data or default
    """
    if default is None:
        default = {}

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON file {filepath}: {e}")
        return default
    except Exception as e:
        print(f"Error reading JSON file {filepath}: {e}")
        return default


def save_json_safely(filepath: Path, data: Dict) -> bool:
    """
    Safely save data to a JSON file.

    Args:
        filepath: Path to the JSON file
        data: Data to save

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        ensure_directory_exists(filepath.parent)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving JSON file {filepath}: {e}")
        return False


def normalize_path(path: str) -> str:
    """
    Normalize a path string by resolving .. and .

    Args:
        path: Path string to normalize

    Returns:
        Normalized path string
    """
    return os.path.normpath(path)


def is_subpath(child: Path, parent: Path) -> bool:
    """
    Check if child path is a subpath of parent path.

    Args:
        child: Child path to check
        parent: Parent path to check against

    Returns:
        True if child is subpath of parent, False otherwise
    """
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def get_file_hash(filepath: Path) -> str:
    """
    Get the SHA-256 hash of a file.

    Args:
        filepath: Path to the file

    Returns:
        SHA-256 hash of the file
    """
    hash_sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length.

    Args:
        text: String to truncate
        max_length: Maximum length of the string
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix