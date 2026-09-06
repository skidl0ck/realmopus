"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";
import { reportPaymentResultAndClose, isPaymentPopup } from "@/lib/payment-popup";

type ResultState = "checking" | "success" | "error";

const MAX_ATTEMPTS = 3;
const RETRY_DELAY_MS = 2000;

function PaymongoReturnInner() {
  const searchParams = useSearchParams();
  const [state, setState] = useState<ResultState>("checking");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const intentId = searchParams.get("payment_intent_id");
    if (!intentId) {
      setState("error");
      setMessage("Missing payment reference - this doesn't look like a valid return from checkout.");
      return;
    }

    let cancelled = false;

    async function confirm() {
      for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
        try {
          await apiClient.post("/payments/payments/paymongo_confirm/", { payment_intent_id: intentId });
          if (!cancelled) {
            setState("success");
            reportPaymentResultAndClose({ success: true });
          }
          return;
        } catch (err: unknown) {
          const response = (err as { response?: { status?: number; data?: { detail?: string } } })?.response;
          const stillProcessing = response?.status === 402 && attempt < MAX_ATTEMPTS;
          if (stillProcessing) {
            await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY_MS));
            continue;
          }
          if (!cancelled) {
            setState("error");
            setMessage(response?.data?.detail || "We couldn't confirm this payment. If you were charged, please contact us.");
            reportPaymentResultAndClose({ success: false, detail: response?.data?.detail || "We couldn't confirm this payment. If you were charged, please contact us." });
          }
          return;
        }
      }
    }

    confirm();
    return () => {
      cancelled = true;
    };
  }, [searchParams]);

  return (
    <div className="max-w-md">
      <h1 className="font-display text-2xl mb-4 text-ink uppercase">Confirming your payment…</h1>

      {state === "checking" && <p className="text-neutral-600">Please wait while we confirm your payment.</p>}

      {state === "success" && (
        <div className="border border-green-200 bg-green-50 p-6">
          <p className="text-green-800 font-medium mb-2">Payment confirmed!</p>
          <p className="text-neutral-600 text-sm">Your reservation is now active.</p>
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
        <Link href="/portal/reservations" className="inline-block mt-6 text-accent font-medium hover:underline">
          Back to My Reservations
        </Link>
      )}
    </div>
  );
}

export default function PaymongoReturnPage() {
  return (
    <Suspense fallback={<p className="text-neutral-600">Loading…</p>}>
      <PaymongoReturnInner />
    </Suspense>
  );
}