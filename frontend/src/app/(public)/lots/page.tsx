"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { Lot } from "@/types";

const STATUS_STYLES: Record<string, string> = {
  available: "bg-emerald-100 text-emerald-800",
  reserved: "bg-amber-100 text-amber-800",
  sold: "bg-stone-200 text-stone-600",
  on_hold: "bg-red-100 text-red-800",
};

async function fetchLots(): Promise<Lot[]> {
  const { data } = await apiClient.get("/properties/lots/");
  return data.results ?? data;
}

export default function LotsPage() {
  const { data: lots, isLoading, isError } = useQuery({
    queryKey: ["lots"],
    queryFn: fetchLots,
  });

  return (
    <main className="flex-1 mx-auto max-w-6xl px-6 py-16 w-full">
      <h1 className="font-serif text-3xl mb-2">Available Lots</h1>
      <p className="text-stone-600 mb-10">
        Browse our current inventory. Reserve a lot to hold your spot while we
        prepare your contract.
      </p>

      {isLoading && <p className="text-stone-500">Loading lots…</p>}
      {isError && (
        <p className="text-red-600">
          Couldn&apos;t load lots right now — check that the backend API is running.
        </p>
      )}

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {lots?.map((lot) => (
          <div
            key={lot.id}
            className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm hover:shadow-md transition"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="font-serif text-lg">
                Block {lot.block_number}, Lot {lot.lot_number}
              </span>
              <span
                className={`text-xs px-2 py-1 rounded-full font-medium ${STATUS_STYLES[lot.status]}`}
              >
                {lot.status.replace("_", " ")}
              </span>
            </div>
            <p className="text-stone-500 text-sm mb-1">{lot.area_sqm} sqm</p>
            <p className="text-emerald-800 font-medium text-lg">
              ₱{Number(lot.total_price).toLocaleString()}
            </p>
          </div>
        ))}
      </div>
    </main>
  );
}
