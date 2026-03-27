"use client";

import { cn } from "@/lib/utils";
import { Heart, MessageCircle, Clock, Video, Image, ExternalLink } from "lucide-react";
import { InstagramPost } from "@/lib/api";

// Party colors - matching the comparison page
const PARTY_COLORS: Record<string, string> = {
  CHP: "#E53935",
  "AK Parti": "#FF9800",
  MHP: "#C62828",
  "IYI Parti": "#1E88E5",
  "DEM Parti": "#7B1FA2",
  BBP: "#D32F2F",
  TIP: "#F44336",
  "Saadet Partisi": "#43A047",
  Bagimsiz: "#78909C",
};

const getPartyColor = (party: string): string => {
  return PARTY_COLORS[party] || "#EC4899"; // Default to pink (Instagram color)
};

const formatNumber = (num: number) => {
  if (num === undefined || num === null) return "0";
  if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
  if (num >= 1000) return (num / 1000).toFixed(1) + "K";
  return num.toLocaleString("tr-TR");
};

interface InstagramCardProps {
  post: InstagramPost;
  showUser?: boolean;
  party?: string;
  name?: string;
  className?: string;
}

export function InstagramCard({
  post,
  showUser = true,
  party,
  name,
  className,
}: InstagramCardProps) {
  return (
    <div
      className={cn(
        "bg-[#0B0B0B] rounded-lg border border-white/5 p-4 hover:border-pink-500/20 transition-all",
        className
      )}
    >
      {showUser && (
        <div className="flex items-center gap-2 mb-2">
          <span className="text-pink-400 font-mono text-sm">@{post.username}</span>
          {party && (
            <span
              className="px-2 py-0.5 text-xs rounded-full"
              style={{
                backgroundColor: getPartyColor(party) + "30",
                color: getPartyColor(party),
              }}
            >
              {party}
            </span>
          )}
          {post.is_video && (
            <span className="flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-purple-500/20 text-purple-400">
              <Video className="w-3 h-3" />
              Video
            </span>
          )}
          {!post.is_video && (
            <span className="flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-pink-500/20 text-pink-400">
              <Image className="w-3 h-3" />
              Foto
            </span>
          )}
        </div>
      )}

      {name && (
        <p className="text-white/60 text-xs mb-2">{name}</p>
      )}

      <p className="text-gray-300 text-sm mb-3 line-clamp-3">
        {post.caption || "(Aciklama yok)"}
      </p>

      <div className="flex items-center justify-between text-xs text-gray-500">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1">
            <Heart className="w-3 h-3 text-red-400" />
            {formatNumber(post.likes)}
          </span>
          <span className="flex items-center gap-1">
            <MessageCircle className="w-3 h-3 text-blue-400" />
            {formatNumber(post.comments)}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {post.post_date?.split("T")[0] || "-"}
          </span>
          {post.post_url && (
            <a
              href={post.post_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-pink-400 hover:text-pink-300 transition-colors"
              title="Instagram'da Ac"
            >
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

// Compact version for lists
interface InstagramCardCompactProps {
  post: InstagramPost;
  rank?: number;
  className?: string;
}

export function InstagramCardCompact({
  post,
  rank,
  className,
}: InstagramCardCompactProps) {
  return (
    <div
      className={cn(
        "flex items-start gap-3 bg-[#0B0B0B] rounded-lg border border-white/5 p-3 hover:border-pink-500/20 transition-all",
        className
      )}
    >
      {rank && (
        <span className="text-lg font-bold text-pink-400/50 w-6">#{rank}</span>
      )}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-pink-400 font-mono text-xs">@{post.username}</span>
          {post.is_video ? (
            <Video className="w-3 h-3 text-purple-400" />
          ) : (
            <Image className="w-3 h-3 text-pink-400" />
          )}
        </div>
        <p className="text-gray-400 text-xs line-clamp-2 mb-1">
          {post.caption || "(Aciklama yok)"}
        </p>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <Heart className="w-3 h-3 text-red-400" />
            {formatNumber(post.likes)}
          </span>
          <span className="flex items-center gap-1">
            <MessageCircle className="w-3 h-3 text-blue-400" />
            {formatNumber(post.comments)}
          </span>
        </div>
      </div>
    </div>
  );
}

// Grid version for dashboard/analytics
interface InstagramPostGridProps {
  posts: InstagramPost[];
  maxPosts?: number;
  className?: string;
}

export function InstagramPostGrid({
  posts,
  maxPosts = 6,
  className,
}: InstagramPostGridProps) {
  const displayPosts = posts.slice(0, maxPosts);

  if (displayPosts.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <Image className="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p>Instagram postu bulunamadi</p>
      </div>
    );
  }

  return (
    <div className={cn("grid grid-cols-1 md:grid-cols-2 gap-3", className)}>
      {displayPosts.map((post, index) => (
        <InstagramCardCompact key={post.id || index} post={post} rank={index + 1} />
      ))}
    </div>
  );
}

// Stats summary card
interface InstagramStatsCardProps {
  totalPosts: number;
  totalLikes: number;
  totalComments: number;
  totalVideos?: number;
  totalPhotos?: number;
  className?: string;
}

export function InstagramStatsCard({
  totalPosts,
  totalLikes,
  totalComments,
  totalVideos = 0,
  totalPhotos = 0,
  className,
}: InstagramStatsCardProps) {
  return (
    <div
      className={cn(
        "bg-gradient-to-br from-pink-500/10 via-purple-500/10 to-pink-500/5 rounded-xl border border-pink-500/20 p-4",
        className
      )}
    >
      <div className="flex items-center gap-2 mb-3">
        <div className="p-2 rounded-lg bg-gradient-to-r from-purple-500 to-pink-500">
          <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current text-white">
            <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z" />
          </svg>
        </div>
        <span className="text-white font-semibold">Instagram Ozeti</span>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <p className="text-xs text-gray-500 mb-1">Toplam Post</p>
          <p className="text-xl font-bold text-white">{formatNumber(totalPosts)}</p>
          <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <Image className="w-3 h-3 text-pink-400" />
              {formatNumber(totalPhotos)}
            </span>
            <span className="flex items-center gap-1">
              <Video className="w-3 h-3 text-purple-400" />
              {formatNumber(totalVideos)}
            </span>
          </div>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1">Toplam Etkilesim</p>
          <p className="text-xl font-bold text-pink-400">
            {formatNumber(totalLikes + totalComments)}
          </p>
          <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <Heart className="w-3 h-3 text-red-400" />
              {formatNumber(totalLikes)}
            </span>
            <span className="flex items-center gap-1">
              <MessageCircle className="w-3 h-3 text-blue-400" />
              {formatNumber(totalComments)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
