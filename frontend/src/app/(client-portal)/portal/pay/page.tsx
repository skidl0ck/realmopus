"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { useCurrencySymbol } from "@/lib/currency";
import { payWithPaymongo, type PaymongoMethodType } from "@/lib/paymongo";
import { openPaymentPopup, waitForPaymentPopup, type PopupPaymentResult } from "@/lib/payment-popup";
import type { Contract, Installment } from "@/types";

async function fetchMyContract(): Promise<Contract | null> {
  const { data } = await apiClient.get("/sales/contracts/");
  const contracts = data.results ?? data;
  return contracts[0] ?? null;
}

type Method = "paypal" | "gcash" | "paymaya" | "card";

function checkoutErrorMessage(err: unknown): string {
  const response = (err as { response?: { status?: number; data?: { detail?: string } } })?.response;
  if (response?.status === 503) {
    return "This payment method isn't available right now. Please contact us or try again later.";
  }
  return response?.data?.detail || (err as Error)?.message || "Couldn't process that payment - please try again.";
}

export default function PayPage() {
  const { data: contract } = useQuery({ queryKey: ["my-contract-pay"], queryFn: fetchMyContract });
  const currency = useCurrencySymbol();
  const queryClient = useQueryClient();

  const [selectedInstallment, setSelectedInstallment] = useState<string>("");
  const [method, setMethod] = useState<Method>("paypal");
  const [cardNumber, setCardNumber] = useState("");
  const [expMonth, setExpMonth] = useState("");
  const [expYear, setExpYear] = useState("");
  const [cvc, setCvc] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const unpaidInstallments = (contract?.installments ?? []).filter(
    (i: Installment) => i.status !== "paid"
  );
  const installment = unpaidInstallments.find((i) => i.id === selectedInstallment);
  const amountDue = installment ? Number(installment.balance ?? installment.amount_due) : 0;

  async function handlePayPal(popup: Window | null) {
    if (!installment) return;
    setSubmitting(true);
    setError(null);
    try {
      const returnUrl = `${window.location.origin}/portal/pay/paypal-return`;
      const cancelUrl = `${window.location.origin}/portal/pay?cancelled=1`;
      const { data } = await apiClient.post("/payments/payments/paypal_checkout/", {
        installment: installment.id,
        return_url: returnUrl,
        cancel_url: cancelUrl,
      });
      if (popup && !popup.closed) {
        popup.location.href = data.approve_url;
        handlePopupResult(await waitForPaymentPopup(popup));
      } else {
        // Popup was blocked (or unsupported) -- fall back to the original
        // full-page redirect rather than leaving the user stuck.
        window.location.href = data.approve_url;
      }
    } catch (err: unknown) {
      setError(checkoutErrorMessage(err));
      setSubmitting(false);
      popup?.close();
    }
  }

  async function handlePaymongo(type: PaymongoMethodType, popup: Window | null) {
    if (!installment) return;
    setSubmitting(true);
    setError(null);
    try {
      const { data: intent } = await apiClient.post("/payments/payments/paymongo_checkout/", {
        installment: installment.id,
      });
      const returnUrl = `${window.location.origin}/portal/pay/paymongo-return`;
      const card =
        type === "card" ? { cardNumber, expMonth: Number(expMonth), expYear: Number(expYear), cvc } : undefined;
      const result = await payWithPaymongo(intent.id, intent.client_key, type, returnUrl, card);

      if (result.redirectUrl) {
        if (popup && !popup.closed) {
          popup.location.href = result.redirectUrl;
          handlePopupResult(await waitForPaymentPopup(popup));
        } else {
          window.location.href = result.redirectUrl;
        }
        return;
      }
      // No redirect needed (card payments without 3DS confirm immediately) --
      // the popup opened speculatively before this resolved was never used.
      popup?.close();
      await apiClient.post("/payments/payments/paymongo_confirm/", { payment_intent_id: intent.id });
      handlePopupResult({ success: true });
    } catch (err: unknown) {
      setError(checkoutErrorMessage(err));
      setSubmitting(false);
      popup?.close();
    }
  }

  function handlePopupResult(result: PopupPaymentResult) {
    setSubmitting(false);
    if (result.success) {
      setError(null);
      // Stays on this same page (unlike the lot/reservation checkout flows,
      // which navigate away on success) -- the installment/contract data
      // needs an explicit refetch so the just-paid installment actually
      // shows as paid, rather than the page quietly going stale.
      queryClient.invalidateQueries({ queryKey: ["my-contract-pay"] });
      return;
    }
    if (result.unknown) {
      setError("We couldn't tell whether that payment went through — check your payment schedule, or try again.");
      return;
    }
    setError(result.detail || "We couldn't confirm this payment.");
  }

  function handlePay() {
    if (!installment) {
      setError("Select an installment to pay first.");
      return;
    }
    // Opened synchronously, right here in the click handler -- this is
    // what keeps a popup from being blocked, since browsers only allow
    // window.open() without a block when it's tied directly to a user
    // gesture, not after the async calls the handlers above make. Points
    // at a blank page until the real gateway URL is known.
    const popup = openPaymentPopup();
    if (method === "paypal") {
      handlePayPal(popup);
    } else {
      handlePaymongo(method, popup);
    }
  }

  return (
    <div>
      <h1 className="font-display font-semibold uppercase text-2xl mb-1 text-ink">Make a Payment</h1>
      <p className="text-neutral-600 text-sm mb-8">
        Pay an upcoming installment via PayPal or a local e-wallet.
      </p>

      <div className="border border-divider p-6 max-w-md">
        <div className="field mb-4">
          <label>Installment</label>
          <select
            value={selectedInstallment}
            onChange={(e) => setSelectedInstallment(e.target.value)}
            className="input"
          >
            <option value="">Select an installment…</option>
            {unpaidInstallments.map((inst: Installment) => (
              <option key={inst.id} value={inst.id}>
                #{inst.installment_number} - {contract?.payment_plan_type === "full_payment" ? "contract date" : "due"} {inst.due_date} - {currency}
                {Number(inst.balance ?? inst.amount_due).toLocaleString()}
              </option>
            ))}
          </select>
        </div>

        <label className="block text-sm font-medium text-neutral-600 mb-1">Payment method</label>
        <div className="grid grid-cols-2 gap-2 mb-4">
          {(["paypal", "gcash", "paymaya", "card"] as Method[]).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setMethod(m)}
              className={`border px-3 py-2 text-sm font-medium cursor-pointer ${
                method === m ? "border-accent bg-accent-100 text-accent-800" : "border-divider text-neutral-600"
              }`}
            >
              {m === "paypal" ? "PayPal" : m === "gcash" ? "GCash" : m === "paymaya" ? "Maya" : "Card"}
            </button>
          ))}
        </div>

        {method === "card" && (
          <div className="space-y-3 mb-4">
            <input
              type="text"
              placeholder="Card number"
              value={cardNumber}
              onChange={(e) => setCardNumber(e.target.value)}
              className="input"
            />
            <div className="grid grid-cols-3 gap-2">
              <input
                type="text"
                placeholder="MM"
                value={expMonth}
                onChange={(e) => setExpMonth(e.target.value)}
                className="input"
              />
              <input
                type="text"
                placeholder="YYYY"
                value={expYear}
                onChange={(e) => setExpYear(e.target.value)}
                className="input"
              />
              <input
                type="text"
                placeholder="CVC"
                value={cvc}
                onChange={(e) => setCvc(e.target.value)}
                className="input"
              />
            </div>
          </div>
        )}

        {error && (
          <p className="mb-4 text-sm px-3 py-2 bg-red-50 text-red-800 border border-red-200">
            {error}
          </p>
        )}

        <button
          onClick={handlePay}
          disabled={submitting}
          className="btn btn-primary btn-block w-full"
        >
          {submitting
            ? "Processing…"
            : installment
              ? `Pay ${currency}${amountDue.toLocaleString()}`
              : "Continue to payment"}
        </button>
      </div>
    </div>
  );
}