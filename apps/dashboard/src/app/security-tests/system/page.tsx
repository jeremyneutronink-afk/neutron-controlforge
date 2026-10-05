import Link from "next/link";
import {
  revalidatePath,
} from "next/cache";

import {
  getAgents,
} from "@/lib/api";

import {
  FindingResponse,
  createFindingFromSystemTest,
  getFindings,
} from "@/lib/findings-api";

import {
  AssessmentRun,
  SystemTestResult,
  getLatestSystemAssessment,
  getSystemAssessmentResults,
  getSystemAssessments,
  getSystemTestCatalog,
  runAllSystemTests,
} from "@/lib/system-tests-api";


async function runSuiteAction(
  formData: FormData
) {
  "use server";

  const agentId = String(
    formData.get("agent_id") ?? ""
  );

  const agentApiKey = String(
    formData.get("agent_api_key") ?? ""
  ).trim();

  if (
    !agentId ||
    !agentApiKey
  ) {
    return;
  }

  await runAllSystemTests(
    agentId,
    agentApiKey
  );

  revalidatePath(
    "/security-tests/system"
  );

  revalidatePath(
    "/security-tests"
  );

  revalidatePath(
    "/runs"
  );

  revalidatePath("/");
}


async function createSystemFindingAction(
  formData: FormData
) {
  "use server";

  const testResultId = String(
    formData.get("test_result_id") ?? ""
  );

  if (!testResultId) {
    return;
  }

  await createFindingFromSystemTest(
    testResultId
  );

  revalidatePath(
    "/security-tests/system"
  );

  revalidatePath(
    "/findings"
  );

  revalidatePath(
    "/reports"
  );
}


