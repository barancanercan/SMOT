"use client";

import { cn } from "@/lib/utils";

export type Platform = "twitter" | "instagram" | "both";

interface PlatformSelectorProps {
  value: Platform;
  onChange: (platform: Platform) => void;
  className?: string;
  size?: "sm" | "md" | "lg";
  disabled?: boolean;
}

export function PlatformSelector({
  value,
  onChange,
  className,
  size = "md",
  disabled = false,
}: PlatformSelectorProps) {
  const sizeClasses = {
    sm: "text-xs px-2 py-1",
    md: "text-sm px-3 py-1.5",
    lg: "text-base px-4 py-2",
  };

  const platforms: { value: Platform; label: string; color: string; activeColor: string }[] = [
    {
      value: "twitter",
      label: "X (Twitter)",
      color: "text-gray-400 hover:text-blue-400",
      activeColor: "bg-blue-600 text-white",
    },
    {
      value: "instagram",
      label: "Instagram",
      color: "text-gray-400 hover:text-pink-400",
      activeColor: "bg-gradient-to-r from-purple-500 to-pink-500 text-white",
    },
    {
      value: "both",
      label: "Her Ikisi",
      color: "text-gray-400 hover:text-purple-400",
      activeColor: "bg-gradient-to-r from-blue-600 via-purple-500 to-pink-500 text-white",
    },
  ];

  return (
    <div
      className={cn(
        "inline-flex gap-1 p-1 bg-[#0B0B0B] rounded-xl border border-white/10",
        disabled && "opacity-50 pointer-events-none",
        className
      )}
    >
      {platforms.map((platform) => (
        <button
          key={platform.value}
          onClick={() => onChange(platform.value)}
          disabled={disabled}
          className={cn(
            "rounded-lg font-medium transition-all duration-200",
            sizeClasses[size],
            value === platform.value
              ? platform.activeColor
              : `bg-transparent ${platform.color} hover:bg-white/5`
          )}
        >
          {platform.label}
        </button>
      ))}
    </div>
  );
}

// Compact version for tight spaces
interface PlatformBadgeProps {
  platform: Platform;
  className?: string;
}

export function PlatformBadge({ platform, className }: PlatformBadgeProps) {
  const badges: Record<Platform, { label: string; className: string }> = {
    twitter: {
      label: "X",
      className: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    },
    instagram: {
      label: "IG",
      className: "bg-pink-500/20 text-pink-400 border-pink-500/30",
    },
    both: {
      label: "X+IG",
      className: "bg-purple-500/20 text-purple-400 border-purple-500/30",
    },
  };

  const badge = badges[platform];

  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 text-xs font-medium rounded border",
        badge.className,
        className
      )}
    >
      {badge.label}
    </span>
  );
}

// Icon-only version
interface PlatformIconProps {
  platform: Platform;
  className?: string;
}

export function PlatformIcon({ platform, className }: PlatformIconProps) {
  if (platform === "twitter") {
    return (
      <svg
        viewBox="0 0 24 24"
        className={cn("w-4 h-4 fill-current text-blue-400", className)}
      >
        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
      </svg>
    );
  }

  if (platform === "instagram") {
    return (
      <svg
        viewBox="0 0 24 24"
        className={cn("w-4 h-4 fill-current text-pink-400", className)}
      >
        <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z" />
      </svg>
    );
  }

  // Both platforms
  return (
    <div className={cn("flex items-center gap-0.5", className)}>
      <svg viewBox="0 0 24 24" className="w-3 h-3 fill-current text-blue-400">
        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
      </svg>
      <span className="text-gray-500">+</span>
      <svg viewBox="0 0 24 24" className="w-3 h-3 fill-current text-pink-400">
        <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z" />
      </svg>
    </div>
  );
}
