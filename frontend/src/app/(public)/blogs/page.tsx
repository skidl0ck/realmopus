"use client";

import Link from "next/link";
import Image from "next/image";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { Reveal } from "@/components/reveal";
import { Blueprint } from "@/components/blueprint";

interface Blog {
  id: string;
  title: string;
  slug: string;
  summary: string;
  thumbnail: string | null;
  is_featured: boolean;
  published_at: string;
}

async function fetchBlogs(): Promise<Blog[]> {
  const { data } = await apiClient.get("/blogs/");
  return data.results ?? data;
}

function ThumbnailOrPlaceholder({ blog, aspect }: { blog: Blog; aspect: string }) {
  if (blog.thumbnail) {
    return (
      <div className={`relative w-full ${aspect}`}>
        <Image src={blog.thumbnail} alt={blog.title} fill className="object-cover" sizes="(min-width: 1024px) 33vw, (min-width: 640px) 50vw, 100vw" />
      </div>
    );
  }
  return <div className={`w-full ${aspect} bg-accent-100 flex items-center justify-center`}>
    <span className="font-display font-semibold text-accent-700 text-sm">{blog.title.charAt(0).toUpperCase()}</span>
  </div>;
}

export default function BlogsPage() {
  const { data: blogs } = useQuery({ queryKey: ["blogs"], queryFn: fetchBlogs });

  const featured = (blogs ?? []).filter((b) => b.is_featured);
  const rest = (blogs ?? []).filter((b) => !b.is_featured);

  return (
    <div className="mx-auto max-w-6xl px-6 py-16">
      <h1 className="font-display font-semibold text-3xl uppercase text-ink mb-2">Blog</h1>
      <p className="text-neutral-600 mb-12">News, guides, and updates.</p>

      {featured.length > 0 && (
        <section className="mb-16">
          <p className="text-xs uppercase tracking-wide text-neutral-500 font-semibold mb-4">Featured</p>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {featured.map((blog, i) => (
              <Reveal key={blog.id} delay={i * 80}>
                <Link href={`/blogs/${blog.slug}`}>
                  <Blueprint className="overflow-hidden flex flex-col h-full">
                    <ThumbnailOrPlaceholder blog={blog} aspect="aspect-[4/3]" />
                    <div className="p-5">
                      <p className="font-display font-semibold uppercase text-ink mb-1">{blog.title}</p>
                      <p className="text-sm text-neutral-600 line-clamp-2">{blog.summary}</p>
                    </div>
                  </Blueprint>
                </Link>
              </Reveal>
            ))}
          </div>
        </section>
      )}

      <section className="space-y-10">
        {rest.map((blog, i) => (
          <Reveal key={blog.id} delay={i * 60}>
            <Link href={`/blogs/${blog.slug}`} className="block">
              <div className={`grid sm:grid-cols-2 gap-8 items-center ${i % 2 === 1 ? "sm:[direction:rtl]" : ""}`}>
                <div className="sm:[direction:ltr]">
                  <ThumbnailOrPlaceholder blog={blog} aspect="aspect-[16/10]" />
                </div>
                <div className="sm:[direction:ltr]">
                  <p className="text-xs text-neutral-500 mb-2">
                    {new Date(blog.published_at).toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" })}
                  </p>
                  <p className="font-display font-semibold uppercase text-2xl text-ink mb-3">{blog.title}</p>
                  <p className="text-neutral-600">{blog.summary}</p>
                </div>
              </div>
            </Link>
          </Reveal>
        ))}
        {blogs && blogs.length === 0 && (
          <p className="text-neutral-500 text-center py-12">No posts yet — check back soon.</p>
        )}
      </section>
    </div>
  );
}