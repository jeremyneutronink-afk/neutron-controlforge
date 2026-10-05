from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.core.database import get_db
from apps.api.app.models import (
    Agent,
    Finding,
    SecurityTestResult,
    SystemSecurityTestResult,
)
from apps.api.app.schemas.finding import (
    FindingCreateRequest,
    FindingResponse,
    FindingUpdateRequest,
)
from apps.api.app.services.auth import (
    require_admin_key,
)
from apps.api.app.services.policy_engine import evaluate_action
from apps.api.app.services.security_test_catalog import get_security_test


router = APIRouter(
    prefix="/findings",
    tags=["Findings"],
    dependencies=[
        Depends(require_admin_key)
    ],
)


@router.get(
    "",
    response_model=list[FindingResponse],
)
def list_findings(
    db: Session = Depends(get_db),
):
    statement = (
        select(Finding)
        .order_by(
            Finding.created_at.desc()
        )
    )

    return db.scalars(statement).all()


@router.get(
    "/{finding_id}",
    response_model=FindingResponse,
)
def get_finding(
    finding_id: str,
    db: Session = Depends(get_db),
):
    finding = db.get(
        Finding,
        finding_id,
    )

    if finding is None:
        raise HTTPException(
            status_code=404,
            detail="Finding not found.",
        )

    return finding


@router.post(
    "",
    response_model=FindingResponse,
)
def create_manual_finding(
    payload: FindingCreateRequest,
    db: Session = Depends(get_db),
):
    agent = db.get(
        Agent,
        payload.agent_id,
    )

    if agent is None:
        raise HTTPException(
            status_code=404,
            detail="Agent not found.",
        )

    finding = Finding(
        agent_id=payload.agent_id,
        title=payload.title,
        severity=payload.severity.value,
        status="OPEN",
        description=payload.description,
        evidence={
            "source": "manual",
            "agent_name": agent.name,
        },
        remediation=payload.remediation,
        retest_status="NOT_RUN",
    )

    db.add(finding)
    db.commit()
    db.refresh(finding)

    return finding


@router.post(
    "/from-test/{test_result_id}",
    response_model=FindingResponse,
)
def create_finding_from_test(
    test_result_id: str,
    db: Session = Depends(get_db),
):
    test_result = db.get(
        SecurityTestResult,
        test_result_id,
    )

    if test_result is None:
        raise HTTPException(
            status_code=404,
            detail="Security test result not found.",
        )

    if test_result.passed:
        raise HTTPException(
            status_code=409,
            detail=(
                "A finding cannot be created from "
                "a passing security test."
            ),
        )

    existing_statement = select(
        Finding
    ).where(
        Finding.source_test_result_id
        == test_result.id
    )

    existing_finding = db.scalar(
        existing_statement
    )

    if existing_finding is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "A finding already exists for "
                "this security test result."
            ),
        )

    risk = test_result.evidence.get(
        "risk",
        "HIGH",
    )

    if risk not in {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    }:
        risk = "HIGH"

    finding = Finding(
        agent_id=test_result.agent_id,
        source_test_result_id=test_result.id,
        title=(
            f"{test_result.test_name} "
            f"security control failure"
        ),
        severity=risk,
        status="OPEN",
        description=(
            f"Security test '{test_result.test_name}' "
            f"expected {test_result.expected_decision} "
            f"but observed {test_result.actual_decision}."
        ),
        evidence={
            "source": "security_test",
            "security_test_result_id": test_result.id,
            "test_key": test_result.test_key,
            "test_name": test_result.test_name,
            "category": test_result.category,
            "expected_decision": (
                test_result.expected_decision
            ),
            "actual_decision": (
                test_result.actual_decision
            ),
            "test_evidence": (
                test_result.evidence
            ),
        },
        remediation=None,
        retest_status="NOT_RUN",
    )

    db.add(finding)
    db.commit()
    db.refresh(finding)

    return finding




@router.post(
    "/from-system-test/{test_result_id}",
    response_model=FindingResponse,
)
def create_finding_from_system_test(
    test_result_id: str,
    db: Session = Depends(get_db),
):
    test_result = db.get(
        SystemSecurityTestResult,
        test_result_id,
    )

    if test_result is None:
        raise HTTPException(
            status_code=404,
            detail="System security test result not found.",
        )

    if test_result.passed:
        raise HTTPException(
            status_code=409,
            detail=(
                "A finding cannot be created from "
                "a passing system security test."
            ),
        )

    existing_findings = db.scalars(
        select(Finding).where(
            Finding.agent_id == test_result.agent_id
        )
    ).all()

    for existing in existing_findings:
        evidence = existing.evidence or {}
        if (
            evidence.get("source") == "system_test"
            and evidence.get("system_test_result_id")
            == test_result.id
        ):
            raise HTTPException(
                status_code=409,
                detail=(
                    "A finding already exists for "
                    "this system security test result."
                ),
            )

    finding = Finding(
        agent_id=test_result.agent_id,
        source_test_result_id=None,
        title=(
            f"{test_result.test_name} "
            "system control failure"
        ),
        severity=test_result.severity,
        status="OPEN",
        description=(
            f"System security test '{test_result.test_name}' "
            f"expected {test_result.expected_outcome} "
            f"but observed {test_result.actual_outcome}."
        ),
        evidence={
            "source": "system_test",
            "system_test_result_id": test_result.id,
            "assessment_run_id": test_result.assessment_run_id,
            "test_key": test_result.test_key,
            "test_name": test_result.test_name,
            "category": test_result.category,
            "expected_outcome": test_result.expected_outcome,
            "actual_outcome": test_result.actual_outcome,
            "test_evidence": test_result.evidence,
        },
        remediation=None,
        retest_status="NOT_RUN",
    )

    db.add(finding)
    db.commit()
    db.refresh(finding)

    return finding


