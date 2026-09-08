"use client";

import Link from "next/link";
import { useAuthModalStore } from "@/lib/auth-modal-store";
import { useCompanyName } from "@/lib/site-config";
import { useCookieSettingsStore } from "@/lib/cookie-settings-store";
import { SierraMadreMotif } from "@/components/sierra-madre-motif";

export function SiteFooter() {
  const openAuthModal = useAuthModalStore((s) => s.open);
  const openCookieSettings = useCookieSettingsStore((s) => s.open);
  const companyName = useCompanyName();

  return (
    <footer className="bg-accent-900">
      <SierraMadreMotif className="w-full h-10 sm:h-14 block" />

      <div className="mx-auto max-w-6xl px-6 py-12 grid gap-10 sm:grid-cols-4">
        <div className="sm:col-span-2">
          <p className="font-display font-semibold text-lg uppercase text-bg mb-2">{companyName}</p>
          <p className="text-sm text-neutral-300 max-w-xs leading-relaxed">
            Quality lots and ready-to-build subdivisions across Cagayan Valley
            — flexible full or installment payment plans, with everything
            manageable online.
          </p>
        </div>

        <div>
          <p className="text-xs uppercase tracking-wide text-neutral-400 font-semibold mb-3">Explore</p>
          <ul className="space-y-2 text-sm text-neutral-300">
            <li><Link href="/lots" className="hover:text-accent-300 transition">Browse lots</Link></li>
            <li><Link href="/#offerings" className="hover:text-accent-300 transition">What we offer</Link></li>
            <li><Link href="/#how-it-works" className="hover:text-accent-300 transition">How it works</Link></li>
          </ul>
        </div>

        <div>
          <p className="text-xs uppercase tracking-wide text-neutral-400 font-semibold mb-3">Account</p>
          <ul className="space-y-2 text-sm text-neutral-300">
            <li>
              <button onClick={() => openAuthModal("register")} className="hover:text-accent-300 transition cursor-pointer">
                Create an account
              </button>
            </li>
            <li>
              <button onClick={() => openAuthModal("login")} className="hover:text-accent-300 transition cursor-pointer">
                Client login
              </button>
            </li>
          </ul>
        </div>
      </div>

      <div className="border-t border-neutral-700/50">
        <div className="mx-auto max-w-6xl px-6 py-6 flex flex-col sm:flex-row justify-between gap-2 text-xs text-neutral-400">
          <p>© {new Date().getFullYear()} {companyName}. All rights reserved.</p>
          <div className="flex gap-4">
            <Link href="/privacy" className="hover:text-accent-300 transition">Privacy &amp; Cookies</Link>
            <button onClick={openCookieSettings} className="hover:text-accent-300 transition cursor-pointer">
              Cookie Settings
            </button>
          </div>
          <p>Built on RealmOpus — a real estate sales &amp; operations platform.</p>
        </div>
      </div>
    </footer>
  );
}