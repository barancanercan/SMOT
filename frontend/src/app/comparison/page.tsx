"use client";

import { useState, useMemo, useRef, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  api,
  User,
  PaginatedResponse,
  ComparisonResponse,
  ComparisonLLMResponse,
} from "@/lib/api";
import { useToast } from "@/components/ui/toast";
import { MarkdownRenderer } from "@/components/ui/markdown-renderer";
import {
  GitCompare,
  Users,
  RefreshCw,
  AlertCircle,
  Sparkles,
  TrendingUp,
  Heart,
  MessageCircle,
  Eye,
  BarChart3,
  Brain,
  Search,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from "recharts";

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

// Format numbers for display
const formatNumber = (num: number) => {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
  if (num >= 1000) return (num / 1000).toFixed(1) + "K";
  return num.toLocaleString("tr-TR");
};

// Custom tooltip for charts
const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload || !payload.length) return null;

  return (
    <div className="bg-[#1A1A1A] border border-white/20 rounded-lg px-4 py-3 shadow-xl">
      <p className="text-white font-semibold mb-2">{label}</p>
      {payload.map((entry: any, index: number) => (
        <p key={index} className="text-gray-300 text-sm">
          <span style={{ color: entry.fill || entry.stroke }}>{entry.name}:</span>{" "}
          <span className="font-mono">{formatNumber(entry.value)}</span>
        </p>
      ))}
    </div>
  );
};

