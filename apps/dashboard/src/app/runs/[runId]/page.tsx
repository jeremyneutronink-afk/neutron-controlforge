import Link from "next/link";
import {
  revalidatePath,
} from "next/cache";
import {
  notFound,
} from "next/navigation";

import {
  completeRun,
  getAgents,
  getRun,
  getRunTimeline,
} from "@/lib/api";


type PageProps = {
  params: Promise<{
    runId: string;
  }>;
};


async function completeRunAction(
  formData: FormData
) {
  "use server";

  const runId = String(
    formData.get("run_id") ?? ""
  );

  const agentKey = String(
    formData.get("agent_key") ?? ""
  ).trim();

  if (
    !runId ||
    !agentKey
  ) {
    return;
  }

  await completeRun(
    runId,
    agentKey
  );

  revalidatePath(
    `/runs/${runId}`
  );

  revalidatePath(
    "/runs"
  );

  revalidatePath("/");
}


export default async function RunDetailPage({
  params,
}: PageProps) {
  const { runId } =
    await params;

  const [
    run,
    events,
    agents,
  ] = await Promise.all([
    getRun(runId),
    getRunTimeline(runId),
    getAgents(),
  ]);

  if (!run) {
    notFound();
  }

  const agent =
    (agents ?? []).find(
      (item) =>
        item.id ===
        run.agent_id
    );

  const safeEvents =
    events ?? [];

  const canComplete =
    ![
      "COMPLETED",
      "EXECUTING",
      "WAITING_APPROVAL",
    ].includes(
      run.status
    );

  return (
    <div className="min-h-screen">
      <header className="border-b border-zinc-800 px-8 py-6">
        <Link
          href="/runs"
          className="text-sm text-zinc-500 transition hover:text-white"
        >
          ← Runs
        </Link>

        <div className="mt-4 flex flex-wrap items-start justify-between gap-5">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-xl font-semibold text-white">
                Run
              </h1>

              <RunStatusBadge
                status={
                  run.status
                }
              />
            </div>

            <div className="mt-2 font-mono text-sm text-zinc-500">
              {run.id}
            </div>
          </div>

          <div className="text-right">
            <div className="text-xs uppercase tracking-wide text-zinc-600">
              Agent
            </div>

            <div className="mt-1 text-sm font-medium text-zinc-300">
              {agent?.name ??
                run.agent_id}
            </div>
          </div>
        </div>
      </header>

      <div className="p-8">
        <section className="grid gap-4 md:grid-cols-3">
          <SummaryCard
            label="Status"
            value={humanize(
              run.status
            )}
          />

          <SummaryCard
            label="Started"
            value={formatDate(
              run.started_at
            )}
          />

          <SummaryCard
            label="Completed"
            value={
              run.completed_at
                ? formatDate(
                    run.completed_at
                  )
                : "Not completed"
            }
          />
        </section>

        {canComplete && (
          <section className="mt-8 rounded-xl border border-cyan-900/50 bg-cyan-950/10 p-6">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <h2 className="text-sm font-medium text-cyan-300">
                  Complete Run
                </h2>

                <p className="mt-2 max-w-xl text-sm leading-6 text-zinc-500">
                  Explicitly close this run when the
                  agent has finished all intended work.
                  The agent credential is required.
                </p>
              </div>

              <form
                action={
                  completeRunAction
                }
                className="flex w-full flex-col gap-3 sm:flex-row lg:w-auto"
              >
                <input
                  type="hidden"
                  name="run_id"
                  value={run.id}
                />

                <input
                  name="agent_key"
                  type="password"
                  required
                  autoComplete="off"
                  placeholder="agk_..."
                  className="min-w-72 rounded-lg border border-zinc-700 bg-black px-3 py-2.5 text-sm text-white outline-none placeholder:text-zinc-700 focus:border-cyan-700"
                />

                <button
                  type="submit"
                  className="rounded-lg border border-cyan-800 bg-cyan-950 px-5 py-2.5 text-sm font-medium text-cyan-300 transition hover:bg-cyan-900"
                >
                  Complete Run
                </button>
              </form>
            </div>
          </section>
        )}

        {run.status ===
          "WAITING_APPROVAL" && (
          <section className="mt-8 rounded-xl border border-amber-900/50 bg-amber-950/10 p-5">
            <div className="text-sm font-medium text-amber-400">
              This run is waiting for human approval.
            </div>

            <Link
              href="/approvals"
              className="mt-2 inline-block text-sm text-cyan-400 hover:text-cyan-300"
            >
              Open Approvals →
            </Link>
          </section>
        )}

        {run.status ===
          "BLOCKED" && (
          <section className="mt-8 rounded-xl border border-red-900/50 bg-red-950/10 p-5">
            <div className="text-sm font-medium text-red-400">
              This run has been blocked by policy or reviewer decision.
            </div>
          </section>
        )}

        {run.status ===
          "FAILED" && (
          <section className="mt-8 rounded-xl border border-red-900/50 bg-red-950/10 p-5">
            <div className="text-sm font-medium text-red-400">
              This run failed during execution.
            </div>
          </section>
        )}

        <section className="mt-10">
          <div className="mb-4">
            <h2 className="text-sm font-medium text-zinc-300">
              Security Timeline
            </h2>

            <p className="mt-1 text-sm text-zinc-600">
              Ordered record of security-relevant
              activity for this run.
            </p>
          </div>

          {safeEvents.length === 0 ? (
            <div className="rounded-xl border border-dashed border-zinc-800 p-10 text-center text-sm text-zinc-500">
              No events recorded.
            </div>
          ) : (
            <div className="space-y-4">
              {safeEvents.map(
                (event) => (
                  <div
                    key={event.id}
                    className="rounded-xl border border-zinc-800 bg-zinc-950 p-5"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="rounded-full border border-zinc-700 bg-zinc-900 px-2.5 py-1 text-xs text-zinc-300">
                            {humanize(
                              event.event_type
                            )}
                          </span>

                          <SeverityBadge
                            severity={
                              event.severity
                            }
                          />
                        </div>

                        <div className="mt-3 text-sm leading-6 text-zinc-300">
                          {event.message}
                        </div>
                      </div>

                      <div className="shrink-0 text-xs text-zinc-600">
                        {formatDate(
                          event.created_at
                        )}
                      </div>
                    </div>

                    {Object.keys(
                      event.event_data
                    ).length > 0 && (
                      <details className="mt-4 border-t border-zinc-800 pt-4">
                        <summary className="cursor-pointer text-xs text-zinc-600 hover:text-zinc-400">
                          Technical details
                        </summary>

                        <pre className="mt-3 overflow-x-auto rounded-lg border border-zinc-800 bg-black p-4 text-xs leading-6 text-zinc-400">
                          {JSON.stringify(
                            event.event_data,
                            null,
                            2
                          )}
                        </pre>
                      </details>
                    )}
                  </div>
                )
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}


function SummaryCard({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-5">
      <div className="text-xs font-medium uppercase tracking-wide text-zinc-500">
        {label}
      </div>

      <div className="mt-3 text-sm font-medium text-zinc-200">
        {value}
      </div>
    </div>
  );
}


function RunStatusBadge({
  status,
}: {
  status: string;
}) {
  const style =
    status === "COMPLETED"
      ? "border-emerald-900 bg-emerald-950 text-emerald-400"
      : status === "ACTIVE"
        ? "border-cyan-900 bg-cyan-950 text-cyan-400"
        : status === "WAITING_APPROVAL"
          ? "border-amber-900 bg-amber-950 text-amber-400"
          : status === "BLOCKED"
            ? "border-red-900 bg-red-950 text-red-400"
            : status === "FAILED"
              ? "border-red-800 bg-red-950 text-red-300"
              : status === "EXECUTING"
                ? "border-blue-900 bg-blue-950 text-blue-400"
                : "border-zinc-700 bg-zinc-900 text-zinc-400";

  return (
    <span
      className={`rounded-full border px-2.5 py-1 text-xs font-medium ${style}`}
    >
      {humanize(
        status
      )}
    </span>
  );
}


function SeverityBadge({
  severity,
}: {
  severity: string;
}) {
  const style =
    severity === "CRITICAL" ||
    severity === "HIGH"
      ? "border-red-900 bg-red-950 text-red-400"
      : severity === "MEDIUM"
        ? "border-amber-900 bg-amber-950 text-amber-400"
        : severity === "LOW"
          ? "border-emerald-900 bg-emerald-950 text-emerald-400"
          : "border-zinc-700 bg-zinc-900 text-zinc-500";

  return (
    <span
      className={`rounded-full border px-2.5 py-1 text-xs font-medium ${style}`}
    >
      {severity}
    </span>
  );
}


function humanize(
  value: string
) {
  return value
    .toLowerCase()
    .split("_")
    .map(
      (part) =>
        part.charAt(0).toUpperCase() +
        part.slice(1)
    )
    .join(" ");
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