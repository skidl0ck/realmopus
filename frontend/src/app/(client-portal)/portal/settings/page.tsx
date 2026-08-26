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
      <h1 className="font-display text-2xl mb-1 text-cream">Settings</h1>
      <p className="text-sand text-sm mb-8">Manage how we contact you.</p>

      {isLoading && <p className="text-sand">Loading…</p>}

      {user && (
        <div className="rounded-2xl border border-clay bg-clay p-6 max-w-lg">
          <h2 className="font-display text-lg mb-4 text-cream">Email Notifications</h2>
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={user.email_notifications_enabled}
              onChange={(e) => toggleEmailNotifications(e.target.checked)}
              disabled={saving}
              className="mt-1 rounded border-clay text-marigold focus:ring-marigold"
            />
            <span className="text-sm text-sand">
              Email me about my account and payments — payment confirmations, overdue
              reminders, and contract updates.
            </span>
          </label>
          {saved && <p className="text-sage text-sm mt-3">Saved.</p>}
        </div>
      )}
    </div>
  );
}