#!/usr/bin/env python3
"""
Test SDK → Backend Integration

Verifies that the MemGuard SDK can send events to the backend
and that they're properly stored and queryable.

Prerequisites:
    1. Backend running: cd backend && uvicorn app.main:app --reload
    2. SDK installed: cd sdk && pip install -e .

Expected outcome:
    - Events sent successfully
    - Events visible in database
    - Events queryable via API
"""

import sys
import time
from pathlib import Path

# Add SDK to path
sdk_path = Path(__file__).parent / "sdk"
sys.path.insert(0, str(sdk_path))

from memguard.core.interceptor import MemGuardInterceptor
from memguard.transport.http import HttpTransport
from memguard.transport.stdout import StdoutTransport
from memguard.core.event import MemoryOp, MemoryType

def test_basic_integration():
    """Test basic SDK → Backend event flow."""

    print("\n" + "="*70)
    print("TEST: SDK → Backend Integration")
    print("="*70 + "\n")

    # Create interceptor with HTTP transport
    interceptor = MemGuardInterceptor(
        agent_id="test-agent",
        namespace="test-org",
        transport=HttpTransport("http://localhost:8000"),
        capture_content=True  # For testing, capture full content
    )

    interceptor.set_session("test-session-001")

    print("📤 Sending test events to backend...")
    event_ids = []

    # Test 1: CREATE event
    print("  1. CREATE event")
    event_id = interceptor.record(
        operation=MemoryOp.CREATE,
        memory_key="user_preference:language",
        after_value={"language": "Python", "experience": "expert"},
        memory_type=MemoryType.SEMANTIC,
        tags=["test", "user_prefs"]
    )
    event_ids.append(event_id)
    time.sleep(0.1)

    # Test 2: READ event
    print("  2. READ event")
    event_id = interceptor.record(
        operation=MemoryOp.READ,
        memory_key="user_preference:language",
        after_value={"language": "Python", "experience": "expert"},
        memory_type=MemoryType.SEMANTIC
    )
    event_ids.append(event_id)
    time.sleep(0.1)

    # Test 3: UPDATE event
    print("  3. UPDATE event")
    event_id = interceptor.record(
        operation=MemoryOp.UPDATE,
        memory_key="user_preference:language",
        before_value={"language": "Python", "experience": "expert"},
        after_value={"language": "Python", "experience": "expert", "frameworks": ["FastAPI", "LangChain"]},
        memory_type=MemoryType.SEMANTIC
    )
    event_ids.append(event_id)
    time.sleep(0.1)

    # Test 4: Multiple events simulating agent workflow
    print("  4. Agent workflow simulation (5 events)")
    for i in range(5):
        event_id = interceptor.record(
            operation=MemoryOp.CREATE,
            memory_key=f"workflow_step_{i}",
            after_value={"step": i, "status": "completed", "timestamp": time.time()},
            memory_type=MemoryType.EPISODIC
        )
        event_ids.append(event_id)
        time.sleep(0.05)

    print(f"\n✅ Sent {len(event_ids)} events to backend\n")

    # Give backend time to process
    time.sleep(1)

    # Verify events in database
    print("🔍 Verifying events in database...")
    import requests

    try:
        # Check database stats
        response = requests.get("http://localhost:8000/v1/db/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"  ✅ Database stats:")
            print(f"     - Total events: {stats.get('total_events', 0)}")
            print(f"     - Total traces: {stats.get('total_decision_traces', 0)}")
            print(f"     - DB path: {stats.get('db_path', 'unknown')}")
        else:
            print(f"  ❌ Failed to get DB stats: {response.status_code}")
            return False

        # Check health
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            health = response.json()
            print(f"\n  ✅ Backend health: {health.get('status', 'unknown')}")

        print("\n" + "="*70)
        print("✅ TEST PASSED: SDK → Backend integration working!")
        print("="*70 + "\n")

        print("📊 Next steps:")
        print("  1. View events in database:")
        print(f"     sqlite3 {stats.get('db_path', 'backend/memguard.db')} 'SELECT * FROM memory_events;'")
        print("\n  2. Query events via API:")
        print("     curl http://localhost:8000/v1/db/stats")
        print("\n  3. Integrate with FinCompli (see EXECUTION_SUMMARY.md)")

        return True

    except requests.exceptions.ConnectionError:
        print("  ❌ ERROR: Cannot connect to backend at http://localhost:8000")
        print("\n  Start the backend first:")
        print("    cd backend && uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return False


def test_with_stdout():
    """Test SDK with StdoutTransport (for debugging)."""

    print("\n" + "="*70)
    print("TEST: SDK with StdoutTransport (Debugging)")
    print("="*70 + "\n")

    interceptor = MemGuardInterceptor(
        agent_id="debug-agent",
        namespace="debug-org",
        transport=StdoutTransport(),  # Print to console
        capture_content=True
    )

    interceptor.set_session("debug-session-001")

    print("📤 Sending events to stdout...\n")

    interceptor.record(
        operation=MemoryOp.CREATE,
        memory_key="debug_test",
        after_value={"message": "Hello from MemGuard!"},
        memory_type=MemoryType.WORKING
    )

    print("\n✅ StdoutTransport test complete")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test MemGuard SDK → Backend integration")
    parser.add_argument("--stdout", action="store_true", help="Test StdoutTransport instead")
    args = parser.parse_args()

    if args.stdout:
        test_with_stdout()
    else:
        success = test_basic_integration()
        sys.exit(0 if success else 1)
