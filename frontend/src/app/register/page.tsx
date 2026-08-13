"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { registerWithTransaction, dashboardPathForRole } from "@/lib/auth";
import { useAuthStore } from "@/lib/auth-store";

export default function RegisterPage() {
  const router = useRouter();
  const setUser = useAuthStore((s) => s.setUser);

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [transactionNumber, setTransactionNumber] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const user = await registerWithTransaction(username, password, transactionNumber, email);
      setUser(user);
      router.push(dashboardPathForRole(user.role));
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: Record<string, string[]> } })?.response?.data;
      const message = detail
        ? Object.values(detail).flat().join(" ")
        : "Couldn't create your account. Please try again.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex-1 flex items-center justify-center px-6 py-20">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm rounded-2xl border border-stone-200 bg-white p-8 shadow-sm"
      >
        <h1 className="font-serif text-2xl mb-1">Create your account</h1>
        <p className="text-stone-500 text-sm mb-6">
          Enter the transaction number from your contract to set up online
          payments.
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
          <Link href="/login" className="text-emerald-800 font-medium hover:underline">
            Sign in
          </Link>
        </p>
      </form>
    </main>
  );
}