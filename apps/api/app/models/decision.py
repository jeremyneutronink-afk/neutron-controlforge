import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.app.core.database import Base


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    action_id: Mapped[str] = mapped_column(
        ForeignKey("actions.id"),
        nullable=False,
        index=True,
    )

    decision: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    risk: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    reason: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    policy: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )