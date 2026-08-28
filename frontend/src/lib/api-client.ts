import axios from "axios";

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
        const retryConfig = { ...error.config };
        delete retryConfig.headers?.Authorization;
        return apiClient(retryConfig);
      }
    }
    return Promise.reject(error);
  }
);