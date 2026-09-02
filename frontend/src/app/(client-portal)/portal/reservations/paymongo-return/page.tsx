"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { apiClient } from "@/lib/api-client";

type ResultState = "checking" | "success" | "error";

// PayMongo intent status can briefly still be "processing" right at the
// moment of redirect-back — a couple of retries with a short delay covers
// this without needing a spinner that never resolves.
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
      setMessage("Missing payment reference — this doesn't look like a valid return from checkout.");
      return;
    }

    let cancelled = false;

    async function confirm() {
      for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
        try {
          await apiClient.post("/payments/payments/paymongo_confirm/", { payment_intent_id: intentId });
          if (!cancelled) setState("success");
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
      <h1 className="font-display text-2xl mb-4 text-cream">Confirming your payment…</h1>

      {state === "checking" && <p className="text-sand">Please wait while we confirm your payment.</p>}

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

export default function PaymongoReturnPage() {
  return (
    <Suspense fallback={<p className="text-sand">Loading…</p>}>
      <PaymongoReturnInner />
    </Suspense>
  );
}