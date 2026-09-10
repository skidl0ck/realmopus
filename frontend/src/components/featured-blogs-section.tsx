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
}

async function fetchFeaturedBlogs(): Promise<Blog[]> {
  const { data } = await apiClient.get("/blogs/");
  const all: Blog[] = data.results ?? data;
  return all.filter((b) => b.is_featured);
}

export function FeaturedBlogsSection() {
  const { data: blogs } = useQuery({ queryKey: ["featured-blogs"], queryFn: fetchFeaturedBlogs });

  if (!blogs || blogs.length === 0) return null;

  return (
    <section className="mx-auto max-w-6xl px-6 py-20">
      <Reveal>
        <div className="flex items-baseline justify-between gap-6 mb-10">
          <div>
            <span className="block text-xs tracking-widest uppercase font-semibold text-accent-700 mb-3">06 · From the blog</span>
            <hr className="border-0 h-px bg-divider mb-3" />
            <h2 className="font-display font-semibold uppercase text-3xl text-ink">From the blog</h2>
          </div>
          <Link href="/blogs" className="text-accent-700 font-medium hover:underline text-sm whitespace-nowrap">
            View all posts →
          </Link>
        </div>
      </Reveal>
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {blogs.map((blog, i) => (
          <Reveal key={blog.id} delay={i * 80}>
            <Link href={`/blogs/${blog.slug}`}>
              <Blueprint className="overflow-hidden flex flex-col h-full">
                {blog.thumbnail ? (
                  <div className="relative aspect-[4/3] w-full">
                    <Image src={blog.thumbnail} alt={blog.title} fill className="object-cover" sizes="(min-width: 1024px) 33vw, (min-width: 640px) 50vw, 100vw" />
                  </div>
                ) : (
                  <div className="aspect-[4/3] bg-accent-100 flex items-center justify-center">
                    <span className="font-display font-semibold text-accent-700">{blog.title.charAt(0).toUpperCase()}</span>
                  </div>
                )}
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
  );
}