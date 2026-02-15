#!/usr/bin/env python3
"""
AI Employee - MCP Servers Launcher
Starts all MCP servers (Social Media, Odoo, Email, Calendar, Slack, Payment)
Each server runs as a separate subprocess on its own port.

Usage:
    python start_mcp_servers.py              # Start all MCP servers
    python start_mcp_servers.py --list       # List available servers
    python start_mcp_servers.py --only twitter meta  # Start specific servers
"""

import subprocess
import sys
import signal
import time
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_DIR = Path(__file__).parent
VAULT_DIR = Path(os.getenv("VAULT_DIR", "./demo_vault"))
LOGS_DIR = VAULT_DIR / "Logs"
SKILLS_DIR = PROJECT_DIR / ".claude" / "skills"

# Detect OS and set correct Python path
if os.name == "nt":  # Windows
    VENV_PYTHON = str(PROJECT_DIR / "venv-win" / "Scripts" / "python.exe")
    if not Path(VENV_PYTHON).exists():
        VENV_PYTHON = sys.executable
else:
    VENV_PYTHON = str(PROJECT_DIR / "venv" / "bin" / "python")
    if not Path(VENV_PYTHON).exists():
        VENV_PYTHON = sys.executable

# MCP Server definitions
# Each entry: (name, scripts_dir, main_module, port, required_env_vars)
MCP_SERVERS = {
    "twitter": {
        "name": "Twitter/X MCP",
        "scripts_dir": SKILLS_DIR / "twitter-mcp-server" / "scripts",
        "main_file": "twitter_mcp_server.py",
        "port": 8003,
        "has_init": True,
        "required_env": ["TWITTER_CLIENT_ID", "TWITTER_CLIENT_SECRET"],
    },
    "meta": {
        "name": "Meta Social MCP (Facebook + Instagram)",
        "scripts_dir": SKILLS_DIR / "meta-social-mcp-server" / "scripts",
        "main_file": "meta_mcp_server.py",
        "port": 8004,
        "has_init": True,
        "required_env": ["META_APP_ID", "META_APP_SECRET"],
    },
    "odoo": {
        "name": "Odoo ERP MCP",
        "scripts_dir": SKILLS_DIR / "odoo-mcp-server" / "scripts",
        "main_file": "odoo_mcp_server.py",
        "port": 8005,
        "has_init": True,
        "required_env": ["ODOO_URL", "ODOO_DB", "ODOO_USERNAME"],
    },
    "slack": {
        "name": "Slack MCP",
        "scripts_dir": SKILLS_DIR / "slack-mcp-server" / "scripts",
        "main_file": "slack_mcp_server.py",
        "port": 8006,
        "has_init": False,
        "required_env": ["SLACK_BOT_TOKEN"],
    },
    "email": {
        "name": "Email (Gmail) MCP",
        "scripts_dir": SKILLS_DIR / "email-mcp-server" / "scripts",
        "main_file": "email_mcp_server.py",
        "port": 8007,
        "has_init": False,
        "required_env": ["GMAIL_ADDRESS"],
    },
    "calendar": {
        "name": "Google Calendar MCP",
        "scripts_dir": SKILLS_DIR / "calendar-mcp-server" / "scripts",
        "main_file": "calendar_mcp_server.py",
        "port": 8008,
        "has_init": False,
        "required_env": ["GOOGLE_CALENDAR_ID"],
    },
    "payment": {
        "name": "Browser Payment MCP",
        "scripts_dir": SKILLS_DIR / "browser-payment-mcp" / "scripts",
        "main_file": "browser_payment_mcp.py",
        "port": 8009,
        "has_init": False,
        "required_env": [],
    },
    "linkedin": {
        "name": "LinkedIn MCP",
        "scripts_dir": SKILLS_DIR / "linkedin-posting-automation" / "scripts",
        "main_file": "linkedin_api_integration.py",
        "port": 8010,
        "has_init": False,
        "required_env": ["LINKEDIN_CLIENT_ID", "LINKEDIN_CLIENT_SECRET"],
    },
}

processes = []
running = True


def signal_handler(sig, frame):
    global running
    running = False
    print("\n\n" + "=" * 60)
    print("  Shutting down all MCP servers...")
    print("=" * 60)
    for name, proc in processes:
        try:
            proc.terminate()
            print(f"  Stopped: {name}")
        except Exception:
            pass
    time.sleep(2)
    for name, proc in processes:
        try:
            proc.kill()
        except Exception:
            pass
    print("  All MCP servers stopped.")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def check_env_vars(server_key):
    """Check if required environment variables are set."""
    server = MCP_SERVERS[server_key]
    missing = []
    for var in server["required_env"]:
        val = os.getenv(var, "")
        if not val or val.startswith("your_") or val == "placeholder":
            missing.append(var)
    return missing


