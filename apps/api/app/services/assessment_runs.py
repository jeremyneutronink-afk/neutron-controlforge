from datetime import datetime, timezone

from sqlalchemy.orm import Session

from apps.api.app.models import AssessmentRun


def start_assessment_run(
    *,
    db: Session,
    agent_id: str,
    assessment_type: str,
    scope_key: str | None = None,
) -> AssessmentRun:
    """
    Create a persistent assessment batch.

    The batch begins in RUNNING state and is finalized only after
    all associated tests have finished.
    """

    assessment = AssessmentRun(
        agent_id=agent_id,
        assessment_type=assessment_type,
        scope_key=scope_key,
        status="RUNNING",
        total=0,
        passed=0,
        failed=0,
    )

    db.add(assessment)
    db.flush()

    return assessment


def complete_assessment_run(
    *,
    assessment: AssessmentRun,
    total: int,
    passed: int,
    failed: int,
) -> AssessmentRun:
    """
    Finalize an assessment after all test results are available.
    """

    assessment.status = "COMPLETED"
    assessment.total = total
    assessment.passed = passed
    assessment.failed = failed
    assessment.completed_at = datetime.now(
        timezone.utc
    )

    return assessment


def fail_assessment_run(
    *,
    assessment: AssessmentRun,
    total: int = 0,
    passed: int = 0,
    failed: int = 0,
) -> AssessmentRun:
    """
    Mark a batch as FAILED when the assessment process itself fails.

    This is different from a completed assessment containing failed
    security tests.
    """

    assessment.status = "FAILED"
    assessment.total = total
    assessment.passed = passed
    assessment.failed = failed
    assessment.completed_at = datetime.now(
        timezone.utc
    )

    return assessment