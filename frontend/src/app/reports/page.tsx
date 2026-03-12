"use client";

import { useState, useMemo } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api, User, ReportResponse, PartyReportResponse, PaginatedResponse } from "@/lib/api";
import { useToast } from "@/components/ui/toast";
import { FileText, Download, RefreshCw, Users, AlertCircle } from "lucide-react";

type ReportMode = "user" | "party";

export default function ReportsPage() {
  const [mode, setMode] = useState<ReportMode>("user");
  const [selectedUser, setSelectedUser] = useState<string>("");
  const [selectedParty, setSelectedParty] = useState<string>("");
  const [report, setReport] = useState<string>("");
  const [useLLM, setUseLLM] = useState<boolean>(true);
  const toast = useToast();

  // Fetch users with React Query
  const {
    data: usersData,
    isLoading: usersLoading,
    error: usersError,
  } = useQuery({
    queryKey: ["users"],
    queryFn: () => api.get<PaginatedResponse<User>>("/users/"),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const users = usersData?.items || [];

  // Extract unique parties from users
  const parties = useMemo(() => {
    return [...new Set(users.map((u) => u.party).filter(Boolean))];
  }, [users]);

  // Set default selections when users load
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
    mutationFn: (data: { party: string }) =>
      api.post<PartyReportResponse>("/reports/party", {
        party: data.party,
        use_llm: false,
      }),
    onSuccess: (data) => {
      setReport(data.content);
      toast.success("Parti raporu basariyla olusturuldu");
    },
    onError: (error: Error) => {
      toast.error(`Parti raporu olusturulamadi: ${error.message}`);
    },
  });

  const isGenerating =
    userReportMutation.isPending || partyReportMutation.isPending;

  const handleGenerateUserReport = () => {
    if (!selectedUser) return;
    setReport("");
    userReportMutation.mutate({ username: selectedUser, use_llm: useLLM });
  };

  const handleGeneratePartyReport = () => {
    if (!selectedParty) return;
    setReport("");
    partyReportMutation.mutate({ party: selectedParty });
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
    toast.success("Rapor indirildi");
  };

  if (usersError) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          Kullanicilar yuklenemedi
        </h2>
        <p className="text-gray-500">
          API baglantisini kontrol edin ve sayfayi yenileyin.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <FileText className="h-6 w-6 text-blue-600" />
            Raporlar
          </h1>
          <p className="text-gray-500">Kullanici ve parti analiz raporlari</p>
        </div>
      </div>

      {/* Mode Tabs */}
      <div className="flex gap-2 border-b border-gray-200 pb-2">
        <button
          onClick={() => {
            setMode("user");
            setReport("");
          }}
          className={`flex items-center gap-2 px-4 py-2 rounded-t-lg font-medium transition-colors ${
            mode === "user"
              ? "bg-blue-600 text-white"
              : "bg-gray-100 text-gray-600 hover:bg-gray-200"
          }`}
        >
          <FileText className="h-4 w-4" />
          Kullanici Raporu
        </button>
        <button
          onClick={() => {
            setMode("party");
            setReport("");
          }}
          className={`flex items-center gap-2 px-4 py-2 rounded-t-lg font-medium transition-colors ${
            mode === "party"
              ? "bg-blue-600 text-white"
              : "bg-gray-100 text-gray-600 hover:bg-gray-200"
          }`}
        >
          <Users className="h-4 w-4" />
          Parti Raporu
        </button>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-3 flex-wrap">
        {mode === "user" ? (
          <>
            <select
              value={selectedUser}
              onChange={(e) => setSelectedUser(e.target.value)}
              disabled={usersLoading}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
            >
              {usersLoading ? (
                <option>Yukleniyor...</option>
              ) : (
                users.map((user) => (
                  <option key={user.username} value={user.username}>
                    @{user.username} - {user.name}
                  </option>
                ))
              )}
            </select>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={useLLM}
                onChange={(e) => setUseLLM(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">LLM Analizi (Yavas)</span>
            </label>

            <button
              onClick={handleGenerateUserReport}
              disabled={isGenerating || !selectedUser || usersLoading}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <RefreshCw
                className={`h-4 w-4 ${isGenerating ? "animate-spin" : ""}`}
              />
              {useLLM ? "Tam Rapor Olustur" : "Hizli Rapor"}
            </button>
          </>
        ) : (
          <>
            <select
              value={selectedParty}
              onChange={(e) => setSelectedParty(e.target.value)}
              disabled={usersLoading}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
            >
              {usersLoading ? (
                <option>Yukleniyor...</option>
              ) : (
                parties.map((party) => (
                  <option key={party} value={party}>
                    {party}
                  </option>
                ))
              )}
            </select>

            <button
              onClick={handleGeneratePartyReport}
              disabled={isGenerating || !selectedParty || usersLoading}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <RefreshCw
                className={`h-4 w-4 ${isGenerating ? "animate-spin" : ""}`}
              />
              Parti Raporu Olustur
            </button>
          </>
        )}

        {report && (
          <button
            onClick={downloadReport}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <Download className="h-4 w-4" />
            Indir (.md)
          </button>
        )}
      </div>

      {/* Report Display */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        {isGenerating ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3" />
              <p className="text-gray-500">Rapor olusturuluyor...</p>
              {useLLM && mode === "user" && (
                <p className="text-xs text-gray-400 mt-1">
                  LLM analizi birka dakika surebilir
                </p>
              )}
            </div>
          </div>
        ) : report ? (
          <div className="p-6">
            <pre className="whitespace-pre-wrap font-mono text-sm text-gray-800 leading-relaxed bg-gray-50 p-4 rounded-lg overflow-auto max-h-[600px]">
              {report}
            </pre>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500">
            <FileText className="h-12 w-12 mb-3 text-gray-300" />
            <p>Henuz rapor olusturulmadi</p>
            <p className="text-sm">
              Yukaridaki butonlari kullanarak rapor olusturun
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
