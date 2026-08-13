import { apiClient } from "@/lib/api-client";
import type { User } from "@/types";

interface LoginResponse {
  access: string;
  refresh: string;
}

interface RegisterResponse {
  user: User;
  access: string;
  refresh: string;
}

export class TransactionRequiredError extends Error {}

function storeSession(user: User, access: string, refresh: string) {
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
  localStorage.setItem("user", JSON.stringify(user));
}

export async function login(username: string, password: string): Promise<User> {
  try {
    const { data } = await apiClient.post<LoginResponse>("/auth/login/", { username, password });
    const me = await apiClient.get<User>("/accounts/users/me/", {
      headers: { Authorization: `Bearer ${data.access}` },
    });
    storeSession(me.data, data.access, data.refresh);
    return me.data;
  } catch (err: unknown) {
    const response = (err as { response?: { status?: number; data?: { code?: string } } })?.response;
    if (response?.status === 403 && response?.data?.code === "transaction_required") {
      throw new TransactionRequiredError();
    }
    throw err;
  }
}

export async function registerWithTransaction(
  username: string,
  password: string,
  transactionNumber: string,
  email?: string
): Promise<User> {
  const { data } = await apiClient.post<RegisterResponse>("/accounts/register/", {
    username,
    password,
    email,
    transaction_number: transactionNumber,
  });
  storeSession(data.user, data.access, data.refresh);
  return data.user;
}

export async function reactivateWithTransaction(
  username: string,
  password: string,
  transactionNumber: string
): Promise<User> {
  const { data } = await apiClient.post<RegisterResponse>("/accounts/reactivate/", {
    username,
    password,
    transaction_number: transactionNumber,
  });
  storeSession(data.user, data.access, data.refresh);
  return data.user;
}

export function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("user");
  return raw ? (JSON.parse(raw) as User) : null;
}

export function dashboardPathForRole(role: User["role"]): string {
  switch (role) {
    case "admin":
      return "/admin";
    case "sales_agent":
      return "/agent";
    case "accountant":
      return "/accountant";
    case "client":
    default:
      return "/portal";
  }
}