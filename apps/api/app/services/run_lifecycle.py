from datetime import datetime, timezone

from sqlalchemy.orm import Session

from apps.api.app.models import Event, Run


VALID_RUN_STATUSES = {
    "CREATED",
    "ACTIVE",
    "WAITING_APPROVAL",
    "BLOCKED",
    "EXECUTING",
    "COMPLETED",
    "FAILED",
}


def set_run_status(
    *,
    db: Session,
    run: Run,
    status: str,
    message: str,
    event_data: dict | None = None,
) -> None:
    """
    Update run state and persist a corresponding audit event.

    We avoid emitting duplicate RUN_STATUS_CHANGED events when
    the requested state already matches the current state.
    """

    if status not in VALID_RUN_STATUSES:
        raise ValueError(
            f"Unsupported run status: {status}"
        )

    if run.status == status:
        return

    previous_status = run.status
    run.status = status

    if status == "COMPLETED":
        run.completed_at = datetime.now(
            timezone.utc
        )

    elif previous_status == "COMPLETED":
        # Completed runs should not normally reopen, but keeping this
        # defensive behavior prevents stale completion timestamps if
        # that rule changes later.
        run.completed_at = None

    event = Event(
        run_id=run.id,
        agent_id=run.agent_id,
        event_type="RUN_STATUS_CHANGED",
        severity=(
            "HIGH"
            if status in {
                "BLOCKED",
                "FAILED",
            }
            else "INFO"
        ),
        message=message,
        event_data={
            "previous_status": previous_status,
            "new_status": status,
            **(event_data or {}),
        },
    )

    db.add(event)