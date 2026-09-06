import axios from "axios";
import { useAuthStore } from "@/lib/auth-store";

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api",
});

apiClient.interceptors.request.use((config) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// A 401 here means the token itself was rejected (missing/expired/invalid) —
// DRF's JWT auth fails the whole request in that case even on endpoints that
// otherwise allow anonymous access, so a stale token can silently break
// public pages too, not just protected ones. Clear it and retry once without
// it: public endpoints then succeed as anonymous; protected ones still 401,
// which the app's existing auth-required handling already covers.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      const hadToken = !!localStorage.getItem("access_token");
      if (hadToken) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("user");
        // Clearing localStorage alone left the header stale until a full
        // reload — it reads from this in-memory store, not localStorage
        // directly, so the store has to be cleared too for it to update
        // immediately rather than only on next navigation.
        useAuthStore.getState().setUser(null);
        // Only force visitors off a page that actually required being
        // logged in — a stale token can 401 on a public page's optional,
        // logged-in-only API call too (per the comment above), and forcing
        // a redirect away from a page they're allowed to be on anyway would
        // be more disruptive than just showing them as logged out.
        if (window.location.pathname.startsWith("/portal")) {
          window.location.href = "/";
        }
        const retryConfig = { ...error.config };
        delete retryConfig.headers?.Authorization;
        return apiClient(retryConfig);
      }
    }
    return Promise.reject(error);
  }
);