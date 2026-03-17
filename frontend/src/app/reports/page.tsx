"use client";

import { useState, useMemo } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api, User, ReportResponse, PartyReportResponse, PaginatedResponse } from "@/lib/api";
import { useToast } from "@/components/ui/toast";
import { MarkdownRenderer } from "@/components/ui/markdown-renderer";
import {
  FileText,
  Download,
  RefreshCw,
  Users,
  AlertCircle,
  Sparkles,
  Zap,
  Shield,
  Target,
  Brain,
  Activity,
  Lock,
  TrendingUp,
  FileDown
} from "lucide-react";

type ReportMode = "user" | "party" | "multi";

export default function ReportsPage() {
  const [mode, setMode] = useState<ReportMode>("user");
  const [selectedUser, setSelectedUser] = useState<string>("");
  const [selectedParty, setSelectedParty] = useState<string>("");
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [report, setReport] = useState<string>("");
  const [useLLM, setUseLLM] = useState<boolean>(true);
  const [partyLLM, setPartyLLM] = useState<boolean>(false);
  const toast = useToast();

  // Fetch users with React Query
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

  // Parti normalizasyon fonksiyonu
  const normalizeParty = (party: string): string => {
    const aliases: Record<string, string> = {
      "Cumhuriyet Halk Partisi": "CHP",
      "cumhuriyet halk partisi": "CHP",
      "Adalet ve Kalkınma Partisi": "AK Parti",
      "AKP": "AK Parti",
      "akp": "AK Parti",
      "Milliyetçi Hareket Partisi": "MHP",
      "İYİ": "İYİ Parti",
      "IYI Parti": "İYİ Parti",
      "HDP": "DEM Parti",
      "Halkların Demokratik Partisi": "DEM Parti",
    };
    return aliases[party] || party;
  };

  // Extract unique parties with normalization
  const parties = useMemo(() => {
    const normalized = users.map((u) => normalizeParty(u.party)).filter(Boolean);
    return Array.from(new Set(normalized)).sort();
  }, [users]);

  // Set default selections
  useMemo(() => {
    if (users.length > 0 && !selectedUser) {
      setSelectedUser(users[0].username);
    }
    if (parties.length > 0 && !selectedParty) {
      setSelectedParty(parties[0]);
    }
  }, [users, parties, selectedUser, selectedParty]);

  // User report mutation
  const userReportMutation = useMutation({
    mutationFn: (data: { username: string; use_llm: boolean }) =>
      api.post<ReportResponse>("/reports/generate", {
        username: data.username,
        use_llm: data.use_llm,
        force_refresh: true,
      }),
    onSuccess: (data) => {
      setReport(data.content || data.report || "");
      toast.success("Rapor basariyla olusturuldu");
    },
    onError: (error: Error) => {
      toast.error(`Rapor olusturulamadi: ${error.message}`);
    },
  });

  // Party report mutation
  const partyReportMutation = useMutation({
    mutationFn: (data: { party: string; use_llm: boolean }) =>
      api.post<PartyReportResponse>("/reports/party", {
        party: data.party,
        use_llm: data.use_llm,
      }),
    onSuccess: (data) => {
      setReport(data.content);
      toast.success("Parti raporu basariyla olusturuldu");
    },
    onError: (error: Error) => {
      toast.error(`Parti raporu olusturulamadi: ${error.message}`);
    },
  });

  // Multi-user report mutation
  const multiUserReportMutation = useMutation({
    mutationFn: (data: { usernames: string[]; use_llm: boolean }) =>
      api.post<{ usernames: string[]; content: string; member_count: number }>("/reports/multi", data),
    onSuccess: (data) => {
      setReport(data.content);
      toast.success(`${data.member_count} kullanici raporu olusturuldu`);
    },
    onError: (error: Error) => {
      toast.error(`Coklu rapor olusturulamadi: ${error.message}`);
    },
  });

  const isGenerating = userReportMutation.isPending || partyReportMutation.isPending || multiUserReportMutation.isPending;
  const error = userReportMutation.error || partyReportMutation.error || multiUserReportMutation.error;

  const handleGenerateUserReport = () => {
    if (!selectedUser) return;
    setReport("");
    userReportMutation.mutate({ username: selectedUser, use_llm: useLLM });
  };

  const handleGeneratePartyReport = () => {
    if (!selectedParty) return;
    setReport("");
    partyReportMutation.mutate({ party: selectedParty, use_llm: partyLLM });
  };

  const handleGenerateMultiUserReport = () => {
    if (selectedUsers.length < 2) {
      toast.error("En az 2 kullanici secmelisiniz");
      return;
    }
    setReport("");
    multiUserReportMutation.mutate({ usernames: selectedUsers, use_llm: useLLM });
  };

  const toggleUserSelection = (username: string) => {
    setSelectedUsers((prev) =>
      prev.includes(username)
        ? prev.filter((u) => u !== username)
        : prev.length < 10
        ? [...prev, username]
        : prev
    );
  };

  const downloadReport = () => {
    if (!report) return;

    const blob = new Blob([report], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const filename =
      mode === "user"
        ? `rapor_${selectedUser}_${new Date().toISOString().split("T")[0]}.md`
        : `parti_rapor_${selectedParty}_${new Date().toISOString().split("T")[0]}.md`;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success("Markdown rapor indirildi");
  };

  const downloadPDF = async () => {
    if (!selectedUser || mode !== "user") return;

    try {
      toast.success("PDF hazirlaniyor...");
      const filename = `istihbarat_rapor_${selectedUser}_${new Date().toISOString().split("T")[0]}.pdf`;
      await api.downloadFile(`/exports/report/${selectedUser}/pdf`, filename);
      toast.success("PDF rapor indirildi");
    } catch (error: any) {
      toast.error(`PDF indirilemedi: ${error.message}`);
    }
  };

  if (usersError) {
    return (
      <div className="min-h-screen bg-[#0B0B0B] text-white">
        <div className="fixed inset-0 bg-[url('/grid.svg')] opacity-5 pointer-events-none" />
        <div className="relative max-w-6xl mx-auto px-4 py-8">
          <div className="bg-[#1A1A1A]/80 backdrop-blur-xl rounded-2xl border border-red-500/30 p-12 text-center">
            <div className="w-20 h-20 bg-red-500/20 rounded-full flex items-center justify-center mx-auto border border-red-500/30">
              <AlertCircle className="w-10 h-10 text-red-400" />
            </div>
            <h2 className="mt-6 text-2xl font-bold text-white">
              Sistem Hatasi
            </h2>
            <p className="mt-3 text-gray-400 font-mono text-sm">
              API_CONNECTION_FAILED // Baglanti kurulamadi
            </p>
            <button
              onClick={() => window.location.reload()}
              className="mt-6 px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl transition-all font-medium shadow-lg shadow-blue-500/25"
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
      {/* Animated background grid */}
      <div className="fixed inset-0 bg-[url('/grid.svg')] opacity-5 pointer-events-none" />

      {/* Gradient overlay */}
      <div className="fixed inset-0 bg-gradient-to-br from-blue-500/5 via-transparent to-emerald-500/5 pointer-events-none" />

      {/* Subtle radial gradient */}
      <div className="fixed inset-0 bg-radial-gradient from-blue-500/10 via-transparent to-transparent pointer-events-none" />

      <div className="relative max-w-6xl mx-auto px-4 py-8">
        {/* Header - Intelligence Command Center Style */}
        <div className="relative mb-8 p-8 rounded-2xl bg-gradient-to-br from-[#1A1A1A] via-[#151515] to-[#0F0F0F] border border-white/10 overflow-hidden shadow-2xl">
          {/* Neural network pattern overlay */}
          <div className="absolute inset-0 opacity-10 bg-[url('/neural-network.svg')]" />

          {/* Animated scan line */}
          <div className="absolute inset-0 overflow-hidden">
            <div className="absolute h-px w-full bg-gradient-to-r from-transparent via-blue-400/50 to-transparent animate-scan" />
          </div>

          <div className="relative flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2.5 rounded-xl bg-gradient-to-br from-blue-500/20 to-blue-600/10 border border-blue-500/30 shadow-lg shadow-blue-500/20">
                  <Brain className="h-6 w-6 text-blue-400" />
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-blue-400 tracking-wider uppercase">Intelligence System</span>
                  <div className="h-1 w-1 rounded-full bg-blue-400 animate-pulse" />
                </div>
              </div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent mb-2">
                Istihbarat Raporlari
              </h1>
              <p className="text-gray-500 text-sm font-mono">Meclis uyelerinin sosyal medya analizi // AI Powered</p>
            </div>

            <div className="hidden sm:flex flex-col gap-3">
              <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/30 backdrop-blur-sm">
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-lg shadow-emerald-400/50" />
                <span className="text-sm font-medium text-emerald-400 font-mono">AI Active</span>
              </div>
              <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/30 backdrop-blur-sm">
                <Lock className="h-3 w-3 text-blue-400" />
                <span className="text-xs font-medium text-blue-400 font-mono">Secure</span>
              </div>
            </div>
          </div>
        </div>

        {/* Mode Tabs - Glassmorphism Style */}
        <div className="flex gap-2 p-1.5 bg-[#1A1A1A]/80 backdrop-blur-xl rounded-xl border border-white/10 w-fit mb-8 shadow-xl">
          <button
            onClick={() => {
              setMode("user");
              setReport("");
            }}
            className={`group flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all duration-300 ${
              mode === "user"
                ? "bg-gradient-to-r from-blue-600/30 to-blue-500/20 text-blue-400 border border-blue-500/40 shadow-lg shadow-blue-500/20"
                : "text-gray-500 hover:text-gray-300 hover:bg-white/5"
            }`}
          >
            <Target className={`h-4 w-4 transition-transform ${mode === "user" ? "rotate-0" : "group-hover:rotate-12"}`} />
            <span>Kullanici Analizi</span>
          </button>
          <button
            onClick={() => {
              setMode("party");
              setReport("");
            }}
            className={`group flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all duration-300 ${
              mode === "party"
                ? "bg-gradient-to-r from-blue-600/30 to-blue-500/20 text-blue-400 border border-blue-500/40 shadow-lg shadow-blue-500/20"
                : "text-gray-500 hover:text-gray-300 hover:bg-white/5"
            }`}
          >
            <Shield className={`h-4 w-4 transition-transform ${mode === "party" ? "rotate-0" : "group-hover:rotate-12"}`} />
            <span>Parti Analizi</span>
          </button>
          <button
            onClick={() => {
              setMode("multi");
              setReport("");
              setSelectedUsers([]);
            }}
            className={`group flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all duration-300 ${
              mode === "multi"
                ? "bg-gradient-to-r from-purple-600/30 to-purple-500/20 text-purple-400 border border-purple-500/40 shadow-lg shadow-purple-500/20"
                : "text-gray-500 hover:text-gray-300 hover:bg-white/5"
            }`}
          >
            <Users className={`h-4 w-4 transition-transform ${mode === "multi" ? "rotate-0" : "group-hover:rotate-12"}`} />
            <span>Coklu Kullanici</span>
          </button>
        </div>

        {/* Controls - Dark Intelligence Card */}
        <div className="bg-[#1A1A1A]/80 backdrop-blur-xl rounded-2xl border border-white/10 p-6 mb-6 shadow-2xl">
          <div className="flex items-end gap-4 flex-wrap">
            {mode === "user" ? (
              <>
                <div className="flex-1 min-w-[280px]">
                  <label className="block text-sm font-medium text-gray-400 mb-2 font-mono uppercase tracking-wider">
                    Target Selection
                  </label>
                  <select
                    value={selectedUser}
                    onChange={(e) => setSelectedUser(e.target.value)}
                    disabled={usersLoading}
                    className="w-full px-4 py-3 bg-[#0B0B0B] border border-white/10 rounded-xl text-white font-mono text-sm focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:border-white/20"
                  >
                    {usersLoading ? (
                      <option>Loading...</option>
                    ) : (
                      users.map((user) => (
                        <option key={user.username} value={user.username} className="bg-[#0B0B0B]">
                          @{user.username} - {user.name}
                        </option>
                      ))
                    )}
                  </select>
                </div>

                <div className="flex flex-col gap-3">
                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={useLLM}
                        onChange={(e) => setUseLLM(e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-12 h-6 bg-[#0B0B0B] border border-white/10 rounded-full peer-checked:bg-gradient-to-r peer-checked:from-blue-600 peer-checked:to-blue-500 peer-checked:border-blue-500/50 transition-all shadow-inner"></div>
                      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-6 peer-checked:shadow-lg peer-checked:shadow-blue-500/50"></div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-yellow-400" />
                      <span className="text-sm font-medium text-gray-300 group-hover:text-white transition-colors font-mono">
                        Deep Analysis
                      </span>
                      {useLLM && (
                        <span className="text-xs bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded-full border border-amber-500/30 font-mono">
                          AI
                        </span>
                      )}
                    </div>
                  </label>

                  <button
                    onClick={handleGenerateUserReport}
                    disabled={isGenerating || !selectedUser || usersLoading}
                    className={`group flex items-center gap-2 px-6 py-3 rounded-xl font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg ${
                      useLLM
                        ? "bg-gradient-to-r from-blue-600 to-blue-500 text-white hover:from-blue-500 hover:to-blue-400 shadow-blue-500/25 hover:shadow-blue-500/40"
                        : "bg-gradient-to-r from-emerald-600 to-emerald-500 text-white hover:from-emerald-500 hover:to-emerald-400 shadow-emerald-500/25 hover:shadow-emerald-500/40"
                    }`}
                  >
                    {useLLM ? (
                      <Sparkles className={`h-4 w-4 ${isGenerating ? "animate-spin" : "group-hover:rotate-12 transition-transform"}`} />
                    ) : (
                      <Zap className={`h-4 w-4 ${isGenerating ? "animate-pulse" : "group-hover:scale-110 transition-transform"}`} />
                    )}
                    {isGenerating ? (
                      <span className="font-mono">Processing...</span>
                    ) : useLLM ? (
                      <span>Analiz Baslat</span>
                    ) : (
                      <span>Hizli Rapor</span>
                    )}
                  </button>
                </div>
              </>
            ) : mode === "party" ? (
              <>
                <div className="flex-1 min-w-[280px]">
                  <label className="block text-sm font-medium text-gray-400 mb-2 font-mono uppercase tracking-wider">
                    Party Selection
                  </label>
                  <select
                    value={selectedParty}
                    onChange={(e) => setSelectedParty(e.target.value)}
                    disabled={usersLoading}
                    className="w-full px-4 py-3 bg-[#0B0B0B] border border-white/10 rounded-xl text-white font-mono text-sm focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:border-white/20"
                  >
                    {usersLoading ? (
                      <option>Loading...</option>
                    ) : (
                      parties.map((party) => (
                        <option key={party} value={party} className="bg-[#0B0B0B]">
                          {party}
                        </option>
                      ))
                    )}
                  </select>
                </div>

                <div className="flex flex-col gap-3">
                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={partyLLM}
                        onChange={(e) => setPartyLLM(e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-12 h-6 bg-[#0B0B0B] border border-white/10 rounded-full peer-checked:bg-gradient-to-r peer-checked:from-purple-600 peer-checked:to-purple-500 peer-checked:border-purple-500/50 transition-all shadow-inner"></div>
                      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-6 peer-checked:shadow-lg peer-checked:shadow-purple-500/50"></div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-purple-400" />
                      <span className="text-sm font-medium text-gray-300 group-hover:text-white transition-colors font-mono">
                        LLM Analizi
                      </span>
                    </div>
                  </label>

                  <button
                    onClick={handleGeneratePartyReport}
                    disabled={isGenerating || !selectedParty || usersLoading}
                    className="group flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-500 text-white rounded-xl hover:from-purple-500 hover:to-purple-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium shadow-lg shadow-purple-500/25 hover:shadow-purple-500/40"
                  >
                    <Users className={`h-4 w-4 ${isGenerating ? "animate-pulse" : "group-hover:scale-110 transition-transform"}`} />
                    {isGenerating ? <span className="font-mono">Processing...</span> : <span>Parti Analizi</span>}
                  </button>
                </div>
              </>
            ) : (
              /* Multi-user mode */
              <>
                <div className="flex-1">
                  <label className="block text-sm font-medium text-gray-400 mb-2 font-mono uppercase tracking-wider">
                    Kullanici Secimi ({selectedUsers.length}/10)
                  </label>
                  <div className="max-h-48 overflow-y-auto bg-[#0B0B0B] border border-white/10 rounded-xl p-3 space-y-1">
                    {usersLoading ? (
                      <p className="text-gray-500 text-sm">Yukleniyor...</p>
                    ) : (
                      users.map((user) => (
                        <label
                          key={user.username}
                          className={`flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-all ${
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
                          <span className="text-sm text-white">
                            <span className="text-blue-400 font-mono">@{user.username}</span>
                            <span className="text-gray-400 ml-2">- {user.name}</span>
                          </span>
                        </label>
                      ))
                    )}
                  </div>
                </div>

                <div className="flex flex-col gap-3">
                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={useLLM}
                        onChange={(e) => setUseLLM(e.target.checked)}
                        className="sr-only peer"
                      />
                      <div className="w-12 h-6 bg-[#0B0B0B] border border-white/10 rounded-full peer-checked:bg-gradient-to-r peer-checked:from-purple-600 peer-checked:to-purple-500 peer-checked:border-purple-500/50 transition-all shadow-inner"></div>
                      <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-6 peer-checked:shadow-lg peer-checked:shadow-purple-500/50"></div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-purple-400" />
                      <span className="text-sm font-medium text-gray-300 group-hover:text-white transition-colors font-mono">
                        Birlesik AI Analizi
                      </span>
                    </div>
                  </label>

                  <button
                    onClick={handleGenerateMultiUserReport}
                    disabled={isGenerating || selectedUsers.length < 2 || usersLoading}
                    className="group flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-purple-500 text-white rounded-xl hover:from-purple-500 hover:to-purple-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium shadow-lg shadow-purple-500/25 hover:shadow-purple-500/40"
                  >
                    <Users className={`h-4 w-4 ${isGenerating ? "animate-pulse" : "group-hover:scale-110 transition-transform"}`} />
                    {isGenerating ? (
                      <span className="font-mono">Processing...</span>
                    ) : (
                      <span>Birlesik Rapor ({selectedUsers.length})</span>
                    )}
                  </button>
                </div>
              </>
            )}

            {report && !isGenerating && (
              <div className="flex flex-col gap-3 ml-auto">
                <div className="h-6"></div>
                <div className="flex gap-2">
                  {mode === "user" && (
                    <button
                      onClick={downloadPDF}
                      className="group flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-red-600 to-red-500 text-white rounded-xl hover:from-red-500 hover:to-red-400 transition-all font-medium shadow-lg shadow-red-500/25 hover:shadow-red-500/40"
                    >
                      <FileDown className="h-4 w-4 group-hover:translate-y-0.5 transition-transform" />
                      <span>PDF</span>
                    </button>
                  )}
                  <button
                    onClick={downloadReport}
                    className="group flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-emerald-600 to-emerald-500 text-white rounded-xl hover:from-emerald-500 hover:to-emerald-400 transition-all font-medium shadow-lg shadow-emerald-500/25 hover:shadow-emerald-500/40"
                  >
                    <Download className="h-4 w-4 group-hover:translate-y-0.5 transition-transform" />
                    <span>MD</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Error Display - Cyber Alert */}
        {error && !isGenerating && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-start gap-3 mb-6 backdrop-blur-sm animate-pulse">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-red-400 font-medium font-mono">ERROR_DETECTED</p>
              <p className="text-red-300/80 text-sm mt-1 font-mono">{error.message}</p>
            </div>
          </div>
        )}

        {/* Loading State - Advanced Cyber Animation */}
        {isGenerating && (
          <div className="bg-[#1A1A1A]/80 backdrop-blur-xl rounded-2xl border border-white/10 p-12 text-center shadow-2xl overflow-hidden">
            <div className="relative inline-flex mb-8">
              {/* Outer pulse ring */}
              <div className="absolute inset-0 w-24 h-24 -m-2 rounded-full border-2 border-blue-500/30 animate-ping" />

              {/* Main spinner */}
              <div className="relative w-24 h-24 rounded-full border-2 border-transparent border-t-blue-500 border-r-blue-400/70 border-b-blue-300/40 border-l-blue-200/20 animate-spin" />

              {/* Inner glow */}
              <div className="absolute inset-0 w-24 h-24 rounded-full bg-gradient-to-br from-blue-500/20 to-transparent blur-xl" />

              {/* Center icon */}
              <div className="absolute inset-0 flex items-center justify-center">
                <Brain className="h-10 w-10 text-blue-400 animate-pulse" />
              </div>
            </div>

            <p className="text-lg font-semibold text-white mb-2">Analiz Isleniyor</p>
            <p className="text-sm text-gray-500 font-mono">AI_PROCESSING // STATUS: ACTIVE</p>

            {useLLM && mode === "user" && (
              <p className="text-xs text-gray-600 mt-4 font-mono">
                Deep analysis may take several minutes...
              </p>
            )}

            {/* Progress bar */}
            <div className="w-full max-w-md mx-auto h-1.5 bg-[#0B0B0B] rounded-full mt-8 overflow-hidden border border-white/10">
              <div className="h-full bg-gradient-to-r from-blue-600 via-blue-400 to-blue-600 rounded-full animate-shimmer bg-[length:200%_100%]" />
            </div>

            {/* Activity indicators */}
            <div className="flex items-center justify-center gap-6 mt-8">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-emerald-400 animate-pulse" />
                <span className="text-xs text-gray-500 font-mono">Neural Network</span>
              </div>
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-blue-400 animate-pulse" />
                <span className="text-xs text-gray-500 font-mono">Data Analysis</span>
              </div>
            </div>
          </div>
        )}

        {/* Report Display - Terminal/Command Center Style */}
        {report && !isGenerating && (
          <div className="bg-[#1A1A1A]/80 backdrop-blur-xl rounded-2xl border border-white/10 overflow-hidden shadow-2xl">
            {/* Terminal header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-gradient-to-r from-emerald-500/10 via-emerald-500/5 to-transparent">
              <div className="flex items-center gap-4">
                {/* macOS-style dots */}
                <div className="flex gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500 shadow-lg shadow-red-500/50" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500 shadow-lg shadow-yellow-500/50" />
                  <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-lg shadow-emerald-500/50" />
                </div>

                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-emerald-400" />
                  <span className="text-emerald-400 font-mono text-sm font-medium">RAPOR_HAZIR.md</span>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 bg-emerald-500/20 px-3 py-1.5 rounded-lg border border-emerald-500/30">
                  <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse shadow-lg shadow-emerald-400/50" />
                  <span className="text-emerald-400 text-xs font-medium font-mono">COMPLETE</span>
                </div>

                {mode === "user" && (
                  <button
                    onClick={downloadPDF}
                    className="group flex items-center gap-2 px-4 py-2 bg-red-500/20 text-red-400 rounded-lg border border-red-500/30 hover:bg-red-500/30 transition-all"
                    title="PDF olarak indir"
                  >
                    <FileDown className="h-4 w-4 group-hover:translate-y-0.5 transition-transform" />
                    <span className="text-sm font-mono">PDF</span>
                  </button>
                )}

                <button
                  onClick={downloadReport}
                  className="group flex items-center gap-2 px-4 py-2 bg-emerald-500/20 text-emerald-400 rounded-lg border border-emerald-500/30 hover:bg-emerald-500/30 transition-all"
                  title="Markdown olarak indir"
                >
                  <Download className="h-4 w-4 group-hover:translate-y-0.5 transition-transform" />
                  <span className="text-sm font-mono">MD</span>
                </button>
              </div>
            </div>

            {/* Report content */}
            <div className="p-6 max-h-[600px] overflow-auto custom-scrollbar">
              <MarkdownRenderer content={report} />
            </div>
          </div>
        )}

        {/* Empty State - Intelligence Waiting Mode */}
        {!report && !isGenerating && (
          <div className="bg-[#1A1A1A]/80 backdrop-blur-xl rounded-2xl border border-white/10 p-12 text-center shadow-2xl overflow-hidden">
            {/* Background pattern */}
            <div className="absolute inset-0 bg-[url('/neural-network.svg')] opacity-5" />

            <div className="relative">
              <div className="w-24 h-24 mx-auto rounded-2xl bg-gradient-to-br from-blue-500/20 via-blue-600/10 to-emerald-500/10 flex items-center justify-center border border-white/10 shadow-2xl shadow-blue-500/10 mb-6">
                <Brain className="w-12 h-12 text-blue-400" />
              </div>

              <h3 className="text-xl font-semibold text-white mb-2">Analiz Baslatmayi Bekliyor</h3>
              <p className="text-gray-500 font-mono text-sm">Select target and initiate AI analysis</p>

              {/* Feature indicators */}
              <div className="mt-8 flex items-center justify-center gap-6 text-xs text-gray-600">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-blue-400" />
                  <span className="font-mono">Deep LLM</span>
                </div>
                <div className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-emerald-400" />
                  <span className="font-mono">Fast Mode</span>
                </div>
                <div className="flex items-center gap-2">
                  <Download className="h-4 w-4 text-purple-400" />
                  <span className="font-mono">Export MD</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <style jsx global>{`
        @keyframes scan {
          0% {
            transform: translateY(-100%);
            opacity: 0;
          }
          50% {
            opacity: 1;
          }
          100% {
            transform: translateY(200vh);
            opacity: 0;
          }
        }

        @keyframes shimmer {
          0% {
            background-position: -200% 0;
          }
          100% {
            background-position: 200% 0;
          }
        }

        .animate-scan {
          animation: scan 8s linear infinite;
        }

        .animate-shimmer {
          animation: shimmer 2s linear infinite;
        }

        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }

        .custom-scrollbar::-webkit-scrollbar-track {
          background: #0B0B0B;
          border-radius: 4px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(77, 163, 255, 0.3);
          border-radius: 4px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(77, 163, 255, 0.5);
        }
      `}</style>
    </div>
  );
}
