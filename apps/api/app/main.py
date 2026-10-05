from datetime import datetime, timezone

from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.core.config import get_settings
from apps.api.app.core.database import get_db
from apps.api.app.models import (
    Action,
    Agent,
    Approval,
    Decision,
    Event,
    Execution,
    IdempotencyRecord,
    Run,
)
from apps.api.app.routes.dashboard import (
    router as dashboard_router,
)
from apps.api.app.routes.security_tests import (
    router as security_tests_router,
)
from apps.api.app.schemas.action import (
    ActionEvaluateRequest,
    ActionEvaluateResponse,
    DecisionType,
)
from apps.api.app.schemas.agent import (
    AgentCreate,
    AgentCredentialResponse,
)
from apps.api.app.schemas.approval import (
    ApprovalResolveRequest,
    ApprovalResponse,
)
from apps.api.app.schemas.event import (
    EventResponse,
)
from apps.api.app.schemas.execution import (
    ExecutionResponse,
)
from apps.api.app.schemas.run import (
    RunCreate,
    RunResponse,
)
from apps.api.app.services.auth import (
    authenticate_agent,
    provision_agent_api_key,
    require_admin_key,
    write_security_audit_event,
)
from apps.api.app.services.idempotency import (
    calculate_request_hash,
)
from apps.api.app.services.policy_engine import (
    evaluate_action,
)
from apps.api.app.services.run_lifecycle import (
    set_run_status,
)
from apps.api.app.services.sandbox_executor import (
    SandboxExecutionError,
    execute_sandbox_action,
)


settings = get_settings()


app = FastAPI(
    title=settings.app_name,
    description=(
        "Agent-agnostic security assessment and control platform "
        "for AI agents."
    ),
    version=settings.app_version,
)


# -------------------------------------------------------------------
# ROUTERS
# -------------------------------------------------------------------

app.include_router(
    dashboard_router
)

app.include_router(
    security_tests_router
)


# -------------------------------------------------------------------
# HEALTH
# -------------------------------------------------------------------


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "neutron-controlforge-api",
        "version": settings.app_version,
        "environment": settings.environment,
    }


# -------------------------------------------------------------------
# AGENTS
# -------------------------------------------------------------------


@app.post(
    "/v1/agents",
    response_model=AgentCredentialResponse,
)
def create_agent(
    payload: AgentCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key),
):
    """
    Register an agent and provision its initial machine credential.

    The raw API key is returned only during provisioning. ControlForge
    stores only its one-way hash and a short identifying prefix.
    """

    agent = Agent(
        name=payload.name,
        description=payload.description,
    )

    db.add(agent)

    # Generate the agent ID before creating the associated audit event.
    db.flush()

    raw_api_key = (
        provision_agent_api_key(
            agent
        )
    )

    write_security_audit_event(
        db=db,
        event_type="AGENT_KEY_PROVISIONED",
        severity="INFO",
        message=(
            "Initial API credential provisioned for agent."
        ),
        agent_id=agent.id,
        event_data={
            "agent_name": agent.name,
            "credential_prefix": (
                agent.api_key_prefix
            ),
        },
    )

    db.commit()
    db.refresh(agent)

    return AgentCredentialResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        is_active=agent.is_active,
        api_key_prefix=agent.api_key_prefix,
        api_key=raw_api_key,
    )


@app.post(
    "/v1/agents/{agent_id}/rotate-key",
    response_model=AgentCredentialResponse,
)
def rotate_agent_api_key(
    agent_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key),
):
    """
    Replace an agent's current credential.

    Once committed, the previous API key becomes invalid immediately.
    """

    statement = (
        select(Agent)
        .where(
            Agent.id == agent_id
        )
        .with_for_update()
    )

    agent = db.scalar(
        statement
    )

    if agent is None:
        raise HTTPException(
            status_code=404,
            detail="Agent not found.",
        )

    previous_prefix = (
        agent.api_key_prefix
    )

    raw_api_key = (
        provision_agent_api_key(
            agent
        )
    )

    event_type = (
        "AGENT_KEY_ROTATED"
        if previous_prefix
        else "AGENT_KEY_PROVISIONED"
    )

    message = (
        "Agent API credential rotated."
        if previous_prefix
        else (
            "Initial API credential provisioned "
            "for existing agent."
        )
    )

    write_security_audit_event(
        db=db,
        event_type=event_type,
        severity="INFO",
        message=message,
        agent_id=agent.id,
        event_data={
            "agent_name": agent.name,
            "previous_credential_prefix": (
                previous_prefix
            ),
            "new_credential_prefix": (
                agent.api_key_prefix
            ),
        },
    )

    db.commit()
    db.refresh(agent)

    return AgentCredentialResponse(
        id=agent.id,
        name=agent.name,
        description=agent.description,
        is_active=agent.is_active,
        api_key_prefix=agent.api_key_prefix,
        api_key=raw_api_key,
    )


