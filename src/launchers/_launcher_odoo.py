#!/usr/bin/env python3
"""Auto-generated launcher for Odoo ERP MCP"""
import sys
import os
from pathlib import Path

# Add the scripts directory to Python path for local imports
scripts_dir = r"E:\hackathon 0 qwen\Personal-AI-Employee\.claude\skills\odoo-mcp-server\scripts"
sys.path.insert(0, scripts_dir)

# Also add project root
sys.path.insert(0, r"E:\hackathon 0 qwen\Personal-AI-Employee")

# Set environment
os.environ.setdefault("MCP_PORT", "8005")
os.environ.setdefault("VAULT_DIR", r"demo_vault")

# Change to scripts directory for relative file access
os.chdir(scripts_dir)

# Import and run

# Package-style import for servers with relative imports
sys.path.insert(0, r"E:\hackathon 0 qwen\Personal-AI-Employee\.claude\skills\odoo-mcp-server")

import importlib
# Patch the module to fix relative imports
import types

# Direct execution approach - load the main file directly
main_path = os.path.join(scripts_dir, "odoo_mcp_server.py")
spec = importlib.util.spec_from_file_location("__main__", main_path,
    submodule_search_locations=[scripts_dir])

# Create fake package for relative imports
package_name = "odoo_mcp_server"
scripts_pkg = types.ModuleType("scripts")
scripts_pkg.__path__ = [scripts_dir]
scripts_pkg.__package__ = "scripts"
sys.modules["scripts"] = scripts_pkg

# Load submodules that the server needs
for py_file in Path(scripts_dir).glob("*.py"):
    if py_file.stem != "__init__" and py_file.stem != "odoo_mcp_server":
        sub_spec = importlib.util.spec_from_file_location(
            py_file.stem, str(py_file))
        sub_mod = importlib.util.module_from_spec(sub_spec)
        sys.modules[py_file.stem] = sub_mod
        sys.modules[f"scripts.{py_file.stem}"] = sub_mod
        # Also register as relative import target
        sys.modules[f".{py_file.stem}"] = sub_mod
        try:
            sub_spec.loader.exec_module(sub_mod)
        except Exception as e:
            print(f"  Warning: Could not load {py_file.stem}: {e}")

# Now load and run the main server
exec(open(main_path, encoding="utf-8").read())
