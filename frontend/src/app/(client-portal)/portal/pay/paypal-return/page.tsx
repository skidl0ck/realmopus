"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";
import { reportPaymentResultAndClose, isPaymentPopup } from "@/lib/payment-popup";

type ResultState = "checking" | "success" | "error";

function PaypalReturnInner() {
  const searchParams = useSearchParams();
  const [state, setState] = useState<ResultState>("checking");
  const [message, setMessage] = useState("");

  useEffect(() => {
    // PayPal appends its own order id as `token` to whatever return_url we
    // gave it - the standard Orders v2 checkout redirect behavior.
    const orderId = searchParams.get("token");
    if (!orderId) {
      setState("error");
      setMessage("Missing order reference - this doesn't look like a valid return from PayPal.");
      return;
    }

    apiClient
      .post("/payments/payments/paypal_capture/", { order_id: orderId })
      .then(() => {
        setState("success");
        reportPaymentResultAndClose({ success: true });
      })
      .catch((err: unknown) => {
        const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
        setState("error");
        setMessage(detail || "We couldn't confirm this payment. If you were charged, please contact us.");
        reportPaymentResultAndClose({ success: false, detail: detail || "We couldn't confirm this payment. If you were charged, please contact us." });
      });
  }, [searchParams]);

  return (
    <div className="max-w-md">
      <h1 className="font-display text-2xl mb-4 text-ink uppercase">Confirming your payment…</h1>

      {state === "checking" && <p className="text-neutral-600">Please wait while we confirm your payment with PayPal.</p>}

      {state === "success" && (
        <div className="border border-green-200 bg-green-50 p-6">
          <p className="text-green-800 font-medium mb-2">Payment confirmed!</p>
          <p className="text-neutral-600 text-sm">Your payment has been recorded on your contract.</p>
        </div>
      )}

      {state === "error" && (
        <div className="border border-red-200 bg-red-50 p-6">
          <p className="text-red-800 font-medium mb-2">We couldn't confirm this payment</p>
          <p className="text-neutral-600 text-sm">{message}</p>
        </div>
      )}

      {isPaymentPopup() ? (
        <p className="mt-6 text-sm text-neutral-500">This window will close automatically…</p>
      ) : (
        <Link href="/portal/pay" className="inline-block mt-6 text-accent font-medium hover:underline">
          Back to Make a Payment
        </Link>
      )}
    </div>
  );
}

export default function PaypalReturnPage() {
  return (
    <Suspense fallback={<p className="text-neutral-600">Loading…</p>}>
      <PaypalReturnInner />
    </Suspense>
  );
}