import { getHealth } from "@/lib/api";

export async function ApiStatus() {
  const health = await getHealth();

  const healthy = health?.status === "ok";

  return (
    <div className="flex items-center gap-2">
      <span
        className={`h-2.5 w-2.5 rounded-full ${
          healthy ? "bg-emerald-400" : "bg-red-400"
        }`}
      />

      <span className="text-sm text-zinc-400">
        API {healthy ? "Healthy" : "Unavailable"}
      </span>
    </div>
  );
}