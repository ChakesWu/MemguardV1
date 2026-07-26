"""
Test automatic influence score calculation for DecisionTraces.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services import MemoryGateway, MemoryEvent, DecisionTrace


def test_automatic_influence_calculation():
    """Test that influence scores are auto-calculated when not provided."""
    gateway = MemoryGateway()

    # Create a decision timestamp
    decision_time = datetime.now(timezone.utc)

    # Create 3 memory events with different types and ages
    # Event 1: Recent semantic memory (should score high)
    event1 = MemoryEvent(
        event_id="evt_001",
        tenant_id="test",
        agent_id="test-agent",
        memory_id="mem_001",
        trace_id="trace_001",
        event_type="read",
        source_type="semantic",  # type_weight = 1.0
        content="Important regulation",
        content_hash="hash1",
        policy_decision="allow",
        trust_score=90.0,
        created_at=(decision_time - timedelta(seconds=30)).isoformat(),  # 30s ago, recency_weight = 1.0
    )

    # Event 2: Episodic memory from 10 minutes ago (medium score)
    event2 = MemoryEvent(
        event_id="evt_002",
        tenant_id="test",
        agent_id="test-agent",
        memory_id="mem_002",
        trace_id="trace_001",
        event_type="read",
        source_type="episodic",  # type_weight = 0.8
        content="Past SAR report",
        content_hash="hash2",
        policy_decision="allow",
        trust_score=85.0,
        created_at=(decision_time - timedelta(minutes=10)).isoformat(),  # 10min ago (600s), recency_weight = 0.7 (< 1 hour)
    )

    # Event 3: Old procedural memory from 2 hours ago (lower score)
    event3 = MemoryEvent(
        event_id="evt_003",
        tenant_id="test",
        agent_id="test-agent",
        memory_id="mem_003",
        trace_id="trace_001",
        event_type="read",
        source_type="procedural",  # type_weight = 0.6
        content="Standard operating procedure",
        content_hash="hash3",
        policy_decision="allow",
        trust_score=80.0,
        created_at=(decision_time - timedelta(hours=2)).isoformat(),  # 2hrs ago (7200s), recency_weight = 0.5 (< 24 hours)
    )

    # Add events to gateway
    with gateway._lock:
        gateway.events.extend([event1, event2, event3])

    # Persist to DB so the calculation can find them
    gateway._persist_event(event1)
    gateway._persist_event(event2)
    gateway._persist_event(event3)

    # Create a DecisionTrace WITHOUT providing influence scores
    trace = DecisionTrace(
        trace_id="trace_001",
        tenant_id="test",
        agent_id="test-agent",
        session_id="session_001",
        timestamp=decision_time.isoformat(),
        input_memory_ids=["evt_001", "evt_002", "evt_003"],
        input_memory_events=["evt_001", "evt_002", "evt_003"],
        user_input="Test query",
        llm_prompt_hash="prompt_hash",
        llm_output="Test output",
        llm_output_hash="output_hash",
        llm_model="test-model",
        output_memory_ids=[],
        output_memory_events=[],
        memory_influence_scores={},  # Empty - should be auto-calculated
        total_influence_score=0.0,   # Zero - should be auto-calculated
        metadata={},
    )

    # Call create_decision_trace - should auto-calculate scores
    gateway.create_decision_trace(trace)

    # Verify scores were calculated
    assert trace.memory_influence_scores, "Influence scores should be calculated"
    assert trace.total_influence_score > 0.0, "Total influence score should be > 0"

    # Verify individual scores
    # Event 1: semantic (1.0) × recent <60s (1.0) = 1.0
    assert trace.memory_influence_scores["evt_001"] == 1.0, f"Event 1 score should be 1.0, got {trace.memory_influence_scores.get('evt_001')}"

    # Event 2: episodic (0.8) × 10min ago (0.7, falls in <1hr bracket) = 0.56
    expected_score_2 = 0.8 * 0.7
    actual_score_2 = trace.memory_influence_scores["evt_002"]
    assert abs(actual_score_2 - expected_score_2) < 0.01, f"Event 2 score should be ~{expected_score_2}, got {actual_score_2}"

    # Event 3: procedural (0.6) × 2hr ago (0.5, falls in <24hr bracket) = 0.30
    expected_score_3 = 0.6 * 0.5
    actual_score_3 = trace.memory_influence_scores["evt_003"]
    assert abs(actual_score_3 - expected_score_3) < 0.01, f"Event 3 score should be ~{expected_score_3}, got {actual_score_3}"

    # Verify overall score = average of individual scores
    expected_overall = (1.0 + 0.56 + 0.30) / 3
    assert abs(trace.total_influence_score - expected_overall) < 0.01, \
        f"Overall score should be ~{expected_overall}, got {trace.total_influence_score}"

    print("✅ All assertions passed!")
    print(f"   Event 1 (semantic, 30s ago): {trace.memory_influence_scores['evt_001']:.2f}")
    print(f"   Event 2 (episodic, 10m ago): {trace.memory_influence_scores['evt_002']:.2f}")
    print(f"   Event 3 (procedural, 2h ago): {trace.memory_influence_scores['evt_003']:.2f}")
    print(f"   Overall influence: {trace.total_influence_score:.2f}")


def test_manual_override():
    """Test that manually-provided scores override auto-calculation."""
    gateway = MemoryGateway()

    decision_time = datetime.now(timezone.utc)

    # Create one event
    event = MemoryEvent(
        event_id="evt_manual",
        tenant_id="test",
        agent_id="test-agent",
        memory_id="mem_manual",
        trace_id="trace_manual",
        event_type="read",
        source_type="semantic",
        content="Test content",
        content_hash="hash_manual",
        policy_decision="allow",
        trust_score=90.0,
        created_at=(decision_time - timedelta(seconds=30)).isoformat(),
    )

    with gateway._lock:
        gateway.events.append(event)
    gateway._persist_event(event)

    # Create trace WITH manual scores
    manual_scores = {"evt_manual": 0.95}
    manual_total = 0.95

    trace = DecisionTrace(
        trace_id="trace_manual",
        tenant_id="test",
        agent_id="test-agent",
        session_id="session_manual",
        timestamp=decision_time.isoformat(),
        input_memory_ids=["evt_manual"],
        input_memory_events=["evt_manual"],
        user_input="Test query",
        llm_prompt_hash="prompt_hash",
        llm_output="Test output",
        llm_output_hash="output_hash",
        llm_model="test-model",
        output_memory_ids=[],
        output_memory_events=[],
        memory_influence_scores=manual_scores,  # Manually provided
        total_influence_score=manual_total,     # Manually provided
        metadata={},
    )

    # Call create_decision_trace
    gateway.create_decision_trace(trace)

    # Verify manual scores were NOT overridden
    assert trace.memory_influence_scores == manual_scores, "Manual scores should be preserved"
    assert trace.total_influence_score == manual_total, "Manual total should be preserved"

    print("✅ Manual override test passed!")
    print(f"   Manual score preserved: {trace.memory_influence_scores['evt_manual']:.2f}")


if __name__ == "__main__":
    print("Testing automatic influence score calculation...\n")
    test_automatic_influence_calculation()
    print("\nTesting manual override...\n")
    test_manual_override()
    print("\n🎉 All tests passed!")
