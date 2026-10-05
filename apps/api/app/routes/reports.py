from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.core.database import get_db
from apps.api.app.models import (
    Agent,
    AssessmentRun,
    Finding,
    SecurityTestResult,
    SystemSecurityTestResult,
)
from apps.api.app.services.auth import require_admin_key


router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
    dependencies=[Depends(require_admin_key)],
)


class ReportAssessment(BaseModel):
    id: str
    assessment_type: str
    status: str
    total: int
    passed: int
    failed: int
    started_at: datetime
    completed_at: datetime | None


class ReportTestResult(BaseModel):
    id: str
    test_key: str
    test_name: str
    category: str
    passed: bool
    expected: str
    actual: str
    severity: str | None = None
    evidence: dict[str, Any]


class ReportFinding(BaseModel):
    id: str
    title: str
    severity: str
    status: str
    description: str
    remediation: str | None
    retest_status: str | None
    evidence: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class AgentSecurityReport(BaseModel):
    generated_at: datetime

    agent_id: str
    agent_name: str
    agent_description: str | None

    overall_risk: str

    findings_total: int
    findings_open: int
    findings_resolved: int
    critical_open: int
    high_open: int

    latest_policy_assessment: ReportAssessment | None
    latest_system_assessment: ReportAssessment | None

    policy_results: list[ReportTestResult]
    system_results: list[ReportTestResult]
    findings: list[ReportFinding]


def _assessment_to_report(
    assessment: AssessmentRun | None,
) -> ReportAssessment | None:
    if assessment is None:
        return None

    return ReportAssessment(
        id=assessment.id,
        assessment_type=assessment.assessment_type,
        status=assessment.status,
        total=assessment.total,
        passed=assessment.passed,
        failed=assessment.failed,
        started_at=assessment.started_at,
        completed_at=assessment.completed_at,
    )


def _latest_policy_assessment(
    db: Session,
    agent_id: str,
) -> AssessmentRun | None:
    preferred = db.scalar(
        select(AssessmentRun)
        .where(
            AssessmentRun.agent_id == agent_id,
            AssessmentRun.assessment_type == "POLICY_ALL",
        )
        .order_by(AssessmentRun.started_at.desc())
        .limit(1)
    )

    if preferred is not None:
        return preferred

    return db.scalar(
        select(AssessmentRun)
        .where(
            AssessmentRun.agent_id == agent_id,
            AssessmentRun.assessment_type.in_(
                [
                    "POLICY_SINGLE",
                    "POLICY_PACK",
                    "POLICY_ALL",
                ]
            ),
        )
        .order_by(AssessmentRun.started_at.desc())
        .limit(1)
    )


def _latest_system_assessment(
    db: Session,
    agent_id: str,
) -> AssessmentRun | None:
    return db.scalar(
        select(AssessmentRun)
        .where(
            AssessmentRun.agent_id == agent_id,
            AssessmentRun.assessment_type == "SYSTEM_ALL",
        )
        .order_by(AssessmentRun.started_at.desc())
        .limit(1)
    )


def _policy_results(
    db: Session,
    assessment: AssessmentRun | None,
) -> list[ReportTestResult]:
    if assessment is None:
        return []

    rows = db.scalars(
        select(SecurityTestResult)
        .where(
            SecurityTestResult.assessment_run_id
            == assessment.id
        )
        .order_by(SecurityTestResult.created_at.asc())
    ).all()

    return [
        ReportTestResult(
            id=row.id,
            test_key=row.test_key,
            test_name=row.test_name,
            category=row.category,
            passed=row.passed,
            expected=row.expected_decision,
            actual=row.actual_decision,
            severity=str(
                row.evidence.get("severity")
                or row.evidence.get("risk")
                or "MEDIUM"
            ),
            evidence=row.evidence,
        )
        for row in rows
    ]


def _system_results(
    db: Session,
    assessment: AssessmentRun | None,
) -> list[ReportTestResult]:
    if assessment is None:
        return []

    rows = db.scalars(
        select(SystemSecurityTestResult)
        .where(
            SystemSecurityTestResult.assessment_run_id
            == assessment.id
        )
        .order_by(SystemSecurityTestResult.created_at.asc())
    ).all()

    return [
        ReportTestResult(
            id=row.id,
            test_key=row.test_key,
            test_name=row.test_name,
            category=row.category,
            passed=row.passed,
            expected=row.expected_outcome,
            actual=row.actual_outcome,
            severity=row.severity,
            evidence=row.evidence,
        )
        for row in rows
    ]


def _finding_rows(
    db: Session,
    agent_id: str,
) -> list[Finding]:
    return list(
        db.scalars(
            select(Finding)
            .where(Finding.agent_id == agent_id)
            .order_by(
                Finding.created_at.desc()
            )
        ).all()
    )


