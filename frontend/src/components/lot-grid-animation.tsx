"use client";

import { useEffect, useRef, useState } from "react";

// A stylized, illustrative subdivision map — not a literal live per-cell feed
// (the public API only ever exposes available lots, never reserved/sold ones,
// so exact real-time status per cell isn't something the public site can show).
// The initial layout is a deterministic decorative pattern; after mount, cells
// occasionally shift status (available → reserved → sold → available) purely
// as ambient motion to suggest an active, moving market — not real sales data.

const COLS = 8;
const ROWS = 5;
const CELL_COUNT = COLS * ROWS;
const TICK_MS = 2400;

type Status = "available" | "reserved" | "sold";

function seededRandom(i: number) {
  const x = Math.sin(i * 12.9898) * 43758.5453;
  return x - Math.floor(x);
}

function statusFor(i: number): Status {
  const r = seededRandom(i);
  if (r < 0.62) return "available";
  if (r < 0.82) return "reserved";
  return "sold";
}

function nextStatus(current: Status): Status {
  if (current === "available") return "reserved";
  if (current === "reserved") return Math.random() < 0.7 ? "sold" : "available";
  return "available"; // sold recycles back, simulating turnover/new releases
}

const STATUS_STYLES: Record<Status, string> = {
  available: "bg-sage",
  reserved: "bg-marigold/70",
  sold: "bg-cream/20",
};

export function LotGridAnimation() {
  const [statuses, setStatuses] = useState<Status[]>(() =>
    Array.from({ length: CELL_COUNT }, (_, i) => statusFor(i))
  );
  const [flashIndex, setFlashIndex] = useState<number | null>(null);
  const flashTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const interval = setInterval(() => {
      const index = Math.floor(Math.random() * CELL_COUNT);
      setStatuses((prev) => {
        const updated = [...prev];
        updated[index] = nextStatus(prev[index]);
        return updated;
      });
      setFlashIndex(index);
      if (flashTimeout.current) clearTimeout(flashTimeout.current);
      flashTimeout.current = setTimeout(() => setFlashIndex(null), 700);
    }, TICK_MS);

    return () => {
      clearInterval(interval);
      if (flashTimeout.current) clearTimeout(flashTimeout.current);
    };
  }, []);

  return (
    <div className="w-full max-w-sm">
      <div className="flex flex-col gap-1.5">
        {Array.from({ length: ROWS }, (_, row) => (
          <div key={row} className="flex gap-1.5">
            {statuses.slice(row * COLS, row * COLS + COLS).map((status, colIndex) => {
              const i = row * COLS + colIndex;
              const isPulsing = status === "available" && i % 9 === 0;
              const isFlashing = flashIndex === i;
              return (
                <div
                  key={i}
                  className={`lot-cell flex-1 aspect-square rounded-sm transition-colors duration-700 ease-out ${
                    STATUS_STYLES[status]
                  } ${isPulsing ? "animate-lot-pulse" : ""} ${
                    isFlashing ? "ring-2 ring-white/80 scale-110" : ""
                  }`}
                  style={{ animationDelay: `${i * 35}ms`, transitionProperty: "background-color, transform" }}
                />
              );
            })}
          </div>
        ))}
      </div>

      <div className="flex items-center gap-4 mt-5 text-xs text-sand">
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-sm bg-sage inline-block" /> Available
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-sm bg-marigold/70 inline-block" /> Reserved
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-sm bg-cream/20 inline-block" /> Sold
        </span>
      </div>
    </div>
  );
}