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
      setProfileError(detail ? Object.values(detail).flat().join(" ") : "Couldn't save your profile - please try again.");
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
      setPasswordError(detail ? Object.values(detail).flat().join(" ") : "Couldn't change your password - please try again.");
    } finally {
      setSavingPassword(false);
    }
  }

  return (
    <div>
      <h1 className="font-display font-semibold uppercase text-2xl mb-1 text-ink">Settings</h1>
      <p className="text-neutral-600 text-sm mb-8">Manage your profile, password, and how we contact you.</p>

      {isLoading && <p className="text-neutral-600">Loading…</p>}

      {user && (
        <div className="space-y-6 max-w-lg">
          {/* Profile */}
          <form onSubmit={saveProfile} className="border border-divider p-6">
            <h2 className="font-display font-semibold uppercase text-lg mb-4 text-ink">Profile</h2>

            {profileError && (
              <p className="mb-4 text-sm text-red-800 bg-red-50 border border-red-200 px-3 py-2">
                {profileError}
              </p>
            )}

            <div className="grid grid-cols-2 gap-3 mb-4">
              <div>
                <label className="block text-sm font-medium text-neutral-600 mb-1">First name</label>
                <input
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  required
                  className="input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-neutral-600 mb-1">Last name</label>
                <input
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  required
                  className="input"
                />
              </div>
            </div>

            <label className="block text-sm font-medium text-neutral-600 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="input mb-4"
            />

            <label className="block text-sm font-medium text-neutral-600 mb-1">Phone number</label>
            <input
              type="tel"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              className="input mb-4"
            />

            <button
              type="submit"
              disabled={savingProfile}
              className="btn btn-primary"
            >
              {savingProfile ? "Saving…" : "Save profile"}
            </button>
            {profileSaved && <p className="text-green-800 text-sm mt-3">Saved.</p>}
          </form>

          {/* Password */}
          <form onSubmit={changePassword} className="border border-divider p-6">
            <h2 className="font-display font-semibold uppercase text-lg mb-4 text-ink">Change Password</h2>

            {passwordError && (
              <p className="mb-4 text-sm text-red-800 bg-red-50 border border-red-200 px-3 py-2">
                {passwordError}
              </p>
            )}

            <label className="block text-sm font-medium text-neutral-600 mb-1">Current password</label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
              className="input mb-4"
            />

            <label className="block text-sm font-medium text-neutral-600 mb-1">New password</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              className="input mb-4"
            />

            <button
              type="submit"
              disabled={savingPassword}
              className="btn btn-primary"
            >
              {savingPassword ? "Changing…" : "Change password"}
            </button>
            {passwordSaved && <p className="text-green-800 text-sm mt-3">Password changed.</p>}
          </form>

          {/* Email notifications (existing) */}
          <div className="border border-divider p-6">
            <h2 className="font-display font-semibold uppercase text-lg mb-4 text-ink">Email Notifications</h2>
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={user.email_notifications_enabled}
                onChange={(e) => toggleEmailNotifications(e.target.checked)}
                disabled={savingNotif}
                className="mt-1 border-divider text-accent"
              />
              <span className="text-sm text-neutral-600">
                Email me about my account and payments - payment confirmations, overdue
                reminders, and contract updates.
              </span>
            </label>
            {savedNotif && <p className="text-green-800 text-sm mt-3">Saved.</p>}
          </div>
        </div>
      )}
    </div>
  );
}