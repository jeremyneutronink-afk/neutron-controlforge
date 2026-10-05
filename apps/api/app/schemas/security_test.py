from datetime import datetime
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
)


class SecurityTestCatalogItem(BaseModel):
    key: str
    pack_key: str
    pack_name: str

    name: str
    category: str
    description: str

    expected_decision: str

    severity: str
    remediation_hint: str
    tags: list[str]


class SecurityTestPackResponse(BaseModel):
    key: str
    name: str
    description: str
    category: str

    test_count: int


class SecurityTestRunRequest(BaseModel):
    agent_id: str
    test_key: str


class SecurityTestPackRunRequest(BaseModel):
    agent_id: str
    pack_key: str


class SecurityTestRunAllRequest(BaseModel):
    agent_id: str


class SecurityTestResultResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: str
    agent_id: str

    assessment_run_id: str | None

    test_key: str
    test_name: str
    category: str

    expected_decision: str
    actual_decision: str

    passed: bool

    evidence: dict[str, Any]

    created_at: datetime


class SecurityTestBatchResponse(BaseModel):
    assessment_run_id: str

    scope: str
    scope_key: str | None
    agent_id: str

    total: int
    passed: int
    failed: int

    results: list[
        SecurityTestResultResponse
    ]