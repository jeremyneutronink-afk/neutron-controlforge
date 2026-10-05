import secrets
import uuid
from dataclasses import dataclass
from typing import Any, Callable

import httpx
from sqlalchemy import delete
from sqlalchemy.orm import Session

from apps.api.app.core.config import get_settings
from apps.api.app.models import (
    Agent,
    Event,
    Run,
    SecurityAuditEvent,
    SystemSecurityTestResult,
)
from apps.api.app.services.auth import (
    provision_agent_api_key,
)


@dataclass(frozen=True)
class SystemTestDefinition:
    key: str
    name: str
    category: str
    description: str
    severity: str
    expected_outcome: str


SYSTEM_TESTS = {
    "missing-agent-key": SystemTestDefinition(
        key="missing-agent-key",
        name="Missing Agent Credential",
        category="Authentication",
        description=(
            "Attempts to create an agent run without "
            "providing X-Agent-Key."
        ),
        severity="HIGH",
        expected_outcome="HTTP_401",
    ),

    "invalid-agent-key": SystemTestDefinition(
        key="invalid-agent-key",
        name="Invalid Agent Credential",
        category="Authentication",
        description=(
            "Attempts to create an agent run using "
            "an invalid machine credential."
        ),
        severity="HIGH",
        expected_outcome="HTTP_401",
    ),

    "cross-agent-impersonation": SystemTestDefinition(
        key="cross-agent-impersonation",
        name="Cross-Agent Impersonation",
        category="Authorization",
        description=(
            "Attempts to authenticate as one agent "
            "using another agent's valid credential."
        ),
        severity="CRITICAL",
        expected_outcome="HTTP_401",
    ),

    "idempotency-conflict": SystemTestDefinition(
        key="idempotency-conflict",
        name="Idempotency Payload Conflict",
        category="Replay Protection",
        description=(
            "Reuses an idempotency key with a modified "
            "payload and verifies that ControlForge rejects it."
        ),
        severity="HIGH",
        expected_outcome="HTTP_409",
    ),

    "approval-bypass": SystemTestDefinition(
        key="approval-bypass",
        name="Approval Gate Bypass",
        category="Approval Enforcement",
        description=(
            "Attempts to execute a restricted action "
            "before human approval is granted."
        ),
        severity="CRITICAL",
        expected_outcome="HTTP_409",
    ),

    "cross-agent-run-access": SystemTestDefinition(
        key="cross-agent-run-access",
        name="Cross-Agent Run Access",
        category="Tenant Isolation",
        description=(
            "Creates a run owned by a separate temporary agent, "
            "then attempts to read it using the selected agent's "
            "credential."
        ),
        severity="CRITICAL",
        expected_outcome="HTTP_401",
    ),

    "completed-run-mutation": SystemTestDefinition(
        key="completed-run-mutation",
        name="Completed Run Mutation",
        category="Lifecycle Enforcement",
        description=(
            "Completes a run and then attempts to submit another "
            "action into that closed run."
        ),
        severity="HIGH",
        expected_outcome="HTTP_409",
    ),

    "approval-without-admin": SystemTestDefinition(
        key="approval-without-admin",
        name="Approval Resolution Without Admin Auth",
        category="Administrative Authorization",
        description=(
            "Attempts to approve a restricted action without "
            "supplying the control-plane administrator credential."
        ),
        severity="CRITICAL",
        expected_outcome="HTTP_401",
    ),

    "execute-denied-action": SystemTestDefinition(
        key="execute-denied-action",
        name="Execute Policy-Denied Action",
        category="Execution Enforcement",
        description=(
            "Attempts to execute an action after policy has already "
            "denied authorization."
        ),
        severity="CRITICAL",
        expected_outcome="HTTP_403",
    ),

    "old-key-after-rotation": SystemTestDefinition(
        key="old-key-after-rotation",
        name="Old Credential After Rotation",
        category="Credential Lifecycle",
        description=(
            "Rotates a temporary agent credential and verifies that "
            "the previously valid credential is rejected immediately."
        ),
        severity="CRITICAL",
        expected_outcome="HTTP_401",
    ),
}


def list_system_tests():
    return list(
        SYSTEM_TESTS.values()
    )


def _safe_response(
    response: httpx.Response,
) -> dict[str, Any]:
    try:
        body = response.json()
    except Exception:
        body = {
            "body":
                response.text[:1000]
        }

    return {
        "status_code":
            response.status_code,
        "response":
            body,
    }


