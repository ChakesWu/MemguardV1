from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .llm import LLMClient
from .schemas import MemoryWriteRequest
from .services import DecisionTrace, MemoryGateway


@dataclass
class AgentRunResult:
    answer: str
    memory_write: dict[str, Any]
    cited_memory_ids: list[str]
    retrieved_memory_ids: list[str]
    raw_llm: dict[str, Any]
    trace_id: str  # New: link to decision trace
    memory_influence_scores: dict[str, float]  # New: which memories mattered most


class MemoryAwareAgent:
    def __init__(self, gateway: MemoryGateway, llm: LLMClient | None = None) -> None:
        self.gateway = gateway
        self.llm = llm or LLMClient()

    def _calculate_memory_influence_scores(
        self,
        candidate_memories: list[dict[str, Any]],
        user_input: str,
        llm_output: str
    ) -> dict[str, float]:
        """
        Calculate how much each memory influenced the decision.

        Score factors:
        - Trust score of the memory (higher = more influence)
        - Recency (more recent = more influence)
        - Content relevance (closer content length = more similar topic)
        """
        scores = {}

        if not candidate_memories:
            return scores

        for memory in candidate_memories:
            memory_id = memory["memory_id"]

            # Base score from trust (0-100 -> 0-0.4)
            trust_component = memory.get("trust_score", 50.0) / 100.0 * 0.4

            # Recency component (0-0.3)
            # Newer memories get higher scores
            created_at = memory.get("created_at", "")
            try:
                mem_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                age_hours = (datetime.now(timezone.utc) - mem_time).total_seconds() / 3600
                recency_component = max(0, 0.3 * (1 - min(age_hours / 168, 1)))  # 168 hours = 1 week
            except:
                recency_component = 0.15  # default mid-range

            # Relevance component (0-0.3)
            # Check if memory content appears in output
            memory_content = memory.get("content", "").lower()
            output_lower = llm_output.lower()

            if memory_content and memory_content in output_lower:
                relevance_component = 0.3  # Memory content directly used
            else:
                # Content length similarity as proxy for topic relevance
                len_diff = abs(len(memory_content) - len(user_input))
                relevance_component = max(0, 0.15 * (1 - min(len_diff / 1000, 1)))

            total_score = trust_component + recency_component + relevance_component
            scores[memory_id] = round(min(1.0, total_score), 3)

        return scores

    def run(self, tenant_id: str, agent_id: str, user_input: str, session_id: str | None = None) -> AgentRunResult:
        trace_id = str(uuid4())

        # Step 1: Retrieve relevant memories
        query_result = self.gateway.query_memory(
            type("QueryPayload", (), {"tenant_id": tenant_id, "agent_id": agent_id, "query": user_input, "filters": {}})()
        )
        candidate_memories = query_result["results"][:5]
        retrieved_memory_ids = [m["memory_id"] for m in candidate_memories]

        # Record READ events for each retrieved memory
        read_event_ids = []
        for memory in candidate_memories:
            read_event = self.gateway.write_memory(
                MemoryWriteRequest(
                    tenant_id=tenant_id,
                    agent_id=agent_id,
                    content=f"[READ] {memory['content']}",
                    source_type="system",
                    session_id=session_id,
                    metadata={
                        "event_type": "read",
                        "memory_id": memory["memory_id"],
                        "trace_id": trace_id,
                        "operation": "memory_retrieval"
                    }
                )
            )
            read_event_ids.append(read_event["event"]["event_id"])

        # Step 2: Build context and call LLM
        context_block = "\n".join(f"- {m['content']} [memory_id={m['memory_id']}]" for m in candidate_memories)
        messages = [
            {"role": "system", "content": "You are a memory-aware enterprise agent. Cite memory_ids in your answer when relevant."},
            {"role": "system", "content": f"Relevant memories:\n{context_block}" if context_block else "Relevant memories:\n(none)"},
            {"role": "user", "content": user_input},
        ]

        # Create prompt hash for tracing
        prompt_str = str(messages)
        llm_prompt_hash = hashlib.sha256(prompt_str.encode("utf-8")).hexdigest()

        llm_response = self.llm.chat(messages)
        llm_output_hash = hashlib.sha256(llm_response.content.encode("utf-8")).hexdigest()

        # Step 3: Calculate memory influence scores
        memory_influence_scores = self._calculate_memory_influence_scores(
            candidate_memories, user_input, llm_response.content
        )

        # Calculate total influence (0 = no memory used, 1 = heavily influenced by memory)
        if memory_influence_scores:
            total_influence = round(sum(memory_influence_scores.values()) / len(memory_influence_scores), 3)
        else:
            total_influence = 0.0

        cited_memory_ids = retrieved_memory_ids  # In production, parse LLM output for actual citations

        # Step 4: Write user input as memory event
        write = self.gateway.write_memory(
            MemoryWriteRequest(
                tenant_id=tenant_id,
                agent_id=agent_id,
                content=user_input,
                source_type="user",
                session_id=session_id,
                metadata={
                    "trace_id": trace_id,
                    "answer_preview": llm_response.content[:200],
                    "cited_memory_ids": cited_memory_ids,
                    "retrieved_memory_ids": retrieved_memory_ids,
                    "llm_model": self.llm.model,
                    "memory_influence_scores": memory_influence_scores,
                    "total_influence_score": total_influence
                },
            )
        )

        output_event_ids = [write["event"]["event_id"]]
        output_memory_ids = [write["memory_id"]]

        # Step 5: Create decision trace
        decision_trace = DecisionTrace(
            trace_id=trace_id,
            tenant_id=tenant_id,
            agent_id=agent_id,
            session_id=session_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            input_memory_ids=retrieved_memory_ids,
            input_memory_events=read_event_ids,
            user_input=user_input,
            llm_prompt_hash=llm_prompt_hash,
            llm_output=llm_response.content,
            llm_output_hash=llm_output_hash,
            llm_model=self.llm.model,
            output_memory_ids=output_memory_ids,
            output_memory_events=output_event_ids,
            memory_influence_scores=memory_influence_scores,
            total_influence_score=total_influence,
            metadata={
                "retrieved_count": len(candidate_memories),
                "cited_count": len(cited_memory_ids)
            }
        )

        self.gateway.create_decision_trace(decision_trace)

        return AgentRunResult(
            answer=llm_response.content,
            memory_write=write,
            cited_memory_ids=cited_memory_ids,
            retrieved_memory_ids=retrieved_memory_ids,
            raw_llm=llm_response.raw,
            trace_id=trace_id,
            memory_influence_scores=memory_influence_scores
        )
