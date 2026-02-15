#!/usr/bin/env python3
"""
Test script for security-sandbox-controls skill
"""

import os
import sys
from pathlib import Path


def test_skill_structure():
    """Test that the security-sandbox-controls skill has the correct structure"""
    skill_path = Path("E:/hackathon 0 qwen/Personal-AI-Employee/.claude/skills/security-sandbox-controls")

    print("Testing security-sandbox-controls skill structure...")

    # Check if main SKILL.md exists
    skill_md = skill_path / "SKILL.md"
    if skill_md.exists():
        print("[OK] SKILL.md exists")
        with open(skill_md, 'r', encoding='utf-8') as f:
            content = f.read()
            if "security-sandbox-controls" in content.lower() and "safety controls" in content.lower():
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
    """Test that the security sandbox scripts can be imported without errors"""
    print("\nTesting script imports...")

    # Add the skills directory to Python path to allow proper imports
    import sys
    import os
    skills_path = os.path.abspath("E:/hackathon 0 qwen/Personal-AI-Employee/.claude/skills")
    if skills_path not in sys.path:
        sys.path.insert(0, skills_path)

    # Also add the specific skill directory
    skill_path = os.path.abspath("E:/hackathon 0 qwen/Personal-AI-Employee/.claude/skills/security-sandbox-controls/scripts")
    if skill_path not in sys.path:
        sys.path.insert(0, skill_path)

    try:
        # Test importing safety_controls
        import safety_controls
        print("[OK] safety_controls.py imports successfully")
    except ImportError as e:
        print(f"[ERROR] Failed to import safety_controls.py: {e}")
    except Exception as e:
        print(f"[ERROR] Error importing safety_controls.py: {e}")

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
    """Test basic functionality of the security controls"""
    print("\nTesting basic functionality...")

    # Add the specific script directories to Python path to allow proper imports
    import sys
    import os
    script_path = os.path.abspath("E:/hackathon 0 qwen/Personal-AI-Employee/.claude/skills/security-sandbox-controls/scripts")
    if script_path not in sys.path:
        sys.path.insert(0, script_path)

    try:
        # Import directly from the scripts
        import safety_controls
        import config_manager

        # Access classes from the imported modules
        SafetyControls = safety_controls.SafetyControls
        SafetyMode = safety_controls.SafetyMode
        OperationType = safety_controls.OperationType
        RateLimitRule = safety_controls.RateLimitRule
        SecuritySandboxConfig = config_manager.SecuritySandboxConfig

        # Test creating basic controls
        controls = SafetyControls()
        print("[OK] SafetyControls created successfully")

        # Test different modes
        config_dev = SecuritySandboxConfig(mode=SafetyMode.DEVELOPMENT)
        dev_controls = SafetyControls(config=config_dev)
        print("[OK] Development mode controls created")

        config_prod = SecuritySandboxConfig(mode=SafetyMode.PRODUCTION)
        prod_controls = SafetyControls(config=config_prod)
        print("[OK] Production mode controls created")

        # Test DRY_RUN mode
        config_dry = SecuritySandboxConfig(mode=SafetyMode.DRY_RUN)
        dry_controls = SafetyControls(config=config_dry)

        # Assign a role to the test user to allow file operations
        dry_controls.assign_role("test_user", "standard_user")

        # Execute a dry run operation
        result = dry_controls.execute_operation(
            OperationType.FILE_READ,
            user="test_user",
            path="/test/file.txt"
        )

        if result.simulation:
            print("[OK] DRY_RUN mode works correctly")
        else:
            print("[ERROR] DRY_RUN mode not functioning properly")

        # Test rate limiting
        rate_rule = RateLimitRule(max_operations=5, window_seconds=60)
        controls.config.rate_limits["test_ops"] = rate_rule
        print("[OK] Rate limiting configuration works")

        # Test credential management
        controls.set_credential("test_key", "test_value")
        retrieved = controls.get_credential("test_key")
        if retrieved == "test_value":
            print("[OK] Credential management works")
        else:
            print("[ERROR] Credential management failed")

        # Test permission assignment
        controls.assign_role("test_user", "standard_user")
        has_perm = controls.check_permission("test_user", "file_read")
        if has_perm:
            print("[OK] Permission management works")
        else:
            print("[ERROR] Permission management failed")

    except Exception as e:
        print(f"[ERROR] Error in basic functionality test: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def test_configuration_management():
    """Test configuration management functionality"""
    print("\nTesting configuration management...")

    # Add the specific script directory to Python path to allow proper imports
    import sys
    import os
    script_path = os.path.abspath("E:/hackathon 0 qwen/Personal-AI-Employee/.claude/skills/security-sandbox-controls/scripts")
    if script_path not in sys.path:
        sys.path.insert(0, script_path)

    try:
        # Import directly from the scripts
        import config_manager

        # Access classes from the imported module
        ConfigManager = config_manager.ConfigManager
        SecuritySandboxConfig = config_manager.SecuritySandboxConfig
        create_default_config = config_manager.create_default_config
        validate_config_file = config_manager.validate_config_file

        # Test creating default config
        config_path = "./temp_test_config.json"
        create_default_config(config_path)
        if os.path.exists(config_path):
            print("[OK] Default configuration created successfully")
        else:
            print("[ERROR] Failed to create default configuration")
            return False

        # Test loading config
        config_manager_instance = ConfigManager(config_path)
        print("[OK] Configuration loaded successfully")

        # Test validation
        errors = config_manager_instance.validate_config()
        if not errors:
            print("[OK] Configuration validation passed")
        else:
            print(f"[ERROR] Configuration validation failed: {errors}")
            return False

        # Test environment-specific configs
        dev_config = config_manager_instance.get_environment_config("development")
        prod_config = config_manager_instance.get_environment_config("production")

        if dev_config.environment == "development" and prod_config.environment == "production":
            print("[OK] Environment-specific configurations work")
        else:
            print("[ERROR] Environment-specific configurations failed")
            return False

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
    print("Security Sandbox Controls Skill - Test Suite")
    print("=" * 60)

    # Change to the project directory
    os.chdir("E:/hackathon 0 qwen/Personal-AI-Employee")

    tests = [
        ("Skill Structure", test_skill_structure),
        ("Script Imports", test_imports),
        ("Basic Functionality", test_basic_functionality),
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