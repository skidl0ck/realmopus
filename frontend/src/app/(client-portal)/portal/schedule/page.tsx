"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { useCurrencySymbol } from "@/lib/currency";
import type { Contract, Installment } from "@/types";

async function fetchMyContract(): Promise<Contract | null> {
  const { data } = await apiClient.get("/sales/contracts/");
  const contracts = data.results ?? data;
  return contracts[0] ?? null;
}

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-sand/20 text-sand",
  partially_paid: "bg-marigold/20 text-marigold",
  paid: "bg-sage/20 text-sage",
  overdue: "bg-rust/20 text-rust",
};

export default function SchedulePage() {
  const currency = useCurrencySymbol();
  const { data: contract, isLoading } = useQuery({
    queryKey: ["my-contract-schedule"],
    queryFn: fetchMyContract,
  });

  return (
    <div>
      <h1 className="font-display text-2xl mb-1 text-cream">Payment Schedule</h1>
      <p className="text-sand text-sm mb-8">
        Your full amortization schedule, including fees and any penalties.
      </p>

      {isLoading && <p className="text-sand">Loading…</p>}
      {!isLoading && !contract && <p className="text-sand">No contract found.</p>}

      {contract && (
        <div className="rounded-2xl border border-clay bg-clay overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-ink text-sand text-left">
              <tr>
                <th className="px-4 py-3 font-medium">#</th>
                <th className="px-4 py-3 font-medium">Due date</th>
                <th className="px-4 py-3 font-medium">Amount due</th>
                <th className="px-4 py-3 font-medium">Paid</th>
                <th className="px-4 py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {(contract.installments ?? []).map((inst: Installment) => (
                <tr key={inst.id} className="border-t border-ink text-cream">
                  <td className="px-4 py-3">{inst.installment_number}</td>
                  <td className="px-4 py-3">{inst.due_date}</td>
                  <td className="px-4 py-3">{currency}{Number(inst.amount_due).toLocaleString()}</td>
                  <td className="px-4 py-3">{currency}{Number(inst.amount_paid).toLocaleString()}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-xs px-2 py-1 rounded-full font-medium ${STATUS_STYLES[inst.status]}`}
                    >
                      {inst.status.replace("_", " ")}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}