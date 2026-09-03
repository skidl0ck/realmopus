"use client";

import Image from "next/image";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { Lot } from "@/types";
import { Reveal } from "@/components/reveal";
import { LotGridAnimation } from "@/components/lot-grid-animation";
import { Blueprint } from "@/components/blueprint";
import { useAuthModalStore } from "@/lib/auth-modal-store";
import { useCurrencySymbol } from "@/lib/currency";
import { useCompanyName } from "@/lib/site-config";

async function fetchFeaturedLots(): Promise<Lot[]> {
  const { data } = await apiClient.get("/properties/lots/?status=available");
  const lots = data.results ?? data;
  return lots.slice(0, 3);
}

const OFFERINGS = [
  {
    title: "Flexible payment plans",
    body: "Pay in full, or spread your purchase over fixed monthly installments with transparent service fees - no hidden charges.",
  },
  {
    title: "Reserve online",
    body: "Found a lot you like? Reserve it directly through the site with a reservation fee while we prepare your contract.",
  },
  {
    title: "Pay anytime, anywhere",
    body: "Settle your monthly dues through PayPal or your preferred local e-wallet, right from your client account.",
  },
  {
    title: "Clear payment schedule",
    body: "See your full amortization schedule up front - every due date, amount, and fee, laid out with no surprises.",
  },
  {
    title: "Digital receipts",
    body: "Every payment is recorded the moment it's made, with an official receipt you can access anytime.",
  },
  {
    title: "Dedicated sales support",
    body: "Our sales team is on hand to help you pick the right lot and walk you through the paperwork.",
  },
];

const STEPS = [
  { title: "Browse available lots", body: "Explore lots by block, size, and price across the development." },
  { title: "Reserve your lot", body: "Pay a small reservation fee to hold your chosen lot while your contract is prepared." },
  { title: "Sign your contract", body: "Choose full payment or an installment plan that fits your budget." },
  { title: "Create your account", body: "Use the transaction number from your contract to set up online access." },
  { title: "Pay & track online", body: "Make payments anytime and monitor your balance, schedule, and receipts from your portal." },
];

