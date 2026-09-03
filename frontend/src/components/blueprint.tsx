import type { ReactNode, ElementType } from "react";

interface BlueprintProps {
  children: ReactNode;
  className?: string;
  as?: ElementType;
}

/**
 * Wraps content in the Industry design system's signature frame — a
 * hairline border with four "+" registration marks at the corners.
 * Square, transparent, never rounded or filled. Used for cards, figures,
 * and other framed content throughout the site.
 */
export function Blueprint({ children, className = "", as: Tag = "div" }: BlueprintProps) {
  return (
    <Tag className={`blueprint ${className}`}>
      <i className="corner tl" />
      <i className="corner tr" />
      <i className="corner bl" />
      <i className="corner br" />
      {children}
    </Tag>
  );
}