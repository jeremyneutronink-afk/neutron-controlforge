import "server-only";


export type ReportAssessment = {
  id: string;
  assessment_type: string;
  status: string;
  total: number;
  passed: number;
  failed: number;
  started_at: string;
  completed_at: string | null;
};

export type ReportTestResult = {
  id: string;
  test_key: string;
  test_name: string;
  category: string;
  passed: boolean;
  expected: string;
  actual: string;
  severity: string | null;
  evidence: Record<string, unknown>;
};

export type ReportFinding = {
  id: string;
  title: string;
  severity: string;
  status: string;
  description: string;
  remediation: string | null;
  retest_status: string | null;
  evidence: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type AgentSecurityReport = {
  generated_at: string;

  agent_id: string;
  agent_name: string;
  agent_description: string | null;

  overall_risk: string;

  findings_total: number;
  findings_open: number;
  findings_resolved: number;
  critical_open: number;
  high_open: number;

  latest_policy_assessment:
    | ReportAssessment
    | null;

  latest_system_assessment:
    | ReportAssessment
    | null;

  policy_results: ReportTestResult[];
  system_results: ReportTestResult[];
  findings: ReportFinding[];
};


const API_BASE_URL =
  process.env.AGENTGUARD_API_URL ??
  "http://127.0.0.1:8000";


function getAdminKey():
  | string
  | null {
  return (
    process.env.AGENTGUARD_ADMIN_KEY ??
    null
  );
}


export async function getAgentSecurityReport(
  agentId: string
): Promise<AgentSecurityReport | null> {
  const adminKey =
    getAdminKey();

  if (!adminKey) {
    return null;
  }

  try {
    const response = await fetch(
      `${API_BASE_URL}/v1/reports/agent/${agentId}`,
      {
        cache: "no-store",
        headers: {
          "X-Admin-Key": adminKey,
        },
      }
    );

    if (!response.ok) {
      return null;
    }

    return (
      await response.json()
    ) as AgentSecurityReport;
  } catch {
    return null;
  }
}
