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

export class AccountDeactivatedError extends Error {}

function storeSession(user: User, access: string, refresh: string) {
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
  localStorage.setItem("user", JSON.stringify(user));
}

/** Updates just the token pair, leaving the stored user untouched — for
 * endpoints like change_password that reissue fresh tokens (since changing
 * a password now blacklists every previously issued one, including the
 * one the current session was using) without the user's own data changing. */
export function updateStoredTokens(access: string, refresh: string) {
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
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
    if (response?.status === 403 && response?.data?.code === "account_deactivated") {
      throw new AccountDeactivatedError();
    }
    throw err;
  }
}

export interface RegisterFields {
  firstName: string;
  lastName: string;
  email: string;
  phoneNumber: string;
  username: string;
  password: string;
}

export async function register(fields: RegisterFields): Promise<User> {
  const { data } = await apiClient.post<RegisterResponse>("/accounts/register/", {
    first_name: fields.firstName,
    last_name: fields.lastName,
    email: fields.email,
    phone_number: fields.phoneNumber,
    username: fields.username,
    password: fields.password,
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