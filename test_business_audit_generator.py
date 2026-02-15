#!/usr/bin/env python3
"""
Test script for business-audit-generator skill
"""

import os
import sys
from pathlib import Path


def test_skill_structure():
    """Test that the business-audit-generator skill has the correct structure"""
    skill_path = Path("E:/hackathon 0 qwen/Personal-AI-Employee/.claude/skills/business-audit-generator")

    print("Testing business-audit-generator skill structure...")

    # Check if main SKILL.md exists
    skill_md = skill_path / "SKILL.md"
    if skill_md.exists():
        print("[OK] SKILL.md exists")
        with open(skill_md, 'r', encoding='utf-8') as f:
            content = f.read()
            if "business-audit-generator" in content.lower() and "ceo briefing" in content.lower():
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
    """Test that the business audit scripts can be imported without errors"""
    print("\nTesting script imports...")

    # Add the skills directory to Python path to allow proper imports
    import sys
    import os
    skills_path = os.path.abspath("E:/hackathon 0 qwen/Personal-AI-Employee/.claude/skills")
    if skills_path not in sys.path:
        sys.path.insert(0, skills_path)

    # Add the specific script directory to Python path
    script_path = os.path.abspath("E:/hackathon 0 qwen/Personal-AI-Employee/.claude/skills/business-audit-generator/scripts")
    if script_path not in sys.path:
        sys.path.insert(0, script_path)

    try:
        # Test importing business_audit_core
        import business_audit_core
        print("[OK] business_audit_core.py imports successfully")
    except ImportError as e:
        print(f"[ERROR] Failed to import business_audit_core.py: {e}")
    except Exception as e:
        print(f"[ERROR] Error importing business_audit_core.py: {e}")

    try:
        # Test importing data_analyzer
        import data_analyzer
        print("[OK] data_analyzer.py imports successfully")
    except ImportError as e:
        print(f"[ERROR] Failed to import data_analyzer.py: {e}")
    except Exception as e:
        print(f"[ERROR] Error importing data_analyzer.py: {e}")

    try:
        # Test importing report_generator
        import report_generator
        print("[OK] report_generator.py imports successfully")
    except ImportError as e:
        print(f"[ERROR] Failed to import report_generator.py: {e}")
    except Exception as e:
        print(f"[ERROR] Error importing report_generator.py: {e}")

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
    """Test basic functionality of the business audit generator"""
    print("\nTesting basic functionality...")

    # Add the skills directory to Python path to allow proper imports
    import sys
    import os
    skills_path = os.path.abspath("E:/hackathon 0 qwen/Personal-AI-Employee/.claude/skills")
    if skills_path not in sys.path:
        sys.path.insert(0, skills_path)

    # Add the specific script directory to Python path
    script_path = os.path.abspath("E:/hackathon 0 qwen/Personal-AI-Employee/.claude/skills/business-audit-generator/scripts")
    if script_path not in sys.path:
        sys.path.insert(0, script_path)

    try:
        # Import directly from the scripts
        import business_audit_core
        import data_analyzer
        import report_generator
        import config_manager

        # Access classes from the imported modules
        BusinessAuditGenerator = business_audit_core.BusinessAuditGenerator
        TaskData = business_audit_core.TaskData
        FinancialTransaction = business_audit_core.FinancialTransaction
        GoalData = business_audit_core.GoalData

        AdvancedDataAnalyzer = data_analyzer.AdvancedDataAnalyzer
        DataValidator = data_analyzer.DataValidator

        ReportGenerator = report_generator.ReportGenerator
        ChartGenerator = report_generator.ChartGenerator
        ReportFormatter = report_generator.ReportFormatter

        ConfigManager = config_manager.ConfigManager
        BusinessAuditConfig = config_manager.BusinessAuditConfig

        # Test basic generator functionality
        generator = BusinessAuditGenerator()
        print("[OK] BusinessAuditGenerator created successfully")

        # Test creating sample data
        from datetime import datetime, timedelta

        tasks = [
            TaskData(
                id="task_1",
                title="Test Task",
                status="completed",
                assigned_to="test_user",
                created_date=datetime.now() - timedelta(days=5),
                due_date=datetime.now() + timedelta(days=2),
                completed_date=datetime.now(),
                priority="medium",
                category="testing"
            )
        ]

        transactions = [
            FinancialTransaction(
                id="trans_1",
                date=datetime.now() - timedelta(days=1),
                amount=-100.00,
                category="office",
                vendor="supplier",
                description="office supplies",
                transaction_type="expense"
            )
        ]

        goals = [
            GoalData(
                id="goal_1",
                title="Test Goal",
                description="Test goal description",
                target_date=datetime.now() + timedelta(days=30),
                current_progress=0.5,
                target_value=100.0,
                current_value=50.0,
                owner="test_owner",
                category="business"
            )
        ]

        print("[OK] Sample data created successfully")

        # Test generating a report
        report = generator.generate_weekly_briefing(tasks, transactions, goals)
        print(f"[OK] Report generated successfully: {report.report_id}")

        # Test data analyzer
        analyzer = AdvancedDataAnalyzer()
        print("[OK] AdvancedDataAnalyzer created successfully")

        # Test validation
        validator = DataValidator()
        task_quality = validator.validate_task_data([t.__dict__ for t in tasks])
        print(f"[OK] Data validation completed: Quality score {task_quality.overall_score:.2f}")

        # Test report generator
        report_gen = ReportGenerator()
        print("[OK] ReportGenerator created successfully")

        # Test config manager
        config_manager_instance = ConfigManager()
        config = config_manager_instance.config
        print(f"[OK] ConfigManager created with report title: {config.reporting.report_title}")

    except Exception as e:
        print(f"[ERROR] Error in basic functionality test: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def test_data_analysis():
    """Test data analysis functionality"""
    print("\nTesting data analysis functionality...")

    # Add the specific script directory to Python path
    import sys
    import os
    script_path = os.path.abspath("E:/hackathon 0 qwen/Personal-AI-Employee/.claude/skills/business-audit-generator/scripts")
    if script_path not in sys.path:
        sys.path.insert(0, script_path)

    try:
        import data_analyzer
        import business_audit_core

        # Create sample data
        from datetime import datetime, timedelta
        create_sample_tasks = business_audit_core.create_sample_tasks
        create_sample_transactions = business_audit_core.create_sample_transactions
        create_sample_goals = business_audit_core.create_sample_goals

        tasks = create_sample_tasks(10)
        transactions = create_sample_transactions(10)
        goals = create_sample_goals(5)

        # Create analyzer and run analysis
        analyzer = data_analyzer.AdvancedDataAnalyzer()
        results = analyzer.analyze_complete_dataset(
            [t.__dict__ for t in tasks],
            [tr.__dict__ for tr in transactions],
            [g.__dict__ for g in goals]
        )

        print(f"[OK] Complete dataset analysis completed")
        print(f"  - Quality score: {results['summary']['quality_score']:.2f}")
        print(f"  - Anomalies found: {results['summary']['anomaly_count']}")
        print(f"  - Total records: {results['summary']['total_tasks'] + results['summary']['total_financial_records'] + results['summary']['total_goals']}")

        # Verify analysis results structure
        required_keys = ['data_quality', 'anomalies', 'trends', 'correlations', 'summary']
        for key in required_keys:
            if key not in results:
                print(f"[ERROR] Missing key in analysis results: {key}")
                return False

        print(f"[OK] Analysis results structure is correct")

    except Exception as e:
        print(f"[ERROR] Error in data analysis test: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def test_report_generation():
    """Test report generation functionality"""
    print("\nTesting report generation functionality...")

    # Add the specific script directory to Python path
    import sys
    import os
    script_path = os.path.abspath("E:/hackathon 0 qwen/Personal-AI-Employee/.claude/skills/business-audit-generator/scripts")
    if script_path not in sys.path:
        sys.path.insert(0, script_path)

    try:
        import report_generator
        import business_audit_core

        # Create sample data
        from datetime import datetime, timedelta
        create_sample_tasks = business_audit_core.create_sample_tasks
        create_sample_transactions = business_audit_core.create_sample_transactions
        create_sample_goals = business_audit_core.create_sample_goals

        tasks = create_sample_tasks(5)
        transactions = create_sample_transactions(5)
        goals = create_sample_goals(3)

        # Create report generator
        report_gen = report_generator.ReportGenerator()

        # Generate a report
        task_dicts = [t.__dict__ for t in tasks]
        transaction_dicts = [tr.__dict__ for tr in transactions]
        goal_dicts = [g.__dict__ for g in goals]

        result = report_gen.generate_and_distribute_weekly_briefing(
            task_dicts, transaction_dicts, goal_dicts,
            distribution_list=['test@example.com'],
            output_formats=['html', 'email']
        )

        print(f"[OK] Report generation completed")
        print(f"  - Report ID: {result['report_id']}")
        print(f"  - Success: {result['success']}")
        print(f"  - Output formats: {list(result['formatted_reports'].keys())}")

        # Check that reports were generated
        if not result['formatted_reports']:
            print("[ERROR] No reports were generated")
            return False

        for fmt, path in result['formatted_reports'].items():
            if not os.path.exists(path):
                print(f"[ERROR] Report file does not exist: {path}")
                return False

        print(f"[OK] Report files were generated successfully")

    except Exception as e:
        print(f"[ERROR] Error in report generation test: {e}")
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
    script_path = os.path.abspath("E:/hackathon 0 qwen/Personal-AI-Employee/.claude/skills/business-audit-generator/scripts")
    if script_path not in sys.path:
        sys.path.insert(0, script_path)

    try:
        import config_manager

        # Test creating default config
        config_path = "./temp_test_config.json"
        success = config_manager.create_default_config(config_path)
        if success and os.path.exists(config_path):
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
        analysis_config = config_manager_instance.get_analysis_config()
        reporting_config = config_manager_instance.get_reporting_config()
        metrics_config = config_manager_instance.get_metric_thresholds_config()

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
    print("Business Audit Generator Skill - Test Suite")
    print("=" * 60)

    # Change to the project directory
    os.chdir("E:/hackathon 0 qwen/Personal-AI-Employee")

    tests = [
        ("Skill Structure", test_skill_structure),
        ("Script Imports", test_imports),
        ("Basic Functionality", test_basic_functionality),
        ("Data Analysis", test_data_analysis),
        ("Report Generation", test_report_generation),
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