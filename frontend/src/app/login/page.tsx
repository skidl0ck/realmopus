"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { login, reactivateWithTransaction, dashboardPathForRole, TransactionRequiredError } from "@/lib/auth";
import { useAuthStore } from "@/lib/auth-store";

export default function LoginPage() {
  const router = useRouter();
  const setUser = useAuthStore((s) => s.setUser);

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [transactionNumber, setTransactionNumber] = useState("");
  const [needsReactivation, setNeedsReactivation] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const user = await login(username, password);
      setUser(user);
      router.push(dashboardPathForRole(user.role));
    } catch (err) {
      if (err instanceof TransactionRequiredError) {
        setNeedsReactivation(true);
      } else {
        setError("Invalid username or password.");
      }
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
      setUser(user);
      router.push(dashboardPathForRole(user.role));
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: Record<string, string[]> } })?.response?.data;
      const message = detail
        ? Object.values(detail).flat().join(" ")
        : "Couldn't reactivate your account. Check the transaction number and try again.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex-1 flex items-center justify-center px-6 py-20 overflow-hidden">
      <div className="relative w-full max-w-sm h-[420px]">
        {/* Normal login panel */}
        <div
          className={`absolute inset-0 transition-transform duration-300 ease-out ${
            needsReactivation ? "-translate-x-full opacity-0 pointer-events-none" : "translate-x-0 opacity-100"
          }`}
        >
          <form
            onSubmit={handleLogin}
            className="rounded-2xl border border-stone-200 bg-white p-8 shadow-sm"
          >
            <h1 className="font-serif text-2xl mb-1">Sign in</h1>
            <p className="text-stone-500 text-sm mb-6">
              Access your contract, payment schedule, and receipts.
            </p>

            {error && !needsReactivation && (
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
              <Link href="/register" className="text-emerald-800 font-medium hover:underline">
                Register with your transaction number
              </Link>
            </p>
          </form>
        </div>

        {/* Reactivation panel — slides in once the last transaction has completed */}
        <div
          className={`absolute inset-0 transition-transform duration-300 ease-out ${
            needsReactivation ? "translate-x-0 opacity-100" : "translate-x-full opacity-0 pointer-events-none"
          }`}
        >
          <form
            onSubmit={handleReactivate}
            className="rounded-2xl border border-amber-200 bg-amber-50 p-8 shadow-sm"
          >
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

            <label className="block text-sm font-medium text-stone-700 mb-1">
              New transaction number
            </label>
            <input
              type="text"
              value={transactionNumber}
              onChange={(e) => setTransactionNumber(e.target.value)}
              placeholder="e.g. GV-2026-0002"
              required
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
              onClick={() => {
                setNeedsReactivation(false);
                setError(null);
              }}
              className="mt-4 w-full text-center text-sm text-stone-500 hover:text-stone-700"
            >
              ← Back to sign in
            </button>
          </form>
        </div>
      </div>
    </main>
  );
}