"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { Notification } from "@/types";

async function fetchNotifications(): Promise<Notification[]> {
  const { data } = await apiClient.get("/notifications/");
  return data.results ?? data;
}

export default function NotificationsPage() {
  const queryClient = useQueryClient();
  const { data: notifications, isLoading } = useQuery({
    queryKey: ["notifications"],
    queryFn: fetchNotifications,
  });

  const unreadCount = notifications?.filter((n) => !n.is_read).length ?? 0;

  async function markRead(id: string) {
    await apiClient.post(`/notifications/${id}/mark_read/`);
    queryClient.invalidateQueries({ queryKey: ["notifications"] });
    queryClient.invalidateQueries({ queryKey: ["unread-notification-count"] });
  }

  async function markAllRead() {
    await apiClient.post("/notifications/mark_all_read/");
    queryClient.invalidateQueries({ queryKey: ["notifications"] });
    queryClient.invalidateQueries({ queryKey: ["unread-notification-count"] });
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <h1 className="font-serif text-2xl">Notifications</h1>
        {unreadCount > 0 && (
          <button
            onClick={markAllRead}
            className="rounded-full border border-stone-300 px-4 py-1.5 text-sm font-medium text-stone-700 hover:bg-stone-50"
          >
            Mark all read
          </button>
        )}
      </div>
      <p className="text-stone-500 text-sm mb-8">Updates about your contract and payments.</p>

      {isLoading && <p className="text-stone-500">Loading…</p>}
      {notifications?.length === 0 && <p className="text-stone-500">No notifications yet.</p>}

      <div className="space-y-2">
        {notifications?.map((n) => (
          <div
            key={n.id}
            className={`rounded-xl border bg-white p-5 shadow-sm ${
              n.is_read ? "border-stone-200" : "border-emerald-300"
            }`}
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className={`text-sm ${n.is_read ? "font-medium text-stone-700" : "font-semibold text-stone-900"}`}>
                  {n.title}
                </p>
                <p className="text-stone-500 text-sm mt-1">{n.message}</p>
                <p className="text-stone-400 text-xs mt-2">
                  {new Date(n.created_at).toLocaleString()}
                </p>
              </div>
              {!n.is_read && (
                <button
                  onClick={() => markRead(n.id)}
                  className="text-emerald-800 text-sm font-medium hover:underline shrink-0"
                >
                  Mark read
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}