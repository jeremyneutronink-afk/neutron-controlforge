import {
  revalidatePath,
} from "next/cache";

import {
  getAgents,
  getLatestSecurityAssessment,
  getSecurityAssessmentResults,
  getSecurityAssessments,
  getSecurityTestCatalog,
  getSecurityTestPacks,
  runAllSecurityTests,
  runSecurityTest,
  runSecurityTestPack,
} from "@/lib/api";

import {
  createFindingFromTest,
  getFindings,
} from "@/lib/findings-api";


async function runTestAction(
  formData: FormData
) {
  "use server";

  const agentId = String(
    formData.get("agent_id") ??
      ""
  );

  const testKey = String(
    formData.get("test_key") ??
      ""
  );

  if (
    !agentId ||
    !testKey
  ) {
    return;
  }

  await runSecurityTest(
    agentId,
    testKey
  );

  revalidatePath(
    "/security-tests"
  );
}


async function runPackAction(
  formData: FormData
) {
  "use server";

  const agentId = String(
    formData.get("agent_id") ??
      ""
  );

  const packKey = String(
    formData.get("pack_key") ??
      ""
  );

  if (
    !agentId ||
    !packKey
  ) {
    return;
  }

  await runSecurityTestPack(
    agentId,
    packKey
  );

  revalidatePath(
    "/security-tests"
  );
}


async function runAllAction(
  formData: FormData
) {
  "use server";

  const agentId = String(
    formData.get("agent_id") ??
      ""
  );

  if (!agentId) {
    return;
  }

  await runAllSecurityTests(
    agentId
  );

  revalidatePath(
    "/security-tests"
  );
}


async function createFindingAction(
  formData: FormData
) {
  "use server";

  const testResultId = String(
    formData.get(
      "test_result_id"
    ) ?? ""
  );

  if (!testResultId) {
    return;
  }

  await createFindingFromTest(
    testResultId
  );

  revalidatePath(
    "/security-tests"
  );

  revalidatePath(
    "/findings"
  );
}


