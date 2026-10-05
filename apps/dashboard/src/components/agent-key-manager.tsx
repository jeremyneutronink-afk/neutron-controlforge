"use client";

import {
  useActionState,
} from "react";

import {
  CredentialActionState,
  rotateAgentKeyAction,
} from "@/app/agents/actions";


const initialState:
  CredentialActionState = {
    status: "idle",
  };


type AgentKeyManagerProps = {
  agentId: string;
  currentPrefix: string | null;
};


export function AgentKeyManager({
  agentId,
  currentPrefix,
}: AgentKeyManagerProps) {
  const [
    state,
    formAction,
    pending,
  ] = useActionState(
    rotateAgentKeyAction,
    initialState
  );

  async function copyKey() {
    if (!state.apiKey) {
      return;
    }

    await navigator.clipboard.writeText(
      state.apiKey
    );
  }

  const hasCredential =
    currentPrefix !== null;

  return (
    <div className="mt-5 border-t border-zinc-800 pt-5">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="text-xs font-medium uppercase tracking-wide text-zinc-600">
            Agent Credential
          </div>

          {hasCredential ? (
            <div className="mt-2 font-mono text-sm text-zinc-400">
              {currentPrefix}••••••••
            </div>
          ) : (
            <div className="mt-2 text-sm text-amber-400">
              No API key provisioned
            </div>
          )}
        </div>

        <form
          action={formAction}
        >
          <input
            type="hidden"
            name="agent_id"
            value={agentId}
          />

          <button
            type="submit"
            disabled={pending}
            className={
              hasCredential
                ? "rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-500 hover:text-white disabled:opacity-50"
                : "rounded-lg border border-amber-800 bg-amber-950 px-4 py-2 text-sm font-medium text-amber-300 transition hover:bg-amber-900 disabled:opacity-50"
            }
          >
            {pending
              ? "Provisioning..."
              : hasCredential
                ? "Rotate Key"
                : "Provision Key"}
          </button>
        </form>
      </div>

      {state.status ===
        "error" && (
        <div className="mt-4 rounded-lg border border-red-900 bg-red-950/20 p-4 text-sm text-red-400">
          {state.message}
        </div>
      )}

      {state.status ===
        "success" &&
        state.apiKey && (
          <div className="mt-4 rounded-lg border border-amber-800 bg-amber-950/20 p-4">
            <div className="text-sm font-semibold text-amber-300">
              One-time API key
            </div>

            <p className="mt-2 text-sm text-zinc-400">
              Copy this somewhere secure
              before leaving the page.
            </p>

            <div className="mt-3 flex flex-col gap-3 md:flex-row">
              <code className="min-w-0 flex-1 overflow-x-auto rounded-lg border border-zinc-800 bg-black p-3 text-sm text-cyan-300">
                {state.apiKey}
              </code>

              <button
                type="button"
                onClick={copyKey}
                className="rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 hover:border-zinc-500 hover:text-white"
              >
                Copy Key
              </button>
            </div>

            {hasCredential && (
              <p className="mt-3 text-xs text-red-400">
                The previous key is now invalid.
              </p>
            )}
          </div>
        )}
    </div>
  );
}