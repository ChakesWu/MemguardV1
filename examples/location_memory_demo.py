"""Run the installed MemGuard location-memory demo."""

import os

from memguard import MemGuard
from memguard.demo import run_location_demo


if __name__ == "__main__":
    guard = MemGuard(
        api_url=os.getenv("MEMGUARD_API_URL", "http://localhost:8000"),
        api_key=os.environ["MEMGUARD_API_TOKEN"],
        agent_id="location-agent",
        namespace=os.getenv("MEMGUARD_TENANT_ID", "acme-dev"),
        capture_content=True,
    )
    print(run_location_demo(guard))
