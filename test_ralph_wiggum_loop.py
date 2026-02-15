#!/usr/bin/env python3
"""
Tests for Ralph Wiggum Loop - Autonomous Task Completion System
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the skills path
sys.path.insert(0, str(Path(__file__).parent / ".claude" / "skills" / "ralph-wiggum-loop" / "scripts"))

from models import (
    CompletionCriteria,
    CompletionType,
    RalphWiggumConfig,
    TaskStatus,
    TrackedTask,
)


class TestRalphWiggumModels(unittest.TestCase):
    """Test Ralph Wiggum data models"""

    def test_task_status_values(self):
        """Test TaskStatus enum values"""
        self.assertEqual(TaskStatus.PENDING.value, "pending")
        self.assertEqual(TaskStatus.IN_PROGRESS.value, "in_progress")
        self.assertEqual(TaskStatus.COMPLETED.value, "completed")
        self.assertEqual(TaskStatus.FAILED.value, "failed")

    def test_completion_type_values(self):
        """Test CompletionType enum values"""
        self.assertEqual(CompletionType.FILE_MOVED.value, "file_moved")
        self.assertEqual(CompletionType.STATUS_MARKER.value, "status_marker")
        self.assertEqual(CompletionType.CUSTOM_CRITERIA.value, "custom_criteria")

    def test_completion_criteria_to_dict(self):
        """Test CompletionCriteria serialization"""
        criteria = CompletionCriteria(
            type=CompletionType.FILE_MOVED,
            destination_folder="./vault/Done/",
            status_markers=["status: completed"]
        )
        result = criteria.to_dict()

        self.assertEqual(result["type"], "file_moved")
        self.assertEqual(result["destination_folder"], "./vault/Done/")
        self.assertIn("status: completed", result["status_markers"])

    def test_completion_criteria_from_dict(self):
        """Test CompletionCriteria deserialization"""
        data = {
            "type": "status_marker",
            "destination_folder": None,
            "status_markers": ["## Completed"],
            "custom_check": None
        }
        criteria = CompletionCriteria.from_dict(data)

        self.assertEqual(criteria.type, CompletionType.STATUS_MARKER)
        self.assertIn("## Completed", criteria.status_markers)

    def test_tracked_task_to_dict(self):
        """Test TrackedTask serialization"""
        task = TrackedTask(
            id="task_123",
            name="Test task",
            source_file="./test.md",
            status=TaskStatus.PENDING,
            iteration_count=0,
            max_iterations=5
        )
        result = task.to_dict()

        self.assertEqual(result["id"], "task_123")
        self.assertEqual(result["name"], "Test task")
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["iteration_count"], 0)

    def test_ralph_wiggum_config_defaults(self):
        """Test RalphWiggumConfig default values"""
        config = RalphWiggumConfig()

        self.assertEqual(config.max_global_iterations, 10)
        self.assertEqual(config.max_task_iterations, 5)
        self.assertEqual(config.check_interval_seconds, 5)
        self.assertEqual(config.done_folder, "./vault/Done/")
        self.assertEqual(config.failed_folder, "./vault/Failed/")
        self.assertTrue(config.enable_audit_logging)

    def test_ralph_wiggum_config_from_dict(self):
        """Test RalphWiggumConfig from dictionary"""
        data = {
            "max_global_iterations": 20,
            "max_task_iterations": 10,
            "done_folder": "/custom/Done/"
        }
        config = RalphWiggumConfig.from_dict(data)

        self.assertEqual(config.max_global_iterations, 20)
        self.assertEqual(config.max_task_iterations, 10)
        self.assertEqual(config.done_folder, "/custom/Done/")


class TestTaskTracker(unittest.TestCase):
    """Test TaskTracker database operations"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_ralph.db")
        self.config = RalphWiggumConfig(database_path=self.db_path)

    def tearDown(self):
        """Clean up"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_task_tracker_initialization(self):
        """Test TaskTracker creates database"""
        from task_tracker import TaskTracker
        tracker = TaskTracker(self.config)
        self.assertTrue(os.path.exists(self.db_path))

    def test_create_task(self):
        """Test creating a new task"""
        from task_tracker import TaskTracker
        tracker = TaskTracker(self.config)

        task = tracker.create_task(
            name="Test task",
            source_file="./test.md",
            metadata={"key": "value"}
        )

        self.assertIsNotNone(task.id)
        self.assertTrue(task.id.startswith("task_"))
        self.assertEqual(task.name, "Test task")
        self.assertEqual(task.status, TaskStatus.PENDING)

    def test_get_task(self):
        """Test retrieving a task"""
        from task_tracker import TaskTracker
        tracker = TaskTracker(self.config)

        created = tracker.create_task(name="Test", source_file="./test.md")
        retrieved = tracker.get_task(created.id)

        self.assertIsNotNone(retrieved)
        self.assertEqual(created.id, retrieved.id)
        self.assertEqual(created.name, retrieved.name)

    def test_update_task_status(self):
        """Test updating task status"""
        from task_tracker import TaskTracker
        tracker = TaskTracker(self.config)

        task = tracker.create_task(name="Test", source_file="./test.md")
        result = tracker.update_task_status(task.id, TaskStatus.IN_PROGRESS)

        self.assertTrue(result)

        updated = tracker.get_task(task.id)
        self.assertEqual(updated.status, TaskStatus.IN_PROGRESS)
        self.assertIsNotNone(updated.started_at)

    def test_increment_iteration(self):
        """Test incrementing iteration count"""
        from task_tracker import TaskTracker
        tracker = TaskTracker(self.config)

        task = tracker.create_task(name="Test", source_file="./test.md")
        new_count = tracker.increment_iteration(task.id)

        self.assertEqual(new_count, 1)

        task = tracker.get_task(task.id)
        self.assertEqual(task.iteration_count, 1)
        self.assertIsNotNone(task.last_continuation_at)

    def test_get_active_tasks(self):
        """Test getting active tasks"""
        from task_tracker import TaskTracker
        tracker = TaskTracker(self.config)

        # Create multiple tasks
        tracker.create_task(name="Task 1", source_file="./t1.md")
        tracker.create_task(name="Task 2", source_file="./t2.md")
        task3 = tracker.create_task(name="Task 3", source_file="./t3.md")

        # Complete one
        tracker.update_task_status(task3.id, TaskStatus.COMPLETED)

        active = tracker.get_active_tasks()
        self.assertEqual(len(active), 2)

    def test_global_iteration_count(self):
        """Test global iteration tracking"""
        from task_tracker import TaskTracker
        tracker = TaskTracker(self.config)

        self.assertEqual(tracker.get_global_iteration_count(), 0)

        tracker.increment_global_iteration()
        self.assertEqual(tracker.get_global_iteration_count(), 1)

        tracker.increment_global_iteration()
        self.assertEqual(tracker.get_global_iteration_count(), 2)

        tracker.reset_global_iteration()
        self.assertEqual(tracker.get_global_iteration_count(), 0)


class TestCompletionDetector(unittest.TestCase):
    """Test CompletionDetector"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = RalphWiggumConfig(
            done_folder=os.path.join(self.temp_dir, "Done"),
            failed_folder=os.path.join(self.temp_dir, "Failed"),
            emergency_stop_file=os.path.join(self.temp_dir, ".ralph_stop")
        )
        os.makedirs(self.config.done_folder, exist_ok=True)

    def tearDown(self):
        """Clean up"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_check_file_moved_complete(self):
        """Test file moved completion detection"""
        from completion_detector import CompletionDetector

        detector = CompletionDetector(self.config)

        # Create source file
        source_file = os.path.join(self.temp_dir, "task.md")
        with open(source_file, "w") as f:
            f.write("Test content")

        task = TrackedTask(
            id="task_1",
            name="Test",
            source_file=source_file,
            completion_criteria=CompletionCriteria(
                type=CompletionType.FILE_MOVED,
                destination_folder=self.config.done_folder
            )
        )

        # File not in Done yet
        is_complete, reason = detector.check_completion(task)
        self.assertFalse(is_complete)

        # Move file to Done
        done_file = os.path.join(self.config.done_folder, "task.md")
        os.rename(source_file, done_file)

        # Now should be complete
        is_complete, reason = detector.check_completion(task)
        self.assertTrue(is_complete)

    def test_check_status_marker_complete(self):
        """Test status marker completion detection"""
        from completion_detector import CompletionDetector

        detector = CompletionDetector(self.config)

        # Create file without marker
        source_file = os.path.join(self.temp_dir, "task.md")
        with open(source_file, "w") as f:
            f.write("Test content")

        task = TrackedTask(
            id="task_1",
            name="Test",
            source_file=source_file,
            completion_criteria=CompletionCriteria(
                type=CompletionType.STATUS_MARKER,
                status_markers=["status: completed"]
            )
        )

        # Not complete yet
        is_complete, reason = detector.check_completion(task)
        self.assertFalse(is_complete)

        # Add status marker
        with open(source_file, "w") as f:
            f.write("Test content\nstatus: completed")

        # Now should be complete
        is_complete, reason = detector.check_completion(task)
        self.assertTrue(is_complete)

    def test_check_max_iterations(self):
        """Test max iterations check"""
        from completion_detector import CompletionDetector

        detector = CompletionDetector(self.config)

        task = TrackedTask(
            id="task_1",
            name="Test",
            source_file="./test.md",
            iteration_count=5,
            max_iterations=5
        )

        exceeded, status = detector.check_max_iterations(task)
        self.assertTrue(exceeded)
        self.assertIn("Max iterations", status)

    def test_emergency_stop(self):
        """Test emergency stop detection"""
        from completion_detector import CompletionDetector

        detector = CompletionDetector(self.config)

        # No stop file
        self.assertFalse(detector.check_emergency_stop())

        # Create stop file
        with open(self.config.emergency_stop_file, "w") as f:
            f.write("stop")

        self.assertTrue(detector.check_emergency_stop())


class TestPromptInjector(unittest.TestCase):
    """Test PromptInjector"""

    def test_get_continuation_prompt(self):
        """Test generating continuation prompt"""
        from prompt_injector import PromptInjector

        injector = PromptInjector()

        task = TrackedTask(
            id="task_1",
            name="Process invoices",
            source_file="./invoices.md",
            iteration_count=2,
            max_iterations=5
        )

        prompt = injector.get_continuation_prompt(task)

        self.assertIn("Task Continuation", prompt)
        self.assertIn("Process invoices", prompt)
        self.assertIn("Iteration 3/5", prompt)

    def test_get_failure_prompt(self):
        """Test generating failure prompt"""
        from prompt_injector import PromptInjector

        injector = PromptInjector()

        task = TrackedTask(
            id="task_1",
            name="Test task",
            source_file="./test.md",
            iteration_count=5,
            max_iterations=5
        )

        prompt = injector.get_failure_prompt(task, "Max iterations reached")

        self.assertIn("Task Failed", prompt)
        self.assertIn("Max iterations reached", prompt)


if __name__ == "__main__":
    unittest.main()
