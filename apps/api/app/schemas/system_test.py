from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    SecretStr,
)


class SystemTestCatalogItem(BaseModel):
    key: str
    name: str
    category: str
    description: str

    severity: str
    expected_outcome: str


class SystemTestRunRequest(BaseModel):
    agent_id: str

    # SecretStr prevents accidental display in representations
    # and validation error output.
    agent_api_key: SecretStr


class SystemTestResultResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: str
    agent_id: str

    assessment_run_id: str | None

    test_key: str
    test_name: str
    category: str
    severity: str

    expected_outcome: str
    actual_outcome: str

    passed: bool
    evidence: dict

    created_at: datetime


class SystemTestBatchResponse(BaseModel):
    assessment_run_id: str
    agent_id: str

    total: int
    passed: int
    failed: int

    results: list[
        SystemTestResultResponse
    ]