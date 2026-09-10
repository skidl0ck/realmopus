import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    // Required as of Next.js 16 -- without an explicit allowlist, the
    // default quality value next/image actually requests (75) gets
    // rejected with a 400, since there's no longer an implicit default.
    qualities: [75],
    // Next.js 16 blocks image optimization for any URL resolving to a
    // private/local IP by default (a genuine, separate SSRF-hardening
    // change, not a bug) -- this only ever matters for local development,
    // since that's the only time images come from localhost at all;
    // production images come from S3's real public hostname, which was
    // never going to hit this restriction regardless of this setting.
    dangerouslyAllowLocalIP: true,
    remotePatterns: [
      {
        // Production: S3-backed media (lot photos, blog thumbnails/inline
        // images, testimonial photos). The exact bucket hostname, not a
        // wildcard -- django-storages generates URLs in the bucket.s3.
        // amazonaws.com form (no region in the hostname) for this bucket,
        // confirmed against a real presigned URL from production. A
        // wildcard like *.s3.amazonaws.com would trust every S3 bucket in
        // every AWS account, not just this project's own.
        protocol: "https",
        hostname: "realmopus-media-533354334579-ap-southeast-1-an.s3.amazonaws.com",
      },
      {
        // Local development: Django's own local media serving when
        // AWS_STORAGE_BUCKET_NAME isn't set (see backend/config/settings.py).
        protocol: "http",
        hostname: "localhost",
        port: "8000",
        pathname: "/media/**",
      },
    ],
  },
};

export default nextConfig;