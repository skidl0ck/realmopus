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
  pending: "bg-stone-100 text-stone-600",
  partially_paid: "bg-amber-100 text-amber-800",
  paid: "bg-emerald-100 text-emerald-800",
  overdue: "bg-red-100 text-red-700",
};

export default function SchedulePage() {
  const currency = useCurrencySymbol();
  const { data: contract, isLoading } = useQuery({
    queryKey: ["my-contract-schedule"],
    queryFn: fetchMyContract,
  });

  return (
    <div>
      <h1 className="font-serif text-2xl mb-1">Payment Schedule</h1>
      <p className="text-stone-500 text-sm mb-8">
        Your full amortization schedule, including fees and any penalties.
      </p>

      {isLoading && <p className="text-stone-500">Loading…</p>}
      {!isLoading && !contract && <p className="text-stone-500">No contract found.</p>}

      {contract && (
        <div className="rounded-2xl border border-stone-200 bg-white overflow-hidden shadow-sm">
          <table className="w-full text-sm">
            <thead className="bg-stone-50 text-stone-500 text-left">
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
                <tr key={inst.id} className="border-t border-stone-100">
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