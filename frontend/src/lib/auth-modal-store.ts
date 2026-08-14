import { create } from "zustand";

export type AuthModalMode = "login" | "register";

interface AuthModalState {
  isOpen: boolean;
  mode: AuthModalMode;
  nextPath: string | null;
  open: (mode: AuthModalMode, nextPath?: string) => void;
  close: () => void;
  setMode: (mode: AuthModalMode) => void;
}

export const useAuthModalStore = create<AuthModalState>((set) => ({
  isOpen: false,
  mode: "login",
  nextPath: null,
  open: (mode, nextPath) => set({ isOpen: true, mode, nextPath: nextPath ?? null }),
  close: () => set({ isOpen: false }),
  setMode: (mode) => set({ mode }),
}));