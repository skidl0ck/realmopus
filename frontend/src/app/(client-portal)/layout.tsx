"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { getStoredUser, logout } from "@/lib/auth";
import { useAuthStore, NAV_ITEMS_BY_ROLE } from "@/lib/auth-store";

export default function ClientPortalLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, setUser } = useAuthStore();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const stored = getStoredUser();
    if (!stored || stored.role !== "client") {
      router.replace("/login");
      return;
    }
    setUser(stored);
    setReady(true);
  }, [router, setUser]);

  if (!ready || !user) {
    return <div className="flex-1 flex items-center justify-center text-stone-400">Loading…</div>;
  }

  const navItems = NAV_ITEMS_BY_ROLE.client;

  return (
    <div className="flex-1 flex">
      <aside className="w-64 shrink-0 border-r border-stone-200 bg-white px-4 py-8 hidden sm:block">
        <p className="text-xs uppercase tracking-wide text-stone-400 px-3 mb-4">
          Client Portal
        </p>
        <nav className="space-y-1">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`block rounded-lg px-3 py-2 text-sm font-medium transition ${
                pathname === item.href
                  ? "bg-emerald-50 text-emerald-800"
                  : "text-stone-600 hover:bg-stone-50"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <button
          onClick={() => {
            logout();
            router.push("/login");
          }}
          className="mt-8 px-3 text-sm text-stone-400 hover:text-stone-600"
        >
          Sign out
        </button>
      </aside>
      <div className="flex-1 px-6 sm:px-10 py-10 max-w-4xl">{children}</div>
    </div>
  );
}