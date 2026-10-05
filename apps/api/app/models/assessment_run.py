import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from apps.api.app.core.database import Base


class AssessmentRun(Base):
    __tablename__ = "assessment_runs"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(
            uuid.uuid4()
        ),
    )

    agent_id: Mapped[str] = mapped_column(
        ForeignKey("agents.id"),
        nullable=False,
        index=True,
    )

    # Examples:
    # POLICY_SINGLE
    # POLICY_PACK
    # POLICY_ALL
    # SYSTEM_ALL
    assessment_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        index=True,
    )

    # Optional identifier for the specific thing being run.
    #
    # Examples:
    # authorization-baseline
    # trust-boundary
    # safe-refund
    #
    # SYSTEM_ALL and POLICY_ALL generally use None.
    scope_key: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        index=True,
    )

    # RUNNING
    # COMPLETED
    # FAILED
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="RUNNING",
        index=True,
    )

    total: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    passed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    failed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
        index=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )