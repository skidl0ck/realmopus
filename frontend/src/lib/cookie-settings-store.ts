import { create } from "zustand";

interface CookieSettingsState {
  isOpen: boolean;
  open: () => void;
  close: () => void;
}

export const useCookieSettingsStore = create<CookieSettingsState>((set) => ({
  isOpen: false,
  open: () => set({ isOpen: true }),
  close: () => set({ isOpen: false }),
}));