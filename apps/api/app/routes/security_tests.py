from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.core.database import get_db
from apps.api.app.models import (
    Agent,
    AssessmentRun,
    SecurityTestResult,
)
from apps.api.app.schemas.assessment_run import (
    AssessmentRunResponse,
)
from apps.api.app.schemas.security_test import (
    SecurityTestBatchResponse,
    SecurityTestCatalogItem,
    SecurityTestPackResponse,
    SecurityTestPackRunRequest,
    SecurityTestResultResponse,
    SecurityTestRunAllRequest,
    SecurityTestRunRequest,
)
from apps.api.app.services.auth import (
    require_admin_key,
)
from apps.api.app.services.assessment_runs import (
    complete_assessment_run,
    fail_assessment_run,
    start_assessment_run,
)
from apps.api.app.services.policy_engine import (
    evaluate_action,
)
from apps.api.app.services.security_test_catalog import (
    get_security_test,
    get_security_test_pack,
    get_tests_for_pack,
    list_security_test_packs,
    list_security_tests,
)


router = APIRouter(
    prefix="/v1/security-tests",
    tags=["Security Tests"],
    dependencies=[
        Depends(require_admin_key)
    ],
)


def require_agent(
    *,
    db: Session,
    agent_id: str,
) -> Agent:
    agent = db.get(
        Agent,
        agent_id,
    )

    if agent is None:
        raise HTTPException(
            status_code=404,
            detail="Agent not found.",
        )

    return agent


def execute_security_test(
    *,
    db: Session,
    agent: Agent,
    test,
    assessment_run_id: str,
) -> SecurityTestResult:
    """
    Execute one deterministic policy test.

    Policy security tests intentionally call the policy engine
    directly. They test policy behavior, not HTTP authentication,
    transport security, replay handling, or control-plane security.
    """

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

    evidence = {
        "pack_key":
            test.pack_key,

        "action":
            test.action,

        "resource":
            test.resource,

        "arguments":
            test.arguments,

        "provenance":
            test.provenance,

        "expected_decision":
            test.expected_decision,

        "actual_decision":
            actual_decision,

        "risk":
            policy_result.risk.value,

        "reason":
            policy_result.reason,

        "policy":
            policy_result.policy,

        "severity":
            test.severity,

        "remediation_hint":
            test.remediation_hint,

        "tags":
            test.tags,
    }

    result = SecurityTestResult(
        agent_id=agent.id,
        assessment_run_id=assessment_run_id,
        test_key=test.key,
        test_name=test.name,
        category=test.category,
        expected_decision=test.expected_decision,
        actual_decision=actual_decision,
        passed=passed,
        evidence=evidence,
    )

    db.add(result)
    db.flush()

    return result


@router.get(
    "/packs",
    response_model=list[
        SecurityTestPackResponse
    ],
)
def get_test_packs():
    packs = []

    for pack in (
        list_security_test_packs()
    ):
        packs.append(
            SecurityTestPackResponse(
                key=pack.key,
                name=pack.name,
                description=pack.description,
                category=pack.category,
                test_count=len(
                    pack.test_keys
                ),
            )
        )

    return packs


@router.get(
    "/catalog",
    response_model=list[
        SecurityTestCatalogItem
    ],
)
def get_test_catalog():
    catalog = []

    packs_by_key = {
        pack.key: pack
        for pack
        in list_security_test_packs()
    }

    for test in (
        list_security_tests()
    ):
        pack = packs_by_key.get(
            test.pack_key
        )

        catalog.append(
            SecurityTestCatalogItem(
                key=test.key,
                pack_key=test.pack_key,
                pack_name=(
                    pack.name
                    if pack
                    else test.pack_key
                ),
                name=test.name,
                category=test.category,
                description=test.description,
                expected_decision=(
                    test.expected_decision
                ),
                severity=test.severity,
                remediation_hint=(
                    test.remediation_hint
                ),
                tags=test.tags,
            )
        )

    return catalog


