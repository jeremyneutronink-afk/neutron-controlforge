import Link from "next/link";

import {
  AgentKeyManager,
} from "@/components/agent-key-manager";
import {
  AgentRegistrationForm,
} from "@/components/agent-registration-form";

import {
  getAgents,
  getRuns,
} from "@/lib/api";


export default async function AgentsPage() {
  const [
    agents,
    runs,
  ] = await Promise.all([
    getAgents(),
    getRuns(),
  ]);

  const runList =
    runs ?? [];

  return (
    <div className="min-h-screen">
      <header className="border-b border-zinc-800 px-8 py-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-semibold text-white">
              Agents
            </h1>

            <p className="mt-1 text-sm text-zinc-500">
              Manage authenticated AI
              agents connected to ControlForge.
            </p>
          </div>

          {agents && (
            <div className="rounded-full border border-zinc-800 bg-zinc-950 px-3 py-1 text-xs text-zinc-400">
              {agents.length} Registered
            </div>
          )}
        </div>
      </header>

      <div className="p-8">
        <section>
          <div className="mb-4">
            <h2 className="text-sm font-medium text-zinc-300">
              Register Agent
            </h2>

            <p className="mt-1 text-sm text-zinc-600">
              Registration automatically
              provisions a unique machine
              credential.
            </p>
          </div>

          <AgentRegistrationForm />
        </section>

        <section className="mt-10">
          <div className="mb-4">
            <h2 className="text-sm font-medium text-zinc-300">
              Registered Agents
            </h2>
          </div>

          {!agents ? (
            <ErrorState />
          ) : agents.length === 0 ? (
            <EmptyState />
          ) : (
            <div className="grid gap-4 xl:grid-cols-2">
              {agents.map(
                (agent) => {
                  const agentRuns =
                    runList.filter(
                      (run) =>
                        run.agent_id ===
                        agent.id
                    );

                  const latestRun =
                    agentRuns[0] ??
                    null;

                  return (
                    <div
                      key={agent.id}
                      className="rounded-xl border border-zinc-800 bg-zinc-950 p-6"
                    >
                      <div className="flex items-start justify-between gap-5">
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <h3 className="text-base font-semibold text-white">
                              {
                                agent.name
                              }
                            </h3>

                            <StatusBadge
                              active={
                                agent.is_active
                              }
                            />

                            <CredentialBadge
                              provisioned={
                                agent.api_key_prefix !==
                                null
                              }
                            />
                          </div>

                          <p className="mt-2 min-h-10 text-sm leading-5 text-zinc-500">
                            {agent.description ??
                              "No description provided."}
                          </p>
                        </div>

                        <Link
                          href={`/agents/${agent.id}`}
                          className="shrink-0 text-sm text-cyan-400 transition hover:text-cyan-300"
                        >
                          View Agent →
                        </Link>
                      </div>

                      <div className="mt-6 grid grid-cols-2 gap-3">
                        <Metric
                          label="Runs"
                          value={String(
                            agentRuns.length
                          )}
                        />

                        <Metric
                          label="Latest Activity"
                          value={
                            latestRun
                              ? formatDate(
                                  latestRun.started_at
                                )
                              : "None"
                          }
                        />
                      </div>

                      <div className="mt-5 border-t border-zinc-800 pt-4">
                        <div className="text-xs text-zinc-600">
                          Agent ID
                        </div>

                        <div className="mt-1 truncate font-mono text-xs text-zinc-500">
                          {agent.id}
                        </div>
                      </div>

                      <AgentKeyManager
                        agentId={
                          agent.id
                        }
                        currentPrefix={
                          agent.api_key_prefix
                        }
                      />
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


function Metric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-black p-4">
      <div className="text-xs uppercase tracking-wide text-zinc-600">
        {label}
      </div>

      <div className="mt-2 text-sm font-medium text-zinc-300">
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
      {active
        ? "Active"
        : "Inactive"}
    </span>
  );
}


function CredentialBadge({
  provisioned,
}: {
  provisioned: boolean;
}) {
  return (
    <span
      className={
        provisioned
          ? "rounded-full border border-cyan-900 bg-cyan-950 px-2.5 py-1 text-xs font-medium text-cyan-400"
          : "rounded-full border border-amber-900 bg-amber-950 px-2.5 py-1 text-xs font-medium text-amber-400"
      }
    >
      {provisioned
        ? "Authenticated"
        : "Key Required"}
    </span>
  );
}


function EmptyState() {
  return (
    <div className="rounded-xl border border-dashed border-zinc-800 p-12 text-center">
      <h3 className="font-medium text-zinc-200">
        No agents registered
      </h3>

      <p className="mt-2 text-sm text-zinc-500">
        Register your first agent above.
      </p>
    </div>
  );
}


function ErrorState() {
  return (
    <div className="rounded-xl border border-red-950 bg-red-950/20 p-6">
      <div className="font-medium text-red-400">
        Unable to load agents
      </div>

      <p className="mt-2 text-sm text-zinc-500">
        The dashboard could not reach ControlForge.
      </p>
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