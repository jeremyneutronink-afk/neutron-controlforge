from pydantic import BaseModel, ConfigDict, Field


class AgentCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )


class AgentResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: str
    name: str
    description: str | None
    is_active: bool

    api_key_prefix: str | None = None


class AgentCredentialResponse(
    AgentResponse
):
    # Returned only during initial provisioning/rotation.
    # The raw key cannot be recovered later because only
    # its hash is stored.
    api_key: str