"use client";

import { useState } from "react";
import { apiClient } from "@/lib/api-client";
import { rateLimitMessage } from "@/lib/rate-limit";

interface InquiryFormProps {
  /** Where this form is being rendered — sent along with the submission so
   * staff reviewing inquiries in the admin panel can see where a lead
   * actually came from (e.g. "homepage", "contact_page"). */
  source: string;
  /** Set only when this form is shown in the context of a specific lot
   * (e.g. a future lot detail page) — omit for a general inquiry. */
  relatedLotId?: string;
  /** Optional — shown above the fields. */
  title?: string;
}

export function InquiryForm({ source, relatedLotId, title }: InquiryFormProps) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await apiClient.post("/inquiries/", {
        name,
        email,
        phone,
        message,
        source,
        related_lot: relatedLotId ?? null,
      });
      setSubmitted(true);
    } catch (err) {
      setError(rateLimitMessage(err) ?? "Something went wrong — please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  if (submitted) {
    return (
      <div className="border border-divider p-6 text-center">
        <p className="font-display font-semibold uppercase text-ink mb-1">Thanks for reaching out</p>
        <p className="text-sm text-neutral-600">We&apos;ve received your message and will get back to you soon.</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {title && <h3 className="font-display font-semibold uppercase text-lg text-ink">{title}</h3>}

      {error && (
        <p className="text-sm px-3 py-2 bg-red-50 text-red-800 border border-red-200">{error}</p>
      )}

      <div>
        <label className="block text-xs uppercase tracking-wide text-neutral-500 mb-1">Name</label>
        <input
          type="text" required value={name} onChange={(e) => setName(e.target.value)}
          className="w-full border border-divider px-3 py-2 text-sm"
        />
      </div>

      <div>
        <label className="block text-xs uppercase tracking-wide text-neutral-500 mb-1">Email</label>
        <input
          type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
          className="w-full border border-divider px-3 py-2 text-sm"
        />
      </div>

      <div>
        <label className="block text-xs uppercase tracking-wide text-neutral-500 mb-1">Phone (optional)</label>
        <input
          type="tel" value={phone} onChange={(e) => setPhone(e.target.value)}
          className="w-full border border-divider px-3 py-2 text-sm"
        />
      </div>

      <div>
        <label className="block text-xs uppercase tracking-wide text-neutral-500 mb-1">Message</label>
        <textarea
          required rows={4} value={message} onChange={(e) => setMessage(e.target.value)}
          className="w-full border border-divider px-3 py-2 text-sm"
        />
      </div>

      <button type="submit" disabled={submitting} className="btn btn-primary w-full">
        {submitting ? "Sending…" : "Send message"}
      </button>
    </form>
  );
}