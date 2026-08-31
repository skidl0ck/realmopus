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
  const [drawerOpen, setDrawerOpen] = useState(false);

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

  // Close the drawer automatically on navigation, so it doesn't linger open
  // over the new page after tapping a link.
  useEffect(() => {
    setDrawerOpen(false);
  }, [pathname]);

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

  const navLinks = (
    <>
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
    </>
  );

  return (
    <div className="flex-1 flex flex-col sm:flex-row bg-ink">
      {/* Mobile header — hamburger toggle, hidden from sm: up since the sidebar is always visible there */}
      <header className="sm:hidden sticky top-0 z-30 flex items-center justify-between px-4 py-3 bg-clay border-b border-clay">
        <p className="text-xs uppercase tracking-wide text-sand/70">Client Portal</p>
        <button
          onClick={() => setDrawerOpen(true)}
          aria-label="Open menu"
          className="text-cream p-1"
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M4 6h16M4 12h16M4 18h16" strokeLinecap="round" />
          </svg>
        </button>
      </header>

      {/* Backdrop — mobile only, shown while the drawer is open */}
      {drawerOpen && (
        <div
          className="sm:hidden fixed inset-0 z-40 bg-ink/70"
          onClick={() => setDrawerOpen(false)}
        />
      )}

      <aside
        className={`w-64 shrink-0 border-r border-clay bg-clay px-4 py-8 fixed inset-y-0 left-0 z-50 transform transition-transform duration-200 ease-in-out sm:static sm:translate-x-0 sm:transition-none ${
          drawerOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between mb-4 sm:block">
          <p className="text-xs uppercase tracking-wide text-sand/70 px-3">
            Client Portal
          </p>
          <button
            onClick={() => setDrawerOpen(false)}
            aria-label="Close menu"
            className="sm:hidden text-sand/70 hover:text-cream p-1"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6 6 18M6 6l12 12" strokeLinecap="round" />
            </svg>
          </button>
        </div>
        {navLinks}
      </aside>

      <div className="flex-1 px-6 sm:px-10 py-10 max-w-4xl overflow-x-hidden">{children}</div>
      <ChatWidget />
    </div>
  );
}