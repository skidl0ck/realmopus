"use client";

import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthModalStore } from "@/lib/auth-modal-store";

function LoginRedirect() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const open = useAuthModalStore((s) => s.open);

  useEffect(() => {
    open("login", searchParams.get("next") || undefined);
    router.replace("/");
  }, [open, router, searchParams]);

  return null;
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginRedirect />
    </Suspense>
  );
}