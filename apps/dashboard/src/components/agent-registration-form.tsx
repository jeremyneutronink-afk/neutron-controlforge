"use client";

import {
  useActionState,
} from "react";

import {
  createAgentAction,
  CredentialActionState,
} from "@/app/agents/actions";


const initialState:
  CredentialActionState = {
    status: "idle",
  };


export function AgentRegistrationForm() {
  const [
    state,
    formAction,
    pending,
  ] = useActionState(
    createAgentAction,
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

  return (
    <div>
      <form
        action={formAction}
        className="rounded-xl border border-zinc-800 bg-zinc-950 p-6"
      >
        <div className="grid gap-4 md:grid-cols-[1fr_2fr_auto] md:items-end">
          <label>
            <div className="mb-2 text-xs font-medium text-zinc-500">
              Agent name
            </div>

            <input
              name="name"
              required
              placeholder="Support Agent"
              className="w-full rounded-lg border border-zinc-700 bg-black px-3 py-2.5 text-sm text-white outline-none transition placeholder:text-zinc-700 focus:border-cyan-700"
            />
          </label>

          <label>
            <div className="mb-2 text-xs font-medium text-zinc-500">
              Description
            </div>

            <input
              name="description"
              placeholder="Handles customer support workflows"
              className="w-full rounded-lg border border-zinc-700 bg-black px-3 py-2.5 text-sm text-white outline-none transition placeholder:text-zinc-700 focus:border-cyan-700"
            />
          </label>

          <button
            type="submit"
            disabled={pending}
            className="rounded-lg border border-cyan-800 bg-cyan-950 px-5 py-2.5 text-sm font-medium text-cyan-300 transition hover:bg-cyan-900 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {pending
              ? "Registering..."
              : "Register Agent"}
          </button>
        </div>
      </form>

      {state.status ===
        "error" && (
        <div className="mt-4 rounded-xl border border-red-900 bg-red-950/30 p-4 text-sm text-red-400">
          {state.message}
        </div>
      )}

      {state.status ===
        "success" &&
        state.apiKey && (
          <div className="mt-4 rounded-xl border border-amber-800 bg-amber-950/20 p-5">
            <div className="text-sm font-semibold text-amber-300">
              Save this API key now
            </div>

            <p className="mt-2 text-sm leading-6 text-zinc-400">
              Only the hash is stored by
              ControlForge. Once this message
              disappears, the raw key cannot
              be retrieved.
            </p>

            <div className="mt-4 flex flex-col gap-3 md:flex-row">
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
          </div>
        )}
    </div>
  );
}