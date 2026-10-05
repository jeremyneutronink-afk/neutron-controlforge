from __future__ import annotations

import uuid
from typing import Any

import httpx

from .exceptions import ControlForgeAPIError


class ControlForgeClient:
    """
    Synchronous client for agent-facing ControlForge APIs.

    The raw agent credential remains in process memory only.
    """

    def __init__(
        self,
        *,
        base_url: str,
        agent_id: str,
        api_key: str,
        timeout: float = 15.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not base_url.strip():
            raise ValueError("base_url is required.")
        if not agent_id.strip():
            raise ValueError("agent_id is required.")
        if not api_key.strip():
            raise ValueError("api_key is required.")

        self.base_url = base_url.rstrip("/")
        self.agent_id = agent_id
        self._api_key = api_key
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            transport=transport,
        )

    def __enter__(self) -> "ControlForgeClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def _agent_headers(
        self,
        *,
        idempotency_key: str | None = None,
    ) -> dict[str, str]:
        headers = {
            "X-Agent-Key": self._api_key,
        }

        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        return headers

    @staticmethod
    def _parse_response(
        response: httpx.Response,
    ) -> Any:
        if response.is_success:
            if not response.content:
                return None
            return response.json()

        try:
            body = response.json()
        except Exception:
            body = {
                "detail": response.text,
            }

        detail = body.get("detail") if isinstance(body, dict) else None

        raise ControlForgeAPIError(
            status_code=response.status_code,
            message=str(detail or "Request failed."),
            body=body,
        )

    def health(self) -> dict[str, Any]:
        response = self._client.get("/health")
        return self._parse_response(response)

    def create_run(self) -> dict[str, Any]:
        response = self._client.post(
            "/v1/runs",
            headers=self._agent_headers(),
            json={
                "agent_id": self.agent_id,
            },
        )
        return self._parse_response(response)

    def get_run(
        self,
        run_id: str,
    ) -> dict[str, Any]:
        response = self._client.get(
            f"/v1/runs/{run_id}",
            headers=self._agent_headers(),
        )
        return self._parse_response(response)

    def get_run_events(
        self,
        run_id: str,
    ) -> list[dict[str, Any]]:
        response = self._client.get(
            f"/v1/runs/{run_id}/events",
            headers=self._agent_headers(),
        )
        return self._parse_response(response)

    def evaluate(
        self,
        *,
        run_id: str,
        action: str,
        resource: str | None = None,
        arguments: dict[str, Any] | None = None,
        provenance: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        key = (
            idempotency_key
            or f"sdk-{uuid.uuid4()}"
        )

        response = self._client.post(
            "/v1/actions/evaluate",
            headers=self._agent_headers(
                idempotency_key=key,
            ),
            json={
                "agent_id": self.agent_id,
                "run_id": run_id,
                "action": action,
                "resource": resource,
                "arguments": arguments or {},
                "provenance": provenance or {
                    "source": "controlforge_sdk",
                    "trust": "trusted_internal",
                },
            },
        )
        return self._parse_response(response)

    def get_execution(
        self,
        action_id: str,
    ) -> dict[str, Any]:
        response = self._client.get(
            f"/v1/actions/{action_id}/execution",
            headers=self._agent_headers(),
        )
        return self._parse_response(response)

    def execute(
        self,
        action_id: str,
    ) -> dict[str, Any]:
        response = self._client.post(
            f"/v1/actions/{action_id}/execute",
            headers=self._agent_headers(),
        )
        return self._parse_response(response)

    def complete_run(
        self,
        run_id: str,
    ) -> dict[str, Any]:
        response = self._client.post(
            f"/v1/runs/{run_id}/complete",
            headers=self._agent_headers(),
        )
        return self._parse_response(response)
