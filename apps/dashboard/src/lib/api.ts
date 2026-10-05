import "server-only";


export type HealthResponse = {
  status: string;
  service: string;
  version: string;
  environment: string;
};

export type AgentResponse = {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  api_key_prefix: string | null;
};

export type AgentCredentialResponse =
  AgentResponse & {
    api_key: string;
  };

export type RunResponse = {
  id: string;
  agent_id: string;
  status: string;
  started_at: string;
  completed_at: string | null;
};

export type EventResponse = {
  id: string;
  run_id: string;
  agent_id: string;
  event_type: string;
  severity: string;
  message: string;
  event_data: Record<string, unknown>;
  created_at: string;
};

export type SecurityAuditEventResponse = {
  id: string;
  agent_id: string | null;
  event_type: string;
  severity: string;
  message: string;
  event_data: Record<string, unknown>;
  created_at: string;
};

export type DashboardApprovalResponse = {
  id: string;
  action_id: string;
  run_id: string;
  agent_id: string;

  agent_name: string;
  action_name: string;
  resource: string | null;
  arguments: Record<string, unknown>;

  status: string;
  reason: string;
  created_at: string;
};

export type ApprovalResponse = {
  id: string;
  action_id: string;
  run_id: string;
  agent_id: string;

  status:
    | "PENDING"
    | "APPROVED"
    | "DENIED";

  reason: string;

  created_at: string;
  resolved_at: string | null;
  resolved_by: string | null;
  resolution_note: string | null;
};

export type AssessmentRunResponse = {
  id: string;
  agent_id: string;

  assessment_type: string;
  scope_key: string | null;

  status: string;

  total: number;
  passed: number;
  failed: number;

  started_at: string;
  completed_at: string | null;
};

export type SecurityTestPackResponse = {
  key: string;
  name: string;
  description: string;
  category: string;
  test_count: number;
};

export type SecurityTestCatalogItem = {
  key: string;

  pack_key: string;
  pack_name: string;

  name: string;
  category: string;
  description: string;

  expected_decision: string;

  severity: string;
  remediation_hint: string;

  tags: string[];
};

export type SecurityTestResultResponse = {
  id: string;
  agent_id: string;

  assessment_run_id: string | null;

  test_key: string;
  test_name: string;
  category: string;

  expected_decision: string;
  actual_decision: string;

  passed: boolean;

  evidence: Record<
    string,
    unknown
  >;

  created_at: string;
};

export type SecurityTestBatchResponse = {
  assessment_run_id: string;

  scope: "PACK" | "ALL";
  scope_key: string | null;

  agent_id: string;

  total: number;
  passed: number;
  failed: number;

  results:
    SecurityTestResultResponse[];
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


async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T | null> {
  try {
    const response = await fetch(
      `${API_BASE_URL}${path}`,
      {
        cache: "no-store",
        ...options,
      }
    );

    if (!response.ok) {
      return null;
    }

    return (
      await response.json()
    ) as T;
  } catch {
    return null;
  }
}


async function operatorFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T | null> {
  const adminKey =
    getAdminKey();

  if (!adminKey) {
    return null;
  }

  const headers =
    new Headers(
      options?.headers
    );

  headers.set(
    "X-Admin-Key",
    adminKey
  );

  return apiFetch<T>(
    path,
    {
      ...options,
      headers,
    }
  );
}


export async function getHealth() {
  return apiFetch<HealthResponse>(
    "/health"
  );
}


export async function getAgents() {
  return operatorFetch<
    AgentResponse[]
  >(
    "/v1/agents"
  );
}


export async function createAgent(
  name: string,
  description: string | null
) {
  return operatorFetch<
    AgentCredentialResponse
  >(
    "/v1/agents",
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/json",
      },
      body: JSON.stringify({
        name,
        description,
      }),
    }
  );
}


export async function rotateAgentKey(
  agentId: string
) {
  return operatorFetch<
    AgentCredentialResponse
  >(
    `/v1/agents/${agentId}/rotate-key`,
    {
      method: "POST",
    }
  );
}


export async function getRuns() {
  return operatorFetch<
    RunResponse[]
  >(
    "/v1/runs"
  );
}


