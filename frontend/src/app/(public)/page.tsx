"use client";

import Image from "next/image";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { Lot } from "@/types";
import { Reveal } from "@/components/reveal";
import { LotGridAnimation } from "@/components/lot-grid-animation";
import { useAuthModalStore } from "@/lib/auth-modal-store";

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

  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-b from-emerald-900 to-emerald-800 text-white">
        <div className="absolute inset-0">
          {/* /public/images/hero-background.jpg — subtle background behind the gradient, keeps the animated grid as the clear foreground focal point */}
          <Image
            src="/images/hero-background.jpg"
            alt=""
            fill
            priority
            className="object-cover opacity-25"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-emerald-900/95 via-emerald-900/90 to-emerald-800/95" />
        </div>

        <div className="relative mx-auto max-w-6xl px-6 py-28 grid lg:grid-cols-2 gap-16 items-center">
          <div>
            <p className="text-emerald-300 font-medium tracking-wide uppercase text-sm">
              Greenview Estates — Pangasinan
            </p>
            <h1 className="mt-4 text-5xl font-serif font-medium leading-tight">
              Own a lot today, pay at your own pace.
            </h1>
            <p className="mt-6 text-emerald-100 max-w-xl text-lg">
              Browse available lots, reserve online, and manage your installment
              payments — all in one place.
            </p>
            <div className="mt-10 flex flex-wrap gap-4">
              <Link
                href="/lots"
                className="rounded-full bg-white text-emerald-900 px-6 py-3 font-medium hover:bg-emerald-50 transition"
              >
                Browse available lots
              </Link>
              <button
                onClick={() => openAuthModal("login")}
                className="rounded-full border border-white/40 px-6 py-3 font-medium hover:bg-white/10 transition"
              >
                Client portal login
              </button>
            </div>
          </div>

          <div className="flex justify-center lg:justify-end">
            <LotGridAnimation />
          </div>
        </div>
      </section>

      {/* About */}
      <section className="mx-auto max-w-3xl px-6 py-20 text-center">
        <Reveal>
          <h2 className="font-serif text-3xl mb-4">A simpler way to buy land</h2>
          <p className="text-stone-600 leading-relaxed">
            Greenview Estates is a residential lot development in Pangasinan
            offering straightforward lot ownership on your terms. Whether you're
            ready to pay in full or prefer to spread the cost over time, the
            entire process — from browsing available lots to making your final
            payment — happens online, with nothing lost in translation between
            you and our sales office.
          </p>
        </Reveal>
      </section>

      {/* Community photo */}
      <section className="mx-auto max-w-6xl px-6 pb-20">
        <Reveal>
          <div className="relative rounded-2xl overflow-hidden aspect-[16/7] bg-stone-200">
            {/* /public/images/community-aerial.jpg — see image guide below */}
            <Image
              src="/images/community-aerial.jpg"
              alt="Aerial view of the Greenview Estates subdivision"
              fill
              className="object-cover"
              sizes="(min-width: 1024px) 1152px, 100vw"
            />
          </div>
        </Reveal>
      </section>

      {/* Offerings */}
      <section id="offerings" className="bg-white border-y border-stone-200">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <Reveal>
            <h2 className="font-serif text-3xl mb-2 text-center">What we offer</h2>
            <p className="text-stone-500 text-center mb-14 max-w-xl mx-auto">
              Everything you need to buy and manage your lot, without the paperwork runaround.
            </p>
          </Reveal>
          <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-3">
            {OFFERINGS.map((f, i) => (
              <Reveal key={f.title} delay={i * 80}>
                <h3 className="font-serif text-xl mb-2">{f.title}</h3>
                <p className="text-stone-600 text-sm leading-relaxed">{f.body}</p>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* Featured lots */}
      {featuredLots && featuredLots.length > 0 && (
        <section className="mx-auto max-w-6xl px-6 py-20">
          <Reveal>
            <div className="flex items-center justify-between mb-10">
              <h2 className="font-serif text-3xl">Available now</h2>
              <Link href="/lots" className="text-emerald-800 font-medium hover:underline text-sm">
                View all lots →
              </Link>
            </div>
          </Reveal>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {featuredLots.map((lot, i) => (
              <Reveal key={lot.id} delay={i * 100}>
                <div className="rounded-2xl border border-stone-200 bg-white overflow-hidden shadow-sm hover:shadow-md transition">
                  <div className="relative aspect-[4/3] bg-stone-200">
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
                    <p className="font-serif text-lg mb-1">
                      Block {lot.block_number}, Lot {lot.lot_number}
                    </p>
                    <p className="text-stone-500 text-sm mb-3">{lot.area_sqm} sqm</p>
                    <p className="text-emerald-800 font-medium text-lg">
                      ₱{Number(lot.total_price).toLocaleString()}
                    </p>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </section>
      )}

      {/* How it works */}
      <section id="how-it-works" className="bg-emerald-900 text-white">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <Reveal>
            <h2 className="font-serif text-3xl mb-14 text-center">How it works</h2>
          </Reveal>
          <div className="grid gap-10 sm:grid-cols-5">
            {STEPS.map((step, i) => (
              <Reveal key={step.title} delay={i * 100}>
                <p className="font-serif text-3xl text-emerald-400 mb-3">{i + 1}</p>
                <h3 className="font-medium mb-2">{step.title}</h3>
                <p className="text-emerald-100 text-sm leading-relaxed">{step.body}</p>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* Why choose us */}
      <section className="mx-auto max-w-6xl px-6 py-20 grid lg:grid-cols-2 gap-14 items-center">
        <Reveal>
          <div className="relative rounded-2xl overflow-hidden aspect-[4/3] bg-stone-200">
            {/* /public/images/site-entrance.jpg — see image guide below */}
            <Image
              src="/images/site-entrance.jpg"
              alt="Greenview Estates subdivision entrance"
              fill
              className="object-cover"
              sizes="(min-width: 1024px) 576px, 100vw"
            />
          </div>
        </Reveal>
        <div className="grid grid-cols-2 gap-10">
          {[
            { label: "Prime location", body: "Well-situated lots across Pangasinan." },
            { label: "Transparent terms", body: "Fixed schedules, no hidden fees." },
            { label: "Secure payments", body: "PayPal & trusted local e-wallets." },
            { label: "Real-time availability", body: "Live inventory, always up to date." },
          ].map((item, i) => (
            <Reveal key={item.label} delay={i * 80}>
              <p className="font-serif text-lg mb-1">{item.label}</p>
              <p className="text-stone-500 text-sm">{item.body}</p>
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
          <div className="absolute inset-0 bg-emerald-950/75" />
          <div className="relative mx-auto max-w-3xl px-6 text-center text-white">
            <Reveal>
              <h2 className="font-serif text-3xl mb-4">Ready to find your lot?</h2>
              <p className="text-emerald-100 mb-8">
                Browse what's available today, or create an account if you've already reserved a lot with us.
              </p>
              <div className="flex flex-wrap gap-4 justify-center">
                <Link
                  href="/lots"
                  className="rounded-full bg-white text-emerald-900 px-6 py-3 font-medium hover:bg-emerald-50 transition"
                >
                  Browse available lots
                </Link>
                <button
                  onClick={() => openAuthModal("register")}
                  className="rounded-full border border-white/40 px-6 py-3 font-medium hover:bg-white/10 transition"
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