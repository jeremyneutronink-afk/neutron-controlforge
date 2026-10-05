import json

import httpx
import pytest

from controlforge import (
    ControlForgeAPIError,
    ControlForgeClient,
)


def make_transport():
    seen = []

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        seen.append(request)

        if (
            request.method == "POST"
            and request.url.path == "/v1/runs"
        ):
            return httpx.Response(
                200,
                json={
                    "id": "run-1",
                    "agent_id": "agent-1",
                    "status": "CREATED",
                    "started_at": "2026-10-04T00:00:00Z",
                    "completed_at": None,
                },
            )

        if (
            request.method == "POST"
            and request.url.path == "/v1/actions/evaluate"
        ):
            return httpx.Response(
                200,
                json={
                    "action_id": "action-1",
                    "decision_id": "decision-1",
                    "execution_id": "execution-1",
                    "approval_id": None,
                    "decision": "ALLOW",
                    "risk": "LOW",
                    "reason": "Allowed.",
                    "policy": "test-policy",
                },
            )

        return httpx.Response(
            401,
            json={
                "detail": "Invalid agent credential.",
            },
        )

    return (
        httpx.MockTransport(handler),
        seen,
    )


def test_sdk_sends_agent_key_and_idempotency_key():
    transport, seen = make_transport()

    with ControlForgeClient(
        base_url="http://controlforge.test",
        agent_id="agent-1",
        api_key="agk_secret",
        transport=transport,
    ) as client:
        run = client.create_run()

        client.evaluate(
            run_id=run["id"],
            action="read_customer",
            resource="customer/1",
            idempotency_key="idem-1",
        )

    create_request = seen[0]
    evaluate_request = seen[1]

    assert (
        create_request.headers["x-agent-key"]
        == "agk_secret"
    )

    assert (
        evaluate_request.headers["idempotency-key"]
        == "idem-1"
    )

    payload = json.loads(
        evaluate_request.content
    )

    assert payload["agent_id"] == "agent-1"


def test_sdk_raises_typed_api_error():
    transport, _ = make_transport()

    with ControlForgeClient(
        base_url="http://controlforge.test",
        agent_id="agent-1",
        api_key="agk_secret",
        transport=transport,
    ) as client:
        with pytest.raises(
            ControlForgeAPIError
        ) as exc:
            client.get_run(
                "missing-run"
            )

    assert exc.value.status_code == 401