export default async function SystemTestsPage() {
  const [
    agents,
    catalog,
    latestAssessment,
    assessmentHistory,
    findings,
  ] = await Promise.all([
    getAgents(),
    getSystemTestCatalog(),
    getLatestSystemAssessment(),
    getSystemAssessments({
      limit: 12,
    }),
    getFindings(),
  ]);

  const safeAgents =
    agents ?? [];

  const safeCatalog =
    catalog ?? [];

  const safeHistory =
    assessmentHistory ?? [];

  const safeFindings =
    findings ?? [];

  const findingBySystemTestResult =
    new Map<string, FindingResponse>();

  for (const finding of safeFindings) {
    const source =
      finding.evidence?.source;

    const resultId =
      finding.evidence?.system_test_result_id;

    if (
      source === "system_test" &&
      typeof resultId === "string"
    ) {
      findingBySystemTestResult.set(
        resultId,
        finding
      );
    }
  }

  const latestResults =
    latestAssessment
      ? await getSystemAssessmentResults(
          latestAssessment.id
        )
      : [];

  const agentMap =
    new Map(
      safeAgents.map(
        (agent) => [
          agent.id,
          agent.name,
        ]
      )
    );

  return (
    <div className="min-h-screen">
      <header className="border-b border-zinc-800 px-8 py-6">
        <div className="flex flex-wrap items-start justify-between gap-5">
          <div>
            <Link
              href="/security-tests"
              className="text-sm text-zinc-500 transition hover:text-white"
            >
              ← Policy Tests
            </Link>

            <h1 className="mt-4 text-xl font-semibold text-white">
              System Security Tests
            </h1>

            <p className="mt-1 max-w-3xl text-sm leading-6 text-zinc-500">
              Exercise ControlForge through its
              real HTTP authentication,
              authorization, replay protection,
              lifecycle, approval, and execution
              boundaries.
            </p>
          </div>

          {latestAssessment ? (
            <div className="flex gap-2">
              <Metric
                label="Passed"
                value={
                  latestAssessment.passed
                }
                type="pass"
              />

              <Metric
                label="Failed"
                value={
                  latestAssessment.failed
                }
                type="fail"
              />

              <Metric
                label="Total"
                value={
                  latestAssessment.total
                }
                type="neutral"
              />
            </div>
          ) : null}
        </div>
      </header>

      <div className="space-y-10 p-8">
        <section className="rounded-xl border border-red-900/40 bg-red-950/10 p-6">
          <div className="text-xs font-medium uppercase tracking-wide text-red-400">
            Adversarial Harness
          </div>

          <h2 className="mt-2 text-lg font-semibold text-white">
            Run System Attack Suite
          </h2>

          <p className="mt-2 max-w-3xl text-sm leading-6 text-zinc-500">
            Each execution is stored as one
            assessment batch. The supplied
            agent credential is used only during
            the run and is not written to test
            evidence or persisted as plaintext.
          </p>

          {safeAgents.length === 0 ? (
            <div className="mt-6 rounded-lg border border-zinc-800 bg-black p-4 text-sm text-zinc-500">
              Register an agent before running
              the system suite.
            </div>
          ) : (
            <form
              action={runSuiteAction}
              className="mt-6 grid gap-4 lg:grid-cols-[1fr_2fr_auto] lg:items-end"
            >
              <label>
                <FieldLabel>
                  Target Agent
                </FieldLabel>

                <select
                  name="agent_id"
                  required
                  defaultValue={
                    safeAgents[0]?.id
                  }
                  className="w-full rounded-lg border border-zinc-700 bg-black px-3 py-2.5 text-sm text-white outline-none focus:border-cyan-700"
                >
                  {safeAgents.map(
                    (agent) => (
                      <option
                        key={agent.id}
                        value={agent.id}
                      >
                        {agent.name}
                      </option>
                    )
                  )}
                </select>
              </label>

              <label>
                <FieldLabel>
                  Agent API Key
                </FieldLabel>

                <input
                  type="password"
                  name="agent_api_key"
                  autoComplete="off"
                  required
                  placeholder="agk_..."
                  className="w-full rounded-lg border border-zinc-700 bg-black px-3 py-2.5 text-sm text-white outline-none placeholder:text-zinc-700 focus:border-cyan-700"
                />
              </label>

              <button
                type="submit"
                className="rounded-lg border border-red-800 bg-red-950 px-5 py-2.5 text-sm font-medium text-red-300 transition hover:bg-red-900"
              >
                Run Attack Suite
              </button>
            </form>
          )}
        </section>

        <section>
          <SectionHeading
            title="Latest Assessment"
            description={
              latestAssessment
                ? "Only results from the newest assessment batch are counted here."
                : "Run the system suite to create the first assessment."
            }
          />

          {!latestAssessment ? (
            <EmptyState>
              No system assessment has been
              completed yet.
            </EmptyState>
          ) : (
            <div className="space-y-4">
              <AssessmentSummary
                assessment={
                  latestAssessment
                }
                agentName={
                  agentMap.get(
                    latestAssessment.agent_id
                  ) ??
                  latestAssessment.agent_id
                }
              />

              <div className="grid gap-4 xl:grid-cols-2">
                {latestResults.map(
                  (result) => (
                    <ResultCard
                      key={result.id}
                      result={result}
                      finding={
                        findingBySystemTestResult.get(
                          result.id
                        )
                      }
                    />
                  )
                )}
              </div>
            </div>
          )}
        </section>

        <section>
          <SectionHeading
            title="Assessment History"
            description="Previous suite executions remain available as separate batches instead of being mixed into the current score."
          />

          {safeHistory.length === 0 ? (
            <EmptyState>
              No assessment history yet.
            </EmptyState>
          ) : (
            <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950">
              <div className="grid grid-cols-[minmax(0,2fr)_1fr_1fr_1fr_1.5fr] gap-4 border-b border-zinc-800 px-5 py-3 text-xs uppercase tracking-wide text-zinc-600">
                <div>Assessment</div>
                <div>Passed</div>
                <div>Failed</div>
                <div>Status</div>
                <div>Completed</div>
              </div>

              {safeHistory.map(
                (assessment) => (
                  <div
                    key={assessment.id}
                    className="grid grid-cols-[minmax(0,2fr)_1fr_1fr_1fr_1.5fr] gap-4 border-b border-zinc-900 px-5 py-4 text-sm last:border-b-0"
                  >
                    <div>
                      <div className="font-medium text-zinc-200">
                        {
                          agentMap.get(
                            assessment.agent_id
                          ) ??
                          "Unknown agent"
                        }
                      </div>

                      <div className="mt-1 font-mono text-xs text-zinc-600">
                        {shortId(
                          assessment.id
                        )}
                      </div>
                    </div>

                    <div className="text-emerald-400">
                      {assessment.passed}
                    </div>

                    <div
                      className={
                        assessment.failed > 0
                          ? "text-red-400"
                          : "text-zinc-500"
                      }
                    >
                      {assessment.failed}
                    </div>

                    <div>
                      <StatusBadge
                        status={
                          assessment.status
                        }
                      />
                    </div>

                    <div className="text-zinc-500">
                      {formatDate(
                        assessment.completed_at ??
                        assessment.started_at
                      )}
                    </div>
                  </div>
                )
              )}
            </div>
          )}
        </section>

        <section>
          <SectionHeading
            title="System Test Catalog"
            description="The current attack scenarios executed against the running control plane."
          />

          <div className="grid gap-4 xl:grid-cols-2">
            {safeCatalog.map(
              (test) => (
                <div
                  key={test.key}
                  className="rounded-xl border border-zinc-800 bg-zinc-950 p-6"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="text-xs font-medium uppercase tracking-wide text-cyan-500">
                        {test.category}
                      </div>

                      <h3 className="mt-2 font-semibold text-white">
                        {test.name}
                      </h3>
                    </div>

                    <SeverityBadge
                      severity={
                        test.severity
                      }
                    />
                  </div>

                  <p className="mt-3 text-sm leading-6 text-zinc-500">
                    {test.description}
                  </p>

                  <div className="mt-5 border-t border-zinc-800 pt-4">
                    <div className="text-xs text-zinc-600">
                      Expected Outcome
                    </div>

                    <div className="mt-2 font-mono text-sm text-zinc-300">
                      {
                        test.expected_outcome
                      }
                    </div>
                  </div>
                </div>
              )
            )}
          </div>
        </section>
      </div>
    </div>
  );
}


