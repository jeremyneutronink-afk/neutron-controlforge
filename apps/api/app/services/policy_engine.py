from dataclasses import dataclass
from typing import Any

from apps.api.app.schemas.action import DecisionType, RiskLevel


@dataclass
class PolicyResult:
    decision: DecisionType
    risk: RiskLevel
    reason: str
    policy: str


def evaluate_action(
    action: str,
    arguments: dict[str, Any],
    provenance: dict[str, Any],
) -> PolicyResult:
    """
    Deterministic first-generation ControlForge policy engine.

    Unknown actions fail closed rather than being silently allowed.
    """

    trust = provenance.get("trust")

    if action == "issue_refund":
        amount = arguments.get("amount")

        if not isinstance(amount, (int, float)):
            return PolicyResult(
                decision=DecisionType.DENY,
                risk=RiskLevel.HIGH,
                reason="Refund amount is missing or invalid.",
                policy="refund-validation",
            )

        if amount < 0:
            return PolicyResult(
                decision=DecisionType.DENY,
                risk=RiskLevel.HIGH,
                reason="Refund amount cannot be negative.",
                policy="refund-validation",
            )

        if amount <= 250:
            return PolicyResult(
                decision=DecisionType.ALLOW,
                risk=RiskLevel.LOW,
                reason="Refund is within the autonomous refund limit.",
                policy="refund-threshold",
            )

        return PolicyResult(
            decision=DecisionType.REQUIRE_APPROVAL,
            risk=RiskLevel.HIGH,
            reason="Refund exceeds the $250 autonomous limit.",
            policy="refund-threshold",
        )

    if action == "delete_customer":
        if trust == "external_untrusted":
            return PolicyResult(
                decision=DecisionType.DENY,
                risk=RiskLevel.CRITICAL,
                reason=(
                    "Untrusted external content cannot authorize "
                    "customer deletion."
                ),
                policy="untrusted-destructive-action",
            )

        return PolicyResult(
            decision=DecisionType.REQUIRE_APPROVAL,
            risk=RiskLevel.HIGH,
            reason="Customer deletion requires human approval.",
            policy="destructive-action-approval",
        )

    if action == "read_customer":
        return PolicyResult(
            decision=DecisionType.ALLOW,
            risk=RiskLevel.LOW,
            reason="Read-only customer access is permitted.",
            policy="read-access",
        )

    # Security-critical default:
    # anything ControlForge does not understand is denied.
    return PolicyResult(
        decision=DecisionType.DENY,
        risk=RiskLevel.HIGH,
        reason="Action is not recognized by the active policy set.",
        policy="default-deny",
    )