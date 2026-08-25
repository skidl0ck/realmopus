import { create } from "zustand";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface ChatState {
  isOpen: boolean;
  messages: ChatMessage[];
  isSending: boolean;
  hasLoadedHistory: boolean;
  toggle: () => void;
  close: () => void;
  addMessage: (message: ChatMessage) => void;
  setSending: (sending: boolean) => void;
  restoreHistory: (messages: ChatMessage[]) => void;
  reset: () => void;
}

const WELCOME_MESSAGE: ChatMessage = {
  role: "assistant",
  content: "Hi! I can answer questions about our available lots, pricing, and the buying process. What would you like to know?",
};

const SESSION_ID_KEY = "estateos_chat_session_id";

/** A stable, opaque ID for this visitor's chat session — generated once and
 * kept in localStorage so returning to the site (even after a refresh)
 * reconnects to the same conversation instead of starting a new one. */
export function getOrCreateChatSessionId(): string {
  if (typeof window === "undefined") return "";
  let id = window.localStorage.getItem(SESSION_ID_KEY);
  if (!id) {
    id = crypto.randomUUID();
    window.localStorage.setItem(SESSION_ID_KEY, id);
  }
  return id;
}

export const useChatStore = create<ChatState>((set) => ({
  isOpen: false,
  messages: [WELCOME_MESSAGE],
  isSending: false,
  hasLoadedHistory: false,
  toggle: () => set((state) => ({ isOpen: !state.isOpen })),
  close: () => set({ isOpen: false }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setSending: (sending) => set({ isSending: sending }),
  restoreHistory: (messages) =>
    set({ messages: messages.length > 0 ? messages : [WELCOME_MESSAGE], hasLoadedHistory: true }),
  reset: () => set({ messages: [WELCOME_MESSAGE] }),
}));