function AssessmentSummary({
  assessment,
  agentName,
}: {
  assessment: AssessmentRun;
  agentName: string;
}) {
  const clean =
    assessment.failed === 0 &&
    assessment.status ===
      "COMPLETED";

  return (
    <div
      className={
        clean
          ? "rounded-xl border border-emerald-900/50 bg-emerald-950/10 p-6"
          : "rounded-xl border border-red-900/50 bg-red-950/10 p-6"
      }
    >
      <div className="flex flex-wrap items-start justify-between gap-5">
        <div>
          <div
            className={
              clean
                ? "text-xs font-medium uppercase tracking-wide text-emerald-400"
                : "text-xs font-medium uppercase tracking-wide text-red-400"
            }
          >
            {clean
              ? "Controls Verified"
              : "Attention Required"}
          </div>

          <h3 className="mt-2 text-lg font-semibold text-white">
            {assessment.passed}/
            {assessment.total} tests
            passed
          </h3>

          <div className="mt-2 text-sm text-zinc-500">
            {agentName}
          </div>
        </div>

        <div className="text-right text-xs text-zinc-600">
          <div>
            {formatDate(
              assessment.completed_at ??
              assessment.started_at
            )}
          </div>

          <div className="mt-2 font-mono">
            {assessment.id}
          </div>
        </div>
      </div>
    </div>
  );
}


function ResultCard({
  result,
  finding,
}: {
  result: SystemTestResult;
  finding?: FindingResponse;
}) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <ResultBadge
              passed={
                result.passed
              }
            />

            <SeverityBadge
              severity={
                result.severity
              }
            />

            <span className="rounded-full border border-zinc-700 bg-zinc-900 px-2.5 py-1 text-xs text-zinc-400">
              {result.category}
            </span>
          </div>

          <h3 className="mt-3 font-semibold text-white">
            {result.test_name}
          </h3>
        </div>

        <div className="font-mono text-xs text-zinc-500">
          {result.expected_outcome}
          {" → "}
          {result.actual_outcome}
        </div>
      </div>

      <details className="mt-5 border-t border-zinc-800 pt-4">
        <summary className="cursor-pointer text-sm text-zinc-500 transition hover:text-zinc-300">
          View evidence
        </summary>

        <pre className="mt-3 overflow-x-auto rounded-lg border border-zinc-800 bg-black p-4 text-xs leading-6 text-zinc-400">
          {JSON.stringify(
            result.evidence,
            null,
            2
          )}
        </pre>
      </details>

      {!result.passed && (
        <div className="mt-5 border-t border-zinc-800 pt-4">
          {finding ? (
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <div className="text-sm font-medium text-amber-300">
                  Finding created
                </div>

                <div className="mt-1 text-xs text-zinc-600">
                  {finding.status.replaceAll(
                    "_",
                    " "
                  )}
                </div>
              </div>

              <Link
                href="/findings"
                className="text-sm text-cyan-400 transition hover:text-cyan-300"
              >
                View Finding →
              </Link>
            </div>
          ) : (
            <form
              action={createSystemFindingAction}
            >
              <input
                type="hidden"
                name="test_result_id"
                value={result.id}
              />

              <button
                type="submit"
                className="rounded-lg border border-amber-800 bg-amber-950 px-4 py-2 text-sm font-medium text-amber-300 transition hover:bg-amber-900"
              >
                Create Finding
              </button>
            </form>
          )}
        </div>
      )}
    </div>
  );
}


