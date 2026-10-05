from __future__ import annotations

from typing import Any


class ControlForgeError(Exception):
    """Base exception for the ControlForge SDK."""


class ControlForgeAPIError(ControlForgeError):
    """Raised when the ControlForge API rejects or cannot process a request."""

    def __init__(
        self,
        *,
        status_code: int,
        message: str,
        body: Any = None,
    ) -> None:
        super().__init__(
            f"ControlForge API error {status_code}: {message}"
        )
        self.status_code = status_code
        self.message = message
        self.body = body
