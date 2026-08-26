"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { getStoredUser, logout } from "@/lib/auth";
import { useAuthStore, NAV_ITEMS_BY_ROLE } from "@/lib/auth-store";
import { useAuthModalStore } from "@/lib/auth-modal-store";
import { apiClient } from "@/lib/api-client";
import { ChatWidget } from "@/components/chat-widget";

async function fetchUnreadCount(): Promise<number> {
  const { data } = await apiClient.get("/notifications/unread_count/");
  return data.unread_count;
}

export default function ClientPortalLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, setUser } = useAuthStore();
  const openAuthModal = useAuthModalStore((s) => s.open);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const stored = getStoredUser();
    if (!stored || stored.role !== "client") {
      openAuthModal("login", pathname);
      router.replace("/");
      return;
    }
    setUser(stored);
    setReady(true);
  }, [router, setUser, openAuthModal, pathname]);

  const { data: unreadCount } = useQuery({
    queryKey: ["unread-notification-count"],
    queryFn: fetchUnreadCount,
    enabled: ready,
    refetchInterval: 30000,
  });

  if (!ready || !user) {
    return <div className="flex-1 flex items-center justify-center bg-ink text-sand">Loading…</div>;
  }

  const navItems = NAV_ITEMS_BY_ROLE.client;

  return (
    <div className="flex-1 flex bg-ink">
      <aside className="w-64 shrink-0 border-r border-clay bg-clay px-4 py-8 hidden sm:block">
        <p className="text-xs uppercase tracking-wide text-sand/70 px-3 mb-4">
          Client Portal
        </p>
        <nav className="space-y-1">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center justify-between rounded-lg px-3 py-2 text-sm font-medium transition ${
                pathname === item.href
                  ? "bg-marigold/20 text-marigold"
                  : "text-sand hover:bg-ink"
              }`}
            >
              <span>{item.label}</span>
              {item.href === "/portal/notifications" && !!unreadCount && (
                <span className="rounded-full bg-marigold text-ink text-xs px-1.5 py-0.5 min-w-[1.25rem] text-center">
                  {unreadCount}
                </span>
              )}
            </Link>
          ))}
        </nav>
        <button
          onClick={() => {
            logout();
            router.push("/");
          }}
          className="mt-8 px-3 text-sm text-sand/70 hover:text-cream"
        >
          Sign out
        </button>
      </aside>
      <div className="flex-1 px-6 sm:px-10 py-10 max-w-4xl">{children}</div>
      <ChatWidget />
    </div>
  );
}