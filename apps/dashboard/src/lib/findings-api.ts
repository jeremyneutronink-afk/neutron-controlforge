import "server-only";


export type FindingSeverity =
  | "LOW"
  | "MEDIUM"
  | "HIGH"
  | "CRITICAL";

export type FindingStatus =
  | "OPEN"
  | "IN_REMEDIATION"
  | "READY_FOR_RETEST"
  | "RESOLVED";

export type FindingResponse = {
  id: string;
  agent_id: string;

  source_test_result_id:
    | string
    | null;

  title: string;

  severity: FindingSeverity;
  status: FindingStatus;

  description: string;

  evidence: Record<
    string,
    unknown
  >;

  remediation: string | null;

  retest_status:
    | string
    | null;

  created_at: string;
  updated_at: string;
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


async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T | null> {
  const adminKey =
    getAdminKey();

  if (!adminKey) {
    return null;
  }

  try {
    const headers =
      new Headers(
        options?.headers
      );

    headers.set(
      "X-Admin-Key",
      adminKey
    );

    const response = await fetch(
      `${API_BASE_URL}${path}`,
      {
        cache: "no-store",
        ...options,
        headers,
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


export async function getFindings() {
  return request<
    FindingResponse[]
  >(
    "/v1/findings"
  );
}


export async function createFinding(
  agentId: string,
  title: string,
  severity: FindingSeverity,
  description: string,
  remediation: string | null
) {
  return request<FindingResponse>(
    "/v1/findings",
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/json",
      },
      body: JSON.stringify({
        agent_id: agentId,
        title,
        severity,
        description,
        remediation,
      }),
    }
  );
}


export async function updateFinding(
  findingId: string,
  data: {
    status?: FindingStatus;
    severity?: FindingSeverity;
    remediation?: string;
    retest_status?: string;
  }
) {
  return request<FindingResponse>(
    `/v1/findings/${findingId}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type":
          "application/json",
      },
      body: JSON.stringify(
        data
      ),
    }
  );
}


export async function createFindingFromTest(
  testResultId: string
) {
  return request<FindingResponse>(
    `/v1/findings/from-test/${testResultId}`,
    {
      method: "POST",
    }
  );
}


export async function createFindingFromSystemTest(
  testResultId: string
) {
  return request<FindingResponse>(
    `/v1/findings/from-system-test/${testResultId}`,
    {
      method: "POST",
    }
  );
}


export async function retestFinding(
  findingId: string
) {
  return request<FindingResponse>(
    `/v1/findings/${findingId}/retest`,
    {
      method: "POST",
    }
  );
}
