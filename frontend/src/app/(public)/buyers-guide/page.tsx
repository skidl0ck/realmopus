"use client";

import Link from "next/link";
import { useCompanyName } from "@/lib/site-config";

export default function BuyersGuidePage() {
  const companyName = useCompanyName();

  return (
    <div className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="font-display font-semibold text-3xl uppercase text-ink mb-2">
        Buyer&apos;s Guide
      </h1>
      <p className="text-neutral-700 leading-relaxed mb-10">
        A straightforward, step-by-step look at how buying a lot with {companyName}
        actually works, from first browsing a listing to your final payment.
      </p>

      <ol className="space-y-8">
        <li>
          <h2 className="font-display font-semibold text-lg uppercase text-ink mb-1">
            1. Browse available lots
          </h2>
          <p className="text-neutral-700 leading-relaxed">
            Explore listings by project, with real-time availability - each lot shows its
            area, price, and current status (available, reserved, or sold), so you always
            see accurate, up-to-date inventory.
          </p>
        </li>

        <li>
          <h2 className="font-display font-semibold text-lg uppercase text-ink mb-1">
            2. Reserve your chosen lot
          </h2>
          <p className="text-neutral-700 leading-relaxed">
            Reserving a lot online holds it exclusively for you for a set period, taking it
            off the market while you finalize your decision. A small reservation fee
            applies where required, paid securely through PayPal or a local e-wallet.
          </p>
        </li>

        <li>
          <h2 className="font-display font-semibold text-lg uppercase text-ink mb-1">
            3. Finalize your contract
          </h2>
          <p className="text-neutral-700 leading-relaxed">
            Our team finalizes the contract terms with you directly - choosing between
            full payment or an installment plan that fits your timeline.
          </p>
        </li>

        <li>
          <h2 className="font-display font-semibold text-lg uppercase text-ink mb-1">
            4. Pay on your schedule
          </h2>
          <p className="text-neutral-700 leading-relaxed">
            Once your contract is active, your full payment schedule is visible in your
            account at all times - see exactly what&apos;s paid, what&apos;s upcoming, and
            when it&apos;s due. Pay each installment online whenever it&apos;s due.
          </p>
        </li>

        <li>
          <h2 className="font-display font-semibold text-lg uppercase text-ink mb-1">
            5. Track everything in one place
          </h2>
          <p className="text-neutral-700 leading-relaxed">
            Every payment generates an instant receipt, stored in your account alongside
            your contract - nothing to request, nothing to chase down later.
          </p>
        </li>
      </ol>

      <p className="text-sm text-neutral-500 mt-10">
        Ready to get started?{" "}
        <Link href="/lots" className="text-accent font-medium hover:underline">Browse available lots</Link>.
      </p>
    </div>
  );
}