"use client";

import Link from "next/link";
import { useAuthModalStore } from "@/lib/auth-modal-store";
import { useCompanyName } from "@/lib/site-config";
import { SierraMadreMotif } from "@/components/sierra-madre-motif";

export function SiteFooter() {
  const openAuthModal = useAuthModalStore((s) => s.open);
  const companyName = useCompanyName();

  return (
    <footer className="bg-ink">
      <SierraMadreMotif className="w-full h-10 sm:h-14 block" />

      <div className="mx-auto max-w-6xl px-6 py-12 grid gap-10 sm:grid-cols-4">
        <div className="sm:col-span-2">
          <p className="font-display text-lg font-semibold text-cream mb-2">{companyName}</p>
          <p className="text-sm text-sand max-w-xs leading-relaxed">
            Quality lots and ready-to-build subdivisions across Cagayan Valley
            — flexible full or installment payment plans, with everything
            manageable online.
          </p>
        </div>

        <div>
          <p className="text-xs uppercase tracking-wide text-sand/70 font-medium mb-3">Explore</p>
          <ul className="space-y-2 text-sm text-sand">
            <li><Link href="/lots" className="hover:text-marigold transition">Browse lots</Link></li>
            <li><Link href="/#offerings" className="hover:text-marigold transition">What we offer</Link></li>
            <li><Link href="/#how-it-works" className="hover:text-marigold transition">How it works</Link></li>
          </ul>
        </div>

        <div>
          <p className="text-xs uppercase tracking-wide text-sand/70 font-medium mb-3">Account</p>
          <ul className="space-y-2 text-sm text-sand">
            <li>
              <button onClick={() => openAuthModal("register")} className="hover:text-marigold transition">
                Create an account
              </button>
            </li>
            <li>
              <button onClick={() => openAuthModal("login")} className="hover:text-marigold transition">
                Client login
              </button>
            </li>
          </ul>
        </div>
      </div>

      <div className="border-t border-clay">
        <div className="mx-auto max-w-6xl px-6 py-6 flex flex-col sm:flex-row justify-between gap-2 text-xs text-sand/70">
          <p>© {new Date().getFullYear()} {companyName}. All rights reserved.</p>
          <p>Built on EstateOS — a real estate sales &amp; operations platform.</p>
        </div>
      </div>
    </footer>
  );
}