"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";

type ResultState = "checking" | "success" | "error";

function PaypalReturnInner() {
  const searchParams = useSearchParams();
  const [state, setState] = useState<ResultState>("checking");
  const [message, setMessage] = useState("");

  useEffect(() => {
    // PayPal appends its own order id as `token` to whatever return_url we
    // gave it — this is the standard Orders v2 checkout redirect behavior.
    const orderId = searchParams.get("token");
    if (!orderId) {
      setState("error");
      setMessage("Missing order reference — this doesn't look like a valid return from PayPal.");
      return;
    }

    apiClient
      .post("/payments/payments/paypal_capture/", { order_id: orderId })
      .then(() => {
        setState("success");
      })
      .catch((err: unknown) => {
        const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
        setState("error");
        setMessage(detail || "We couldn't confirm this payment. If you were charged, please contact us.");
      });
  }, [searchParams]);

  return (
    <div className="max-w-md">
      <h1 className="font-display text-2xl mb-4 text-cream">Confirming your payment…</h1>

      {state === "checking" && <p className="text-sand">Please wait while we confirm your payment with PayPal.</p>}

      {state === "success" && (
        <div className="rounded-2xl border border-sage/30 bg-sage/10 p-6">
          <p className="text-sage font-medium mb-2">Payment confirmed!</p>
          <p className="text-sand text-sm">Your reservation is now active.</p>
        </div>
      )}

      {state === "error" && (
        <div className="rounded-2xl border border-rust/30 bg-rust/10 p-6">
          <p className="text-rust font-medium mb-2">We couldn't confirm this payment</p>
          <p className="text-sand text-sm">{message}</p>
        </div>
      )}

      <Link href="/portal/reservations" className="inline-block mt-6 text-marigold font-medium hover:underline">
        Back to My Reservations
      </Link>
    </div>
  );
}

export default function PaypalReturnPage() {
  return (
    <Suspense fallback={<p className="text-sand">Loading…</p>}>
      <PaypalReturnInner />
    </Suspense>
  );
}