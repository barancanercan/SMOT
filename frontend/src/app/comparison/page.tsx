"use client";

import { useState, useMemo, useRef, useEffect } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  api,
  User,
  PaginatedResponse,
  ComparisonResponse,
  ComparisonLLMResponse,
  PartyComparisonResponse,
  PartyComparisonLLMResponse,
  WeeklyTopTweetsResponse,
  RecentTweetsResponse,
  TweetItem,
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
  Repeat2,
  Eye,
  BarChart3,
  Brain,
  Search,
  Building2,
  Calendar,
  Clock,
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

const formatNumber = (num: number) => {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
  if (num >= 1000) return (num / 1000).toFixed(1) + "K";
  return num.toLocaleString("tr-TR");
};

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

// Tweet Card Component
const TweetCard = ({ tweet, showUser = true }: { tweet: TweetItem; showUser?: boolean }) => (
  <div className="bg-[#0B0B0B] rounded-lg border border-white/5 p-4 hover:border-white/10 transition-all">
    {showUser && (
      <div className="flex items-center gap-2 mb-2">
        <span className="text-blue-400 font-mono text-sm">@{tweet.username}</span>
        <span
          className="px-2 py-0.5 text-xs rounded-full"
          style={{
            backgroundColor: getPartyColor(tweet.party) + "30",
            color: getPartyColor(tweet.party),
          }}
        >
          {tweet.party}
        </span>
      </div>
    )}
    <p className="text-gray-300 text-sm mb-3 line-clamp-3">{tweet.tweet_text}</p>
    <div className="flex items-center justify-between text-xs text-gray-500">
      <div className="flex items-center gap-3">
        <span className="flex items-center gap-1">
          <Heart className="w-3 h-3 text-red-400" />
          {formatNumber(tweet.likes)}
        </span>
        <span className="flex items-center gap-1">
          <Repeat2 className="w-3 h-3 text-green-400" />
          {formatNumber(tweet.retweets)}
        </span>
        <span className="flex items-center gap-1">
          <Eye className="w-3 h-3 text-blue-400" />
          {formatNumber(tweet.views)}
        </span>
      </div>
      <span className="flex items-center gap-1">
        <Clock className="w-3 h-3" />
        {tweet.tweet_date?.split("T")[0] || "-"}
      </span>
    </div>
  </div>
);

