"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { Reveal } from "@/components/reveal";
import { Blueprint } from "@/components/blueprint";

interface Testimonial {
  id: string;
  name: string;
  role: string;
  quote: string;
  photo: string | null;
}

async function fetchTestimonials(): Promise<Testimonial[]> {
  const { data } = await apiClient.get("/testimonials/");
  return data.results ?? data;
}

export function TestimonialsSection() {
  const [visibleCount, setVisibleCount] = useState(3);
  const { data: testimonials } = useQuery({
    queryKey: ["testimonials"],
    queryFn: fetchTestimonials,
  });

  // No real testimonials yet (or the request failed) -- render nothing rather
  // than an empty-looking section or placeholder content. This section only
  // ever shows genuine customer quotes, added by staff through the admin
  // panel, never invented copy standing in for real ones.
  if (!testimonials || testimonials.length === 0) return null;

  return (
    <section className="mx-auto max-w-6xl px-6 py-20">
      <Reveal>
        <span className="block text-xs tracking-widest uppercase font-semibold text-accent-700 mb-3">07 · What buyers say</span>
        <hr className="border-0 h-px bg-divider mb-9" />
        <h2 className="font-display font-semibold uppercase text-3xl mb-2 text-ink">What buyers say</h2>
        <p className="text-neutral-600 mb-14 max-w-xl">
          Real feedback from people who&apos;ve bought and reserved lots with us.
        </p>
      </Reveal>
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {testimonials.slice(0, visibleCount).map((t, i) => (
          <Reveal key={t.id} delay={i * 80}>
            <Blueprint className="p-6 h-full flex flex-col">
              <p className="text-neutral-700 leading-relaxed text-sm flex-1 mb-4">&ldquo;{t.quote}&rdquo;</p>
              <div className="flex items-center gap-3">
                {t.photo ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={t.photo} alt="" className="w-10 h-10 rounded-full object-cover" />
                ) : (
                  <div className="w-10 h-10 rounded-full bg-accent-100 flex items-center justify-center font-display font-semibold text-accent-700">
                    {t.name.charAt(0).toUpperCase()}
                  </div>
                )}
                <div>
                  <p className="font-medium text-ink text-sm">{t.name}</p>
                  {t.role && <p className="text-xs text-neutral-500">{t.role}</p>}
                </div>
              </div>
            </Blueprint>
          </Reveal>
        ))}
      </div>
      {visibleCount < testimonials.length && (
        <div className="mt-8 flex justify-center">
          <button
            type="button"
            onClick={() => setVisibleCount((count) => count + 3)}
            className="border border-accent-700 px-5 py-2 text-sm font-semibold uppercase tracking-wide text-accent-700 transition-colors hover:bg-accent-700 hover:text-white cursor-pointer"
          >
            Show more
          </button>
        </div>
      )}
    </section>
  );
}