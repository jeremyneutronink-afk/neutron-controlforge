import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from apps.api.app.core.database import Base


class SystemSecurityTestResult(Base):
    __tablename__ = "system_security_test_results"

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

    # Nullable so test history created before assessment batching
    # remains compatible.
    assessment_run_id: Mapped[str | None] = mapped_column(
        ForeignKey("assessment_runs.id"),
        nullable=True,
        index=True,
    )

    test_key: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    test_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
        index=True,
    )

    severity: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    expected_outcome: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    actual_outcome: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    passed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        index=True,
    )

    evidence: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(
            timezone.utc
        ),
        index=True,
    )