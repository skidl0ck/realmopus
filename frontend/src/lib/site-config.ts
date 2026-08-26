import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

interface SiteConfig {
  currency_symbol: string;
  company_name: string;
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