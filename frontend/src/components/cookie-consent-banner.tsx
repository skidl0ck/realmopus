"use client";

import { useEffect, useState } from "react";
import { hasDecided, hasFunctionalConsent, saveConsent } from "@/lib/cookie-consent";
import { useCookieSettingsStore } from "@/lib/cookie-settings-store";

type View = "banner" | "settings";

export function CookieConsentBanner() {
  const [firstVisitPending, setFirstVisitPending] = useState(false);
  const [view, setView] = useState<View>("banner");
  const [functionalChoice, setFunctionalChoice] = useState(false);
  const reopened = useCookieSettingsStore((s) => s.isOpen);
  const closeReopened = useCookieSettingsStore((s) => s.close);

  // Only decided on the client, after mount -- matches the same
  // hydration-safety reasoning as site-config.ts's placeholderData: the
  // server has no concept of localStorage at all, so this must start false
  // (same as the server sees) and only flip inside an effect, never during
  // the render itself, or the first client render could disagree with the
  // server's and trigger a hydration mismatch.
  useEffect(() => {
    if (!hasDecided()) setFirstVisitPending(true);
  }, []);

  // Reopening via the footer link jumps straight to the settings view
  // (the visitor already knows what this is), rather than replaying the
  // first-visit pitch.
  useEffect(() => {
    if (reopened) {
      setFunctionalChoice(hasFunctionalConsent());
      setView("settings");
    }
  }, [reopened]);

  const visible = firstVisitPending || reopened;
  if (!visible) return null;

  function handleAcceptAll() {
    saveConsent(true);
    finish();
  }

  function handleNecessaryOnly() {
    saveConsent(false);
    finish();
  }

  function handleSavePreferences() {
    saveConsent(functionalChoice);
    finish();
  }

  function finish() {
    setFirstVisitPending(false);
    setView("banner");
    closeReopened();
  }

  if (view === "settings") {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center px-4 bg-black/40">
        <div className="w-full max-w-md rounded bg-bg border border-divider p-6 shadow-xl">
          <h2 className="font-display font-semibold text-lg uppercase text-ink mb-1">Cookie settings</h2>
          <p className="text-sm text-neutral-600 mb-5">
            Choose what this site is allowed to store in your browser. You can change this anytime from the link in the footer.
          </p>

          <div className="space-y-4 mb-6">
            <div className="flex items-start justify-between gap-4 border-b border-divider pb-4">
              <div>
                <p className="font-medium text-ink text-sm">Necessary</p>
                <p className="text-xs text-neutral-500 mt-0.5">
                  Keeps you signed in. Required for the site to work at all — always on.
                </p>
              </div>
              <input type="checkbox" checked disabled className="mt-1 cursor-not-allowed opacity-60" />
            </div>

            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="font-medium text-ink text-sm">Functional</p>
                <p className="text-xs text-neutral-500 mt-0.5">
                  Remembers your last-seen page branding and keeps a chat conversation going across visits. Not required — the site works fine without it.
                </p>
              </div>
              <input
                type="checkbox"
                checked={functionalChoice}
                onChange={(e) => setFunctionalChoice(e.target.checked)}
                className="mt-1 cursor-pointer"
              />
            </div>
          </div>

          <button onClick={handleSavePreferences} className="btn btn-primary btn-block w-full">
            Save preferences
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-x-0 bottom-0 z-50 border-t border-divider bg-bg shadow-lg">
      <div className="mx-auto max-w-4xl px-6 py-5 flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <p className="text-sm text-neutral-600 flex-1">
          This site stores a little information in your browser — some of it necessary
          (keeping you signed in), some of it just for convenience (remembering
          branding, keeping a chat conversation going). You can choose which of the
          optional kind to allow.
        </p>
        <div className="flex gap-2 shrink-0">
          <button
            onClick={() => {
              setFunctionalChoice(hasFunctionalConsent());
              setView("settings");
            }}
            className="btn btn-secondary"
          >
            Customize
          </button>
          <button onClick={handleNecessaryOnly} className="btn btn-secondary">
            Necessary only
          </button>
          <button onClick={handleAcceptAll} className="btn btn-primary">
            Accept all
          </button>
        </div>
      </div>
    </div>
  );
}