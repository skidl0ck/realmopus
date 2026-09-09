"use client";

import { useCompanyName } from "@/lib/site-config";

export default function AboutPage() {
  const companyName = useCompanyName();

  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="font-display font-semibold text-3xl uppercase text-ink mb-2">
        About {companyName}
      </h1>
      <p className="text-xs text-neutral-500 mb-8">
        Demo Disclosure - The information below is mock data used for demonstration purposes only.
      </p>

      <section className="mb-10">
        <h2 className="font-display font-semibold text-lg uppercase text-ink mb-2">Our story</h2>
        <p className="text-neutral-700 leading-relaxed">
          Founded in 2021, {companyName} was created to make property buying simpler,
          clearer, and more accessible. We set out to give buyers a straightforward way
          to discover homes, understand their options, and move from reservation to
          ownership with confidence.
        </p>
      </section>

      <section className="mb-10">
        <h2 className="font-display font-semibold text-lg uppercase text-ink mb-2">Why buy with us</h2>
        <div className="grid sm:grid-cols-3 gap-6">
          <div>
            <p className="font-medium text-ink mb-1">Everything online</p>
            <p className="text-sm text-neutral-600">
              Browse, reserve, sign, and pay - track your entire purchase from one account,
              without chasing paperwork.
            </p>
          </div>
          <div>
            <p className="font-medium text-ink mb-1">Flexible payment plans</p>
            <p className="text-sm text-neutral-600">
              Pay in full or spread the cost over an installment schedule that fits your
              timeline.
            </p>
          </div>
          <div>
            <p className="font-medium text-ink mb-1">Clear at every step</p>
            <p className="text-sm text-neutral-600">
              Real-time payment schedules, instant receipts, and a straightforward
              reservation-to-contract process.
            </p>
          </div>
        </div>
      </section>

      <section className="mb-10">
        <h2 className="font-display font-semibold text-lg uppercase text-ink mb-2">Our team</h2>
        <p className="text-neutral-700 leading-relaxed">
          Our team brings together experienced property advisors, customer support
          specialists, and technology professionals committed to making every purchase
          clear and straightforward. Meet our mock leadership team: Juan Dela Cruz, CEO;
          Pedro Reyes, Head of Property; and Maria Delos Santos, Customer Experience Lead.
        </p>
      </section>
    </div>
  );
}