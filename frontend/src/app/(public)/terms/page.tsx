"use client";

import { useCompanyName } from "@/lib/site-config";
import { useSiteConfigQuery } from "@/lib/site-config";

export default function TermsPage() {
  const companyName = useCompanyName();
  const business_settings = useSiteConfigQuery();

  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="font-display font-semibold text-3xl uppercase text-ink mb-2">
        Terms &amp; Reservation Agreement
      </h1>
      <p className="text-xs text-neutral-500 mb-8">
        Demo disclosure - the information below is a draft template for demonstration
        purposes only and is not intended to serve as final legal terms or advice.
      </p>

      <p className="text-neutral-700 leading-relaxed mb-8">
        These terms govern browsing {companyName}&apos;s lot listings, reserving a lot,
        and entering into a contract to purchase, whether paid in full or through an
        installment plan.
      </p>

      <section className="mb-8">
        <h2 className="font-display font-semibold text-lg uppercase text-ink mb-2">1. Reservations</h2>
        <p className="text-neutral-700 leading-relaxed">
          Reserving a lot requires payment of the posted reservation fee and holds that
          lot exclusively for you for {business_settings.data?.reservation_hold_days} days. A reservation may be
          extended, up to {business_settings.data?.max_reservation_extensions} times, subject to availability. If the
          hold period lapses without a signed contract, the reservation may be released
          and the lot made available to other buyers. The reservation fee is
          non-refundable because accepting it removes the specific lot from the market,
          holds its price, and prevents us from offering it to other potential buyers.
          If a buyer walks away, we lose active selling time and other potential clients.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="font-display font-semibold text-lg uppercase text-ink mb-2">2. Contracts &amp; installment plans</h2>
        <p className="text-neutral-700 leading-relaxed">
          A contract to purchase is finalized with our staff, not self-service through the
          portal. Installment plans follow the payment schedule shown in your account at
          the time of signing. Payments received after the due date may
            incur a late fee of {business_settings.data?.default_penalty_rate_percent}% of the overdue amount. A 15-day grace period is
            provided before a missed payment is treated as a default. If an account
            remains unpaid after written notice and a further 15 days, the contract may
            be suspended or cancelled, and the lot may be offered to another buyer.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="font-display font-semibold text-lg uppercase text-ink mb-2">3. Payments</h2>
        <p className="text-neutral-700 leading-relaxed">
          Payments are processed through PayPal or PayMongo (GCash, Maya, or card). A
          payment is only considered complete once independently confirmed with the
          payment provider - not merely submitted. Receipts are generated automatically
          and available in your account.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="font-display font-semibold text-lg uppercase text-ink mb-2">4. Cancellations &amp; refunds</h2>
        <p className="text-neutral-700 leading-relaxed">
          Mock policy: Reservation fees are non-refundable after a reservation is
          confirmed. A buyer may request cancellation of an installment contract within
          7 days of signing for a full refund of payments made, less any processing
          fees. After that period, approved cancellations may receive a refund of
          eligible payments within 30 business days, less the reservation fee, overdue
          balances, and applicable administrative charges. Refunds are returned through
          the original payment method.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="font-display font-semibold text-lg uppercase text-ink mb-2">5. Limitation of liability</h2>
        <p className="text-neutral-700 leading-relaxed">
          Mock policy: To the fullest extent permitted by applicable law, our liability
          arising from browsing listings, reservations, contracts, payment processing, or
          use of the portal is limited to the amount you paid directly to us for the
          specific transaction giving rise to the claim. We are not responsible for
          indirect, incidental, special, or consequential losses, including lost profits,
          lost opportunities, or delays caused by events outside our reasonable control.
          This mock clause does not limit liability that cannot legally be excluded.
        </p>
      </section>

      <p className="text-sm text-neutral-500">
        Questions about these terms? See our{" "}
        <a href="/contact" className="text-accent font-medium hover:underline">Contact Us</a> page.
      </p>
    </div>
  );
}