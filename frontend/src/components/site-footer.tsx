"use client";

import Link from "next/link";
import { useAuthModalStore } from "@/lib/auth-modal-store";

export function SiteFooter() {
  const openAuthModal = useAuthModalStore((s) => s.open);

  return (
    <footer className="border-t border-stone-200 bg-white">
      <div className="mx-auto max-w-6xl px-6 py-12 grid gap-10 sm:grid-cols-4">
        <div className="sm:col-span-2">
          <p className="font-serif text-lg font-semibold text-emerald-900 mb-2">Greenview Estates</p>
          <p className="text-sm text-stone-500 max-w-xs leading-relaxed">
            A residential lot development in Pangasinan, offering flexible
            full or installment payment plans with everything manageable
            online.
          </p>
        </div>

        <div>
          <p className="text-xs uppercase tracking-wide text-stone-400 font-medium mb-3">Explore</p>
          <ul className="space-y-2 text-sm text-stone-600">
            <li><Link href="/lots" className="hover:text-emerald-800 transition">Browse lots</Link></li>
            <li><Link href="/#offerings" className="hover:text-emerald-800 transition">What we offer</Link></li>
            <li><Link href="/#how-it-works" className="hover:text-emerald-800 transition">How it works</Link></li>
          </ul>
        </div>

        <div>
          <p className="text-xs uppercase tracking-wide text-stone-400 font-medium mb-3">Account</p>
          <ul className="space-y-2 text-sm text-stone-600">
            <li>
              <button onClick={() => openAuthModal("register")} className="hover:text-emerald-800 transition">
                Create an account
              </button>
            </li>
            <li>
              <button onClick={() => openAuthModal("login")} className="hover:text-emerald-800 transition">
                Client login
              </button>
            </li>
          </ul>
        </div>
      </div>

      <div className="border-t border-stone-200">
        <div className="mx-auto max-w-6xl px-6 py-6 flex flex-col sm:flex-row justify-between gap-2 text-xs text-stone-400">
          <p>© {new Date().getFullYear()} Greenview Estates. All rights reserved.</p>
          <p>Built on EstateOS — a real estate sales &amp; operations platform.</p>
        </div>
      </div>
    </footer>
  );
}