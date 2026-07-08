from __future__ import annotations

"""
LLM Client for FinCompli Baseline — calls local Qwen via llama-server.

Uses the OpenAI-compatible API at {LLM_BASE_URL}/chat/completions.
Graceful fallback: if Qwen is unreachable, returns a structured fallback
response rather than crashing the pipeline.
"""

import json
import logging
from dataclasses import dataclass
from typing import Any

import requests

from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    content: str
    raw: dict[str, Any]


class LLMClient:
    """Thin wrapper around llama-server's OpenAI-compatible API."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        timeout: float = 120.0,
    ):
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.model = model or settings.llm_model
        self.api_key = api_key or settings.llm_api_key
        self.timeout = timeout

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Send a chat completion request to the LLM endpoint."""
        headers = {"Content-Type": "application/json"}
        if self.api_key and self.api_key != "not-needed-for-local":
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        url = f"{self.base_url}/chat/completions"
        logger.debug("LLM request -> %s (model=%s)", url, self.model)

        response = requests.post(
            url, json=payload, headers=headers, timeout=self.timeout
        )
        response.raise_for_status()
        data = response.json()

        content = data["choices"][0]["message"]["content"]
        return LLMResponse(content=content, raw=data)

    def chat_safe(
        self,
        messages: list[dict[str, str]],
        fallback: dict[str, Any] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Call chat() with graceful fallback. Never raises."""
        try:
            return self.chat(messages, temperature=temperature, max_tokens=max_tokens)
        except Exception as e:
            logger.warning(
                "Qwen unreachable at %s: %s - using fallback", self.base_url, e
            )
            fallback_content = json.dumps(fallback or {"error": str(e)})
            return LLMResponse(content=fallback_content, raw={"fallback": True, "error": str(e)})

    def health_check(self) -> bool:
        """Return True if the LLM endpoint is reachable."""
        try:
            resp = requests.get(f"{self.base_url}/models", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False


def parse_json_response(content: str) -> dict[str, Any]:
    """Parse JSON from an LLM response, handling markdown code blocks."""
    text = content.strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try markdown code block
    if "```json" in text:
        try:
            start = text.index("```json") + 7
            end = text.index("```", start)
            return json.loads(text[start:end].strip())
        except (ValueError, json.JSONDecodeError):
            pass

    # Try to find first JSON object
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        pass

    # Give up
    return {"raw_response": text}