export default async function SecurityTestsPage() {
  const [
    agents,
    packs,
    catalog,
    latestAssessment,
    assessmentHistory,
    findings,
  ] = await Promise.all([
    getAgents(),
    getSecurityTestPacks(),
    getSecurityTestCatalog(),
    getLatestSecurityAssessment(),
    getSecurityAssessments({
      limit: 12,
    }),
    getFindings(),
  ]);

  const safeAgents =
    agents ?? [];

  const safePacks =
    packs ?? [];

  const safeCatalog =
    catalog ?? [];

  const latestResults =
    latestAssessment
      ? (
          await getSecurityAssessmentResults(
            latestAssessment.id
          )
        ) ?? []
      : [];

  const safeHistory =
    assessmentHistory ?? [];

  const safeFindings =
    findings ?? [];

  const findingByTestResult =
    new Map(
      safeFindings
        .filter(
          (finding) =>
            finding.source_test_result_id
        )
        .map(
          (finding) => [
            finding.source_test_result_id,
            finding,
          ]
        )
    );

  const agentMap =
    new Map(
      safeAgents.map(
        (agent) => [
          agent.id,
          agent,
        ]
      )
    );

  const recentResults =
    latestResults;

  const passedCount =
    latestAssessment?.passed ??
    0;

  const failedCount =
    latestAssessment?.failed ??
    0;

  return (
    <div className="min-h-screen">
      <header className="border-b border-zinc-800 px-8 py-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold text-white">
              Security Tests
            </h1>

            <p className="mt-1 text-sm text-zinc-500">
              Run reusable adversarial
              assessment packs and policy
              regression scenarios.
            </p>
          </div>

          <div className="flex gap-2">
            <SummaryBadge
              label="Passed"
              value={passedCount}
              type="pass"
            />

            <SummaryBadge
              label="Failed"
              value={failedCount}
              type="fail"
            />
          </div>
        </div>
      </header>

      <div className="p-8">
        {safeAgents.length > 0 && (
          <section className="mb-10 rounded-xl border border-cyan-900/40 bg-cyan-950/10 p-6">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <div className="text-xs font-medium uppercase tracking-wide text-cyan-500">
                  Full Regression Suite
                </div>

                <h2 className="mt-2 text-lg font-semibold text-white">
                  Run All Security Tests
                </h2>

                <p className="mt-2 max-w-2xl text-sm leading-6 text-zinc-500">
                  Execute every active
                  policy-layer scenario and
                  persist the complete result
                  set for regression analysis.
                </p>
              </div>

              <form
                action={
                  runAllAction
                }
                className="flex flex-col gap-3 sm:flex-row"
              >
                <select
                  name="agent_id"
                  required
                  className="rounded-lg border border-zinc-700 bg-black px-3 py-2.5 text-sm text-white"
                  defaultValue={
                    safeAgents[0]?.id
                  }
                >
                  {safeAgents.map(
                    (agent) => (
                      <option
                        key={
                          agent.id
                        }
                        value={
                          agent.id
                        }
                      >
                        {
                          agent.name
                        }
                      </option>
                    )
                  )}
                </select>

                <button
                  type="submit"
                  className="rounded-lg border border-cyan-700 bg-cyan-950 px-5 py-2.5 text-sm font-medium text-cyan-300 transition hover:bg-cyan-900"
                >
                  Run Full Suite
                </button>
              </form>
            </div>
          </section>
        )}

        <section>
          <div className="mb-4">
            <h2 className="text-sm font-medium text-zinc-300">
              Assessment Packs
            </h2>

            <p className="mt-1 text-sm text-zinc-600">
              Run related groups of tests
              against a selected agent.
            </p>
          </div>

          <div className="grid gap-4 xl:grid-cols-3">
            {safePacks.map(
              (pack) => {
                const packTests =
                  safeCatalog.filter(
                    (test) =>
                      test.pack_key ===
                      pack.key
                  );

                return (
                  <div
                    key={
                      pack.key
                    }
                    className="rounded-xl border border-zinc-800 bg-zinc-950 p-6"
                  >
                    <div className="text-xs font-medium uppercase tracking-wide text-cyan-500">
                      {
                        pack.category
                      }
                    </div>

                    <h3 className="mt-2 text-lg font-semibold text-white">
                      {pack.name}
                    </h3>

                    <p className="mt-2 min-h-20 text-sm leading-6 text-zinc-500">
                      {
                        pack.description
                      }
                    </p>

                    <div className="mt-4 text-xs text-zinc-600">
                      {
                        pack.test_count
                      }{" "}
                      scenarios
                    </div>

                    <div className="mt-4 flex flex-wrap gap-2">
                      {packTests.map(
                        (test) => (
                          <span
                            key={
                              test.key
                            }
                            className="rounded-full border border-zinc-800 bg-black px-2.5 py-1 text-xs text-zinc-500"
                          >
                            {
                              test.name
                            }
                          </span>
                        )
                      )}
                    </div>

                    {safeAgents.length > 0 && (
                      <form
                        action={
                          runPackAction
                        }
                        className="mt-6 border-t border-zinc-800 pt-5"
                      >
                        <input
                          type="hidden"
                          name="pack_key"
                          value={
                            pack.key
                          }
                        />

                        <select
                          name="agent_id"
                          required
                          className="w-full rounded-lg border border-zinc-700 bg-black px-3 py-2.5 text-sm text-white"
                          defaultValue={
                            safeAgents[0]?.id
                          }
                        >
                          {safeAgents.map(
                            (agent) => (
                              <option
                                key={
                                  agent.id
                                }
                                value={
                                  agent.id
                                }
                              >
                                {
                                  agent.name
                                }
                              </option>
                            )
                          )}
                        </select>

                        <button
                          type="submit"
                          className="mt-3 w-full rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2.5 text-sm text-zinc-300 transition hover:border-cyan-800 hover:text-cyan-300"
                        >
                          Run Pack
                        </button>
                      </form>
                    )}
                  </div>
                );
              }
            )}
          </div>
        </section>

        <section className="mt-12">
          <div className="mb-4">
            <h2 className="text-sm font-medium text-zinc-300">
              Scenario Catalog
            </h2>

            <p className="mt-1 text-sm text-zinc-600">
              Run individual scenarios or
              inspect their expected security
              behavior.
            </p>
          </div>

          <div className="grid gap-4 xl:grid-cols-2">
            {safeCatalog.map(
              (test) => (
                <form
                  key={
                    test.key
                  }
                  action={
                    runTestAction
                  }
                  className="rounded-xl border border-zinc-800 bg-zinc-950 p-6"
                >
                  <input
                    type="hidden"
                    name="test_key"
                    value={
                      test.key
                    }
                  />

                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="flex flex-wrap gap-2">
                        <span className="text-xs font-medium uppercase tracking-wide text-cyan-500">
                          {
                            test.pack_name
                          }
                        </span>

                        <SeverityBadge
                          severity={
                            test.severity
                          }
                        />
                      </div>

                      <h3 className="mt-3 text-base font-semibold text-white">
                        {
                          test.name
                        }
                      </h3>

                      <p className="mt-2 text-sm leading-6 text-zinc-500">
                        {
                          test.description
                        }
                      </p>
                    </div>

                    <DecisionBadge
                      decision={
                        test.expected_decision
                      }
                    />
                  </div>

                  <div className="mt-4 flex flex-wrap gap-2">
                    {test.tags.map(
                      (tag) => (
                        <span
                          key={tag}
                          className="rounded-full border border-zinc-800 bg-black px-2 py-1 text-xs text-zinc-600"
                        >
                          {tag}
                        </span>
                      )
                    )}
                  </div>

                  <details className="mt-5 border-t border-zinc-800 pt-4">
                    <summary className="cursor-pointer text-xs text-zinc-500 hover:text-zinc-300">
                      Remediation guidance
                    </summary>

                    <p className="mt-3 text-sm leading-6 text-zinc-400">
                      {
                        test.remediation_hint
                      }
                    </p>
                  </details>

                  {safeAgents.length > 0 && (
                    <div className="mt-5 border-t border-zinc-800 pt-5">
                      <select
                        name="agent_id"
                        required
                        className="w-full rounded-lg border border-zinc-700 bg-black px-3 py-2.5 text-sm text-white"
                        defaultValue={
                          safeAgents[0]?.id
                        }
                      >
                        {safeAgents.map(
                          (agent) => (
                            <option
                              key={
                                agent.id
                              }
                              value={
                                agent.id
                              }
                            >
                              {
                                agent.name
                              }
                            </option>
                          )
                        )}
                      </select>

                      <button
                        type="submit"
                        className="mt-3 w-full rounded-lg border border-cyan-800 bg-cyan-950 px-4 py-2.5 text-sm font-medium text-cyan-300 transition hover:bg-cyan-900"
                      >
                        Run Scenario
                      </button>
                    </div>
                  )}
                </form>
              )
            )}
          </div>
        </section>

        <section className="mt-12">
          <div className="mb-4">
            <h2 className="text-sm font-medium text-zinc-300">
              Assessment History
            </h2>

            <p className="mt-1 text-sm text-zinc-600">
              Each policy suite execution is
              tracked as its own assessment
              batch.
            </p>
          </div>

          {safeHistory.length === 0 ? (
            <div className="rounded-xl border border-dashed border-zinc-800 p-8 text-center text-sm text-zinc-500">
              No policy assessment history yet.
            </div>
          ) : (
            <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950">
              {safeHistory.map(
                (assessment) => (
                  <div
                    key={
                      assessment.id
                    }
                    className="flex flex-wrap items-center justify-between gap-4 border-b border-zinc-900 px-5 py-4 last:border-b-0"
                  >
                    <div>
                      <div className="text-sm font-medium text-zinc-200">
                        {
                          assessment.assessment_type
                        }
                      </div>

                      <div className="mt-1 text-xs text-zinc-600">
                        {
                          agentMap.get(
                            assessment.agent_id
                          )?.name ??
                          assessment.agent_id
                        }
                        {" · "}
                        {
                          assessment.scope_key ??
                          "all scenarios"
                        }
                      </div>
                    </div>

                    <div className="flex items-center gap-4 text-sm">
                      <span className="text-emerald-400">
                        {
                          assessment.passed
                        }{" "}
                        passed
                      </span>

                      <span
                        className={
                          assessment.failed > 0
                            ? "text-red-400"
                            : "text-zinc-600"
                        }
                      >
                        {
                          assessment.failed
                        }{" "}
                        failed
                      </span>

                      <span className="text-xs text-zinc-600">
                        {formatDate(
                          assessment.completed_at ??
                          assessment.started_at
                        )}
                      </span>
                    </div>
                  </div>
                )
              )}
            </div>
          )}
        </section>

        <section className="mt-12">
          <div className="mb-4">
            <h2 className="text-sm font-medium text-zinc-300">
              Latest Assessment Results
            </h2>

            <p className="mt-1 text-sm text-zinc-600">
              Results are isolated to the newest
              assessment batch so older failures do
              not contaminate the current score.
            </p>
          </div>

          {recentResults.length === 0 ? (
            <div className="rounded-xl border border-dashed border-zinc-800 p-10 text-center text-sm text-zinc-500">
              No security tests have been run yet.
            </div>
          ) : (
            <div className="space-y-4">
              {recentResults.map(
                (result) => {
                  const agent =
                    agentMap.get(
                      result.agent_id
                    );

                  const finding =
                    findingByTestResult.get(
                      result.id
                    );

                  const packKey =
                    typeof result
                      .evidence
                      .pack_key ===
                    "string"
                      ? result
                          .evidence
                          .pack_key
                      : null;

                  return (
                    <div
                      key={
                        result.id
                      }
                      className="rounded-xl border border-zinc-800 bg-zinc-950 p-6"
                    >
                      <div className="flex flex-wrap items-start justify-between gap-4">
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <ResultBadge
                              passed={
                                result.passed
                              }
                            />

                            <span className="rounded-full border border-zinc-700 bg-zinc-900 px-2.5 py-1 text-xs text-zinc-400">
                              {
                                result.category
                              }
                            </span>

                            {packKey && (
                              <span className="rounded-full border border-cyan-950 bg-cyan-950/40 px-2.5 py-1 text-xs text-cyan-500">
                                {
                                  packKey
                                }
                              </span>
                            )}
                          </div>

                          <h3 className="mt-3 text-base font-semibold text-white">
                            {
                              result.test_name
                            }
                          </h3>

                          <div className="mt-1 text-sm text-zinc-500">
                            {agent?.name ??
                              result.agent_id}
                          </div>
                        </div>

                        <div className="text-right">
                          <div className="text-xs text-zinc-600">
                            {formatDate(
                              result.created_at
                            )}
                          </div>

                          <div className="mt-3 flex flex-wrap justify-end gap-2">
                            <DecisionBadge
                              decision={
                                result.expected_decision
                              }
                              prefix="Expected"
                            />

                            <DecisionBadge
                              decision={
                                result.actual_decision
                              }
                              prefix="Actual"
                            />
                          </div>
                        </div>
                      </div>

                      {!result.passed && (
                        <div className="mt-5 border-t border-zinc-800 pt-5">
                          {finding ? (
                            <div className="flex items-center justify-between rounded-lg border border-amber-900/50 bg-amber-950/20 p-4">
                              <div>
                                <div className="text-sm font-medium text-amber-400">
                                  Finding created
                                </div>

                                <div className="mt-1 text-xs text-zinc-500">
                                  Status:{" "}
                                  {
                                    finding.status
                                  }
                                </div>
                              </div>

                              <a
                                href="/findings"
                                className="text-sm text-cyan-400 hover:text-cyan-300"
                              >
                                View Finding →
                              </a>
                            </div>
                          ) : (
                            <form
                              action={
                                createFindingAction
                              }
                            >
                              <input
                                type="hidden"
                                name="test_result_id"
                                value={
                                  result.id
                                }
                              />

                              <button
                                type="submit"
                                className="rounded-lg border border-amber-800 bg-amber-950 px-4 py-2.5 text-sm font-medium text-amber-300 transition hover:bg-amber-900"
                              >
                                Create Finding
                              </button>
                            </form>
                          )}
                        </div>
                      )}

                      <details className="mt-5 border-t border-zinc-800 pt-4">
                        <summary className="cursor-pointer text-sm text-zinc-500 hover:text-zinc-300">
                          View evidence
                        </summary>

                        <pre className="mt-4 overflow-x-auto rounded-lg border border-zinc-800 bg-black p-4 text-xs leading-6 text-zinc-400">
                          {JSON.stringify(
                            result.evidence,
                            null,
                            2
                          )}
                        </pre>
                      </details>
                    </div>
                  );
                }
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}


function SummaryBadge({
  label,
  value,
  type,
}: {
  label: string;
  value: number;
  type: "pass" | "fail";
}) {
  const style =
    type === "pass"
      ? "border-emerald-900 bg-emerald-950 text-emerald-400"
      : "border-red-900 bg-red-950 text-red-400";

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
      className={`rounded-full border px-2 py-1 text-xs font-medium ${style}`}
    >
      {severity}
    </span>
  );
}


function DecisionBadge({
  decision,
  prefix,
}: {
  decision: string;
  prefix?: string;
}) {
  const style =
    decision === "DENY"
      ? "border-red-900 bg-red-950 text-red-400"
      : decision ===
          "REQUIRE_APPROVAL"
        ? "border-amber-900 bg-amber-950 text-amber-400"
        : "border-emerald-900 bg-emerald-950 text-emerald-400";

  return (
    <span
      className={`rounded-full border px-2.5 py-1 text-xs font-medium ${style}`}
    >
      {prefix
        ? `${prefix}: ${decision}`
        : decision}
    </span>
  );
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
