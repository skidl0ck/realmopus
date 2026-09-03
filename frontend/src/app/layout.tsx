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

export const metadata: Metadata = {
  title: "EstateOS | Real Estate Sales & Property Management",
  description: "Browse available lots, manage contracts, and track payments.",
};

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