# -------------------------------------------------------------------
# RUNS
# -------------------------------------------------------------------


@app.post(
    "/v1/runs",
    response_model=RunResponse,
)
def create_run(
    payload: RunCreate,
    x_agent_key: str | None = Header(
        default=None,
        alias="X-Agent-Key",
    ),
    db: Session = Depends(get_db),
):
    """
    Start a new authenticated agent run.

    New runs begin in CREATED state.
    """

    authenticate_agent(
        db=db,
        agent_id=payload.agent_id,
        api_key=x_agent_key,
    )

    run = Run(
        agent_id=payload.agent_id,
        status="CREATED",
    )

    db.add(run)
    db.flush()

    db.add(
        Event(
            run_id=run.id,
            agent_id=payload.agent_id,
            event_type="RUN_CREATED",
            severity="INFO",
            message=(
                "Authenticated agent run created."
            ),
            event_data={
                "status": run.status,
                "authenticated": True,
            },
        )
    )

    db.commit()
    db.refresh(run)

    return run


@app.get(
    "/v1/runs/{run_id}",
    response_model=RunResponse,
)
def get_run(
    run_id: str,
    x_agent_key: str | None = Header(
        default=None,
        alias="X-Agent-Key",
    ),
    db: Session = Depends(get_db),
):
    """
    Return a run only to the agent that owns it.

    A valid credential for some other agent is not sufficient.
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

    authenticate_agent(
        db=db,
        agent_id=run.agent_id,
        api_key=x_agent_key,
    )

    return run


@app.get(
    "/v1/runs/{run_id}/events",
    response_model=list[EventResponse],
)
def get_run_events(
    run_id: str,
    x_agent_key: str | None = Header(
        default=None,
        alias="X-Agent-Key",
    ),
    db: Session = Depends(get_db),
):
    """
    Return run events only to the owning agent.

    This prevents cross-agent event and timeline disclosure.
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

    authenticate_agent(
        db=db,
        agent_id=run.agent_id,
        api_key=x_agent_key,
    )

    statement = (
        select(Event)
        .where(
            Event.run_id == run_id
        )
        .order_by(
            Event.created_at.asc()
        )
    )

    return db.scalars(
        statement
    ).all()


@app.post(
    "/v1/runs/{run_id}/complete",
    response_model=RunResponse,
)
def complete_run(
    run_id: str,
    x_agent_key: str | None = Header(
        default=None,
        alias="X-Agent-Key",
    ),
    db: Session = Depends(get_db),
):
    """
    Explicitly complete a run.

    ControlForge does not automatically mark a run complete when a
    single action finishes because one run may contain many actions.
    """

    statement = (
        select(Run)
        .where(
            Run.id == run_id
        )
        .with_for_update()
    )

    run = db.scalar(
        statement
    )

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="Run not found.",
        )

    authenticate_agent(
        db=db,
        agent_id=run.agent_id,
        api_key=x_agent_key,
    )

    if run.status == "COMPLETED":
        raise HTTPException(
            status_code=409,
            detail=(
                "Run has already been completed."
            ),
        )

    if run.status == "EXECUTING":
        raise HTTPException(
            status_code=409,
            detail=(
                "Run cannot be completed while "
                "an action is executing."
            ),
        )

    pending_approval_statement = (
        select(Approval)
        .where(
            Approval.run_id == run.id,
            Approval.status == "PENDING",
        )
    )

    pending_approval = db.scalar(
        pending_approval_statement
    )

    if pending_approval is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Run cannot be completed while "
                "an approval is pending."
            ),
        )

    set_run_status(
        db=db,
        run=run,
        status="COMPLETED",
        message=(
            "Agent run explicitly completed."
        ),
        event_data={
            "authenticated": True,
        },
    )

    db.commit()
    db.refresh(run)

    return run


# -------------------------------------------------------------------
# ACTION EVALUATION
# -------------------------------------------------------------------


