"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { User } from "@/types";

async function fetchMe(): Promise<User> {
  const { data } = await apiClient.get("/accounts/users/me/");
  return data;
}

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { data: user, isLoading } = useQuery({ queryKey: ["me"], queryFn: fetchMe });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  async function toggleEmailNotifications(checked: boolean) {
    setSaving(true);
    setSaved(false);
    try {
      await apiClient.patch("/accounts/users/me/", { email_notifications_enabled: checked });
      queryClient.setQueryData(["me"], (old: User | undefined) =>
        old ? { ...old, email_notifications_enabled: checked } : old
      );
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <h1 className="font-serif text-2xl mb-1">Settings</h1>
      <p className="text-stone-500 text-sm mb-8">Manage how we contact you.</p>

      {isLoading && <p className="text-stone-500">Loading…</p>}

      {user && (
        <div className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm max-w-lg">
          <h2 className="font-serif text-lg mb-4">Email Notifications</h2>
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={user.email_notifications_enabled}
              onChange={(e) => toggleEmailNotifications(e.target.checked)}
              disabled={saving}
              className="mt-1 rounded border-stone-300 text-emerald-700 focus:ring-emerald-600"
            />
            <span className="text-sm text-stone-700">
              Email me about my account and payments — payment confirmations, overdue
              reminders, and contract updates.
            </span>
          </label>
          {saved && <p className="text-emerald-700 text-sm mt-3">Saved.</p>}
        </div>
      )}
    </div>
  );
}