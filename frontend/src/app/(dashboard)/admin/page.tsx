"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { Project, Lot, Contract } from "@/types";

interface CashFlowSummary {
  total_collections: string;
  total_expenses: string;
  net_cash_flow: string;
}

interface Paginated<T> {
  count: number;
  results: T[];
}

async function fetchProjects(): Promise<Project[]> {
  const { data } = await apiClient.get("/properties/projects/");
  return data.results ?? data;
}

async function fetchLots(): Promise<Lot[]> {
  const { data } = await apiClient.get("/properties/lots/?page_size=500");
  return data.results ?? data;
}

async function fetchContracts(): Promise<Paginated<Contract>> {
  const { data } = await apiClient.get("/sales/contracts/");
  return data;
}

async function fetchCashFlow(): Promise<CashFlowSummary> {
  const { data } = await apiClient.get("/expenses/cash-flow/");
  return data;
}

function peso(value: string | number) {
  return `₱${Number(value).toLocaleString()}`;
}

export default function AdminOverviewPage() {
  const { data: projects } = useQuery({ queryKey: ["admin-projects"], queryFn: fetchProjects });
  const { data: lots } = useQuery({ queryKey: ["admin-lots"], queryFn: fetchLots });
  const { data: contracts } = useQuery({ queryKey: ["admin-contracts"], queryFn: fetchContracts });
  const { data: cashFlow } = useQuery({ queryKey: ["admin-cash-flow"], queryFn: fetchCashFlow });

  const lotCounts = {
    available: lots?.filter((l) => l.status === "available").length ?? 0,
    reserved: lots?.filter((l) => l.status === "reserved").length ?? 0,
    sold: lots?.filter((l) => l.status === "sold").length ?? 0,
    on_hold: lots?.filter((l) => l.status === "on_hold").length ?? 0,
  };

  const contractCounts = {
    active: contracts?.results.filter((c) => c.status === "active").length ?? 0,
    completed: contracts?.results.filter((c) => c.status === "completed").length ?? 0,
  };

  return (
    <div>
      <h1 className="font-serif text-2xl mb-1">Overview</h1>
      <p className="text-stone-500 text-sm mb-8">
        A snapshot of inventory, sales, and cash flow across all projects.
      </p>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        <StatCard label="Projects" value={projects?.length ?? "—"} />
        <StatCard label="Total lots" value={lots?.length ?? "—"} />
        <StatCard label="Active contracts" value={contractCounts.active} />
        <StatCard label="Completed contracts" value={contractCounts.completed} />
      </div>

      <div className="grid sm:grid-cols-2 gap-6 mb-8">
        <div className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
          <h2 className="font-serif text-lg mb-4">Lot inventory</h2>
          <div className="space-y-2 text-sm">
            <LotRow label="Available" value={lotCounts.available} color="bg-emerald-500" />
            <LotRow label="Reserved" value={lotCounts.reserved} color="bg-amber-500" />
            <LotRow label="Sold" value={lotCounts.sold} color="bg-stone-400" />
            <LotRow label="On hold" value={lotCounts.on_hold} color="bg-red-500" />
          </div>
          <Link
            href="/admin/lots"
            className="mt-4 inline-block text-sm text-emerald-800 font-medium hover:underline"
          >
            Manage lots →
          </Link>
        </div>

        <div className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
          <h2 className="font-serif text-lg mb-4">Cash flow</h2>
          {cashFlow ? (
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-stone-500">Total collections</span>
                <span className="font-medium text-emerald-700">
                  {peso(cashFlow.total_collections)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-stone-500">Total expenses</span>
                <span className="font-medium text-red-600">{peso(cashFlow.total_expenses)}</span>
              </div>
              <div className="flex justify-between border-t border-stone-100 pt-3">
                <span className="text-stone-700 font-medium">Net</span>
                <span className="font-serif text-lg">{peso(cashFlow.net_cash_flow)}</span>
              </div>
            </div>
          ) : (
            <p className="text-stone-400 text-sm">Loading…</p>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-xl border border-stone-200 bg-white px-4 py-4 shadow-sm">
      <p className="text-2xl font-serif">{value}</p>
      <p className="text-sm text-stone-500">{label}</p>
    </div>
  );
}

function LotRow({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="flex items-center gap-2 text-stone-600">
        <span className={`w-2 h-2 rounded-full ${color}`} />
        {label}
      </span>
      <span className="font-medium">{value}</span>
    </div>
  );
}