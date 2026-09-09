import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { hasFunctionalConsent } from "@/lib/cookie-consent";

interface SiteConfig {
  currency_symbol: string;
  company_name: string;
  default_reservation_fee: string;
  default_penalty_rate_percent: string;
  default_interest_rate_percent: string;
  reservation_hold_days: number;
  max_reservation_extensions: number;
}

const CACHE_KEY = "site-config-cache";

async function fetchSiteConfig(): Promise<SiteConfig> {
  const { data } = await apiClient.get("/site-config/");
  return data;
}

/** Reads whatever site config was last successfully fetched, if anything --
 * used as placeholderData below so a page refresh shows last time's real
 * company name/currency immediately, instead of the generic fallback
 * flashing on screen for the moment before the fresh fetch resolves.
 * Gated behind functional consent -- this cache is exactly the kind of
 * "not strictly necessary" storage the cookie settings panel lets a
 * visitor decline; if they have, this simply behaves as if nothing were
 * ever cached, same as a first-ever visit. */
function readCachedSiteConfig(): SiteConfig | undefined {
  if (typeof window === "undefined") return undefined;
  if (!hasFunctionalConsent()) return undefined;
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    return raw ? JSON.parse(raw) : undefined;
  } catch {
    return undefined;
  }
}

function useSiteConfig() {
  // Server-side rendering has no localStorage at all, so the server's HTML
  // is always generated with no cached placeholder -- if the client's very
  // first render (during hydration) went and read localStorage right away,
  // it could produce different output than that server HTML in the same
  // pass, and React throws a hydration-mismatch error over the difference.
  // hydrated starts false (matching the server, which has no concept of it
  // at all) and only flips true inside an effect -- guaranteed to run after
  // hydration has already committed, never during it -- so the client's
  // first render is always identical to the server's, and the cached value
  // only takes over in the very next render right after, not the same one.
  const [hydrated, setHydrated] = useState(false);
  useEffect(() => setHydrated(true), []);

  const query = useQuery({
    queryKey: ["site-config"],
    queryFn: fetchSiteConfig,
    staleTime: 5 * 60 * 1000,
    placeholderData: hydrated ? readCachedSiteConfig() : undefined,
  });

  useEffect(() => {
    function writeIfConsented() {
      if (!query.data || typeof window === "undefined") return;
      if (!hasFunctionalConsent()) return;
      try {
        localStorage.setItem(CACHE_KEY, JSON.stringify(query.data));
      } catch {
        // Storage unavailable (private browsing, quota, disabled) -- caching
        // is a nice-to-have here, not something worth surfacing an error for.
      }
    }
    // Covers the normal case (data just arrived) directly, and also
    // re-attempts the write when consent itself changes -- accepting
    // functional cookies doesn't change query.data at all (the site config
    // was already fetched before the visitor made a choice), so without
    // this listener, granting consent would silently do nothing until some
    // unrelated data change happened to fire this effect again.
    writeIfConsented();
    window.addEventListener("cookie-consent-changed", writeIfConsented);
    return () => window.removeEventListener("cookie-consent-changed", writeIfConsented);
  }, [query.data]);

  return query;
}

/**
 * The site-wide currency symbol, configured in Business Settings. Display
 * only — no conversion is ever applied to the underlying amounts.
 * Falls back to ₱ while loading or if the request fails, so nothing ever
 * renders blank.
 */
export function useCurrencySymbol(): string {
  const { data } = useSiteConfig();
  return data?.currency_symbol ?? "₱";
}

export function useSiteConfigQuery() {
  return useSiteConfig();
}

/**
 * The company name, configured in Business Settings — the single source of
 * truth so this never drifts out of sync with what's hardcoded in the UI.
 * Falls back to "RealmOpus" while loading or if the request fails -- in
 * practice this only shows up on someone's very first visit ever, before
 * anything's been cached locally; every visit after that shows last time's
 * real value immediately, via useSiteConfig's placeholderData above.
 */
export function useCompanyName(): string {
  const { data } = useSiteConfig();
  return data?.company_name ?? "RealmOpus";
}

/**
 * The current reservation fee, configured in Business Settings. Returns
 * undefined while still loading or on failure — deliberately NOT a 0
 * fallback, since callers use this to decide whether reserving a lot needs
 * to go through checkout at all; a stale/wrong "0" could skip checkout for
 * a lot that actually has a real fee.
 */
export function useDefaultReservationFee(): number | undefined {
  const { data } = useSiteConfig();
  return data ? Number(data.default_reservation_fee) : undefined;
}