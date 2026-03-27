"use client";

import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, User, PaginatedResponse, InstagramPostItem, TopPostsResponse } from "@/lib/api";
import {
  Camera,
  Heart,
  MessageCircle,
  AlertCircle,
  Activity,
  Zap,
  Building2,
  Users,
  Clock,
  Settings2,
  Video,
  Image as ImageIcon,
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
  return PARTY_COLORS[party] || "#E1306C";
};

export default function InstagramPage() {
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

  // Fetch top posts
  const {
    data: postsData,
    isLoading: postsLoading,
    error: postsError,
  } = useQuery({
    queryKey: ["top-posts", activeTab, selectedUser, selectedParty, limit],
    queryFn: () => {
      if (activeTab === "party" && selectedParty) {
        return api.get<TopPostsResponse>(`/analytics/posts/top?party=${encodeURIComponent(selectedParty)}&limit=${limit}`);
      } else if (activeTab === "user" && selectedUser) {
        return api.get<TopPostsResponse>(`/analytics/posts/top?username=${selectedUser}&limit=${limit}`);
      }
      return null;
    },
    enabled: (activeTab === "party" && !!selectedParty) || (activeTab === "user" && !!selectedUser),
    staleTime: 2 * 60 * 1000,
  });

  const posts = postsData?.posts || [];

  const formatNumber = (num: number) => {
    if (num === undefined || num === null) return "0";
    if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
    if (num >= 1000) return (num / 1000).toFixed(1) + "K";
    return num.toString();
  };

  const getEngagementLevel = (engagement: number) => {
    if (engagement >= 1000) return { color: "text-[#00D1B2]", label: "YUKSEK" };
    if (engagement >= 500) return { color: "text-[#E1306C]", label: "ORTA" };
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
        <div className="relative bg-[#1A1A1A] border border-[#E1306C]/20 rounded-xl p-6 backdrop-blur-xl">
          <div className="absolute inset-0 bg-gradient-to-br from-[#E1306C]/5 to-[#833AB4]/5 rounded-xl" />

          <div className="relative">
            {/* Title Row */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <div className="relative">
                    <div className="absolute inset-0 blur-lg bg-gradient-to-r from-[#E1306C]/30 to-[#833AB4]/30 rounded-full" />
                    <Camera className="relative h-7 w-7 text-[#E1306C]" />
                  </div>
                  <h1 className="text-2xl font-bold text-white tracking-tight">
                    TOP INSTAGRAM POSTLARI
                  </h1>
                  <div className="px-3 py-1 bg-[#E1306C]/10 border border-[#E1306C]/30 rounded-full">
                    <span className="text-xs font-mono text-[#E1306C]">ICERIK ANALIZI</span>
                  </div>
                </div>
                <p className="text-gray-400 text-sm font-mono">
                  En cok etkilesim alan Instagram postlari // gorsel icerik sinyalleri
                </p>
              </div>

              {/* Tab Buttons */}
              <div className="flex bg-[#0B0B0B] rounded-xl p-1 border border-white/10">
                <button
                  onClick={() => setActiveTab("party")}
                  className={`flex items-center gap-2 px-4 py-2.5 rounded-lg transition-all ${
                    activeTab === "party"
                      ? "bg-gradient-to-r from-[#E1306C] to-[#833AB4] text-white"
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
                      ? "bg-gradient-to-r from-[#E1306C] to-[#833AB4] text-white"
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
                    className="px-4 py-2.5 bg-[#0B0B0B] border border-[#E1306C]/30 rounded-lg
                             text-white font-mono text-sm min-w-[180px]
                             focus:ring-2 focus:ring-[#E1306C]/50 focus:border-[#E1306C]
                             hover:border-[#E1306C]/50 transition-all cursor-pointer"
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
                    className="px-4 py-2.5 bg-[#0B0B0B] border border-[#E1306C]/30 rounded-lg
                             text-white font-mono text-sm min-w-[180px]
                             focus:ring-2 focus:ring-[#E1306C]/50 focus:border-[#E1306C]
                             hover:border-[#E1306C]/50 transition-all
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
                <label className="block text-xs text-gray-500 font-mono mb-1">POST SAYISI</label>
                <div className="flex items-center gap-2">
                  <select
                    value={limit}
                    onChange={(e) => setLimit(Number(e.target.value))}
                    className="px-4 py-2.5 bg-[#0B0B0B] border border-[#E1306C]/30 rounded-lg
                             text-white font-mono text-sm
                             focus:ring-2 focus:ring-[#E1306C]/50 focus:border-[#E1306C]
                             hover:border-[#E1306C]/50 transition-all cursor-pointer"
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
                <span className="text-gray-500 text-xs">({posts.length} post)</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Error state */}
      {postsError && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg flex items-center gap-3 backdrop-blur-sm">
          <AlertCircle className="h-5 w-5 flex-shrink-0" />
          <span className="font-mono text-sm">POSTLAR YUKLENEMEDI</span>
        </div>
      )}

      {/* Loading state */}
      {postsLoading ? (
        <div className="flex flex-col items-center justify-center h-64">
          <div className="relative">
            <div className="absolute inset-0 blur-xl bg-[#E1306C]/20 rounded-full animate-pulse" />
            <div className="relative animate-spin rounded-full h-12 w-12 border-2 border-transparent border-t-[#E1306C] border-r-[#833AB4]" />
          </div>
          <p className="mt-4 text-gray-500 font-mono text-sm">ICERIK ANALIZ EDILIYOR...</p>
        </div>
      ) : posts.length === 0 ? (
        <div className="text-center py-12">
          <div className="relative inline-block mb-4">
            <div className="absolute inset-0 blur-2xl bg-gray-500/10 rounded-full" />
            <Camera className="relative h-12 w-12 mx-auto text-gray-600" />
          </div>
          <p className="text-gray-500 font-mono">POST BULUNAMADI</p>
        </div>
      ) : (
        <div className="space-y-3">
          {posts.map((post, index) => {
            const engagementLevel = getEngagementLevel(post.engagement || 0);

            return (
              <div
                key={post.id || index}
                className="group relative bg-[#1A1A1A] border border-[#E1306C]/10 rounded-lg p-5
                         hover:border-[#E1306C]/30 hover:bg-[#1A1A1A]/80
                         transition-all duration-300"
              >
                {/* Hover glow effect */}
                <div className="absolute inset-0 bg-gradient-to-br from-[#E1306C]/0 to-[#833AB4]/0
                              group-hover:from-[#E1306C]/5 group-hover:to-[#833AB4]/5
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
                            index === 1 ? 'bg-[#E1306C]/10 border-[#E1306C]/40 text-[#E1306C]' :
                            index === 2 ? 'bg-[#833AB4]/10 border-[#833AB4]/40 text-[#833AB4]' :
                            'bg-gray-500/10 border-gray-500/30 text-gray-500'}
                        `}>
                          #{index + 1}
                        </div>
                      </div>

                      {/* Username & Party */}
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[#E1306C] font-medium">
                          @{post.username}
                        </span>
                        {activeTab === "party" && (
                          <>
                            <span className="text-xs text-gray-600">|</span>
                            <span className="text-xs text-gray-400">{post.name}</span>
                          </>
                        )}
                        <span
                          className="px-2 py-0.5 text-xs rounded-full"
                          style={{
                            backgroundColor: getPartyColor(post.party) + "30",
                            color: getPartyColor(post.party),
                          }}
                        >
                          {post.party}
                        </span>

                        {/* Media type badge */}
                        <div className={`flex items-center gap-1 px-2 py-0.5 rounded text-xs ${
                          post.is_video
                            ? 'bg-purple-500/20 text-purple-400'
                            : 'bg-blue-500/20 text-blue-400'
                        }`}>
                          {post.is_video ? <Video className="w-3 h-3" /> : <ImageIcon className="w-3 h-3" />}
                          {post.is_video ? 'Video' : 'Foto'}
                        </div>

                        <div className="w-1 h-1 rounded-full bg-gray-600" />
                        <span className="text-xs text-gray-500 font-mono flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {post.post_date?.split("T")[0] || "-"}
                        </span>
                      </div>
                    </div>

                    {/* Engagement badge + Link */}
                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-2 px-3 py-1.5 bg-[#0B0B0B] border border-[#E1306C]/20 rounded-lg">
                        <Zap className={`h-3.5 w-3.5 ${engagementLevel.color}`} />
                        <span className={`text-xs font-mono font-bold ${engagementLevel.color}`}>
                          {engagementLevel.label}
                        </span>
                      </div>
                      {post.post_url && (
                        <a
                          href={post.post_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-1.5 bg-[#0B0B0B] border border-white/10 rounded-lg hover:border-[#E1306C]/30 transition-colors"
                        >
                          <ExternalLink className="w-4 h-4 text-gray-400 hover:text-[#E1306C]" />
                        </a>
                      )}
                    </div>
                  </div>

                  {/* Caption */}
                  <div className="mb-4 pl-1">
                    <p className="text-gray-300 leading-relaxed whitespace-pre-wrap text-[15px]">
                      {post.caption || "(Aciklama yok)"}
                    </p>
                  </div>

                  {/* Metrics */}
                  <div className="flex items-center gap-6 text-sm flex-wrap">
                    {/* Like */}
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-[#0B0B0B]/50 rounded-md border border-gray-800 hover:border-[#E1306C]/30 transition-colors group/metric">
                      <Heart className="h-4 w-4 text-gray-500 group-hover/metric:text-[#E1306C] transition-colors" />
                      <span className="font-mono text-gray-400 group-hover/metric:text-[#E1306C] transition-colors">
                        {formatNumber(post.likes)}
                      </span>
                    </div>

                    {/* Comments */}
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-[#0B0B0B]/50 rounded-md border border-gray-800 hover:border-[#833AB4]/30 transition-colors group/metric">
                      <MessageCircle className="h-4 w-4 text-gray-500 group-hover/metric:text-[#833AB4] transition-colors" />
                      <span className="font-mono text-gray-400 group-hover/metric:text-[#833AB4] transition-colors">
                        {formatNumber(post.comments)}
                      </span>
                    </div>

                    {/* Total engagement */}
                    <div className="ml-auto flex items-center gap-2 px-4 py-1.5 bg-gradient-to-r from-[#E1306C]/10 to-[#833AB4]/10 rounded-md border border-[#E1306C]/20">
                      <Activity className="h-4 w-4 text-[#E1306C]" />
                      <span className="font-mono text-white font-bold text-sm">
                        {formatNumber(post.engagement || 0)}
                      </span>
                      <span className="text-xs text-gray-500 font-mono">ETK</span>
                    </div>
                  </div>
                </div>

                {/* Bottom accent line */}
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-[#E1306C]/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
