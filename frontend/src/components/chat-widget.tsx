"use client";

import { useEffect, useRef, useState } from "react";
import { apiClient } from "@/lib/api-client";
import { useChatStore, getOrCreateChatSessionId, type ChatMessage } from "@/lib/chat-store";

export function ChatWidget() {
  const { isOpen, messages, isSending, hasLoadedHistory, toggle, close, addMessage, setSending, restoreHistory } =
    useChatStore();
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (hasLoadedHistory) return;
    const sessionId = getOrCreateChatSessionId();
    apiClient
      .get("/chat/history/", { params: { session_id: sessionId } })
      .then(({ data }) => restoreHistory(data.messages))
      .catch(() => restoreHistory([])); // fine to just start fresh if this fails
  }, [hasLoadedHistory, restoreHistory]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isOpen]);

  async function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || isSending) return;

    const userMessage: ChatMessage = { role: "user", content: text };
    const history = [...messages, userMessage];
    addMessage(userMessage);
    setInput("");
    setSending(true);

    try {
      const sessionId = getOrCreateChatSessionId();
      const { data } = await apiClient.post("/chat/", { messages: history, session_id: sessionId });
      addMessage({ role: "assistant", content: data.reply });
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { error?: string } } })?.response?.data?.error ??
        "Something went wrong — please try again in a moment.";
      addMessage({ role: "assistant", content: detail });
    } finally {
      setSending(false);
    }
  }

  return (
    <>
      {/* Floating toggle button */}
      <button
        onClick={toggle}
        aria-label={isOpen ? "Close chat" : "Open chat"}
        className="fixed bottom-6 right-6 z-40 w-14 h-14 rounded-full bg-emerald-800 text-white shadow-lg hover:bg-emerald-900 transition flex items-center justify-center"
      >
        {isOpen ? (
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M18 6 6 18M6 6l12 12" strokeLinecap="round" />
          </svg>
        ) : (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path
              d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5Z"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        )}
      </button>

      {/* Chat panel */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 z-40 w-[calc(100vw-3rem)] max-w-sm h-[32rem] max-h-[70vh] bg-white rounded-2xl shadow-2xl border border-stone-200 flex flex-col overflow-hidden">
          <div className="bg-emerald-800 text-white px-4 py-3 flex items-center justify-between shrink-0">
            <div>
              <p className="font-serif text-base leading-tight">Chat with us</p>
              <p className="text-xs text-emerald-100">Usually replies in seconds</p>
            </div>
            <button onClick={close} aria-label="Close chat" className="text-emerald-100 hover:text-white">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6 6 18M6 6l12 12" strokeLinecap="round" />
              </svg>
            </button>
          </div>

          <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-3 bg-stone-50">
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm ${
                    m.role === "user"
                      ? "bg-emerald-800 text-white rounded-br-sm"
                      : "bg-white border border-stone-200 text-stone-700 rounded-bl-sm"
                  }`}
                >
                  {m.content}
                </div>
              </div>
            ))}
            {isSending && (
              <div className="flex justify-start">
                <div className="bg-white border border-stone-200 rounded-2xl rounded-bl-sm px-3 py-2 text-sm text-stone-400">
                  Typing…
                </div>
              </div>
            )}
          </div>

          <form onSubmit={sendMessage} className="border-t border-stone-200 p-3 flex flex-col gap-2 shrink-0">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask a question…"
                disabled={isSending}
                className="flex-1 rounded-full border border-stone-300 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-700"
              />
              <button
                type="submit"
                disabled={isSending || !input.trim()}
                aria-label="Send"
                className="w-9 h-9 shrink-0 rounded-full bg-emerald-800 text-white flex items-center justify-center disabled:opacity-40 hover:bg-emerald-900 transition"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7Z" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            </div>
            <p className="text-[11px] text-stone-400 text-center leading-tight">
              Portfolio demo — please don&apos;t share real personal or financial information. Responses are AI-generated.
            </p>
          </form>
        </div>
      )}
    </>
  );
}