def create_launcher_script(server_key):
    """Create a temporary launcher script that fixes imports and runs the MCP server."""
    server = MCP_SERVERS[server_key]
    scripts_dir = server["scripts_dir"]
    main_file = server["main_file"]
    port = server["port"]

    # Create a wrapper script that handles imports properly
    launcher_content = f'''#!/usr/bin/env python3
"""Auto-generated launcher for {server["name"]}"""
import sys
import os
from pathlib import Path

# Add the scripts directory to Python path for local imports
scripts_dir = r"{scripts_dir}"
sys.path.insert(0, scripts_dir)

# Also add project root
sys.path.insert(0, r"{PROJECT_DIR}")

# Set environment
os.environ.setdefault("MCP_PORT", "{port}")
os.environ.setdefault("VAULT_DIR", r"{VAULT_DIR}")

# Change to scripts directory for relative file access
os.chdir(scripts_dir)

# Import and run
'''

    if server["has_init"]:
        # Servers with __init__.py use relative imports - need special handling
        # We need to add the parent of scripts_dir so the package can be found
        parent_dir = scripts_dir.parent
        package_name = "scripts"
        launcher_content += f'''
# Package-style import for servers with relative imports
sys.path.insert(0, r"{parent_dir}")

import importlib
# Patch the module to fix relative imports
import types

# Direct execution approach - load the main file directly
main_path = os.path.join(scripts_dir, "{main_file}")
spec = importlib.util.spec_from_file_location("__main__", main_path,
    submodule_search_locations=[scripts_dir])

# Create fake package for relative imports
package_name = "{main_file.replace('.py', '')}"
scripts_pkg = types.ModuleType("scripts")
scripts_pkg.__path__ = [scripts_dir]
scripts_pkg.__package__ = "scripts"
sys.modules["scripts"] = scripts_pkg

# Load submodules that the server needs
for py_file in Path(scripts_dir).glob("*.py"):
    if py_file.stem != "__init__" and py_file.stem != "{main_file.replace('.py', '')}":
        sub_spec = importlib.util.spec_from_file_location(
            py_file.stem, str(py_file))
        sub_mod = importlib.util.module_from_spec(sub_spec)
        sys.modules[py_file.stem] = sub_mod
        sys.modules[f"scripts.{{py_file.stem}}"] = sub_mod
        # Also register as relative import target
        sys.modules[f".{{py_file.stem}}"] = sub_mod
        try:
            sub_spec.loader.exec_module(sub_mod)
        except Exception as e:
            print(f"  Warning: Could not load {{py_file.stem}}: {{e}}")

# Now load and run the main server
exec(open(main_path, encoding="utf-8").read())
'''
    else:
        # Servers without __init__.py use direct imports
        launcher_content += f'''
# Direct execution - imports work from sys.path
exec(open(os.path.join(scripts_dir, "{main_file}"), encoding="utf-8").read())
'''

    launcher_path = PROJECT_DIR / f"_launcher_{server_key}.py"
    launcher_path.write_text(launcher_content, encoding="utf-8")
    return launcher_path


def start_server(server_key):
    """Start a single MCP server."""
    server = MCP_SERVERS[server_key]

    # Check env vars
    missing = check_env_vars(server_key)
    if missing:
        print(f"  [SKIP] {server['name']} - Missing env vars: {', '.join(missing)}")
        return None

    # Check if scripts directory exists
    if not server["scripts_dir"].exists():
        print(f"  [SKIP] {server['name']} - Scripts directory not found")
        return None

    # Create launcher
    launcher_path = create_launcher_script(server_key)

    cmd = [VENV_PYTHON, str(launcher_path)]
    proc = subprocess.Popen(
        cmd,
        cwd=str(PROJECT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True,
        env={**os.environ, "MCP_PORT": str(server["port"])},
    )
    processes.append((server["name"], proc))
    print(f"  Started: {server['name']} (PID: {proc.pid}, Port: {server['port']})")
    return proc


def log_activity(action, details=""):
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"mcp_servers_{datetime.now().strftime('%Y%m%d')}.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {action}: {details}\n")


def print_output(name, proc):
    try:
        line = proc.stdout.readline()
        if line:
            print(f"  [{name}] {line.strip()}")
            return True
    except Exception:
        pass
    return False


def main():
    only = []
    if "--only" in sys.argv:
        idx = sys.argv.index("--only")
        only = sys.argv[idx + 1:]

    if "--list" in sys.argv:
        print("\nAvailable MCP Servers:")
        print("-" * 60)
        for key, server in MCP_SERVERS.items():
            missing = check_env_vars(key)
            status = "READY" if not missing else f"Missing: {', '.join(missing)}"
            print(f"  {key:12s} | {server['name']:35s} | {status}")
        print()
        return

    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    print()
    print("=" * 60)
    print("  AI Employee - MCP Servers Launcher")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Python: {VENV_PYTHON}")
    print("=" * 60)
    print()

    # Start servers
    print("Starting MCP servers...")
    print("-" * 40)

    started = 0
    skipped = 0
    for key, server in MCP_SERVERS.items():
        if only and key not in only:
            continue
        result = start_server(key)
        if result:
            started += 1
        else:
            skipped += 1

    print("-" * 40)
    print(f"\n  {started} MCP server(s) started, {skipped} skipped")
    if started > 0:
        print("  Press Ctrl+C to stop all\n")
    print("=" * 60)

    log_activity("STARTED", f"{started} MCP servers started, {skipped} skipped")

    # Monitor
    while running and started > 0:
        any_output = False
        for name, proc in processes:
            if proc.poll() is not None:
                print(f"\n  [WARNING] {name} exited with code {proc.returncode}")
                log_activity("EXITED", f"{name} code={proc.returncode}")
                # Remove from list to avoid re-checking
                processes.remove((name, proc))
                continue
            if print_output(name, proc):
                any_output = True
        if not any_output:
            time.sleep(0.5)

    # Cleanup launcher scripts
    for key in MCP_SERVERS:
        launcher = PROJECT_DIR / f"_launcher_{key}.py"
        if launcher.exists():
            try:
                launcher.unlink()
            except Exception:
                pass


if __name__ == "__main__":
    main()
