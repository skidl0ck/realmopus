"use client";

import { useCompanyName } from "@/lib/site-config";
import { useCookieSettingsStore } from "@/lib/cookie-settings-store";

export default function PrivacyPage() {
  const companyName = useCompanyName();
  const openCookieSettings = useCookieSettingsStore((s) => s.open);

  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="font-display font-semibold text-3xl uppercase text-ink mb-6">
        Cookies &amp; browser storage
      </h1>

      <p className="text-neutral-700 leading-relaxed mb-6">
        This page describes everything {companyName} stores in your browser — there
        is no analytics or advertising tracking on this site, so this list is short
        and complete, not a summary of a longer one.
      </p>

      <section className="mb-8">
        <h2 className="font-display font-semibold text-lg uppercase text-ink mb-2">Necessary</h2>
        <p className="text-neutral-700 leading-relaxed mb-3">
          Always active — the site cannot function while logged in without these.
        </p>
        <ul className="list-disc pl-5 space-y-1 text-sm text-neutral-600">
          <li>Your login session (access and refresh tokens), so you stay signed in as you move between pages</li>
        </ul>
      </section>

      <section className="mb-8">
        <h2 className="font-display font-semibold text-lg uppercase text-ink mb-2">Functional</h2>
        <p className="text-neutral-700 leading-relaxed mb-3">
          Optional — the site works without these, just with a rougher edge. Requires
          your consent, and you can withdraw it at any time.
        </p>
        <ul className="list-disc pl-5 space-y-1 text-sm text-neutral-600">
          <li>A cached copy of this site&apos;s branding (company name, currency), so it appears instantly on your next visit instead of flashing a generic placeholder first</li>
          <li>An anonymous ID for the chat widget, so a conversation you start survives a page refresh instead of starting over</li>
        </ul>
      </section>

      <button onClick={openCookieSettings} className="btn btn-primary">
        Change my cookie preferences
      </button>
    </div>
  );
}