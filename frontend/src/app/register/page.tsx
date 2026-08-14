"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthModalStore } from "@/lib/auth-modal-store";

export default function RegisterPage() {
  const router = useRouter();
  const open = useAuthModalStore((s) => s.open);

  useEffect(() => {
    open("register");
    router.replace("/");
  }, [open, router]);

  return null;
}