@app.post(
    "/v1/actions/evaluate",
    response_model=ActionEvaluateResponse,
)
def evaluate_proposed_action(
    payload: ActionEvaluateRequest,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",
        min_length=1,
        max_length=255,
    ),
    x_agent_key: str | None = Header(
        default=None,
        alias="X-Agent-Key",
    ),
    db: Session = Depends(get_db),
):
    """
    Evaluate a proposed action from an authenticated agent.

    Policy outcome also updates the run lifecycle:
      ALLOW              -> ACTIVE
      REQUIRE_APPROVAL   -> WAITING_APPROVAL
      DENY               -> BLOCKED
    """

    authenticate_agent(
        db=db,
        agent_id=payload.agent_id,
        api_key=x_agent_key,
    )

    run_statement = (
        select(Run)
        .where(
            Run.id == payload.run_id
        )
        .with_for_update()
    )

    run = db.scalar(
        run_statement
    )

    if run is None:
        raise HTTPException(
            status_code=404,
            detail="Run not found.",
        )

    if (
        run.agent_id
        != payload.agent_id
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "Run does not belong to "
                "the authenticated agent."
            ),
        )

    if run.status == "COMPLETED":
        raise HTTPException(
            status_code=409,
            detail=(
                "Completed runs cannot accept "
                "new actions."
            ),
        )

    if run.status == "FAILED":
        raise HTTPException(
            status_code=409,
            detail=(
                "Failed runs cannot accept "
                "new actions."
            ),
        )

    request_payload = (
        payload.model_dump(
            mode="json"
        )
    )

    request_hash = (
        calculate_request_hash(
            request_payload
        )
    )

    # ----------------------------------------------------------------
    # IDEMPOTENCY
    # ----------------------------------------------------------------

    existing_statement = (
        select(
            IdempotencyRecord
        )
        .where(
            IdempotencyRecord.agent_id
            == payload.agent_id,
            IdempotencyRecord.idempotency_key
            == idempotency_key,
        )
    )

    existing_record = db.scalar(
        existing_statement
    )

    if existing_record is not None:
        if (
            existing_record.request_hash
            != request_hash
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Idempotency key has already been used "
                    "with a different request."
                ),
            )

        db.add(
            Event(
                run_id=payload.run_id,
                agent_id=payload.agent_id,
                event_type="IDEMPOTENCY_REPLAYED",
                severity="INFO",
                message=(
                    "Duplicate authenticated action evaluation "
                    "request detected. Original result returned."
                ),
                event_data={
                    "idempotency_key": (
                        idempotency_key
                    ),
                    "request_hash": (
                        request_hash
                    ),
                    "action_id": (
                        existing_record
                        .response_data
                        .get(
                            "action_id"
                        )
                    ),
                },
            )
        )

        db.commit()

        return (
            ActionEvaluateResponse
            .model_validate(
                existing_record
                .response_data
            )
        )

    provenance = (
        payload.provenance
        .model_dump()
    )

    # ----------------------------------------------------------------
    # ACTION
    # ----------------------------------------------------------------

    action = Action(
        agent_id=payload.agent_id,
        run_id=payload.run_id,
        action_name=payload.action,
        resource=payload.resource,
        arguments=payload.arguments,
        provenance=provenance,
    )

    db.add(action)
    db.flush()

    # ----------------------------------------------------------------
    # POLICY
    # ----------------------------------------------------------------

    result = evaluate_action(
        action=payload.action,
        arguments=payload.arguments,
        provenance=provenance,
    )

    decision = Decision(
        action_id=action.id,
        decision=(
            result.decision.value
        ),
        risk=result.risk.value,
        reason=result.reason,
        policy=result.policy,
    )

    db.add(decision)
    db.flush()

    # ----------------------------------------------------------------
    # EXECUTION GATE
    # ----------------------------------------------------------------

    approval = None

    if (
        result.decision
        == DecisionType.ALLOW
    ):
        execution_status = "READY"

    elif (
        result.decision
        == DecisionType.REQUIRE_APPROVAL
    ):
        execution_status = (
            "BLOCKED_APPROVAL"
        )

    else:
        execution_status = (
            "BLOCKED_DENY"
        )

    execution = Execution(
        action_id=action.id,
        run_id=payload.run_id,
        agent_id=payload.agent_id,
        status=execution_status,
        executor="sandbox",
        created_at=(
            datetime.now(
                timezone.utc
            )
        ),
    )

    db.add(execution)
    db.flush()

    # ----------------------------------------------------------------
    # APPROVAL
    # ----------------------------------------------------------------

    if (
        result.decision
        == DecisionType.REQUIRE_APPROVAL
    ):
        approval = Approval(
            action_id=action.id,
            run_id=payload.run_id,
            agent_id=payload.agent_id,
            status="PENDING",
            reason=result.reason,
        )

        db.add(approval)
        db.flush()

        db.add(
            Event(
                run_id=payload.run_id,
                agent_id=payload.agent_id,
                event_type="APPROVAL_REQUESTED",
                severity=result.risk.value,
                message=(
                    "Human approval required for action "
                    f"'{payload.action}'."
                ),
                event_data={
                    "approval_id": (
                        approval.id
                    ),
                    "action_id": (
                        action.id
                    ),
                    "execution_id": (
                        execution.id
                    ),
                    "reason": (
                        result.reason
                    ),
                    "policy": (
                        result.policy
                    ),
                },
            )
        )

    # ----------------------------------------------------------------
    # RUN LIFECYCLE
    # ----------------------------------------------------------------

    if (
        result.decision
        == DecisionType.ALLOW
    ):
        set_run_status(
            db=db,
            run=run,
            status="ACTIVE",
            message=(
                "Run became active after "
                "an action was allowed."
            ),
            event_data={
                "action_id": action.id,
                "decision": (
                    result.decision.value
                ),
            },
        )

    elif (
        result.decision
        == DecisionType.REQUIRE_APPROVAL
    ):
        set_run_status(
            db=db,
            run=run,
            status="WAITING_APPROVAL",
            message=(
                "Run is waiting for human approval."
            ),
            event_data={
                "action_id": action.id,
                "approval_id": (
                    approval.id
                    if approval
                    else None
                ),
                "decision": (
                    result.decision.value
                ),
            },
        )

    else:
        set_run_status(
            db=db,
            run=run,
            status="BLOCKED",
            message=(
                "Run was blocked by policy."
            ),
            event_data={
                "action_id": action.id,
                "decision": (
                    result.decision.value
                ),
                "policy": (
                    result.policy
                ),
            },
        )

    # ----------------------------------------------------------------
    # ACTION AUDIT EVENT
    # ----------------------------------------------------------------

    db.add(
        Event(
            run_id=payload.run_id,
            agent_id=payload.agent_id,
            event_type="ACTION_EVALUATED",
            severity=result.risk.value,
            message=(
                f"Authenticated action '{payload.action}' "
                f"evaluated as {result.decision.value}."
            ),
            event_data={
                "action_id": (
                    action.id
                ),
                "decision_id": (
                    decision.id
                ),
                "execution_id": (
                    execution.id
                ),
                "approval_id": (
                    approval.id
                    if approval is not None
                    else None
                ),
                "action": (
                    payload.action
                ),
                "resource": (
                    payload.resource
                ),
                "decision": (
                    result.decision.value
                ),
                "risk": (
                    result.risk.value
                ),
                "policy": (
                    result.policy
                ),
                "reason": (
                    result.reason
                ),
                "execution_status": (
                    execution.status
                ),
                "run_status": (
                    run.status
                ),
                "provenance": (
                    provenance
                ),
                "idempotency_key": (
                    idempotency_key
                ),
                "authenticated": True,
            },
        )
    )

    # ----------------------------------------------------------------
    # RESPONSE
    # ----------------------------------------------------------------

    response = (
        ActionEvaluateResponse(
            action_id=action.id,
            decision_id=decision.id,
            execution_id=(
                execution.id
            ),
            approval_id=(
                approval.id
                if approval is not None
                else None
            ),
            decision=(
                result.decision
            ),
            risk=result.risk,
            reason=result.reason,
            policy=result.policy,
        )
    )

    # ----------------------------------------------------------------
    # IDEMPOTENCY RECORD
    # ----------------------------------------------------------------

    db.add(
        IdempotencyRecord(
            agent_id=(
                payload.agent_id
            ),
            idempotency_key=(
                idempotency_key
            ),
            request_hash=(
                request_hash
            ),
            response_data=(
                response.model_dump(
                    mode="json"
                )
            ),
        )
    )

    db.commit()

    return response


