import Link from "next/link";
import { revalidatePath } from "next/cache";

import {
  approveApproval,
  denyApproval,
  getDashboardApprovals,
} from "@/lib/api";


async function resolveApproval(
  formData: FormData
) {
  "use server";

  const approvalId = String(
    formData.get("approval_id") ?? ""
  );

  const runId = String(
    formData.get("run_id") ?? ""
  );

  const resolution = String(
    formData.get("resolution") ?? ""
  );

  const resolvedBy = String(
    formData.get("resolved_by") ?? ""
  ).trim();

  const rawNote = String(
    formData.get("note") ?? ""
  ).trim();

  const note =
    rawNote.length > 0
      ? rawNote
      : null;

  if (
    !approvalId ||
    !resolvedBy
  ) {
    return;
  }

  if (resolution === "approve") {
    await approveApproval(
      approvalId,
      resolvedBy,
      note
    );
  }

  if (resolution === "deny") {
    await denyApproval(
      approvalId,
      resolvedBy,
      note
    );
  }

  revalidatePath("/approvals");

  if (runId) {
    revalidatePath(
      `/runs/${runId}`
    );
  }
}


export default async function ApprovalsPage() {
  const approvals =
    await getDashboardApprovals();

  return (
    <div className="min-h-screen">
      <header className="border-b border-zinc-800 px-8 py-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-semibold text-white">
              Approvals
            </h1>

            <p className="mt-1 text-sm text-zinc-500">
              Review sensitive agent actions
              before they are allowed to execute.
            </p>
          </div>

          {approvals && (
            <div className="rounded-full border border-amber-900 bg-amber-950 px-3 py-1 text-xs font-medium text-amber-400">
              {approvals.length} Pending
            </div>
          )}
        </div>
      </header>

      <div className="p-8">
        {!approvals ? (
          <ErrorState />
        ) : approvals.length === 0 ? (
          <EmptyState />
        ) : (
          <div className="space-y-5">
            {approvals.map(
              (approval) => (
                <form
                  key={approval.id}
                  action={resolveApproval}
                  className="overflow-hidden rounded-xl border border-zinc-800 bg-zinc-950"
                >
                  <input
                    type="hidden"
                    name="approval_id"
                    value={approval.id}
                  />

                  <input
                    type="hidden"
                    name="run_id"
                    value={approval.run_id}
                  />

                  <div className="border-b border-zinc-800 p-6">
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="rounded-full border border-amber-900 bg-amber-950 px-2.5 py-1 text-xs font-medium text-amber-400">
                            Approval Required
                          </span>

                          <span className="text-xs text-zinc-600">
                            {formatDate(
                              approval.created_at
                            )}
                          </span>
                        </div>

                        <h2 className="mt-4 text-lg font-semibold text-white">
                          {humanize(
                            approval.action_name
                          )}
                        </h2>

                        <p className="mt-1 text-sm text-zinc-500">
                          Requested by{" "}
                          <span className="text-zinc-300">
                            {approval.agent_name}
                          </span>
                        </p>
                      </div>

                      <Link
                        href={`/runs/${approval.run_id}`}
                        className="text-sm text-cyan-400 transition hover:text-cyan-300"
                      >
                        View Run →
                      </Link>
                    </div>

                    <div className="mt-6 grid gap-4 md:grid-cols-2">
                      <InfoCard
                        label="Resource"
                        value={
                          approval.resource ??
                          "None"
                        }
                      />

                      <InfoCard
                        label="Action ID"
                        value={shortId(
                          approval.action_id
                        )}
                      />
                    </div>

                    <div className="mt-4 rounded-lg border border-zinc-800 bg-black p-4">
                      <div className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                        Arguments
                      </div>

                      <div className="mt-3">
                        <ArgumentsView
                          arguments={
                            approval.arguments
                          }
                        />
                      </div>
                    </div>
                  </div>

                  <div className="border-b border-zinc-800 bg-black/30 p-6">
                    <div className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                      Why ControlForge stopped it
                    </div>

                    <p className="mt-3 max-w-3xl text-sm leading-6 text-zinc-300">
                      {approval.reason}
                    </p>
                  </div>

                  <div className="p-6">
                    <div className="grid gap-4 md:grid-cols-2">
                      <label>
                        <div className="mb-2 text-xs font-medium text-zinc-500">
                          Reviewer
                        </div>

                        <input
                          name="resolved_by"
                          required
                          placeholder="Jeremy"
                          className="w-full rounded-lg border border-zinc-700 bg-black px-3 py-2.5 text-sm text-white outline-none transition placeholder:text-zinc-700 focus:border-cyan-700"
                        />
                      </label>

                      <label>
                        <div className="mb-2 text-xs font-medium text-zinc-500">
                          Review note
                        </div>

                        <input
                          name="note"
                          placeholder="Optional note"
                          className="w-full rounded-lg border border-zinc-700 bg-black px-3 py-2.5 text-sm text-white outline-none transition placeholder:text-zinc-700 focus:border-cyan-700"
                        />
                      </label>
                    </div>

                    <div className="mt-6 flex justify-end gap-3">
                      <button
                        type="submit"
                        name="resolution"
                        value="deny"
                        className="rounded-lg border border-red-900 bg-red-950/40 px-4 py-2.5 text-sm font-medium text-red-400 transition hover:bg-red-950"
                      >
                        Deny
                      </button>

                      <button
                        type="submit"
                        name="resolution"
                        value="approve"
                        className="rounded-lg border border-emerald-800 bg-emerald-950 px-4 py-2.5 text-sm font-medium text-emerald-400 transition hover:bg-emerald-900"
                      >
                        Approve
                      </button>
                    </div>
                  </div>
                </form>
              )
            )}
          </div>
        )}
      </div>
    </div>
  );
}


