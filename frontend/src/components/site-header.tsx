"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthModalStore } from "@/lib/auth-modal-store";
import { useAuthStore } from "@/lib/auth-store";
import { useCompanyName } from "@/lib/site-config";
import { getStoredUser, logout, dashboardPathForRole } from "@/lib/auth";

export function SiteHeader() {
  const [open, setOpen] = useState(false);
  const router = useRouter();
  const openAuthModal = useAuthModalStore((s) => s.open);
  const { user, setUser } = useAuthStore();
  const companyName = useCompanyName();

  // The public site never redirects an unauthenticated visitor away (unlike
  // the portal/dashboard layouts), so this only rehydrates the shared store
  // from a token that's already there — it doesn't gate access to anything.
  useEffect(() => {
    const stored = getStoredUser();
    if (stored) setUser(stored);
  }, [setUser]);

  function handleSignOut() {
    logout();
    setUser(null);
    setOpen(false);
    router.push("/");
  }

  return (
    <header className="sticky top-0 z-40 bg-ink/90 backdrop-blur border-b border-clay">
      <div className="mx-auto max-w-6xl px-6 h-16 flex items-center justify-between">
        <Link href="/" className="font-display text-lg font-semibold text-cream tracking-tight">
          {companyName}
        </Link>

        <nav className="hidden sm:flex items-center gap-8 text-sm font-medium text-sand">
          <Link href="/#offerings" className="hover:text-marigold transition">What we offer</Link>
          <Link href="/lots" className="hover:text-marigold transition">Browse lots</Link>
          <Link href="/#how-it-works" className="hover:text-marigold transition">How it works</Link>
        </nav>

        <div className="hidden sm:flex items-center gap-3">
          {user ? (
            <>
              <Link
                href={dashboardPathForRole(user.role)}
                className="text-sm font-medium text-sand hover:text-marigold transition"
              >
                {user.first_name || user.username}
              </Link>
              <button
                onClick={handleSignOut}
                className="rounded-full bg-clay text-cream text-sm font-semibold px-4 py-2 hover:opacity-90 transition cursor-pointer"
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => openAuthModal("login")}
                className="text-sm font-medium text-sand hover:text-marigold transition cursor-pointer"
              >
                Client login
              </button>
              <button
                onClick={() => openAuthModal("register")}
                className="rounded-full bg-marigold text-ink text-sm font-semibold px-4 py-2 hover:opacity-90 transition cursor-pointer"
              >
                Register
              </button>
            </>
          )}
        </div>

        <button
          onClick={() => setOpen(!open)}
          className="sm:hidden text-sand"
          aria-label="Toggle menu"
        >
          {open ? "✕" : "☰"}
        </button>
      </div>

      {open && (
        <div className="sm:hidden border-t border-clay px-6 py-4 space-y-3 text-sm font-medium text-sand">
          <Link href="/#offerings" className="block" onClick={() => setOpen(false)}>What we offer</Link>
          <Link href="/lots" className="block" onClick={() => setOpen(false)}>Browse lots</Link>
          <Link href="/#how-it-works" className="block" onClick={() => setOpen(false)}>How it works</Link>
          {user ? (
            <>
              <Link href={dashboardPathForRole(user.role)} className="block" onClick={() => setOpen(false)}>
                {user.first_name || user.username}
              </Link>
              <button className="block text-left" onClick={handleSignOut}>Sign out</button>
            </>
          ) : (
            <>
              <button
                className="block text-left"
                onClick={() => { setOpen(false); openAuthModal("login"); }}
              >
                Client login
              </button>
              <button
                className="block text-left text-marigold"
                onClick={() => { setOpen(false); openAuthModal("register"); }}
              >
                Register
              </button>
            </>
          )}
        </div>
      )}
    </header>
  );
}