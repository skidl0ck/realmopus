"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { Receipt } from "@/types";

async function fetchMyReceipts(): Promise<Receipt[]> {
  const { data } = await apiClient.get("/payments/receipts/");
  return data.results ?? data;
}

export default function ReceiptsPage() {
  const { data: receipts, isLoading } = useQuery({
    queryKey: ["my-receipts"],
    queryFn: fetchMyReceipts,
  });

  return (
    <div>
      <h1 className="font-display text-2xl mb-1 text-cream">Receipts</h1>
      <p className="text-sand text-sm mb-8">Official receipts for each completed payment.</p>

      {isLoading && <p className="text-sand">Loading…</p>}
      {receipts?.length === 0 && <p className="text-sand">No receipts yet.</p>}

      <div className="space-y-3">
        {receipts?.map((receipt) => (
          <div
            key={receipt.id}
            className="rounded-xl border border-clay bg-clay px-5 py-4 flex items-center justify-between"
          >
            <div>
              <p className="font-medium text-cream">{receipt.receipt_number}</p>
              <p className="text-sand/70 text-sm">
                Issued {new Date(receipt.issued_at).toLocaleDateString()}
              </p>
            </div>
            {receipt.pdf_file ? (
              <a
                href={receipt.pdf_file}
                className="text-sm text-marigold font-medium hover:underline"
              >
                Download PDF
              </a>
            ) : (
              <span className="text-sm text-sand/70">PDF pending</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}