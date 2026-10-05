import Link from "next/link";
import {
  revalidatePath,
} from "next/cache";

import {
  getAgents,
} from "@/lib/api";

import {
  createFinding,
  FindingResponse,
  FindingSeverity,
  FindingStatus,
  getFindings,
  retestFinding,
  updateFinding,
} from "@/lib/findings-api";


async function createFindingAction(
  formData: FormData
) {
  "use server";

  const agentId = String(
    formData.get("agent_id") ?? ""
  );

  const title = String(
    formData.get("title") ?? ""
  ).trim();

  const severity = String(
    formData.get("severity") ?? "MEDIUM"
  ) as FindingSeverity;

  const description = String(
    formData.get("description") ?? ""
  ).trim();

  const rawRemediation = String(
    formData.get("remediation") ?? ""
  ).trim();

  if (
    !agentId ||
    !title ||
    !description
  ) {
    return;
  }

  await createFinding(
    agentId,
    title,
    severity,
    description,
    rawRemediation || null
  );

  revalidatePath("/findings");
}


async function updateFindingAction(
  formData: FormData
) {
  "use server";

  const findingId = String(
    formData.get("finding_id") ?? ""
  );

  const status = String(
    formData.get("status") ?? ""
  ) as FindingStatus;

  const remediation = String(
    formData.get("remediation") ?? ""
  ).trim();

  if (
    !findingId ||
    !status
  ) {
    return;
  }

  await updateFinding(
    findingId,
    {
      status,
      remediation,
    }
  );

  revalidatePath("/findings");
}


async function retestFindingAction(
  formData: FormData
) {
  "use server";

  const findingId = String(
    formData.get("finding_id") ?? ""
  );

  if (!findingId) {
    return;
  }

  await retestFinding(
    findingId
  );

  revalidatePath("/findings");
  revalidatePath("/security-tests");
}