export async function getRun(
  runId: string
) {
  return operatorFetch<
    RunResponse
  >(
    `/v1/dashboard/runs/${runId}`
  );
}


export async function completeRun(
  runId: string,
  agentKey: string
) {
  return apiFetch<
    RunResponse
  >(
    `/v1/runs/${runId}/complete`,
    {
      method: "POST",
      headers: {
        "X-Agent-Key":
          agentKey,
      },
    }
  );
}


export async function getRunTimeline(
  runId: string
) {
  return operatorFetch<
    EventResponse[]
  >(
    `/v1/runs/${runId}/timeline`
  );
}


export async function getSecurityAuditEvents(
  limit = 12
) {
  return operatorFetch<
    SecurityAuditEventResponse[]
  >(
    `/v1/dashboard/security-audit?limit=${limit}`
  );
}


export async function getDashboardApprovals() {
  return operatorFetch<
    DashboardApprovalResponse[]
  >(
    "/v1/dashboard/approvals"
  );
}


export async function approveApproval(
  approvalId: string,
  resolvedBy: string,
  note: string | null
) {
  return operatorFetch<
    ApprovalResponse
  >(
    `/v1/approvals/${approvalId}/approve`,
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/json",
      },
      body: JSON.stringify({
        resolved_by:
          resolvedBy,
        note,
      }),
    }
  );
}


export async function denyApproval(
  approvalId: string,
  resolvedBy: string,
  note: string | null
) {
  return operatorFetch<
    ApprovalResponse
  >(
    `/v1/approvals/${approvalId}/deny`,
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/json",
      },
      body: JSON.stringify({
        resolved_by:
          resolvedBy,
        note,
      }),
    }
  );
}


export async function getSecurityTestPacks() {
  return operatorFetch<
    SecurityTestPackResponse[]
  >(
    "/v1/security-tests/packs"
  );
}


export async function getSecurityTestCatalog() {
  return operatorFetch<
    SecurityTestCatalogItem[]
  >(
    "/v1/security-tests/catalog"
  );
}


export async function getSecurityTestResults(
  limit = 100
) {
  return operatorFetch<
    SecurityTestResultResponse[]
  >(
    `/v1/security-tests/results?limit=${limit}`
  );
}


export async function getSecurityAssessments(
  options?: {
    agentId?: string;
    limit?: number;
  }
) {
  const params =
    new URLSearchParams();

  params.set(
    "limit",
    String(
      options?.limit ?? 25
    )
  );

  if (options?.agentId) {
    params.set(
      "agent_id",
      options.agentId
    );
  }

  return operatorFetch<
    AssessmentRunResponse[]
  >(
    `/v1/security-tests/assessments?${params.toString()}`
  );
}


export async function getLatestSecurityAssessment(
  agentId?: string
) {
  const params =
    new URLSearchParams();

  if (agentId) {
    params.set(
      "agent_id",
      agentId
    );
  }

  const query =
    params.toString();

  return operatorFetch<
    AssessmentRunResponse
  >(
    query
      ? `/v1/security-tests/assessments/latest?${query}`
      : "/v1/security-tests/assessments/latest"
  );
}


export async function getSecurityAssessmentResults(
  assessmentRunId: string
) {
  return operatorFetch<
    SecurityTestResultResponse[]
  >(
    `/v1/security-tests/assessments/${assessmentRunId}/results`
  );
}


export async function runSecurityTest(
  agentId: string,
  testKey: string
) {
  return operatorFetch<
    SecurityTestResultResponse
  >(
    "/v1/security-tests/run",
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/json",
      },
      body: JSON.stringify({
        agent_id: agentId,
        test_key: testKey,
      }),
    }
  );
}


export async function runSecurityTestPack(
  agentId: string,
  packKey: string
) {
  return operatorFetch<
    SecurityTestBatchResponse
  >(
    "/v1/security-tests/run-pack",
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/json",
      },
      body: JSON.stringify({
        agent_id: agentId,
        pack_key: packKey,
      }),
    }
  );
}


export async function runAllSecurityTests(
  agentId: string
) {
  return operatorFetch<
    SecurityTestBatchResponse
  >(
    "/v1/security-tests/run-all",
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/json",
      },
      body: JSON.stringify({
        agent_id: agentId,
      }),
    }
  );
}
