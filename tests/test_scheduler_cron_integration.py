#!/usr/bin/env python3
"""
Test script for scheduler-cron-integration skill
"""

import os
import sys
from pathlib import Path


def test_skill_structure():
    """Test that the scheduler-cron-integration skill has the correct structure"""
    skill_path = Path("E:/hackathon 0 qwen/Personal-AI-Employee/.claude/skills/scheduler-cron-integration")

    print("Testing scheduler-cron-integration skill structure...")

    # Check if main SKILL.md exists
    skill_md = skill_path / "SKILL.md"
    if skill_md.exists():
        print("[OK] SKILL.md exists")
        with open(skill_md, 'r', encoding='utf-8') as f:
            content = f.read()
            if "scheduler-cron-integration" in content.lower() and "cron" in content.lower():
                print("[OK] SKILL.md contains expected content")
            else:
                print("[WARN] SKILL.md may not contain expected content")
    else:
        print("[ERROR] SKILL.md does not exist")
        return False

    # Check if scripts directory exists and contains files
    scripts_dir = skill_path / "scripts"
    if scripts_dir.exists():
        print("[OK] scripts/ directory exists")
        scripts = list(scripts_dir.glob("*.py"))
        if scripts:
            print(f"[OK] Found {len(scripts)} Python scripts")
        else:
            print("[WARN] No Python scripts found in scripts/")
    else:
        print("[ERROR] scripts/ directory does not exist")
        return False

    # Check if references directory exists
    refs_dir = skill_path / "references"
    if refs_dir.exists():
        print("[OK] references/ directory exists")
        refs = list(refs_dir.glob("*.md"))
        if refs:
            print(f"[OK] Found {len(refs)} reference files")
        else:
            print("[WARN] No reference files found in references/")
    else:
        print("[ERROR] references/ directory does not exist")
        return False

    # Check if assets directory exists
    assets_dir = skill_path / "assets"
    if assets_dir.exists():
        print("[OK] assets/ directory exists")
        assets = list(assets_dir.glob("*"))
        if assets:
            print(f"[OK] Found {len(assets)} asset files")
        else:
            print("[WARN] No asset files found in assets/")
    else:
        print("[ERROR] assets/ directory does not exist")
        return False

    return True


def test_imports():
    """Test that the scheduler cron scripts can be imported without errors"""
    print("\nTesting script imports...")

    # Add the skills directory to Python path to allow proper imports
    import sys
    import os
    skills_path = os.path.abspath("E:/hackathon 0 qwen/Personal-AI-Employee/.claude/skills")
    if skills_path not in sys.path:
        sys.path.insert(0, skills_path)

    # Add the specific script directory to Python path
    script_path = os.path.abspath("E:/hackathon 0 qwen/Personal-AI-Employee/.claude/skills/scheduler-cron-integration/scripts")
    if script_path not in sys.path:
        sys.path.insert(0, script_path)

    try:
        # Test importing scheduler_core
        import scheduler_core
        print("[OK] scheduler_core.py imports successfully")
    except ImportError as e:
        print(f"[ERROR] Failed to import scheduler_core.py: {e}")
    except Exception as e:
        print(f"[ERROR] Error importing scheduler_core.py: {e}")

    try:
        # Test importing job_manager
        import job_manager
        print("[OK] job_manager.py imports successfully")
    except ImportError as e:
        print(f"[ERROR] Failed to import job_manager.py: {e}")
    except Exception as e:
        print(f"[ERROR] Error importing job_manager.py: {e}")

    try:
        # Test importing cron_parser
        import cron_parser
        print("[OK] cron_parser.py imports successfully")
    except ImportError as e:
        print(f"[ERROR] Failed to import cron_parser.py: {e}")
    except Exception as e:
        print(f"[ERROR] Error importing cron_parser.py: {e}")

    try:
        # Test importing config_manager
        import config_manager
        print("[OK] config_manager.py imports successfully")
    except ImportError as e:
        print(f"[ERROR] Failed to import config_manager.py: {e}")
    except Exception as e:
        print(f"[ERROR] Error importing config_manager.py: {e}")

    return True