def _overall_risk(
    findings: list[Finding],
) -> str:
    open_findings = [
        finding
        for finding in findings
        if finding.status != "RESOLVED"
    ]

    if not open_findings:
        return "CLEAN"

    severities = {
        finding.severity
        for finding in open_findings
    }

    for severity in (
        "CRITICAL",
        "HIGH",
        "MEDIUM",
        "LOW",
    ):
        if severity in severities:
            return severity

    return "MEDIUM"


def build_agent_report(
    *,
    db: Session,
    agent_id: str,
) -> AgentSecurityReport:
    agent = db.get(Agent, agent_id)

    if agent is None:
        raise HTTPException(
            status_code=404,
            detail="Agent not found.",
        )

    policy_assessment = _latest_policy_assessment(
        db,
        agent_id,
    )
    system_assessment = _latest_system_assessment(
        db,
        agent_id,
    )

    findings = _finding_rows(
        db,
        agent_id,
    )

    open_findings = [
        finding
        for finding in findings
        if finding.status != "RESOLVED"
    ]

    report_findings = [
        ReportFinding(
            id=finding.id,
            title=finding.title,
            severity=finding.severity,
            status=finding.status,
            description=finding.description,
            remediation=finding.remediation,
            retest_status=finding.retest_status,
            evidence=finding.evidence,
            created_at=finding.created_at,
            updated_at=finding.updated_at,
        )
        for finding in findings
    ]

    return AgentSecurityReport(
        generated_at=datetime.now(timezone.utc),
        agent_id=agent.id,
        agent_name=agent.name,
        agent_description=agent.description,
        overall_risk=_overall_risk(findings),
        findings_total=len(findings),
        findings_open=len(open_findings),
        findings_resolved=(
            len(findings) - len(open_findings)
        ),
        critical_open=sum(
            1
            for finding in open_findings
            if finding.severity == "CRITICAL"
        ),
        high_open=sum(
            1
            for finding in open_findings
            if finding.severity == "HIGH"
        ),
        latest_policy_assessment=(
            _assessment_to_report(
                policy_assessment
            )
        ),
        latest_system_assessment=(
            _assessment_to_report(
                system_assessment
            )
        ),
        policy_results=_policy_results(
            db,
            policy_assessment,
        ),
        system_results=_system_results(
            db,
            system_assessment,
        ),
        findings=report_findings,
    )


@router.get(
    "/agent/{agent_id}",
    response_model=AgentSecurityReport,
)
def get_agent_report(
    agent_id: str,
    db: Session = Depends(get_db),
):
    return build_agent_report(
        db=db,
        agent_id=agent_id,
    )


def _fmt_dt(
    value: datetime | None,
) -> str:
    if value is None:
        return "—"

    return value.astimezone(
        timezone.utc
    ).strftime(
        "%Y-%m-%d %H:%M UTC"
    )


def _assessment_html(
    title: str,
    assessment: ReportAssessment | None,
) -> str:
    if assessment is None:
        return (
            f"<section><h2>{escape(title)}</h2>"
            "<p class='muted'>No assessment recorded.</p></section>"
        )

    return f"""
    <section>
      <h2>{escape(title)}</h2>
      <div class="metrics">
        <div><span>Passed</span><strong>{assessment.passed}</strong></div>
        <div><span>Failed</span><strong>{assessment.failed}</strong></div>
        <div><span>Total</span><strong>{assessment.total}</strong></div>
        <div><span>Status</span><strong>{escape(assessment.status)}</strong></div>
      </div>
      <p class="muted">Assessment {escape(assessment.id)} · Completed {_fmt_dt(assessment.completed_at or assessment.started_at)}</p>
    </section>
    """


def _tests_html(
    title: str,
    results: list[ReportTestResult],
) -> str:
    if not results:
        return (
            f"<section><h2>{escape(title)}</h2>"
            "<p class='muted'>No results recorded.</p></section>"
        )

    rows = []

    for result in results:
        outcome = "PASS" if result.passed else "FAIL"
        css = "pass" if result.passed else "fail"
        rows.append(
            "<tr>"
            f"<td>{escape(result.test_name)}</td>"
            f"<td>{escape(result.category)}</td>"
            f"<td>{escape(result.expected)}</td>"
            f"<td>{escape(result.actual)}</td>"
            f"<td class='{css}'>{outcome}</td>"
            "</tr>"
        )

    return f"""
    <section>
      <h2>{escape(title)}</h2>
      <table>
        <thead>
          <tr>
            <th>Test</th>
            <th>Category</th>
            <th>Expected</th>
            <th>Actual</th>
            <th>Result</th>
          </tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
      </table>
    </section>
    """


