/** DRF's throttle responses always carry a Retry-After header (seconds,
 * per RFC 7231) on top of the human-readable "detail" message in the body
 * -- the header is the more reliable of the two to build a UI message
 * from, since it's a plain number rather than something that'd need
 * parsing out of a sentence. Returns null for anything that isn't
 * actually a 429, so callers can tell "this wasn't a rate limit" apart
 * from "it was, but the wait time couldn't be read".
 *
 * Requires CORS_EXPOSE_HEADERS = ['Retry-After'] on the backend -- without
 * it, the browser silently hides this header from cross-origin JavaScript
 * even though the server did send it (see TROUBLESHOOTING.md). */
export function rateLimitMessage(err: unknown): string | null {
  const response = (err as { response?: { status?: number; headers?: Record<string, string> } })?.response;
  if (response?.status !== 429) return null;
  const waitSeconds = Number(response.headers?.["retry-after"]);
  if (!(waitSeconds > 0)) return "Too many attempts. Please wait a moment and try again.";
  const wait =
    waitSeconds >= 60
      ? `${Math.ceil(waitSeconds / 60)} minute${Math.ceil(waitSeconds / 60) === 1 ? "" : "s"}`
      : `${waitSeconds} second${waitSeconds === 1 ? "" : "s"}`;
  return `Too many attempts. Please try again in ${wait}.`;
}