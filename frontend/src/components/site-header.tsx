"use client";

import Link from "next/link";
import { useState } from "react";
import { useAuthModalStore } from "@/lib/auth-modal-store";

export function SiteHeader() {
  const [open, setOpen] = useState(false);
  const openAuthModal = useAuthModalStore((s) => s.open);

  return (
    <header className="sticky top-0 z-40 bg-stone-50/90 backdrop-blur border-b border-stone-200">
      <div className="mx-auto max-w-6xl px-6 h-16 flex items-center justify-between">
        <Link href="/" className="font-serif text-lg font-semibold text-emerald-900">
          Greenview Estates
        </Link>

        <nav className="hidden sm:flex items-center gap-8 text-sm font-medium text-stone-600">
          <Link href="/#offerings" className="hover:text-emerald-800 transition">What we offer</Link>
          <Link href="/lots" className="hover:text-emerald-800 transition">Browse lots</Link>
          <Link href="/#how-it-works" className="hover:text-emerald-800 transition">How it works</Link>
        </nav>

        <div className="hidden sm:flex items-center gap-3">
          <button
            onClick={() => openAuthModal("login")}
            className="text-sm font-medium text-stone-600 hover:text-emerald-800 transition cursor-pointer"
          >
            Client login
          </button>
          <button
            onClick={() => openAuthModal("register")}
            className="rounded-full bg-emerald-800 text-white text-sm font-medium px-4 py-2 hover:bg-emerald-900 transition cursor-pointer"
          >
            Register
          </button>
        </div>

        <button
          onClick={() => setOpen(!open)}
          className="sm:hidden text-stone-600"
          aria-label="Toggle menu"
        >
          {open ? "✕" : "☰"}
        </button>
      </div>

      {open && (
        <div className="sm:hidden border-t border-stone-200 px-6 py-4 space-y-3 text-sm font-medium text-stone-600">
          <Link href="/#offerings" className="block" onClick={() => setOpen(false)}>What we offer</Link>
          <Link href="/lots" className="block" onClick={() => setOpen(false)}>Browse lots</Link>
          <Link href="/#how-it-works" className="block" onClick={() => setOpen(false)}>How it works</Link>
          <button
            className="block text-left"
            onClick={() => { setOpen(false); openAuthModal("login"); }}
          >
            Client login
          </button>
          <button
            className="block text-left text-emerald-800"
            onClick={() => { setOpen(false); openAuthModal("register"); }}
          >
            Register
          </button>
        </div>
      )}
    </header>
  );
}