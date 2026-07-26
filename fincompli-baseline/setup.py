#!/usr/bin/env python3
"""
FinCompli Baseline - One-Click Setup Script

This script initializes the project environment:
1. Creates necessary directories
2. Copies .env.example to .env if not exists
3. Provides next steps

[Business Purpose] Ensures consistent setup across all team members
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def print_header(message: str):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {message}")
    print("=" * 70)


def create_directories():
    """Create all necessary directories"""
    print_header("Step 1: Creating Directories")

    directories = [
        "data/chroma",
        "data/sqlite",
        "audit_logs",
        "mock_data/seeds"
    ]

    for directory in directories:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ Created: {directory}")


def setup_env_file():
    """Copy .env.example to .env if not exists"""
    print_header("Step 2: Setting up Environment File")

    env_example = Path(".env.example")
    env_file = Path(".env")

    if not env_file.exists():
        if env_example.exists():
            shutil.copy(env_example, env_file)
            print(f"  ✓ Copied .env.example → .env")
            print(f"  Please review and update .env with your local settings")
        else:
            print(f"  ⚠️  .env.example not found")
    else:
        print(f"  ℹ️  .env already exists, skipping")


def check_python_version():
    """Check Python version"""
    print_header("Step 3: Checking Python Version")

    version = sys.version_info
    print(f"  Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"  Python 3.9+ is required. Current: {version.major}.{version.minor}")
        return False

    if version.major == 3 and version.minor < 11:
        print(f"  Python 3.11+ is recommended. Current: {version.major}.{version.minor}")
        print(f"  Continuing with Python {version.major}.{version.minor}...")

    print(f"  ✓ Python version is compatible")
    return True


def install_dependencies():
    """Prompt to install dependencies"""
    print_header("Step 4: Dependencies")

    print("  To install dependencies, run:")
    print()
    print("    pip install -r requirements.txt")
    print()
    print("  Or if you prefer using a virtual environment:")
    print()
    print("    python -m venv venv")
    print("    source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
    print("    pip install -r requirements.txt")
    print()


def print_next_steps():
    """Print next steps"""
    print_header("Setup Complete!")

    print()
    print("  Next Steps:")
    print()
    print("  1. Install dependencies (if not already done):")
    print("     pip install -r requirements.txt")
    print()
    print("  2. Verify installation:")
    print("     python -c \"import langgraph; import chromadb; print('✓ OK')\"")
    print()
    print("  3. Generate mock data:")
    print("     python mock_data/seed_database.py")
    print()
    print("  4. Run a test scenario:")
    print("     python cli/interactive.py --scenario 02")
    print()
    print("  5. Start API server:")
    print("     uvicorn api.server:app --reload")
    print()
    print("  For more information, see README.md")
    print()


def main():
    """Main setup function"""
    print_header("FinCompli Baseline - Setup Script")
    print("  Version 0.1")
    print("  Enterprise Multi-Agent Compliance System")

    try:
        # Check Python version
        if not check_python_version():
            sys.exit(1)

        # Create directories
        create_directories()

        # Setup environment file
        setup_env_file()

        # Show install instructions
        install_dependencies()

        # Print next steps
        print_next_steps()

    except Exception as e:
        print(f"\n  Error during setup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
