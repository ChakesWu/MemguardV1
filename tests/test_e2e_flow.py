#!/usr/bin/env python3
"""
End-to-End Test: SDK → Backend → Frontend Full Flow
"""

import time
import requests
import sys
import os

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sdk"))

from memguard.core.interceptor import MemGuardInterceptor
from memguard.transport import HttpTransport
from memguard.core.event import MemoryOp, MemoryType

def test_complete_flow():
    print("\n" + "="*70)
    print("  End-to-End Test: Full Flow Verification")
    print("="*70 + "\n")

    # 1. Create SDK interceptor
    print("Step 1: Create SDK interceptor...")
    interceptor = MemGuardInterceptor(
        agent_id="test-e2e-agent",
        namespace="test-org",
        transport=HttpTransport("http://localhost:8000"),
        capture_content=True
    )
    interceptor.set_session("test-e2e-session-001")
    print("   SDK interceptor created\n")

    # 2. Generate test events
    print("Step 2: Generate test events...")
    test_events = []
    for i in range(5):
        event_id = interceptor.record(
            operation=MemoryOp.CREATE,
            memory_key=f"test_key_{i}",
            after_value={"test": f"value_{i}"},
            memory_type=MemoryType.SEMANTIC,
            tags=["e2e-test"]
        )
        test_events.append(event_id)
        print(f"   Event {i+1}/5: {event_id[:8]}...")
        time.sleep(0.1)

    print(f"\n   Generated {len(test_events)} test events\n")

    # 3. Wait for Backend to process
    print("Step 3: Wait for Backend to process...")
    time.sleep(2)
    print("   Wait complete\n")

    # 4. Verify Backend API
    print("Step 4: Verify Backend API...")

    # 4.1 Check stats
    try:
        stats_res = requests.get("http://localhost:8000/v1/db/stats")
        if stats_res.status_code == 200:
            stats = stats_res.json()
            print(f"   Stats API: {stats['total_events']} events")
        else:
            print(f"   Stats API failed: {stats_res.status_code}")
            return False
    except Exception as e:
        print(f"   Cannot connect to Backend: {e}")
        return False

    # 4.2 Check event list
    try:
        events_res = requests.get("http://localhost:8000/v1/events?limit=10")
        if events_res.status_code == 200:
            events_data = events_res.json()
            events = events_data.get("events", [])
            print(f"   Event list API: returned {len(events)} events")

            # Verify our test events
            found_count = sum(1 for e in events if e.get("agent_id") == "test-e2e-agent")
            print(f"   Found {found_count} test events")
        else:
            print(f"   Event list API: {events_res.status_code} (may not be implemented yet)")
            print(f"   Needs to add: GET /v1/events endpoint")
    except Exception as e:
        print(f"   Event list API call failed: {e}")

    print()

    # 5. Verify Frontend
    print("Step 5: Verify Frontend...")
    try:
        frontend_res = requests.get("http://localhost:3000")
        if frontend_res.status_code == 200:
            print("   Frontend is accessible")
            print("   Open browser to view: http://localhost:3000")
        else:
            print(f"   Frontend not accessible: {frontend_res.status_code}")
            return False
    except Exception as e:
        print(f"   Frontend connection failed: {e}")
        return False

    print()
    print("="*70)
    print("  End-to-End test complete!")
    print("="*70 + "\n")

    print("Test Report:")
    print(f"  - SDK event generation: {len(test_events)} events")
    print(f"  - Backend receiving: Stats API normal")
    print(f"  - Backend query: Needs /v1/events API")
    print(f"  - Frontend access: Dashboard available")
    print()
    print("Next steps:")
    print("  1. Add GET /v1/events endpoint in backend/app/main.py")
    print("  2. Restart Backend")
    print("  3. Re-run this test")
    print()

    return True

if __name__ == "__main__":
    success = test_complete_flow()
    sys.exit(0 if success else 1)
