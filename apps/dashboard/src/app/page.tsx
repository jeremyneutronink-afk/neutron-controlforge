import Link from "next/link";

import { ApiStatus } from "@/components/api-status";

import {
  EventResponse,
  getAgents,
  getDashboardApprovals,
  getHealth,
  getRuns,
  getRunTimeline,
  getSecurityAuditEvents,
  SecurityAuditEventResponse,
} from "@/lib/api";


export default async function Home() {
  const [
    health,
    agents,
    runs,
    approvals,
    securityAudit,
  ] = await Promise.all([
    getHealth(),
    getAgents(),
    getRuns(),
    getDashboardApprovals(),
    getSecurityAuditEvents(12),
  ]);

  const safeAgents =
    agents ?? [];

  const safeRuns =
    runs ?? [];

  const safeApprovals =
    approvals ?? [];

  const safeSecurityAudit =
    securityAudit ?? [];

  const recentRuns =
    safeRuns.slice(0, 5);

  const recentTimelines =
    await Promise.all(
      recentRuns.map(
        async (run) => {
          const events =
            await getRunTimeline(
              run.id
            );

          return {
            run,
            events:
              events ?? [],
          };
        }
      )
    );

  const recentEvents =
    recentTimelines
      .flatMap(
        ({
          run,
          events,
        }) =>
          events.map(
            (event) => ({
              ...event,
              run,
            })
          )
      )
      .sort(
        (a, b) =>
          new Date(
            b.created_at
          ).getTime() -
          new Date(
            a.created_at
          ).getTime()
      );

  const highRiskEvents =
    recentEvents.filter(
      (event) =>
        event.severity ===
          "HIGH" ||
        event.severity ===
          "CRITICAL"
    );

  const activeAgents =
    safeAgents.filter(
      (agent) =>
        agent.is_active
    );

  const failedAuthCount =
    safeSecurityAudit.filter(
      (event) =>
        event.event_type ===
        "AGENT_AUTH_FAILED"
    ).length;

  return (
    <div className="min-h-screen">
      <header className="flex items-center justify-between border-b border-zinc-800 px-8 py-6">
        <div>
          <h1 className="text-xl font-semibold text-white">
            Control Plane Overview
          </h1>

          <p className="mt-1 text-sm text-zinc-500">
            Current ControlForge activity,
            approvals, and security events.
          </p>
        </div>

        <ApiStatus />
      </header>

      <div className="p-8">
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            label="Registered Agents"
            value={String(
              safeAgents.length
            )}
            detail={`${activeAgents.length} active`}
            href="/agents"
          />

          <MetricCard
            label="Runs"
            value={String(
              safeRuns.length
            )}
            detail="Stored ControlForge runs"
            href="/runs"
          />

          <MetricCard
            label="Pending Approvals"
            value={String(
              safeApprovals.length
            )}
            detail={
              safeApprovals.length === 0
                ? "No actions waiting"
                : "Human review required"
            }
            href="/approvals"
            attention={
              safeApprovals.length > 0
            }
          />

          <MetricCard
            label="Auth Failures"
            value={String(
              failedAuthCount
            )}
            detail="Among recent audit events"
            href="/"
            danger={
              failedAuthCount > 0
            }
          />
        </section>

        <section className="mt-8 grid gap-6 xl:grid-cols-2">
          <div>
            <div className="mb-4 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-medium text-zinc-300">
                  Agent Security Activity
                </h2>

                <p className="mt-1 text-sm text-zinc-600">
                  Latest events generated
                  during agent runs.
                </p>
              </div>

              <Link
                href="/runs"
                className="text-sm text-cyan-400 hover:text-cyan-300"
              >
                View Runs →
              </Link>
            </div>

            {recentEvents.length === 0 ? (
              <EmptyActivity />
            ) : (
              <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950">
                {recentEvents
                  .slice(0, 8)
                  .map(
                    (event) => (
                      <ActivityRow
                        key={
                          event.id
                        }
                        event={
                          event
                        }
                      />
                    )
                  )}
              </div>
            )}
          </div>

          <div>
            <div className="mb-4">
              <h2 className="text-sm font-medium text-zinc-300">
                Control Plane Security Activity
              </h2>

              <p className="mt-1 text-sm text-zinc-600">
                Authentication and credential
                activity against ControlForge
                itself.
              </p>
            </div>

            {safeSecurityAudit.length ===
            0 ? (
              <EmptyActivity />
            ) : (
              <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950">
                {safeSecurityAudit
                  .slice(0, 8)
                  .map(
                    (event) => (
                      <SecurityAuditRow
                        key={
                          event.id
                        }
                        event={
                          event
                        }
                      />
                    )
                  )}
              </div>
            )}
          </div>
        </section>

        <section className="mt-10">
          <div className="mb-4">
            <h2 className="text-sm font-medium text-zinc-300">
              Pending Human Review
            </h2>

            <p className="mt-1 text-sm text-zinc-600">
              Sensitive actions currently
              waiting on approval.
            </p>
          </div>

          {safeApprovals.length === 0 ? (
            <div className="rounded-xl border border-zinc-800 bg-zinc-950 p-6">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full border border-emerald-900 bg-emerald-950 text-sm text-emerald-400">
                  ✓
                </div>

                <div>
                  <div className="text-sm font-medium text-zinc-200">
                    No approvals waiting
                  </div>

                  <div className="mt-1 text-sm text-zinc-500">
                    No sensitive actions
                    currently require human
                    authorization.
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="grid gap-4 lg:grid-cols-2">
              {safeApprovals
                .slice(0, 4)
                .map(
                  (approval) => (
                    <Link
                      key={
                        approval.id
                      }
                      href="/approvals"
                      className="rounded-xl border border-amber-900/50 bg-amber-950/20 p-5 transition hover:border-amber-800"
                    >
                      <div className="text-xs font-medium uppercase tracking-wide text-amber-500">
                        Approval Required
                      </div>

                      <div className="mt-2 text-sm font-medium text-white">
                        {humanize(
                          approval.action_name
                        )}
                      </div>

                      <div className="mt-1 text-sm text-zinc-500">
                        {
                          approval.agent_name
                        }
                      </div>

                      <p className="mt-4 text-sm leading-6 text-zinc-400">
                        {
                          approval.reason
                        }
                      </p>
                    </Link>
                  )
                )}
            </div>
          )}
        </section>

        <section className="mt-10 grid gap-6 xl:grid-cols-[1fr_2fr]">
          <div>
            <div className="mb-4">
              <h2 className="text-sm font-medium text-zinc-300">
                System Status
              </h2>
            </div>

            <div className="space-y-4">
              <SystemCard
                label="Backend"
                value={
                  health?.service ??
                  "Unavailable"
                }
              />

              <SystemCard
                label="Environment"
                value={
                  health?.environment ??
                  "Unknown"
                }
              />

              <SystemCard
                label="API Version"
                value={
                  health?.version ??
                  "Unknown"
                }
              />
            </div>
          </div>

          <div>
            <div className="mb-4">
              <h2 className="text-sm font-medium text-zinc-300">
                Active Controls
              </h2>
            </div>

            <div className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950">
              <ControlRow
                name="Agent Authentication"
                description="Machine credentials bind API requests to registered agent identities."
              />

              <ControlRow
                name="Deterministic Policy Engine"
                description="Proposed actions are evaluated before execution."
              />

              <ControlRow
                name="Human Approval Gates"
                description="Sensitive actions require explicit operator authorization."
              />

              <ControlRow
                name="Execution Enforcement"
                description="Denied actions cannot enter the execution path."
              />

              <ControlRow
                name="Security Audit Stream"
                description="Authentication and credential activity is persistently recorded."
                last
              />
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}


function MetricCard({
  label,
  value,
  detail,
  href,
  attention = false,
  danger = false,
}: {
  label: string;
  value: string;
  detail: string;
  href: string;
  attention?: boolean;
  danger?: boolean;
}) {
  const valueClass =
    danger
      ? "text-red-400"
      : attention
        ? "text-amber-400"
        : "text-white";

  return (
    <Link
      href={href}
      className="rounded-xl border border-zinc-800 bg-zinc-950 p-5 transition hover:border-zinc-700"
    >
      <div className="text-xs font-medium uppercase tracking-wide text-zinc-500">
        {label}
      </div>

      <div
        className={`mt-3 text-3xl font-semibold ${valueClass}`}
      >
        {value}
      </div>

      <div className="mt-2 text-sm text-zinc-500">
        {detail}
      </div>
    </Link>
  );
}


function ActivityRow({
  event,
}: {
  event: EventResponse;
}) {
  return (
    <Link
      href={`/runs/${event.run_id}`}
      className="block border-b border-zinc-800 px-5 py-4 transition last:border-b-0 hover:bg-zinc-900/50"
    >
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-full border border-zinc-700 bg-zinc-900 px-2 py-1 text-xs text-zinc-300">
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

      <div className="mt-3 text-sm text-zinc-300">
        {event.message}
      </div>

      <div className="mt-2 text-xs text-zinc-600">
        {formatDate(
          event.created_at
        )}
      </div>
    </Link>
  );
}


function SecurityAuditRow({
  event,
}: {
  event: SecurityAuditEventResponse;
}) {
  return (
    <div className="border-b border-zinc-800 px-5 py-4 last:border-b-0">
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-full border border-zinc-700 bg-zinc-900 px-2 py-1 text-xs text-zinc-300">
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

      <div className="mt-3 text-sm text-zinc-300">
        {event.message}
      </div>

      {event.agent_id && (
        <div className="mt-2 font-mono text-xs text-zinc-600">
          Agent{" "}
          {event.agent_id.slice(
            0,
            8
          )}
          ...
        </div>
      )}

      <div className="mt-2 text-xs text-zinc-600">
        {formatDate(
          event.created_at
        )}
      </div>
    </div>
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
      className={`rounded-full border px-2 py-1 text-xs font-medium ${style}`}
    >
      {severity}
    </span>
  );
}


function SystemCard({
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

      <div className="mt-3 text-sm font-semibold capitalize text-white">
        {value}
      </div>
    </div>
  );
}


function ControlRow({
  name,
  description,
  last = false,
}: {
  name: string;
  description: string;
  last?: boolean;
}) {
  return (
    <div
      className={`flex items-center justify-between gap-5 px-5 py-4 ${
        last
          ? ""
          : "border-b border-zinc-800"
      }`}
    >
      <div>
        <div className="text-sm font-medium text-zinc-200">
          {name}
        </div>

        <div className="mt-1 text-sm text-zinc-500">
          {description}
        </div>
      </div>

      <div className="shrink-0 rounded-full border border-emerald-900 bg-emerald-950 px-2.5 py-1 text-xs font-medium text-emerald-400">
        Active
      </div>
    </div>
  );
}


function EmptyActivity() {
  return (
    <div className="rounded-xl border border-dashed border-zinc-800 p-10 text-center text-sm text-zinc-500">
      No security activity yet.
    </div>
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
        part
          .charAt(0)
          .toUpperCase() +
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