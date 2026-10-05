import type {
  Metadata,
} from "next";

import { Sidebar } from "@/components/sidebar";
import { getDashboardApprovals } from "@/lib/api";

import "./globals.css";


export const metadata: Metadata = {
  title: "Neutron ControlForge",
  description:
    "AI agent policy enforcement, approvals, observability, and security testing.",
};


export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const approvals =
    await getDashboardApprovals();

  const pendingApprovals =
    approvals?.length ?? 0;

  return (
    <html lang="en">
      <body>
        <div className="flex min-h-screen bg-black">
          <Sidebar
            pendingApprovals={
              pendingApprovals
            }
          />

          <main className="min-w-0 flex-1">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}