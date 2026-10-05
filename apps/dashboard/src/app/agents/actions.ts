"use server";

import {
  revalidatePath,
} from "next/cache";

import {
  createAgent,
  rotateAgentKey,
} from "@/lib/api";


export type CredentialActionState = {
  status:
    | "idle"
    | "success"
    | "error";

  message?: string;

  agentId?: string;
  apiKey?: string;
  apiKeyPrefix?: string;
};


export async function createAgentAction(
  _previousState:
    CredentialActionState,
  formData: FormData
): Promise<CredentialActionState> {
  const name = String(
    formData.get("name") ?? ""
  ).trim();

  const rawDescription =
    String(
      formData.get(
        "description"
      ) ?? ""
    ).trim();

  if (!name) {
    return {
      status: "error",
      message:
        "Agent name is required.",
    };
  }

  const result =
    await createAgent(
      name,
      rawDescription ||
        null
    );

  if (!result) {
    return {
      status: "error",
      message:
        "Agent could not be created. Check the API and admin credential.",
    };
  }

  revalidatePath("/agents");

  return {
    status: "success",
    message:
      "Agent registered. Save this API key now — ControlForge will not show it again.",
    agentId: result.id,
    apiKey: result.api_key,
    apiKeyPrefix:
      result.api_key_prefix ??
      undefined,
  };
}


export async function rotateAgentKeyAction(
  _previousState:
    CredentialActionState,
  formData: FormData
): Promise<CredentialActionState> {
  const agentId = String(
    formData.get(
      "agent_id"
    ) ?? ""
  );

  if (!agentId) {
    return {
      status: "error",
      message:
        "Agent ID is missing.",
    };
  }

  const result =
    await rotateAgentKey(
      agentId
    );

  if (!result) {
    return {
      status: "error",
      message:
        "Credential could not be provisioned. Check the API and admin credential.",
    };
  }

  revalidatePath("/agents");
  revalidatePath(
    `/agents/${agentId}`
  );

  return {
    status: "success",
    message:
      "Credential provisioned. Save this API key now — it cannot be recovered later.",
    agentId: result.id,
    apiKey: result.api_key,
    apiKeyPrefix:
      result.api_key_prefix ??
      undefined,
  };
}