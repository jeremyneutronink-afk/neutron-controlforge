from apps.api.app.services.policy_engine import (
    evaluate_action,
)


def decision_for(
    action: str,
    *,
    arguments: dict | None = None,
    trust: str = "trusted_internal",
) -> str:
    result = evaluate_action(
        action=action,
        arguments=arguments or {},
        provenance={
            "source": "pytest",
            "trust": trust,
        },
    )

    return result.decision.value


def test_safe_refund_is_allowed():
    assert (
        decision_for(
            "issue_refund",
            arguments={"amount": 100},
        )
        == "ALLOW"
    )


def test_refund_boundary_is_allowed():
    assert (
        decision_for(
            "issue_refund",
            arguments={"amount": 250},
        )
        == "ALLOW"
    )


def test_large_refund_requires_approval():
    assert (
        decision_for(
            "issue_refund",
            arguments={"amount": 251},
        )
        == "REQUIRE_APPROVAL"
    )


def test_negative_refund_is_denied():
    assert (
        decision_for(
            "issue_refund",
            arguments={"amount": -1},
        )
        == "DENY"
    )


def test_untrusted_delete_is_denied():
    assert (
        decision_for(
            "delete_customer",
            trust="external_untrusted",
        )
        == "DENY"
    )


def test_trusted_delete_requires_approval():
    assert (
        decision_for(
            "delete_customer",
        )
        == "REQUIRE_APPROVAL"
    )


def test_unknown_action_fails_closed():
    assert (
        decision_for(
            "totally_unknown_action",
        )
        == "DENY"
    )
