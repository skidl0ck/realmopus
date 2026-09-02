"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { Lot, Project, Reservation } from "@/types";
import { useCurrencySymbol } from "@/lib/currency";
import { useAuthStore } from "@/lib/auth-store";
import { useAuthModalStore } from "@/lib/auth-modal-store";

const STATUS_STYLES: Record<string, string> = {
  available: "bg-sage/20 text-sage",
  reserved: "bg-marigold/20 text-marigold",
  sold: "bg-sand/20 text-sand",
  on_hold: "bg-rust/20 text-rust",
};

const PAGE_SIZE = 20;

interface LotsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Lot[];
}

interface Filters {
  search: string;
  project: string;
  priceMin: string;
  priceMax: string;
  areaMin: string;
  areaMax: string;
  page: number;
}

async function fetchProjects(): Promise<Project[]> {
  const { data } = await apiClient.get("/properties/projects/");
  return data.results ?? data;
}

async function fetchLots(filters: Filters): Promise<LotsResponse> {
  const params: Record<string, string | number> = { page: filters.page };
  if (filters.search) params.search = filters.search;
  if (filters.project) params.project = filters.project;
  if (filters.priceMin) params.price_min = filters.priceMin;
  if (filters.priceMax) params.price_max = filters.priceMax;
  if (filters.areaMin) params.area_min = filters.areaMin;
  if (filters.areaMax) params.area_max = filters.areaMax;
  const { data } = await apiClient.get("/properties/lots/", { params });
  return data;
}

async function reserveLot(lotId: string): Promise<Reservation> {
  const { data } = await apiClient.post("/properties/reservations/mine/", { lot: lotId });
  return data;
}

interface Feedback {
  type: "success" | "error";
  message: string;
}