def _findings_html(
    findings: list[ReportFinding],
) -> str:
    if not findings:
        return (
            "<section><h2>Findings</h2>"
            "<p class='muted'>No findings recorded.</p></section>"
        )

    cards = []

    for finding in findings:
        remediation = (
            finding.remediation
            or "No remediation guidance recorded."
        )

        cards.append(
            f"""
            <article class="finding">
              <div class="finding-head">
                <h3>{escape(finding.title)}</h3>
                <span class="pill">{escape(finding.severity)}</span>
              </div>
              <p><strong>Status:</strong> {escape(finding.status)}</p>
              <p>{escape(finding.description)}</p>
              <p><strong>Remediation:</strong> {escape(remediation)}</p>
              <p><strong>Retest:</strong> {escape(finding.retest_status or 'NOT_RUN')}</p>
            </article>
            """
        )

    return (
        "<section><h2>Findings</h2>"
        + "".join(cards)
        + "</section>"
    )


def render_report_html(
    report: AgentSecurityReport,
) -> str:
    summary_text = (
        "No unresolved findings are currently recorded."
        if report.findings_open == 0
        else (
            f"{report.findings_open} unresolved finding(s) remain, "
            f"including {report.critical_open} critical and "
            f"{report.high_open} high severity finding(s)."
        )
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>ControlForge Security Report - {escape(report.agent_name)}</title>
<style>
  :root {{ color-scheme: light; }}
  body {{ font-family: Arial, Helvetica, sans-serif; margin: 0; color: #171717; background: #f5f5f5; }}
  main {{ max-width: 980px; margin: 0 auto; background: white; min-height: 100vh; padding: 48px; }}
  h1 {{ margin: 0; font-size: 30px; }}
  h2 {{ margin-top: 0; font-size: 20px; }}
  h3 {{ margin: 0; font-size: 16px; }}
  section {{ margin-top: 36px; }}
  .eyebrow {{ text-transform: uppercase; letter-spacing: .12em; font-size: 11px; color: #777; }}
  .muted {{ color: #666; font-size: 13px; }}
  .hero {{ border-bottom: 2px solid #111; padding-bottom: 28px; }}
  .risk {{ display: inline-block; margin-top: 14px; padding: 7px 10px; border: 1px solid #222; border-radius: 6px; font-weight: 700; }}
  .metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }}
  .metrics div {{ border: 1px solid #ddd; border-radius: 8px; padding: 14px; }}
  .metrics span {{ display: block; color: #777; font-size: 11px; text-transform: uppercase; }}
  .metrics strong {{ display: block; margin-top: 8px; font-size: 20px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  th, td {{ padding: 10px; border: 1px solid #ddd; text-align: left; vertical-align: top; }}
  th {{ background: #f2f2f2; }}
  .pass {{ font-weight: 700; }}
  .fail {{ font-weight: 700; }}
  .finding {{ border: 1px solid #ddd; border-radius: 8px; padding: 18px; margin-bottom: 14px; break-inside: avoid; }}
  .finding-head {{ display: flex; justify-content: space-between; gap: 16px; align-items: start; }}
  .pill {{ border: 1px solid #aaa; border-radius: 999px; padding: 4px 8px; font-size: 11px; }}
  .footer {{ margin-top: 48px; padding-top: 18px; border-top: 1px solid #ddd; color: #777; font-size: 11px; }}
  @media print {{
    body {{ background: white; }}
    main {{ max-width: none; padding: 0; }}
    @page {{ margin: 18mm; }}
  }}
</style>
</head>
<body>
<main>
  <header class="hero">
    <div class="eyebrow">Neutron ControlForge Security Assessment</div>
    <h1>{escape(report.agent_name)}</h1>
    <p class="muted">Generated {_fmt_dt(report.generated_at)} · Agent ID {escape(report.agent_id)}</p>
    <div class="risk">Overall Risk: {escape(report.overall_risk)}</div>
  </header>

  <section>
    <h2>Executive Summary</h2>
    <p>{escape(summary_text)}</p>
    <div class="metrics">
      <div><span>Open Findings</span><strong>{report.findings_open}</strong></div>
      <div><span>Resolved</span><strong>{report.findings_resolved}</strong></div>
      <div><span>Critical Open</span><strong>{report.critical_open}</strong></div>
      <div><span>High Open</span><strong>{report.high_open}</strong></div>
    </div>
  </section>

  {_assessment_html('Latest Policy Assessment', report.latest_policy_assessment)}
  {_tests_html('Policy Test Results', report.policy_results)}
  {_assessment_html('Latest System Assessment', report.latest_system_assessment)}
  {_tests_html('System Test Results', report.system_results)}
  {_findings_html(report.findings)}

  <div class="footer">
    Generated by Neutron ControlForge. This report reflects the latest persisted assessment and finding data available at generation time.
  </div>
</main>
</body>
</html>"""


@router.get(
    "/agent/{agent_id}/html",
    response_class=HTMLResponse,
)
def get_agent_report_html(
    agent_id: str,
    db: Session = Depends(get_db),
):
    report = build_agent_report(
        db=db,
        agent_id=agent_id,
    )

    return HTMLResponse(
        content=render_report_html(
            report
        )
    )
