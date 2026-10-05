from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RunCreate(BaseModel):
    agent_id: str


class RunResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: str
    agent_id: str

    status: str

    started_at: datetime
    completed_at: datetime | None