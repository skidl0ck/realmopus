"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  login,
  registerWithTransaction,
  reactivateWithTransaction,
  dashboardPathForRole,
  TransactionRequiredError,
  AccountDeactivatedError,
} from "@/lib/auth";
import { useAuthStore } from "@/lib/auth-store";
import { useAuthModalStore } from "@/lib/auth-modal-store";

type Panel = "login" | "register" | "reactivate";

export function AuthModal() {
  const router = useRouter();
  const setUser = useAuthStore((s) => s.setUser);
  const { isOpen, mode, nextPath, close } = useAuthModalStore();

  const [panel, setPanel] = useState<Panel>(mode);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState("");
  const [transactionNumber, setTransactionNumber] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Reset form state each time the modal is (re)opened, and honor the mode it was opened in.
  useEffect(() => {
    if (isOpen) {
      setPanel(mode);
      setUsername("");
      setPassword("");
      setEmail("");
      setTransactionNumber("");
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
      if (err instanceof TransactionRequiredError) {
        setPanel("reactivate");
      } else if (err instanceof AccountDeactivatedError) {
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
      const user = await registerWithTransaction(username, password, transactionNumber, email);
      finishAuth(user);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: Record<string, string[]> } })?.response?.data;
      setError(detail ? Object.values(detail).flat().join(" ") : "Couldn't create your account. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleReactivate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const user = await reactivateWithTransaction(username, password, transactionNumber);
      finishAuth(user);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: Record<string, string[]> } })?.response?.data;
      setError(
        detail
          ? Object.values(detail).flat().join(" ")
          : "Couldn't reactivate your account. Check the transaction number and try again."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-stone-900/50 backdrop-blur-sm" onClick={close} />

      {/* Modal card */}
      <div className="relative w-full max-w-sm rounded-2xl bg-white shadow-xl p-8">
        <button
          onClick={close}
          aria-label="Close"
          className="absolute top-4 right-4 text-stone-400 hover:text-stone-600"
        >
          ✕
        </button>

        {panel === "login" && (
          <form onSubmit={handleLogin}>
            <h1 className="font-serif text-2xl mb-1">Sign in</h1>
            <p className="text-stone-500 text-sm mb-6">
              Access your contract, payment schedule, and receipts.
            </p>

            {error && (
              <p className="mb-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <label className="block text-sm font-medium text-stone-700 mb-1">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
              className="w-full mb-4 rounded-lg border border-stone-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
            />

            <label className="block text-sm font-medium text-stone-700 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full mb-6 rounded-lg border border-stone-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
            />

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-full bg-emerald-800 text-white py-2.5 font-medium hover:bg-emerald-900 transition disabled:opacity-50"
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>

            <p className="mt-5 text-center text-sm text-stone-500">
              New buyer?{" "}
              <button
                type="button"
                onClick={() => { setPanel("register"); setError(null); }}
                className="text-emerald-800 font-medium hover:underline"
              >
                Register with your transaction number
              </button>
            </p>
          </form>
        )}

        {panel === "register" && (
          <form onSubmit={handleRegister}>
            <h1 className="font-serif text-2xl mb-1">Create your account</h1>
            <p className="text-stone-500 text-sm mb-6">
              Enter the transaction number from your contract to set up online payments.
            </p>

            {error && (
              <p className="mb-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <label className="block text-sm font-medium text-stone-700 mb-1">Transaction number</label>
            <input
              type="text"
              value={transactionNumber}
              onChange={(e) => setTransactionNumber(e.target.value)}
              placeholder="e.g. GV-2026-0001"
              required
              autoFocus
              className="w-full mb-4 rounded-lg border border-stone-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
            />

            <label className="block text-sm font-medium text-stone-700 mb-1">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="w-full mb-4 rounded-lg border border-stone-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
            />

            <label className="block text-sm font-medium text-stone-700 mb-1">Email (optional)</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full mb-4 rounded-lg border border-stone-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
            />

            <label className="block text-sm font-medium text-stone-700 mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full mb-6 rounded-lg border border-stone-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
            />

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-full bg-emerald-800 text-white py-2.5 font-medium hover:bg-emerald-900 transition disabled:opacity-50"
            >
              {loading ? "Creating account…" : "Create account"}
            </button>

            <p className="mt-5 text-center text-sm text-stone-500">
              Already registered?{" "}
              <button
                type="button"
                onClick={() => { setPanel("login"); setError(null); }}
                className="text-emerald-800 font-medium hover:underline"
              >
                Sign in
              </button>
            </p>
          </form>
        )}

        {panel === "reactivate" && (
          <form onSubmit={handleReactivate}>
            <h1 className="font-serif text-2xl mb-1">Transaction completed</h1>
            <p className="text-stone-600 text-sm mb-6">
              Your last transaction has been fully paid. Enter a new active
              transaction number to log in again.
            </p>

            {error && (
              <p className="mb-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <label className="block text-sm font-medium text-stone-700 mb-1">New transaction number</label>
            <input
              type="text"
              value={transactionNumber}
              onChange={(e) => setTransactionNumber(e.target.value)}
              placeholder="e.g. GV-2026-0002"
              required
              autoFocus
              className="w-full mb-6 rounded-lg border border-stone-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-600"
            />

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-full bg-emerald-800 text-white py-2.5 font-medium hover:bg-emerald-900 transition disabled:opacity-50"
            >
              {loading ? "Verifying…" : "Reactivate and sign in"}
            </button>

            <button
              type="button"
              onClick={() => { setPanel("login"); setError(null); }}
              className="mt-4 w-full text-center text-sm text-stone-500 hover:text-stone-700"
            >
              ← Back to sign in
            </button>
          </form>
        )}
      </div>
    </div>
  );
}