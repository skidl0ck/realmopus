"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { useCurrencySymbol, useDefaultReservationFee } from "@/lib/site-config";
import { payWithPaymongo, type PaymongoMethodType } from "@/lib/paymongo";
import { openPaymentPopup, waitForPaymentPopup, type PopupPaymentResult } from "@/lib/payment-popup";
import type { Lot } from "@/types";

async function fetchLot(id: string): Promise<Lot> {
  const { data } = await apiClient.get(`/properties/lots/${id}/`);
  return data;
}

type Method = "paypal" | "gcash" | "paymaya" | "card";

function checkoutErrorMessage(err: unknown): string {
  const response = (err as { response?: { status?: number; data?: { detail?: string } } })?.response;
  if (response?.status === 503) {
    return "This payment method isn't available right now. Please contact us or try again later.";
  }
  if (response?.status === 409) {
    return response?.data?.detail || "This lot was just reserved by someone else.";
  }
  return response?.data?.detail || (err as Error)?.message || "Couldn't process that payment - please try again.";
}

function LotThumbnail({ url }: { url: string | null | undefined }) {
  if (url) {
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={url} alt="Lot" className="duotone w-full h-44 object-cover mb-4" />;
  }
  return (
    <div className="w-full h-44 mb-4 bg-bg flex items-center justify-center border border-divider">
      <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-neutral-400">
        <path d="M3 10.5L12 3l9 7.5" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M5 9.5V20a1 1 0 001 1h4v-6h4v6h4a1 1 0 001-1V9.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
}

export default function LotCheckoutPage() {
  const params = useParams<{ lotId: string }>();
  const router = useRouter();
  const currency = useCurrencySymbol();
  const fee = useDefaultReservationFee();

  const { data: lot, isLoading, isError } = useQuery({
    queryKey: ["lot-checkout", params.lotId],
    queryFn: () => fetchLot(params.lotId),
  });

  const [method, setMethod] = useState<Method>("paypal");
  const [cardNumber, setCardNumber] = useState("");
  const [expMonth, setExpMonth] = useState("");
  const [expYear, setExpYear] = useState("");
  const [cvc, setCvc] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handlePayPal(popup: Window | null) {
    if (!lot) return;
    setSubmitting(true);
    setError(null);
    try {
      const returnUrl = `${window.location.origin}/portal/lots/${lot.id}/checkout/paypal-return`;
      const cancelUrl = `${window.location.origin}/portal/lots/${lot.id}/checkout?cancelled=1`;
      const { data } = await apiClient.post("/payments/payments/paypal_checkout/", {
        lot: lot.id,
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
    if (!lot) return;
    setSubmitting(true);
    setError(null);
    try {
      const { data: intent } = await apiClient.post("/payments/payments/paymongo_checkout/", { lot: lot.id });
      const returnUrl = `${window.location.origin}/portal/lots/${lot.id}/checkout/paymongo-return`;
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
      router.push("/portal/reservations");
      return;
    }
    if (result.unknown) {
      setError("We couldn't tell whether that payment went through — check My Reservations, or try again.");
      return;
    }
    setError(result.detail || "We couldn't confirm this payment.");
  }

  function handlePay() {
    // Opened synchronously, right here in the click handler -- this is
    // what keeps a popup from being blocked, since browsers only allow
    // window.open() without a block when it's tied directly to a user
    // gesture, not after the async calls the handlers below make. Points
    // at a blank page until the real gateway URL is known.
    const popup = openPaymentPopup();
    if (method === "paypal") {
      handlePayPal(popup);
    } else {
      handlePaymongo(method, popup);
    }
  }

  if (isLoading) return <p className="text-neutral-600">Loading…</p>;
  if (isError || !lot) {
    return (
      <div className="max-w-md">
        <p className="text-red-700">Couldn&apos;t load this lot.</p>
      </div>
    );
  }

  if (lot.status !== "available") {
    return (
      <div className="max-w-md">
        <p className="text-neutral-600">This lot is no longer available for reservation.</p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="font-display font-semibold uppercase text-2xl mb-1 text-ink">Checkout</h1>
      <p className="text-neutral-600 text-sm mb-8">Pay your reservation fee to hold this lot.</p>

      <div className="grid lg:grid-cols-[1fr_360px] gap-8">
        {/* Left: payment methods */}
        <div className="border border-divider p-6">
          <p className="text-sm font-medium text-neutral-600 mb-3">Choose a payment method</p>
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

          {method === "paypal" && (
            <p className="text-neutral-600 text-sm">You&apos;ll be redirected to PayPal to complete your payment.</p>
          )}
          {(method === "gcash" || method === "paymaya") && (
            <p className="text-neutral-600 text-sm">You&apos;ll be redirected to {method === "gcash" ? "GCash" : "Maya"} to complete your payment.</p>
          )}

          {method === "card" && (
            <div className="space-y-3">
              <div className="field">
                <label>Card number</label>
                <input
                  type="text"
                  value={cardNumber}
                  onChange={(e) => setCardNumber(e.target.value)}
                  className="input"
                />
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div className="field">
                  <label>MM</label>
                  <input
                    type="text"
                    value={expMonth}
                    onChange={(e) => setExpMonth(e.target.value)}
                    className="input"
                  />
                </div>
                <div className="field">
                  <label>YYYY</label>
                  <input
                    type="text"
                    value={expYear}
                    onChange={(e) => setExpYear(e.target.value)}
                    className="input"
                  />
                </div>
                <div className="field">
                  <label>CVC</label>
                  <input
                    type="text"
                    value={cvc}
                    onChange={(e) => setCvc(e.target.value)}
                    className="input"
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right: lot summary + pay button */}
        <div className="border border-divider p-6 h-fit lg:sticky lg:top-6">
          <LotThumbnail url={lot.thumbnail} />
          <h2 className="font-display font-semibold uppercase text-lg text-ink mb-1">
            Block {lot.block_number}, Lot {lot.lot_number}
          </h2>
          {lot.project_name && <p className="text-neutral-600 text-sm mb-3">{lot.project_name}</p>}
          <p className="text-neutral-600 text-sm mb-1">{lot.area_sqm} sqm</p>
          <p className="text-neutral-600 text-sm mb-4">
            Lot price: {currency}{Number(lot.total_price).toLocaleString()}
          </p>

          <div className="border-t border-divider pt-4 mb-4">
            <div className="flex items-center justify-between mb-1">
              <span className="text-neutral-600 text-sm">Reservation fee</span>
              <span className="text-ink font-semibold font-data">
                {fee !== undefined ? `${currency}${fee.toLocaleString()}` : "…"}
              </span>
            </div>
          </div>

          {error && (
            <p className="mb-4 text-sm px-3 py-2 bg-red-50 text-red-800 border border-red-200">
              {error}
            </p>
          )}

          <button
            onClick={handlePay}
            disabled={submitting || fee === undefined}
            className="btn btn-primary btn-block w-full"
          >
            {submitting ? "Processing…" : fee !== undefined ? `Pay ${currency}${fee.toLocaleString()}` : "Loading…"}
          </button>
        </div>
      </div>
    </div>
  );
}