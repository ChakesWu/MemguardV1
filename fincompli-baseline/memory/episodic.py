"""
Episodic Memory Module

Episodic memory stores and retrieves historical SAR case experiences.
Uses ChromaDB for vector similarity search.

[Business Purpose] Enables agents to learn from past compliance cases
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class EpisodicMemory:
    """
    Episodic Memory Manager

    Stores: Historical SAR cases with case summaries
    Query: "Find similar past cases for this transaction pattern"
    """

    def __init__(self, chroma_path: Optional[Path] = None):
        """
        Initialize episodic memory with ChromaDB

        Args:
            chroma_path: Path to ChromaDB persistence directory
        """
        self.chroma_path = chroma_path
        self.collection = None
        self._initialize_collection()

    def _initialize_collection(self):
        """Initialize ChromaDB collection"""
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            if self.chroma_path:
                self.client = chromadb.PersistentClient(
                    path=str(self.chroma_path),
                    settings=ChromaSettings(anonymized_telemetry=False)
                )
            else:
                # In-memory for testing
                self.client = chromadb.Client()

            self.collection = self.client.get_or_create_collection(
                name="episodic_memory",
                metadata={"description": "Historical SAR cases"}
            )

            logger.info(f"Episodic memory initialized: {self.collection.count()} cases")

        except ImportError:
            logger.warning("ChromaDB not installed - episodic memory disabled")
            self.collection = None
        except Exception as e:
            logger.error(f"Failed to initialize episodic memory: {e}")
            self.collection = None

    def query_similar_cases(
        self,
        transaction_pattern: str,
        n_results: int = 5,
        case_type_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query for similar historical SAR cases

        Args:
            transaction_pattern: Description of current transaction pattern
            n_results: Number of similar cases to return
            case_type_filter: Optional filter by case type (e.g., "structuring")

        Returns:
            List of similar case dicts with metadata and similarity scores
        """
        if not self.collection:
            logger.warning("Episodic memory not available")
            return []

        try:
            # Build filter
            where_filter = None
            if case_type_filter:
                where_filter = {"case_type": case_type_filter}

            # Query ChromaDB
            results = self.collection.query(
                query_texts=[transaction_pattern],
                n_results=n_results,
                where=where_filter
            )

            # Format results
            similar_cases = []
            if results and results['ids'] and len(results['ids']) > 0:
                for i in range(len(results['ids'][0])):
                    case = {
                        "sar_id": results['ids'][0][i],
                        "case_summary": results['documents'][0][i],
                        "similarity_score": 1 - results['distances'][0][i] if 'distances' in results else None,
                        "metadata": results['metadatas'][0][i] if 'metadatas' in results else {}
                    }
                    similar_cases.append(case)

            logger.info(f"Found {len(similar_cases)} similar cases for pattern: {transaction_pattern[:50]}...")
            return similar_cases

        except Exception as e:
            logger.error(f"Episodic memory query failed: {e}")
            return []

    def get_case_by_id(self, sar_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific SAR case by ID

        Args:
            sar_id: SAR case identifier

        Returns:
            Case dict or None if not found
        """
        if not self.collection:
            return None

        try:
            result = self.collection.get(ids=[sar_id])

            if result and result['ids']:
                return {
                    "sar_id": result['ids'][0],
                    "case_summary": result['documents'][0],
                    "metadata": result['metadatas'][0] if result['metadatas'] else {}
                }

            return None

        except Exception as e:
            logger.error(f"Failed to retrieve case {sar_id}: {e}")
            return None

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get episodic memory statistics

        Returns:
            Statistics dict
        """
        if not self.collection:
            return {"status": "disabled", "total_cases": 0}

        try:
            return {
                "status": "active",
                "total_cases": self.collection.count(),
                "collection_name": self.collection.name
            }
        except Exception as e:
            logger.error(f"Failed to get episodic memory stats: {e}")
            return {"status": "error", "error": str(e)}
