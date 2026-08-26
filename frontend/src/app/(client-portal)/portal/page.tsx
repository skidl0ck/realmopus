"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";
import { useCurrencySymbol } from "@/lib/currency";
import type { Contract } from "@/types";

async function fetchMyContracts(): Promise<Contract[]> {
  const { data } = await apiClient.get("/sales/contracts/");
  return data.results ?? data;
}

const STATUS_STYLES: Record<string, string> = {
  draft: "bg-sand/20 text-sand",
  active: "bg-sage/20 text-sage",
  completed: "bg-marigold/20 text-marigold",
  cancelled: "bg-rust/20 text-rust",
  defaulted: "bg-rust/20 text-rust",
};

export default function PortalOverviewPage() {
  const currency = useCurrencySymbol();
  const { data: contracts, isLoading, isError } = useQuery({
    queryKey: ["my-contracts"],
    queryFn: fetchMyContracts,
  });

  return (
    <div>
      <h1 className="font-display text-2xl mb-1 text-cream">My Contract</h1>
      <p className="text-sand text-sm mb-8">
        Overview of your lot purchase and current balance.
      </p>

      {isLoading && <p className="text-sand">Loading…</p>}
      {isError && <p className="text-rust">Couldn&apos;t load your contract right now.</p>}
      {contracts?.length === 0 && (
        <p className="text-sand">You don&apos;t have any contracts yet.</p>
      )}

      <div className="space-y-6">
        {contracts?.map((contract) => (
          <div
            key={contract.id}
            className="rounded-2xl border border-clay bg-clay p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="font-display text-lg text-cream">{contract.contract_number}</p>
                <p className="text-sand text-sm">{contract.lot_display}</p>
              </div>
              <span
                className={`text-xs px-2 py-1 rounded-full font-medium ${STATUS_STYLES[contract.status]}`}
              >
                {contract.status}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm mb-4">
              <div>
                <p className="text-sand/70">Total price</p>
                <p className="font-medium text-cream font-data">
                  {currency}{Number(contract.total_contract_price).toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-sand/70">Down payment</p>
                <p className="font-medium text-cream font-data">{currency}{Number(contract.down_payment).toLocaleString()}</p>
              </div>
              <div>
                <p className="text-sand/70">Total paid</p>
                <p className="font-medium text-cream font-data">
                  {currency}{Number(contract.total_paid ?? 0).toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-sand/70">Balance</p>
                <p className="font-medium text-marigold font-data">
                  {currency}{Number(contract.outstanding_balance ?? 0).toLocaleString()}
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <Link
                href="/portal/schedule"
                className="text-sm text-marigold font-medium hover:underline"
              >
                View payment schedule →
              </Link>
              <Link href="/portal/pay" className="text-sm text-marigold font-medium hover:underline">
                Make a payment →
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}