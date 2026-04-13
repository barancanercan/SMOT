"use client";

import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, User, PaginatedResponse, TweetItem } from "@/lib/api";
import {
  Flame,
  ThumbsUp,
  MessageCircle,
  Repeat2,
  Eye,
  AlertCircle,
  Activity,
  Zap,
  Building2,
  Users,
  Clock,
  Settings2,
  ExternalLink,
} from "lucide-react";

// Party colors
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
  return PARTY_COLORS[party] || "#60A5FA";
};

interface TopTweetsResponse {
  filter: { party?: string; username?: string };
  limit: number;
  tweets: TweetItem[];
}

export default function TweetsPage() {
  const [activeTab, setActiveTab] = useState<"party" | "user">("party");
  const [selectedUser, setSelectedUser] = useState<string>("");
  const [selectedParty, setSelectedParty] = useState<string>("");
  const [limit, setLimit] = useState<number>(10);

  // Fetch users
  const {
    data: usersData,
    isLoading: usersLoading,
    error: usersError,
  } = useQuery({
    queryKey: ["users"],
    queryFn: () => api.get<PaginatedResponse<User>>("/users/?page_size=100"),
    staleTime: 5 * 60 * 1000,
  });

  const users = usersData?.items || [];

  // Get unique parties
  const parties = useMemo(() => {
    const partySet = new Set(users.map((u) => u.party).filter(Boolean));
    return Array.from(partySet).sort();
  }, [users]);

  // Set defaults when data loads
  useMemo(() => {
    if (users.length > 0 && !selectedUser) {
      setSelectedUser(users[0].username);
    }
    if (parties.length > 0 && !selectedParty) {
      setSelectedParty(parties[0]);
    }
  }, [users, parties, selectedUser, selectedParty]);

  // Fetch top tweets
  const {
    data: tweetsData,
    isLoading: tweetsLoading,
    error: tweetsError,
  } = useQuery({
    queryKey: ["top-tweets", activeTab, selectedUser, selectedParty, limit],
    queryFn: () => {
      if (activeTab === "party" && selectedParty) {
        return api.get<TopTweetsResponse>(`/analytics/tweets/top?party=${encodeURIComponent(selectedParty)}&limit=${limit}`);
      } else if (activeTab === "user" && selectedUser) {
        return api.get<TopTweetsResponse>(`/analytics/tweets/top?username=${selectedUser}&limit=${limit}`);
      }
      return null;
    },
    enabled: (activeTab === "party" && !!selectedParty) || (activeTab === "user" && !!selectedUser),
    staleTime: 2 * 60 * 1000,
  });

  const tweets = tweetsData?.tweets || [];

  const formatNumber = (num: number) => {
    if (num === undefined || num === null) return "0";
    if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
    if (num >= 1000) return (num / 1000).toFixed(1) + "K";
    return num.toString();
  };

  const getEngagementLevel = (engagement: number) => {
    if (engagement >= 10000) return { color: "text-[#00D1B2]", label: "YUKSEK" };
    if (engagement >= 5000) return { color: "text-[#4DA3FF]", label: "ORTA" };
    return { color: "text-gray-500", label: "DUSUK" };
  };

  if (usersError) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <div className="relative">
          <div className="absolute inset-0 blur-xl bg-red-500/20 rounded-full" />
          <AlertCircle className="relative h-12 w-12 text-red-500 mb-4" />
        </div>
        <h2 className="text-xl font-semibold text-white mb-2">
          KULLANICILAR YUKLENEMEDI
        </h2>
        <p className="text-gray-400">
          API baglantisini kontrol edin ve sayfayi yenileyin.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="relative">
        <div className="relative bg-[#1A1A1A] border border-[#4DA3FF]/20 rounded-xl p-6 backdrop-blur-xl">
          <div className="absolute inset-0 bg-gradient-to-br from-[#4DA3FF]/5 to-transparent rounded-xl" />

          <div className="relative">
            {/* Title Row */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <div className="relative">
                    <div className="absolute inset-0 blur-lg bg-orange-500/30 rounded-full" />
                    <Flame className="relative h-7 w-7 text-orange-500" />
                  </div>
                  <h1 className="text-2xl font-bold text-white tracking-tight">
                    TOP TWEETLER
                  </h1>
                  <div className="px-3 py-1 bg-[#00D1B2]/10 border border-[#00D1B2]/30 rounded-full">
                    <span className="text-xs font-mono text-[#00D1B2]">SINYAL ANALIZI</span>
                  </div>
                </div>
                <p className="text-gray-400 text-sm font-mono">
                  En cok etkilesim alan tweetler // yuksek etkilesim sinyalleri
                </p>
              </div>

              {/* Tab Buttons */}
              <div className="flex bg-[#0B0B0B] rounded-xl p-1 border border-white/10">
                <button
                  onClick={() => setActiveTab("party")}
                  className={`flex items-center gap-2 px-4 py-2.5 rounded-lg transition-all ${
                    activeTab === "party"
                      ? "bg-orange-600 text-white"
                      : "text-gray-400 hover:text-white"
                  }`}
                >
                  <Building2 className="w-4 h-4" />
                  Parti
                </button>
                <button
                  onClick={() => setActiveTab("user")}
                  className={`flex items-center gap-2 px-4 py-2.5 rounded-lg transition-all ${
                    activeTab === "user"
                      ? "bg-orange-600 text-white"
                      : "text-gray-400 hover:text-white"
                  }`}
                >
                  <Users className="w-4 h-4" />
                  Uye
                </button>
              </div>
            </div>

            {/* Filter Row */}
            <div className="flex items-center gap-4 flex-wrap">
              {/* Party/User Selector */}
              {activeTab === "party" ? (
                <div className="relative">
                  <label className="block text-xs text-gray-500 font-mono mb-1">PARTI SEC</label>
                  <select
                    value={selectedParty}
                    onChange={(e) => setSelectedParty(e.target.value)}
                    className="px-4 py-2.5 bg-[#0B0B0B] border border-[#4DA3FF]/30 rounded-lg
                             text-white font-mono text-sm min-w-[180px]
                             focus:ring-2 focus:ring-[#4DA3FF]/50 focus:border-[#4DA3FF]
                             hover:border-[#4DA3FF]/50 transition-all cursor-pointer"
                  >
                    {parties.map((party) => (
                      <option key={party} value={party}>
                        {party}
                      </option>
                    ))}
                  </select>
                </div>
              ) : (
                <div className="relative">
                  <label className="block text-xs text-gray-500 font-mono mb-1">UYE SEC</label>
                  <select
                    value={selectedUser}
                    onChange={(e) => setSelectedUser(e.target.value)}
                    disabled={usersLoading}
                    className="px-4 py-2.5 bg-[#0B0B0B] border border-[#4DA3FF]/30 rounded-lg
                             text-white font-mono text-sm min-w-[180px]
                             focus:ring-2 focus:ring-[#4DA3FF]/50 focus:border-[#4DA3FF]
                             hover:border-[#4DA3FF]/50 transition-all
                             disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                  >
                    {usersLoading ? (
                      <option>YUKLENIYOR...</option>
                    ) : (
                      users.map((user) => (
                        <option key={user.username} value={user.username}>
                          @{user.username} - {user.party}
                        </option>
                      ))
                    )}
                  </select>
                </div>
              )}

              {/* Limit Selector */}
              <div className="relative">
                <label className="block text-xs text-gray-500 font-mono mb-1">TWEET SAYISI</label>
                <div className="flex items-center gap-2">
                  <select
                    value={limit}
                    onChange={(e) => setLimit(Number(e.target.value))}
                    className="px-4 py-2.5 bg-[#0B0B0B] border border-[#4DA3FF]/30 rounded-lg
                             text-white font-mono text-sm
                             focus:ring-2 focus:ring-[#4DA3FF]/50 focus:border-[#4DA3FF]
                             hover:border-[#4DA3FF]/50 transition-all cursor-pointer"
                  >
                    <option value={5}>Top 5</option>
                    <option value={10}>Top 10</option>
                    <option value={15}>Top 15</option>
                    <option value={20}>Top 20</option>
                    <option value={30}>Top 30</option>
                    <option value={50}>Top 50</option>
                  </select>
                  <Settings2 className="w-4 h-4 text-gray-500" />
                </div>
              </div>

              {/* Active filter badge */}
              <div className="ml-auto flex items-center gap-2 px-4 py-2 bg-[#0B0B0B] border border-white/10 rounded-lg">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{
                    backgroundColor: activeTab === "party"
                      ? getPartyColor(selectedParty)
                      : getPartyColor(users.find(u => u.username === selectedUser)?.party || ""),
                  }}
                />
                <span className="text-white font-mono text-sm">
                  {activeTab === "party" ? selectedParty : `@${selectedUser}`}
                </span>
                <span className="text-gray-500 text-xs">({tweets.length} tweet)</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Error state */}
      {tweetsError && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg flex items-center gap-3 backdrop-blur-sm">
          <AlertCircle className="h-5 w-5 flex-shrink-0" />
          <span className="font-mono text-sm">TWEETLER YUKLENEMEDI</span>
        </div>
      )}

      {/* Loading state */}
      {tweetsLoading ? (
        <div className="flex flex-col items-center justify-center h-64">
          <div className="relative">
            <div className="absolute inset-0 blur-xl bg-[#4DA3FF]/20 rounded-full animate-pulse" />
            <div className="relative animate-spin rounded-full h-12 w-12 border-2 border-transparent border-t-[#4DA3FF] border-r-[#00D1B2]" />
          </div>
          <p className="mt-4 text-gray-500 font-mono text-sm">SINYALLER ANALIZ EDILIYOR...</p>
        </div>
      ) : tweets.length === 0 ? (
        <div className="text-center py-12">
          <div className="relative inline-block mb-4">
            <div className="absolute inset-0 blur-2xl bg-gray-500/10 rounded-full" />
            <Flame className="relative h-12 w-12 mx-auto text-gray-600" />
          </div>
          <p className="text-gray-500 font-mono">SINYAL BULUNAMADI</p>
        </div>
      ) : (
        <div className="space-y-3">
          {tweets.map((tweet, index) => {
            const engagementLevel = getEngagementLevel(tweet.engagement || 0);

            return (
              <a
                key={tweet.id || index}
                href={tweet.tweet_url || `https://x.com/${tweet.username}`}
                target="_blank"
                rel="noopener noreferrer"
                className="group relative bg-[#1A1A1A] border border-[#4DA3FF]/10 rounded-lg p-5
                         hover:border-[#4DA3FF]/30 hover:bg-[#1A1A1A]/80
                         transition-all duration-300 block cursor-pointer"
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

                      {/* Username & Party */}
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[#4DA3FF] font-medium">
                          @{tweet.username}
                        </span>
                        {activeTab === "party" && (
                          <>
                            <span className="text-xs text-gray-600">|</span>
                            <span className="text-xs text-gray-400">{tweet.name}</span>
                          </>
                        )}
                        <span
                          className="px-2 py-0.5 text-xs rounded-full"
                          style={{
                            backgroundColor: getPartyColor(tweet.party) + "30",
                            color: getPartyColor(tweet.party),
                          }}
                        >
                          {tweet.party}
                        </span>
                        <div className="w-1 h-1 rounded-full bg-gray-600" />
                        <span className="text-xs text-gray-500 font-mono flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {tweet.tweet_date?.split("T")[0] || "-"}
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
                  <div className="flex items-center gap-6 text-sm flex-wrap">
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
                        {formatNumber(tweet.engagement || 0)}
                      </span>
                      <span className="text-xs text-gray-500 font-mono">ETK</span>
                    </div>

                    {/* External link indicator */}
                    <div className="p-1.5 bg-[#0B0B0B] border border-white/10 rounded-lg group-hover:border-blue-500/30 transition-colors">
                      <ExternalLink className="w-4 h-4 text-gray-600 group-hover:text-blue-400 transition-colors" />
                    </div>
                  </div>
                </div>

                {/* Bottom accent line */}
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-[#4DA3FF]/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              </a>
            );
          })}
        </div>
      )}
    </div>
  );
}
