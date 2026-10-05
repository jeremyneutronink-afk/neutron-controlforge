from datetime import datetime, timezone

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
    Finding,
    SystemSecurityTestResult,
)
from apps.api.app.schemas.assessment_run import (
    AssessmentRunResponse,
)
from apps.api.app.schemas.system_test import (
    SystemTestBatchResponse,
    SystemTestCatalogItem,
    SystemTestResultResponse,
    SystemTestRunRequest,
)
from apps.api.app.services.auth import (
    require_admin_key,
)
from apps.api.app.services.assessment_runs import (
    complete_assessment_run,
    fail_assessment_run,
    start_assessment_run,
)
from apps.api.app.services.auth import (
    authenticate_agent,
)
from apps.api.app.services.system_test_runner import (
    list_system_tests,
    run_system_test_suite,
)


router = APIRouter(
    prefix="/system-tests",
    tags=["System Security Tests"],
    dependencies=[
        Depends(require_admin_key)
    ],
)


# -------------------------------------------------------------------
# CATALOG
# -------------------------------------------------------------------


@router.get(
    "/catalog",
    response_model=list[
        SystemTestCatalogItem
    ],
)
def get_system_test_catalog():
    """
    Return the system-level security tests currently available.

    These tests attack the running ControlForge HTTP control plane
    instead of calling policy logic directly.
    """

    return [
        SystemTestCatalogItem(
            key=test.key,
            name=test.name,
            category=test.category,
            description=test.description,
            severity=test.severity,
            expected_outcome=(
                test.expected_outcome
            ),
        )
        for test in list_system_tests()
    ]


# -------------------------------------------------------------------
# RAW TEST RESULT HISTORY
# -------------------------------------------------------------------


@router.get(
    "/results",
    response_model=list[
        SystemTestResultResponse
    ],
)
def get_system_test_results(
    limit: int = 100,
    db: Session = Depends(
        get_db
    ),
):
    """
    Return individual persisted test results.

    This endpoint is useful for forensic history, but dashboards
    should prefer assessment batches when displaying pass/fail totals.
    """

    limit = max(
        1,
        min(
            limit,
            500,
        ),
    )

    statement = (
        select(
            SystemSecurityTestResult
        )
        .order_by(
            SystemSecurityTestResult
            .created_at
            .desc()
        )
        .limit(limit)
    )

    return db.scalars(
        statement
    ).all()


# -------------------------------------------------------------------
# ASSESSMENT HISTORY
# -------------------------------------------------------------------


@router.get(
    "/assessments",
    response_model=list[
        AssessmentRunResponse
    ],
)
def get_system_assessments(
    agent_id: str | None = None,
    limit: int = 25,
    db: Session = Depends(
        get_db
    ),
):
    """
    Return system-security assessment batches.

    Historical individual test rows are deliberately not mixed
    together here. Each assessment represents one actual suite run.
    """

    limit = max(
        1,
        min(
            limit,
            100,
        ),
    )

    statement = (
        select(
            AssessmentRun
        )
        .where(
            AssessmentRun.assessment_type
            == "SYSTEM_ALL"
        )
    )

    if agent_id:
        statement = (
            statement.where(
                AssessmentRun.agent_id
                == agent_id
            )
        )

    statement = (
        statement
        .order_by(
            AssessmentRun
            .started_at
            .desc()
        )
        .limit(limit)
    )

    return db.scalars(
        statement
    ).all()


@router.get(
    "/assessments/latest",
    response_model=(
        AssessmentRunResponse
        | None
    ),
)
def get_latest_system_assessment(
    agent_id: str | None = None,
    db: Session = Depends(
        get_db
    ),
):
    """
    Return the newest system assessment.

    Supplying agent_id limits the lookup to a specific agent.
    """

    statement = (
        select(
            AssessmentRun
        )
        .where(
            AssessmentRun.assessment_type
            == "SYSTEM_ALL"
        )
    )

    if agent_id:
        statement = (
            statement.where(
                AssessmentRun.agent_id
                == agent_id
            )
        )

    statement = (
        statement
        .order_by(
            AssessmentRun
            .started_at
            .desc()
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
def get_system_assessment(
    assessment_run_id: str,
    db: Session = Depends(
        get_db
    ),
):
    """
    Return one system assessment batch.
    """

    assessment = db.get(
        AssessmentRun,
        assessment_run_id,
    )

    if assessment is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Assessment not found."
            ),
        )

    if (
        assessment.assessment_type
        != "SYSTEM_ALL"
    ):
        raise HTTPException(
            status_code=404,
            detail=(
                "System assessment not found."
            ),
        )

    return assessment


