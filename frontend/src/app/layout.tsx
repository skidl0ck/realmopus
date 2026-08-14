import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "@/lib/providers";
import { AuthModal } from "@/components/auth-modal";

export const metadata: Metadata = {
  title: "EstateOS | Real Estate Sales & Property Management",
  description: "Browse available lots, manage contracts, and track payments.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-stone-50 text-stone-900 font-sans">
        <Providers>
          {children}
          <AuthModal />
        </Providers>
      </body>
    </html>
  );
}