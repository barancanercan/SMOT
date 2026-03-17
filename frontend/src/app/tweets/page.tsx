"use client";

import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, User, Tweet, PaginatedResponse } from "@/lib/api";
import {
  Flame,
  ThumbsUp,
  MessageCircle,
  Repeat2,
  Eye,
  AlertCircle,
  Activity,
  Zap,
} from "lucide-react";

interface TopTweetsResponse {
  username: string;
  tweets: (Tweet & { engagement: number })[];
}

export default function TweetsPage() {
  const [selectedUser, setSelectedUser] = useState<string>("");

  // Fetch users
  const {
    data: usersData,
    isLoading: usersLoading,
    error: usersError,
  } = useQuery({
    queryKey: ["users"],
    queryFn: () => api.get<PaginatedResponse<User>>("/users/"),
    staleTime: 5 * 60 * 1000,
  });

  const users = usersData?.items || [];

  // Set default user when users load
  useMemo(() => {
    if (users.length > 0 && !selectedUser) {
      setSelectedUser(users[0].username);
    }
  }, [users, selectedUser]);

  // Fetch top tweets for selected user
  const {
    data: tweetsData,
    isLoading: tweetsLoading,
    error: tweetsError,
  } = useQuery({
    queryKey: ["top-tweets", selectedUser],
    queryFn: () =>
      api.get<TopTweetsResponse>(`/tweets/${selectedUser}/top?limit=20`),
    enabled: !!selectedUser,
    staleTime: 2 * 60 * 1000,
  });

  const tweets = tweetsData?.tweets || [];

  const formatNumber = (num: number) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
    if (num >= 1000) return (num / 1000).toFixed(1) + "K";
    return num.toString();
  };

  // Get engagement level color
  const getEngagementLevel = (engagement: number) => {
    if (engagement >= 10000) return { color: "text-[#00D1B2]", label: "YÜKSEK" };
    if (engagement >= 5000) return { color: "text-[#4DA3FF]", label: "ORTA" };
    return { color: "text-gray-500", label: "DÜŞÜK" };
  };

  if (usersError) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <div className="relative">
          <div className="absolute inset-0 blur-xl bg-red-500/20 rounded-full" />
          <AlertCircle className="relative h-12 w-12 text-red-500 mb-4" />
        </div>
        <h2 className="text-xl font-semibold text-white mb-2">
          KULLANICILAR YÜKLENEMEDI
        </h2>
        <p className="text-gray-400">
          API bağlantısını kontrol edin ve sayfayı yenileyin.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative">
        {/* Glassmorphism card */}
        <div className="relative bg-[#1A1A1A] border border-[#4DA3FF]/20 rounded-xl p-6 backdrop-blur-xl">
          <div className="absolute inset-0 bg-gradient-to-br from-[#4DA3FF]/5 to-transparent rounded-xl" />

          <div className="relative flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <div className="relative">
                  <div className="absolute inset-0 blur-lg bg-orange-500/30 rounded-full" />
                  <Flame className="relative h-7 w-7 text-orange-500" />
                </div>
                <h1 className="text-2xl font-bold text-white tracking-tight">
                  TOP TWEETS
                </h1>
                <div className="px-3 py-1 bg-[#00D1B2]/10 border border-[#00D1B2]/30 rounded-full">
                  <span className="text-xs font-mono text-[#00D1B2]">SIGNAL ANALYSIS</span>
                </div>
              </div>
              <p className="text-gray-400 text-sm font-mono">
                En çok etkileşim alan tweetler / yüksek engagement sinyalleri
              </p>
            </div>

            {/* User selector */}
            <div className="relative">
              <select
                value={selectedUser}
                onChange={(e) => setSelectedUser(e.target.value)}
                disabled={usersLoading}
                className="px-5 py-2.5 bg-[#0B0B0B] border border-[#4DA3FF]/30 rounded-lg
                         text-white font-mono text-sm
                         focus:ring-2 focus:ring-[#4DA3FF]/50 focus:border-[#4DA3FF]
                         hover:border-[#4DA3FF]/50 transition-all
                         disabled:opacity-50 disabled:cursor-not-allowed
                         appearance-none cursor-pointer
                         pr-10"
                style={{
                  backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%234DA3FF'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`,
                  backgroundRepeat: "no-repeat",
                  backgroundPosition: "right 0.5rem center",
                  backgroundSize: "1.5em 1.5em",
                }}
              >
                {usersLoading ? (
                  <option>YÜKLENIYOR...</option>
                ) : (
                  users.map((user) => (
                    <option key={user.username} value={user.username}>
                      @{user.username}
                    </option>
                  ))
                )}
              </select>
              <div className="absolute -bottom-1 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-[#4DA3FF]/30 to-transparent" />
            </div>
          </div>
        </div>
      </div>

      {/* Error state */}
      {tweetsError && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg flex items-center gap-3 backdrop-blur-sm">
          <AlertCircle className="h-5 w-5 flex-shrink-0" />
          <span className="font-mono text-sm">TWEETLER YÜKLENEMEDI</span>
        </div>
      )}

      {/* Loading state */}
      {tweetsLoading ? (
        <div className="flex flex-col items-center justify-center h-64">
          <div className="relative">
            <div className="absolute inset-0 blur-xl bg-[#4DA3FF]/20 rounded-full animate-pulse" />
            <div className="relative animate-spin rounded-full h-12 w-12 border-2 border-transparent border-t-[#4DA3FF] border-r-[#00D1B2]" />
          </div>
          <p className="mt-4 text-gray-500 font-mono text-sm">ANALYZING SIGNALS...</p>
        </div>
      ) : tweets.length === 0 ? (
        <div className="text-center py-12">
          <div className="relative inline-block mb-4">
            <div className="absolute inset-0 blur-2xl bg-gray-500/10 rounded-full" />
            <Flame className="relative h-12 w-12 mx-auto text-gray-600" />
          </div>
          <p className="text-gray-500 font-mono">NO SIGNALS DETECTED</p>
        </div>
      ) : (
        <div className="space-y-3">
          {tweets.map((tweet, index) => {
            const engagementLevel = getEngagementLevel(tweet.engagement);

            return (
              <div
                key={tweet.id || index}
                className="group relative bg-[#1A1A1A] border border-[#4DA3FF]/10 rounded-lg p-5
                         hover:border-[#4DA3FF]/30 hover:bg-[#1A1A1A]/80
                         transition-all duration-300"
              >
                {/* Hover glow effect */}
                <div className="absolute inset-0 bg-gradient-to-br from-[#4DA3FF]/0 to-[#00D1B2]/0
                              group-hover:from-[#4DA3FF]/5 group-hover:to-[#00D1B2]/5
                              rounded-lg transition-all duration-300 pointer-events-none" />

                {/* Content */}
                <div className="relative">
                  {/* Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      {/* Rank badge */}
                      <div className="relative">
                        <div className={`
                          px-3 py-1 rounded border font-mono text-sm font-bold
                          ${index === 0 ? 'bg-[#00D1B2]/10 border-[#00D1B2]/40 text-[#00D1B2]' :
                            index === 1 ? 'bg-[#4DA3FF]/10 border-[#4DA3FF]/40 text-[#4DA3FF]' :
                            index === 2 ? 'bg-orange-500/10 border-orange-500/40 text-orange-500' :
                            'bg-gray-500/10 border-gray-500/30 text-gray-500'}
                        `}>
                          #{index + 1}
                        </div>
                      </div>

                      {/* Username */}
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[#4DA3FF] font-medium">
                          @{tweet.username}
                        </span>
                        <div className="w-1 h-1 rounded-full bg-gray-600" />
                        <span className="text-xs text-gray-500 font-mono">
                          {tweet.tweet_date}
                        </span>
                      </div>
                    </div>

                    {/* Engagement badge */}
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-[#0B0B0B] border border-[#4DA3FF]/20 rounded-lg">
                      <Zap className={`h-3.5 w-3.5 ${engagementLevel.color}`} />
                      <span className={`text-xs font-mono font-bold ${engagementLevel.color}`}>
                        {engagementLevel.label}
                      </span>
                    </div>
                  </div>

                  {/* Tweet text */}
                  <div className="mb-4 pl-1">
                    <p className="text-gray-300 leading-relaxed whitespace-pre-wrap text-[15px]">
                      {tweet.tweet_text}
                    </p>
                  </div>

                  {/* Metrics */}
                  <div className="flex items-center gap-6 text-sm">
                    {/* Like */}
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-[#0B0B0B]/50 rounded-md border border-gray-800 hover:border-pink-500/30 transition-colors group/metric">
                      <ThumbsUp className="h-4 w-4 text-gray-500 group-hover/metric:text-pink-500 transition-colors" />
                      <span className="font-mono text-gray-400 group-hover/metric:text-pink-500 transition-colors">
                        {formatNumber(tweet.likes)}
                      </span>
                    </div>

                    {/* Reply */}
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-[#0B0B0B]/50 rounded-md border border-gray-800 hover:border-blue-500/30 transition-colors group/metric">
                      <MessageCircle className="h-4 w-4 text-gray-500 group-hover/metric:text-blue-500 transition-colors" />
                      <span className="font-mono text-gray-400 group-hover/metric:text-blue-500 transition-colors">
                        {formatNumber(tweet.replies)}
                      </span>
                    </div>

                    {/* Retweet */}
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-[#0B0B0B]/50 rounded-md border border-gray-800 hover:border-green-500/30 transition-colors group/metric">
                      <Repeat2 className="h-4 w-4 text-gray-500 group-hover/metric:text-green-500 transition-colors" />
                      <span className="font-mono text-gray-400 group-hover/metric:text-green-500 transition-colors">
                        {formatNumber(tweet.retweets)}
                      </span>
                    </div>

                    {/* Views */}
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-[#0B0B0B]/50 rounded-md border border-gray-800 hover:border-purple-500/30 transition-colors group/metric">
                      <Eye className="h-4 w-4 text-gray-500 group-hover/metric:text-purple-500 transition-colors" />
                      <span className="font-mono text-gray-400 group-hover/metric:text-purple-500 transition-colors">
                        {formatNumber(tweet.views)}
                      </span>
                    </div>

                    {/* Total engagement */}
                    <div className="ml-auto flex items-center gap-2 px-4 py-1.5 bg-gradient-to-r from-[#4DA3FF]/10 to-[#00D1B2]/10 rounded-md border border-[#4DA3FF]/20">
                      <Activity className="h-4 w-4 text-[#00D1B2]" />
                      <span className="font-mono text-white font-bold text-sm">
                        {formatNumber(tweet.engagement)}
                      </span>
                      <span className="text-xs text-gray-500 font-mono">ENG</span>
                    </div>
                  </div>
                </div>

                {/* Bottom accent line */}
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-[#4DA3FF]/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
