import type { Metadata } from "next";
import { Fraunces, Work_Sans, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/lib/providers";
import { AuthModal } from "@/components/auth-modal";

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
  display: "swap",
  axes: ["opsz", "SOFT", "WONK"],
});

const workSans = Work_Sans({
  subsets: ["latin"],
  variable: "--font-worksans",
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-plexmono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "EstateOS | Real Estate Sales & Property Management",
  description: "Browse available lots, manage contracts, and track payments.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`h-full antialiased ${fraunces.variable} ${workSans.variable} ${plexMono.variable}`}>
      <body className="min-h-full flex flex-col bg-ink text-cream font-body">
        <Providers>
          {children}
          <AuthModal />
        </Providers>
      </body>
    </html>
  );
}