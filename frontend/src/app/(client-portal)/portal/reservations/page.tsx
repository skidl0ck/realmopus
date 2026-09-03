"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { useCurrencySymbol } from "@/lib/currency";
import type { Reservation } from "@/types";

async function fetchMyReservations(): Promise<Reservation[]> {
  const { data } = await apiClient.get("/properties/reservations/mine/");
  return data.results ?? data;
}

const STATUS_STYLES: Record<string, string> = {
  pending_payment: "bg-accent-100 text-accent-800",
  active: "bg-green-100 text-green-800",
  converted: "bg-green-100 text-green-800",
  expired: "bg-neutral-100 text-neutral-600",
  cancelled: "bg-red-100 text-red-800",
};

function daysLeftLabel(deadline: string): { label: string; overdue: boolean } {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const due = new Date(deadline + "T00:00:00");
  const diffDays = Math.round((due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays > 0) return { label: `${diffDays} day${diffDays === 1 ? "" : "s"} left`, overdue: false };
  if (diffDays === 0) return { label: "Due today", overdue: false };
  return { label: `Overdue by ${Math.abs(diffDays)} day${Math.abs(diffDays) === 1 ? "" : "s"}`, overdue: true };
}

export default function ReservationsPage() {
  const currency = useCurrencySymbol();
  const queryClient = useQueryClient();
  const { data: reservations, isLoading } = useQuery({
    queryKey: ["my-reservations"],
    queryFn: fetchMyReservations,
  });

  const [actioningId, setActioningId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<Record<string, string>>({});

  async function handleExtend(id: string) {
    setActioningId(id);
    setActionError((prev) => ({ ...prev, [id]: "" }));
    try {
      await apiClient.post(`/properties/reservations/mine/${id}/extend/`);
      queryClient.invalidateQueries({ queryKey: ["my-reservations"] });
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setActionError((prev) => ({ ...prev, [id]: detail || "Couldn't extend this reservation." }));
    } finally {
      setActioningId(null);
    }
  }

  async function handleDismiss(id: string, isExpired: boolean) {
    if (isExpired && !window.confirm("This will permanently remove this reservation from your history. Continue?")) {
      return;
    }
    setActioningId(id);
    setActionError((prev) => ({ ...prev, [id]: "" }));
    try {
      await apiClient.post(`/properties/reservations/mine/${id}/dismiss/`);
      queryClient.invalidateQueries({ queryKey: ["my-reservations"] });
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setActionError((prev) => ({ ...prev, [id]: detail || "Couldn't dismiss this reservation." }));
    } finally {
      setActioningId(null);
    }
  }

  return (
    <div>
      <h1 className="font-display font-semibold uppercase text-2xl mb-1 text-ink">My Reservations</h1>
      <p className="text-neutral-600 text-sm mb-8">Lots you've reserved, and how much time is left to confirm them.</p>

      {isLoading && <p className="text-neutral-600">Loading…</p>}
      {!isLoading && (!reservations || reservations.length === 0) && (
        <p className="text-neutral-600">No reservations yet - browse available lots to reserve one.</p>
      )}

      <div className="space-y-4 max-w-lg">
        {reservations?.map((reservation) => {
          const isPending = reservation.status === "pending_payment";
          const isExpired = reservation.status === "expired";
          const isActing = actioningId === reservation.id;
          const countdown = isPending ? daysLeftLabel(reservation.deadline) : null;
          const error = actionError[reservation.id];

          return (
            <div key={reservation.id} className="border border-divider p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="font-display font-semibold uppercase text-ink">{reservation.lot_display}</span>
                <span className={`tag ${STATUS_STYLES[reservation.status] ?? "bg-neutral-100 text-neutral-600"}`}>
                  {reservation.status.replace("_", " ")}
                </span>
              </div>

              {isPending && (
                <>
                  <p className="text-neutral-600 text-sm mb-1">
                    {currency}{Number(reservation.reservation_fee).toLocaleString()} reservation fee
                  </p>
                  <p className={`text-sm mb-4 ${countdown?.overdue ? "text-red-700" : "text-neutral-600"}`}>
                    {countdown?.label}
                    {reservation.extension_count > 0 && (
                      <span className="text-neutral-500"> · extended {reservation.extension_count}/{reservation.max_extensions}</span>
                    )}
                  </p>

                  {error && (
                    <p className="mb-3 text-sm text-red-800 bg-red-50 border border-red-200 px-3 py-2">
                      {error}
                    </p>
                  )}

                  <div className="flex flex-wrap gap-3">
                    <Link
                      href={`/portal/reservations/${reservation.id}/checkout`}
                      className="btn btn-primary"
                    >
                      Pay Now
                    </Link>
                    {reservation.can_extend && (
                      <button
                        onClick={() => handleExtend(reservation.id)}
                        disabled={isActing}
                        className="btn btn-secondary"
                      >
                        {isActing ? "…" : "Extend"}
                      </button>
                    )}
                    <button
                      onClick={() => handleDismiss(reservation.id, false)}
                      disabled={isActing}
                      className="btn btn-secondary"
                    >
                      {isActing ? "…" : "Dismiss"}
                    </button>
                  </div>
                </>
              )}

              {isExpired && (
                <>
                  <p className="text-neutral-600 text-sm mb-4">
                    Your fee was paid, but a contract wasn&apos;t signed before the deadline - this lot has been
                    released back to available.
                  </p>

                  {error && (
                    <p className="mb-3 text-sm text-red-800 bg-red-50 border border-red-200 px-3 py-2">
                      {error}
                    </p>
                  )}

                  <button
                    onClick={() => handleDismiss(reservation.id, true)}
                    disabled={isActing}
                    className="btn btn-secondary"
                  >
                    {isActing ? "…" : "Dismiss"}
                  </button>
                </>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}