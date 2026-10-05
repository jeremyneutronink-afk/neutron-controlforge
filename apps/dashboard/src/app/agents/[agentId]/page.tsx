import Link from "next/link";
import { notFound } from "next/navigation";

import {
  getAgents,
  getRuns,
} from "@/lib/api";


type PageProps = {
  params: Promise<{
    agentId: string;
  }>;
};


export default async function AgentDetailPage({
  params,
}: PageProps) {
  const { agentId } = await params;

  const [agents, runs] =
    await Promise.all([
      getAgents(),
      getRuns(),
    ]);

  const agent = (agents ?? []).find(
    (item) => item.id === agentId
  );

  if (!agent) {
    notFound();
  }

  const agentRuns = (runs ?? [])
    .filter(
      (run) =>
        run.agent_id === agent.id
    )
    .sort(
      (a, b) =>
        new Date(
          b.started_at
        ).getTime() -
        new Date(
          a.started_at
        ).getTime()
    );

  return (
    <div className="min-h-screen">
      <header className="border-b border-zinc-800 px-8 py-6">
        <Link
          href="/agents"
          className="text-sm text-zinc-500 transition hover:text-white"
        >
          ← Agents
        </Link>

        <div className="mt-4 flex items-start justify-between gap-6">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-semibold text-white">
                {agent.name}
              </h1>

              <StatusBadge
                active={agent.is_active}
              />
            </div>

            <p className="mt-2 max-w-2xl text-sm text-zinc-500">
              {agent.description ??
                "No description provided."}
            </p>
          </div>
        </div>
      </header>

      <div className="p-8">
        <div className="grid gap-4 md:grid-cols-3">
          <SummaryCard
            label="Status"
            value={
              agent.is_active
                ? "Active"
                : "Inactive"
            }
          />

          <SummaryCard
            label="Runs"
            value={String(
              agentRuns.length
            )}
          />

          <SummaryCard
            label="Latest Activity"
            value={
              agentRuns.length > 0
                ? formatDate(
                    agentRuns[0]
                      .started_at
                  )
                : "No activity"
            }
          />
        </div>

        <section className="mt-8">
          <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-5">
            <div className="text-xs font-medium uppercase tracking-wide text-zinc-500">
              Agent ID
            </div>

            <div className="mt-2 break-all font-mono text-sm text-zinc-300">
              {agent.id}
            </div>
          </div>
        </section>

        <section className="mt-10">
          <div className="mb-4">
            <h2 className="text-sm font-medium text-zinc-300">
              Run History
            </h2>

            <p className="mt-1 text-sm text-zinc-600">
              Recent activity submitted by
              this agent.
            </p>
          </div>

          {agentRuns.length === 0 ? (
            <div className="rounded-xl border border-dashed border-zinc-800 p-10 text-center">
              <div className="text-sm text-zinc-500">
                This agent has not created
                any runs yet.
              </div>
            </div>
          ) : (
            <div className="overflow-hidden rounded-xl border border-zinc-800">
              {agentRuns.map(
                (run) => (
                  <div
                    key={run.id}
                    className="flex items-center justify-between gap-6 border-b border-zinc-800 bg-zinc-950 px-5 py-4 last:border-b-0"
                  >
                    <div>
                      <div className="flex items-center gap-3">
                        <span className="rounded-full border border-cyan-900 bg-cyan-950 px-2.5 py-1 text-xs font-medium text-cyan-400">
                          {run.status}
                        </span>

                        <span className="text-sm text-zinc-400">
                          {formatDate(
                            run.started_at
                          )}
                        </span>
                      </div>

                      <div className="mt-2 font-mono text-xs text-zinc-600">
                        {run.id}
                      </div>
                    </div>

                    <Link
                      href={`/runs/${run.id}`}
                      className="shrink-0 rounded-lg border border-zinc-700 px-3 py-2 text-sm text-zinc-300 transition hover:border-zinc-500 hover:bg-zinc-900 hover:text-white"
                    >
                      Inspect Run
                    </Link>
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


function StatusBadge({
  active,
}: {
  active: boolean;
}) {
  return (
    <span
      className={
        active
          ? "rounded-full border border-emerald-900 bg-emerald-950 px-2.5 py-1 text-xs font-medium text-emerald-400"
          : "rounded-full border border-zinc-700 bg-zinc-900 px-2.5 py-1 text-xs font-medium text-zinc-500"
      }
    >
      {active ? "Active" : "Inactive"}
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
  ).format(new Date(value));
}