# -------------------------------------------------------------------
# ACTION EXECUTION
# -------------------------------------------------------------------


@app.get(
    "/v1/actions/{action_id}/execution",
    response_model=ExecutionResponse,
)
def get_action_execution(
    action_id: str,
    x_agent_key: str | None = Header(
        default=None,
        alias="X-Agent-Key",
    ),
    db: Session = Depends(get_db),
):
    statement = (
        select(Execution)
        .where(
            Execution.action_id
            == action_id
        )
    )

    execution = db.scalar(
        statement
    )

    if execution is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Execution record not found."
            ),
        )

    authenticate_agent(
        db=db,
        agent_id=execution.agent_id,
        api_key=x_agent_key,
    )

    db.commit()

    return execution


@app.post(
    "/v1/actions/{action_id}/execute",
    response_model=ExecutionResponse,
)
def execute_action(
    action_id: str,
    x_agent_key: str | None = Header(
        default=None,
        alias="X-Agent-Key",
    ),
    db: Session = Depends(get_db),
):
    """
    Execute an authorized action.

    Run lifecycle:
      READY -> EXECUTING -> ACTIVE
                        or FAILED
    """

    action = db.get(
        Action,
        action_id,
    )

    if action is None:
        raise HTTPException(
            status_code=404,
            detail="Action not found.",
        )

    authenticate_agent(
        db=db,
        agent_id=action.agent_id,
        api_key=x_agent_key,
    )

    execution_statement = (
        select(Execution)
        .where(
            Execution.action_id
            == action_id
        )
        .with_for_update()
    )

    execution = db.scalar(
        execution_statement
    )

    if execution is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Execution record not found."
            ),
        )

    run_statement = (
        select(Run)
        .where(
            Run.id == execution.run_id
        )
        .with_for_update()
    )

    run = db.scalar(
        run_statement
    )

    if run is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "Run state is missing for "
                "this execution."
            ),
        )

    if (
        execution.agent_id
        != action.agent_id
    ):
        raise HTTPException(
            status_code=500,
            detail=(
                "Execution ownership does not "
                "match action ownership."
            ),
        )

    if run.status == "COMPLETED":
        raise HTTPException(
            status_code=409,
            detail=(
                "Actions cannot execute after "
                "the run has completed."
            ),
        )

    if (
        execution.status
        == "BLOCKED_APPROVAL"
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Action is waiting for human approval."
            ),
        )

    if execution.status in {
        "BLOCKED_DENY",
        "DENIED",
    }:
        raise HTTPException(
            status_code=403,
            detail=(
                "Action is not authorized for execution."
            ),
        )

    if (
        execution.status
        == "EXECUTED"
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Action has already been executed."
            ),
        )

    if (
        execution.status
        == "EXECUTING"
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Action execution is already in progress."
            ),
        )

    if (
        execution.status
        == "FAILED"
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Action previously failed. "
                "Automatic retry is not enabled."
            ),
        )

    if (
        execution.status
        != "READY"
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Action cannot execute from status "
                f"{execution.status}."
            ),
        )

    # ----------------------------------------------------------------
    # EXECUTION START
    # ----------------------------------------------------------------

    execution.status = (
        "EXECUTING"
    )

    set_run_status(
        db=db,
        run=run,
        status="EXECUTING",
        message=(
            "Run entered execution state."
        ),
        event_data={
            "action_id": action.id,
            "execution_id": (
                execution.id
            ),
        },
    )

    db.add(
        Event(
            run_id=(
                execution.run_id
            ),
            agent_id=(
                execution.agent_id
            ),
            event_type="EXECUTION_STARTED",
            severity="INFO",
            message=(
                "Authenticated sandbox execution started "
                f"for '{action.action_name}'."
            ),
            event_data={
                "action_id": (
                    action.id
                ),
                "execution_id": (
                    execution.id
                ),
                "executor": (
                    execution.executor
                ),
                "authenticated": True,
            },
        )
    )

    # Commit EXECUTING before the sandbox operation so a second
    # request cannot start the same action concurrently.
    db.commit()

    try:
        result = (
            execute_sandbox_action(
                action=(
                    action.action_name
                ),
                resource=(
                    action.resource
                ),
                arguments=(
                    action.arguments
                ),
            )
        )

    except SandboxExecutionError as exc:
        execution.status = (
            "FAILED"
        )

        execution.error_message = (
            str(exc)
        )

        execution.executed_at = (
            datetime.now(
                timezone.utc
            )
        )

        set_run_status(
            db=db,
            run=run,
            status="FAILED",
            message=(
                "Run failed during action execution."
            ),
            event_data={
                "action_id": (
                    action.id
                ),
                "execution_id": (
                    execution.id
                ),
                "error": (
                    str(exc)
                ),
            },
        )

        db.add(
            Event(
                run_id=(
                    execution.run_id
                ),
                agent_id=(
                    execution.agent_id
                ),
                event_type="EXECUTION_FAILED",
                severity="HIGH",
                message=(
                    "Sandbox execution failed for "
                    f"'{action.action_name}'."
                ),
                event_data={
                    "action_id": (
                        action.id
                    ),
                    "execution_id": (
                        execution.id
                    ),
                    "error": (
                        str(exc)
                    ),
                },
            )
        )

        db.commit()
        db.refresh(
            execution
        )

        return execution

    # ----------------------------------------------------------------
    # EXECUTION SUCCESS
    # ----------------------------------------------------------------

    execution.status = (
        "EXECUTED"
    )

    execution.result = (
        result
    )

    execution.error_message = (
        None
    )

    execution.executed_at = (
        datetime.now(
            timezone.utc
        )
    )

    set_run_status(
        db=db,
        run=run,
        status="ACTIVE",
        message=(
            "Run returned to active state "
            "after successful execution."
        ),
        event_data={
            "action_id": (
                action.id
            ),
            "execution_id": (
                execution.id
            ),
        },
    )

    db.add(
        Event(
            run_id=(
                execution.run_id
            ),
            agent_id=(
                execution.agent_id
            ),
            event_type="EXECUTION_COMPLETED",
            severity="INFO",
            message=(
                "Sandbox execution completed for "
                f"'{action.action_name}'."
            ),
            event_data={
                "action_id": (
                    action.id
                ),
                "execution_id": (
                    execution.id
                ),
                "result": result,
            },
        )
    )

    db.commit()
    db.refresh(
        execution
    )

    return execution


