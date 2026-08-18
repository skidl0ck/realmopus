import { create } from "zustand";
import type { User } from "@/types";

interface AuthState {
  user: User | null;
  setUser: (user: User | null) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
}));

export const NAV_ITEMS_BY_ROLE: Record<string, { label: string; href: string }[]> = {
  admin: [
    { label: "Overview", href: "/admin" },
    { label: "Projects & Lots", href: "/admin/lots" },
    { label: "Contracts", href: "/admin/contracts" },
    { label: "Clients", href: "/admin/clients" },
    { label: "Users & Roles", href: "/admin/users" },
  ],
  sales_agent: [
    { label: "My Reservations", href: "/agent" },
    { label: "Available Lots", href: "/agent/lots" },
    { label: "My Contracts", href: "/agent/contracts" },
    { label: "Commissions", href: "/agent/commissions" },
  ],
  accountant: [
    { label: "Cash Flow", href: "/accountant" },
    { label: "Payments", href: "/accountant/payments" },
    { label: "Expenses", href: "/accountant/expenses" },
    { label: "Aging Report", href: "/accountant/aging" },
  ],
  client: [
    { label: "My Contract", href: "/portal" },
    { label: "Payment Schedule", href: "/portal/schedule" },
    { label: "Make a Payment", href: "/portal/pay" },
    { label: "Receipts", href: "/portal/receipts" },
    { label: "Notifications", href: "/portal/notifications" },
    { label: "Settings", href: "/portal/settings" },
  ],
};