#!/usr/bin/env python3
"""
Stage 2 Runner — FinCompli + MemGuard SDK with Full Observability.

This script orchestrates the Stage 2 demo:
1. Verifies MemGuard SDK is installed
2. Verifies backend connectivity
3. Initializes all MemGuard components explicitly
4. Runs the compliance workflow with full tracing
5. Prints observability dashboard URLs and event summary

Usage:
    python run_with_memguard.py --scenario 02
    python run_with_memguard.py --scenario 02 --no-qwen  # heuristic only
"""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

# Ensure we can import fincompli modules
sys.path.insert(0, str(Path(__file__).parent))


def check_sdk():
    """Verify MemGuard SDK is importable."""
    try:
        import memguard  # noqa: F401
        print("✅ MemGuard SDK imported")
        return True
    except ImportError:
        print("❌ MemGuard SDK not installed")
        print("   Run: pip install -e ../sdk")
        return False


def check_backend():
    """Verify MemGuard backend is reachable."""
    import requests
    try:
        resp = requests.get("http://localhost:8000/health", timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ MemGuard backend reachable (model: {data.get('llm_model', '?')})")
            return True
    except Exception:
        pass
    print("⚠️  MemGuard backend not reachable at http://localhost:8000")
    print("   Start: cd ../backend && uvicorn app.main:app --host 0.0.0.0 --port 8000")
    return False


def check_qwen():
    """Verify Qwen/llama-server is reachable."""
    import requests
    try:
        resp = requests.get("http://localhost:8080/v1/models", timeout=3)
        if resp.status_code == 200:
            print("✅ Qwen (llama-server) reachable on port 8080")
            return True
    except Exception:
        pass
    print("⚠️  Qwen not reachable — agents will use heuristic fallback")
    return False


def main():
    parser = argparse.ArgumentParser(
        description="FinCompli + MemGuard — Stage 2 Runner"
    )
    parser.add_argument(
        "--scenario", type=str, default="02",
        help="Scenario ID to run (default: 02)"
    )
    parser.add_argument(
        "--no-qwen", action="store_true",
        help="Skip Qwen, use heuristics only"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  FinCompli + MemGuard SDK")
    print("  Stage 2: Full Memory Observability")
    print("=" * 60)
    print()

    # ── Pre-flight checks ──
    sdk_ok = check_sdk()
    if not sdk_ok:
        sys.exit(1)

    backend_ok = check_backend()
    qwen_ok = check_qwen() if not args.no_qwen else False

    print()
    print("─" * 60)
    print("  Running compliance workflow...")
    print("─" * 60)
    print()

    # ── Delegate to CLI runner ──
    from cli.interactive import run_scenario

    run_scenario(
        scenario_id=args.scenario,
        use_memory=True,
        use_llm=not args.no_qwen,
        use_memguard=True,
    )

    # ── Post-run observability summary ──
    print()
    print("=" * 60)
    print("  📊 Observability Summary")
    print("=" * 60)
    print()

    if backend_ok:
        import requests
        try:
            stats = requests.get(
                "http://localhost:8000/v1/db/stats", timeout=3
            ).json()
            print(f"  Total Events:     {stats.get('total_events', '?'):>6}")
            print(f"  Decision Traces:  {stats.get('total_decision_traces', '?'):>6}")
        except Exception:
            pass

    print()
    print("  🔍 Dashboard:  http://localhost:3001")
    print("  📡 API Docs:   http://localhost:8000/docs")
    print()
    print("  On the dashboard, filter by agent to see:")
    print("    • fraud_detection    — episodic memory reads + Qwen analysis")
    print("    • case_history       — similar SAR case retrievals")
    print("    • compliance_research — regulation queries + synthesis")
    print("    • report_generation  — SAR generation from all prior analyses")
    print()
    print("  Click any DecisionTrace to see:")
    print("    🧠 Memory IN  →  🤖 Agent Decision  →  💾 Memory OUT")
    print()


if __name__ == "__main__":
    main()
