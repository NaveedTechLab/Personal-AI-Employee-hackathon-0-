"""
Scheduler for Phase 2 - Functional Assistant (Silver Tier)

Implements basic scheduling functionality to trigger Claude execution periodically
without creating autonomous loops.
"""

import schedule
import time
import threading
from datetime import datetime
from typing import Callable, Optional
from config import SCHEDULE_INTERVAL_MINUTES, SCHEDULER_ENABLED


class Scheduler:
    """
    Basic scheduler to trigger Claude execution at specified intervals
    without creating autonomous loops.
    """

    def __init__(self, interval_minutes: Optional[int] = None):
        """
        Initialize the scheduler.

        Args:
            interval_minutes: Interval in minutes between executions (uses config default if None)
        """
        if interval_minutes is None:
            self.interval_minutes = SCHEDULE_INTERVAL_MINUTES
        else:
            self.interval_minutes = interval_minutes

        self.enabled = SCHEDULER_ENABLED
        self.is_running = False
        self.scheduler_thread = None

        # Store callback functions
        self.callbacks = []

    def add_job(self, func: Callable, *args, **kwargs):
        """
        Add a job to be executed on schedule.

        Args:
            func: Function to call
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
        """
        job = lambda: func(*args, **kwargs)
        schedule.every(self.interval_minutes).minutes.do(job)
        self.callbacks.append(job)

    def start(self):
        """
        Start the scheduler in a separate thread.
        """
        if not self.enabled:
            print("Scheduler is disabled according to configuration")
            return

        if self.is_running:
            print("Scheduler is already running")
            return

        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        print(f"Scheduler started with {self.interval_minutes}-minute intervals")

    def stop(self):
        """
        Stop the scheduler.
        """
        self.is_running = False
        schedule.clear()
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=2)
        print("Scheduler stopped")

    def _run_scheduler(self):
        """
        Internal method to run the scheduler loop.
        """
        print(f"Scheduler running... Checking every {self.interval_minutes} minutes")
        while self.is_running:
            schedule.run_pending()
            time.sleep(1)  # Check every second for pending jobs

    def run_immediate(self):
        """
        Run all scheduled jobs immediately (for testing or manual triggers).
        """
        print("Running scheduled jobs immediately...")
        schedule.run_all()
        print("Immediate execution completed.")

    def get_next_run_time(self):
        """
        Get the next scheduled run time.

        Returns:
            Next run time as a datetime object, or None if no jobs scheduled
        """
        if schedule.jobs:
            return schedule.jobs[0].next_run
        return None

    def get_job_count(self):
        """
        Get the number of scheduled jobs.

        Returns:
            Number of scheduled jobs
        """
        return len(schedule.jobs)


def run_claude_execution_cycle():
    """
    Function to run a Claude execution cycle - this would typically process
    any pending items in the system, but without creating autonomous loops.
    """
    print(f"[SCHEDULED] Claude execution cycle started at {datetime.now()}")

    # This is where Claude would process items, but only if there are items to process
    # and without creating any automated responses or actions that would lead to loops

    # Example: Check for items in various directories and process them according to rules
    # This would connect to the vault manager, check for items needing attention, etc.
    print("[SCHEDULED] Checking for items requiring attention...")

    # In a real implementation, this would:
    # 1. Check Needs_Action for new items
    # 2. Potentially create Plan.md files for complex items
    # 3. Check for pending approvals
    # 4. Process any completed items
    # 5. Update dashboards/stats
    # But importantly: NOT automatically respond to items or create new cycles

    print(f"[SCHEDULED] Claude execution cycle completed at {datetime.now()}")


def main():
    """
    Main function to demonstrate the scheduler functionality.
    """
    print("Personal AI Employee - Scheduler Module")
    print("=======================================")

    # Create scheduler instance
    scheduler = Scheduler()

    if not scheduler.enabled:
        print("Scheduler is disabled by configuration")
        return

    # Add the Claude execution cycle to the schedule
    scheduler.add_job(run_claude_execution_cycle)

    print(f"Added Claude execution cycle to schedule (every {scheduler.interval_minutes} minutes)")
    print(f"Next run: {scheduler.get_next_run_time()}")

    try:
        # Start the scheduler
        scheduler.start()

        print("Scheduler is now running. Press Ctrl+C to stop.")
        print("Jobs will run every", scheduler.interval_minutes, "minutes.")

        # Keep the main thread alive
        while True:
            time.sleep(10)  # Sleep in chunks to allow interruption

    except KeyboardInterrupt:
        print("\nStopping scheduler...")
        scheduler.stop()
        print("Scheduler stopped.")


if __name__ == "__main__":
    main()