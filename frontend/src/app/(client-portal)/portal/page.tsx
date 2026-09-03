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
  draft: "bg-neutral-100 text-neutral-600",
  active: "bg-green-100 text-green-800",
  completed: "bg-accent-100 text-accent-800",
  cancelled: "bg-red-100 text-red-800",
  defaulted: "bg-red-100 text-red-800",
};

export default function PortalOverviewPage() {
  const currency = useCurrencySymbol();
  const { data: contracts, isLoading, isError } = useQuery({
    queryKey: ["my-contracts"],
    queryFn: fetchMyContracts,
  });

  return (
    <div>
      <h1 className="font-display font-semibold uppercase text-2xl mb-1 text-ink">My Contract</h1>
      <p className="text-neutral-600 text-sm mb-8">
        Overview of your lot purchase and current balance.
      </p>

      {isLoading && <p className="text-neutral-600">Loading…</p>}
      {isError && <p className="text-red-800">Couldn&apos;t load your contract right now.</p>}
      {contracts?.length === 0 && (
        <p className="text-neutral-600">You don&apos;t have any contracts yet.</p>
      )}

      <div className="space-y-6">
        {contracts?.map((contract) => (
          <div
            key={contract.id}
            className="border border-divider p-6"
          >
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="font-display font-semibold uppercase text-lg text-ink">{contract.contract_number}</p>
                <p className="text-neutral-600 text-sm">{contract.lot_display}</p>
              </div>
              <span
                className={`tag ${STATUS_STYLES[contract.status]}`}
              >
                {contract.status}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm mb-4">
              <div>
                <p className="text-neutral-600/70">Total price</p>
                <p className="font-medium text-ink font-data">
                  {currency}{Number(contract.total_contract_price).toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-neutral-600/70">Down payment</p>
                <p className="font-medium text-ink font-data">{currency}{Number(contract.down_payment).toLocaleString()}</p>
              </div>
              <div>
                <p className="text-neutral-600/70">Total paid</p>
                <p className="font-medium text-ink font-data">
                  {currency}{Number(contract.total_paid ?? 0).toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-neutral-600/70">Balance</p>
                <p className="font-medium text-accent font-data">
                  {currency}{Number(contract.outstanding_balance ?? 0).toLocaleString()}
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <Link
                href="/portal/schedule"
                className="text-sm text-accent font-medium hover:underline"
              >
                View payment schedule →
              </Link>
              <Link href="/portal/pay" className="text-sm text-accent font-medium hover:underline">
                Make a payment →
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}