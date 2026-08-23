import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

async function fetchCurrencySymbol(): Promise<string> {
  const { data } = await apiClient.get("/site-config/");
  return data.currency_symbol;
}

/**
 * The site-wide currency symbol, configured in Business Settings. Display
 * only — no conversion is ever applied to the underlying amounts.
 * Falls back to ₱ while loading or if the request fails, so nothing ever
 * renders blank.
 */
export function useCurrencySymbol(): string {
  const { data } = useQuery({
    queryKey: ["site-config", "currency"],
    queryFn: fetchCurrencySymbol,
    staleTime: 5 * 60 * 1000,
  });
  return data ?? "₱";
}