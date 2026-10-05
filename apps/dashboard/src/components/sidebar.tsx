"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";


type SidebarProps = {
  pendingApprovals: number;
};


const navigation = [
  {
    name: "Overview",
    href: "/",
  },
  {
    name: "Agents",
    href: "/agents",
  },
  {
    name: "Runs",
    href: "/runs",
  },
  {
    name: "Approvals",
    href: "/approvals",
  },
  {
    name: "Security Tests",
    href: "/security-tests",
  },
  {
    name: "Findings",
    href: "/findings",
  },
];


export function Sidebar({
  pendingApprovals,
}: SidebarProps) {
  const pathname = usePathname();

  function isActive(
    href: string
  ) {
    if (href === "/") {
      return pathname === "/";
    }

    return (
      pathname === href ||
      pathname.startsWith(
        `${href}/`
      )
    );
  }

  return (
    <aside className="flex min-h-screen w-64 shrink-0 flex-col border-r border-zinc-800 bg-zinc-950">
      <div className="border-b border-zinc-800 px-6 py-6">
        <div className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-400">
          Neutron
        </div>

        <div className="mt-1 text-xl font-semibold text-white">
          ControlForge
        </div>

        <div className="mt-2 text-xs text-zinc-500">
          AI Agent Control Plane
        </div>
      </div>

      <nav className="flex-1 px-3 py-5">
        <div className="space-y-1">
          {navigation.map(
            (item) => {
              const active =
                isActive(
                  item.href
                );

              const showApprovalBadge =
                item.href ===
                  "/approvals" &&
                pendingApprovals > 0;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={
                    active
                      ? "flex items-center justify-between rounded-lg border border-cyan-950 bg-cyan-950/50 px-3 py-2.5 text-sm font-medium text-cyan-300"
                      : "flex items-center justify-between rounded-lg border border-transparent px-3 py-2.5 text-sm text-zinc-400 transition hover:bg-zinc-900 hover:text-white"
                  }
                >
                  <span>
                    {item.name}
                  </span>

                  {showApprovalBadge && (
                    <span className="min-w-6 rounded-full border border-amber-800 bg-amber-950 px-1.5 py-0.5 text-center text-xs font-semibold text-amber-400">
                      {
                        pendingApprovals
                      }
                    </span>
                  )}
                </Link>
              );
            }
          )}
        </div>
      </nav>

      <div className="border-t border-zinc-800 px-3 py-5">
        <Link
          href="/settings"
          className={
            isActive("/settings")
              ? "block rounded-lg border border-cyan-950 bg-cyan-950/50 px-3 py-2.5 text-sm font-medium text-cyan-300"
              : "block rounded-lg border border-transparent px-3 py-2.5 text-sm text-zinc-500 transition hover:bg-zinc-900 hover:text-white"
          }
        >
          Settings
        </Link>

        <div className="mt-4 px-3 text-xs text-zinc-700">
          ControlForge v0.1.0
        </div>
      </div>
    </aside>
  );
}