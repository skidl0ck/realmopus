// Re-exported from site-config.ts, which now also provides useCompanyName()
// and shares a single fetch/cache entry for both. Kept here so existing
// imports across the app don't need to change.
export { useCurrencySymbol } from "@/lib/site-config";