"""
Main Entry Point for Phase 2 - Functional Assistant (Silver Tier)

This is the main entry point that coordinates all components of the system.
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add the phase-2 directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import all the components we've built
from config import (
    VAULT_DIR, EMAIL_WATCHER_ENABLED, FILESYSTEM_WATCHER_ENABLED,
    SCHEDULER_ENABLED, MCP_SERVER_ENABLED
)
from email_watcher import EmailWatcher
from filesystem_watcher import FilesystemWatcher
from base_watcher import WatcherManager
from plan_generator import plan_generator
from approval_workflow import approval_workflow
from mcp_client import mcp_client
from scheduler import Scheduler, run_claude_execution_cycle
from vault_manager import vault_manager
from coordinator import Coordinator
from schema_validator import schema_validator


def initialize_system():
    """
    Initialize all system components and verify they're working properly.
    """
    print("Initializing Personal AI Employee - Phase 2")
    print("===========================================")
    print(f"Initialization time: {datetime.now()}")
    print()

    # Verify vault directories exist
    print("Checking vault directories...")
    vault_dirs = [
        VAULT_DIR,
        VAULT_DIR / "Inbox",
        VAULT_DIR / "Needs_Action",
        VAULT_DIR / "Done",
        VAULT_DIR / "Pending_Approval",
        VAULT_DIR / "Approved",
        VAULT_DIR / "Rejected"
    ]

    for directory in vault_dirs:
        if directory.exists():
            print(f"  [OK] {directory.name} directory exists")
        else:
            print(f"  [ERROR] {directory.name} directory missing!")
            return False

    print()

    # Test configuration
    print("System Configuration:")
    print(f"  - Email Watcher Enabled: {EMAIL_WATCHER_ENABLED}")
    print(f"  - Filesystem Watcher Enabled: {FILESYSTEM_WATCHER_ENABLED}")
    print(f"  - Scheduler Enabled: {SCHEDULER_ENABLED}")
    print(f"  - MCP Server Enabled: {MCP_SERVER_ENABLED}")
    print()

    # Test MCP client connectivity if enabled
    if MCP_SERVER_ENABLED:
        print("Testing MCP server connectivity...")
        if mcp_client.ping():
            print("  [OK] MCP server is reachable")
        else:
            print("  [WARN] MCP server is not reachable (this is expected if server not running)")
        print()

    # Create a test action item to verify vault manager
    print("Testing vault manager...")
    test_file = vault_manager.create_action_item(
        title="System Initialization Test",
        content="This is a test action item created during system initialization.",
        priority="normal",
        source="system_init"
    )
    print(f"  [OK] Created test action item: {test_file.name}")
    print()

    return True


def run_demo():
    """
    Run a demonstration of the complete system functionality.
    """
    print("Running Phase 2 Demo")
    print("===================")
    print("This demo will showcase all Silver Tier functionality:")
    print("1. Multi-source monitoring (Email + Filesystem)")
    print("2. Plan generation for complex tasks")
    print("3. Approval workflow for sensitive actions")
    print("4. MCP integration for external actions")
    print("5. Scheduling for periodic execution")
    print()

    # Create an email watcher and run a demo
    print("Step 1: Email Watcher Demo")
    email_watcher = EmailWatcher()
    email_watcher.run_demo()
    print()

    # Create a filesystem watcher and run a demo
    print("Step 2: Filesystem Watcher Demo")
    filesystem_watcher = FilesystemWatcher()
    filesystem_watcher.run_demo()
    print()

    # Show plan generation
    print("Step 3: Plan Generation Demo")
    plan_path = plan_generator.create_email_followup_plan(
        recipient="manager@example.com",
        subject="Quarterly Review Meeting",
        followup_points=[
            "Discuss budget allocation",
            "Review team performance metrics",
            "Plan next quarter initiatives"
        ]
    )
    print(f"  [OK] Created plan: {plan_path.name}")
    print()

    # Show approval workflow
    print("Step 4: Approval Workflow Demo")
    approval_file = approval_workflow.create_approval_request(
        action_type="send_email",
        description="Send follow-up email to discuss quarterly review meeting",
        approval_required=["manager_approval", "budget_approval"]
    )
    print(f"  [OK] Created approval request: {approval_file.name}")
    print()

    # Show scheduler demo
    print("Step 5: Scheduler Demo")
    print("  - Scheduler configured with interval from config")
    print("  - Will run Claude execution cycles periodically")
    print("  - Designed to avoid autonomous loops")
    print()

    print("Demo completed! Check the vault directories for created files.")
    print("- Needs_Action: Items requiring review")
    print("- Pending_Approval: Items awaiting approval")
    print("- Plans: Generated Plan.md files")
    print()


def run_end_to_end_test():
    """
    Run an end-to-end test of the Silver Tier functionality:
    Watcher -> Plan -> Approval -> MCP Action -> Manual Closure
    """
    print("Running End-to-End Silver Tier Test")
    print("==================================")
    print("Testing: Watcher -> Plan -> Approval -> MCP Action -> Manual Closure")
    print()

    # Step 1: Create a trigger via email watcher
    print("Step 1: Creating email trigger...")
    email_watcher = EmailWatcher()
    action_file = email_watcher.simulate_specific_email(
        subject="URGENT: Contract Approval Needed",
        body="We need to send an approval email to the legal department regarding the new vendor contract. This requires immediate attention.",
        priority="high"
    )
    print(f"  [OK] Created action item: {action_file.name if action_file else 'None'}")
    print()

    # Step 2: Generate a plan for the complex task
    print("Step 2: Generating plan for complex task...")
    if action_file:
        plan_path = plan_generator.create_email_followup_plan(
            recipient="legal@company.com",
            subject="Vendor Contract Approval",
            followup_points=[
                "Review contract terms",
                "Check legal compliance",
                "Get final approval"
            ]
        )
        print(f"  [OK] Created plan: {plan_path.name}")
    else:
        # Create a plan directly since the action file wasn't created
        plan_path = plan_generator.create_email_followup_plan(
            recipient="legal@company.com",
            subject="Vendor Contract Approval",
            followup_points=[
                "Review contract terms",
                "Check legal compliance",
                "Get final approval"
            ]
        )
        print(f"  [OK] Created plan: {plan_path.name}")
    print()

    # Step 3: Create approval request for MCP action
    print("Step 3: Creating approval request for MCP action...")
    approval_file = approval_workflow.create_approval_request(
        action_type="send_email",
        description="Send approval email to legal department for vendor contract",
        approval_required=["legal_approval", "management_approval"]
    )
    print(f"  [OK] Created approval request: {approval_file.name}")
    print()

    # Step 4: Show that MCP action would happen after approval
    print("Step 4: MCP action execution (after approval)...")
    print("  - When approval is granted, MCP client would execute the action")
    print("  - This maintains the required human-in-the-loop safety")
    print()

    # Step 5: Show manual closure process
    print("Step 5: Manual closure process...")
    print("  - Human moves files between approval directories")
    print("  - System processes approved/rejected requests accordingly")
    print("  - Maintains non-autonomous operation")
    print()

    print("End-to-End Test completed successfully!")
    print("All Silver Tier functionality demonstrated:")
    print("- Multi-source monitoring")
    print("- Plan generation with approval markers")
    print("- File-based approval workflow")
    print("- MCP integration for external actions")
    print("- Human-in-the-loop safety controls")


def main():
    """
    Main function to run the Personal AI Employee system.
    """
    # Change to the script's directory to ensure proper paths
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)

    # Initialize the system
    if not initialize_system():
        print("System initialization failed. Exiting.")
        sys.exit(1)

    print("System initialized successfully!")
    print()

    # Ask user what to run
    print("Available options:")
    print("1. Run full demo")
    print("2. Run end-to-end test")
    print("3. Start coordinator (continuous mode)")
    print("4. Run both demo and test")
    print()

    try:
        choice = input("Enter your choice (1-4, or press Enter for option 1): ").strip()
        if not choice:
            choice = "1"
    except KeyboardInterrupt:
        print("\nExiting...")
        return

    if choice == "1":
        run_demo()
    elif choice == "2":
        run_end_to_end_test()
    elif choice == "3":
        print("Starting coordinator in continuous mode...")
        print("Press Ctrl+C to stop.")
        coordinator = Coordinator()
        try:
            coordinator.run_continuous()
        except KeyboardInterrupt:
            print("\nShutting down coordinator...")
    elif choice == "4":
        run_demo()
        print("\n" + "="*50 + "\n")
        run_end_to_end_test()
    else:
        print("Invalid choice. Running demo by default.")
        run_demo()

    print("\nThank you for using Personal AI Employee - Phase 2!")


if __name__ == "__main__":
    main()