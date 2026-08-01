#!/usr/bin/env python3
"""
Integration test: Verify automatic influence score calculation via API.
"""

import requests
import pytest
import time
from datetime import datetime, timezone, timedelta

API_BASE = "http://localhost:8000"

pytestmark = pytest.mark.live

def test_api_influence_calculation():
    """Test that POST /v1/trace auto-calculates influence scores."""

    print("🧪 Integration Test: Automatic Influence Score Calculation\n")

    # Step 1: Create some memory events via SDK ingestion
    print("Step 1: Creating memory events...")

    decision_time = datetime.now(timezone.utc)

    events = [
        {
            "event_id": "evt_api_001",
            "agent_id": "test-api-agent",
            "operation": "read",
            "memory_key": "semantic:regulation_XYZ",
            "memory_type": "semantic",
            "namespace": "test-api",
            "session_id": "session_api_test",
            "timestamp": (decision_time - timedelta(seconds=45)).isoformat(),
            "content_hash": "hash_semantic",
            "context": {"source": "semantic"}
        },
        {
            "event_id": "evt_api_002",
            "agent_id": "test-api-agent",
            "operation": "read",
            "memory_key": "episodic:SAR_123",
            "memory_type": "episodic",
            "namespace": "test-api",
            "session_id": "session_api_test",
            "timestamp": (decision_time - timedelta(minutes=15)).isoformat(),
            "content_hash": "hash_episodic",
            "context": {"source": "episodic"}
        },
        {
            "event_id": "evt_api_003",
            "agent_id": "test-api-agent",
            "operation": "read",
            "memory_key": "working:temp_state",
            "memory_type": "working",
            "namespace": "test-api",
            "session_id": "session_api_test",
            "timestamp": (decision_time - timedelta(hours=3)).isoformat(),
            "content_hash": "hash_working",
            "context": {"source": "working"}
        }
    ]

    response = requests.post(f"{API_BASE}/v1/events", json={"events": events})
    if response.status_code != 200:
        print(f"❌ Failed to create events: {response.text}")
        return False

    print(f"✅ Created {len(events)} memory events\n")

    # Step 2: Create a DecisionTrace WITHOUT influence scores
    print("Step 2: Creating DecisionTrace without influence scores...")

    trace_payload = {
        "trace_id": "trace_api_test",
        "agent_id": "test-api-agent",
        "namespace": "test-api",
        "session_id": "session_api_test",
        "timestamp": decision_time.isoformat(),
        "input_event_ids": ["evt_api_001", "evt_api_002", "evt_api_003"],
        "output_event_ids": [],
        "prompt_hash": "test_prompt_hash",
        "output_hash": "test_output_hash",
        "output_summary": "Test decision output",
        # NO memory_influence_scores or memory_influence_score provided
        "context": {"test": "api_integration"}
    }

    response = requests.post(f"{API_BASE}/v1/trace", json=trace_payload)
    if response.status_code != 200:
        print(f"❌ Failed to create trace: {response.text}")
        return False

    print(f"✅ Created DecisionTrace: {response.json()['trace_id']}\n")

    # Step 3: Retrieve the trace and verify scores were calculated
    print("Step 3: Retrieving trace to verify auto-calculated scores...")
    time.sleep(0.5)  # Brief pause to ensure persistence

    response = requests.get(f"{API_BASE}/v1/trace/trace_api_test")
    if response.status_code != 200:
        print(f"❌ Failed to retrieve trace: {response.text}")
        return False

    trace_data = response.json()

    # Verify scores exist
    if not trace_data.get("memory_influence_scores"):
        print("❌ No influence scores found - auto-calculation failed!")
        return False

    scores = trace_data["memory_influence_scores"]
    total_score = trace_data.get("total_influence_score", 0.0)

    print(f"✅ Influence scores auto-calculated:\n")

    # Print per-memory scores
    for event_id in ["evt_api_001", "evt_api_002", "evt_api_003"]:
        if event_id in scores:
            score = scores[event_id]
            print(f"   • {event_id}: {score:.2f}")
        else:
            print(f"   • {event_id}: NOT FOUND ❌")

    print(f"\n   Overall influence: {total_score:.2f}\n")

    # Validate score ranges
    if not (0.0 <= total_score <= 1.0):
        print(f"❌ Total score {total_score} out of range [0.0, 1.0]")
        return False

    for event_id, score in scores.items():
        if not (0.0 <= score <= 1.0):
            print(f"❌ Score for {event_id} = {score} out of range [0.0, 1.0]")
            return False

    # Validate expected ordering (semantic > episodic > working)
    if scores.get("evt_api_001", 0) < scores.get("evt_api_003", 1):
        print("❌ Semantic memory should score higher than working memory")
        return False

    print("✅ All validation checks passed!")
    print("\n🎉 Integration test successful!\n")
    return True


if __name__ == "__main__":
    try:
        result = test_api_influence_calculation()
        exit(0 if result else 1)
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend at http://localhost:8000")
        print("   Make sure the backend is running: cd backend && uvicorn app.main:app")
        exit(1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