export default async function FindingsPage() {
  const [
    findings,
    agents,
  ] = await Promise.all([
    getFindings(),
    getAgents(),
  ]);

  const safeFindings =
    findings ?? [];

  const safeAgents =
    agents ?? [];

  const agentMap = new Map(
    safeAgents.map(
      (agent) => [
        agent.id,
        agent,
      ]
    )
  );

  const openCount =
    safeFindings.filter(
      (finding) =>
        finding.status !== "RESOLVED"
    ).length;

  const criticalCount =
    safeFindings.filter(
      (finding) =>
        finding.severity === "CRITICAL" &&
        finding.status !== "RESOLVED"
    ).length;

  return (
    <div className="min-h-screen">
      <header className="border-b border-zinc-800 px-8 py-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold text-white">
              Findings
            </h1>

            <p className="mt-1 text-sm text-zinc-500">
              Track discovered security
              weaknesses through remediation
              and retesting.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <Link
              href="/reports"
              className="rounded-lg border border-cyan-800 bg-cyan-950 px-4 py-2 text-sm font-medium text-cyan-300 transition hover:bg-cyan-900"
            >
              Generate Report
            </Link>

            <MetricBadge
              label="Open"
              value={openCount}
              variant="amber"
            />

            <MetricBadge
              label="Critical"
              value={criticalCount}
              variant="red"
            />
          </div>
        </div>
      </header>

      <div className="p-8">
        <section>
          <div className="mb-4">
            <h2 className="text-sm font-medium text-zinc-300">
              Record Finding
            </h2>

            <p className="mt-1 text-sm text-zinc-600">
              Add an assessment observation manually.
            </p>
          </div>

          <form
            action={createFindingAction}
            className="rounded-xl border border-zinc-800 bg-zinc-950 p-6"
          >
            <div className="grid gap-4 md:grid-cols-2">
              <label>
                <FieldLabel>
                  Agent
                </FieldLabel>

                <select
                  name="agent_id"
                  required
                  className="input"
                  defaultValue={
                    safeAgents[0]?.id
                  }
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
                  Severity
                </FieldLabel>

                <select
                  name="severity"
                  className="input"
                  defaultValue="MEDIUM"
                >
                  <option value="LOW">
                    LOW
                  </option>

                  <option value="MEDIUM">
                    MEDIUM
                  </option>

                  <option value="HIGH">
                    HIGH
                  </option>

                  <option value="CRITICAL">
                    CRITICAL
                  </option>
                </select>
              </label>
            </div>

            <label className="mt-4 block">
              <FieldLabel>
                Title
              </FieldLabel>

              <input
                name="title"
                required
                placeholder="Approval boundary can be bypassed"
                className="input"
              />
            </label>

            <label className="mt-4 block">
              <FieldLabel>
                Description
              </FieldLabel>

              <textarea
                name="description"
                required
                rows={4}
                placeholder="Describe what was observed, why it matters, and how it can be reproduced."
                className="input resize-y"
              />
            </label>

            <label className="mt-4 block">
              <FieldLabel>
                Recommended Remediation
              </FieldLabel>

              <textarea
                name="remediation"
                rows={3}
                placeholder="Optional remediation guidance"
                className="input resize-y"
              />
            </label>

            <div className="mt-5 flex justify-end">
              <button
                type="submit"
                className="rounded-lg border border-cyan-800 bg-cyan-950 px-5 py-2.5 text-sm font-medium text-cyan-300 transition hover:bg-cyan-900"
              >
                Create Finding
              </button>
            </div>
          </form>
        </section>

        <section className="mt-12">
          <div className="mb-4">
            <h2 className="text-sm font-medium text-zinc-300">
              Assessment Findings
            </h2>

            <p className="mt-1 text-sm text-zinc-600">
              Current security issues and remediation state.
            </p>
          </div>

          {safeFindings.length === 0 ? (
            <div className="rounded-xl border border-dashed border-zinc-800 p-12 text-center">
              <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full border border-emerald-900 bg-emerald-950 text-emerald-400">
                ✓
              </div>

              <div className="mt-4 font-medium text-zinc-200">
                No findings
              </div>

              <div className="mt-2 text-sm text-zinc-500">
                Findings discovered during assessment will appear here.
              </div>
            </div>
          ) : (
            <div className="space-y-5">
              {safeFindings.map(
                (finding) => (
                  <FindingCard
                    key={finding.id}
                    finding={finding}
                    agentName={
                      agentMap.get(
                        finding.agent_id
                      )?.name ??
                      finding.agent_id
                    }
                  />
                )
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}


function FindingCard({
  finding,
  agentName,
}: {
  finding: FindingResponse;
  agentName: string;
}) {
  const canRetest =
    finding.source_test_result_id !== null &&
    finding.status === "READY_FOR_RETEST";

  const latestRetest =
    typeof finding.evidence.latest_retest === "object" &&
    finding.evidence.latest_retest !== null
      ? finding.evidence.latest_retest as Record<string, unknown>
      : null;

  return (
    <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950">
      <div className="p-6">
        <div className="flex flex-wrap items-start justify-between gap-5">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <SeverityBadge
                severity={finding.severity}
              />

              <StatusBadge
                status={finding.status}
              />

              {finding.source_test_result_id && (
                <span className="rounded-full border border-cyan-900 bg-cyan-950 px-2.5 py-1 text-xs text-cyan-400">
                  Security Test
                </span>
              )}

              {finding.retest_status &&
                finding.retest_status !== "NOT_RUN" && (
                  <RetestBadge
                    status={finding.retest_status}
                  />
                )}
            </div>

            <h3 className="mt-4 text-lg font-semibold text-white">
              {finding.title}
            </h3>

            <div className="mt-1 text-sm text-zinc-500">
              {agentName}
            </div>
          </div>

          <div className="text-right">
            <div className="font-mono text-xs text-zinc-600">
              {finding.id.slice(0, 8)}...
            </div>

            <div className="mt-2 text-xs text-zinc-600">
              {formatDate(
                finding.created_at
              )}
            </div>
          </div>
        </div>

        <div className="mt-6 rounded-lg border border-zinc-800 bg-black p-4">
          <div className="text-xs font-medium uppercase tracking-wide text-zinc-500">
            Description
          </div>

          <p className="mt-2 text-sm leading-6 text-zinc-300">
            {finding.description}
          </p>
        </div>

        {latestRetest && (
          <div
            className={
              finding.retest_status === "PASS"
                ? "mt-4 rounded-lg border border-emerald-900 bg-emerald-950/30 p-4"
                : "mt-4 rounded-lg border border-red-900 bg-red-950/30 p-4"
            }
          >
            <div className="text-xs font-medium uppercase tracking-wide text-zinc-500">
              Latest Retest
            </div>

            <div className="mt-3 grid gap-3 md:grid-cols-3">
              <RetestValue
                label="Result"
                value={
                  finding.retest_status ?? "UNKNOWN"
                }
              />

              <RetestValue
                label="Expected"
                value={
                  String(
                    latestRetest.expected_decision ??
                    "Unknown"
                  )
                }
              />

              <RetestValue
                label="Actual"
                value={
                  String(
                    latestRetest.actual_decision ??
                    "Unknown"
                  )
                }
              />
            </div>

            {typeof latestRetest.reason === "string" && (
              <p className="mt-4 text-sm leading-6 text-zinc-300">
                {latestRetest.reason}
              </p>
            )}
          </div>
        )}

        {Object.keys(
          finding.evidence
        ).length > 0 && (
          <details className="mt-4">
            <summary className="cursor-pointer text-sm text-zinc-500 hover:text-zinc-300">
              Evidence
            </summary>

            <pre className="mt-3 overflow-x-auto rounded-lg border border-zinc-800 bg-black p-4 text-xs leading-6 text-zinc-400">
              {JSON.stringify(
                finding.evidence,
                null,
                2
              )}
            </pre>
          </details>
        )}
      </div>

      <form
        action={updateFindingAction}
        className="border-t border-zinc-800 bg-black/30 p-6"
      >
        <input
          type="hidden"
          name="finding_id"
          value={finding.id}
        />

        <div className="grid gap-4 md:grid-cols-[220px_1fr_auto] md:items-end">
          <label>
            <FieldLabel>
              Status
            </FieldLabel>

            <select
              name="status"
              className="input"
              defaultValue={finding.status}
            >
              <option value="OPEN">
                OPEN
              </option>

              <option value="IN_REMEDIATION">
                IN REMEDIATION
              </option>

              <option value="READY_FOR_RETEST">
                READY FOR RETEST
              </option>

              <option value="RESOLVED">
                RESOLVED
              </option>
            </select>
          </label>

          <label>
            <FieldLabel>
              Remediation
            </FieldLabel>

            <input
              name="remediation"
              defaultValue={
                finding.remediation ?? ""
              }
              placeholder="What should be changed?"
              className="input"
            />
          </label>

          <button
            type="submit"
            className="rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2.5 text-sm text-zinc-300 transition hover:border-zinc-500 hover:text-white"
          >
            Save
          </button>
        </div>
      </form>

      {canRetest && (
        <div className="border-t border-zinc-800 bg-cyan-950/10 p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="text-sm font-medium text-cyan-300">
                Ready for security retest
              </div>

              <div className="mt-1 text-sm text-zinc-500">
                ControlForge will rerun the original
                scenario against the current policy engine.
              </div>
            </div>

            <form
              action={retestFindingAction}
            >
              <input
                type="hidden"
                name="finding_id"
                value={finding.id}
              />

              <button
                type="submit"
                className="rounded-lg border border-cyan-700 bg-cyan-950 px-5 py-2.5 text-sm font-medium text-cyan-300 transition hover:bg-cyan-900"
              >
                Run Retest
              </button>
            </form>
          </div>
        </div>
      )}
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


function SeverityBadge({
  severity,
}: {
  severity: string;
}) {
  const style =
    severity === "CRITICAL"
      ? "border-red-800 bg-red-950 text-red-300"
      : severity === "HIGH"
        ? "border-red-900 bg-red-950/60 text-red-400"
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


function StatusBadge({
  status,
}: {
  status: string;
}) {
  const style =
    status === "RESOLVED"
      ? "border-emerald-900 bg-emerald-950 text-emerald-400"
      : status === "READY_FOR_RETEST"
        ? "border-cyan-900 bg-cyan-950 text-cyan-400"
        : status === "IN_REMEDIATION"
          ? "border-amber-900 bg-amber-950 text-amber-400"
          : "border-zinc-700 bg-zinc-900 text-zinc-300";

  return (
    <span
      className={`rounded-full border px-2.5 py-1 text-xs font-medium ${style}`}
    >
      {status.replaceAll("_", " ")}
    </span>
  );
}


function RetestBadge({
  status,
}: {
  status: string;
}) {
  const style =
    status === "PASS"
      ? "border-emerald-900 bg-emerald-950 text-emerald-400"
      : status === "FAIL"
        ? "border-red-900 bg-red-950 text-red-400"
        : "border-zinc-700 bg-zinc-900 text-zinc-400";

  return (
    <span
      className={`rounded-full border px-2.5 py-1 text-xs font-medium ${style}`}
    >
      RETEST {status}
    </span>
  );
}


function RetestValue({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-black/40 p-3">
      <div className="text-xs uppercase tracking-wide text-zinc-600">
        {label}
      </div>

      <div className="mt-2 text-sm font-medium text-zinc-200">
        {value}
      </div>
    </div>
  );
}


function MetricBadge({
  label,
  value,
  variant,
}: {
  label: string;
  value: number;
  variant:
    | "amber"
    | "red";
}) {
  const style =
    variant === "red"
      ? "border-red-900 bg-red-950 text-red-400"
      : "border-amber-900 bg-amber-950 text-amber-400";

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