@router.get(
    "/results",
    response_model=list[
        SecurityTestResultResponse
    ],
)
def get_test_results(
    limit: int = 100,
    db: Session = Depends(
        get_db
    ),
):
    limit = max(
        1,
        min(
            limit,
            500,
        ),
    )

    statement = (
        select(
            SecurityTestResult
        )
        .order_by(
            SecurityTestResult
            .created_at
            .desc()
        )
        .limit(limit)
    )

    return db.scalars(
        statement
    ).all()


@router.get(
    "/assessments",
    response_model=list[
        AssessmentRunResponse
    ],
)
def get_policy_assessments(
    agent_id: str | None = None,
    limit: int = 25,
    db: Session = Depends(
        get_db
    ),
):
    """Return persisted policy assessment batches."""

    safe_limit = max(
        1,
        min(limit, 100),
    )

    statement = (
        select(AssessmentRun)
        .where(
            AssessmentRun.assessment_type.in_(
                [
                    "POLICY_SINGLE",
                    "POLICY_PACK",
                    "POLICY_ALL",
                ]
            )
        )
    )

    if agent_id:
        statement = statement.where(
            AssessmentRun.agent_id
            == agent_id
        )

    statement = (
        statement
        .order_by(
            AssessmentRun.started_at.desc()
        )
        .limit(safe_limit)
    )

    return db.scalars(
        statement
    ).all()


@router.get(
    "/assessments/latest",
    response_model=AssessmentRunResponse | None,
)
def get_latest_policy_assessment(
    agent_id: str | None = None,
    db: Session = Depends(
        get_db
    ),
):
    """Return the newest policy assessment batch."""

    statement = (
        select(AssessmentRun)
        .where(
            AssessmentRun.assessment_type.in_(
                [
                    "POLICY_SINGLE",
                    "POLICY_PACK",
                    "POLICY_ALL",
                ]
            )
        )
    )

    if agent_id:
        statement = statement.where(
            AssessmentRun.agent_id
            == agent_id
        )

    statement = (
        statement
        .order_by(
            AssessmentRun.started_at.desc()
        )
        .limit(1)
    )

    return db.scalar(
        statement
    )


@router.get(
    "/assessments/{assessment_run_id}",
    response_model=AssessmentRunResponse,
)
def get_policy_assessment(
    assessment_run_id: str,
    db: Session = Depends(
        get_db
    ),
):
    assessment = db.get(
        AssessmentRun,
        assessment_run_id,
    )

    if (
        assessment is None
        or not assessment.assessment_type.startswith(
            "POLICY_"
        )
    ):
        raise HTTPException(
            status_code=404,
            detail="Policy assessment not found.",
        )

    return assessment


@router.get(
    "/assessments/{assessment_run_id}/results",
    response_model=list[
        SecurityTestResultResponse
    ],
)
def get_policy_assessment_results(
    assessment_run_id: str,
    db: Session = Depends(
        get_db
    ),
):
    assessment = db.get(
        AssessmentRun,
        assessment_run_id,
    )

    if (
        assessment is None
        or not assessment.assessment_type.startswith(
            "POLICY_"
        )
    ):
        raise HTTPException(
            status_code=404,
            detail="Policy assessment not found.",
        )

    statement = (
        select(SecurityTestResult)
        .where(
            SecurityTestResult.assessment_run_id
            == assessment_run_id
        )
        .order_by(
            SecurityTestResult.created_at.asc()
        )
    )

    return db.scalars(
        statement
    ).all()


