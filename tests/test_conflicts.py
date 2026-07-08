#!/usr/bin/env python3
"""Simulate memory conflicts — two agents writing to same key concurrently."""

import sys, os, time, threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sdk"))

from memguard.core.interceptor import MemGuardInterceptor, Transport
from memguard.core.event import MemoryOp, MemoryType

# Sync Transport — sends HTTP inline (no async/daemon issues)
class SyncHttpTransport(Transport):
    def __init__(self, base_url="http://localhost:8000"):
        import urllib.request, json as _json
        self.base_url = base_url.rstrip("/")
        self._request = urllib.request
        self._json = _json

    async def emit(self, event) -> None:
        from dataclasses import asdict
        payload = asdict(event)
        body = self._json.dumps({"events": [payload]}).encode("utf-8")
        req = self._request.Request(
            f"{self.base_url}/v1/events",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            self._request.urlopen(req, timeout=2.0)
        except Exception:
            pass


def agent_worker(agent_id, namespace, memory_key, iterations):
    """Simulate one agent writing repeatedly to the same key."""
    interceptor = MemGuardInterceptor(
        agent_id=agent_id,
        namespace=namespace,
        transport=SyncHttpTransport("http://localhost:8000"),
        capture_content=True,
    )
    interceptor.set_session(f"conflict-test-{agent_id}")

    for i in range(iterations):
        # Simulate: read state, then update it
        interceptor.record(
            operation=MemoryOp.READ,
            memory_key=memory_key,
            after_value={"shared_counter": i, "agent": agent_id},
            memory_type=MemoryType.WORKING,
        )

        interceptor.record(
            operation=MemoryOp.UPDATE,
            memory_key=memory_key,
            before_value={"shared_counter": i, "agent": agent_id},
            after_value={"shared_counter": i + 1, "agent": agent_id},
            memory_type=MemoryType.WORKING,
        )

        # 极小延迟让两个 agent 有时间重叠
        time.sleep(0.05)


def main():
    print("\n" + "=" * 70)
    print("  Conflict Detection Test — Concurrent Agent Writes")
    print("=" * 70 + "\n")

    SHARED_KEY = "global:shared_counter"
    ITERATIONS = 8

    print(f"📝 Shared memory key: {SHARED_KEY}")
    print(f"📝 Each agent writes {ITERATIONS} times (UPDATE)")
    print(f"📝 3 agents running simultaneously\n")

    # 启动线程
    threads = []
    for agent_name in ["fraud-detection", "case-history", "compliance-research"]:
        t = threading.Thread(
            target=agent_worker,
            args=(agent_name, "conflict-test", SHARED_KEY, ITERATIONS),
            daemon=False,
        )
        threads.append(t)

    print("🚀 Starting concurrent writes...")
    start = time.time()

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    elapsed = time.time() - start
    print(f"\n✅ All agents finished in {elapsed:.1f}s")
    print(f"   Expected events: {3 * ITERATIONS * 2} (3 agents × {ITERATIONS} × read+update)")

    # 等待 Backend 写入完成
    time.sleep(1)

    # 检查统计
    import requests
    stats = requests.get("http://localhost:8000/v1/db/stats").json()
    print(f"\n📊 Database: {stats['total_events']} events")

    # 检测冲突
    conflicts = requests.get(
        "http://localhost:8000/v1/analysis/conflicts?window_seconds=60"
    ).json()
    print(f"🔴 Conflicts detected: {conflicts['total']}")

    if conflicts["conflicts"]:
        print("\n" + "=" * 70)
        print("  Conflicts Found:")
        print("=" * 70)
        for c in conflicts["conflicts"]:
            sev_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡"}.get(c["severity"], "⚪")
            print(f"\n  {sev_emoji} [{c['severity'].upper()}] {c['memory_key']}")
            print(f"     Agent A: {c['agent_a']} @ {c['time_a'][:19]}")
            print(f"     Agent B: {c['agent_b']} @ {c['time_b'][:19]}")
            print(f"     Delta: {c['delta_seconds']}s | Same content: {c['same_content']}")
    else:
        print("\n   ℹ️  No conflicts in this run (try smaller window_seconds)")

    print("\n" + "=" * 70)
    print(f"  Dashboard: http://localhost:3000")
    print(f"  Conflicts API: curl 'http://localhost:8000/v1/analysis/conflicts?window_seconds=10'")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