export default function HomePage() {
  const { data: featuredLots } = useQuery({ queryKey: ["featured-lots"], queryFn: fetchFeaturedLots });
  const openAuthModal = useAuthModalStore((s) => s.open);
  const currency = useCurrencySymbol();
  const companyName = useCompanyName();

  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden">
        <video
          autoPlay muted loop playsInline
          className="absolute inset-0 w-full h-full object-cover"
        >
          <source src="/videos/5031099-uhd_3840_2160_30fps.mp4" type="video/mp4" />
        </video>
        {/* Accent wash over the footage -- ties it to the same "photographs
            washed in the accent" treatment used everywhere else in this
            theme, rather than a raw, unrelated stock clip. */}
        <div
          className="absolute inset-0 pointer-events-none"
          style={{ background: "var(--color-accent)", mixBlendMode: "color" }}
        />
        {/* Light scrim so the dark headline stays legible regardless of what
            the footage is doing at any given moment -- strongest behind the
            text column, fading out toward the site-plan card on the right,
            which already has its own solid ground. */}
        <div className="absolute inset-0 pointer-events-none bg-gradient-to-r from-bg via-bg/85 to-bg/40" />

        <div className="relative mx-auto max-w-6xl px-6 pt-20 pb-16 grid lg:grid-cols-[7fr_5fr] gap-12 items-end">
          <div>
            <h1 className="font-display font-semibold uppercase leading-[1.04] tracking-tight text-5xl sm:text-6xl lg:text-7xl text-ink">
              Your family&apos;s place<br />in the valley.
            </h1>
            <p className="mt-7 text-neutral-700 max-w-xl text-[17px] leading-relaxed">
              Surveyed subdivision lots across Cagayan Valley, in view of the Sierra
              Madre. Reserve online, pay on a fixed schedule, and track every peso
              from your account - whether you&apos;re building here or sending from abroad.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/lots" className="btn btn-primary">
                Browse available lots
              </Link>
              <button onClick={() => openAuthModal("login")} className="btn btn-secondary">
                Client portal login
              </button>
            </div>
            <p className="mt-8 text-xs tracking-widest uppercase font-semibold text-neutral-500">
              {companyName} · Tuguegarao City · Cagayan Valley
            </p>
          </div>

          <Blueprint className="p-5 bg-bg">
            <div className="flex justify-between gap-3 text-xs tracking-widest uppercase font-semibold text-neutral-600 mb-3.5">
              <span>Site plan</span>
            <span>Live inventory</span>
          </div>
          <LotGridAnimation />
          </Blueprint>
        </div>
      </section>

      {/* About */}
      <section className="bg-surface border-y border-divider">
        <div className="mx-auto max-w-3xl px-6 py-20 text-center">
          <Reveal>
            <h2 className="font-display font-semibold uppercase text-3xl mb-4 text-ink">A simpler way to buy land</h2>
            <p className="text-neutral-700 leading-relaxed">
              {companyName} offers straightforward lot ownership across Cagayan Valley, on your terms.
              Whether you&apos;re ready to pay in full or prefer to spread the cost over time, the
              entire process - from browsing available lots to making your final
              payment - happens online, with nothing lost in translation between
              you and our sales office.
            </p>
          </Reveal>
        </div>
      </section>

      {/* Community photo */}
      <section className="mx-auto max-w-6xl px-6 py-20">
        <Reveal>
          <Blueprint className="duotone relative overflow-hidden aspect-[16/7]" as="figure">
            <Image
              src="/images/community-aerial.jpg"
              alt={`Aerial view of a ${companyName} subdivision`}
              fill
              className="object-cover"
              sizes="(min-width: 1024px) 1152px, 100vw"
            />
          </Blueprint>
        </Reveal>
      </section>

      {/* Offerings */}
      <section id="offerings" className="mx-auto max-w-6xl px-6 py-20">
        <Reveal>
          <span className="block text-xs tracking-widest uppercase font-semibold text-accent-700 mb-3">03 · What we offer</span>
          <hr className="border-0 h-px bg-divider mb-9" />
          <h2 className="font-display font-semibold uppercase text-3xl mb-2 text-ink">What we offer</h2>
          <p className="text-neutral-600 mb-14 max-w-xl">
            Everything you need to buy and manage your lot, without the paperwork runaround.
          </p>
        </Reveal>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {OFFERINGS.map((f, i) => (
            <Reveal key={f.title} delay={i * 80}>
              <Blueprint className="p-6 h-full">
                <h3 className="font-display font-semibold uppercase text-xl mb-2 text-ink">{f.title}</h3>
                <p className="text-neutral-600 text-sm leading-relaxed">{f.body}</p>
              </Blueprint>
            </Reveal>
          ))}
        </div>
      </section>

      {/* Featured lots */}
      {featuredLots && featuredLots.length > 0 && (
        <section className="bg-surface border-y border-divider">
          <div className="mx-auto max-w-6xl px-6 py-20">
            <Reveal>
              <span className="block text-xs tracking-widest uppercase font-semibold text-accent-700 mb-3">02 · Available now</span>
              <hr className="border-0 h-px bg-divider mb-3" />
              <div className="flex items-baseline justify-between gap-6 mb-10">
                <h2 className="font-display font-semibold uppercase text-3xl text-ink">Available now</h2>
                <Link href="/lots" className="text-accent-700 font-medium hover:underline text-sm whitespace-nowrap">
                  View all lots →
                </Link>
              </div>
            </Reveal>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {featuredLots.map((lot, i) => (
                <Reveal key={lot.id} delay={i * 100}>
                  <Blueprint className="p-5 flex flex-col">
                    <div className="duotone relative aspect-[4/3] mb-5">
                      <Image
                        src="/images/lot-placeholder.jpg"
                        alt={`Block ${lot.block_number}, Lot ${lot.lot_number}`}
                        fill
                        className="object-cover"
                        sizes="(min-width: 1024px) 33vw, (min-width: 640px) 50vw, 100vw"
                      />
                    </div>
                    <p className="font-display font-semibold uppercase text-lg mb-1 text-ink">
                      Block {lot.block_number}, Lot {lot.lot_number}
                    </p>
                    <p className="text-neutral-600 text-sm mb-3">{lot.area_sqm} sqm</p>
                    <p className="text-ink font-semibold text-2xl font-data">
                      {currency}{Number(lot.total_price).toLocaleString()}
                    </p>
                  </Blueprint>
                </Reveal>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* How it works */}
      <section id="how-it-works" className="mx-auto max-w-6xl px-6 py-20">
        <Reveal>
          <span className="block text-xs tracking-widest uppercase font-semibold text-accent-700 mb-3">04 · How it works</span>
          <hr className="border-0 h-px bg-divider mb-2" />
        </Reveal>
        <div className="grid gap-6 sm:grid-cols-5 mt-8">
          {STEPS.map((step, i) => (
            <Reveal key={step.title} delay={i * 100}>
              <div className="border-t border-divider pt-4">
                <p className="font-display font-semibold text-4xl text-accent mb-2 font-data">{String(i + 1).padStart(2, "0")}</p>
                <h3 className="font-display font-semibold uppercase text-lg mb-2 text-ink">{step.title}</h3>
                <p className="text-neutral-600 text-sm leading-relaxed">{step.body}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* Why choose us */}
      <section className="bg-surface border-y border-divider">
        <div className="mx-auto max-w-6xl px-6 py-20 grid lg:grid-cols-2 gap-12 items-center">
          <Reveal>
            <Blueprint className="duotone relative overflow-hidden aspect-[4/3]" as="figure">
              <Image
                src="/images/site-entrance.jpg"
                alt={`${companyName} subdivision entrance`}
                fill
                className="object-cover"
                sizes="(min-width: 1024px) 576px, 100vw"
              />
            </Blueprint>
          </Reveal>
          <div>
            <span className="block text-xs tracking-widest uppercase font-semibold text-accent-700 mb-3">05 · Why buy here</span>
            <hr className="border-0 h-px bg-divider mb-7" />
            <div className="grid grid-cols-2 gap-7">
              {[
                { label: "Prime location", body: "Well-situated lots across Cagayan Valley." },
                { label: "Transparent terms", body: "Fixed schedules, no hidden fees." },
                { label: "Secure payments", body: "PayPal & trusted local e-wallets." },
                { label: "Real-time availability", body: "Live inventory, always up to date." },
              ].map((item, i) => (
                <Reveal key={item.label} delay={i * 80}>
                  <p className="font-display font-semibold uppercase text-lg mb-1 text-ink">{item.label}</p>
                  <p className="text-neutral-600 text-sm">{item.body}</p>
                </Reveal>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="mx-auto max-w-6xl px-6 py-20">
        <Reveal>
          <Blueprint className="p-10 sm:p-14 text-center">
            <h2 className="font-display font-semibold uppercase text-3xl sm:text-4xl mb-4 text-ink">Ready to find your lot?</h2>
            <p className="text-neutral-600 mb-8 max-w-xl mx-auto">
              Browse what&apos;s available today, or create an account if you&apos;ve already reserved a lot with us.
            </p>
            <div className="flex flex-wrap gap-3 justify-center">
              <Link href="/lots" className="btn btn-primary">
                Browse available lots
              </Link>
              <button onClick={() => openAuthModal("register")} className="btn btn-secondary">
                Create an account
              </button>
            </div>
          </Blueprint>
        </Reveal>
      </section>
    </>
  );
}