@router.patch(
    "/{finding_id}",
    response_model=FindingResponse,
)
def update_finding(
    finding_id: str,
    payload: FindingUpdateRequest,
    db: Session = Depends(get_db),
):
    statement = (
        select(Finding)
        .where(
            Finding.id == finding_id
        )
        .with_for_update()
    )

    finding = db.scalar(statement)

    if finding is None:
        raise HTTPException(
            status_code=404,
            detail="Finding not found.",
        )

    if payload.status is not None:
        finding.status = (
            payload.status.value
        )

    if payload.severity is not None:
        finding.severity = (
            payload.severity.value
        )

    if payload.remediation is not None:
        finding.remediation = (
            payload.remediation
        )

    if payload.retest_status is not None:
        finding.retest_status = (
            payload.retest_status.value
        )

    finding.updated_at = (
        datetime.now(timezone.utc)
    )

    db.commit()
    db.refresh(finding)

    return finding


@router.post(
    "/{finding_id}/retest",
    response_model=FindingResponse,
)
def retest_finding(
    finding_id: str,
    db: Session = Depends(get_db),
):
    statement = (
        select(Finding)
        .where(
            Finding.id == finding_id
        )
        .with_for_update()
    )

    finding = db.scalar(statement)

    if finding is None:
        raise HTTPException(
            status_code=404,
            detail="Finding not found.",
        )

    if finding.source_test_result_id is None:
        source = (
            finding.evidence or {}
        ).get("source")

        if source == "system_test":
            raise HTTPException(
                status_code=409,
                detail=(
                    "System findings are retested by rerunning "
                    "the System Security Test suite."
                ),
            )

        raise HTTPException(
            status_code=409,
            detail=(
                "Manual findings cannot be automatically retested."
            ),
        )

    if finding.status != "READY_FOR_RETEST":
        raise HTTPException(
            status_code=409,
            detail=(
                "Finding must be READY_FOR_RETEST "
                "before a retest can run."
            ),
        )

    original_result = db.get(
        SecurityTestResult,
        finding.source_test_result_id,
    )

    if original_result is None:
        raise HTTPException(
            status_code=500,
            detail=(
                "Original security test result is missing."
            ),
        )

    test = get_security_test(
        original_result.test_key
    )

    if test is None:
        raise HTTPException(
            status_code=409,
            detail=(
                "The original security test is no longer "
                "available in the active test catalog."
            ),
        )

    agent = db.get(
        Agent,
        finding.agent_id,
    )

    if agent is None:
        raise HTTPException(
            status_code=404,
            detail="Agent not found.",
        )

    policy_result = evaluate_action(
        action=test.action,
        arguments=test.arguments,
        provenance=test.provenance,
    )

    actual_decision = (
        policy_result.decision.value
    )

    passed = (
        actual_decision
        == test.expected_decision
    )

    retest_result = SecurityTestResult(
        agent_id=agent.id,
        test_key=test.key,
        test_name=test.name,
        category=test.category,
        expected_decision=(
            test.expected_decision
        ),
        actual_decision=(
            actual_decision
        ),
        passed=passed,
        evidence={
            "agent_name": agent.name,
            "action": test.action,
            "resource": test.resource,
            "arguments": test.arguments,
            "provenance": test.provenance,
            "expected_decision": (
                test.expected_decision
            ),
            "actual_decision": (
                actual_decision
            ),
            "risk": (
                policy_result.risk.value
            ),
            "policy": (
                policy_result.policy
            ),
            "reason": (
                policy_result.reason
            ),
            "retest_of_finding": (
                finding.id
            ),
            "original_test_result_id": (
                original_result.id
            ),
        },
    )

    db.add(retest_result)
    db.flush()

    new_evidence = dict(
        finding.evidence
    )

    new_evidence["latest_retest"] = {
        "result_id": retest_result.id,
        "passed": passed,
        "expected_decision": (
            test.expected_decision
        ),
        "actual_decision": (
            actual_decision
        ),
        "policy": (
            policy_result.policy
        ),
        "risk": (
            policy_result.risk.value
        ),
        "reason": (
            policy_result.reason
        ),
        "timestamp": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
    }

    finding.evidence = (
        new_evidence
    )

    if passed:
        finding.retest_status = "PASS"
        finding.status = "RESOLVED"
    else:
        finding.retest_status = "FAIL"
        finding.status = "IN_REMEDIATION"

    finding.updated_at = (
        datetime.now(timezone.utc)
    )

    db.commit()
    db.refresh(finding)

    return finding
