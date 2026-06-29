#!/usr/bin/env python3
"""
FinCompli Baseline - One-Click Setup Script
FinCompli Baseline - 一鍵初始化腳本

This script initializes the project environment:
此腳本初始化項目環境：
1. Creates necessary directories / 創建必要目錄
2. Copies .env.example to .env if not exists / 如果不存在則複製 .env.example 到 .env
3. Provides next steps / 提供後續步驟

[Business Purpose] Ensures consistent setup across all team members
[業務目的] 確保所有團隊成員的環境設置一致
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def print_header(message: str):
    """Print formatted header / 打印格式化標題"""
    print("\n" + "=" * 70)
    print(f"  {message}")
    print("=" * 70)


def create_directories():
    """Create all necessary directories / 創建所有必要目錄"""
    print_header("Step 1: Creating Directories / 步驟 1：創建目錄")

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
    """Copy .env.example to .env if not exists / 如果不存在則複製環境配置文件"""
    print_header("Step 2: Setting up Environment File / 步驟 2：設置環境文件")

    env_example = Path(".env.example")
    env_file = Path(".env")

    if not env_file.exists():
        if env_example.exists():
            shutil.copy(env_example, env_file)
            print(f"  ✓ Copied .env.example → .env")
            print(f"  ℹ️  Please review and update .env with your local settings")
            print(f"  ℹ️  請檢查並更新 .env 中的本地設置")
        else:
            print(f"  ⚠️  .env.example not found")
    else:
        print(f"  ℹ️  .env already exists, skipping")


def check_python_version():
    """Check Python version / 檢查 Python 版本"""
    print_header("Step 3: Checking Python Version / 步驟 3：檢查 Python 版本")

    version = sys.version_info
    print(f"  Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"  ❌ Python 3.9+ is required. Current: {version.major}.{version.minor}")
        print(f"  ❌ 需要 Python 3.9+。當前版本：{version.major}.{version.minor}")
        return False

    if version.major == 3 and version.minor < 11:
        print(f"  ⚠️  Python 3.11+ is recommended. Current: {version.major}.{version.minor}")
        print(f"  ⚠️  建議使用 Python 3.11+。當前版本：{version.major}.{version.minor}")
        print(f"  ℹ️  Continuing with Python {version.major}.{version.minor}...")

    print(f"  ✓ Python version is compatible")
    return True


def install_dependencies():
    """Prompt to install dependencies / 提示安裝依賴"""
    print_header("Step 4: Dependencies / 步驟 4：依賴管理")

    print("  To install dependencies, run:")
    print("  要安裝依賴，請運行：")
    print()
    print("    pip install -r requirements.txt")
    print()
    print("  Or if you prefer using a virtual environment:")
    print("  或者如果您更喜歡使用虛擬環境：")
    print()
    print("    python -m venv venv")
    print("    source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
    print("    pip install -r requirements.txt")
    print()


def print_next_steps():
    """Print next steps / 打印後續步驟"""
    print_header("Setup Complete! / 設置完成！")

    print()
    print("  Next Steps / 後續步驟：")
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
    """Main setup function / 主設置函數"""
    print_header("FinCompli Baseline - Setup Script")
    print("  Version 0.1")
    print("  Enterprise Multi-Agent Compliance System")
    print("  企業級多 Agent 合規系統")

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
        print(f"\n  ❌ Error during setup: {e}")
        print(f"  ❌ 設置過程中出錯：{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
