"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { Lot } from "@/types";
import { useCurrencySymbol } from "@/lib/currency";

const STATUS_STYLES: Record<string, string> = {
  available: "bg-sage/20 text-sage",
  reserved: "bg-marigold/20 text-marigold",
  sold: "bg-sand/20 text-sand",
  on_hold: "bg-rust/20 text-rust",
};

async function fetchLots(): Promise<Lot[]> {
  const { data } = await apiClient.get("/properties/lots/");
  return data.results ?? data;
}

export default function LotsPage() {
  const currency = useCurrencySymbol();
  const { data: lots, isLoading, isError } = useQuery({
    queryKey: ["lots"],
    queryFn: fetchLots,
  });

  return (
    <main className="flex-1 bg-ink mx-auto max-w-6xl px-6 py-16 w-full">
      <h1 className="font-display text-3xl mb-2 text-cream">Available Lots</h1>
      <p className="text-sand mb-10">
        Browse our current inventory. Reserve a lot to hold your spot while we
        prepare your contract.
      </p>

      {isLoading && <p className="text-sand">Loading lots…</p>}
      {isError && (
        <p className="text-rust">
          Couldn&apos;t load lots right now — check that the backend API is running.
        </p>
      )}

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {lots?.map((lot) => (
          <div
            key={lot.id}
            className="rounded-2xl border border-clay bg-clay p-6 hover:border-marigold/60 transition"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="font-display text-lg text-cream">
                Block {lot.block_number}, Lot {lot.lot_number}
              </span>
              <span
                className={`text-xs px-2 py-1 rounded-full font-medium ${STATUS_STYLES[lot.status]}`}
              >
                {lot.status.replace("_", " ")}
              </span>
            </div>
            <p className="text-sand text-sm mb-1">{lot.area_sqm} sqm</p>
            <p className="text-marigold font-semibold text-lg font-data">
              {currency}{Number(lot.total_price).toLocaleString()}
            </p>
          </div>
        ))}
      </div>
    </main>
  );
}