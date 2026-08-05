"""Provider-neutral contracts for memory governance."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Mapping, Optional, Tuple


class TrustLevel(str, Enum):
    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PolicyAction(str, Enum):
    ALLOW = "allow"
    WARN = "warn"
    REVIEW_REQUIRED = "review_required"
    BLOCK = "block"
    QUARANTINE = "quarantine"


class ConflictStatus(str, Enum):
    UNKNOWN = "unknown"
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DataClassification(str, Enum):
    UNKNOWN = "unknown"
    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"
    PRIVATE_EMPLOYEE = "private_employee"
    SECRET = "secret"


@dataclass(frozen=True)
class RetrievalSignals:
    """Retrieval evidence. These values are not a trust score."""

    similarity: Optional[float] = None
    importance: Optional[float] = None
    recency: Optional[float] = None
    retrieval_score: Optional[float] = None
    confidence_level: Optional[str] = None
    retrieved: bool = False
    included_in_prompt: bool = False
    cited: bool = False


@dataclass(frozen=True)
class MemoryEvidence:
    memory_id: str
    tenant_id: Optional[str] = None
    content: Optional[str] = None
    content_hash: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    writer_id: Optional[str] = None
    created_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    version_id: Optional[str] = None
    superseded_by_version_id: Optional[str] = None
    conflict_status: ConflictStatus = ConflictStatus.UNKNOWN
    conflicting_memory_ids: Tuple[str, ...] = ()
    data_classification: DataClassification = DataClassification.UNKNOWN
    allowed_purposes: Optional[Tuple[str, ...]] = None
    retrieval: RetrievalSignals = field(default_factory=RetrievalSignals)
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.content_hash and self.content is not None:
            object.__setattr__(self, "content_hash", hashlib.sha256(self.content.encode("utf-8")).hexdigest())


@dataclass(frozen=True)
class GovernanceContext:
    tenant_id: str
    agent_id: str
    purpose: str
    evaluated_at: datetime
    actor_id: Optional[str] = None
    risk_level: str = "standard"


def _validate_score_map(name: str, values: Mapping[str, float]) -> None:
    for key, score in values.items():
        if not 0 <= float(score) <= 100:
            raise ValueError(f"{name}[{key!r}] must be between 0 and 100")


@dataclass(frozen=True)
class GovernancePolicy:
    policy_id: str
    source_scores: Mapping[str, float] = field(default_factory=dict)
    writer_scores: Mapping[str, float] = field(default_factory=dict)
    max_age_days: Mapping[str, int] = field(default_factory=dict)
    allow_threshold: float = 80.0
    warn_threshold: float = 60.0
    review_threshold: float = 40.0

    def __post_init__(self) -> None:
        _validate_score_map("source_scores", self.source_scores)
        _validate_score_map("writer_scores", self.writer_scores)
        if not 0 <= self.review_threshold <= self.warn_threshold <= self.allow_threshold <= 100:
            raise ValueError("policy thresholds must be ordered between 0 and 100")
        if any(days <= 0 for days in self.max_age_days.values()):
            raise ValueError("max_age_days values must be positive")


@dataclass(frozen=True)
class TrustFactor:
    score: Optional[float] = None
    reason: str = "metadata unavailable"


@dataclass(frozen=True)
class TrustFactors:
    source: TrustFactor = field(default_factory=TrustFactor)
    writer: TrustFactor = field(default_factory=TrustFactor)
    freshness: TrustFactor = field(default_factory=TrustFactor)
    conflict: TrustFactor = field(default_factory=TrustFactor)
    policy_fit: TrustFactor = field(default_factory=TrustFactor)


@dataclass(frozen=True)
class TrustResult:
    score: Optional[float]
    level: TrustLevel
    factors: TrustFactors
    reason_codes: Tuple[str, ...]
    missing_factors: Tuple[str, ...]


@dataclass(frozen=True)
class PolicyDecision:
    action: PolicyAction
    enforced: bool
    reason_codes: Tuple[str, ...]
    explanation: str


@dataclass(frozen=True)
class InfluenceResult:
    memory_id: str
    score: float
    retrieved: bool
    included_in_prompt: bool
    cited: bool
    output_supported: bool
    reason_codes: Tuple[str, ...]


@dataclass(frozen=True)
class EvidenceEvaluation:
    evidence: MemoryEvidence
    trust: TrustResult
    policy: PolicyDecision
    influence: InfluenceResult


@dataclass(frozen=True)
class PromptGateResult:
    prompt: str
    included_memory_ids: Tuple[str, ...]
    blocked_memory_ids: Tuple[str, ...]
