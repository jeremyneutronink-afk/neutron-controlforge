import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.app.core.database import Base


class Execution(Base):
    __tablename__ = "executions"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    action_id: Mapped[str] = mapped_column(
        ForeignKey("actions.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    run_id: Mapped[str] = mapped_column(
        ForeignKey("runs.id"),
        nullable=False,
        index=True,
    )

    agent_id: Mapped[str] = mapped_column(
        ForeignKey("agents.id"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        index=True,
    )

    executor: Mapped[str] = mapped_column(
        String(100),
        default="sandbox",
        nullable=False,
    )

    result: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    executed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )