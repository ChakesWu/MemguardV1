"""Command-line entry point for MemGuard SDK diagnostics and demos."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Sequence
from urllib.request import Request, urlopen

from .client import MemGuard
from .demo import run_location_demo


def _get_json(url: str, token: str | None = None) -> Any:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    request = Request(url, headers=headers)
    with urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _doctor(args: argparse.Namespace) -> int:
    api_url = args.api_url.rstrip("/")
    try:
        health = _get_json(f"{api_url}/health")
        traces = _get_json(
            f"{api_url}/v1/trace/tenant/{args.tenant_id}", args.api_token
        )
    except Exception as exc:
        print(f"MemGuard doctor failed: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "api_reachable": health.get("status") == "ok",
                "authenticated_tenant": args.tenant_id,
                "trace_endpoint_reachable": isinstance(traces, list),
            },
            indent=2,
        )
    )
    return 0 if health.get("status") == "ok" and isinstance(traces, list) else 1


def _demo(args: argparse.Namespace) -> int:
    client = MemGuard(
        api_url=args.api_url,
        api_key=args.api_token,
        agent_id=args.agent_id,
        namespace=args.tenant_id,
        capture_content=True,
    )
    try:
        result = run_location_demo(client, dashboard_url=args.dashboard_url)
    except Exception as exc:
        print(f"MemGuard demo failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="memguard", description="Inspect evidence behind agent outputs"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Verify API and tenant access")
    doctor.add_argument("--api-url", default="http://localhost:8000")
    doctor.add_argument("--api-token", required=True)
    doctor.add_argument("--tenant-id", default="acme-dev")
    doctor.set_defaults(handler=_doctor)

    demo = subparsers.add_parser("demo", help="Record the location-memory demo")
    demo.add_argument("--api-url", default="http://localhost:8000")
    demo.add_argument("--api-token", required=True)
    demo.add_argument("--tenant-id", default="acme-dev")
    demo.add_argument("--agent-id", default="location-agent")
    demo.add_argument("--dashboard-url", default="http://localhost:3001")
    demo.set_defaults(handler=_demo)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
