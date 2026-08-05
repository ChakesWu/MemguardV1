"""Map WideMem retrieval results into MemGuard evidence without coupling packages."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping, Optional, Tuple

from ..models import ConflictStatus, DataClassification, MemoryEvidence, RetrievalSignals


def _parse_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return None


class WideMemSignalAdapter:
    """Uses duck typing so WideMem remains an optional dependency."""

    def from_search_result(
        self,
        result: Any,
        *,
        tenant_id: str,
        conflict_status: Optional[ConflictStatus] = None,
        data_classification: Optional[DataClassification] = None,
        allowed_purposes: Optional[Tuple[str, ...]] = None,
    ) -> MemoryEvidence:
        memory = result.memory
        metadata = dict(getattr(memory, "metadata", {}) or {})
        return MemoryEvidence(
            memory_id=str(getattr(memory, "id")),
            tenant_id=tenant_id,
            content=getattr(memory, "content", None),
            source_type=metadata.get("source_type"),
            source_id=metadata.get("source_id"),
            writer_id=metadata.get("writer_id"),
            created_at=_parse_datetime(getattr(memory, "created_at", None)),
            verified_at=_parse_datetime(metadata.get("verified_at")),
            valid_until=_parse_datetime(metadata.get("valid_until")),
            conflict_status=conflict_status or self._conflict_status(metadata.get("conflict_status")),
            data_classification=data_classification or self._classification(metadata.get("data_classification")),
            allowed_purposes=(
                allowed_purposes
                if allowed_purposes is not None
                else tuple(metadata["allowed_purposes"]) if metadata.get("allowed_purposes") is not None else None
            ),
            retrieval=RetrievalSignals(
                similarity=float(result.similarity_score),
                importance=float(result.importance_score),
                recency=float(result.temporal_score),
                retrieval_score=float(result.final_score),
                retrieved=True,
            ),
            metadata={"provider": "widemem"},
        )

    def from_mapping(self, item: Mapping[str, Any]) -> MemoryEvidence:
        return MemoryEvidence(
            memory_id=str(item["id"]),
            tenant_id=str(item["tenant_id"]),
            content=item.get("content"),
            source_type=item.get("source_type"),
            source_id=item.get("source_id"),
            writer_id=item.get("writer_id"),
            created_at=_parse_datetime(item.get("created_at")),
            verified_at=_parse_datetime(item.get("verified_at")),
            valid_until=_parse_datetime(item.get("valid_until")),
            conflict_status=self._conflict_status(item.get("conflict_status")),
            data_classification=self._classification(item.get("data_classification")),
            allowed_purposes=tuple(item["allowed_purposes"]) if item.get("allowed_purposes") is not None else None,
            retrieval=RetrievalSignals(
                similarity=self._float(item.get("similarity")),
                importance=self._float(item.get("importance")),
                recency=self._float(item.get("recency")),
                retrieval_score=self._float(item.get("final_score")),
                confidence_level=item.get("confidence_level"),
                retrieved=True,
            ),
            metadata={"provider": "widemem"},
        )

    @staticmethod
    def _float(value: Any) -> Optional[float]:
        return float(value) if value is not None else None

    @staticmethod
    def _classification(value: Any) -> DataClassification:
        if isinstance(value, DataClassification):
            return value
        return DataClassification(str(value)) if value is not None else DataClassification.UNKNOWN

    @staticmethod
    def _conflict_status(value: Any) -> ConflictStatus:
        if isinstance(value, ConflictStatus):
            return value
        return ConflictStatus(str(value)) if value is not None else ConflictStatus.UNKNOWN
