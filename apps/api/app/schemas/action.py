from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DecisionType(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ProvenanceInput(BaseModel):
    source: str
    trust: str


class ActionEvaluateRequest(BaseModel):
    agent_id: str
    run_id: str

    action: str = Field(
        min_length=1,
        max_length=120,
    )

    resource: str | None = None

    arguments: dict[str, Any] = Field(
        default_factory=dict,
    )

    provenance: ProvenanceInput


class ActionEvaluateResponse(BaseModel):
    action_id: str
    decision_id: str
    execution_id: str
    approval_id: str | None = None

    decision: DecisionType
    risk: RiskLevel

    reason: str
    policy: str