function InfoCard({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-black p-4">
      <div className="text-xs font-medium uppercase tracking-wide text-zinc-500">
        {label}
      </div>

      <div className="mt-2 font-mono text-sm text-zinc-300">
        {value}
      </div>
    </div>
  );
}


function ArgumentsView({
  arguments: values,
}: {
  arguments: Record<string, unknown>;
}) {
  const entries =
    Object.entries(values);

  if (entries.length === 0) {
    return (
      <div className="text-sm text-zinc-600">
        No arguments supplied.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {entries.map(
        ([key, value]) => (
          <div
            key={key}
            className="flex items-center justify-between gap-6 text-sm"
          >
            <span className="text-zinc-500">
              {humanize(key)}
            </span>

            <span className="font-mono text-zinc-200">
              {formatValue(value)}
            </span>
          </div>
        )
      )}
    </div>
  );
}


function ErrorState() {
  return (
    <div className="rounded-xl border border-red-950 bg-red-950/20 p-6">
      <div className="font-medium text-red-400">
        Unable to load approvals
      </div>

      <p className="mt-2 text-sm text-zinc-500">
        The dashboard could not retrieve
        pending approvals from ControlForge.
      </p>
    </div>
  );
}


function EmptyState() {
  return (
    <div className="rounded-xl border border-dashed border-zinc-800 p-12 text-center">
      <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full border border-emerald-900 bg-emerald-950 text-emerald-400">
        ✓
      </div>

      <h2 className="mt-4 font-medium text-zinc-200">
        No approvals waiting
      </h2>

      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-zinc-500">
        Sensitive actions requiring human
        authorization will appear here.
      </p>
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
        part.charAt(0).toUpperCase() +
        part.slice(1)
    )
    .join(" ");
}


function shortId(
  id: string
) {
  return `${id.slice(0, 8)}...`;
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


function formatValue(
  value: unknown
) {
  if (
    typeof value === "number"
  ) {
    return String(value);
  }

  if (
    typeof value === "string"
  ) {
    return value;
  }

  if (
    typeof value === "boolean"
  ) {
    return value
      ? "true"
      : "false";
  }

  return JSON.stringify(value);
}