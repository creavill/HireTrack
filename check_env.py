"""
Environment validation script for Hammy the Hire Tracker.

Run this script to check if your environment is properly set up.
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.11+"""
    version = sys.version_info
    print(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"✗ ERROR: Python 3.11+ required, you have {version.major}.{version.minor}.{version.micro}")
        return False
    return True

def check_virtual_env():
    """Check if running in a virtual environment"""
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )

    if in_venv:
        print("✓ Running in virtual environment")
        return True
    else:
        print("⚠ WARNING: Not in a virtual environment")
        print("  It's recommended to use: python -m venv venv")
        print("  Then activate with: venv\\Scripts\\activate (Windows) or source venv/bin/activate (Mac/Linux)")
        return False

def check_required_packages():
    """Check if all required packages are installed"""
    required_packages = [
        'flask',
        'flask_cors',
        'google.auth',
        'google_auth_oauthlib',
        'googleapiclient',
        'bs4',  # beautifulsoup4
        'anthropic',
        'dotenv',  # python-dotenv
        'yaml',  # pyyaml
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} installed")
        except ImportError:
            print(f"✗ {package} NOT installed")
            missing.append(package)

    if missing:
        print(f"\n✗ ERROR: Missing packages: {', '.join(missing)}")
        print("  Run: pip install -r requirements-local.txt")
        return False
    return True

def check_config_files():
    """Check if required config files exist"""
    required_files = {
        'config.yaml': 'Copy from config.example.yaml and edit',
        '.env': 'Create with ANTHROPIC_API_KEY=your_key',
    }

    all_exist = True
    for filename, instruction in required_files.items():
        if Path(filename).exists():
            print(f"✓ {filename} exists")
        else:
            print(f"✗ {filename} missing - {instruction}")
            all_exist = False

    return all_exist

def check_api_key():
    """Check if API key is set"""
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key and api_key != 'your_key_here' and api_key != 'your_anthropic_api_key_here':
        print("✓ ANTHROPIC_API_KEY is set")
        return True
    else:
        print("✗ ANTHROPIC_API_KEY not set or using placeholder value")
        print("  Set it in your .env file")
        return False

def main():
    print("\n" + "="*60)
    print("  Hammy the Hire Tracker - Environment Check")
    print("="*60 + "\n")

    checks = [
        ("Python Version", check_python_version),
        ("Virtual Environment", check_virtual_env),
        ("Required Packages", check_required_packages),
        ("Configuration Files", check_config_files),
        ("API Key", check_api_key),
    ]

    results = []
    for name, check_func in checks:
        print(f"\n[Checking {name}]")
        results.append(check_func())

    print("\n" + "="*60)
    if all(results[::2]):  # Check only critical checks (skip virtual env warning)
        print("✓ All checks passed! You're ready to run Hammy.")
        print("\nRun: python local_app.py")
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        print("\nFor help, see TROUBLESHOOTING.md")
    print("="*60 + "\n")

    return 0 if all(results[::2]) else 1

if __name__ == '__main__':
    sys.exit(main())
