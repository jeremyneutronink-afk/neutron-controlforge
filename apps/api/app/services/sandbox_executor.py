from typing import Any


class SandboxExecutionError(Exception):
    pass


def execute_sandbox_action(
    action: str,
    resource: str | None,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    """
    Safely simulate tool execution.

    No real external systems are touched here.
    The returned payload describes what WOULD have happened.
    """

    if action == "issue_refund":
        amount = arguments.get("amount")

        if not isinstance(amount, (int, float)):
            raise SandboxExecutionError(
                "Refund amount is missing or invalid."
            )

        return {
            "mode": "sandbox",
            "tool": "issue_refund",
            "resource": resource,
            "amount": amount,
            "currency": "USD",
            "simulated": True,
            "message": (
                f"Simulated refund of ${amount:.2f} "
                f"for {resource}."
            ),
        }

    if action == "delete_customer":
        return {
            "mode": "sandbox",
            "tool": "delete_customer",
            "resource": resource,
            "simulated": True,
            "message": (
                f"Simulated deletion of {resource}. "
                "No customer data was changed."
            ),
        }

    if action == "read_customer":
        return {
            "mode": "sandbox",
            "tool": "read_customer",
            "resource": resource,
            "simulated": True,
            "customer": {
                "id": resource,
                "name": "Sandbox Customer",
                "status": "active",
            },
        }

    raise SandboxExecutionError(
        f"No sandbox executor exists for action '{action}'."
    )