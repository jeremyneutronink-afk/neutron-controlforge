import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.app.core.database import Base


class Action(Base):
    __tablename__ = "actions"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    agent_id: Mapped[str] = mapped_column(
        ForeignKey("agents.id"),
        nullable=False,
        index=True,
    )

    run_id: Mapped[str] = mapped_column(
        ForeignKey("runs.id"),
        nullable=False,
        index=True,
    )

    action_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    resource: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    arguments: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    provenance: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )