"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  login,
  register,
  dashboardPathForRole,
  AccountDeactivatedError,
} from "@/lib/auth";
import { useAuthStore } from "@/lib/auth-store";
import { useAuthModalStore } from "@/lib/auth-modal-store";

type Panel = "login" | "register";

// Mirrors accounts/management/commands/seed_demo_accounts.py's defaults --
// override both together via env vars if the backend's demo password is
// ever changed at deploy time, so this button doesn't quietly drift out of
// sync with what actually authenticates.
const DEMO_USERNAME = process.env.NEXT_PUBLIC_DEMO_CLIENT_USERNAME || "demo_client";
const DEMO_PASSWORD = process.env.NEXT_PUBLIC_DEMO_CLIENT_PASSWORD || "DemoClient2026!";

/** DRF's throttle responses always carry a Retry-After header (seconds,
 * per RFC 7231) on top of the human-readable "detail" message in the body
 * -- the header is the more reliable of the two to build a UI message
 * from, since it's a plain number rather than something that'd need
 * parsing out of a sentence. Returns null for anything that isn't
 * actually a 429, so callers can tell "this wasn't a rate limit" apart
 * from "it was, but the wait time couldn't be read". */
function rateLimitMessage(err: unknown): string | null {
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

export function AuthModal() {
  const router = useRouter();
  const setUser = useAuthStore((s) => s.setUser);
  const { isOpen, mode, nextPath, close } = useAuthModalStore();

  const [panel, setPanel] = useState<Panel>(mode);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);

  // Reset form state each time the modal is (re)opened, and honor the mode it was opened in.
  useEffect(() => {
    if (isOpen) {
      setPanel(mode);
      setUsername("");
      setPassword("");
      setFirstName("");
      setLastName("");
      setEmail("");
      setPhoneNumber("");
      setError(null);
    }
  }, [isOpen, mode]);

  if (!isOpen) return null;

  function finishAuth(user: { role: "admin" | "sales_agent" | "accountant" | "client" }) {
    setUser(user as never);
    close();
    router.push(nextPath || dashboardPathForRole(user.role));
  }

  async function handleDemoLogin() {
    setError(null);
    setDemoLoading(true);
    try {
      const user = await login(DEMO_USERNAME, DEMO_PASSWORD);
      finishAuth(user);
    } catch {
      setError("Couldn't reach the demo account right now — please try again.");
    } finally {
      setDemoLoading(false);
    }
  }

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const user = await login(username, password);
      finishAuth(user);
    } catch (err) {
      if (err instanceof AccountDeactivatedError) {
        setError("This account has been deactivated. Please contact support.");
      } else {
        setError(rateLimitMessage(err) ?? "Invalid username or password.");
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const user = await register({ firstName, lastName, email, phoneNumber, username, password });
      finishAuth(user);
    } catch (err: unknown) {
      const rateLimit = rateLimitMessage(err);
      const detail = (err as { response?: { data?: Record<string, string[]> } })?.response?.data;
      setError(rateLimit ?? (detail ? Object.values(detail).flat().join(" ") : "Couldn't create your account. Please try again."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-ink/60 backdrop-blur-sm" onClick={close} />

      {/* Modal card */}
      <div className="blueprint relative w-full max-w-sm bg-bg shadow-lg p-8">
        <i className="corner tl" /><i className="corner tr" /><i className="corner bl" /><i className="corner br" />
        <button
          onClick={close}
          aria-label="Close"
          className="absolute top-4 right-4 text-neutral-500 hover:text-ink cursor-pointer"
        >
          ✕
        </button>

        {panel === "login" && (
          <form onSubmit={handleLogin}>
            <h1 className="font-display font-semibold text-2xl uppercase mb-1 text-ink">Sign in</h1>
            <p className="text-neutral-600 text-sm mb-6">
              Access your contracts, payment schedule, and receipts.
            </p>

            {error && (
              <p className="mb-4 text-sm text-red-700 bg-red-50 border border-red-200 px-3 py-2">
                {error}
              </p>
            )}

            <div className="field mb-4">
              <label>Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoFocus
                className="input"
              />
            </div>

            <div className="field mb-6">
              <label>Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="input"
              />
            </div>

            <button type="submit" disabled={loading} className="btn btn-primary btn-block w-full">
              {loading ? "Signing in…" : "Sign in"}
            </button>

            <div className="my-4 flex items-center gap-3 text-xs text-neutral-500 uppercase tracking-wide">
              <span className="h-px flex-1 bg-divider" />
              or
              <span className="h-px flex-1 bg-divider" />
            </div>

            <button
              type="button"
              onClick={handleDemoLogin}
              disabled={demoLoading}
              className="btn btn-secondary btn-block w-full"
            >
              {demoLoading ? "Loading demo…" : "Try the demo — no signup needed"}
            </button>

            <p className="mt-5 text-center text-sm text-neutral-600">
              New here?{" "}
              <button
                type="button"
                onClick={() => { setPanel("register"); setError(null); }}
                className="text-accent font-medium hover:underline cursor-pointer"
              >
                Create an account
              </button>
            </p>
          </form>
        )}

        {panel === "register" && (
          <form onSubmit={handleRegister}>
            <h1 className="font-display font-semibold text-2xl uppercase mb-1 text-ink">Create your account</h1>
            <p className="text-neutral-600 text-sm mb-6">
              Set up your profile — you can browse, reserve a lot, and view contracts once you&apos;re in.
            </p>

            {error && (
              <p className="mb-4 text-sm text-red-700 bg-red-50 border border-red-200 px-3 py-2">
                {error}
              </p>
            )}

            <div className="grid grid-cols-2 gap-3 mb-4">
              <div className="field">
                <label>First name</label>
                <input
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  required
                  autoFocus
                  className="input"
                />
              </div>
              <div className="field">
                <label>Last name</label>
                <input
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  required
                  className="input"
                />
              </div>
            </div>

            <div className="field mb-4">
              <label>Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="input"
              />
            </div>

            <div className="field mb-4">
              <label>Phone number</label>
              <input
                type="tel"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                required
                className="input"
              />
            </div>

            <div className="field mb-4">
              <label>Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="input"
              />
            </div>

            <div className="field mb-6">
              <label>Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="input"
              />
            </div>

            <button type="submit" disabled={loading} className="btn btn-primary btn-block w-full">
              {loading ? "Creating account…" : "Create account"}
            </button>

            <p className="mt-5 text-center text-sm text-neutral-600">
              Already registered?{" "}
              <button
                type="button"
                onClick={() => { setPanel("login"); setError(null); }}
                className="text-accent font-medium hover:underline cursor-pointer"
              >
                Sign in
              </button>
            </p>
          </form>
        )}
      </div>
    </div>
  );
}