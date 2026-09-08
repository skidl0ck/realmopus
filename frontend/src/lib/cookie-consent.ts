/**
 * Cookie/storage consent, covering both real cookies and localStorage --
 * GDPR's cookie rules apply to "cookies or similar technologies", which
 * includes localStorage, not just literal HTTP cookies.
 *
 * This app has two tiers, not the usual three or four:
 *   - Necessary: auth tokens (access/refresh/user in localStorage). Always
 *     active, never asked about -- a logged-in session can't work without
 *     them, and GDPR doesn't require consent for storage that's necessary
 *     for a service the visitor explicitly requested (choosing to log in).
 *   - Functional: the site-config cache (avoids a flash of the wrong
 *     company name on refresh) and the anonymous chat session ID (lets a
 *     conversation survive a refresh). Neither is strictly necessary --
 *     the site still works without them, just with a rougher edge -- so
 *     both require opt-in consent and are what this module actually gates.
 *
 * There's no analytics/marketing tier because this app doesn't have any
 * analytics or marketing scripts to gate -- adding one here that does
 * nothing would be misleading, not thorough.
 */

export interface CookieConsent {
  functional: boolean;
  decidedAt: string;
}

const CONSENT_KEY = "cookie-consent";

// Storage keys that live in OTHER modules (site-config.ts, chat-store.ts)
// but need clearing the moment functional consent is revoked. Centralized
// here rather than importing those modules directly, which would create a
// circular dependency -- they both need to import *this* file to check
// consent in the first place.
const FUNCTIONAL_STORAGE_KEYS = ["site-config-cache", "realmopus_chat_session_id"];

export function getStoredConsent(): CookieConsent | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(CONSENT_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

/** Whether the visitor has made ANY choice yet -- distinct from what they
 * chose. Used to decide whether to show the initial banner at all. */
export function hasDecided(): boolean {
  return getStoredConsent() !== null;
}

/** Whether functional storage is currently allowed. Defaults to false
 * (not yet decided, or explicitly declined) -- consent must be an
 * affirmative opt-in, never assumed. */
export function hasFunctionalConsent(): boolean {
  return getStoredConsent()?.functional ?? false;
}

export function saveConsent(functional: boolean) {
  if (typeof window === "undefined") return;
  const consent: CookieConsent = { functional, decidedAt: new Date().toISOString() };
  try {
    localStorage.setItem(CONSENT_KEY, JSON.stringify(consent));
  } catch {
    return;
  }
  if (!functional) {
    // Revoking isn't just "stop writing new functional data" -- anything
    // already stored under that tier gets removed immediately too, rather
    // than left sitting there stale until it happens to get overwritten.
    FUNCTIONAL_STORAGE_KEYS.forEach((key) => {
      try {
        localStorage.removeItem(key);
      } catch {
        // ignore
      }
    });
  }
  // Lets modules like site-config.ts re-attempt a write the moment consent
  // is granted -- their own write effects only re-run when their actual
  // data changes, which consent alone doesn't trigger (the data was
  // already fetched before the visitor ever made a choice), so without
  // this, accepting functional cookies would silently do nothing until
  // some unrelated data change happened to fire the effect again.
  window.dispatchEvent(new Event("cookie-consent-changed"));
}