"use client";

import { useCompanyName } from "@/lib/site-config";
import { InquiryForm } from "@/components/inquiry-form";

export default function ContactPage() {
  const companyName = useCompanyName();

  return (
    <div className="mx-auto max-w-4xl px-6 py-16 grid gap-12 sm:grid-cols-2">
      <div>
        <h1 className="font-display font-semibold text-3xl uppercase text-ink mb-4">
          Contact Us
        </h1>
        <p className="text-neutral-700 leading-relaxed mb-8">
          Questions about a lot, a reservation, or your payment schedule? Send us a message
          and someone from {companyName} will get back to you.
        </p>

        <div className="space-y-4 text-sm">
          <div>
            <p className="text-xs uppercase tracking-wide text-neutral-500 mb-1">Office</p>
            <p className="text-neutral-700">[Replace with your real office address]</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-neutral-500 mb-1">Hours</p>
            <p className="text-neutral-700">[Replace with your real business hours]</p>
          </div>
        </div>
      </div>

      <InquiryForm source="contact_page" />
    </div>
  );
}