function LotThumbnail({ lot }: { lot: Lot }) {
  if (lot.thumbnail) {
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={lot.thumbnail} alt={`Block ${lot.block_number}, Lot ${lot.lot_number}`} className="w-full h-40 object-cover rounded-lg mb-4" />;
  }
  // Themed placeholder — a simple lot/house glyph rather than a generic gray box.
  return (
    <div className="w-full h-40 rounded-lg mb-4 bg-ink flex items-center justify-center border border-clay">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-sand/40">
        <path d="M3 10.5L12 3l9 7.5" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M5 9.5V20a1 1 0 001 1h4v-6h4v6h4a1 1 0 001-1V9.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
}

export default function LotsPage() {
  const currency = useCurrencySymbol();
  const queryClient = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const openAuthModal = useAuthModalStore((s) => s.open);
  const [feedback, setFeedback] = useState<Feedback | null>(null);

  // Raw text-input state, debounced into the actual applied filters below --
  // otherwise every keystroke in search/price/area would fire a request.
  const [searchInput, setSearchInput] = useState("");
  const [priceMinInput, setPriceMinInput] = useState("");
  const [priceMaxInput, setPriceMaxInput] = useState("");
  const [areaMinInput, setAreaMinInput] = useState("");
  const [areaMaxInput, setAreaMaxInput] = useState("");
  const [project, setProject] = useState("");
  const [page, setPage] = useState(1);

  const [filters, setFilters] = useState<Filters>({
    search: "", project: "", priceMin: "", priceMax: "", areaMin: "", areaMax: "", page: 1,
  });

  useEffect(() => {
    const timer = setTimeout(() => {
      setFilters({
        search: searchInput, project, priceMin: priceMinInput, priceMax: priceMaxInput,
        areaMin: areaMinInput, areaMax: areaMaxInput, page: 1,
      });
      setPage(1);
    }, 400);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchInput, project, priceMinInput, priceMaxInput, areaMinInput, areaMaxInput]);

  useEffect(() => {
    setFilters((prev) => ({ ...prev, page }));
  }, [page]);

  const { data: projects } = useQuery({ queryKey: ["projects"], queryFn: fetchProjects });
  const { data: lotsResponse, isLoading, isError } = useQuery({
    queryKey: ["lots", filters],
    queryFn: () => fetchLots(filters),
  });

  const reserveMutation = useMutation({
    mutationFn: reserveLot,
    onSuccess: (reservation) => {
      queryClient.invalidateQueries({ queryKey: ["lots"] });
      const message =
        reservation.status === "pending_payment"
          ? `Reserved! A ${currency}${Number(reservation.reservation_fee).toLocaleString()} fee is due by ${reservation.deadline} to confirm it.`
          : "Reserved! We'll be in touch to arrange your contract.";
      setFeedback({ type: "success", message });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: Record<string, string[] | string> } })?.response?.data;
      const message = detail
        ? Object.values(detail).flat().join(" ")
        : "Couldn't reserve this lot — please try again.";
      setFeedback({ type: "error", message });
    },
  });

  function handleReserve(lot: Lot) {
    if (!user) {
      openAuthModal("register", "/lots");
      return;
    }
    if (user.role !== "client") {
      setFeedback({ type: "error", message: "Only client accounts can reserve a lot." });
      return;
    }
    setFeedback(null);
    reserveMutation.mutate(lot.id);
  }

  const totalPages = lotsResponse ? Math.max(1, Math.ceil(lotsResponse.count / PAGE_SIZE)) : 1;

  return (
    <main className="flex-1 bg-ink mx-auto max-w-6xl px-6 py-16 w-full">
      <h1 className="font-display text-3xl mb-2 text-cream">Available Lots</h1>
      <p className="text-sand mb-6">
        Browse our current inventory. Reserve a lot to hold your spot while we
        prepare your contract.
      </p>

      {feedback && (
        <p className={`mb-6 text-sm rounded-lg px-4 py-3 border ${
          feedback.type === "success"
            ? "text-sage bg-sage/10 border-sage/30"
            : "text-rust bg-rust/10 border-rust/30"
        }`}>
          {feedback.message}
        </p>
      )}

      {/* Filters */}
      <div className="rounded-2xl border border-clay bg-clay p-5 mb-8">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="lg:col-span-2">
            <label className="block text-xs font-medium text-sand mb-1">Search</label>
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Block or lot number"
              className="w-full rounded-lg border border-clay bg-ink text-cream px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-marigold"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-sand mb-1">Project</label>
            <select
              value={project}
              onChange={(e) => setProject(e.target.value)}
              className="w-full rounded-lg border border-clay bg-ink text-cream px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-marigold"
            >
              <option value="">All projects</option>
              {projects?.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
          <div>
            <label className="block text-xs font-medium text-sand mb-1">Min price ({currency})</label>
            <input
              type="number" min="0" value={priceMinInput}
              onChange={(e) => setPriceMinInput(e.target.value)}
              className="w-full rounded-lg border border-clay bg-ink text-cream px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-marigold"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-sand mb-1">Max price ({currency})</label>
            <input
              type="number" min="0" value={priceMaxInput}
              onChange={(e) => setPriceMaxInput(e.target.value)}
              className="w-full rounded-lg border border-clay bg-ink text-cream px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-marigold"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-sand mb-1">Min size (sqm)</label>
            <input
              type="number" min="0" value={areaMinInput}
              onChange={(e) => setAreaMinInput(e.target.value)}
              className="w-full rounded-lg border border-clay bg-ink text-cream px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-marigold"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-sand mb-1">Max size (sqm)</label>
            <input
              type="number" min="0" value={areaMaxInput}
              onChange={(e) => setAreaMaxInput(e.target.value)}
              className="w-full rounded-lg border border-clay bg-ink text-cream px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-marigold"
            />
          </div>
        </div>
      </div>

      {isLoading && <p className="text-sand">Loading lots…</p>}
      {isError && (
        <p className="text-rust">
          Couldn&apos;t load lots right now — check that the backend API is running.
        </p>
      )}
      {lotsResponse && lotsResponse.count === 0 && (
        <p className="text-sand">No lots match these filters.</p>
      )}

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {lotsResponse?.results.map((lot) => {
          const isAvailable = lot.status === "available";
          const isReservingThis = reserveMutation.isPending && reserveMutation.variables === lot.id;

          return (
            <div
              key={lot.id}
              className="rounded-2xl border border-clay bg-clay p-6 hover:border-marigold/60 transition"
            >
              <LotThumbnail lot={lot} />
              <div className="flex items-center justify-between mb-3">
                <span className="font-display text-lg text-cream">
                  Block {lot.block_number}, Lot {lot.lot_number}
                </span>
                <span
                  className={`text-xs px-2 py-1 rounded-full font-medium ${STATUS_STYLES[lot.status]}`}
                >
                  {lot.status.replace("_", " ")}
                </span>
              </div>
              <p className="text-sand text-sm mb-1">{lot.area_sqm} sqm</p>
              <p className="text-marigold font-semibold text-lg font-data mb-4">
                {currency}{Number(lot.total_price).toLocaleString()}
              </p>

              {isAvailable && (
                <button
                  onClick={() => handleReserve(lot)}
                  disabled={isReservingThis}
                  className="w-full rounded-full bg-marigold text-ink text-sm font-semibold py-2 hover:opacity-90 transition disabled:opacity-50 cursor-pointer"
                >
                  {isReservingThis ? "Reserving…" : "Reserve this lot"}
                </button>
              )}
            </div>
          );
        })}
      </div>

      {lotsResponse && lotsResponse.count > 0 && (
        <div className="flex items-center justify-center gap-4 mt-10">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={!lotsResponse.previous}
            className="text-sm text-sand hover:text-marigold transition disabled:opacity-30 disabled:hover:text-sand cursor-pointer"
          >
            ← Previous
          </button>
          <span className="text-sm text-sand">Page {page} of {totalPages}</span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={!lotsResponse.next}
            className="text-sm text-sand hover:text-marigold transition disabled:opacity-30 disabled:hover:text-sand cursor-pointer"
          >
            Next →
          </button>
        </div>
      )}
    </main>
  );
}