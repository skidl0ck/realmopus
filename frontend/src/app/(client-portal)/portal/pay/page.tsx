"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { useCurrencySymbol } from "@/lib/currency";
import type { Contract, Installment } from "@/types";

async function fetchMyContract(): Promise<Contract | null> {
  const { data } = await apiClient.get("/sales/contracts/");
  const contracts = data.results ?? data;
  return contracts[0] ?? null;
}

export default function PayPage() {
  const { data: contract } = useQuery({ queryKey: ["my-contract-pay"], queryFn: fetchMyContract });
  const currency = useCurrencySymbol();
  const [selectedInstallment, setSelectedInstallment] = useState<string>("");
  const [method, setMethod] = useState<"paypal" | "paymongo">("paypal");
  const [status, setStatus] = useState<{ type: "info" | "error"; message: string } | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const unpaidInstallments = (contract?.installments ?? []).filter(
    (i: Installment) => i.status !== "paid"
  );

  async function handlePay() {
    if (!selectedInstallment) {
      setStatus({ type: "error", message: "Select an installment to pay first." });
      return;
    }
    const installment = unpaidInstallments.find((i) => i.id === selectedInstallment);
    if (!installment) return;

    setSubmitting(true);
    setStatus(null);
    try {
      const endpoint = method === "paypal" ? "/payments/payments/paypal_checkout/" : "/payments/payments/paymongo_checkout/";
      await apiClient.post(endpoint, { amount: installment.amount_due });
      setStatus({ type: "info", message: "Redirecting to checkout…" });
    } catch (err: unknown) {
      // Deliberately not surfacing err.response.data.detail here — that's an internal
      // config message ("PAYPAL_CLIENT_ID is not set...") meant for developers, not buyers.
      setStatus({
        type: "error",
        message: "This payment method isn't available right now. Please contact us or try again later.",
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <h1 className="font-serif text-2xl mb-1">Make a Payment</h1>
      <p className="text-stone-500 text-sm mb-8">
        Pay an upcoming installment via PayPal or a local e-wallet.
      </p>

      <div className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm max-w-md">
        <label className="block text-sm font-medium text-stone-700 mb-1">Installment</label>
        <select
          value={selectedInstallment}
          onChange={(e) => setSelectedInstallment(e.target.value)}
          className="w-full mb-4 rounded-lg border border-stone-300 px-3 py-2 text-sm"
        >
          <option value="">Select an installment…</option>
          {unpaidInstallments.map((inst: Installment) => (
            <option key={inst.id} value={inst.id}>
              #{inst.installment_number} — due {inst.due_date} — {currency}
              {Number(inst.amount_due).toLocaleString()}
            </option>
          ))}
        </select>

        <label className="block text-sm font-medium text-stone-700 mb-1">Payment method</label>
        <div className="flex gap-3 mb-6">
          <button
            type="button"
            onClick={() => setMethod("paypal")}
            className={`flex-1 rounded-lg border px-3 py-2 text-sm font-medium ${
              method === "paypal"
                ? "border-emerald-700 bg-emerald-50 text-emerald-800"
                : "border-stone-300 text-stone-600"
            }`}
          >
            PayPal
          </button>
          <button
            type="button"
            onClick={() => setMethod("paymongo")}
            className={`flex-1 rounded-lg border px-3 py-2 text-sm font-medium ${
              method === "paymongo"
                ? "border-emerald-700 bg-emerald-50 text-emerald-800"
                : "border-stone-300 text-stone-600"
            }`}
          >
            GCash / Maya
          </button>
        </div>

        {status && (
          <p
            className={`mb-4 text-sm rounded-lg px-3 py-2 ${
              status.type === "error"
                ? "bg-red-50 text-red-600 border border-red-200"
                : "bg-emerald-50 text-emerald-800 border border-emerald-200"
            }`}
          >
            {status.message}
          </p>
        )}

        <button
          onClick={handlePay}
          disabled={submitting}
          className="w-full rounded-full bg-emerald-800 text-white py-2.5 font-medium hover:bg-emerald-900 transition disabled:opacity-50"
        >
          {submitting ? "Processing…" : "Continue to payment"}
        </button>
      </div>
    </div>
  );
}