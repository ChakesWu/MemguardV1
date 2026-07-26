"""
Influence Score Calculation

Calculates how much each memory operation influenced the final decision.

Algorithm:
- Base score = 1.0 (every read has base influence)
- Similarity boost = similarity_score (for vector retrievals)
- Recency boost = 1.0 / (1 + hours_since_read)
- Type weight = {episodic: 1.2, semantic: 1.1, procedural: 1.0, working: 0.9}

Final influence = base * (1 + similarity) * recency * type_weight
Normalized to [0, 1] range
"""

from typing import List, Dict, Optional
from datetime import datetime
import math


class InfluenceCalculator:
    """Calculate memory influence scores for decision tracing"""

    # Memory type weights - episodic and semantic are most influential
    TYPE_WEIGHTS = {
        "episodic": 1.2,      # Historical cases are highly influential
        "semantic": 1.1,      # Regulations are important
        "procedural": 1.0,    # SOPs are standard weight
        "working": 0.9,       # Current state is context
        "user_preferences": 0.8,  # User prefs are background
    }

    @staticmethod
    def calculate_influence(
        memory_event: Dict,
        decision_time: datetime,
        similarity_score: Optional[float] = None
    ) -> float:
        """
        Calculate influence score for a single memory event

        Args:
            memory_event: Memory operation event dict
            decision_time: When the decision was made
            similarity_score: Similarity from vector search (0-1), optional

        Returns:
            Influence score (0-1)
        """
        # Base score - all reads have base influence
        base = 1.0

        # Similarity boost (for vector retrievals like ChromaDB)
        similarity_boost = similarity_score if similarity_score else 0.0

        # Recency boost - more recent memories are more influential
        try:
            event_time = datetime.fromisoformat(memory_event.get("timestamp", datetime.now().isoformat()))
            hours_diff = (decision_time - event_time).total_seconds() / 3600
            # Decay function: fresh memories (0 hours) = 1.0, old memories decay
            recency = 1.0 / (1.0 + hours_diff)
        except Exception:
            recency = 1.0  # Default if timestamp parsing fails

        # Memory type weight
        memory_type = memory_event.get("memory_type", "working")
        type_weight = InfluenceCalculator.TYPE_WEIGHTS.get(memory_type, 1.0)

        # Calculate final score
        # Formula: base * (1 + similarity) * recency * type_weight
        influence = base * (1.0 + similarity_boost) * recency * type_weight

        # Normalize to [0, 1] - cap at 1.0
        normalized = min(influence, 1.0)

        return round(normalized, 2)

    @staticmethod
    def calculate_batch_influences(
        memory_events: List[Dict],
        decision_time: datetime
    ) -> List[Dict]:
        """
        Calculate influences for a batch of memory events

        Args:
            memory_events: List of memory event dicts
            decision_time: When the decision was made

        Returns:
            List of events with influence_score field added
        """
        results = []

        for event in memory_events:
            # Extract similarity if available from context
            similarity = None
            context = event.get("context", {})

            # Check for similarities array (from vector search)
            if isinstance(context, dict):
                similarities = context.get("similarities", [])
                if similarities and len(similarities) > 0:
                    similarity = max(similarities)  # Use best match

            # Calculate influence
            influence = InfluenceCalculator.calculate_influence(
                event, decision_time, similarity
            )

            # Add to result
            results.append({
                **event,
                "influence_score": influence
            })

        return results

    @staticmethod
    def get_top_influences(
        memory_events: List[Dict],
        decision_time: datetime,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Get top K most influential memory events

        Args:
            memory_events: List of memory event dicts
            decision_time: When the decision was made
            top_k: Number of top events to return

        Returns:
            List of top K events sorted by influence score
        """
        # Calculate all influences
        with_influences = InfluenceCalculator.calculate_batch_influences(
            memory_events, decision_time
        )

        # Sort by influence score (descending)
        sorted_events = sorted(
            with_influences,
            key=lambda x: x.get("influence_score", 0),
            reverse=True
        )

        # Return top K
        return sorted_events[:top_k]

    @staticmethod
    def calculate_total_influence(memory_events: List[Dict]) -> float:
        """
        Calculate total influence score across all events

        Args:
            memory_events: List of events (must have influence_score field)

        Returns:
            Total influence score
        """
        total = sum(e.get("influence_score", 0) for e in memory_events)
        return round(total, 2)
