from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    agent_id: str
    event_type: str
    severity: str
    message: str
    event_data: dict[str, Any]
    created_at: datetime