export default function ComparisonPage() {
  const [activeTab, setActiveTab] = useState<"party" | "user">("party");
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [selectedParties, setSelectedParties] = useState<string[]>([]);
  const [comparisonData, setComparisonData] = useState<ComparisonResponse | null>(null);
  const [partyComparisonData, setPartyComparisonData] = useState<PartyComparisonResponse | null>(null);
  const [analysisText, setAnalysisText] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const searchInputRef = useRef<HTMLInputElement>(null);
  const toast = useToast();

  // Fetch users list
  const { data: usersData, isLoading: usersLoading } = useQuery({
    queryKey: ["users", "all"],
    queryFn: () => api.get<PaginatedResponse<User>>("/users/?page_size=100"),
    staleTime: 5 * 60 * 1000,
  });

  const users = usersData?.items || [];

  // Get unique parties
  const parties = useMemo(() => {
    const partySet = new Set(users.map((u) => u.party).filter(Boolean));
    return Array.from(partySet).sort();
  }, [users]);

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

  // Weekly top tweets query
  const { data: weeklyTopTweets, refetch: refetchWeeklyTop } = useQuery({
    queryKey: ["weekly-top-tweets", activeTab, selectedParties, selectedUsers],
    queryFn: () => {
      if (activeTab === "party" && selectedParties.length > 0) {
        return api.get<WeeklyTopTweetsResponse>(`/analytics/tweets/weekly-top?party=${selectedParties[0]}&limit=5`);
      } else if (activeTab === "user" && selectedUsers.length > 0) {
        return api.get<WeeklyTopTweetsResponse>(`/analytics/tweets/weekly-top?username=${selectedUsers[0]}&limit=5`);
      }
      return api.get<WeeklyTopTweetsResponse>("/analytics/tweets/weekly-top?limit=5");
    },
    enabled: (activeTab === "party" && selectedParties.length > 0) || (activeTab === "user" && selectedUsers.length > 0),
  });

  // Top 5 tweets query for first selection (by engagement)
  const { data: partyTopTweets1, refetch: refetchPartyTop1 } = useQuery({
    queryKey: ["party-top-tweets-1", activeTab, selectedParties[0], selectedUsers[0]],
    queryFn: () => {
      if (activeTab === "party" && selectedParties.length > 0) {
        return api.get<RecentTweetsResponse>(`/analytics/tweets/top?party=${encodeURIComponent(selectedParties[0])}&limit=5`);
      } else if (activeTab === "user" && selectedUsers.length > 0) {
        return api.get<RecentTweetsResponse>(`/analytics/tweets/top?username=${selectedUsers[0]}&limit=5`);
      }
      return null;
    },
    enabled: (activeTab === "party" && selectedParties.length > 0) || (activeTab === "user" && selectedUsers.length > 0),
  });

  // Top 5 tweets query for second selection (by engagement)
  const { data: partyTopTweets2, refetch: refetchPartyTop2 } = useQuery({
    queryKey: ["party-top-tweets-2", activeTab, selectedParties[1], selectedUsers[1]],
    queryFn: () => {
      if (activeTab === "party" && selectedParties.length > 1) {
        return api.get<RecentTweetsResponse>(`/analytics/tweets/top?party=${encodeURIComponent(selectedParties[1])}&limit=5`);
      } else if (activeTab === "user" && selectedUsers.length > 1) {
        return api.get<RecentTweetsResponse>(`/analytics/tweets/top?username=${selectedUsers[1]}&limit=5`);
      }
      return null;
    },
    enabled: (activeTab === "party" && selectedParties.length > 1) || (activeTab === "user" && selectedUsers.length > 1),
  });

  // User compare mutation
  const compareMutation = useMutation({
    mutationFn: (usernames: string[]) =>
      api.post<ComparisonResponse>("/analytics/compare", { usernames }),
    onSuccess: (data) => {
      setComparisonData(data);
      setAnalysisText("");
      toast.success("Karsilastirma tamamlandi");
      refetchWeeklyTop();
      refetchPartyTop1();
      refetchPartyTop2();
    },
    onError: (error: Error) => {
      toast.error(`Karsilastirma basarisiz: ${error.message}`);
    },
  });

  // User compare with LLM
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

  // Party compare mutation
  const partyCompareMutation = useMutation({
    mutationFn: (partyList: string[]) =>
      api.post<PartyComparisonResponse>("/analytics/parties/compare", { parties: partyList }),
    onSuccess: (data) => {
      setPartyComparisonData(data);
      setAnalysisText("");
      toast.success("Parti karsilastirmasi tamamlandi");
      refetchWeeklyTop();
      refetchPartyTop1();
      refetchPartyTop2();
    },
    onError: (error: Error) => {
      toast.error(`Parti karsilastirmasi basarisiz: ${error.message}`);
    },
  });

  // Party compare with LLM
  const partyCompareLLMMutation = useMutation({
    mutationFn: (partyList: string[]) =>
      api.post<PartyComparisonLLMResponse>("/analytics/parties/compare/llm", { parties: partyList }),
    onSuccess: (data) => {
      setPartyComparisonData({ parties: data.parties });
      setAnalysisText(data.analysis);
      toast.success("AI parti analizi tamamlandi");
    },
    onError: (error: Error) => {
      toast.error(`AI parti analizi basarisiz: ${error.message}`);
    },
  });

  const isComparing =
    compareMutation.isPending ||
    compareLLMMutation.isPending ||
    partyCompareMutation.isPending ||
    partyCompareLLMMutation.isPending;

  const toggleUserSelection = (username: string) => {
    setSelectedUsers((prev) =>
      prev.includes(username)
        ? prev.filter((u) => u !== username)
        : prev.length < 10
        ? [...prev, username]
        : prev
    );
  };

  const togglePartySelection = (party: string) => {
    setSelectedParties((prev) =>
      prev.includes(party)
        ? prev.filter((p) => p !== party)
        : prev.length < 10
        ? [...prev, party]
        : prev
    );
  };

  const handleCompare = () => {
    if (activeTab === "user") {
      if (selectedUsers.length < 2) {
        toast.error("En az 2 kullanici secmelisiniz");
        return;
      }
      compareMutation.mutate(selectedUsers);
    } else {
      if (selectedParties.length < 2) {
        toast.error("En az 2 parti secmelisiniz");
        return;
      }
      partyCompareMutation.mutate(selectedParties);
    }
  };

  const handleCompareWithLLM = () => {
    if (activeTab === "user") {
      if (selectedUsers.length < 2) {
        toast.error("En az 2 kullanici secmelisiniz");
        return;
      }
      compareLLMMutation.mutate(selectedUsers);
    } else {
      if (selectedParties.length < 2) {
        toast.error("En az 2 parti secmelisiniz");
        return;
      }
      partyCompareLLMMutation.mutate(selectedParties);
    }
  };

  const clearSelection = () => {
    if (activeTab === "user") {
      setSelectedUsers([]);
      setComparisonData(null);
    } else {
      setSelectedParties([]);
      setPartyComparisonData(null);
    }
    setAnalysisText("");
  };

  // Chart data
  const userBarChartData = comparisonData?.users.map((u) => ({
    name: `@${u.username}`,
    Takipci: u.followers,
    Tweet: u.tweet_count,
    Like: u.total_likes,
    RT: u.total_retweets,
    party: u.party,
  })) || [];

  const partyBarChartData = partyComparisonData?.parties.map((p) => ({
    name: p.party,
    Takipci: p.total_followers,
    Tweet: p.tweet_count,
    Like: p.total_likes,
    RT: p.total_retweets,
    Uye: p.member_count,
  })) || [];

  return (
    <div className="min-h-screen bg-[#0B0B0B] text-white">
      <div className="fixed inset-0 bg-[url('/grid.svg')] opacity-5 pointer-events-none" />
      <div className="fixed inset-0 bg-gradient-to-br from-purple-500/5 via-transparent to-blue-500/5 pointer-events-none" />

      <div className="relative max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="relative mb-8 p-8 rounded-2xl bg-gradient-to-br from-[#1A1A1A] via-[#151515] to-[#0F0F0F] border border-white/10 overflow-hidden shadow-2xl">
          <div className="flex items-center justify-between flex-wrap gap-4">
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
                {activeTab === "party" ? "Parti Karsilastirma" : "Uye Karsilastirma"}
              </h1>
              <p className="text-gray-500 text-sm">
                {activeTab === "party"
                  ? "Partileri yan yana karsilastirin ve AI analizi yapin"
                  : "Meclis uyelerini yan yana karsilastirin ve AI analizi yapin"}
              </p>
            </div>

            {/* Tab Buttons */}
            <div className="flex bg-[#0B0B0B] rounded-xl p-1 border border-white/10">
              <button
                onClick={() => {
                  setActiveTab("party");
                  setComparisonData(null);
                  setAnalysisText("");
                }}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg transition-all ${
                  activeTab === "party"
                    ? "bg-purple-600 text-white"
                    : "text-gray-400 hover:text-white"
                }`}
              >
                <Building2 className="w-4 h-4" />
                Parti
              </button>
              <button
                onClick={() => {
                  setActiveTab("user");
                  setPartyComparisonData(null);
                  setAnalysisText("");
                }}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg transition-all ${
                  activeTab === "user"
                    ? "bg-purple-600 text-white"
                    : "text-gray-400 hover:text-white"
                }`}
              >
                <Users className="w-4 h-4" />
                Uye
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Selection Panel */}
          <div className="lg:col-span-1">
            <div className="bg-[#1A1A1A]/80 backdrop-blur-xl rounded-xl border border-white/10 p-6 sticky top-8">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                {activeTab === "party" ? (
                  <>
                    <Building2 className="h-5 w-5 text-purple-400" />
                    Parti Sec ({selectedParties.length}/10)
                  </>
                ) : (
                  <>
                    <Users className="h-5 w-5 text-purple-400" />
                    Kullanici Sec ({selectedUsers.length}/10)
                  </>
                )}
              </h3>

              {activeTab === "user" && (
                <div className="relative mb-3">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Search className="h-4 w-4 text-gray-500" />
                  </div>
                  <input
                    ref={searchInputRef}
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Ara..."
                    className="w-full pl-10 pr-4 py-2 bg-[#0B0B0B] border border-white/10 rounded-lg text-white font-mono text-sm focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20 transition-all placeholder:text-gray-600"
                  />
                </div>
              )}

              <div className="max-h-64 overflow-y-auto space-y-1 mb-4">
                {activeTab === "party" ? (
                  parties.map((party) => (
                    <label
                      key={party}
                      className={`flex items-center gap-3 p-2.5 rounded-lg cursor-pointer transition-all ${
                        selectedParties.includes(party)
                          ? "bg-purple-500/20 border border-purple-500/30"
                          : "hover:bg-white/5"
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selectedParties.includes(party)}
                        onChange={() => togglePartySelection(party)}
                        className="w-4 h-4 rounded border-white/20 bg-[#0B0B0B] text-purple-500"
                      />
                      <span
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: getPartyColor(party) }}
                      />
                      <span className="text-white">{party}</span>
                      <span className="text-xs text-gray-500 ml-auto">
                        {users.filter((u) => u.party === party).length} uye
                      </span>
                    </label>
                  ))
                ) : usersLoading ? (
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
                        className="w-4 h-4 rounded border-white/20 bg-[#0B0B0B] text-purple-500"
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
                  disabled={isComparing || (activeTab === "user" ? selectedUsers.length < 2 : selectedParties.length < 2)}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-purple-600 to-purple-500 text-white rounded-xl hover:from-purple-500 hover:to-purple-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium"
                >
                  <BarChart3 className={`h-5 w-5 ${isComparing ? "animate-pulse" : ""}`} />
                  {isComparing ? "Karsilastiriliyor..." : "Karsilastir"}
                </button>

                <button
                  onClick={handleCompareWithLLM}
                  disabled={isComparing || (activeTab === "user" ? selectedUsers.length < 2 : selectedParties.length < 2)}
                  className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-xl hover:from-blue-500 hover:to-blue-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium"
                >
                  <Sparkles className={`h-5 w-5 ${isComparing ? "animate-spin" : ""}`} />
                  {isComparing ? "Analiz Ediliyor..." : "AI Analizi"}
                </button>

                {(selectedUsers.length > 0 || selectedParties.length > 0) && (
                  <button
                    onClick={clearSelection}
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
            {/* Empty State */}
            {!comparisonData && !partyComparisonData && !isComparing && (
              <div className="bg-[#1A1A1A]/80 backdrop-blur-xl rounded-xl border border-white/10 p-12 text-center">
                <GitCompare className="w-16 h-16 text-purple-400/50 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">Karsilastirma Bekliyor</h3>
                <p className="text-gray-500">
                  {activeTab === "party"
                    ? "En az 2 parti secin ve karsilastir butonuna basin"
                    : "En az 2 kullanici secin ve karsilastir butonuna basin"}
                </p>
              </div>
            )}

            {/* Loading State */}
            {isComparing && (
              <div className="bg-[#1A1A1A]/80 backdrop-blur-xl rounded-xl border border-white/10 p-12 text-center">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full border-2 border-purple-500 border-t-transparent animate-spin" />
                <p className="text-white font-semibold">Karsilastirma Yapiliyor...</p>
              </div>
            )}

            {/* Party Comparison Results */}
            {activeTab === "party" && partyComparisonData && !isComparing && (
              <>
                {/* Party Cards */}
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  {partyComparisonData.parties.map((party) => (
                    <div
                      key={party.party}
                      className="bg-[#1A1A1A]/80 backdrop-blur-xl rounded-xl border border-white/10 p-4"
                    >
                      <div className="flex items-center gap-2 mb-3">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: getPartyColor(party.party) }}
                        />
                        <span className="text-white font-semibold">{party.party}</span>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-500">Uye</span>
                          <span className="text-white font-mono">{party.member_count}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Takipci</span>
                          <span className="text-white font-mono">{formatNumber(party.total_followers)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Tweet</span>
                          <span className="text-white font-mono">{formatNumber(party.tweet_count)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Etkilesim</span>
                          <span className="text-emerald-400 font-mono">{party.engagement_rate}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Party Bar Chart */}
                <div className="bg-[#1A1A1A]/80 backdrop-blur-xl rounded-xl border border-white/10 p-6">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-purple-400" />
                    Parti Metrikleri
                  </h3>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={partyBarChartData} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                        <XAxis type="number" tick={{ fontSize: 12, fill: "#9CA3AF" }} tickFormatter={formatNumber} />
                        <YAxis type="category" dataKey="name" tick={{ fontSize: 12, fill: "#9CA3AF" }} width={100} />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend />
                        <Bar dataKey="Takipci" fill="#8B5CF6" radius={[0, 4, 4, 0]} />
                        <Bar dataKey="Tweet" fill="#3B82F6" radius={[0, 4, 4, 0]} />
                        <Bar dataKey="Like" fill="#EF4444" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </>
            )}

            {/* User Comparison Results */}
            {activeTab === "user" && comparisonData && !isComparing && (
              <>
                {/* User Cards */}
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
                        <div className="flex justify-between">
                          <span className="text-xs text-gray-500">Takipci</span>
                          <span className="text-white font-mono">{formatNumber(user.followers)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-xs text-gray-500">Tweet</span>
                          <span className="text-white font-mono">{formatNumber(user.tweet_count)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-xs text-gray-500">Etkilesim</span>
                          <span className="text-emerald-400 font-mono">{user.engagement_rate.toFixed(1)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* User Bar Chart */}
                <div className="bg-[#1A1A1A]/80 backdrop-blur-xl rounded-xl border border-white/10 p-6">
                  <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-purple-400" />
                    Metrik Karsilastirmasi
                  </h3>
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={userBarChartData} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                        <XAxis type="number" tick={{ fontSize: 12, fill: "#9CA3AF" }} tickFormatter={formatNumber} />
                        <YAxis type="category" dataKey="name" tick={{ fontSize: 12, fill: "#9CA3AF" }} width={100} />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend />
                        <Bar dataKey="Takipci" fill="#8B5CF6" radius={[0, 4, 4, 0]} />
                        <Bar dataKey="Tweet" fill="#3B82F6" radius={[0, 4, 4, 0]} />
                        <Bar dataKey="Like" fill="#EF4444" radius={[0, 4, 4, 0]} />
                        <Bar dataKey="RT" fill="#10B981" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </>
            )}

            {/* Top 5 Weekly Tweets */}
            {weeklyTopTweets?.tweets && weeklyTopTweets.tweets.length > 0 && (comparisonData || partyComparisonData) && (
              <div className="bg-[#1A1A1A]/80 backdrop-blur-xl rounded-xl border border-white/10 overflow-hidden">
                <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent">
                  <div className="flex items-center gap-3">
                    <Calendar className="h-5 w-5 text-amber-400" />
                    <span className="text-white font-semibold">Bu Haftanin Top 5 Tweeti</span>
                  </div>
                  <span className="text-xs text-gray-500 font-mono">{weeklyTopTweets.period}</span>
                </div>
                <div className="p-4 space-y-3">
                  {weeklyTopTweets.tweets.map((tweet, idx) => (
                    <div key={tweet.id} className="flex gap-3">
                      <span className="text-2xl font-bold text-amber-400/50 w-8">#{idx + 1}</span>
                      <div className="flex-1">
                        <TweetCard tweet={tweet} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Top 5 Tweets - Side by Side for Party Comparison */}
            {activeTab === "party" && partyComparisonData && (partyTopTweets1?.tweets || partyTopTweets2?.tweets) && (
              <div className="bg-[#1A1A1A]/80 backdrop-blur-xl rounded-xl border border-white/10 overflow-hidden">
                <div className="flex items-center gap-3 px-6 py-4 border-b border-white/10 bg-gradient-to-r from-orange-500/10 via-orange-500/5 to-transparent">
                  <TrendingUp className="h-5 w-5 text-orange-400" />
                  <span className="text-white font-semibold">Top 5 Tweet (Parti Bazli)</span>
                </div>
                <div className="grid md:grid-cols-2 gap-4 p-4">
                  {/* First Party */}
                  {selectedParties[0] && (
                    <div className="space-y-3">
                      <div className="flex items-center gap-2 mb-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: getPartyColor(selectedParties[0]) }}
                        />
                        <span className="text-white font-semibold">{selectedParties[0]}</span>
                      </div>
                      {partyTopTweets1?.tweets && partyTopTweets1.tweets.length > 0 ? (
                        partyTopTweets1.tweets.map((tweet, idx) => (
                          <div key={tweet.id} className="flex gap-2">
                            <span className="text-lg font-bold text-orange-400/50 w-6">#{idx + 1}</span>
                            <div className="flex-1">
                              <TweetCard tweet={tweet} />
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="text-gray-500 text-sm text-center py-4">Tweet bulunamadi</div>
                      )}
                    </div>
                  )}
                  {/* Second Party */}
                  {selectedParties[1] && (
                    <div className="space-y-3">
                      <div className="flex items-center gap-2 mb-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: getPartyColor(selectedParties[1]) }}
                        />
                        <span className="text-white font-semibold">{selectedParties[1]}</span>
                      </div>
                      {partyTopTweets2?.tweets && partyTopTweets2.tweets.length > 0 ? (
                        partyTopTweets2.tweets.map((tweet, idx) => (
                          <div key={tweet.id} className="flex gap-2">
                            <span className="text-lg font-bold text-orange-400/50 w-6">#{idx + 1}</span>
                            <div className="flex-1">
                              <TweetCard tweet={tweet} />
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="text-gray-500 text-sm text-center py-4">Tweet bulunamadi</div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Top 5 Tweets - for User Comparison */}
            {activeTab === "user" && comparisonData && partyTopTweets1?.tweets && partyTopTweets1.tweets.length > 0 && (
              <div className="bg-[#1A1A1A]/80 backdrop-blur-xl rounded-xl border border-white/10 overflow-hidden">
                <div className="flex items-center gap-3 px-6 py-4 border-b border-white/10 bg-gradient-to-r from-orange-500/10 via-orange-500/5 to-transparent">
                  <TrendingUp className="h-5 w-5 text-orange-400" />
                  <span className="text-white font-semibold">Top 5 Tweet</span>
                </div>
                <div className="p-4 space-y-3">
                  {partyTopTweets1.tweets.map((tweet, idx) => (
                    <div key={tweet.id} className="flex gap-3">
                      <span className="text-xl font-bold text-orange-400/50 w-8">#{idx + 1}</span>
                      <div className="flex-1">
                        <TweetCard tweet={tweet} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

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
          </div>
        </div>
      </div>
    </div>
  );
}
