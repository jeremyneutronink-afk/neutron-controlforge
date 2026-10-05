import "server-only";


const API_URL =
  process.env.AGENTGUARD_API_URL ??
  "http://127.0.0.1:8000";


export type SystemTestCatalogItem = {
  key: string;
  name: string;
  category: string;
  description: string;
  severity: string;
  expected_outcome: string;
};


export type SystemTestResult = {
  id: string;
  agent_id: string;

  assessment_run_id:
    | string
    | null;

  test_key: string;
  test_name: string;
  category: string;
  severity: string;

  expected_outcome: string;
  actual_outcome: string;

  passed: boolean;

  evidence: Record<
    string,
    unknown
  >;

  created_at: string;
};


export type AssessmentRun = {
  id: string;
  agent_id: string;

  assessment_type: string;

  scope_key:
    | string
    | null;

  status: string;

  total: number;
  passed: number;
  failed: number;

  started_at: string;

  completed_at:
    | string
    | null;
};


export type SystemTestBatch = {
  assessment_run_id: string;
  agent_id: string;

  total: number;
  passed: number;
  failed: number;

  results: SystemTestResult[];
};


function getAdminKey():
  | string
  | null {
  return (
    process.env.AGENTGUARD_ADMIN_KEY ??
    null
  );
}


async function readError(
  response: Response,
): Promise<string> {
  try {
    const body = await response.json();

    if (
      typeof body?.detail ===
      "string"
    ) {
      return body.detail;
    }

    return JSON.stringify(
      body
    );
  } catch {
    return (
      response.statusText ||
      "Request failed."
    );
  }
}


async function operatorFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const adminKey =
    getAdminKey();

  if (!adminKey) {
    throw new Error(
      "AGENTGUARD_ADMIN_KEY is not configured for the dashboard."
    );
  }

  const headers =
    new Headers(
      options?.headers
    );

  headers.set(
    "X-Admin-Key",
    adminKey
  );

  const response = await fetch(
    `${API_URL}${path}`,
    {
      cache: "no-store",
      ...options,
      headers,
    },
  );

  if (!response.ok) {
    throw new Error(
      await readError(
        response
      ),
    );
  }

  return response.json();
}


export async function getSystemTestCatalog():
  Promise<SystemTestCatalogItem[]> {
  return operatorFetch<
    SystemTestCatalogItem[]
  >(
    "/v1/system-tests/catalog"
  );
}


export async function getSystemTestResults(
  limit = 100,
): Promise<SystemTestResult[]> {
  return operatorFetch<
    SystemTestResult[]
  >(
    `/v1/system-tests/results?limit=${limit}`
  );
}


export async function getSystemAssessments(
  options?: {
    agentId?: string;
    limit?: number;
  },
): Promise<AssessmentRun[]> {
  const params =
    new URLSearchParams();

  params.set(
    "limit",
    String(
      options?.limit ?? 25
    ),
  );

  if (options?.agentId) {
    params.set(
      "agent_id",
      options.agentId,
    );
  }

  return operatorFetch<
    AssessmentRun[]
  >(
    `/v1/system-tests/assessments?${params.toString()}`
  );
}


export async function getLatestSystemAssessment(
  agentId?: string,
): Promise<AssessmentRun | null> {
  const params =
    new URLSearchParams();

  if (agentId) {
    params.set(
      "agent_id",
      agentId,
    );
  }

  const query =
    params.toString();

  return operatorFetch<
    AssessmentRun | null
  >(
    query
      ? `/v1/system-tests/assessments/latest?${query}`
      : "/v1/system-tests/assessments/latest"
  );
}


export async function getSystemAssessment(
  assessmentRunId: string,
): Promise<AssessmentRun> {
  return operatorFetch<
    AssessmentRun
  >(
    `/v1/system-tests/assessments/${assessmentRunId}`
  );
}


export async function getSystemAssessmentResults(
  assessmentRunId: string,
): Promise<SystemTestResult[]> {
  return operatorFetch<
    SystemTestResult[]
  >(
    `/v1/system-tests/assessments/${assessmentRunId}/results`
  );
}


export async function runSystemTestSuite(
  agentId: string,
  agentApiKey: string,
): Promise<SystemTestBatch> {
  return operatorFetch<
    SystemTestBatch
  >(
    "/v1/system-tests/run-all",
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body: JSON.stringify({
        agent_id:
          agentId,

        agent_api_key:
          agentApiKey,
      }),
    },
  );
}


/*
 * Keep the original dashboard action name working while the clearer
 * runSystemTestSuite() name remains available to new code.
 */
export async function runAllSystemTests(
  agentId: string,
  agentApiKey: string,
): Promise<SystemTestBatch> {
  return runSystemTestSuite(
    agentId,
    agentApiKey,
  );
}
