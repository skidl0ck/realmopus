"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { Receipt } from "@/types";

async function fetchMyReceipts(): Promise<Receipt[]> {
  const { data } = await apiClient.get("/payments/receipts/");
  return data.results ?? data;
}

interface ContractGroup {
  contract: string;
  contractNumber: string;
  lotDisplay: string | null;
  receipts: Receipt[];
}

function groupByContract(receipts: Receipt[]): ContractGroup[] {
  const map = new Map<string, ContractGroup>();
  for (const receipt of receipts) {
    const key = receipt.contract ?? "unknown";
    if (!map.has(key)) {
      map.set(key, {
        contract: key,
        contractNumber: receipt.contract_number ?? "Unknown contract",
        lotDisplay: receipt.lot_display,
        receipts: [],
      });
    }
    map.get(key)!.receipts.push(receipt);
  }
  return Array.from(map.values());
}

export default function ReceiptsPage() {
  const { data: receipts, isLoading } = useQuery({
    queryKey: ["my-receipts"],
    queryFn: fetchMyReceipts,
  });
  const [collapsedIds, setCollapsedIds] = useState<Set<string>>(new Set());
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  function toggle(id: string) {
    setCollapsedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  // The zip endpoint requires the same auth as everything else in the portal,
  // so a plain <a href> won't work (browsers don't attach the Bearer token to
  // ordinary link navigation) -- fetch it as a blob through the authenticated
  // client instead, then trigger the download manually.
  async function downloadZip(contractId: string, contractNumber: string) {
    setDownloadError(null);
    setDownloadingId(contractId);
    try {
      const response = await apiClient.get(`/sales/contracts/${contractId}/receipts_zip/`, {
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.download = `${contractNumber}_receipts.zip`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      setDownloadError("Couldn't download receipts for this contract — try again in a moment.");
    } finally {
      setDownloadingId(null);
    }
  }

  const groups = groupByContract(receipts ?? []);

  return (
    <div>
      <h1 className="font-display text-2xl mb-1 text-cream">Receipts</h1>
      <p className="text-sand text-sm mb-8">Official receipts for each completed payment.</p>

      {isLoading && <p className="text-sand">Loading…</p>}
      {!isLoading && groups.length === 0 && <p className="text-sand">No receipts yet.</p>}
      {downloadError && <p className="text-rust text-sm mb-4">{downloadError}</p>}

      <div className="space-y-4">
        {groups.map((group) => {
          const isOpen = !collapsedIds.has(group.contract);
          return (
            <div key={group.contract} className="rounded-2xl border border-clay bg-clay overflow-hidden">
              <div className="w-full flex items-center justify-between gap-3 px-5 py-4">
                <button
                  onClick={() => toggle(group.contract)}
                  className="flex-1 min-w-0 text-left"
                  aria-expanded={isOpen}
                >
                  <p className="font-medium text-cream truncate">
                    {group.contractNumber}
                    {group.lotDisplay && <span className="text-sand font-normal"> — {group.lotDisplay}</span>}
                  </p>
                  <p className="text-sand/70 text-sm">
                    {group.receipts.length} receipt{group.receipts.length !== 1 ? "s" : ""}
                  </p>
                </button>
                <div className="flex items-center gap-3 shrink-0">
                  <button
                    onClick={() => downloadZip(group.contract, group.contractNumber)}
                    disabled={downloadingId === group.contract}
                    className="text-sm text-marigold font-medium hover:underline disabled:opacity-50"
                  >
                    {downloadingId === group.contract ? "Zipping…" : "Download all"}
                  </button>
                  <button onClick={() => toggle(group.contract)} className="text-sand text-lg">
                    {isOpen ? "\u2212" : "+"}
                  </button>
                </div>
              </div>

              {isOpen && (
                <div className="border-t border-ink">
                  {group.receipts.map((receipt) => (
                    <div
                      key={receipt.id}
                      className="px-5 py-3 flex items-center justify-between border-t border-ink first:border-t-0"
                    >
                      <div>
                        <p className="text-cream text-sm">{receipt.receipt_number}</p>
                        <p className="text-sand/70 text-xs">
                          Issued {new Date(receipt.issued_at).toLocaleDateString()}
                        </p>
                      </div>
                      {receipt.pdf_file ? (
                        <a href={receipt.pdf_file} className="text-sm text-marigold font-medium hover:underline">
                          Download PDF
                        </a>
                      ) : (
                        <span className="text-sm text-sand/70">PDF pending</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}