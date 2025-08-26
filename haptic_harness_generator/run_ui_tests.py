#!/usr/bin/env python3
"""
Test runner for UI improvements
Runs all tests and provides a summary report
"""
import sys
import os
import subprocess
import tempfile
from pathlib import Path

def run_tests():
    """Run the UI improvement tests"""
    print("=" * 60)
    print("HAPTIC HARNESS UI IMPROVEMENTS - TEST SUITE")
    print("=" * 60)
    
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    test_file = script_dir / "test_ui_improvements.py"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"📁 Running tests from: {test_file}")
    print()
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_file), 
            "-v", 
            "--tb=short",
            "--color=yes"
        ], capture_output=True, text=True, cwd=script_dir)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
            return True
        else:
            print(f"\n❌ Tests failed with return code: {result.returncode}")
            return False
            
    except FileNotFoundError:
        print("❌ pytest not found. Please install pytest:")
        print("   pip install pytest")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def run_manual_test_checklist():
    """Display manual testing checklist"""
    print("\n" + "=" * 60)
    print("MANUAL TESTING CHECKLIST")
    print("=" * 60)
    
    checklist = [
        "1. Load 'Standard 6-sided' preset → Verify no 'Custom' during scroll",
        "2. Enter invalid value → See error within 500ms",
        "3. Fix error → Generate button enables immediately",
        "4. Scroll parameters → Validation panel stays visible",
        "5. Apply suggestion → Error clears without adjustment",
        "6. Check parameter labels → No confusing [0] brackets",
        "7. Check range labels → Enhanced styling with tooltips",
        "8. Check reference diagram → Has title and subtitle",
        "9. Check parameter alignment → Perfect grid alignment",
        "10. Check validation feedback → Comprehensive suggestions"
    ]
    
    print("Please manually verify the following:")
    print()
    for item in checklist:
        print(f"  {item}")
    
    print("\n📋 To run manual tests:")
    print("   python -m haptic_harness_generator.main")
    print()

if __name__ == "__main__":
    success = run_tests()
    run_manual_test_checklist()
    
    if success:
        print("🎉 UI improvements implementation complete!")
        print("   All automated tests passed.")
        print("   Please run manual tests to verify UI behavior.")
    else:
        print("⚠️  Some tests failed. Please review the output above.")
    
    sys.exit(0 if success else 1)