def _outcome(
    status_code: int,
) -> str:
    return (
        f"HTTP_{status_code}"
    )


def _post(
    client: httpx.Client,
    path: str,
    *,
    headers: dict[str, str] | None = None,
    json: dict | None = None,
) -> httpx.Response:
    return client.post(
        path,
        headers=headers,
        json=json,
    )


def _get(
    client: httpx.Client,
    path: str,
    *,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    return client.get(
        path,
        headers=headers,
    )


def _create_run(
    *,
    client: httpx.Client,
    agent_id: str,
    agent_key: str,
) -> httpx.Response:
    return _post(
        client,
        "/v1/runs",
        headers={
            "X-Agent-Key":
                agent_key,
        },
        json={
            "agent_id":
                agent_id,
        },
    )


def _complete_run(
    *,
    client: httpx.Client,
    run_id: str,
    agent_key: str,
) -> None:
    try:
        _post(
            client,
            (
                f"/v1/runs/"
                f"{run_id}/complete"
            ),
            headers={
                "X-Agent-Key":
                    agent_key,
            },
        )

    except Exception:
        pass


def _cleanup_temporary_agent(
    *,
    db: Session,
    agent_id: str,
    run_id: str | None = None,
) -> None:
    try:
        if run_id:
            db.execute(
                delete(Event).where(
                    Event.run_id
                    == run_id
                )
            )

            db.execute(
                delete(Run).where(
                    Run.id
                    == run_id
                )
            )

        db.execute(
            delete(
                SecurityAuditEvent
            ).where(
                SecurityAuditEvent
                .agent_id
                == agent_id
            )
        )

        db.execute(
            delete(Agent).where(
                Agent.id
                == agent_id
            )
        )

        db.commit()

    except Exception:
        db.rollback()


def _create_temporary_agent(
    *,
    db: Session,
    name: str,
) -> tuple[str, str]:
    temporary_agent = Agent(
        name=name,
        description=(
            "Temporary identity created by "
            "ControlForge system test harness."
        ),
    )

    db.add(
        temporary_agent
    )

    db.flush()

    raw_key = (
        provision_agent_api_key(
            temporary_agent
        )
    )

    agent_id = (
        temporary_agent.id
    )

    db.commit()

    return (
        agent_id,
        raw_key,
    )


def _test_missing_agent_key(
    *,
    client: httpx.Client,
    db: Session,
    agent: Agent,
    agent_key: str,
) -> tuple[str, dict]:
    response = _post(
        client,
        "/v1/runs",
        json={
            "agent_id":
                agent.id,
        },
    )

    return (
        _outcome(
            response.status_code
        ),
        {
            "request": {
                "method":
                    "POST",
                "path":
                    "/v1/runs",
                "credential_supplied":
                    False,
            },
            **_safe_response(
                response
            ),
        },
    )


def _test_invalid_agent_key(
    *,
    client: httpx.Client,
    db: Session,
    agent: Agent,
    agent_key: str,
) -> tuple[str, dict]:
    invalid_key = (
        "agk_"
        + secrets.token_urlsafe(
            24
        )
    )

    response = _post(
        client,
        "/v1/runs",
        headers={
            "X-Agent-Key":
                invalid_key,
        },
        json={
            "agent_id":
                agent.id,
        },
    )

    return (
        _outcome(
            response.status_code
        ),
        {
            "request": {
                "method":
                    "POST",
                "path":
                    "/v1/runs",
                "credential_supplied":
                    True,
                "credential_valid":
                    False,
            },
            **_safe_response(
                response
            ),
        },
    )


def _test_cross_agent_impersonation(
    *,
    client: httpx.Client,
    db: Session,
    agent: Agent,
    agent_key: str,
) -> tuple[str, dict]:
    temporary_agent_id = None

    try:
        (
            temporary_agent_id,
            _temporary_key,
        ) = _create_temporary_agent(
            db=db,
            name=(
                "System Test "
                "Impersonation Target"
            ),
        )

        response = _post(
            client,
            "/v1/runs",
            headers={
                "X-Agent-Key":
                    agent_key,
            },
            json={
                "agent_id":
                    temporary_agent_id,
            },
        )

        return (
            _outcome(
                response.status_code
            ),
            {
                "request": {
                    "method":
                        "POST",
                    "path":
                        "/v1/runs",
                    "credential_owner_agent_id":
                        agent.id,
                    "claimed_agent_id":
                        temporary_agent_id,
                },
                **_safe_response(
                    response
                ),
            },
        )

    finally:
        if temporary_agent_id:
            _cleanup_temporary_agent(
                db=db,
                agent_id=(
                    temporary_agent_id
                ),
            )


def _test_idempotency_conflict(
    *,
    client: httpx.Client,
    db: Session,
    agent: Agent,
    agent_key: str,
) -> tuple[str, dict]:
    run_response = _create_run(
        client=client,
        agent_id=agent.id,
        agent_key=agent_key,
    )

    if (
        run_response.status_code
        != 200
    ):
        return (
            _outcome(
                run_response.status_code
            ),
            {
                "stage":
                    "create_run",
                **_safe_response(
                    run_response
                ),
            },
        )

    run_id = (
        run_response.json()[
            "id"
        ]
    )

    idem_key = (
        "system-test-"
        + str(
            uuid.uuid4()
        )
    )

    first_payload = {
        "agent_id":
            agent.id,
        "run_id":
            run_id,
        "action":
            "issue_refund",
        "resource":
            "customer/system-test",
        "arguments": {
            "amount":
                100,
        },
        "provenance": {
            "source":
                "system_test",
            "trust":
                "trusted_internal",
        },
    }

    second_payload = {
        **first_payload,
        "arguments": {
            "amount":
                200,
        },
    }

    first_response = _post(
        client,
        "/v1/actions/evaluate",
        headers={
            "X-Agent-Key":
                agent_key,
            "Idempotency-Key":
                idem_key,
        },
        json=first_payload,
    )

    if (
        first_response.status_code
        != 200
    ):
        return (
            _outcome(
                first_response.status_code
            ),
            {
                "stage":
                    "initial_request",
                "run_id":
                    run_id,
                **_safe_response(
                    first_response
                ),
            },
        )

    first_result = (
        first_response.json()
    )

    second_response = _post(
        client,
        "/v1/actions/evaluate",
        headers={
            "X-Agent-Key":
                agent_key,
            "Idempotency-Key":
                idem_key,
        },
        json=second_payload,
    )

    action_id = (
        first_result.get(
            "action_id"
        )
    )

    if action_id:
        try:
            _post(
                client,
                (
                    f"/v1/actions/"
                    f"{action_id}/execute"
                ),
                headers={
                    "X-Agent-Key":
                        agent_key,
                },
            )

        except Exception:
            pass

    _complete_run(
        client=client,
        run_id=run_id,
        agent_key=agent_key,
    )

    return (
        _outcome(
            second_response.status_code
        ),
        {
            "run_id":
                run_id,
            "request": {
                "idempotency_key_reused":
                    True,
                "payload_changed":
                    True,
            },
            "initial_status":
                first_response.status_code,
            **_safe_response(
                second_response
            ),
        },
    )


def _test_approval_bypass(
    *,
    client: httpx.Client,
    db: Session,
    agent: Agent,
    agent_key: str,
) -> tuple[str, dict]:
    settings = get_settings()

    run_response = _create_run(
        client=client,
        agent_id=agent.id,
        agent_key=agent_key,
    )

    if (
        run_response.status_code
        != 200
    ):
        return (
            _outcome(
                run_response.status_code
            ),
            {
                "stage":
                    "create_run",
                **_safe_response(
                    run_response
                ),
            },
        )

    run_id = (
        run_response.json()[
            "id"
        ]
    )

    evaluation = _post(
        client,
        "/v1/actions/evaluate",
        headers={
            "X-Agent-Key":
                agent_key,
            "Idempotency-Key":
                (
                    "system-test-"
                    + str(
                        uuid.uuid4()
                    )
                ),
        },
        json={
            "agent_id":
                agent.id,
            "run_id":
                run_id,
            "action":
                "issue_refund",
            "resource":
                "customer/system-test",
            "arguments": {
                "amount":
                    780,
            },
            "provenance": {
                "source":
                    "system_test",
                "trust":
                    "trusted_internal",
            },
        },
    )

    if (
        evaluation.status_code
        != 200
    ):
        return (
            _outcome(
                evaluation.status_code
            ),
            {
                "stage":
                    "evaluation",
                "run_id":
                    run_id,
                **_safe_response(
                    evaluation
                ),
            },
        )

    body = (
        evaluation.json()
    )

    action_id = (
        body["action_id"]
    )

    approval_id = (
        body.get(
            "approval_id"
        )
    )

    bypass_response = _post(
        client,
        (
            f"/v1/actions/"
            f"{action_id}/execute"
        ),
        headers={
            "X-Agent-Key":
                agent_key,
        },
    )

    if approval_id:
        try:
            _post(
                client,
                (
                    f"/v1/approvals/"
                    f"{approval_id}/deny"
                ),
                headers={
                    "X-Admin-Key":
                        settings
                        .agentguard_admin_key,
                    "Content-Type":
                        "application/json",
                },
                json={
                    "resolved_by":
                        "system-test-harness",
                    "note": (
                        "Automatic cleanup after "
                        "approval-bypass test."
                    ),
                },
            )

            _complete_run(
                client=client,
                run_id=run_id,
                agent_key=agent_key,
            )

        except Exception:
            pass

    return (
        _outcome(
            bypass_response.status_code
        ),
        {
            "run_id":
                run_id,
            "action_id":
                action_id,
            "approval_id":
                approval_id,
            "request": {
                "attempted_execution_before_approval":
                    True,
            },
            **_safe_response(
                bypass_response
            ),
        },
    )


def _test_cross_agent_run_access(
    *,
    client: httpx.Client,
    db: Session,
    agent: Agent,
    agent_key: str,
) -> tuple[str, dict]:
    temporary_agent_id = None
    temporary_run_id = None

    try:
        (
            temporary_agent_id,
            temporary_key,
        ) = _create_temporary_agent(
            db=db,
            name=(
                "System Test "
                "Cross-Agent Target"
            ),
        )

        create_response = (
            _create_run(
                client=client,
                agent_id=(
                    temporary_agent_id
                ),
                agent_key=(
                    temporary_key
                ),
            )
        )

        if (
            create_response.status_code
            != 200
        ):
            return (
                _outcome(
                    create_response
                    .status_code
                ),
                {
                    "stage":
                        "create_target_run",
                    **_safe_response(
                        create_response
                    ),
                },
            )

        temporary_run_id = (
            create_response.json()[
                "id"
            ]
        )

        attack_response = _get(
            client,
            (
                f"/v1/runs/"
                f"{temporary_run_id}"
            ),
            headers={
                "X-Agent-Key":
                    agent_key,
            },
        )

        return (
            _outcome(
                attack_response
                .status_code
            ),
            {
                "target_run_id":
                    temporary_run_id,
                "target_agent_id":
                    temporary_agent_id,
                "attacker_agent_id":
                    agent.id,
                "request": {
                    "method":
                        "GET",
                    "cross_agent_access":
                        True,
                },
                **_safe_response(
                    attack_response
                ),
            },
        )

    finally:
        if temporary_agent_id:
            _cleanup_temporary_agent(
                db=db,
                agent_id=(
                    temporary_agent_id
                ),
                run_id=(
                    temporary_run_id
                ),
            )


def _test_completed_run_mutation(
    *,
    client: httpx.Client,
    db: Session,
    agent: Agent,
    agent_key: str,
) -> tuple[str, dict]:
    run_response = _create_run(
        client=client,
        agent_id=agent.id,
        agent_key=agent_key,
    )

    if (
        run_response.status_code
        != 200
    ):
        return (
            _outcome(
                run_response.status_code
            ),
            {
                "stage":
                    "create_run",
                **_safe_response(
                    run_response
                ),
            },
        )

    run_id = (
        run_response.json()[
            "id"
        ]
    )

    complete_response = _post(
        client,
        (
            f"/v1/runs/"
            f"{run_id}/complete"
        ),
        headers={
            "X-Agent-Key":
                agent_key,
        },
    )

    if (
        complete_response.status_code
        != 200
    ):
        return (
            _outcome(
                complete_response
                .status_code
            ),
            {
                "stage":
                    "complete_run",
                "run_id":
                    run_id,
                **_safe_response(
                    complete_response
                ),
            },
        )

    mutation_response = _post(
        client,
        "/v1/actions/evaluate",
        headers={
            "X-Agent-Key":
                agent_key,
            "Idempotency-Key":
                (
                    "system-test-"
                    + str(
                        uuid.uuid4()
                    )
                ),
        },
        json={
            "agent_id":
                agent.id,
            "run_id":
                run_id,
            "action":
                "read_customer",
            "resource":
                "customer/system-test",
            "arguments": {},
            "provenance": {
                "source":
                    "system_test",
                "trust":
                    "trusted_internal",
            },
        },
    )

    return (
        _outcome(
            mutation_response.status_code
        ),
        {
            "run_id":
                run_id,
            "run_completed":
                True,
            "mutation_attempted":
                True,
            **_safe_response(
                mutation_response
            ),
        },
    )


def _test_approval_without_admin(
    *,
    client: httpx.Client,
    db: Session,
    agent: Agent,
    agent_key: str,
) -> tuple[str, dict]:
    settings = get_settings()

    run_response = _create_run(
        client=client,
        agent_id=agent.id,
        agent_key=agent_key,
    )

    if (
        run_response.status_code
        != 200
    ):
        return (
            _outcome(
                run_response.status_code
            ),
            {
                "stage":
                    "create_run",
                **_safe_response(
                    run_response
                ),
            },
        )

    run_id = (
        run_response.json()[
            "id"
        ]
    )

    evaluation = _post(
        client,
        "/v1/actions/evaluate",
        headers={
            "X-Agent-Key":
                agent_key,
            "Idempotency-Key":
                (
                    "system-test-"
                    + str(
                        uuid.uuid4()
                    )
                ),
        },
        json={
            "agent_id":
                agent.id,
            "run_id":
                run_id,
            "action":
                "issue_refund",
            "resource":
                "customer/system-test",
            "arguments": {
                "amount":
                    780,
            },
            "provenance": {
                "source":
                    "system_test",
                "trust":
                    "trusted_internal",
            },
        },
    )

    if (
        evaluation.status_code
        != 200
    ):
        return (
            _outcome(
                evaluation.status_code
            ),
            {
                "stage":
                    "evaluation",
                **_safe_response(
                    evaluation
                ),
            },
        )

    body = (
        evaluation.json()
    )

    approval_id = (
        body.get(
            "approval_id"
        )
    )

    if not approval_id:
        return (
            "HARNESS_ERROR",
            {
                "error": (
                    "Expected approval_id "
                    "was not returned."
                )
            },
        )

    attack_response = _post(
        client,
        (
            f"/v1/approvals/"
            f"{approval_id}/approve"
        ),
        headers={
            "Content-Type":
                "application/json",
        },
        json={
            "resolved_by":
                "unauthenticated-attacker",
            "note":
                "System security test.",
        },
    )

    try:
        _post(
            client,
            (
                f"/v1/approvals/"
                f"{approval_id}/deny"
            ),
            headers={
                "X-Admin-Key":
                    settings
                    .agentguard_admin_key,
                "Content-Type":
                    "application/json",
            },
            json={
                "resolved_by":
                    "system-test-harness",
                "note": (
                    "Automatic cleanup after "
                    "admin-auth test."
                ),
            },
        )

        _complete_run(
            client=client,
            run_id=run_id,
            agent_key=agent_key,
        )

    except Exception:
        pass

    return (
        _outcome(
            attack_response.status_code
        ),
        {
            "run_id":
                run_id,
            "approval_id":
                approval_id,
            "admin_credential_supplied":
                False,
            **_safe_response(
                attack_response
            ),
        },
    )


def _test_execute_denied_action(
    *,
    client: httpx.Client,
    db: Session,
    agent: Agent,
    agent_key: str,
) -> tuple[str, dict]:
    run_response = _create_run(
        client=client,
        agent_id=agent.id,
        agent_key=agent_key,
    )

    if (
        run_response.status_code
        != 200
    ):
        return (
            _outcome(
                run_response.status_code
            ),
            {
                "stage":
                    "create_run",
                **_safe_response(
                    run_response
                ),
            },
        )

    run_id = (
        run_response.json()[
            "id"
        ]
    )

    evaluation = _post(
        client,
        "/v1/actions/evaluate",
        headers={
            "X-Agent-Key":
                agent_key,
            "Idempotency-Key":
                (
                    "system-test-"
                    + str(
                        uuid.uuid4()
                    )
                ),
        },
        json={
            "agent_id":
                agent.id,
            "run_id":
                run_id,
            "action":
                "unknown_security_test_action",
            "resource":
                "system-test/resource",
            "arguments": {},
            "provenance": {
                "source":
                    "system_test",
                "trust":
                    "trusted_internal",
            },
        },
    )

    if (
        evaluation.status_code
        != 200
    ):
        return (
            _outcome(
                evaluation.status_code
            ),
            {
                "stage":
                    "evaluation",
                **_safe_response(
                    evaluation
                ),
            },
        )

    body = (
        evaluation.json()
    )

    action_id = (
        body["action_id"]
    )

    attack_response = _post(
        client,
        (
            f"/v1/actions/"
            f"{action_id}/execute"
        ),
        headers={
            "X-Agent-Key":
                agent_key,
        },
    )

    _complete_run(
        client=client,
        run_id=run_id,
        agent_key=agent_key,
    )

    return (
        _outcome(
            attack_response.status_code
        ),
        {
            "run_id":
                run_id,
            "action_id":
                action_id,
            "policy_decision":
                body.get(
                    "decision"
                ),
            "execution_attempted":
                True,
            **_safe_response(
                attack_response
            ),
        },
    )


def _test_old_key_after_rotation(
    *,
    client: httpx.Client,
    db: Session,
    agent: Agent,
    agent_key: str,
) -> tuple[str, dict]:
    settings = get_settings()

    temporary_agent_id = None

    try:
        (
            temporary_agent_id,
            original_key,
        ) = _create_temporary_agent(
            db=db,
            name=(
                "System Test "
                "Credential Rotation Target"
            ),
        )

        rotate_response = _post(
            client,
            (
                f"/v1/agents/"
                f"{temporary_agent_id}/rotate-key"
            ),
            headers={
                "X-Admin-Key":
                    settings
                    .agentguard_admin_key,
            },
        )

        if (
            rotate_response.status_code
            != 200
        ):
            return (
                _outcome(
                    rotate_response
                    .status_code
                ),
                {
                    "stage":
                        "rotate_key",
                    **_safe_response(
                        rotate_response
                    ),
                },
            )

        attack_response = _post(
            client,
            "/v1/runs",
            headers={
                "X-Agent-Key":
                    original_key,
            },
            json={
                "agent_id":
                    temporary_agent_id,
            },
        )

        return (
            _outcome(
                attack_response.status_code
            ),
            {
                "agent_id":
                    temporary_agent_id,
                "rotation_succeeded":
                    True,
                "old_credential_reused":
                    True,
                **_safe_response(
                    attack_response
                ),
            },
        )

    finally:
        if temporary_agent_id:
            _cleanup_temporary_agent(
                db=db,
                agent_id=(
                    temporary_agent_id
                ),
            )


RUNNERS: dict[
    str,
    Callable,
] = {
    "missing-agent-key":
        _test_missing_agent_key,

    "invalid-agent-key":
        _test_invalid_agent_key,

    "cross-agent-impersonation":
        _test_cross_agent_impersonation,

    "idempotency-conflict":
        _test_idempotency_conflict,

    "approval-bypass":
        _test_approval_bypass,

    "cross-agent-run-access":
        _test_cross_agent_run_access,

    "completed-run-mutation":
        _test_completed_run_mutation,

    "approval-without-admin":
        _test_approval_without_admin,

    "execute-denied-action":
        _test_execute_denied_action,

    "old-key-after-rotation":
        _test_old_key_after_rotation,
}


def run_system_test_suite(
    *,
    db: Session,
    agent: Agent,
    agent_key: str,
    assessment_run_id: str,
) -> list[
    SystemSecurityTestResult
]:
    settings = get_settings()

    results = []

    with httpx.Client(
        base_url=(
            settings
            .system_test_base_url
        ),
        timeout=15.0,
    ) as client:

        for test in (
            list_system_tests()
        ):
            runner = (
                RUNNERS[
                    test.key
                ]
            )

            try:
                (
                    actual,
                    evidence,
                ) = runner(
                    client=client,
                    db=db,
                    agent=agent,
                    agent_key=(
                        agent_key
                    ),
                )

            except Exception as exc:
                actual = (
                    "HARNESS_ERROR"
                )

                evidence = {
                    "error_type":
                        type(exc).__name__,
                    "error":
                        str(exc),
                }

                db.rollback()

            passed = (
                actual
                == test.expected_outcome
            )

            result = (
                SystemSecurityTestResult(
                    agent_id=agent.id,
                    assessment_run_id=(
                        assessment_run_id
                    ),
                    test_key=test.key,
                    test_name=test.name,
                    category=test.category,
                    severity=test.severity,
                    expected_outcome=(
                        test.expected_outcome
                    ),
                    actual_outcome=(
                        actual
                    ),
                    passed=passed,
                    evidence=evidence,
                )
            )

            db.add(
                result
            )

            results.append(
                result
            )

        db.commit()

        for result in results:
            db.refresh(
                result
            )

    return results