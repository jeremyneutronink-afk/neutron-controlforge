from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FindingSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FindingStatus(str, Enum):
    OPEN = "OPEN"
    IN_REMEDIATION = "IN_REMEDIATION"
    READY_FOR_RETEST = "READY_FOR_RETEST"
    RESOLVED = "RESOLVED"


class FindingRetestStatus(str, Enum):
    NOT_RUN = "NOT_RUN"
    PASS = "PASS"
    FAIL = "FAIL"


class FindingCreateRequest(BaseModel):
    agent_id: str

    title: str = Field(
        min_length=1,
        max_length=255,
    )

    severity: FindingSeverity

    description: str = Field(
        min_length=1,
        max_length=5000,
    )

    remediation: str | None = Field(
        default=None,
        max_length=5000,
    )


class FindingUpdateRequest(BaseModel):
    status: FindingStatus | None = None
    severity: FindingSeverity | None = None

    remediation: str | None = Field(
        default=None,
        max_length=5000,
    )

    retest_status: FindingRetestStatus | None = None


class FindingResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: str
    agent_id: str
    source_test_result_id: str | None

    title: str
    severity: FindingSeverity
    status: FindingStatus

    description: str
    evidence: dict[str, Any]

    remediation: str | None
    retest_status: str | None

    created_at: datetime
    updated_at: datetime