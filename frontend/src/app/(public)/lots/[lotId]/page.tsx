"use client";

import { useState } from "react";
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

  const { data: lot, isLoading } = useQuery({
    queryKey: ["lot", lotId],
    queryFn: () => fetchLot(lotId),
  });

  const reserveMutation = useMutation({
    mutationFn: (id: string) => apiClient.post("/properties/reservations/", { lot: id }),
    onSuccess: () => {
      setFeedback({ type: "success", message: "Lot reserved — check My Reservations for next steps." });
      queryClient.invalidateQueries({ queryKey: ["lot", lotId] });
    },
    onError: () => setFeedback({ type: "error", message: "Couldn't reserve this lot — it may no longer be available." }),
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
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={images[activeImage].image} alt={`Block ${lot.block_number}, Lot ${lot.lot_number}`} className="w-full h-full object-cover" />
          </Blueprint>
          {images.length > 1 && (
            <div className="flex gap-2 mb-12">
              {images.map((img, i) => (
                <button
                  key={img.id}
                  onClick={() => setActiveImage(i)}
                  className={`w-20 h-20 overflow-hidden border-2 ${i === activeImage ? "border-accent" : "border-transparent"}`}
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={img.image} alt="" className="w-full h-full object-cover" />
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

      <div className="grid sm:grid-cols-3 gap-8 py-12">
        <div className="sm:col-span-2">
          {lot.description && (
            <div className="mb-6">
              <p className="text-xs uppercase tracking-wide text-neutral-500 mb-1">Description</p>
              <p className="text-neutral-700 leading-relaxed whitespace-pre-line">{lot.description}</p>
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
          <p className="text-ink font-semibold text-3xl font-data mb-4">
            {currency}{Number(lot.total_price).toLocaleString()}
          </p>

          {feedback && (
            <p className={`text-sm px-3 py-2 mb-4 border ${feedback.type === "error" ? "bg-red-50 text-red-800 border-red-200" : "bg-green-50 text-green-800 border-green-200"}`}>
              {feedback.message}
            </p>
          )}

          {isAvailable && (
            <button
              onClick={handleReserve}
              disabled={reserveMutation.isPending}
              className="btn btn-primary btn-block w-full"
            >
              {reserveMutation.isPending ? "Reserving…" : "Reserve this lot"}
            </button>
          )}
        </div>
      </div>
      
      <section id="contact" className="bg-surface border-y border-divider">
        <div className="mx-auto max-w-4xl px-6 py-20 grid gap-10 sm:grid-cols-2">
          <Reveal>
            <h2 className="font-display font-semibold uppercase text-3xl mb-2 text-ink">Have a question?</h2>
            <p className="text-neutral-600 max-w-xs">
              Send us a message and we&apos;ll get back to you — no need to wait for office hours.
            </p>
          </Reveal>
          <Reveal delay={80}>
            <InquiryForm source="lot/{lotId}" />
          </Reveal>
        </div>
      </section>
    </div>
  );
}