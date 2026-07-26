"""
Semantic Memory Module

Semantic memory stores and retrieves regulatory knowledge.
Uses ChromaDB for vector similarity search over regulation text.

Semantic memory stores and retrieves regulatory knowledge.
Uses ChromaDB for vector similarity search over regulation text.

[Business Purpose] Provides regulatory context for compliance decisions
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SemanticMemory:
    """
    Semantic Memory Manager

    Stores: Regulatory text from HKMA, MAS, FinCEN, FATF
    Query: "What regulations apply to structuring transactions?"
    """

    def __init__(self, chroma_path: Optional[Path] = None):
        """
        Initialize semantic memory with ChromaDB

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
                self.client = chromadb.Client()

            self.collection = self.client.get_or_create_collection(
                name="semantic_memory",
                metadata={"description": "Regulatory text knowledge base"}
            )

            logger.info(f"Semantic memory initialized: {self.collection.count()} regulations")

        except ImportError:
            logger.warning("ChromaDB not installed - semantic memory disabled")
            self.collection = None
        except Exception as e:
            logger.error(f"Failed to initialize semantic memory: {e}")
            self.collection = None

    def query_regulations(
        self,
        compliance_question: str,
        n_results: int = 5,
        jurisdiction_filter: Optional[str] = None,
        authority_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query for relevant regulatory text

        Args:
            compliance_question: Question or scenario description
            n_results: Number of relevant regulations to return
            jurisdiction_filter: Optional filter by jurisdiction (e.g., "HK", "SG", "US")
            authority_filter: Optional filter by authority (e.g., "HKMA", "MAS")

        Returns:
            List of regulation dicts with content and metadata
        """
        if not self.collection:
            logger.warning("Semantic memory not available")
            return []

        try:
            # Build filter
            where_filter = {}
            if jurisdiction_filter:
                where_filter["jurisdiction"] = jurisdiction_filter
            if authority_filter:
                where_filter["authority"] = authority_filter

            # Query ChromaDB
            results = self.collection.query(
                query_texts=[compliance_question],
                n_results=n_results,
                where=where_filter if where_filter else None
            )

            # Format results
            regulations = []
            if results and results['ids'] and len(results['ids']) > 0:
                for i in range(len(results['ids'][0])):
                    regulation = {
                        "regulation_id": results['ids'][0][i],
                        "content": results['documents'][0][i],
                        "similarity_score": 1 - results['distances'][0][i] if 'distances' in results else None,
                        "metadata": results['metadatas'][0][i] if 'metadatas' in results else {}
                    }
                    regulations.append(regulation)

            logger.info(f"Found {len(regulations)} relevant regulations for: {compliance_question[:50]}...")
            return regulations

        except Exception as e:
            logger.error(f"Semantic memory query failed: {e}")
            return []

    def get_regulation_by_id(self, regulation_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific regulation by ID

        Args:
            regulation_id: Regulation identifier (e.g., "HKMA-AML-2023-§35")

        Returns:
            Regulation dict or None if not found
        """
        if not self.collection:
            return None

        try:
            result = self.collection.get(ids=[regulation_id])

            if result and result['ids']:
                return {
                    "regulation_id": result['ids'][0],
                    "content": result['documents'][0],
                    "metadata": result['metadatas'][0] if result['metadatas'] else {}
                }

            return None

        except Exception as e:
            logger.error(f"Failed to retrieve regulation {regulation_id}: {e}")
            return None

    def search_by_authority(self, authority: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get all regulations from a specific authority

        Args:
            authority: Authority name (e.g., "HKMA", "MAS", "FinCEN", "FATF")
            limit: Maximum number of results

        Returns:
            List of regulation dicts
        """
        if not self.collection:
            return []

        try:
            results = self.collection.get(
                where={"authority": authority},
                limit=limit
            )

            regulations = []
            if results and results['ids']:
                for i in range(len(results['ids'])):
                    regulation = {
                        "regulation_id": results['ids'][i],
                        "content": results['documents'][i],
                        "metadata": results['metadatas'][i] if results['metadatas'] else {}
                    }
                    regulations.append(regulation)

            return regulations

        except Exception as e:
            logger.error(f"Failed to search regulations by authority {authority}: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get semantic memory statistics

        Returns:
            Statistics dict
        """
        if not self.collection:
            return {"status": "disabled", "total_regulations": 0}

        try:
            return {
                "status": "active",
                "total_regulations": self.collection.count(),
                "collection_name": self.collection.name
            }
        except Exception as e:
            logger.error(f"Failed to get semantic memory stats: {e}")
            return {"status": "error", "error": str(e)}
