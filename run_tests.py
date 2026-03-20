#!/usr/bin/env python3
"""
Automated test runner - executes all tests and generates report.
Run this instead of pytest directly for consistent results.
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

def run_tests():
    """Run all tests and generate report."""
    
    print("=" * 80)
    print(f"🧪 VibeForge - Automated Test Suite")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Run pytest with coverage
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=json",
        "--cov-report=html",
        "--tb=short",
        "-x"  # Stop on first failure
    ]
    
    print(f"\n📋 Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    # Print summary
    print("\n" + "=" * 80)
    if result.returncode == 0:
        print("✅ ALL TESTS PASSED!")
        print("📊 Coverage report saved to: htmlcov/index.html")
    else:
        print("❌ TESTS FAILED - See output above")
        print("💡 Tips:")
        print("   - Check test output above for details")
        print("   - Run specific test: pytest tests/unit/test_<module>.py -v")
        print("   - Debug mode: pytest tests/ -v -s")
    print("=" * 80)
    
    sys.exit(result.returncode)

if __name__ == "__main__":
    run_tests()
