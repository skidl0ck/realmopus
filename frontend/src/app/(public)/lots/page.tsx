"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { Lot, Project, Reservation } from "@/types";
import { useCurrencySymbol } from "@/lib/currency";
import { useDefaultReservationFee } from "@/lib/site-config";
import { useAuthStore } from "@/lib/auth-store";
import { useAuthModalStore } from "@/lib/auth-modal-store";
import { Blueprint } from "@/components/blueprint";

const STATUS_STYLES: Record<string, string> = {
  available: "tag-accent",
  reserved: "tag-neutral",
  sold: "tag-neutral opacity-60",
  on_hold: "bg-red-100 text-red-800",
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
    return <img src={lot.thumbnail} alt={`Block ${lot.block_number}, Lot ${lot.lot_number}`} className="duotone w-full h-40 object-cover mb-5" />;
  }
  // Themed placeholder - a simple lot/house glyph rather than a generic gray box.
  return (
    <div className="w-full h-40 mb-5 bg-surface flex items-center justify-center border border-divider">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-neutral-400">
        <path d="M3 10.5L12 3l9 7.5" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M5 9.5V20a1 1 0 001 1h4v-6h4v6h4a1 1 0 001-1V9.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
}

export default function LotsPage() {
  const currency = useCurrencySymbol();
  const reservationFee = useDefaultReservationFee();
  const router = useRouter();
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
  const [sort, setSort] = useState("price-asc");
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
    onSuccess: () => {
      // Only reached for the fee=0 case now -- a fee>0 reserve never calls
      // this mutation at all, it goes straight to checkout (see
      // handleReserve below) since no Reservation exists until paid.
      queryClient.invalidateQueries({ queryKey: ["lots"] });
      setFeedback({ type: "success", message: "Reserved! We'll be in touch to arrange your contract." });
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: Record<string, string[] | string> } })?.response?.data;
      const message = detail
        ? Object.values(detail).flat().join(" ")
        : "Couldn't reserve this lot - please try again.";
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

    if (reservationFee !== undefined && reservationFee > 0) {
      // No entry is created until the fee is actually paid -- go straight
      // to a checkout keyed on the lot itself, not on a reservation that
      // doesn't exist yet.
      router.push(`/portal/lots/${lot.id}/checkout`);
      return;
    }
    reserveMutation.mutate(lot.id);
  }

  const totalPages = lotsResponse ? Math.max(1, Math.ceil(lotsResponse.count / PAGE_SIZE)) : 1;
  const sortedLots = [...(lotsResponse?.results ?? [])].sort((a, b) => {
    switch (sort) {
      case "price-desc":
        return Number(b.total_price) - Number(a.total_price);
      case "area-asc":
        return Number(a.area_sqm) - Number(b.area_sqm);
      case "area-desc":
        return Number(b.area_sqm) - Number(a.area_sqm);
      case "lot":
        return Number(a.block_number) - Number(b.block_number) || Number(a.lot_number) - Number(b.lot_number);
      default:
        return Number(a.total_price) - Number(b.total_price);
    }
  });

  return (
    <main className="flex-1 bg-bg mx-auto max-w-6xl px-6 py-16 w-full">
      <h1 className="font-display font-semibold uppercase text-3xl mb-2 text-ink">Available Lots</h1>
      <p className="text-neutral-600 mb-6">
        Browse our current inventory. Reserve a lot to hold your spot while we
        prepare your contract.
      </p>

      {feedback && (
        <p className={`mb-6 text-sm px-4 py-3 border ${
          feedback.type === "success"
            ? "text-green-800 bg-green-50 border-green-200"
            : "text-red-800 bg-red-50 border-red-200"
        }`}>
          {feedback.message}
        </p>
      )}

      {/* Filters */}
      <div className="border border-divider p-5 mb-8">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="lg:col-span-2 field">
            <label>Search</label>
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Block or lot number"
              className="input"
            />
          </div>
          <div className="field">
            <label>Project</label>
            <select
              value={project}
              onChange={(e) => setProject(e.target.value)}
              className="input"
            >
              <option value="">All projects</option>
              {projects?.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Sort by</label>
            <select value={sort} onChange={(e) => setSort(e.target.value)} className="input">
              <option value="price-asc">Price: low to high</option>
              <option value="price-desc">Price: high to low</option>
              <option value="area-asc">Size: small to large</option>
              <option value="area-desc">Size: large to small</option>
              <option value="lot">Block and lot</option>
            </select>
          </div>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
          <div className="field">
            <label>Min price ({currency})</label>
            <input
              type="number" min="0" value={priceMinInput}
              onChange={(e) => setPriceMinInput(e.target.value)}
              className="input"
            />
          </div>
          <div className="field">
            <label>Max price ({currency})</label>
            <input
              type="number" min="0" value={priceMaxInput}
              onChange={(e) => setPriceMaxInput(e.target.value)}
              className="input"
            />
          </div>
          <div className="field">
            <label>Min size (sqm)</label>
            <input
              type="number" min="0" value={areaMinInput}
              onChange={(e) => setAreaMinInput(e.target.value)}
              className="input"
            />
          </div>
          <div className="field">
            <label>Max size (sqm)</label>
            <input
              type="number" min="0" value={areaMaxInput}
              onChange={(e) => setAreaMaxInput(e.target.value)}
              className="input"
            />
          </div>
        </div>
      </div>

      {isLoading && <p className="text-neutral-600">Loading lots…</p>}
      {isError && (
        <p className="text-red-700">
          Couldn&apos;t load lots right now - check that the backend API is running.
        </p>
      )}
      {lotsResponse && lotsResponse.count === 0 && (
        <p className="text-neutral-600">No lots match these filters.</p>
      )}

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {sortedLots.map((lot) => {
          const isAvailable = lot.status === "available";
          const isReservingThis = reserveMutation.isPending && reserveMutation.variables === lot.id;

          return (
            <Blueprint key={lot.id} className="p-5 hover:border-accent transition">
              <LotThumbnail lot={lot} />
              <div className="flex items-center justify-between mb-3">
                <span className="font-display font-semibold uppercase text-lg text-ink">
                  Block {lot.block_number}, Lot {lot.lot_number}
                </span>
                <span className={`tag ${STATUS_STYLES[lot.status]}`}>
                  {lot.status.replace("_", " ")}
                </span>
              </div>
              <p className="text-neutral-600 text-sm mb-1">{lot.area_sqm} sqm</p>
              <p className="text-ink font-semibold text-xl font-data mb-4">
                {currency}{Number(lot.total_price).toLocaleString()}
              </p>

              {isAvailable && (
                <button
                  onClick={() => handleReserve(lot)}
                  disabled={isReservingThis}
                  className="btn btn-primary btn-block w-full"
                >
                  {isReservingThis ? "Reserving…" : "Reserve this lot"}
                </button>
              )}
            </Blueprint>
          );
        })}
      </div>

      {lotsResponse && lotsResponse.count > 0 && (
        <div className="flex items-center justify-center gap-4 mt-10">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={!lotsResponse.previous}
            className="text-sm text-neutral-600 hover:text-accent transition disabled:opacity-30 disabled:hover:text-neutral-600 cursor-pointer"
          >
            ← Previous
          </button>
          <span className="text-sm text-neutral-600">Page {page} of {totalPages}</span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={!lotsResponse.next}
            className="text-sm text-neutral-600 hover:text-accent transition disabled:opacity-30 disabled:hover:text-neutral-600 cursor-pointer"
          >
            Next →
          </button>
        </div>
      )}
    </main>
  );
}