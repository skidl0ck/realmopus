"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { useCurrencySymbol } from "@/lib/currency";
import type { Contract, Installment } from "@/types";

async function fetchMyContracts(): Promise<Contract[]> {
  const { data } = await apiClient.get("/sales/contracts/");
  return data.results ?? data;
}

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-sand/20 text-sand",
  partially_paid: "bg-marigold/20 text-marigold",
  paid: "bg-sage/20 text-sage",
  overdue: "bg-rust/20 text-rust",
};

const CONTRACT_STATUS_STYLES: Record<string, string> = {
  draft: "bg-sand/20 text-sand",
  active: "bg-sage/20 text-sage",
  completed: "bg-marigold/20 text-marigold",
  cancelled: "bg-rust/20 text-rust",
  defaulted: "bg-rust/20 text-rust",
};

export default function SchedulePage() {
  const currency = useCurrencySymbol();
  const { data: contracts, isLoading } = useQuery({
    queryKey: ["my-contracts-schedule"],
    queryFn: fetchMyContracts,
  });
  // Collapsed state per contract, keyed by id -- everything defaults open
  // (shows all schedules, paid and pending, right away), collapsing is
  // purely an optional way to reduce clutter once you have more than one.
  const [collapsedIds, setCollapsedIds] = useState<Set<string>>(new Set());

  function toggle(id: string) {
    setCollapsedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  return (
    <div>
      <h1 className="font-display text-2xl mb-1 text-cream">Payment Schedule</h1>
      <p className="text-sand text-sm mb-8">
        Your full amortization schedule for every contract, including fees and any penalties.
      </p>

      {isLoading && <p className="text-sand">Loading…</p>}
      {!isLoading && (!contracts || contracts.length === 0) && (
        <p className="text-sand">No contract found.</p>
      )}

      <div className="space-y-4">
        {(contracts ?? []).map((contract) => {
          const isOpen = !collapsedIds.has(contract.id);
          return (
            <div key={contract.id} className="rounded-2xl border border-clay bg-clay overflow-hidden">
              <button
                onClick={() => toggle(contract.id)}
                className="w-full flex items-center justify-between gap-3 px-4 py-3 text-left hover:bg-ink/40 transition"
                aria-expanded={isOpen}
              >
                <div className="min-w-0">
                  <p className="font-display text-cream truncate">
                    {contract.contract_number}
                    {contract.lot_display && <span className="text-sand font-body"> — {contract.lot_display}</span>}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${CONTRACT_STATUS_STYLES[contract.status] ?? "bg-sand/20 text-sand"}`}>
                      {contract.status.replace("_", " ")}
                    </span>
                    {contract.outstanding_balance !== undefined && (
                      <span className="text-xs text-sand">
                        Balance: {currency}{Number(contract.outstanding_balance).toLocaleString()}
                      </span>
                    )}
                  </div>
                </div>
                <span className="text-sand text-lg shrink-0">{isOpen ? "\u2212" : "+"}</span>
              </button>

              {isOpen && (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-ink text-sand text-left">
                      <tr>
                        <th className="px-4 py-3 font-medium">#</th>
                        <th className="px-4 py-3 font-medium">
                          {contract.payment_plan_type === "full_payment" ? "Contract date" : "Due date"}
                        </th>
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
                            <span className={`text-xs px-2 py-1 rounded-full font-medium ${STATUS_STYLES[inst.status]}`}>
                              {inst.status.replace("_", " ")}
                            </span>
                          </td>
                        </tr>
                      ))}
                      {(contract.installments ?? []).length === 0 && (
                        <tr>
                          <td colSpan={5} className="px-4 py-6 text-center text-sand">
                            No schedule generated for this contract yet.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}