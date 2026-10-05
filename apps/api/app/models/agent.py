import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.app.core.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Never store the raw API key.
    #
    # Existing agents are allowed to have NULL here temporarily
    # so migrations can succeed. An agent without a key simply
    # cannot authenticate until a key is provisioned.
    api_key_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    # Safe identifier for operators to distinguish credentials.
    # This is not enough to authenticate.
    api_key_prefix: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )