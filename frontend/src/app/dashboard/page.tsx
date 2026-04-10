"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, DashboardStats, Platform } from "@/lib/api";
import {
  BarChart3,
  Users,
  Heart,
  Eye,
  MessageCircle,
  Repeat2,
  TrendingUp,
  Shield,
  Zap,
  Camera,
  Video,
} from "lucide-react";
import { SkeletonMetricCard, SkeletonCard } from "@/components/ui/skeleton";
import { PartyBadge } from "@/components/ui/badge";
import { PlatformSelector } from "@/components/ui/platform-selector";
import Image from "next/image";

export default function DashboardPage() {
  const [platform, setPlatform] = useState<Platform>("twitter");

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["dashboard-overview", platform],
    queryFn: () => api.get<DashboardStats>(`/dashboard/overview?platform=${platform}`),
  });

  const { data: topTweets, isLoading: topTweetsLoading } = useQuery({
    queryKey: ["analytics-top-tweets"],
    queryFn: () => api.get<{ tweets: any[] }>("/analytics/tweets/top?limit=5"),
  });

  const { data: topPosts, isLoading: topPostsLoading } = useQuery({
    queryKey: ["analytics-top-posts"],
    queryFn: () => api.get<{ posts: any[] }>("/analytics/posts/top?limit=5"),
  });

  const { data: topUsers, isLoading: topUsersLoading } = useQuery({
    queryKey: ["analytics-engagement-top5"],
    queryFn: () => api.get<any[]>("/analytics/engagement?limit=5"),
  });

  return (
    <div className="min-h-screen bg-[#0B0B0B] p-6 space-y-6">
      {/* Gradient Header with Logo */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-[#1A1A1A] via-[#1A1A1A] to-[#0B0B0B] border border-white/10 p-8">
        {/* Animated Grid Background */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{
            backgroundImage: `linear-gradient(#4DA3FF 1px, transparent 1px), linear-gradient(90deg, #4DA3FF 1px, transparent 1px)`,
            backgroundSize: '50px 50px'
          }} />
        </div>

        {/* Glow Effects */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-[#4DA3FF]/20 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-[#00D1B2]/10 rounded-full blur-3xl" />

        <div className="relative flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="relative w-20 h-20 flex items-center justify-center">
              <div className="absolute inset-0 bg-[#4DA3FF]/20 rounded-xl blur-xl" />
              <Image
                src="/transparan_logo.png"
                alt="SMOT Logo"
                width={80}
                height={80}
                className="relative z-10"
              />
            </div>
            <div>
              <div className="flex items-center gap-3 mb-1">
                <Shield className="h-8 w-8 text-[#4DA3FF]" />
                <div>
                  <h1 className="text-3xl font-bold bg-gradient-to-r from-white via-blue-100 to-[#4DA3FF] bg-clip-text text-transparent">
                    SMOT
                  </h1>
                </div>
              </div>
              <p className="text-gray-400 mt-1">
                Gerçek Zamanlı · Sosyal Medya İzleme Paneli
              </p>
            </div>
          </div>

          {/* Platform Selector & Status */}
          <div className="flex items-center gap-4">
            <PlatformSelector
              value={platform}
              onChange={setPlatform}
              size="md"
            />
            <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#00D1B2]/10 border border-[#00D1B2]/30">
              <div className="w-2 h-2 rounded-full bg-[#00D1B2] animate-pulse" />
              <span className="text-[#00D1B2] text-sm font-medium">SISTEM AKTIF</span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Metrics - Cyber Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statsLoading ? (
          <>
            <SkeletonMetricCard />
            <SkeletonMetricCard />
            <SkeletonMetricCard />
            <SkeletonMetricCard />
          </>
        ) : platform === "twitter" ? (
          <>
            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-[#4DA3FF]/0 via-[#4DA3FF]/10 to-[#4DA3FF]/0 rounded-xl blur-xl group-hover:via-[#4DA3FF]/20 transition-all" />
              <div className="relative bg-[#1A1A1A]/80 backdrop-blur-xl border border-white/10 rounded-xl p-6 hover:border-[#4DA3FF]/50 transition-all">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 rounded-lg bg-[#4DA3FF]/10">
                    <BarChart3 className="h-5 w-5 text-[#4DA3FF]" />
                  </div>
                  <Zap className="h-4 w-4 text-gray-600" />
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-gray-400">Toplam Tweet</p>
                  <p className="text-3xl font-bold text-white">
                    {stats?.total_tweets?.toLocaleString("tr-TR") || "0"}
                  </p>
                  <p className="text-xs text-gray-500">
                    {stats?.total_original?.toLocaleString("tr-TR") || 0} orijinal
                  </p>
                </div>
              </div>
            </div>

            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-[#00D1B2]/0 via-[#00D1B2]/10 to-[#00D1B2]/0 rounded-xl blur-xl group-hover:via-[#00D1B2]/20 transition-all" />
              <div className="relative bg-[#1A1A1A]/80 backdrop-blur-xl border border-white/10 rounded-xl p-6 hover:border-[#00D1B2]/50 transition-all">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 rounded-lg bg-[#00D1B2]/10">
                    <Users className="h-5 w-5 text-[#00D1B2]" />
                  </div>
                  <Zap className="h-4 w-4 text-gray-600" />
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-gray-400">Meclis Uyesi</p>
                  <p className="text-3xl font-bold text-white">
                    {stats?.total_councilors?.toLocaleString("tr-TR") || "0"}
                  </p>
                  <p className="text-xs text-gray-500">
                    {stats?.active_users || 0} aktif
                  </p>
                </div>
              </div>
            </div>

            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-pink-500/0 via-pink-500/10 to-pink-500/0 rounded-xl blur-xl group-hover:via-pink-500/20 transition-all" />
              <div className="relative bg-[#1A1A1A]/80 backdrop-blur-xl border border-white/10 rounded-xl p-6 hover:border-pink-500/50 transition-all">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 rounded-lg bg-pink-500/10">
                    <Heart className="h-5 w-5 text-pink-500" />
                  </div>
                  <Zap className="h-4 w-4 text-gray-600" />
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-gray-400">Toplam Like</p>
                  <p className="text-3xl font-bold text-white">
                    {stats?.total_likes?.toLocaleString("tr-TR") || "0"}
                  </p>
                </div>
              </div>
            </div>

            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-purple-500/0 via-purple-500/10 to-purple-500/0 rounded-xl blur-xl group-hover:via-purple-500/20 transition-all" />
              <div className="relative bg-[#1A1A1A]/80 backdrop-blur-xl border border-white/10 rounded-xl p-6 hover:border-purple-500/50 transition-all">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 rounded-lg bg-purple-500/10">
                    <Eye className="h-5 w-5 text-purple-500" />
                  </div>
                  <Zap className="h-4 w-4 text-gray-600" />
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-gray-400">Toplam Gorus</p>
                  <p className="text-3xl font-bold text-white">
                    {stats?.total_views?.toLocaleString("tr-TR") || "0"}
                  </p>
                </div>
              </div>
            </div>
          </>
        ) : platform === "instagram" ? (
          <>
            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-pink-500/0 via-pink-500/10 to-pink-500/0 rounded-xl blur-xl group-hover:via-pink-500/20 transition-all" />
              <div className="relative bg-[#1A1A1A]/80 backdrop-blur-xl border border-white/10 rounded-xl p-6 hover:border-pink-500/50 transition-all">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 rounded-lg bg-pink-500/10">
                    <Camera className="h-5 w-5 text-pink-500" />
                  </div>
                  <Zap className="h-4 w-4 text-gray-600" />
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-gray-400">Toplam Post</p>
                  <p className="text-3xl font-bold text-white">
                    {stats?.total_posts?.toLocaleString("tr-TR") || "0"}
                  </p>
                  <p className="text-xs text-gray-500">
                    {stats?.total_photos || 0} foto, {stats?.total_videos || 0} video
                  </p>
                </div>
              </div>
            </div>

            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-[#00D1B2]/0 via-[#00D1B2]/10 to-[#00D1B2]/0 rounded-xl blur-xl group-hover:via-[#00D1B2]/20 transition-all" />
              <div className="relative bg-[#1A1A1A]/80 backdrop-blur-xl border border-white/10 rounded-xl p-6 hover:border-[#00D1B2]/50 transition-all">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 rounded-lg bg-[#00D1B2]/10">
                    <Users className="h-5 w-5 text-[#00D1B2]" />
                  </div>
                  <Zap className="h-4 w-4 text-gray-600" />
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-gray-400">Instagram Profil</p>
                  <p className="text-3xl font-bold text-white">
                    {stats?.total_instagram_profiles?.toLocaleString("tr-TR") || "0"}
                  </p>
                  <p className="text-xs text-gray-500">
                    {stats?.instagram_active_users || 0} aktif
                  </p>
                </div>
              </div>
            </div>

            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-red-500/0 via-red-500/10 to-red-500/0 rounded-xl blur-xl group-hover:via-red-500/20 transition-all" />
              <div className="relative bg-[#1A1A1A]/80 backdrop-blur-xl border border-white/10 rounded-xl p-6 hover:border-red-500/50 transition-all">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 rounded-lg bg-red-500/10">
                    <Heart className="h-5 w-5 text-red-500" />
                  </div>
                  <Zap className="h-4 w-4 text-gray-600" />
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-gray-400">Toplam Like</p>
                  <p className="text-3xl font-bold text-white">
                    {stats?.total_likes?.toLocaleString("tr-TR") || "0"}
                  </p>
                </div>
              </div>
            </div>

            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-purple-500/0 via-purple-500/10 to-purple-500/0 rounded-xl blur-xl group-hover:via-purple-500/20 transition-all" />
              <div className="relative bg-[#1A1A1A]/80 backdrop-blur-xl border border-white/10 rounded-xl p-6 hover:border-purple-500/50 transition-all">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 rounded-lg bg-purple-500/10">
                    <MessageCircle className="h-5 w-5 text-purple-500" />
                  </div>
                  <Zap className="h-4 w-4 text-gray-600" />
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-gray-400">Toplam Yorum</p>
                  <p className="text-3xl font-bold text-white">
                    {stats?.total_comments?.toLocaleString("tr-TR") || "0"}
                  </p>
                </div>
              </div>
            </div>
          </>
        ) : (
          /* BOTH platforms */
          <>
            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-[#4DA3FF]/0 via-[#4DA3FF]/10 to-[#4DA3FF]/0 rounded-xl blur-xl group-hover:via-[#4DA3FF]/20 transition-all" />
              <div className="relative bg-[#1A1A1A]/80 backdrop-blur-xl border border-white/10 rounded-xl p-6 hover:border-[#4DA3FF]/50 transition-all">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 rounded-lg bg-gradient-to-r from-[#4DA3FF]/20 to-pink-500/20">
                    <BarChart3 className="h-5 w-5 text-purple-400" />
                  </div>
                  <Zap className="h-4 w-4 text-gray-600" />
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-gray-400">Toplam Icerik</p>
                  <p className="text-3xl font-bold text-white">
                    {stats?.total_content?.toLocaleString("tr-TR") || "0"}
                  </p>
                  <p className="text-xs text-gray-500">
                    {stats?.total_tweets || 0} tweet, {stats?.total_posts || 0} post
                  </p>
                </div>
              </div>
            </div>

            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-[#00D1B2]/0 via-[#00D1B2]/10 to-[#00D1B2]/0 rounded-xl blur-xl group-hover:via-[#00D1B2]/20 transition-all" />
              <div className="relative bg-[#1A1A1A]/80 backdrop-blur-xl border border-white/10 rounded-xl p-6 hover:border-[#00D1B2]/50 transition-all">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 rounded-lg bg-[#00D1B2]/10">
                    <Users className="h-5 w-5 text-[#00D1B2]" />
                  </div>
                  <Zap className="h-4 w-4 text-gray-600" />
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-gray-400">Meclis Uyesi</p>
                  <p className="text-3xl font-bold text-white">
                    {stats?.total_councilors?.toLocaleString("tr-TR") || "0"}
                  </p>
                  <p className="text-xs text-gray-500">
                    {stats?.total_profiles || 0} profil
                  </p>
                </div>
              </div>
            </div>

            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-pink-500/0 via-pink-500/10 to-pink-500/0 rounded-xl blur-xl group-hover:via-pink-500/20 transition-all" />
              <div className="relative bg-[#1A1A1A]/80 backdrop-blur-xl border border-white/10 rounded-xl p-6 hover:border-pink-500/50 transition-all">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 rounded-lg bg-pink-500/10">
                    <Heart className="h-5 w-5 text-pink-500" />
                  </div>
                  <Zap className="h-4 w-4 text-gray-600" />
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-gray-400">Toplam Like</p>
                  <p className="text-3xl font-bold text-white">
                    {stats?.total_likes?.toLocaleString("tr-TR") || "0"}
                  </p>
                  <p className="text-xs text-gray-500">
                    X: {stats?.twitter_likes || 0}, IG: {stats?.instagram_likes || 0}
                  </p>
                </div>
              </div>
            </div>

            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-r from-purple-500/0 via-purple-500/10 to-purple-500/0 rounded-xl blur-xl group-hover:via-purple-500/20 transition-all" />
              <div className="relative bg-[#1A1A1A]/80 backdrop-blur-xl border border-white/10 rounded-xl p-6 hover:border-purple-500/50 transition-all">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-2 rounded-lg bg-purple-500/10">
                    <TrendingUp className="h-5 w-5 text-purple-500" />
                  </div>
                  <Zap className="h-4 w-4 text-gray-600" />
                </div>
                <div className="space-y-1">
                  <p className="text-sm text-gray-400">Toplam Etkilesim</p>
                  <p className="text-3xl font-bold text-white">
                    {stats?.total_engagement?.toLocaleString("tr-TR") || "0"}
                  </p>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Secondary Metrics - Engagement Stats (Platform-aware) */}
      {platform === "twitter" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {statsLoading ? (
            <>
              <SkeletonMetricCard />
              <SkeletonMetricCard />
              <SkeletonMetricCard />
            </>
          ) : (
            <>
              <div className="relative bg-gradient-to-br from-[#1A1A1A] to-[#0B0B0B] border border-white/10 rounded-xl p-6 hover:border-blue-500/50 transition-all overflow-hidden group">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="relative flex items-center gap-4">
                  <div className="p-3 rounded-lg bg-blue-500/10 ring-1 ring-blue-500/20">
                    <MessageCircle className="h-6 w-6 text-blue-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-gray-400">Toplam Reply</p>
                    <p className="text-2xl font-bold text-white">
                      {stats?.total_replies?.toLocaleString("tr-TR") || "0"}
                    </p>
                  </div>
                </div>
              </div>

              <div className="relative bg-gradient-to-br from-[#1A1A1A] to-[#0B0B0B] border border-white/10 rounded-xl p-6 hover:border-green-500/50 transition-all overflow-hidden group">
                <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="relative flex items-center gap-4">
                  <div className="p-3 rounded-lg bg-green-500/10 ring-1 ring-green-500/20">
                    <Repeat2 className="h-6 w-6 text-green-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-gray-400">Toplam Retweet</p>
                    <p className="text-2xl font-bold text-white">
                      {(stats as any)?.total_retweets_count?.toLocaleString("tr-TR") || "0"}
                    </p>
                  </div>
                </div>
              </div>

              <div className="relative bg-gradient-to-br from-[#1A1A1A] to-[#0B0B0B] border border-white/10 rounded-xl p-6 hover:border-purple-500/50 transition-all overflow-hidden group">
                <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="relative flex items-center gap-4">
                  <div className="p-3 rounded-lg bg-purple-500/10 ring-1 ring-purple-500/20">
                    <TrendingUp className="h-6 w-6 text-purple-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm text-gray-400">Ort. Etkilesim</p>
                    <p className="text-2xl font-bold text-white">
                      {stats?.total_tweets && stats.total_tweets > 0
                        ? Math.round(
                            ((stats.total_likes || 0) +
                              (stats.total_replies || 0) +
                              ((stats as any).total_retweets_count || 0)) /
                              stats.total_tweets
                          ).toLocaleString("tr-TR")
                        : "0"}
                    </p>
                    <p className="text-xs text-gray-500">tweet basina</p>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* Charts Row - Top Content Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* En Çok Etkileşim Alan Tweetler */}
        <div className="relative bg-[#1A1A1A]/80 backdrop-blur-xl border border-white/10 rounded-xl overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#4DA3FF]/50 to-transparent" />

          <div className="p-6 border-b border-white/10">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-[#4DA3FF]/10">
                <TrendingUp className="h-5 w-5 text-[#4DA3FF]" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">En Çok Etkileşim Alan Tweetler</h3>
                <p className="text-sm text-gray-500">Tüm zamanların en yüksek etkileşimi</p>
              </div>
            </div>
          </div>

          <div className="p-6">
            {topTweetsLoading ? (
              <div className="space-y-3">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="h-16 bg-[#0B0B0B]/50 rounded-lg animate-pulse" />
                ))}
              </div>
            ) : (
              <div className="space-y-3">
                {topTweets?.tweets?.map((tweet: any, index: number) => (
                  <div key={tweet.id} className="group flex gap-3 p-3 rounded-lg bg-[#0B0B0B]/50 border border-white/5 hover:border-[#4DA3FF]/30 transition-all">
                    <div className="flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-full bg-[#4DA3FF]/10 text-[#4DA3FF] text-sm font-bold">
                      {index + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium text-white truncate">{tweet.name}</span>
                        <PartyBadge party={tweet.party || "BAGIMSIZ"} />
                      </div>
                      <p className="text-xs text-gray-400 line-clamp-2 leading-relaxed">{tweet.tweet_text}</p>
                    </div>
                    <div className="flex-shrink-0 text-right">
                      <div className="flex items-center gap-1 text-pink-400">
                        <Heart className="h-3 w-3" />
                        <span className="text-xs font-semibold">{tweet.likes?.toLocaleString("tr-TR")}</span>
                      </div>
                      <div className="flex items-center gap-1 text-green-400 mt-1">
                        <Repeat2 className="h-3 w-3" />
                        <span className="text-xs">{tweet.retweets?.toLocaleString("tr-TR")}</span>
                      </div>
                    </div>
                  </div>
                ))}
                {(!topTweets?.tweets || topTweets.tweets.length === 0) && (
                  <div className="h-[200px] flex items-center justify-center text-gray-500 text-sm">
                    Veri bulunamadı
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* En Çok Etkileşim Alan Instagram Postları */}
        <div className="relative bg-[#1A1A1A]/80 backdrop-blur-xl border border-white/10 rounded-xl overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#E1306C]/50 to-transparent" />

          <div className="p-6 border-b border-white/10">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-[#E1306C]/10">
                <Camera className="h-5 w-5 text-[#E1306C]" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">En Çok Etkileşim Alan Postlar</h3>
                <p className="text-sm text-gray-500">Instagram tüm zamanların en iyileri</p>
              </div>
            </div>
          </div>

          <div className="p-6">
            {topPostsLoading ? (
              <div className="space-y-3">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="h-16 bg-[#0B0B0B]/50 rounded-lg animate-pulse" />
                ))}
              </div>
            ) : (
              <div className="space-y-3">
                {topPosts?.posts?.map((post: any, index: number) => (
                  <div key={post.id} className="group flex gap-3 p-3 rounded-lg bg-[#0B0B0B]/50 border border-white/5 hover:border-[#E1306C]/30 transition-all">
                    <div className="flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-full bg-[#E1306C]/10 text-[#E1306C] text-sm font-bold">
                      {index + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium text-white truncate">{post.name || post.username}</span>
                        <PartyBadge party={post.party || "BAGIMSIZ"} />
                        {post.is_video && <Video className="h-3 w-3 text-gray-400 flex-shrink-0" />}
                      </div>
                      <p className="text-xs text-gray-400 line-clamp-2 leading-relaxed">{post.caption || "—"}</p>
                    </div>
                    <div className="flex-shrink-0 text-right">
                      <div className="flex items-center gap-1 text-pink-400">
                        <Heart className="h-3 w-3" />
                        <span className="text-xs font-semibold">{post.likes?.toLocaleString("tr-TR")}</span>
                      </div>
                      <div className="flex items-center gap-1 text-purple-400 mt-1">
                        <MessageCircle className="h-3 w-3" />
                        <span className="text-xs">{post.comments?.toLocaleString("tr-TR")}</span>
                      </div>
                    </div>
                  </div>
                ))}
                {(!topPosts?.posts || topPosts.posts.length === 0) && (
                  <div className="h-[200px] flex items-center justify-center text-gray-500 text-sm">
                    Veri bulunamadı
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Top Performers - Intelligence Leaderboard */}
      <div className="relative bg-[#1A1A1A]/80 backdrop-blur-xl border border-white/10 rounded-xl overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#4DA3FF]/50 to-transparent" />

        <div className="p-6 border-b border-white/10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-gradient-to-br from-[#4DA3FF]/20 to-[#00D1B2]/20">
                <TrendingUp className="h-5 w-5 text-[#4DA3FF]" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">En Aktif Uyeler</h3>
                <p className="text-sm text-gray-500">Etkilesime gore en aktifler</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Image
                src="/minik_logo.png"
                alt="MIS"
                width={24}
                height={24}
                className="opacity-50"
              />
            </div>
          </div>
        </div>

        <div className="p-6">
          {topUsersLoading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="flex items-center gap-4 p-4 rounded-lg bg-[#0B0B0B]/50">
                  <div className="w-10 h-10 bg-gray-800 rounded-full animate-pulse" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-gray-800 rounded w-1/3 animate-pulse" />
                    <div className="h-3 bg-gray-800 rounded w-1/4 animate-pulse" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {topUsers?.map((user: any, index: number) => (
                <div
                  key={user.username}
                  className="group relative flex items-center gap-4 p-4 rounded-lg bg-[#0B0B0B]/50 border border-white/5 hover:border-[#4DA3FF]/50 hover:bg-[#0B0B0B]/80 transition-all"
                >
                  {/* Rank Badge */}
                  <div className="relative flex items-center justify-center w-10 h-10 rounded-full bg-gradient-to-br from-[#4DA3FF]/20 to-[#00D1B2]/20 border border-[#4DA3FF]/30 font-bold text-[#4DA3FF] group-hover:from-[#4DA3FF]/30 group-hover:to-[#00D1B2]/30 transition-all">
                    {index === 0 && <div className="absolute -inset-1 bg-[#4DA3FF]/20 rounded-full blur-md" />}
                    <span className="relative text-lg">{index + 1}</span>
                  </div>

                  {/* User Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="font-semibold text-white truncate group-hover:text-[#4DA3FF] transition-colors">
                        {user.name}
                      </p>
                      <PartyBadge party={user.party || "BAGIMSIZ"} />
                    </div>
                    <p className="text-sm text-gray-500">@{user.username}</p>
                  </div>

                  {/* Engagement Score */}
                  <div className="text-right">
                    <p className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-[#4DA3FF] to-[#00D1B2]">
                      {user.total_engagement?.toLocaleString("tr-TR")}
                    </p>
                    <p className="text-xs text-gray-500 uppercase tracking-wider">etkilesim</p>
                  </div>

                  {/* Hover Glow Effect */}
                  <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-[#4DA3FF]/0 via-[#4DA3FF]/5 to-[#00D1B2]/0 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Footer Signal */}
      <div className="flex items-center justify-center gap-2 text-gray-600 text-sm">
        <div className="w-2 h-2 rounded-full bg-[#00D1B2] animate-pulse" />
        <span>Istihbarat sistemi aktif</span>
      </div>
    </div>
  );
}
