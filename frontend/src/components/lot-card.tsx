"use client";

import Image from "next/image";
import Link from "next/link";
import { Blueprint } from "@/components/blueprint";
import type { Lot } from "@/types";

const STATUS_STYLES: Record<string, string> = {
  available: "tag-accent",
  reserved: "tag-neutral",
  sold: "tag-neutral opacity-60",
  on_hold: "bg-red-100 text-red-800",
};

function LotThumbnail({ lot }: { lot: Lot }) {
  if (lot.thumbnail) {
    return (
      <div className="relative aspect-[4/3] w-full mb-5">
        <Image
          src={lot.thumbnail}
          alt={`Block ${lot.block_number}, Lot ${lot.lot_number}`}
          fill
          className="object-cover"
          sizes="(min-width: 1024px) 33vw, (min-width: 640px) 50vw, 100vw"
        />
      </div>
    );
  }
  // Themed placeholder -- a simple lot/house glyph rather than a generic
  // gray box or (as the homepage previously did) a hardcoded stock photo
  // that had nothing to do with the actual lot.
  return (
    <div className="w-full aspect-[4/3] mb-5 bg-surface flex items-center justify-center border border-divider">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-neutral-400">
        <path d="M3 10.5L12 3l9 7.5" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M5 9.5V20a1 1 0 001 1h4v-6h4v6h4a1 1 0 001-1V9.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
}

interface LotCardProps {
  lot: Lot;
  currency: string;
  /** Omit entirely to render a plain browse-only card (e.g. the homepage's
   * featured section) -- pass it to show a "Reserve this lot" button below
   * the card content (e.g. the full lots listing page). */
  onReserve?: (lot: Lot) => void;
  reserving?: boolean;
}

export function LotCard({ lot, currency, onReserve, reserving }: LotCardProps) {
  const isAvailable = lot.status === "available";

  return (
    <Blueprint className="p-5 flex flex-col h-full">
      <Link href={`/lots/${lot.id}`} className="flex-1">
        <LotThumbnail lot={lot} />
        <div className="mb-3">
          <div className="flex items-center justify-between">
            <span className="font-display font-semibold uppercase text-lg text-ink">
              Block {lot.block_number}, Lot {lot.lot_number}
            </span>
            <div className="flex items-center gap-2">
              <span className={`tag ${STATUS_STYLES[lot.status]}`}>
                {lot.status.replace("_", " ")}
              </span>
            </div>
          </div>
          <span className="pill text-xs text-neutral-600 mt-1 inline-block uppercase tracking-wide font-semibold">
            {lot.project_name}
          </span>
        </div>
        <p className="text-neutral-600 text-sm mb-1">{lot.area_sqm} sqm</p>
        <p className="text-ink font-semibold text-xl font-data mb-4">
          {currency}{Number(lot.total_price).toLocaleString()}
        </p>
      </Link>

      {onReserve && isAvailable && (
        <button
          onClick={() => onReserve(lot)}
          disabled={reserving}
          className="btn btn-primary btn-block w-full"
        >
          {reserving ? "Reserving…" : "Reserve this lot"}
        </button>
      )}
    </Blueprint>
  );
}