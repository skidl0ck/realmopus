// Client-side PayMongo calls, using the public key directly against
// PayMongo's API — never through our own backend. This is deliberate:
// PayMongo's own docs are explicit that card details should never reach
// your server. The public key is safe to expose (it can only create
// Payment Methods and attach them using a short-lived client_key scoped
// to one specific intent, nothing more).

const PAYMONGO_API_BASE = "https://api.paymongo.com/v1";

function publicKey(): string {
  const key = process.env.NEXT_PUBLIC_PAYMONGO_PUBLIC_KEY;
  if (!key) {
    throw new Error("NEXT_PUBLIC_PAYMONGO_PUBLIC_KEY is not configured.");
  }
  return key;
}

function authHeader(key: string): string {
  return "Basic " + btoa(`${key}:`);
}

export interface CardDetails {
  cardNumber: string;
  expMonth: number;
  expYear: number;
  cvc: string;
}

export type PaymongoMethodType = "card" | "gcash" | "paymaya";

async function createPaymentMethod(type: PaymongoMethodType, card?: CardDetails): Promise<string> {
  const attributes: Record<string, unknown> = { type };
  if (type === "card") {
    if (!card) throw new Error("Card details are required for card payments.");
    attributes.details = {
      card_number: card.cardNumber.replace(/\s+/g, ""),
      exp_month: card.expMonth,
      exp_year: card.expYear,
      cvc: card.cvc,
    };
  }

  const resp = await fetch(`${PAYMONGO_API_BASE}/payment_methods`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: authHeader(publicKey()) },
    body: JSON.stringify({ data: { attributes } }),
  });
  const data = await resp.json();
  if (!resp.ok) {
    const message = data?.errors?.[0]?.detail || "Couldn't process that payment method.";
    throw new Error(message);
  }
  return data.data.id;
}

interface AttachResult {
  status: string;
  redirectUrl: string | null;
}

async function attachPaymentMethod(
  intentId: string,
  clientKey: string,
  paymentMethodId: string,
  returnUrl: string
): Promise<AttachResult> {
  const resp = await fetch(`${PAYMONGO_API_BASE}/payment_intents/${intentId}/attach`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: authHeader(publicKey()) },
    body: JSON.stringify({
      data: { attributes: { payment_method: paymentMethodId, client_key: clientKey, return_url: returnUrl } },
    }),
  });
  const data = await resp.json();
  if (!resp.ok) {
    const message = data?.errors?.[0]?.detail || "Payment could not be processed.";
    throw new Error(message);
  }
  const attrs = data.data.attributes;
  return {
    status: attrs.status,
    redirectUrl: attrs.status === "awaiting_next_action" ? attrs.next_action?.redirect?.url ?? null : null,
  };
}

/**
 * Creates a Payment Method for the chosen type and attaches it to an
 * already-created Payment Intent. Returns the resulting status plus a
 * redirect URL if 3DS/GCash/Maya authentication is required — the caller
 * decides what to do next (redirect, or immediately confirm with our own
 * backend if the intent already succeeded without needing a redirect).
 */
export async function payWithPaymongo(
  intentId: string,
  clientKey: string,
  type: PaymongoMethodType,
  returnUrl: string,
  card?: CardDetails
): Promise<AttachResult> {
  const paymentMethodId = await createPaymentMethod(type, card);
  return attachPaymentMethod(intentId, clientKey, paymentMethodId, returnUrl);
}