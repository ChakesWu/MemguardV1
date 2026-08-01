from datetime import datetime, timezone
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "backend"))

from app.explanation import explain_trace


TRACE_TIME = "2026-08-01T12:00:00+00:00"


def trace(current_value="New York"):
    return {
        "timestamp": TRACE_TIME,
        "metadata": {"current_facts": {"current_location": current_value}},
    }


def evidence(
    remembered_value="New York",
    *,
    verified_at="2026-08-01T11:00:00+00:00",
    max_age_seconds=86400,
    included=True,
    captured=True,
):
    metadata = {
        "evidence_role": "retrieved_memory",
        "source_type": "conversation",
        "source_id": "trip-message-2026-07-01",
        "memory_created_at": "2026-07-01T09:00:00+00:00",
        "memory_last_verified_at": verified_at,
        "retrieval_rank": 1,
        "retrieval_score": 0.93,
        "included_in_prompt": included,
        "fact_key": "current_location",
        "max_age_seconds": max_age_seconds,
    }
    if captured:
        metadata["_after_value"] = {"current_location": remembered_value}
    return {
        "event_id": "retrieval-location",
        "memory_key": "profile:current_location",
        "side": "input",
        "content_hash": "stable-hash",
        "metadata": metadata,
    }


@pytest.mark.parametrize(
    ("item", "expected_status"),
    [
        (evidence(), "observed"),
        (evidence("Taipei"), "conflict"),
        (
            evidence(verified_at="2026-07-01T09:00:00+00:00"),
            "stale",
        ),
        (
            evidence("Taipei", verified_at="2026-07-01T09:00:00+00:00"),
            "stale_conflict",
        ),
    ],
)
def test_explanation_classifies_recorded_memory(item, expected_status):
    result = explain_trace(trace(), [item], [])

    assert result["status"] == expected_status
    assert result["basis"] == "recorded_evidence"
    assert result["causality_claim"] == "not_proven"
    assert result["findings"][0]["kind"] == expected_status


def test_hash_only_evidence_does_not_claim_remembered_or_current_values():
    result = explain_trace(trace(), [evidence("Taipei", captured=False)], [])

    assert result["status"] == "observed"
    assert "remembered_value" not in result["findings"][0]
    assert "current_value" not in result["findings"][0]
    assert "conflict" not in result["summary"].lower()


def test_missing_linked_event_has_priority_without_fabricated_finding():
    result = explain_trace(trace(), [evidence("Taipei")], ["missing-retrieval-event"])

    assert result["status"] == "evidence_gap"
    assert result["missing_evidence_event_ids"] == ["missing-retrieval-event"]
    assert all(
        finding["event_id"] != "missing-retrieval-event"
        for finding in result["findings"]
    )


def test_excluded_memory_uses_exclusion_wording():
    result = explain_trace(trace(), [evidence("Taipei", included=False)], [])

    assert result["findings"][0]["included_in_prompt"] is False
    assert "excluded" in result["summary"].lower()
    assert "shaped the output" not in result["summary"].lower()


def test_malformed_timestamps_keep_observed_evidence_without_stale_claim():
    result = explain_trace(trace(), [evidence(verified_at="not-a-time")], [])

    assert result["status"] == "observed"
    assert "age_seconds" not in result["findings"][0]


def test_future_verification_time_has_zero_age_and_is_not_stale():
    future = datetime(2026, 8, 2, tzinfo=timezone.utc).isoformat()
    result = explain_trace(trace(), [evidence(verified_at=future)], [])

    assert result["status"] == "observed"
    assert result["findings"][0]["age_seconds"] == 0


def test_non_retrieval_and_output_events_are_not_explanation_findings():
    wrong_role = evidence()
    wrong_role["metadata"]["evidence_role"] = "tool_result"
    output_item = evidence()
    output_item["event_id"] = "output-event"
    output_item["side"] = "output"

    result = explain_trace(trace(), [wrong_role, output_item], [])

    assert result["status"] == "observed"
    assert result["findings"] == []
