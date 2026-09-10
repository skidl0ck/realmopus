"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { Lot } from "@/types";
import { useCurrencySymbol } from "@/lib/currency";
import { useDefaultReservationFee } from "@/lib/site-config";
import { useAuthStore } from "@/lib/auth-store";
import { useAuthModalStore } from "@/lib/auth-modal-store";
import { Blueprint } from "@/components/blueprint";
import { Reveal } from "@/components/reveal";
import { InquiryForm } from "@/components/inquiry-form";
import { LotCard } from "@/components/lot-card";
import { useSiteConfigQuery } from "@/lib/site-config";

const STATUS_STYLES: Record<string, string> = {
  available: "tag-accent",
  reserved: "tag-neutral",
  sold: "tag-neutral opacity-60",
  on_hold: "bg-red-100 text-red-800",
};

async function fetchLot(lotId: string): Promise<Lot> {
  const { data } = await apiClient.get(`/properties/lots/${lotId}/`);
  return data;
}

async function fetchLots(): Promise<Lot[]> {
  const { data } = await apiClient.get("/properties/lots/");
  return Array.isArray(data) ? data : data.results ?? [];
}

export default function LotDetailPage() {
  const { lotId } = useParams<{ lotId: string }>();
  const router = useRouter();
  const queryClient = useQueryClient();
  const currency = useCurrencySymbol();
  const reservationFee = useDefaultReservationFee();
  const user = useAuthStore((s) => s.user);
  const openAuthModal = useAuthModalStore((s) => s.open);
  const [activeImage, setActiveImage] = useState(0);
  const [feedback, setFeedback] = useState<{ type: "error" | "success"; message: string } | null>(null);
  const { data: siteConfig } = useSiteConfigQuery();

  const { data: lot, isLoading } = useQuery({
    queryKey: ["lot", lotId],
    queryFn: () => fetchLot(lotId),
  });

  const { data: allLots } = useQuery({
    queryKey: ["lots"],
    queryFn: fetchLots,
  });

  const reserveMutation = useMutation({
    mutationFn: (id: string) => apiClient.post("/properties/reservations/", { lot: id }),
    onSuccess: () => {
      setFeedback({ type: "success", message: "Lot reserved - check My Reservations for next steps." });
      queryClient.invalidateQueries({ queryKey: ["lot", lotId] });
    },
    onError: () => setFeedback({ type: "error", message: "Couldn't reserve this lot - it may no longer be available." }),
  });

  function handleReserve() {
    if (!lot) return;
    if (!user) {
      openAuthModal("register", `/lots/${lot.id}`);
      return;
    }
    if (user.role !== "client") {
      setFeedback({ type: "error", message: "Only client accounts can reserve a lot." });
      return;
    }
    setFeedback(null);
    if (reservationFee !== undefined && reservationFee > 0) {
      router.push(`/portal/lots/${lot.id}/checkout`);
      return;
    }
    reserveMutation.mutate(lot.id);
  }

  if (isLoading) return <div className="mx-auto max-w-5xl px-6 py-16" />;
  if (!lot) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-16 text-center">
        <p className="text-neutral-600">This lot couldn&apos;t be found.</p>
      </div>
    );
  }

  const images = lot.images && lot.images.length > 0 ? lot.images : null;
  const isAvailable = lot.status === "available";
  const recommendedLots = (allLots ?? [])
    .filter((candidate) => candidate.id !== lot.id && candidate.status === "available" && candidate.project_name === lot.project_name)
    .slice(0, 3);

  return (
    <div className="mx-auto max-w-5xl px-6 py-16">
      <div className="flex items-center justify-between mb-6">
        <div>
          {lot.project_name && <p className="text-neutral-500 text-sm mb-1">{lot.project_name}</p>}
          <h1 className="font-display font-semibold uppercase text-2xl sm:text-3xl text-ink">
            Block {lot.block_number}, Lot {lot.lot_number}
          </h1>
        </div>
        <span className={`tag ${STATUS_STYLES[lot.status]}`}>{lot.status.replace("_", " ")}</span>
      </div>

      {images ? (
        <>
          <Blueprint className="relative w-full aspect-[16/7] overflow-hidden mb-3">
            <Image src={images[activeImage].image} alt={`Block ${lot.block_number}, Lot ${lot.lot_number}`} fill className="object-cover" sizes="(min-width: 1024px) 1024px, 100vw" />
          </Blueprint>
          {images.length > 1 && (
            <div className="flex gap-2 mb-12">
              {images.map((img, i) => (
                <button
                  key={img.id}
                  onClick={() => setActiveImage(i)}
                  className={`relative w-20 h-20 overflow-hidden border-2 ${i === activeImage ? "border-accent" : "border-transparent"}`}
                >
                  <Image src={img.image} alt="" fill className="object-cover" sizes="80px" />
                </button>
              ))}
            </div>
          )}
        </>
      ) : (
        <Blueprint className="duotone relative w-full aspect-[16/7] flex items-center justify-center mb-12">
          <span className="text-neutral-400 text-sm">No photos yet</span>
        </Blueprint>
      )}

      <div className="grid sm:grid-cols-3 gap-8 mb-20">
        <div className="sm:col-span-2">
          {lot.description && (
            <div className="mb-6">
              <p className="text-xs uppercase tracking-wide text-neutral-500 mb-1">Description</p>
              <p className="text-neutral-700 leading-relaxed whitespace-pre-line">{lot.description}</p>
            </div>
          )}
          {lot.project_location && (
            <div className="mb-6">
              <p className="text-xs uppercase tracking-wide text-neutral-500 mb-1">Location</p>
              <p className="text-neutral-700">{lot.project_location}</p>
            </div>
          )}
          <div className="grid grid-cols-2 gap-4 text-sm max-w-xs">
            <div>
              <p className="text-xs uppercase tracking-wide text-neutral-500 mb-1">Area</p>
              <p className="text-ink font-medium">{lot.area_sqm} sqm</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wide text-neutral-500 mb-1">Price / sqm</p>
              <p className="text-ink font-medium">{currency}{Number(lot.price_per_sqm).toLocaleString()}</p>
            </div>
          </div>
        </div>

        <div>
          <div className="mb-4 border-divider bg-surface px-3 py-2">
            <label>Total Price</label>
            <p className="text-ink font-semibold text-3xl font-data mb-4">
              {currency}{Number(lot.total_price).toLocaleString()}
            </p>
          </div>

          {reservationFee !== undefined && reservationFee > 0 && (
            <>
              <div className="mb-4 rounded-lg border border-divider bg-surface px-3 py-2">
                <p className="text-[10px] uppercase tracking-[0.18em] text-neutral-500">Reservation fee</p>
                <p className="text-ink font-medium mt-1">{currency}{Number(reservationFee).toLocaleString()}</p>
                <p className="text-neutral-500 text-xs mt-1">Reserve this lot for {siteConfig?.reservation_hold_days || 3} days while you complete your payment.</p>
              </div>
            </>
          )}

          {feedback && (
            <p className={`text-sm px-3 py-2 mb-4 border ${feedback.type === "error" ? "bg-red-50 text-red-800 border-red-200" : "bg-green-50 text-green-800 border-green-200"}`}>
              {feedback.message}
            </p>
          )}

          {isAvailable && (
            <>
              <button
                onClick={handleReserve}
                disabled={reserveMutation.isPending}
                className="btn btn-primary btn-block w-full"
              >
                {reserveMutation.isPending ? "Reserving…" : reservationFee !== undefined && reservationFee > 0 ? "Reserve this lot" : "Reserve this lot"}
              </button>
            </>
          )}
        </div>
      </div>

      {recommendedLots.length > 0 && (
        <section className="bg-surface border-y border-divider">
          <div className="mx-auto max-w-6xl px-6 py-20">
            <Reveal>
              <div className="flex items-baseline justify-between gap-6 mb-10">
                <h2 className="font-display font-semibold uppercase text-3xl text-ink">Recommended For You</h2>
                <Link href="/lots" className="text-accent-700 font-medium hover:underline text-sm whitespace-nowrap">
                  View all lots →
                </Link>
              </div>
            </Reveal>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {recommendedLots.map((lot, i) => (
                <Reveal key={lot.id} delay={i * 100}>
                  <LotCard lot={lot} currency={currency} />
                </Reveal>
              ))}
            </div>
          </div>
        </section>
      )}

      
      
      <section id="contact" className="bg-surface border-y border-divider">
        <div className="mx-auto max-w-4xl px-6 py-20 grid gap-10 sm:grid-cols-2">
          <Reveal>
            <h2 className="font-display font-semibold uppercase text-3xl mb-2 text-ink">Have a question?</h2>
            <p className="text-neutral-600 max-w-xs">
              Send us a message and we&apos;ll get back to you - no need to wait for office hours.
            </p>
          </Reveal>
          <Reveal delay={80}>
            <InquiryForm source="lots/{lot.id}" />
          </Reveal>
        </div>
      </section>
    </div>
  );
}