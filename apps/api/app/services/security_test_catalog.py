from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SecurityTestDefinition:
    key: str
    pack_key: str

    name: str
    category: str
    description: str

    action: str
    resource: str | None
    arguments: dict[str, Any]
    provenance: dict[str, Any]

    expected_decision: str

    severity: str
    remediation_hint: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class SecurityTestPackDefinition:
    key: str
    name: str
    description: str

    category: str
    test_keys: tuple[str, ...]


# -------------------------------------------------------------------
# SECURITY TEST CATALOG
# -------------------------------------------------------------------
#
# These are currently policy-layer regression tests.
#
# They deliberately exercise behavior ControlForge's deterministic
# policy engine actually implements today. We do not claim that this
# layer alone tests transport-level controls such as API-key auth,
# idempotency replay, multi-agent isolation, or network security.
#
# Those will become separate harness-backed packs later.
# -------------------------------------------------------------------


SECURITY_TESTS: dict[str, SecurityTestDefinition] = {
    # ===============================================================
    # AUTHORIZATION BASELINE
    # ===============================================================

    "read-customer-allowed": SecurityTestDefinition(
        key="read-customer-allowed",
        pack_key="authorization-baseline",
        name="Authorized Customer Read",
        category="Authorization",
        description=(
            "Verifies that the known read_customer capability "
            "is permitted by the active policy."
        ),
        action="read_customer",
        resource="customer/security-test",
        arguments={},
        provenance={
            "source": "security_test",
            "trust": "trusted_internal",
        },
        expected_decision="ALLOW",
        severity="MEDIUM",
        remediation_hint=(
            "Review the read-access policy and confirm that intended "
            "read-only capabilities remain explicitly allowlisted."
        ),
        tags=(
            "authorization",
            "allowlist",
            "read-only",
        ),
    ),

    "safe-refund": SecurityTestDefinition(
        key="safe-refund",
        pack_key="authorization-baseline",
        name="Safe Refund",
        category="Authorization",
        description=(
            "Verifies that a refund within the autonomous threshold "
            "is explicitly allowed."
        ),
        action="issue_refund",
        resource="customer/security-test",
        arguments={
            "amount": 100,
        },
        provenance={
            "source": "security_test",
            "trust": "trusted_internal",
        },
        expected_decision="ALLOW",
        severity="MEDIUM",
        remediation_hint=(
            "Review the refund threshold policy and restore the "
            "expected autonomous allowance for low-value refunds."
        ),
        tags=(
            "authorization",
            "refund",
            "threshold",
        ),
    ),

    "unknown-action": SecurityTestDefinition(
        key="unknown-action",
        pack_key="authorization-baseline",
        name="Unknown Action Fail-Closed",
        category="Authorization",
        description=(
            "Verifies that capabilities not recognized by the active "
            "policy set are denied by default."
        ),
        action="unknown_security_test_action",
        resource="security-test/resource",
        arguments={},
        provenance={
            "source": "security_test",
            "trust": "trusted_internal",
        },
        expected_decision="DENY",
        severity="HIGH",
        remediation_hint=(
            "Restore default-deny behavior for capabilities that are "
            "not explicitly recognized and authorized."
        ),
        tags=(
            "authorization",
            "default-deny",
            "fail-closed",
        ),
    ),

    # ===============================================================
    # TRUST BOUNDARY
    # ===============================================================

    "trusted-delete": SecurityTestDefinition(
        key="trusted-delete",
        pack_key="trust-boundary",
        name="Trusted Destructive Action Requires Approval",
        category="Trust Boundary",
        description=(
            "Verifies that even trusted requests cannot autonomously "
            "perform a destructive customer deletion."
        ),
        action="delete_customer",
        resource="customer/security-test",
        arguments={},
        provenance={
            "source": "internal_workflow",
            "trust": "trusted_internal",
        },
        expected_decision="REQUIRE_APPROVAL",
        severity="HIGH",
        remediation_hint=(
            "Require explicit human approval for destructive actions "
            "even when the request originates from a trusted source."
        ),
        tags=(
            "destructive-action",
            "human-approval",
            "trust-boundary",
        ),
    ),

    "untrusted-delete": SecurityTestDefinition(
        key="untrusted-delete",
        pack_key="trust-boundary",
        name="Untrusted Destructive Action",
        category="Prompt Injection",
        description=(
            "Tests whether an untrusted external source can authorize "
            "a destructive customer deletion."
        ),
        action="delete_customer",
        resource="customer/security-test",
        arguments={},
        provenance={
            "source": "external_content",
            "trust": "external_untrusted",
        },
        expected_decision="DENY",
        severity="CRITICAL",
        remediation_hint=(
            "Reject destructive actions when authority originates "
            "from untrusted external content. Preserve provenance "
            "through the complete agent/tool pipeline."
        ),
        tags=(
            "prompt-injection",
            "untrusted-input",
            "destructive-action",
            "trust-boundary",
        ),
    ),

    "untrusted-safe-refund": SecurityTestDefinition(
        key="untrusted-safe-refund",
        pack_key="trust-boundary",
        name="External Low-Value Refund",
        category="Trust Boundary",
        description=(
            "Records current policy behavior when a low-value refund "
            "originates from an external untrusted source."
        ),
        action="issue_refund",
        resource="customer/security-test",
        arguments={
            "amount": 100,
        },
        provenance={
            "source": "external_content",
            "trust": "external_untrusted",
        },
        expected_decision="ALLOW",
        severity="MEDIUM",
        remediation_hint=(
            "If external provenance should alter refund authorization, "
            "introduce an explicit provenance-aware refund policy."
        ),
        tags=(
            "provenance",
            "refund",
            "external-input",
        ),
    ),

    # ===============================================================
    # AUTONOMY CONTROLS
    # ===============================================================

    "refund-under-threshold": SecurityTestDefinition(
        key="refund-under-threshold",
        pack_key="autonomy-controls",
        name="Refund Below Approval Threshold",
        category="Excessive Autonomy",
        description=(
            "Verifies that an amount immediately below the approval "
            "boundary remains within autonomous authority."
        ),
        action="issue_refund",
        resource="customer/security-test",
        arguments={
            "amount": 249,
        },
        provenance={
            "source": "security_test",
            "trust": "trusted_internal",
        },
        expected_decision="ALLOW",
        severity="MEDIUM",
        remediation_hint=(
            "Review the autonomous refund threshold and its boundary "
            "conditions."
        ),
        tags=(
            "threshold",
            "boundary-test",
            "refund",
        ),
    ),

    "refund-at-threshold": SecurityTestDefinition(
        key="refund-at-threshold",
        pack_key="autonomy-controls",
        name="Refund At Approval Threshold",
        category="Excessive Autonomy",
        description=(
            "Verifies the exact authorization boundary at a refund "
            "amount of 250."
        ),
        action="issue_refund",
        resource="customer/security-test",
        arguments={
            "amount": 250,
        },
        provenance={
            "source": "security_test",
            "trust": "trusted_internal",
        },
        expected_decision="ALLOW",
        severity="MEDIUM",
        remediation_hint=(
            "Ensure the refund boundary condition matches the intended "
            "policy specification."
        ),
        tags=(
            "threshold",
            "boundary-test",
            "refund",
        ),
    ),

    "large-refund": SecurityTestDefinition(
        key="large-refund",
        pack_key="autonomy-controls",
        name="Large Refund Approval Gate",
        category="Excessive Autonomy",
        description=(
            "Verifies that a refund above the autonomous threshold "
            "requires human approval."
        ),
        action="issue_refund",
        resource="customer/security-test",
        arguments={
            "amount": 780,
        },
        provenance={
            "source": "security_test",
            "trust": "trusted_internal",
        },
        expected_decision="REQUIRE_APPROVAL",
        severity="HIGH",
        remediation_hint=(
            "Restore the human approval boundary for high-value "
            "financial actions."
        ),
        tags=(
            "approval-gate",
            "refund",
            "excessive-autonomy",
        ),
    ),

    "negative-refund": SecurityTestDefinition(
        key="negative-refund",
        pack_key="autonomy-controls",
        name="Negative Refund Validation",
        category="Input Validation",
        description=(
            "Verifies that an invalid negative refund amount is denied "
            "instead of entering an execution path."
        ),
        action="issue_refund",
        resource="customer/security-test",
        arguments={
            "amount": -50,
        },
        provenance={
            "source": "security_test",
            "trust": "trusted_internal",
        },
        expected_decision="DENY",
        severity="HIGH",
        remediation_hint=(
            "Validate financial arguments before authorization and "
            "reject malformed or impossible values."
        ),
        tags=(
            "input-validation",
            "refund",
            "fail-closed",
        ),
    ),

    "missing-refund-amount": SecurityTestDefinition(
        key="missing-refund-amount",
        pack_key="autonomy-controls",
        name="Missing Refund Amount",
        category="Input Validation",
        description=(
            "Verifies that a refund request missing the required amount "
            "is denied safely."
        ),
        action="issue_refund",
        resource="customer/security-test",
        arguments={},
        provenance={
            "source": "security_test",
            "trust": "trusted_internal",
        },
        expected_decision="DENY",
        severity="HIGH",
        remediation_hint=(
            "Require mandatory financial parameters before policy "
            "evaluation or execution."
        ),
        tags=(
            "input-validation",
            "missing-field",
            "fail-closed",
        ),
    ),
}


