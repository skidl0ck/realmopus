/**
 * Popup-based checkout, shared by every gateway checkout page (lot
 * reservation, existing-reservation fee, and installment payment) and
 * every gateway return page.
 *
 * Why a popup at all: navigating the whole tab away to PayPal/GCash/Maya
 * and back meant losing the checkout page's own state, and made the
 * return page's own UI the only place a result could ever be shown --
 * easy to miss if the user didn't read it closely before it auto-redirected
 * elsewhere. A popup keeps the main app open throughout; the return page
 * (running inside the popup) reports its result back and closes itself,
 * and the main window is what actually shows the outcome.
 *
 * Why the popup opens before the gateway URL is known: browsers only allow
 * window.open() without being blocked when it's called synchronously inside
 * a user gesture (the click handler) -- not after an `await`. Opening a
 * blank, same-origin loading page immediately on click, then redirecting
 * that already-open window to the real gateway URL once the backend call
 * resolves, keeps the popup tied to the click and avoids the block.
 */

const POPUP_FEATURES = "width=480,height=720,menubar=no,toolbar=no,location=yes,status=no";

export interface PopupPaymentResult {
  success: boolean;
  detail?: string;
  /** True if the popup was closed manually without ever reporting a
   * result -- the payment's actual outcome is genuinely unknown in this
   * case (it may have succeeded on the gateway's side after all), not a
   * confirmed failure. */
  unknown?: boolean;
}

/** Opens a blank popup immediately, synchronously, inside the click
 * handler that calls this -- returns it so the caller can redirect it to
 * the real URL once known. Returns null if the browser blocked it anyway
 * (e.g. a stricter mobile browser), which the caller should treat as
 * "fall back to a normal full-page redirect". */
export function openPaymentPopup(): Window | null {
  return window.open("about:blank", "realmopus_payment", POPUP_FEATURES);
}

/** Waits for the popup to either post a result back (see
 * reportPaymentResultAndClose below) or be closed without one. Resolves,
 * never rejects -- a manually-closed popup is a normal, expected outcome
 * here, not an error. */
export function waitForPaymentPopup(popup: Window): Promise<PopupPaymentResult> {
  return new Promise((resolve) => {
    let settled = false;

    function finish(result: PopupPaymentResult) {
      if (settled) return;
      settled = true;
      window.removeEventListener("message", onMessage);
      clearInterval(pollClosed);
      resolve(result);
    }

    function onMessage(event: MessageEvent) {
      if (event.source !== popup) return;
      if (!event.data || event.data.type !== "realmopus_payment_result") return;
      finish({ success: !!event.data.success, detail: event.data.detail });
    }

    window.addEventListener("message", onMessage);

    // Popups are cross-origin once redirected to the gateway, so this is
    // the only way to detect a manual close from here -- can't inspect a
    // cross-origin window's own location/content directly.
    const pollClosed = setInterval(() => {
      if (popup.closed) {
        finish({ success: false, unknown: true });
      }
    }, 500);
  });
}

/** Called from inside a return page once it has its own definitive result.
 * If running inside a popup (has an opener), reports the result and closes
 * itself after a brief pause -- long enough for the result to be visible
 * to anyone who does glance at the popup, short enough not to feel stuck.
 * Does nothing if there's no opener (e.g. the return URL was visited
 * directly, or the popup got blocked and this ran as a normal full-page
 * redirect instead) -- the page's own success/error UI is the real
 * experience in that case, unchanged. */
export function reportPaymentResultAndClose(result: PopupPaymentResult) {
  if (typeof window === "undefined" || !window.opener) return;
  window.opener.postMessage({ type: "realmopus_payment_result", ...result }, window.location.origin);
  setTimeout(() => window.close(), 1500);
}

/** True if this page is running inside a popup opened by openPaymentPopup
 * above -- return pages use this to decide whether to show their own full
 * "back to..." navigation link (not runnable inside a small popup) or the
 * plain result. */
export function isPaymentPopup(): boolean {
  return typeof window !== "undefined" && !!window.opener;
}