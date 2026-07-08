"""
Natural Language Audit Report Generator

Converts technical memory events into human-readable audit reports
for compliance, debugging, and business stakeholders.
"""

from datetime import datetime
from typing import Any
import os


class AuditReportGenerator:
    """Generate natural language audit reports from memory events."""

    def __init__(self, llm_client=None):
        """
        Initialize with optional LLM client.

        If no LLM provided, uses template-based generation.
        With LLM: richer, context-aware narratives.
        """
        self.llm_client = llm_client

    def generate_session_report(
        self,
        session_id: str,
        events: list[dict],
        traces: list[dict] = None,
        conflicts: list[dict] = None,
        style: str = "compliance",
    ) -> dict[str, Any]:
        """
        Generate a session audit report.

        Args:
            session_id: Session identifier
            events: List of MemoryEvent dicts
            traces: List of DecisionTrace dicts (optional)
            conflicts: List of conflict dicts (optional)
            style: Report style - "compliance", "debug", "business"

        Returns:
            {
                "report_id": str,
                "session_id": str,
                "generated_at": str,
                "style": str,
                "summary": str,  # Natural language summary
                "timeline": list[str],  # Narrative timeline
                "findings": list[dict],  # Key findings
                "recommendations": list[str],
                "metadata": dict,
            }
        """
        if not events:
            return self._empty_report(session_id, style)

        # 基础统计
        metadata = self._compute_metadata(events, traces, conflicts)

        # 生成叙述
        if self.llm_client:
            summary = self._llm_summary(session_id, events, traces, metadata, style)
            timeline = self._llm_timeline(events, traces, style)
        else:
            summary = self._template_summary(session_id, metadata, style)
            timeline = self._template_timeline(events, style)

        findings = self._extract_findings(events, traces, conflicts)
        recommendations = self._generate_recommendations(findings, metadata)

        return {
            "report_id": f"audit-{session_id}-{int(datetime.now().timestamp())}",
            "session_id": session_id,
            "generated_at": datetime.now().isoformat(),
            "style": style,
            "summary": summary,
            "timeline": timeline,
            "findings": findings,
            "recommendations": recommendations,
            "metadata": metadata,
        }

    def _compute_metadata(
        self, events: list[dict], traces: list[dict] = None, conflicts: list[dict] = None
    ) -> dict:
        """Extract metadata from events."""
        if not events:
            return {}

        agents = {e.get("agent_id") for e in events}
        ops = {}
        for e in events:
            op = e.get("operation", "unknown")
            ops[op] = ops.get(op, 0) + 1

        start_time = min((e.get("timestamp") for e in events), default=None)
        end_time = max((e.get("timestamp") for e in events), default=None)

        # Duration
        duration_seconds = 0
        if start_time and end_time:
            try:
                t1 = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                t2 = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                duration_seconds = (t2 - t1).total_seconds()
            except Exception:
                pass

        return {
            "total_events": len(events),
            "agents": list(agents),
            "operations": ops,
            "start_time": start_time,
            "end_time": end_time,
            "duration_seconds": round(duration_seconds, 2),
            "decision_traces": len(traces) if traces else 0,
            "conflicts": len(conflicts) if conflicts else 0,
        }

    def _template_summary(self, session_id: str, metadata: dict, style: str) -> str:
        """Generate template-based summary."""
        agents = ", ".join(metadata.get("agents", []))
        total = metadata.get("total_events", 0)
        duration = metadata.get("duration_seconds", 0)
        ops = metadata.get("operations", {})

        if style == "compliance":
            return (
                f"Session {session_id} audit report. "
                f"Total {total} memory operations recorded over {duration:.1f} seconds. "
                f"Agents involved: {agents}. "
                f"Operations breakdown: {ops.get('create', 0)} CREATE, "
                f"{ops.get('read', 0)} READ, {ops.get('update', 0)} UPDATE, "
                f"{ops.get('delete', 0)} DELETE. "
                f"{metadata.get('conflicts', 0)} conflicts detected."
            )
        elif style == "debug":
            return (
                f"Debug trace for session {session_id}. "
                f"{total} events captured from agents: {agents}. "
                f"Duration: {duration:.1f}s. "
                f"Writes: {ops.get('create', 0) + ops.get('update', 0)}, "
                f"Reads: {ops.get('read', 0)}."
            )
        else:  # business
            conflicts_msg = "No conflicts detected." if metadata.get('conflicts', 0) == 0 else f"{metadata.get('conflicts')} conflicts require attention."
            return (
                f"Session {session_id} involved {len(metadata.get('agents', []))} agent(s) "
                f"performing {total} operations over {duration:.1f} seconds. "
                f"{conflicts_msg}"
            )

    def _template_timeline(self, events: list[dict], style: str) -> list[str]:
        """Generate template-based timeline."""
        timeline = []
        for i, e in enumerate(events[:20], 1):  # Limit to first 20
            op = e.get("operation", "unknown").upper()
            agent = e.get("agent_id", "unknown")
            key = e.get("memory_key", "")[:40]
            ts = e.get("timestamp", "")[:19]

            if style == "compliance":
                timeline.append(f"{i}. [{ts}] Agent '{agent}' performed {op} on key '{key}'")
            elif style == "debug":
                timeline.append(f"{i}. {op} {key} by {agent} @ {ts}")
            else:  # business
                verb = {"create": "created", "read": "accessed", "update": "modified", "delete": "removed"}.get(
                    e.get("operation", ""), "operated on"
                )
                timeline.append(f"{i}. {agent} {verb} data at {ts}")

        if len(events) > 20:
            timeline.append(f"... ({len(events) - 20} more events)")

        return timeline

    def _extract_findings(
        self, events: list[dict], traces: list[dict] = None, conflicts: list[dict] = None
    ) -> list[dict]:
        """Extract key findings."""
        findings = []

        # Conflict findings
        if conflicts:
            for c in conflicts:
                findings.append({
                    "type": "conflict",
                    "severity": c.get("severity", "medium"),
                    "description": f"Concurrent write to {c.get('memory_key')} by {c.get('agent_a')} and {c.get('agent_b')} within {c.get('delta_seconds')}s",
                    "recommendation": "Consider implementing distributed locks or optimistic concurrency control",
                })

        # High write ratio
        ops = {}
        for e in events:
            op = e.get("operation")
            ops[op] = ops.get(op, 0) + 1
        writes = ops.get("create", 0) + ops.get("update", 0)
        reads = ops.get("read", 0)
        if reads > 0 and writes / reads > 2.0:
            findings.append({
                "type": "performance",
                "severity": "medium",
                "description": f"High write-to-read ratio ({writes}:{reads}). May indicate inefficient caching.",
                "recommendation": "Review caching strategy to reduce redundant writes",
            })

        return findings

    def _generate_recommendations(self, findings: list[dict], metadata: dict) -> list[str]:
        """Generate actionable recommendations."""
        recs = []

        if metadata.get("conflicts", 0) > 0:
            recs.append("Implement conflict resolution strategy (e.g., last-write-wins, vector clocks)")

        if metadata.get("total_events", 0) > 1000:
            recs.append("Consider event batching or sampling to reduce observability overhead")

        if len(metadata.get("agents", [])) > 5:
            recs.append("High agent count — consider namespace isolation or per-agent databases")

        if not recs:
            recs.append("System operating normally — no immediate action required")

        return recs

    def _empty_report(self, session_id: str, style: str) -> dict:
        """Generate empty report."""
        return {
            "report_id": f"audit-{session_id}-empty",
            "session_id": session_id,
            "generated_at": datetime.now().isoformat(),
            "style": style,
            "summary": "No events found for this session.",
            "timeline": [],
            "findings": [],
            "recommendations": [],
            "metadata": {},
        }

    def _llm_summary(
        self, session_id: str, events: list[dict], traces: list[dict], metadata: dict, style: str
    ) -> str:
        """Generate LLM-powered summary (placeholder for now)."""
        # TODO: Implement LLM call when client is available
        return self._template_summary(session_id, metadata, style)

    def _llm_timeline(self, events: list[dict], traces: list[dict], style: str) -> list[str]:
        """Generate LLM-powered timeline (placeholder for now)."""
        # TODO: Implement LLM call when client is available
        return self._template_timeline(events, style)


