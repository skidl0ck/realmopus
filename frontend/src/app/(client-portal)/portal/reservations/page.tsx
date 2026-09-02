"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { useCurrencySymbol } from "@/lib/currency";
import { payWithPaymongo, type PaymongoMethodType } from "@/lib/paymongo";
import type { Reservation } from "@/types";

async function fetchMyReservations(): Promise<Reservation[]> {
  const { data } = await apiClient.get("/properties/reservations/mine/");
  return data.results ?? data;
}

const STATUS_STYLES: Record<string, string> = {
  pending_payment: "bg-marigold/20 text-marigold",
  active: "bg-sage/20 text-sage",
  converted: "bg-sage/20 text-sage",
  expired: "bg-sand/20 text-sand",
  cancelled: "bg-rust/20 text-rust",
};

type Method = "paypal" | "gcash" | "paymaya" | "card";

function checkoutErrorMessage(err: unknown): string {
  const response = (err as { response?: { status?: number; data?: { detail?: string } } })?.response;
  if (response?.status === 503) {
    return "This payment method isn't available right now. Please contact us or try again later.";
  }
  return response?.data?.detail || (err as Error)?.message || "Couldn't process that payment — please try again.";
}

export default function ReservationsPage() {
  const currency = useCurrencySymbol();
  const { data: reservations, isLoading, refetch } = useQuery({
    queryKey: ["my-reservations"],
    queryFn: fetchMyReservations,
  });

  const [payingId, setPayingId] = useState<string | null>(null);
  const [method, setMethod] = useState<Method>("paypal");
  const [cardNumber, setCardNumber] = useState("");
  const [expMonth, setExpMonth] = useState("");
  const [expYear, setExpYear] = useState("");
  const [cvc, setCvc] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function openPayFor(reservation: Reservation) {
    setPayingId(reservation.id);
    setMethod("paypal");
    setCardNumber("");
    setExpMonth("");
    setExpYear("");
    setCvc("");
    setError(null);
  }

  async function handlePayPal(reservation: Reservation) {
    setSubmitting(true);
    setError(null);
    try {
      const returnUrl = `${window.location.origin}/portal/reservations/paypal-return?reservation=${reservation.id}`;
      const cancelUrl = `${window.location.origin}/portal/reservations?cancelled=1`;
      const { data } = await apiClient.post("/payments/payments/paypal_checkout/", {
        reservation: reservation.id,
        return_url: returnUrl,
        cancel_url: cancelUrl,
      });
      window.location.href = data.approve_url;
    } catch (err: unknown) {
      setError(checkoutErrorMessage(err));
      setSubmitting(false);
    }
  }

  async function handlePaymongo(reservation: Reservation, type: PaymongoMethodType) {
    setSubmitting(true);
    setError(null);
    try {
      const { data: intent } = await apiClient.post("/payments/payments/paymongo_checkout/", {
        reservation: reservation.id,
      });
      const returnUrl = `${window.location.origin}/portal/reservations/paymongo-return?reservation=${reservation.id}`;
      const card =
        type === "card"
          ? { cardNumber, expMonth: Number(expMonth), expYear: Number(expYear), cvc }
          : undefined;
      const result = await payWithPaymongo(intent.id, intent.client_key, type, returnUrl, card);

      if (result.redirectUrl) {
        window.location.href = result.redirectUrl;
        return;
      }
      // Some methods can resolve without a redirect — still go through our
      // own backend to confirm, never trust the client-side result alone.
      await apiClient.post("/payments/payments/paymongo_confirm/", { payment_intent_id: intent.id });
      setPayingId(null);
      refetch();
    } catch (err: unknown) {
      setError(checkoutErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <h1 className="font-display text-2xl mb-1 text-cream">My Reservations</h1>
      <p className="text-sand text-sm mb-8">Lots you've reserved, and any fee still due to confirm them.</p>

      {isLoading && <p className="text-sand">Loading…</p>}
      {!isLoading && (!reservations || reservations.length === 0) && (
        <p className="text-sand">No reservations yet — browse available lots to reserve one.</p>
      )}

      <div className="space-y-4 max-w-lg">
        {reservations?.map((reservation) => {
          const isPending = reservation.status === "pending_payment";
          const isPayingThis = payingId === reservation.id;

          return (
            <div key={reservation.id} className="rounded-2xl border border-clay bg-clay p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="font-display text-cream">{reservation.lot_display}</span>
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${STATUS_STYLES[reservation.status] ?? "bg-sand/20 text-sand"}`}>
                  {reservation.status.replace("_", " ")}
                </span>
              </div>
              {isPending && (
                <p className="text-sand text-sm mb-4">
                  {currency}{Number(reservation.reservation_fee).toLocaleString()} due by {reservation.deadline}
                </p>
              )}

              {isPending && !isPayingThis && (
                <button
                  onClick={() => openPayFor(reservation)}
                  className="rounded-full bg-marigold text-ink text-sm font-semibold px-5 py-2 hover:opacity-90 transition cursor-pointer"
                >
                  Pay Now
                </button>
              )}

              {isPayingThis && (
                <div className="mt-2 border-t border-ink pt-4">
                  {error && (
                    <p className="mb-4 text-sm text-rust bg-rust/10 border border-rust/30 rounded-lg px-3 py-2">
                      {error}
                    </p>
                  )}

                  <p className="text-sm font-medium text-sand mb-2">Choose a payment method</p>
                  <div className="grid grid-cols-2 gap-2 mb-4">
                    {(["paypal", "gcash", "paymaya", "card"] as Method[]).map((m) => (
                      <button
                        key={m}
                        onClick={() => setMethod(m)}
                        className={`rounded-lg border px-3 py-2 text-sm font-medium cursor-pointer ${
                          method === m ? "border-marigold bg-marigold/10 text-marigold" : "border-clay text-sand"
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
                        className="w-full rounded-lg border border-clay bg-ink text-cream px-3 py-2 text-sm"
                      />
                      <div className="grid grid-cols-3 gap-2">
                        <input
                          type="text"
                          placeholder="MM"
                          value={expMonth}
                          onChange={(e) => setExpMonth(e.target.value)}
                          className="w-full rounded-lg border border-clay bg-ink text-cream px-3 py-2 text-sm"
                        />
                        <input
                          type="text"
                          placeholder="YYYY"
                          value={expYear}
                          onChange={(e) => setExpYear(e.target.value)}
                          className="w-full rounded-lg border border-clay bg-ink text-cream px-3 py-2 text-sm"
                        />
                        <input
                          type="text"
                          placeholder="CVC"
                          value={cvc}
                          onChange={(e) => setCvc(e.target.value)}
                          className="w-full rounded-lg border border-clay bg-ink text-cream px-3 py-2 text-sm"
                        />
                      </div>
                    </div>
                  )}

                  <div className="flex gap-3">
                    <button
                      onClick={() =>
                        method === "paypal" ? handlePayPal(reservation) : handlePaymongo(reservation, method)
                      }
                      disabled={submitting}
                      className="rounded-full bg-marigold text-ink text-sm font-semibold px-5 py-2 hover:opacity-90 transition disabled:opacity-50 cursor-pointer"
                    >
                      {submitting ? "Processing…" : `Pay ${currency}${Number(reservation.reservation_fee).toLocaleString()}`}
                    </button>
                    <button
                      onClick={() => setPayingId(null)}
                      disabled={submitting}
                      className="rounded-full border border-clay text-sand text-sm font-semibold px-5 py-2 hover:opacity-90 transition cursor-pointer"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}