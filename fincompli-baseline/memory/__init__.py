"""
Memory Layer Module

Unified interface for all memory types in the FinCompli system.

Memory Types:
- Short-term: Current conversation context (LangGraph State)
- Episodic: Historical SAR cases (ChromaDB)
- Semantic: Regulatory knowledge (ChromaDB)
- Procedural: SOP rules (SQLite)
- User Preferences: Personalization settings (SQLite)

[Business Purpose] Provides tiered memory architecture for compliance agents
"""

import logging
from pathlib import Path
from typing import Optional

from .short_term import ShortTermMemory
from .episodic import EpisodicMemory
from .semantic import SemanticMemory
from .procedural import ProceduralMemory
from .user_prefs import UserPreferencesMemory

logger = logging.getLogger(__name__)


class MemoryLayer:
    """
    Unified Memory Layer Interface

    Provides single entry point for all memory operations.
    """

    def __init__(
        self,
        chroma_path: Optional[Path] = None,
        sqlite_path: Optional[Path] = None
    ):
        """
        Initialize all memory subsystems

        Args:
            chroma_path: Path to ChromaDB persistence directory
            sqlite_path: Path to SQLite database file
        """
        logger.info("Initializing MemGuard Memory Layer...")

        # Initialize each memory type
        self.short_term = ShortTermMemory()
        self.episodic = EpisodicMemory(chroma_path=chroma_path)
        self.semantic = SemanticMemory(chroma_path=chroma_path)
        self.procedural = ProceduralMemory(db_path=sqlite_path)
        self.user_prefs = UserPreferencesMemory(db_path=sqlite_path)

        logger.info("Memory Layer initialized successfully")

    def get_memory_statistics(self):
        """
        Get statistics for all memory subsystems

        Returns:
            Dict with statistics for each memory type
        """
        return {
            "short_term": {"status": "active", "type": "langgraph_state"},
            "episodic": self.episodic.get_statistics(),
            "semantic": self.semantic.get_statistics(),
            "procedural": self.procedural.get_statistics(),
            "user_prefs": self.user_prefs.get_statistics()
        }

    def health_check(self):
        """
        Check health of all memory subsystems

        Returns:
            Dict with health status
        """
        stats = self.get_memory_statistics()
        
        all_active = all(
            s.get("status") in ["active", "disabled"] 
            for s in stats.values()
        )

        return {
            "healthy": all_active,
            "subsystems": stats
        }


# Convenience exports
__all__ = [
    "MemoryLayer",
    "ShortTermMemory",
    "EpisodicMemory", 
    "SemanticMemory",
    "ProceduralMemory",
    "UserPreferencesMemory"
]