function SectionHeading({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="mb-4">
      <h2 className="text-sm font-medium text-zinc-300">
        {title}
      </h2>

      <p className="mt-1 max-w-3xl text-sm text-zinc-600">
        {description}
      </p>
    </div>
  );
}


function EmptyState({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-dashed border-zinc-800 p-10 text-center text-sm text-zinc-500">
      {children}
    </div>
  );
}


function FieldLabel({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="mb-2 text-xs font-medium text-zinc-500">
      {children}
    </div>
  );
}


function Metric({
  label,
  value,
  type,
}: {
  label: string;
  value: number;
  type:
    | "pass"
    | "fail"
    | "neutral";
}) {
  const style =
    type === "pass"
      ? "border-emerald-900 bg-emerald-950 text-emerald-400"
      : type === "fail"
        ? "border-red-900 bg-red-950 text-red-400"
        : "border-zinc-800 bg-zinc-950 text-zinc-300";

  return (
    <div
      className={`rounded-lg border px-3 py-2 ${style}`}
    >
      <div className="text-[10px] uppercase tracking-wide opacity-70">
        {label}
      </div>

      <div className="mt-1 text-lg font-semibold">
        {value}
      </div>
    </div>
  );
}


function ResultBadge({
  passed,
}: {
  passed: boolean;
}) {
  return (
    <span
      className={
        passed
          ? "rounded-full border border-emerald-900 bg-emerald-950 px-2.5 py-1 text-xs font-semibold text-emerald-400"
          : "rounded-full border border-red-900 bg-red-950 px-2.5 py-1 text-xs font-semibold text-red-400"
      }
    >
      {passed
        ? "PASS"
        : "FAIL"}
    </span>
  );
}


function StatusBadge({
  status,
}: {
  status: string;
}) {
  const style =
    status === "COMPLETED"
      ? "border-emerald-900 bg-emerald-950 text-emerald-400"
      : status === "FAILED"
        ? "border-red-900 bg-red-950 text-red-400"
        : "border-amber-900 bg-amber-950 text-amber-400";

  return (
    <span
      className={`rounded-full border px-2.5 py-1 text-xs font-medium ${style}`}
    >
      {status}
    </span>
  );
}


function SeverityBadge({
  severity,
}: {
  severity: string;
}) {
  const style =
    severity === "CRITICAL"
      ? "border-red-800 bg-red-950 text-red-300"
      : severity === "HIGH"
        ? "border-red-900 bg-red-950 text-red-400"
        : severity === "MEDIUM"
          ? "border-amber-900 bg-amber-950 text-amber-400"
          : "border-zinc-700 bg-zinc-900 text-zinc-400";

  return (
    <span
      className={`rounded-full border px-2.5 py-1 text-xs font-medium ${style}`}
    >
      {severity}
    </span>
  );
}


function shortId(
  value: string
) {
  if (
    value.length <= 12
  ) {
    return value;
  }

  return `${value.slice(0, 8)}…`;
}


function formatDate(
  value: string
) {
  return new Intl.DateTimeFormat(
    "en-US",
    {
      dateStyle: "medium",
      timeStyle: "short",
    }
  ).format(
    new Date(value)
  );
}
