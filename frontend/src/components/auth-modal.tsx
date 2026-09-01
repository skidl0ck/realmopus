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
        setError("Invalid username or password.");
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
      const detail = (err as { response?: { data?: Record<string, string[]> } })?.response?.data;
      setError(detail ? Object.values(detail).flat().join(" ") : "Couldn't create your account. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-ink/70 backdrop-blur-sm" onClick={close} />

      {/* Modal card */}
      <div className="relative w-full max-w-sm rounded-2xl bg-clay shadow-xl p-8 border border-clay">
        <button
          onClick={close}
          aria-label="Close"
          className="absolute top-4 right-4 text-sand/70 hover:text-cream"
        >
          ✕
        </button>

        {panel === "login" && (
          <form onSubmit={handleLogin}>
            <h1 className="font-display text-2xl mb-1 text-cream">Sign in</h1>
            <p className="text-sand text-sm mb-6">
              Access your contracts, payment schedule, and receipts.
            </p>

            {error && (
              <p className="mb-4 text-sm text-rust bg-rust/10 border border-rust/30 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <label className="block text-sm font-medium text-sand mb-1">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
              className="w-full mb-4 rounded-lg border border-clay bg-ink text-cream px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-marigold"
            />

            <label className="block text-sm font-medium text-sand mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full mb-6 rounded-lg border border-clay bg-ink text-cream px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-marigold"
            />

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-full bg-marigold text-ink py-2.5 font-semibold hover:opacity-90 transition disabled:opacity-50"
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>

            <p className="mt-5 text-center text-sm text-sand">
              New here?{" "}
              <button
                type="button"
                onClick={() => { setPanel("register"); setError(null); }}
                className="text-marigold font-medium hover:underline"
              >
                Create an account
              </button>
            </p>
          </form>
        )}

        {panel === "register" && (
          <form onSubmit={handleRegister}>
            <h1 className="font-display text-2xl mb-1 text-cream">Create your account</h1>
            <p className="text-sand text-sm mb-6">
              Set up your profile — you can browse, reserve a lot, and view contracts once you're in.
            </p>

            {error && (
              <p className="mb-4 text-sm text-rust bg-rust/10 border border-rust/30 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <div className="grid grid-cols-2 gap-3 mb-4">
              <div>
                <label className="block text-sm font-medium text-sand mb-1">First name</label>
                <input
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  required
                  autoFocus
                  className="w-full rounded-lg border border-clay bg-ink text-cream px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-marigold"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-sand mb-1">Last name</label>
                <input
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  required
                  className="w-full rounded-lg border border-clay bg-ink text-cream px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-marigold"
                />
              </div>
            </div>

            <label className="block text-sm font-medium text-sand mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full mb-4 rounded-lg border border-clay bg-ink text-cream px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-marigold"
            />

            <label className="block text-sm font-medium text-sand mb-1">Phone number</label>
            <input
              type="tel"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              required
              className="w-full mb-4 rounded-lg border border-clay bg-ink text-cream px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-marigold"
            />

            <label className="block text-sm font-medium text-sand mb-1">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="w-full mb-4 rounded-lg border border-clay bg-ink text-cream px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-marigold"
            />

            <label className="block text-sm font-medium text-sand mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full mb-6 rounded-lg border border-clay bg-ink text-cream px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-marigold"
            />

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-full bg-marigold text-ink py-2.5 font-semibold hover:opacity-90 transition disabled:opacity-50"
            >
              {loading ? "Creating account…" : "Create account"}
            </button>

            <p className="mt-5 text-center text-sm text-sand">
              Already registered?{" "}
              <button
                type="button"
                onClick={() => { setPanel("login"); setError(null); }}
                className="text-marigold font-medium hover:underline"
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