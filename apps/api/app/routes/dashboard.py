from datetime import datetime
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.core.database import get_db
from apps.api.app.models import (
    Action,
    Agent,
    Approval,
    Event,
    Run,
    SecurityAuditEvent,
)
from apps.api.app.routes.findings import (
    router as findings_router,
)
from apps.api.app.routes.system_tests import (
    router as system_tests_router,
)
from apps.api.app.routes.reports import (
    router as reports_router,
)
from apps.api.app.schemas.agent import (
    AgentResponse,
)
from apps.api.app.schemas.event import (
    EventResponse,
)
from apps.api.app.schemas.run import (
    RunResponse,
)
from apps.api.app.services.auth import (
    require_admin_key,
)


router = APIRouter(
    prefix="/v1",
    tags=["Dashboard"],
    dependencies=[
        Depends(require_admin_key)
    ],
)

router.include_router(
    findings_router
)

router.include_router(
    system_tests_router
)

router.include_router(
    reports_router
)


class DashboardApprovalResponse(BaseModel):
    id: str
    action_id: str
    run_id: str
    agent_id: str

    agent_name: str
    action_name: str
    resource: str | None
    arguments: dict[str, Any]

    status: str
    reason: str

    created_at: datetime


class SecurityAuditEventResponse(BaseModel):
    id: str
    agent_id: str | None

    event_type: str
    severity: str
    message: str

    event_data: dict[str, Any]

    created_at: datetime


@router.get(
    "/agents",
    response_model=list[
        AgentResponse
    ],
)
def list_agents(
    db: Session = Depends(
        get_db
    ),
):
    statement = (
        select(Agent)
        .order_by(
            Agent.name.asc()
        )
    )

    return db.scalars(
        statement
    ).all()


@router.get(
    "/runs",
    response_model=list[
        RunResponse
    ],
)
def list_runs(
    db: Session = Depends(
        get_db
    ),
):
    statement = (
        select(Run)
        .order_by(
            Run.started_at.desc()
        )
    )

    return db.scalars(
        statement
    ).all()


@router.get(
    "/dashboard/runs/{run_id}",
    response_model=RunResponse,
)
def get_dashboard_run(
    run_id: str,
    db: Session = Depends(
        get_db
    ),
):
    """
    Operator-only run lookup.

    Agent-facing run reads use X-Agent-Key in main.py. The dashboard
    uses this separate administrator-authenticated route so operators
    never need an agent machine credential just to inspect a run.
    """

    run = db.get(
        Run,
        run_id,
    )

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="Run not found.",
        )

    return run


@router.get(
    "/runs/{run_id}/timeline",
    response_model=list[
        EventResponse
    ],
)
def get_run_timeline(
    run_id: str,
    db: Session = Depends(
        get_db
    ),
):
    run = db.get(
        Run,
        run_id,
    )

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="Run not found.",
        )

    statement = (
        select(Event)
        .where(
            Event.run_id
            == run_id
        )
        .order_by(
            Event.created_at.asc()
        )
    )

    return db.scalars(
        statement
    ).all()


@router.get(
    "/dashboard/approvals",
    response_model=list[
        DashboardApprovalResponse
    ],
)
def list_dashboard_approvals(
    db: Session = Depends(
        get_db
    ),
):
    statement = (
        select(
            Approval,
            Action,
            Agent,
        )
        .join(
            Action,
            Action.id
            == Approval.action_id,
        )
        .join(
            Agent,
            Agent.id
            == Approval.agent_id,
        )
        .where(
            Approval.status
            == "PENDING"
        )
        .order_by(
            Approval.created_at.asc()
        )
    )

    rows = db.execute(
        statement
    ).all()

    return [
        DashboardApprovalResponse(
            id=approval.id,
            action_id=(
                approval.action_id
            ),
            run_id=(
                approval.run_id
            ),
            agent_id=(
                approval.agent_id
            ),
            agent_name=(
                agent.name
            ),
            action_name=(
                action.action_name
            ),
            resource=(
                action.resource
            ),
            arguments=(
                action.arguments
            ),
            status=(
                approval.status
            ),
            reason=(
                approval.reason
            ),
            created_at=(
                approval.created_at
            ),
        )
        for (
            approval,
            action,
            agent,
        ) in rows
    ]


@router.get(
    "/dashboard/security-audit",
    response_model=list[
        SecurityAuditEventResponse
    ],
)
def list_security_audit_events(
    limit: int = 50,
    db: Session = Depends(
        get_db
    ),
):
    safe_limit = max(
        1,
        min(
            limit,
            200,
        ),
    )

    statement = (
        select(
            SecurityAuditEvent
        )
        .order_by(
            SecurityAuditEvent
            .created_at
            .desc()
        )
        .limit(
            safe_limit
        )
    )

    return db.scalars(
        statement
    ).all()
