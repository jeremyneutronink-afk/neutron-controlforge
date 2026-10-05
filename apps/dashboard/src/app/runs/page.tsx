import Link from "next/link";

import {
  getAgents,
  getRuns,
} from "@/lib/api";


export default async function RunsPage() {
  const [
    runs,
    agents,
  ] = await Promise.all([
    getRuns(),
    getAgents(),
  ]);

  const safeRuns =
    runs ?? [];

  const agentMap =
    new Map(
      (agents ?? []).map(
        (agent) => [
          agent.id,
          agent,
        ]
      )
    );

  return (
    <div className="min-h-screen">
      <header className="border-b border-zinc-800 px-8 py-6">
        <div>
          <h1 className="text-xl font-semibold text-white">
            Runs
          </h1>

          <p className="mt-1 text-sm text-zinc-500">
            Inspect agent runs and their
            current lifecycle state.
          </p>
        </div>
      </header>

      <div className="p-8">
        {safeRuns.length === 0 ? (
          <div className="rounded-xl border border-dashed border-zinc-800 p-12 text-center">
            <div className="text-sm text-zinc-500">
              No runs recorded yet.
            </div>
          </div>
        ) : (
          <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950">
            {safeRuns.map(
              (run) => {
                const agent =
                  agentMap.get(
                    run.agent_id
                  );

                return (
                  <div
                    key={run.id}
                    className="flex flex-wrap items-center justify-between gap-5 border-b border-zinc-800 px-5 py-5 last:border-b-0"
                  >
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-3">
                        <RunStatusBadge
                          status={
                            run.status
                          }
                        />

                        <span className="text-sm font-medium text-zinc-200">
                          {agent?.name ??
                            "Unknown Agent"}
                        </span>
                      </div>

                      <div className="mt-3 font-mono text-xs text-zinc-600">
                        {run.id}
                      </div>

                      <div className="mt-2 text-xs text-zinc-600">
                        Started{" "}
                        {formatDate(
                          run.started_at
                        )}
                      </div>

                      {run.completed_at && (
                        <div className="mt-1 text-xs text-emerald-700">
                          Completed{" "}
                          {formatDate(
                            run.completed_at
                          )}
                        </div>
                      )}
                    </div>

                    <Link
                      href={`/runs/${run.id}`}
                      className="rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-500 hover:bg-zinc-900 hover:text-white"
                    >
                      Inspect Run
                    </Link>
                  </div>
                );
              }
            )}
          </div>
        )}
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
      {status.replaceAll(
        "_",
        " "
      )}
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