import type { Metadata } from "next";
import { Barlow, Barlow_Condensed } from "next/font/google";
import "./globals.css";
import { Providers } from "@/lib/providers";
import { AuthModal } from "@/components/auth-modal";

const barlow = Barlow({
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  variable: "--font-barlow",
  display: "swap",
});

const barlowCondensed = Barlow_Condensed({
  subsets: ["latin"],
  weight: ["400", "600"],
  variable: "--font-barlow-condensed",
  display: "swap",
});

export async function generateMetadata(): Promise<Metadata> {
  // Tenant-aware: the browser tab should show whichever real estate firm is
  // actually running this deployment (PlatformSettings.company_name, set in
  // their own admin panel), not a fixed product name baked in at build time.
  // Falls back to the product's own name if the setting is blank, the
  // backend is unreachable, or this runs at build time with no live API yet.
  const FALLBACK_NAME = "RealmOpus";
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

  let companyName = FALLBACK_NAME;
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 3000);
    const res = await fetch(`${apiUrl}/site-config/`, {
      next: { revalidate: 60 }, // re-checks periodically, not on every single request
      signal: controller.signal,
    });
    clearTimeout(timeout);
    if (res.ok) {
      const data = await res.json();
      companyName = data.company_name?.trim() || FALLBACK_NAME;
    }
  } catch {
    // Backend unreachable, timed out, or this is a build-time prerender with
    // no live API yet -- the fallback above already covers all three.
  }

  return {
    title: `${companyName} | Real Estate Sales & Property Management`,
    description: "Browse available lots, manage contracts, and track payments.",
  };
}

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`h-full antialiased ${barlow.variable} ${barlowCondensed.variable}`}>
      <body className="min-h-full flex flex-col bg-bg text-ink font-body">
        <Providers>
          {children}
          <AuthModal />
        </Providers>
      </body>
    </html>
  );
}