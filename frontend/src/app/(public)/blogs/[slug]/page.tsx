"use client";

import { useParams } from "next/navigation";
import Image from "next/image";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

interface Blog {
  id: string;
  title: string;
  slug: string;
  summary: string;
  content: string;
  thumbnail: string | null;
  video_url: string;
  published_at: string;
}

async function fetchBlog(slug: string): Promise<Blog> {
  const { data } = await apiClient.get(`/blogs/${slug}/`);
  return data;
}

/** Converts a YouTube or Vimeo URL into its embeddable form. Deliberately
 * only recognizes these two known, trusted video platforms and returns
 * null for anything else — never falls back to embedding an arbitrary
 * URL directly, since that would turn a staff-entered field into an
 * unrestricted iframe-injection point. */
function toEmbedUrl(url: string): string | null {
  try {
    const parsed = new URL(url);
    if (parsed.hostname.includes("youtube.com")) {
      const id = parsed.searchParams.get("v");
      return id ? `https://www.youtube.com/embed/${id}` : null;
    }
    if (parsed.hostname === "youtu.be") {
      const id = parsed.pathname.slice(1);
      return id ? `https://www.youtube.com/embed/${id}` : null;
    }
    if (parsed.hostname.includes("vimeo.com")) {
      const id = parsed.pathname.split("/").filter(Boolean)[0];
      return id ? `https://player.vimeo.com/video/${id}` : null;
    }
  } catch {
    return null;
  }
  return null;
}

export default function BlogDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const { data: blog, isLoading, isError } = useQuery({
    queryKey: ["blog", slug],
    queryFn: () => fetchBlog(slug),
  });

  if (isLoading) return <div className="mx-auto max-w-2xl px-6 py-16" />;
  if (isError || !blog) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-16 text-center">
        <p className="text-neutral-600">This post doesn&apos;t exist or hasn&apos;t been published.</p>
      </div>
    );
  }

  const embedUrl = blog.video_url ? toEmbedUrl(blog.video_url) : null;

  return (
    <article className="mx-auto max-w-2xl px-6 py-16">
      <p className="text-xs text-neutral-500 mb-2">
        {new Date(blog.published_at).toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" })}
      </p>
      <h1 className="font-display font-semibold text-3xl uppercase text-ink mb-6">{blog.title}</h1>

      {blog.thumbnail && (
        <div className="relative w-full aspect-[16/9] mb-8">
          <Image src={blog.thumbnail} alt={blog.title} fill className="object-cover" sizes="(min-width: 640px) 672px, 100vw" />
        </div>
      )}

      {embedUrl && (
        <div className="aspect-video mb-8">
          <iframe
            src={embedUrl}
            className="w-full h-full"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div>
      )}

      {/* Content is sanitized server-side (bleach) before ever being stored --
          see backend/admin_panel/forms.py BlogForm.clean_content -- so this
          dangerouslySetInnerHTML is rendering already-cleaned HTML, not raw
          user input. This is a deliberate, documented exception to this
          project's general avoidance of the pattern, not an oversight. */}
      <div
        className="prose-content text-neutral-700 leading-relaxed"
        dangerouslySetInnerHTML={{ __html: blog.content }}
      />
    </article>
  );
}