from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"


class ApprovalResolveRequest(BaseModel):
    resolved_by: str = Field(
        min_length=1,
        max_length=120,
    )

    note: str | None = Field(
        default=None,
        max_length=1000,
    )


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    action_id: str
    run_id: str
    agent_id: str

    status: ApprovalStatus
    reason: str

    created_at: datetime
    resolved_at: datetime | None
    resolved_by: str | None
    resolution_note: str | None