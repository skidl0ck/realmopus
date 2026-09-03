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
  const [authLoading, setAuthLoading] = useState(true);
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
    setAuthLoading(false);
  }, [setUser]);

  function handleSignOut() {
    logout();
    setUser(null);
    setOpen(false);
    router.push("/");
  }

  return (
    <header className="nav sticky top-0 z-40 bg-bg/95 backdrop-blur border-b border-divider">
      <div className="mx-auto max-w-6xl px-6 h-16 flex items-center justify-between w-full">
        <Link href="/" className="font-display font-semibold text-lg text-ink tracking-tight uppercase">
          {companyName}
        </Link>

        <nav className="hidden sm:flex items-center gap-8 text-sm font-medium text-neutral-700">
          <Link href="/#offerings" className="hover:text-accent transition">What we offer</Link>
          <Link href="/lots" className="hover:text-accent transition">Browse lots</Link>
          <Link href="/#how-it-works" className="hover:text-accent transition">How it works</Link>
        </nav>

        <div className="hidden sm:flex items-center gap-3">
          {authLoading ? (
            <>
              <span className="h-5 w-24 animate-pulse rounded bg-neutral-200" aria-hidden="true" />
              <span className="h-10 w-20 animate-pulse rounded bg-neutral-200" aria-hidden="true" />
            </>
          ) : user ? (
            <>
              <Link
                href={dashboardPathForRole(user.role)}
                className="text-sm font-medium text-neutral-700 hover:text-accent transition"
              >
                {user.first_name || user.username}
              </Link>
              <button
                onClick={handleSignOut}
                className="btn btn-secondary"
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => openAuthModal("login")}
                className="text-sm font-medium text-neutral-700 hover:text-accent transition cursor-pointer"
              >
                Client login
              </button>
              <button
                onClick={() => openAuthModal("register")}
                className="btn btn-primary"
              >
                Register
              </button>
            </>
          )}
        </div>

        <button
          onClick={() => setOpen(!open)}
          className="sm:hidden text-neutral-700"
          aria-label="Toggle menu"
        >
          {open ? "✕" : "☰"}
        </button>
      </div>

      {open && (
        <div className="sm:hidden border-t border-divider px-6 py-4 space-y-3 text-sm font-medium text-neutral-700">
          <Link href="/#offerings" className="block" onClick={() => setOpen(false)}>What we offer</Link>
          <Link href="/lots" className="block" onClick={() => setOpen(false)}>Browse lots</Link>
          <Link href="/#how-it-works" className="block" onClick={() => setOpen(false)}>How it works</Link>
          <hr className="border-divider" />
          {authLoading ? (
            <div className="flex gap-3" aria-label="Loading authentication options">
              <span className="h-5 w-24 animate-pulse rounded bg-neutral-200" aria-hidden="true" />
              <span className="h-5 w-16 animate-pulse rounded bg-neutral-200" aria-hidden="true" />
            </div>
          ) : user ? (
            <>
              <Link href={dashboardPathForRole(user.role)} className="block" onClick={() => setOpen(false)}>
                My Portal ({user.first_name || user.username})
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
                className="block text-left text-accent"
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