# -------------------------------------------------------------------
# APPROVALS
# -------------------------------------------------------------------


@app.get(
    "/v1/approvals",
    response_model=list[ApprovalResponse],
)
def get_pending_approvals(
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key),
):
    statement = (
        select(Approval)
        .where(
            Approval.status
            == "PENDING"
        )
        .order_by(
            Approval.created_at.asc()
        )
    )

    return db.scalars(
        statement
    ).all()


@app.get(
    "/v1/approvals/{approval_id}",
    response_model=ApprovalResponse,
)
def get_approval(
    approval_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key),
):
    approval = db.get(
        Approval,
        approval_id,
    )

    if approval is None:
        raise HTTPException(
            status_code=404,
            detail="Approval not found.",
        )

    return approval


@app.post(
    "/v1/approvals/{approval_id}/approve",
    response_model=ApprovalResponse,
)
def approve_action(
    approval_id: str,
    payload: ApprovalResolveRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key),
):
    """
    Approve a restricted action.

    Approval changes:
      Execution BLOCKED_APPROVAL -> READY
      Run WAITING_APPROVAL       -> ACTIVE
    """

    approval_statement = (
        select(Approval)
        .where(
            Approval.id
            == approval_id
        )
        .with_for_update()
    )

    approval = db.scalar(
        approval_statement
    )

    if approval is None:
        raise HTTPException(
            status_code=404,
            detail="Approval not found.",
        )

    if (
        approval.status
        != "PENDING"
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Approval has already been resolved as "
                f"{approval.status}."
            ),
        )

    execution_statement = (
        select(Execution)
        .where(
            Execution.action_id
            == approval.action_id
        )
        .with_for_update()
    )

    execution = db.scalar(
        execution_statement
    )

    if execution is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "Execution state is missing "
                "for this action."
            ),
        )

    if (
        execution.status
        != "BLOCKED_APPROVAL"
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Execution is not awaiting approval. "
                f"Current status: {execution.status}."
            ),
        )

    run_statement = (
        select(Run)
        .where(
            Run.id == approval.run_id
        )
        .with_for_update()
    )

    run = db.scalar(
        run_statement
    )

    if run is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "Run state is missing "
                "for this approval."
            ),
        )

    if run.status == "COMPLETED":
        raise HTTPException(
            status_code=409,
            detail=(
                "Approval cannot be resolved after "
                "the run has completed."
            ),
        )

    approval.status = (
        "APPROVED"
    )

    approval.resolved_at = (
        datetime.now(
            timezone.utc
        )
    )

    approval.resolved_by = (
        payload.resolved_by
    )

    approval.resolution_note = (
        payload.note
    )

    execution.status = (
        "READY"
    )

    set_run_status(
        db=db,
        run=run,
        status="ACTIVE",
        message=(
            "Run resumed after human approval."
        ),
        event_data={
            "approval_id": (
                approval.id
            ),
            "action_id": (
                approval.action_id
            ),
            "execution_id": (
                execution.id
            ),
        },
    )

    db.add(
        Event(
            run_id=(
                approval.run_id
            ),
            agent_id=(
                approval.agent_id
            ),
            event_type="APPROVAL_RESOLVED",
            severity="INFO",
            message=(
                "Pending action approved by "
                "authenticated control-plane reviewer."
            ),
            event_data={
                "approval_id": (
                    approval.id
                ),
                "action_id": (
                    approval.action_id
                ),
                "execution_id": (
                    execution.id
                ),
                "status": (
                    approval.status
                ),
                "execution_status": (
                    execution.status
                ),
                "run_status": (
                    run.status
                ),
                "resolved_by": (
                    payload.resolved_by
                ),
                "note": (
                    payload.note
                ),
                "admin_authenticated": True,
            },
        )
    )

    db.commit()
    db.refresh(
        approval
    )

    return approval