@router.post(
    "/run",
    response_model=SecurityTestResultResponse,
)
def run_security_test(
    payload: SecurityTestRunRequest,
    db: Session = Depends(
        get_db
    ),
):
    agent = require_agent(
        db=db,
        agent_id=payload.agent_id,
    )

    test = get_security_test(
        payload.test_key
    )

    if test is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Security test not found."
            ),
        )

    assessment = (
        start_assessment_run(
            db=db,
            agent_id=agent.id,
            assessment_type=(
                "POLICY_SINGLE"
            ),
            scope_key=test.key,
        )
    )

    try:
        result = (
            execute_security_test(
                db=db,
                agent=agent,
                test=test,
                assessment_run_id=(
                    assessment.id
                ),
            )
        )

        complete_assessment_run(
            assessment=assessment,
            total=1,
            passed=(
                1
                if result.passed
                else 0
            ),
            failed=(
                0
                if result.passed
                else 1
            ),
        )

        db.commit()
        db.refresh(result)

        return result

    except Exception:
        db.rollback()

        assessment = db.get(
            type(assessment),
            assessment.id,
        )

        if assessment is not None:
            fail_assessment_run(
                assessment=assessment,
            )

            db.commit()

        raise


@router.post(
    "/run-pack",
    response_model=SecurityTestBatchResponse,
)
def run_security_test_pack(
    payload: SecurityTestPackRunRequest,
    db: Session = Depends(
        get_db
    ),
):
    agent = require_agent(
        db=db,
        agent_id=payload.agent_id,
    )

    pack = get_security_test_pack(
        payload.pack_key
    )

    if pack is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Security test pack "
                "not found."
            ),
        )

    tests = get_tests_for_pack(
        pack.key
    )

    assessment = (
        start_assessment_run(
            db=db,
            agent_id=agent.id,
            assessment_type=(
                "POLICY_PACK"
            ),
            scope_key=pack.key,
        )
    )

    try:
        results = []

        for test in tests:
            result = (
                execute_security_test(
                    db=db,
                    agent=agent,
                    test=test,
                    assessment_run_id=(
                        assessment.id
                    ),
                )
            )

            results.append(
                result
            )

        total = len(
            results
        )

        passed = sum(
            1
            for result in results
            if result.passed
        )

        failed = (
            total - passed
        )

        complete_assessment_run(
            assessment=assessment,
            total=total,
            passed=passed,
            failed=failed,
        )

        db.commit()

        for result in results:
            db.refresh(result)

        return SecurityTestBatchResponse(
            assessment_run_id=(
                assessment.id
            ),
            scope="PACK",
            scope_key=pack.key,
            agent_id=agent.id,
            total=total,
            passed=passed,
            failed=failed,
            results=results,
        )

    except Exception:
        db.rollback()

        assessment = db.get(
            type(assessment),
            assessment.id,
        )

        if assessment is not None:
            fail_assessment_run(
                assessment=assessment,
            )

            db.commit()

        raise


@router.post(
    "/run-all",
    response_model=SecurityTestBatchResponse,
)
def run_all_security_tests(
    payload: SecurityTestRunAllRequest,
    db: Session = Depends(
        get_db
    ),
):
    agent = require_agent(
        db=db,
        agent_id=payload.agent_id,
    )

    tests = list_security_tests()

    assessment = (
        start_assessment_run(
            db=db,
            agent_id=agent.id,
            assessment_type=(
                "POLICY_ALL"
            ),
            scope_key=None,
        )
    )

    try:
        results = []

        for test in tests:
            result = (
                execute_security_test(
                    db=db,
                    agent=agent,
                    test=test,
                    assessment_run_id=(
                        assessment.id
                    ),
                )
            )

            results.append(
                result
            )

        total = len(
            results
        )

        passed = sum(
            1
            for result in results
            if result.passed
        )

        failed = (
            total - passed
        )

        complete_assessment_run(
            assessment=assessment,
            total=total,
            passed=passed,
            failed=failed,
        )

        db.commit()

        for result in results:
            db.refresh(result)

        return SecurityTestBatchResponse(
            assessment_run_id=(
                assessment.id
            ),
            scope="ALL",
            scope_key=None,
            agent_id=agent.id,
            total=total,
            passed=passed,
            failed=failed,
            results=results,
        )

    except Exception:
        db.rollback()

        assessment = db.get(
            type(assessment),
            assessment.id,
        )

        if assessment is not None:
            fail_assessment_run(
                assessment=assessment,
            )

            db.commit()

        raise
