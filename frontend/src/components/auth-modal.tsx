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