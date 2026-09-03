import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

interface SiteConfig {
  currency_symbol: string;
  company_name: string;
  default_reservation_fee: string;
}

async function fetchSiteConfig(): Promise<SiteConfig> {
  const { data } = await apiClient.get("/site-config/");
  return data;
}

function useSiteConfig() {
  return useQuery({
    queryKey: ["site-config"],
    queryFn: fetchSiteConfig,
    staleTime: 5 * 60 * 1000,
  });
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

/**
 * The company name, configured in Business Settings — the single source of
 * truth so this never drifts out of sync with what's hardcoded in the UI.
 * Falls back to "EstateOS" while loading or if the request fails.
 */
export function useCompanyName(): string {
  const { data } = useSiteConfig();
  return data?.company_name ?? "EstateOS";
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