"use client";

import Image from "next/image";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { Lot } from "@/types";
import { Reveal } from "@/components/reveal";
import { LotGridAnimation } from "@/components/lot-grid-animation";
import { SierraMadreMotif } from "@/components/sierra-madre-motif";
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
    body: "Pay in full, or spread your purchase over fixed monthly installments with transparent service fees — no hidden charges.",
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
    body: "See your full amortization schedule up front — every due date, amount, and fee, laid out with no surprises.",
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
      <section className="relative overflow-hidden bg-ink text-cream min-h-[92vh] flex flex-col">
        {/* Dawn glow rising from the horizon — ties the accent color directly to
            the mountain motif instead of leaving it as a flat dark rectangle */}
        <div
          className="absolute inset-0"
          style={{
            background: "radial-gradient(ellipse 90% 60% at 50% 100%, rgba(214, 138, 62, 0.22), transparent 70%)",
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-ink via-ink/95 to-transparent" />

        <div className="relative flex-1 flex flex-col items-center justify-center text-center px-6 pt-24 pb-10">
          <p className="text-marigold font-medium tracking-wide uppercase text-sm">
            {companyName} — Tuguegarao City, Cagayan Valley
          </p>
          <h1 className="mt-5 text-5xl sm:text-6xl font-display font-medium leading-tight max-w-3xl">
            Your family&apos;s place in the valley.
          </h1>
          <p className="mt-6 text-sand max-w-xl text-lg">
            Quality subdivision lots across Cagayan Valley, in view of the Sierra
            Madre — reserve online and pay at your own pace, whether you&apos;re
            building here or from abroad.
          </p>
          <div className="mt-10 flex flex-wrap gap-4 justify-center">
            <Link
              href="/lots"
              className="rounded-full bg-marigold text-ink px-6 py-3 font-semibold hover:opacity-90 transition"
            >
              Browse available lots
            </Link>
            <button
              onClick={() => openAuthModal("login")}
              className="rounded-full border border-sand/40 px-6 py-3 font-medium hover:bg-cream/5 transition"
            >
              Client portal login
            </button>
          </div>
        </div>

        {/* Mountain horizon — the dominant visual close, not a footnote */}
        <div className="relative h-[28vh] sm:h-[34vh] min-h-[180px]">
          <SierraMadreMotif className="absolute inset-0 w-full h-full block" />
          {/* Lot availability grid, tucked into the valley floor as a supporting
              detail — ambient motion, not competing with the headline for attention */}
          <div className="absolute bottom-4 right-4 sm:bottom-6 sm:right-8 scale-[0.55] sm:scale-75 origin-bottom-right opacity-90">
            <LotGridAnimation />
          </div>
        </div>
      </section>

      {/* About */}
      <section className="bg-ink mx-auto max-w-3xl px-6 py-20 text-center">
        <Reveal>
          <h2 className="font-display text-3xl mb-4 text-cream">A simpler way to buy land</h2>
          <p className="text-sand leading-relaxed">
            {companyName} offers straightforward lot ownership across Cagayan Valley, on your terms.
            Whether you&apos;re ready to pay in full or prefer to spread the cost over time, the
            entire process — from browsing available lots to making your final
            payment — happens online, with nothing lost in translation between
            you and our sales office.
          </p>
        </Reveal>
      </section>

      {/* Community photo */}
      <section className="bg-ink mx-auto max-w-6xl px-6 pb-20">
        <Reveal>
          <div className="relative rounded-2xl overflow-hidden aspect-[16/7] bg-clay">
            {/* /public/images/community-aerial.jpg — see image guide below */}
            <Image
              src="/images/community-aerial.jpg"
              alt={`Aerial view of a ${companyName} subdivision`}
              fill
              className="object-cover"
              sizes="(min-width: 1024px) 1152px, 100vw"
            />
          </div>
        </Reveal>
      </section>

      {/* Offerings */}
      <section id="offerings" className="bg-clay border-y border-clay">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <Reveal>
            <h2 className="font-display text-3xl mb-2 text-center text-cream">What we offer</h2>
            <p className="text-sand text-center mb-14 max-w-xl mx-auto">
              Everything you need to buy and manage your lot, without the paperwork runaround.
            </p>
          </Reveal>
          <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-3">
            {OFFERINGS.map((f, i) => (
              <Reveal key={f.title} delay={i * 80}>
                <h3 className="font-display text-xl mb-2 text-cream">{f.title}</h3>
                <p className="text-sand text-sm leading-relaxed">{f.body}</p>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* Featured lots */}
      {featuredLots && featuredLots.length > 0 && (
        <section className="bg-ink mx-auto max-w-6xl px-6 py-20">
          <Reveal>
            <div className="flex items-center justify-between mb-10">
              <h2 className="font-display text-3xl text-cream">Available now</h2>
              <Link href="/lots" className="text-marigold font-medium hover:underline text-sm">
                View all lots →
              </Link>
            </div>
          </Reveal>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {featuredLots.map((lot, i) => (
              <Reveal key={lot.id} delay={i * 100}>
                <div className="rounded-2xl border border-clay bg-clay overflow-hidden hover:border-marigold/60 transition">
                  <div className="relative aspect-[4/3] bg-clay">
                    {/* /public/images/lot-placeholder.jpg — used as a stand-in until real per-lot photos are uploaded */}
                    <Image
                      src="/images/lot-placeholder.jpg"
                      alt={`Block ${lot.block_number}, Lot ${lot.lot_number}`}
                      fill
                      className="object-cover"
                      sizes="(min-width: 1024px) 33vw, (min-width: 640px) 50vw, 100vw"
                    />
                  </div>
                  <div className="p-6">
                    <p className="font-display text-lg mb-1 text-cream">
                      Block {lot.block_number}, Lot {lot.lot_number}
                    </p>
                    <p className="text-sand text-sm mb-3">{lot.area_sqm} sqm</p>
                    <p className="text-marigold font-semibold text-lg font-data">
                      {currency}{Number(lot.total_price).toLocaleString()}
                    </p>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </section>
      )}

      {/* How it works */}
      <section id="how-it-works" className="bg-clay text-cream">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <Reveal>
            <h2 className="font-display text-3xl mb-14 text-center">How it works</h2>
          </Reveal>
          <div className="grid gap-10 sm:grid-cols-5">
            {STEPS.map((step, i) => (
              <Reveal key={step.title} delay={i * 100}>
                <p className="font-display text-3xl text-marigold mb-3 font-data">{String(i + 1).padStart(2, "0")}</p>
                <h3 className="font-medium mb-2">{step.title}</h3>
                <p className="text-sand text-sm leading-relaxed">{step.body}</p>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* Why choose us */}
      <section className="bg-ink mx-auto max-w-6xl px-6 py-20 grid lg:grid-cols-2 gap-14 items-center">
        <Reveal>
          <div className="relative rounded-2xl overflow-hidden aspect-[4/3] bg-clay">
            {/* /public/images/site-entrance.jpg — see image guide below */}
            <Image
              src="/images/site-entrance.jpg"
              alt={`${companyName} subdivision entrance`}
              fill
              className="object-cover"
              sizes="(min-width: 1024px) 576px, 100vw"
            />
          </div>
        </Reveal>
        <div className="grid grid-cols-2 gap-10">
          {[
            { label: "Prime location", body: "Well-situated lots across Cagayan Valley." },
            { label: "Transparent terms", body: "Fixed schedules, no hidden fees." },
            { label: "Secure payments", body: "PayPal & trusted local e-wallets." },
            { label: "Real-time availability", body: "Live inventory, always up to date." },
          ].map((item, i) => (
            <Reveal key={item.label} delay={i * 80}>
              <p className="font-display text-lg mb-1 text-cream">{item.label}</p>
              <p className="text-sand text-sm">{item.body}</p>
            </Reveal>
          ))}
        </div>
      </section>

      {/* Final CTA */}
      <section className="relative">
        <div className="relative py-28 overflow-hidden">
          {/* /public/images/cta-background.jpg — see image guide below */}
          <Image
            src="/images/cta-background.jpg"
            alt=""
            fill
            className="object-cover"
            sizes="100vw"
          />
          <div className="absolute inset-0 bg-ink/85" />
          <div className="relative mx-auto max-w-3xl px-6 text-center text-cream">
            <Reveal>
              <h2 className="font-display text-3xl mb-4">Ready to find your lot?</h2>
              <p className="text-sand mb-8">
                Browse what&apos;s available today, or create an account if you&apos;ve already reserved a lot with us.
              </p>
              <div className="flex flex-wrap gap-4 justify-center">
                <Link
                  href="/lots"
                  className="rounded-full bg-marigold text-ink px-6 py-3 font-semibold hover:opacity-90 transition"
                >
                  Browse available lots
                </Link>
                <button
                  onClick={() => openAuthModal("register")}
                  className="rounded-full border border-sand/40 px-6 py-3 font-medium hover:bg-cream/5 transition"
                >
                  Create an account
                </button>
              </div>
            </Reveal>
          </div>
        </div>
      </section>
    </>
  );
}