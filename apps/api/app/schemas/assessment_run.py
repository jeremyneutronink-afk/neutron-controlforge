from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
)


class AssessmentRunResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: str
    agent_id: str

    assessment_type: str
    scope_key: str | None

    status: str

    total: int
    passed: int
    failed: int

    started_at: datetime
    completed_at: datetime | None