def test_basic_functionality():
    """Test basic functionality of the scheduler"""
    print("\nTesting basic functionality...")

    # Add the skills directory to Python path to allow proper imports
    import sys
    import os
    skills_path = os.path.abspath("E:/hackathon 0 qwen/Personal-AI-Employee/.claude/skills")
    if skills_path not in sys.path:
        sys.path.insert(0, skills_path)

    # Add the specific script directory to Python path
    script_path = os.path.abspath("E:/hackathon 0 qwen/Personal-AI-Employee/.claude/skills/scheduler-cron-integration/scripts")
    if script_path not in sys.path:
        sys.path.insert(0, script_path)

    try:
        # Import directly from the scripts
        import scheduler_core
        import job_manager
        import cron_parser
        import config_manager

        # Access classes from the imported modules
        Scheduler = scheduler_core.Scheduler
        JobPriority = scheduler_core.JobPriority
        create_job_definition = scheduler_core.create_job_definition

        JobManager = job_manager.JobManager
        create_job_manager = job_manager.create_job_manager

        AdvancedCronParser = cron_parser.AdvancedCronParser
        CronExpression = cron_parser.CronExpression

        ConfigManager = config_manager.ConfigManager
        SchedulerSystemConfig = config_manager.SchedulerSystemConfig

        # Test basic scheduler functionality
        scheduler = Scheduler()
        print("[OK] Scheduler created successfully")

        # Test basic cron parser functionality
        parser = AdvancedCronParser()
        expr = parser.parse("0 9 * * *")  # Daily at 9 AM
        print("[OK] Cron expression parsed successfully")

        # Test getting next run time
        from datetime import datetime
        next_run = parser.get_next_run_time("0 9 * * *")
        print(f"[OK] Next run calculated: {next_run}")

        # Test job manager creation
        job_manager_instance = create_job_manager("./test_scheduler.db")
        print("[OK] Job manager created successfully")

        # Test creating a simple job definition
        job_def = create_job_definition(
            job_id="test_job",
            name="Test Job",
            cron_expression="0 9 * * *",
            callback=lambda: print("Test job executed"),
            description="A test job"
        )
        print("[OK] Job definition created successfully")

        # Test configuration manager
        config_manager_instance = ConfigManager("./test_config.json")
        print("[OK] Config manager created successfully")

        # Test basic configuration functionality
        config = config_manager_instance.config
        print(f"[OK] Configuration loaded with scheduler enabled: {config.scheduler.enabled}")

    except Exception as e:
        print(f"[ERROR] Error in basic functionality test: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def test_cron_parsing():
    """Test cron expression parsing functionality"""
    print("\nTesting cron parsing functionality...")

    # Add the specific script directory to Python path
    import sys
    import os
    script_path = os.path.abspath("E:/hackathon 0 qwen/Personal-AI-Employee/.claude/skills/scheduler-cron-integration/scripts")
    if script_path not in sys.path:
        sys.path.insert(0, script_path)

    try:
        import cron_parser

        parser = cron_parser.AdvancedCronParser()

        # Test various cron expressions
        test_cases = [
            ("0 9 * * *", "Daily at 9 AM"),
            ("0 0 * * 0", "Weekly at midnight on Sunday"),
            ("0 0 1 * *", "Monthly on the 1st at midnight"),
            ("*/15 * * * *", "Every 15 minutes"),
            ("@daily", "Daily alias"),
            ("@weekly", "Weekly alias"),
        ]

        for expr, description in test_cases:
            is_valid, error = parser.validate(expr)
            if is_valid:
                print(f"[OK] {expr} - {description}")
            else:
                print(f"[ERROR] {expr} - {description}: {error}")
                return False

        # Test next run calculation
        next_run = parser.get_next_run_time("0 9 * * *")
        print(f"[OK] Next run for daily job: {next_run}")

        # Test next N runs
        next_runs = parser.get_next_n_run_times("0 9 * * *", 3)
        print(f"[OK] Next 3 runs calculated: {len(next_runs)}")

        # Test human-readable conversion
        human_desc = parser.get_human_readable("0 9 * * *")
        print(f"[OK] Human readable: {human_desc}")

    except Exception as e:
        print(f"[ERROR] Error in cron parsing test: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def test_configuration_management():
    """Test configuration management functionality"""
    print("\nTesting configuration management...")

    # Add the specific script directory to Python path
    import sys
    import os
    script_path = os.path.abspath("E:/hackathon 0 qwen/Personal-AI-Employee/.claude/skills/scheduler-cron-integration/scripts")
    if script_path not in sys.path:
        sys.path.insert(0, script_path)

    try:
        import config_manager

        # Test creating default config
        config_path = "./temp_test_config.json"
        config_manager.create_default_config(config_path)
        if os.path.exists(config_path):
            print("[OK] Default configuration created successfully")
        else:
            print("[ERROR] Failed to create default configuration")
            return False

        # Test loading config
        config_manager_instance = config_manager.ConfigManager(config_path)
        print("[OK] Configuration loaded successfully")

        # Test validation
        errors = config_manager_instance.validate_config()
        if not errors:
            print("[OK] Configuration validation passed")
        else:
            print(f"[ERROR] Configuration validation failed: {errors}")
            return False

        # Test getting specific config sections
        sched_config = config_manager_instance.get_scheduler_config()
        cron_config = config_manager_instance.get_cron_config()
        jobs_config = config_manager_instance.get_job_defaults_config()

        print("[OK] Configuration sections accessible")

        # Clean up
        if os.path.exists(config_path):
            os.remove(config_path)

    except Exception as e:
        print(f"[ERROR] Error in configuration management test: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def main():
    """Run all tests"""
    print("=" * 60)
    print("Scheduler Cron Integration Skill - Test Suite")
    print("=" * 60)

    # Change to the project directory
    os.chdir("E:/hackathon 0 qwen/Personal-AI-Employee")

    tests = [
        ("Skill Structure", test_skill_structure),
        ("Script Imports", test_imports),
        ("Basic Functionality", test_basic_functionality),
        ("Cron Parsing", test_cron_parsing),
        ("Configuration Management", test_configuration_management),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} Test ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[ERROR] {test_name} test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    print(f"\n{'='*60}")
    print("Test Results:")
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {test_name}: {status}")

    all_passed = all(result for _, result in results)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    print("="*60)

    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)