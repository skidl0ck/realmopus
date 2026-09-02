"use client";

import { useEffect, useState } from "react";
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

  // --- Notification preference (existing) ---
  const [savingNotif, setSavingNotif] = useState(false);
  const [savedNotif, setSavedNotif] = useState(false);

  async function toggleEmailNotifications(checked: boolean) {
    setSavingNotif(true);
    setSavedNotif(false);
    try {
      await apiClient.patch("/accounts/users/me/", { email_notifications_enabled: checked });
      queryClient.setQueryData(["me"], (old: User | undefined) =>
        old ? { ...old, email_notifications_enabled: checked } : old
      );
      setSavedNotif(true);
      setTimeout(() => setSavedNotif(false), 2000);
    } finally {
      setSavingNotif(false);
    }
  }

  // --- Profile fields ---
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [profileError, setProfileError] = useState<string | null>(null);
  const [profileSaved, setProfileSaved] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);

  useEffect(() => {
    if (user) {
      setFirstName(user.first_name);
      setLastName(user.last_name);
      setEmail(user.email);
      setPhoneNumber(user.phone_number ?? "");
    }
  }, [user]);

  async function saveProfile(e: React.FormEvent) {
    e.preventDefault();
    setProfileError(null);
    setProfileSaved(false);
    setSavingProfile(true);
    try {
      const { data } = await apiClient.patch<User>("/accounts/users/me/", {
        first_name: firstName,
        last_name: lastName,
        email,
        phone_number: phoneNumber,
      });
      queryClient.setQueryData(["me"], data);
      setProfileSaved(true);
      setTimeout(() => setProfileSaved(false), 2000);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: Record<string, string[]> } })?.response?.data;
      setProfileError(detail ? Object.values(detail).flat().join(" ") : "Couldn't save your profile — please try again.");
    } finally {
      setSavingProfile(false);
    }
  }

  // --- Password change ---
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSaved, setPasswordSaved] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);

  async function changePassword(e: React.FormEvent) {
    e.preventDefault();
    setPasswordError(null);
    setPasswordSaved(false);
    setSavingPassword(true);
    try {
      await apiClient.post("/accounts/users/change_password/", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setCurrentPassword("");
      setNewPassword("");
      setPasswordSaved(true);
      setTimeout(() => setPasswordSaved(false), 2000);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: Record<string, string[]> } })?.response?.data;
      setPasswordError(detail ? Object.values(detail).flat().join(" ") : "Couldn't change your password — please try again.");
    } finally {
      setSavingPassword(false);
    }
  }

  return (
    <div>
      <h1 className="font-display text-2xl mb-1 text-cream">Settings</h1>
      <p className="text-sand text-sm mb-8">Manage your profile, password, and how we contact you.</p>

      {isLoading && <p className="text-sand">Loading…</p>}

      {user && (
        <div className="space-y-6 max-w-lg">
          {/* Profile */}
          <form onSubmit={saveProfile} className="rounded-2xl border border-clay bg-clay p-6">
            <h2 className="font-display text-lg mb-4 text-cream">Profile</h2>

            {profileError && (
              <p className="mb-4 text-sm text-rust bg-rust/10 border border-rust/30 rounded-lg px-3 py-2">
                {profileError}
              </p>
            )}

            <div className="grid grid-cols-2 gap-3 mb-4">
              <div>
                <label className="block text-sm font-medium text-sand mb-1">First name</label>
                <input
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  required
                  className="w-full rounded-lg border border-clay bg-ink text-cream px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-marigold"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-sand mb-1">Last name</label>
                <input
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  required
                  className="w-full rounded-lg border border-clay bg-ink text-cream px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-marigold"
                />
              </div>
            </div>

            <label className="block text-sm font-medium text-sand mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full mb-4 rounded-lg border border-clay bg-ink text-cream px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-marigold"
            />

            <label className="block text-sm font-medium text-sand mb-1">Phone number</label>
            <input
              type="tel"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              className="w-full mb-4 rounded-lg border border-clay bg-ink text-cream px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-marigold"
            />

            <button
              type="submit"
              disabled={savingProfile}
              className="rounded-full bg-marigold text-ink text-sm font-semibold px-5 py-2 hover:opacity-90 transition disabled:opacity-50 cursor-pointer"
            >
              {savingProfile ? "Saving…" : "Save profile"}
            </button>
            {profileSaved && <p className="text-sage text-sm mt-3">Saved.</p>}
          </form>

          {/* Password */}
          <form onSubmit={changePassword} className="rounded-2xl border border-clay bg-clay p-6">
            <h2 className="font-display text-lg mb-4 text-cream">Change Password</h2>

            {passwordError && (
              <p className="mb-4 text-sm text-rust bg-rust/10 border border-rust/30 rounded-lg px-3 py-2">
                {passwordError}
              </p>
            )}

            <label className="block text-sm font-medium text-sand mb-1">Current password</label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
              className="w-full mb-4 rounded-lg border border-clay bg-ink text-cream px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-marigold"
            />

            <label className="block text-sm font-medium text-sand mb-1">New password</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              className="w-full mb-4 rounded-lg border border-clay bg-ink text-cream px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-marigold"
            />

            <button
              type="submit"
              disabled={savingPassword}
              className="rounded-full bg-marigold text-ink text-sm font-semibold px-5 py-2 hover:opacity-90 transition disabled:opacity-50 cursor-pointer"
            >
              {savingPassword ? "Changing…" : "Change password"}
            </button>
            {passwordSaved && <p className="text-sage text-sm mt-3">Password changed.</p>}
          </form>

          {/* Email notifications (existing) */}
          <div className="rounded-2xl border border-clay bg-clay p-6">
            <h2 className="font-display text-lg mb-4 text-cream">Email Notifications</h2>
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={user.email_notifications_enabled}
                onChange={(e) => toggleEmailNotifications(e.target.checked)}
                disabled={savingNotif}
                className="mt-1 rounded border-clay text-marigold focus:ring-marigold"
              />
              <span className="text-sm text-sand">
                Email me about my account and payments — payment confirmations, overdue
                reminders, and contract updates.
              </span>
            </label>
            {savedNotif && <p className="text-sage text-sm mt-3">Saved.</p>}
          </div>
        </div>
      )}
    </div>
  );
}