@router.get(
    "/assessments/{assessment_run_id}/results",
    response_model=list[
        SystemTestResultResponse
    ],
)
def get_system_assessment_results(
    assessment_run_id: str,
    db: Session = Depends(
        get_db
    ),
):
    """
    Return only the test results belonging to one assessment run.

    This prevents old failures from being presented as though they
    belong to the current assessment.
    """

    assessment = db.get(
        AssessmentRun,
        assessment_run_id,
    )

    if assessment is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Assessment not found."
            ),
        )

    if (
        assessment.assessment_type
        != "SYSTEM_ALL"
    ):
        raise HTTPException(
            status_code=404,
            detail=(
                "System assessment not found."
            ),
        )

    statement = (
        select(
            SystemSecurityTestResult
        )
        .where(
            SystemSecurityTestResult
            .assessment_run_id
            == assessment_run_id
        )
        .order_by(
            SystemSecurityTestResult
            .created_at
            .asc()
        )
    )

    return db.scalars(
        statement
    ).all()




def _reconcile_system_findings(
    *,
    db: Session,
    agent_id: str,
    results: list[SystemSecurityTestResult],
) -> None:
    """
    Update existing system-test findings when a later suite run
    re-exercises the same control. Findings are only auto-resolved
    after the operator has moved them to READY_FOR_RETEST.
    """

    findings = db.scalars(
        select(Finding).where(
            Finding.agent_id == agent_id
        )
    ).all()

    by_test_key: dict[str, Finding] = {}

    for finding in findings:
        evidence = finding.evidence or {}

        if evidence.get("source") != "system_test":
            continue

        test_key = evidence.get("test_key")

        if isinstance(test_key, str):
            by_test_key[test_key] = finding

    for result in results:
        finding = by_test_key.get(
            result.test_key
        )

        if finding is None:
            continue

        if finding.status != "READY_FOR_RETEST":
            continue

        new_evidence = dict(
            finding.evidence or {}
        )

        new_evidence["latest_retest"] = {
            "system_test_result_id": result.id,
            "assessment_run_id": result.assessment_run_id,
            "passed": result.passed,
            "expected_outcome": result.expected_outcome,
            "actual_outcome": result.actual_outcome,
            "timestamp": result.created_at.isoformat(),
        }

        finding.evidence = new_evidence

        if result.passed:
            finding.retest_status = "PASS"
            finding.status = "RESOLVED"
        else:
            finding.retest_status = "FAIL"
            finding.status = "IN_REMEDIATION"

        finding.updated_at = datetime.now(
            timezone.utc
        )



# -------------------------------------------------------------------
# RUN SYSTEM ASSESSMENT
# -------------------------------------------------------------------


@router.post(
    "/run-all",
    response_model=SystemTestBatchResponse,
)
def run_all_system_tests(
    payload: SystemTestRunRequest,
    db: Session = Depends(
        get_db
    ),
):
    """
    Execute the complete system-security suite.

    The supplied agent API key is used only for the assessment and is
    never persisted with the result batch.
    """

    agent = db.get(
        Agent,
        payload.agent_id,
    )

    if agent is None:
        raise HTTPException(
            status_code=404,
            detail="Agent not found.",
        )

    raw_agent_key = (
        payload.agent_api_key
        .get_secret_value()
    )

    authenticate_agent(
        db=db,
        agent_id=agent.id,
        api_key=raw_agent_key,
    )

    assessment = (
        start_assessment_run(
            db=db,
            agent_id=agent.id,
            assessment_type=(
                "SYSTEM_ALL"
            ),
            scope_key=None,
        )
    )

    # System tests intentionally make requests back into the running
    # ControlForge API. Persist the assessment first so those nested
    # requests can operate independently of this transaction.
    db.commit()
    db.refresh(
        assessment
    )

    assessment_id = (
        assessment.id
    )

    try:
        results = (
            run_system_test_suite(
                db=db,
                agent=agent,
                agent_key=(
                    raw_agent_key
                ),
                assessment_run_id=(
                    assessment_id
                ),
            )
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

        assessment = db.get(
            AssessmentRun,
            assessment_id,
        )

        if assessment is None:
            raise RuntimeError(
                "Assessment batch disappeared "
                "during system test execution."
            )

        complete_assessment_run(
            assessment=assessment,
            total=total,
            passed=passed,
            failed=failed,
        )

        _reconcile_system_findings(
            db=db,
            agent_id=agent.id,
            results=results,
        )

        db.commit()
        db.refresh(
            assessment
        )

        return SystemTestBatchResponse(
            assessment_run_id=(
                assessment.id
            ),
            agent_id=agent.id,
            total=total,
            passed=passed,
            failed=failed,
            results=results,
        )

    except Exception:
        db.rollback()

        assessment = db.get(
            AssessmentRun,
            assessment_id,
        )

        if assessment is not None:
            fail_assessment_run(
                assessment=assessment,
            )

            db.commit()

        raise
