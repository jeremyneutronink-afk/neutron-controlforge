from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict


class ExecutionStatus(str, Enum):
    READY = "READY"
    BLOCKED_APPROVAL = "BLOCKED_APPROVAL"
    BLOCKED_DENY = "BLOCKED_DENY"
    DENIED = "DENIED"
    EXECUTING = "EXECUTING"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class ExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    action_id: str
    run_id: str
    agent_id: str

    status: ExecutionStatus
    executor: str

    result: dict[str, Any] | None
    error_message: str | None

    created_at: datetime
    executed_at: datetime | None