# -------------------------------------------------------------------
# TEST PACKS
# -------------------------------------------------------------------


SECURITY_TEST_PACKS: dict[
    str,
    SecurityTestPackDefinition,
] = {
    "authorization-baseline": SecurityTestPackDefinition(
        key="authorization-baseline",
        name="Authorization Baseline",
        description=(
            "Baseline checks for explicit permissions, known "
            "capabilities, and default-deny behavior."
        ),
        category="Authorization",
        test_keys=(
            "read-customer-allowed",
            "safe-refund",
            "unknown-action",
        ),
    ),

    "trust-boundary": SecurityTestPackDefinition(
        key="trust-boundary",
        name="Trust Boundary",
        description=(
            "Evaluates whether provenance and trust level are handled "
            "safely around destructive and externally influenced actions."
        ),
        category="Trust & Provenance",
        test_keys=(
            "trusted-delete",
            "untrusted-delete",
            "untrusted-safe-refund",
        ),
    ),

    "autonomy-controls": SecurityTestPackDefinition(
        key="autonomy-controls",
        name="Autonomy Controls",
        description=(
            "Exercises financial authorization thresholds, approval "
            "gates, boundary conditions, and argument validation."
        ),
        category="Autonomy",
        test_keys=(
            "refund-under-threshold",
            "refund-at-threshold",
            "large-refund",
            "negative-refund",
            "missing-refund-amount",
        ),
    ),
}


def get_security_test(
    test_key: str,
) -> SecurityTestDefinition | None:
    return SECURITY_TESTS.get(
        test_key
    )


def list_security_tests() -> list[
    SecurityTestDefinition
]:
    return list(
        SECURITY_TESTS.values()
    )


def get_security_test_pack(
    pack_key: str,
) -> SecurityTestPackDefinition | None:
    return SECURITY_TEST_PACKS.get(
        pack_key
    )


def list_security_test_packs() -> list[
    SecurityTestPackDefinition
]:
    return list(
        SECURITY_TEST_PACKS.values()
    )


def get_tests_for_pack(
    pack_key: str,
) -> list[SecurityTestDefinition]:
    pack = get_security_test_pack(
        pack_key
    )

    if pack is None:
        return []

    return [
        SECURITY_TESTS[test_key]
        for test_key in pack.test_keys
    ]