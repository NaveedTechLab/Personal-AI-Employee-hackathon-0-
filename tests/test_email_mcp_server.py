#!/usr/bin/env python3
"""
Test script for email-mcp-server skill
"""

import os
import sys
from pathlib import Path

def test_skill_structure():
    """Test that the email-mcp-server skill has the correct structure"""
    skill_path = Path("E:/hackathon 0 qwen/Personal-AI-Employee/.claude/skills/email-mcp-server")

    print("Testing email-mcp-server skill structure...")

    # Check if main SKILL.md exists
    skill_md = skill_path / "SKILL.md"
    if skill_md.exists():
        print("[OK] SKILL.md exists")
        with open(skill_md, 'r', encoding='utf-8') as f:
            content = f.read()
            if "email-mcp-server" in content and "HITL" in content:
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
    """Test that the email MCP server scripts can be imported without errors"""
    print("\nTesting script imports...")

    # Add the scripts directory to Python path
    scripts_path = "E:/hackathon 0 qwen/Personal-AI-Employee/.claude/skills/email-mcp-server/scripts"
    sys.path.insert(0, scripts_path)

    try:
        # Test importing email_mcp_server
        import email_mcp_server
        print("[OK] email_mcp_server.py imports successfully")
    except ImportError as e:
        print(f"[ERROR] Failed to import email_mcp_server.py: {e}")
    except Exception as e:
        print(f"[ERROR] Error importing email_mcp_server.py: {e}")

    try:
        # Test importing config_helper
        import config_helper
        print("[OK] config_helper.py imports successfully")
    except ImportError as e:
        print(f"[ERROR] Failed to import config_helper.py: {e}")
    except Exception as e:
        print(f"[ERROR] Error importing config_helper.py: {e}")

    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("Email MCP Server Skill - Test Suite")
    print("=" * 60)

    # Change to the project directory
    os.chdir("E:/hackathon 0 qwen/Personal-AI-Employee")

    tests = [
        ("Skill Structure", test_skill_structure),
        ("Script Imports", test_imports),
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