# ── Export Formats ───────────────────────────────────────────────────


def export_to_markdown(report: dict) -> str:
    """Export report to Markdown format."""
    lines = [
        f"# Audit Report: {report['session_id']}",
        f"",
        f"**Report ID**: {report['report_id']}  ",
        f"**Generated**: {report['generated_at']}  ",
        f"**Style**: {report['style']}",
        f"",
        f"## Summary",
        f"",
        report["summary"],
        f"",
        f"## Timeline",
        f"",
    ]

    for item in report["timeline"]:
        lines.append(f"- {item}")

    if report.get("findings"):
        lines.append(f"")
        lines.append(f"## Findings")
        lines.append(f"")
        for finding in report["findings"]:
            sev = finding.get("severity", "").upper()
            lines.append(f"### [{sev}] {finding.get('type', 'Unknown')}")
            lines.append(f"")
            lines.append(finding.get("description", ""))
            lines.append(f"")
            if finding.get("recommendation"):
                lines.append(f"**Recommendation**: {finding['recommendation']}")
                lines.append(f"")

    if report.get("recommendations"):
        lines.append(f"## Recommendations")
        lines.append(f"")
        for rec in report["recommendations"]:
            lines.append(f"- {rec}")

    lines.append(f"")
    lines.append(f"## Metadata")
    lines.append(f"")
    lines.append(f"```json")
    import json
    lines.append(json.dumps(report.get("metadata", {}), indent=2))
    lines.append(f"```")

    return "\n".join(lines)