@app.post(
    "/v1/approvals/{approval_id}/deny",
    response_model=ApprovalResponse,
)
def deny_action(
    approval_id: str,
    payload: ApprovalResolveRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_key),
):
    """
    Deny an approval request.

    Approval denial:
      Execution BLOCKED_APPROVAL -> DENIED
      Run WAITING_APPROVAL       -> BLOCKED
    """

    approval_statement = (
        select(Approval)
        .where(
            Approval.id
            == approval_id
        )
        .with_for_update()
    )

    approval = db.scalar(
        approval_statement
    )

    if approval is None:
        raise HTTPException(
            status_code=404,
            detail="Approval not found.",
        )

    if (
        approval.status
        != "PENDING"
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Approval has already been resolved as "
                f"{approval.status}."
            ),
        )

    execution_statement = (
        select(Execution)
        .where(
            Execution.action_id
            == approval.action_id
        )
        .with_for_update()
    )

    execution = db.scalar(
        execution_statement
    )

    if execution is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "Execution state is missing "
                "for this action."
            ),
        )

    if (
        execution.status
        != "BLOCKED_APPROVAL"
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Execution is not awaiting approval. "
                f"Current status: {execution.status}."
            ),
        )

    run_statement = (
        select(Run)
        .where(
            Run.id == approval.run_id
        )
        .with_for_update()
    )

    run = db.scalar(
        run_statement
    )

    if run is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "Run state is missing "
                "for this approval."
            ),
        )

    if run.status == "COMPLETED":
        raise HTTPException(
            status_code=409,
            detail=(
                "Approval cannot be resolved after "
                "the run has completed."
            ),
        )

    approval.status = (
        "DENIED"
    )

    approval.resolved_at = (
        datetime.now(
            timezone.utc
        )
    )

    approval.resolved_by = (
        payload.resolved_by
    )

    approval.resolution_note = (
        payload.note
    )

    execution.status = (
        "DENIED"
    )

    set_run_status(
        db=db,
        run=run,
        status="BLOCKED",
        message=(
            "Run was blocked after human reviewer "
            "denied the pending action."
        ),
        event_data={
            "approval_id": (
                approval.id
            ),
            "action_id": (
                approval.action_id
            ),
            "execution_id": (
                execution.id
            ),
        },
    )

    db.add(
        Event(
            run_id=(
                approval.run_id
            ),
            agent_id=(
                approval.agent_id
            ),
            event_type="APPROVAL_RESOLVED",
            severity="INFO",
            message=(
                "Pending action denied by "
                "authenticated control-plane reviewer."
            ),
            event_data={
                "approval_id": (
                    approval.id
                ),
                "action_id": (
                    approval.action_id
                ),
                "execution_id": (
                    execution.id
                ),
                "status": (
                    approval.status
                ),
                "execution_status": (
                    execution.status
                ),
                "run_status": (
                    run.status
                ),
                "resolved_by": (
                    payload.resolved_by
                ),
                "note": (
                    payload.note
                ),
                "admin_authenticated": True,
            },
        )
    )

    db.commit()
    db.refresh(
        approval
    )

    return approval
