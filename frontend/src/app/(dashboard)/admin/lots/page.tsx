"use client";

import { useRef, useState } from "react";
import { apiClient } from "@/lib/api-client";

interface CreatedRow {
  row: number;
  lot: string;
}

interface ErrorRow {
  row: number;
  errors: unknown;
}

interface UploadResult {
  created_count: number;
  error_count: number;
  created: CreatedRow[];
  errors: ErrorRow[];
}

const CSV_TEMPLATE =
  "project,block_number,lot_number,area_sqm,price_per_sqm,total_price,status\n" +
  "greenview-estates,1,01,150,5000,,available\n" +
  "greenview-estates,1,02,180,5000,,available\n";

function formatErrors(errors: unknown): string {
  if (typeof errors === "string") return errors;
  if (Array.isArray(errors)) return errors.join(" ");
  if (errors && typeof errors === "object") {
    return Object.entries(errors as Record<string, unknown>)
      .map(([field, msgs]) => `${field}: ${Array.isArray(msgs) ? msgs.join(" ") : String(msgs)}`)
      .join(" · ");
  }
  return String(errors);
}

function downloadTemplate() {
  const blob = new Blob([CSV_TEMPLATE], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "lots-template.csv";
  a.click();
  URL.revokeObjectURL(url);
}

export default function LotsUploadPage() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleUpload() {
    const file = fileInputRef.current?.files?.[0];
    if (!file) {
      setError("Choose a CSV file first.");
      return;
    }
    setUploading(true);
    setError(null);
    setResult(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const { data } = await apiClient.post<UploadResult>("/properties/lots/bulk_upload/", formData);
      setResult(data);
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Upload failed. Check the file and try again.";
      setError(detail);
    } finally {
      setUploading(false);
    }
  }

  return (
    <div>
      <h1 className="font-serif text-2xl mb-1">Projects &amp; Lots</h1>
      <p className="text-stone-500 text-sm mb-8">
        Bulk-add lots to inventory by uploading a CSV.
      </p>

      <div className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm max-w-2xl">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-serif text-lg">Upload lot CSV</h2>
          <button
            onClick={downloadTemplate}
            className="text-sm text-emerald-800 font-medium hover:underline"
          >
            Download template
          </button>
        </div>

        <p className="text-stone-500 text-sm mb-4">
          Required columns: <code className="text-xs bg-stone-100 px-1 py-0.5 rounded">project</code>{" "}
          (slug or ID), <code className="text-xs bg-stone-100 px-1 py-0.5 rounded">block_number</code>,{" "}
          <code className="text-xs bg-stone-100 px-1 py-0.5 rounded">lot_number</code>,{" "}
          <code className="text-xs bg-stone-100 px-1 py-0.5 rounded">area_sqm</code>,{" "}
          <code className="text-xs bg-stone-100 px-1 py-0.5 rounded">price_per_sqm</code>. Optional:{" "}
          <code className="text-xs bg-stone-100 px-1 py-0.5 rounded">total_price</code>,{" "}
          <code className="text-xs bg-stone-100 px-1 py-0.5 rounded">status</code>.
        </p>

        <div className="flex items-center gap-3 mb-4">
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={(e) => setFileName(e.target.files?.[0]?.name ?? null)}
            className="hidden"
            id="csv-file-input"
          />
          <label
            htmlFor="csv-file-input"
            className="rounded-lg border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 hover:bg-stone-50 cursor-pointer"
          >
            Choose file
          </label>
          <span className="text-sm text-stone-500">{fileName ?? "No file chosen"}</span>
        </div>

        {error && (
          <p className="mb-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
            {error}
          </p>
        )}

        <button
          onClick={handleUpload}
          disabled={uploading}
          className="rounded-full bg-emerald-800 text-white px-6 py-2.5 text-sm font-medium hover:bg-emerald-900 transition disabled:opacity-50"
        >
          {uploading ? "Uploading…" : "Upload"}
        </button>
      </div>

      {result && (
        <div className="mt-8 max-w-2xl space-y-6">
          <div className="flex gap-4">
            <div className="flex-1 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3">
              <p className="text-2xl font-serif text-emerald-800">{result.created_count}</p>
              <p className="text-sm text-emerald-700">Lots created</p>
            </div>
            <div className="flex-1 rounded-xl border border-red-200 bg-red-50 px-4 py-3">
              <p className="text-2xl font-serif text-red-700">{result.error_count}</p>
              <p className="text-sm text-red-600">Rows skipped</p>
            </div>
          </div>

          {result.created.length > 0 && (
            <div className="rounded-2xl border border-stone-200 bg-white overflow-hidden shadow-sm">
              <table className="w-full text-sm">
                <thead className="bg-stone-50 text-stone-500 text-left">
                  <tr>
                    <th className="px-4 py-2 font-medium">Row</th>
                    <th className="px-4 py-2 font-medium">Lot created</th>
                  </tr>
                </thead>
                <tbody>
                  {result.created.map((row) => (
                    <tr key={row.row} className="border-t border-stone-100">
                      <td className="px-4 py-2">{row.row}</td>
                      <td className="px-4 py-2">{row.lot}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {result.errors.length > 0 && (
            <div className="rounded-2xl border border-red-200 bg-white overflow-hidden shadow-sm">
              <table className="w-full text-sm">
                <thead className="bg-red-50 text-red-700 text-left">
                  <tr>
                    <th className="px-4 py-2 font-medium">Row</th>
                    <th className="px-4 py-2 font-medium">Error</th>
                  </tr>
                </thead>
                <tbody>
                  {result.errors.map((row) => (
                    <tr key={row.row} className="border-t border-red-100">
                      <td className="px-4 py-2">{row.row}</td>
                      <td className="px-4 py-2 text-red-700">{formatErrors(row.errors)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}