export default function ComparisonPage() {
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [comparisonData, setComparisonData] = useState<ComparisonResponse | null>(null);
  const [analysisText, setAnalysisText] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const searchInputRef = useRef<HTMLInputElement>(null);
  const toast = useToast();

  // Fetch users list
  const {
    data: usersData,
    isLoading: usersLoading,
    error: usersError,
  } = useQuery({
    queryKey: ["users", "all"],
    queryFn: () => api.get<PaginatedResponse<User>>("/users/?page_size=100"),
    staleTime: 5 * 60 * 1000,
  });

  const users = usersData?.items || [];

  // Filter users by search
  const filteredUsers = useMemo(() => {
    if (!searchQuery) return users;
    const query = searchQuery.toLowerCase();
    return users.filter(
      (u) =>
        u.username.toLowerCase().includes(query) ||
        u.name.toLowerCase().includes(query) ||
        u.party?.toLowerCase().includes(query)
    );
  }, [users, searchQuery]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (document.activeElement?.tagName === "INPUT" || document.activeElement?.tagName === "TEXTAREA") {
        return;
      }
      if (e.key.length === 1 && /[a-zA-Z]/.test(e.key)) {
        setSearchQuery(e.key.toLowerCase());
        searchInputRef.current?.focus();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Compare mutation
  const compareMutation = useMutation({
    mutationFn: (usernames: string[]) =>
      api.post<ComparisonResponse>("/analytics/compare", { usernames }),
    onSuccess: (data) => {
      setComparisonData(data);
      setAnalysisText("");
      toast.success("Karsilastirma tamamlandi");
    },
    onError: (error: Error) => {
      toast.error(`Karsilastirma basarisiz: ${error.message}`);
    },
  });

  // Compare with LLM mutation
  const compareLLMMutation = useMutation({
    mutationFn: (usernames: string[]) =>
      api.post<ComparisonLLMResponse>("/analytics/compare/llm", { usernames }),
    onSuccess: (data) => {
      setComparisonData({ users: data.users });
      setAnalysisText(data.analysis);
      toast.success("AI analizi tamamlandi");
    },
    onError: (error: Error) => {
      toast.error(`AI analizi basarisiz: ${error.message}`);
    },
  });

  const isComparing = compareMutation.isPending || compareLLMMutation.isPending;

  const toggleUserSelection = (username: string) => {
    setSelectedUsers((prev) =>
      prev.includes(username)
        ? prev.filter((u) => u !== username)
        : prev.length < 10
        ? [...prev, username]
        : prev
    );
  };

  const handleCompare = () => {
    if (selectedUsers.length < 2) {
      toast.error("En az 2 kullanici secmelisiniz");
      return;
    }
    compareMutation.mutate(selectedUsers);
  };

  const handleCompareWithLLM = () => {
    if (selectedUsers.length < 2) {
      toast.error("En az 2 kullanici secmelisiniz");
      return;
    }
    if (selectedUsers.length > 10) {
      toast.error("Maksimum 10 kullanici secilebilir");
      return;
    }
    compareLLMMutation.mutate(selectedUsers);
  };

  // Prepare chart data
  const barChartData = comparisonData?.users.map((u) => ({
    name: `@${u.username}`,
    Takipci: u.followers,
    Tweet: u.tweet_count,
    Like: u.total_likes,
    RT: u.total_retweets,
    party: u.party,
  })) || [];

  // Prepare radar chart data (normalized)
  const radarChartData = comparisonData ? (() => {
    const maxFollowers = Math.max(...comparisonData.users.map(u => u.followers)) || 1;
    const maxTweets = Math.max(...comparisonData.users.map(u => u.tweet_count)) || 1;
    const maxLikes = Math.max(...comparisonData.users.map(u => u.total_likes)) || 1;
    const maxRetweets = Math.max(...comparisonData.users.map(u => u.total_retweets)) || 1;
    const maxEngagement = Math.max(...comparisonData.users.map(u => u.engagement_rate)) || 1;

    return [
      { metric: "Takipci", ...Object.fromEntries(comparisonData.users.map(u => [u.username, (u.followers / maxFollowers) * 100])) },
      { metric: "Tweet", ...Object.fromEntries(comparisonData.users.map(u => [u.username, (u.tweet_count / maxTweets) * 100])) },
      { metric: "Like", ...Object.fromEntries(comparisonData.users.map(u => [u.username, (u.total_likes / maxLikes) * 100])) },
      { metric: "RT", ...Object.fromEntries(comparisonData.users.map(u => [u.username, (u.total_retweets / maxRetweets) * 100])) },
      { metric: "Etkilesim", ...Object.fromEntries(comparisonData.users.map(u => [u.username, (u.engagement_rate / maxEngagement) * 100])) },
    ];
  })() : [];

  if (usersError) {
    return (
      <div className="min-h-screen bg-[#0B0B0B] text-white p-8">
        <div className="max-w-6xl mx-auto">
          <div className="bg-[#1A1A1A]/80 rounded-2xl border border-red-500/30 p-12 text-center">
            <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-2">Sistem Hatasi</h2>
            <p className="text-gray-400 mb-4">Kullanicilar yuklenemedi</p>
            <button
              onClick={() => window.location.reload()}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl"
            >
              <RefreshCw className="inline-block h-4 w-4 mr-2" />
              Yeniden Dene
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B0B0B] text-white">
      <div className="fixed inset-0 bg-[url('/grid.svg')] opacity-5 pointer-events-none" />
      <div className="fixed inset-0 bg-gradient-to-br from-purple-500/5 via-transparent to-blue-500/5 pointer-events-none" />

      <div className="relative max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="relative mb-8 p-8 rounded-2xl bg-gradient-to-br from-[#1A1A1A] via-[#151515] to-[#0F0F0F] border border-white/10 overflow-hidden shadow-2xl">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2.5 rounded-xl bg-gradient-to-br from-purple-500/20 to-purple-600/10 border border-purple-500/30">
                  <GitCompare className="h-6 w-6 text-purple-400" />
                </div>
                <span className="text-xs font-mono text-purple-400 tracking-wider uppercase">
                  Karsilastirma Modulu
                </span>
              </div>
              <h1 className="text-3xl font-bold text-white mb-2">
                Kullanici Karsilastirma
              </h1>
              <p className="text-gray-500 text-sm">
                Birden fazla kullaniciyi yan yana karsilastirin ve AI analizi yapin
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* User Selection Panel */}
          <div className="lg:col-span-1">
            <div className="bg-[#1A1A1A]/80 backdrop-blur-xl rounded-xl border border-white/10 p-6 sticky top-8">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Users className="h-5 w-5 text-purple-400" />
                Kullanici Sec ({selectedUsers.length}/10)
              </h3>

              {/* Search input */}
              <div className="relative mb-3">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Search className="h-4 w-4 text-gray-500" />
                </div>
                <input
                  ref={searchInputRef}
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Ara... (harf tuslayin)"
                  className="w-full pl-10 pr-4 py-2 bg-[#0B0B0B] border border-white/10 rounded-lg text-white font-mono text-sm focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20 transition-all placeholder:text-gray-600"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery("")}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-500 hover:text-white"
                  >
                    ×
                  </button>
                )}
              </div>

              {searchQuery && (
                <p className="text-xs text-gray-500 mb-2 font-mono">
                  {filteredUsers.length} sonuc bulundu
                </p>
              )}

              <div className="max-h-64 overflow-y-auto space-y-1 mb-4">
                {usersLoading ? (
                  <div className="py-8 text-center">
                    <div className="w-8 h-8 mx-auto mb-2 rounded-full border-2 border-purple-500 border-t-transparent animate-spin" />
                    <p className="text-gray-500 text-sm">Yukleniyor...</p>
                  </div>
                ) : (
                  filteredUsers.map((user) => (
                    <label
                      key={user.username}
                      className={`flex items-center gap-3 p-2.5 rounded-lg cursor-pointer transition-all ${
                        selectedUsers.includes(user.username)
                          ? "bg-purple-500/20 border border-purple-500/30"
                          : "hover:bg-white/5"
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedUsers.includes(user.username)}
                        onChange={() => toggleUserSelection(user.username)}
                        className="w-4 h-4 rounded border-white/20 bg-[#0B0B0B] text-purple-500 focus:ring-purple-500/20"
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-white truncate">
                          <span className="text-blue-400 font-mono">@{user.username}</span>
                        </p>
                        <p className="text-xs text-gray-500 truncate">{user.name}</p>
                      </div>
                      <span
                        className="px-2 py-0.5 text-xs rounded-full"
                        style={{
                          backgroundColor: getPartyColor(user.party) + "30",
                          color: getPartyColor(user.party),
                        }}
                      >
                        {user.party}
                      </span>
                    </label>
                  ))
                )}
              </div>

              <div className="space-y-2">
                <button
                  onClick={handleCompare}
                  disabled={isComparing || selectedUsers.length < 2}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-purple-600 to-purple-500 text-white rounded-xl hover:from-purple-500 hover:to-purple-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium"
                >
                  <BarChart3 className={`h-5 w-5 ${isComparing ? "animate-pulse" : ""}`} />
                  {isComparing ? "Karsilastiriliyor..." : "Karsilastir"}
                </button>

                <button
                  onClick={handleCompareWithLLM}
                  disabled={isComparing || selectedUsers.length < 2}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-xl hover:from-blue-500 hover:to-blue-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium"
                  title={selectedUsers.length < 2 ? "AI karsilastirma icin en az 2 kullanici secin" : ""}
                >
                  <Sparkles className={`h-5 w-5 ${isComparing ? "animate-spin" : ""}`} />
                  {isComparing ? "Analiz Ediliyor..." : selectedUsers.length >= 2 ? `AI Karsilastirma (${selectedUsers.length} Kullanici)` : "En az 2 Kullanici Sec"}
                </button>

                {selectedUsers.length > 0 && (
                  <button
                    onClick={() => {
                      setSelectedUsers([]);
                      setComparisonData(null);
                      setAnalysisText("");
                    }}
                    className="w-full px-4 py-2 text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-all text-sm"
                  >
                    Secimi Temizle
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2 space-y-6">
            {!comparisonData && !isComparing && (
              <div className="bg-[#1A1A1A]/80 backdrop-blur-xl rounded-xl border border-white/10 p-12 text-center">
                <GitCompare className="w-16 h-16 text-purple-400/50 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">
                  Karsilastirma Bekliyor
                </h3>
                <p className="text-gray-500">
                  En az 2 kullanici secin ve karsilastir butonuna basin
                </p>
              </div>
            )}

            {isComparing && (
              <div className="bg-[#1A1A1A]/80 backdrop-blur-xl rounded-xl border border-white/10 p-12 text-center">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full border-2 border-purple-500 border-t-transparent animate-spin" />
                <p className="text-white font-semibold">Karsilastirma Yapiliyor...</p>
                <p className="text-gray-500 text-sm mt-2 font-mono">
                  {selectedUsers.length} kullanici analiz ediliyor
                </p>
              </div>
            )}

            {comparisonData && !isComparing && (
              <>
                {/* Metric Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {comparisonData.users.slice(0, 4).map((user) => (
                    <div
                      key={user.username}
                      className="bg-[#1A1A1A]/80 backdrop-blur-xl rounded-xl border border-white/10 p-4"
                    >
                      <div className="flex items-center gap-2 mb-3">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: getPartyColor(user.party) }}
                        />
                        <span className="text-blue-400 font-mono text-sm">@{user.username}</span>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-500">Takipci</span>
                          <span className="text-white font-mono">{formatNumber(user.followers)}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-500">Tweet</span>
                          <span className="text-white font-mono">{formatNumber(user.tweet_count)}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-500">Etkilesim</span>
                          <span className="text-emerald-400 font-mono">{user.engagement_rate.toFixed(1)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Bar Chart */}
                <div className="bg-[#1A1A1A]/80 backdrop-blur-xl rounded-xl border border-white/10 p-6">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-purple-400" />
                    Metrik Karsilastirmasi
                  </h3>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={barChartData} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                        <XAxis
                          type="number"
                          tick={{ fontSize: 12, fill: "#9CA3AF" }}
                          tickFormatter={formatNumber}
                          axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
                        />
                        <YAxis
                          type="category"
                          dataKey="name"
                          tick={{ fontSize: 12, fill: "#9CA3AF" }}
                          axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
                          width={100}
                        />
                        <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.05)" }} />
                        <Legend wrapperStyle={{ color: "#9CA3AF" }} />
                        <Bar dataKey="Takipci" fill="#8B5CF6" radius={[0, 4, 4, 0]} />
                        <Bar dataKey="Tweet" fill="#3B82F6" radius={[0, 4, 4, 0]} />
                        <Bar dataKey="Like" fill="#EF4444" radius={[0, 4, 4, 0]} />
                        <Bar dataKey="RT" fill="#10B981" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Radar Chart */}
                {radarChartData.length > 0 && comparisonData.users.length <= 5 && (
                  <div className="bg-[#1A1A1A]/80 backdrop-blur-xl rounded-xl border border-white/10 p-6">
                    <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                      <Brain className="h-5 w-5 text-blue-400" />
                      Cok Boyutlu Karsilastirma
                    </h3>
                    <div className="h-80">
                      <ResponsiveContainer width="100%" height="100%">
                        <RadarChart data={radarChartData}>
                          <PolarGrid stroke="rgba(255,255,255,0.1)" />
                          <PolarAngleAxis dataKey="metric" tick={{ fontSize: 12, fill: "#9CA3AF" }} />
                          <PolarRadiusAxis tick={{ fontSize: 10, fill: "#6B7280" }} domain={[0, 100]} />
                          {comparisonData.users.map((user, idx) => (
                            <Radar
                              key={user.username}
                              name={`@${user.username}`}
                              dataKey={user.username}
                              stroke={getPartyColor(user.party)}
                              fill={getPartyColor(user.party)}
                              fillOpacity={0.2}
                              strokeWidth={2}
                            />
                          ))}
                          <Legend wrapperStyle={{ color: "#9CA3AF" }} />
                          <Tooltip content={<CustomTooltip />} />
                        </RadarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}

                {/* Detailed Table */}
                <div className="bg-[#1A1A1A]/80 backdrop-blur-xl rounded-xl border border-white/10 overflow-hidden">
                  <div className="px-6 py-4 border-b border-white/10">
                    <h3 className="text-lg font-semibold text-white">Detayli Metrikler</h3>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-white/10 bg-[#0B0B0B]/50">
                          <th className="text-left py-3 px-4 text-xs font-semibold text-gray-400 uppercase">Kullanici</th>
                          <th className="text-left py-3 px-4 text-xs font-semibold text-gray-400 uppercase">Parti</th>
                          <th className="text-right py-3 px-4 text-xs font-semibold text-gray-400 uppercase">Takipci</th>
                          <th className="text-right py-3 px-4 text-xs font-semibold text-gray-400 uppercase">Tweet</th>
                          <th className="text-right py-3 px-4 text-xs font-semibold text-gray-400 uppercase">Like</th>
                          <th className="text-right py-3 px-4 text-xs font-semibold text-gray-400 uppercase">RT</th>
                          <th className="text-right py-3 px-4 text-xs font-semibold text-gray-400 uppercase">Etkilesim</th>
                        </tr>
                      </thead>
                      <tbody>
                        {comparisonData.users.map((user) => (
                          <tr key={user.username} className="border-b border-white/5 hover:bg-white/5">
                            <td className="py-3 px-4">
                              <span className="text-blue-400 font-mono">@{user.username}</span>
                              <p className="text-xs text-gray-500">{user.name}</p>
                            </td>
                            <td className="py-3 px-4">
                              <span
                                className="px-2 py-1 text-xs rounded-full"
                                style={{
                                  backgroundColor: getPartyColor(user.party) + "30",
                                  color: getPartyColor(user.party),
                                }}
                              >
                                {user.party}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-right text-white font-mono">{formatNumber(user.followers)}</td>
                            <td className="py-3 px-4 text-right text-white font-mono">{formatNumber(user.tweet_count)}</td>
                            <td className="py-3 px-4 text-right text-red-400 font-mono">{formatNumber(user.total_likes)}</td>
                            <td className="py-3 px-4 text-right text-green-400 font-mono">{formatNumber(user.total_retweets)}</td>
                            <td className="py-3 px-4 text-right text-purple-400 font-mono">{user.engagement_rate.toFixed(2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* LLM Analysis */}
                {analysisText && (
                  <div className="bg-[#1A1A1A]/80 backdrop-blur-xl rounded-xl border border-white/10 overflow-hidden">
                    <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-gradient-to-r from-blue-500/10 via-blue-500/5 to-transparent">
                      <div className="flex items-center gap-3">
                        <Sparkles className="h-5 w-5 text-blue-400" />
                        <span className="text-white font-semibold">AI Analiz Ozeti</span>
                      </div>
                      <div className="flex items-center gap-2 bg-blue-500/20 px-3 py-1 rounded-full border border-blue-500/30">
                        <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
                        <span className="text-blue-400 text-xs font-mono">Yapay Zeka</span>
                      </div>
                    </div>
                    <div className="p-6">
                      <MarkdownRenderer content={analysisText} />
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
