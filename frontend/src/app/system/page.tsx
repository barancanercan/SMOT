"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import {
  Settings,
  Database,
  Server,
  RefreshCw,
  CheckCircle,
  XCircle,
  Brain,
  Cpu,
  Activity,
  Shield,
} from "lucide-react";

interface SystemStatus {
  database: {
    connected: boolean;
    councilors: number;
    tweets: number;
    profiles: number;
  };
  llm: {
    provider: string;
    model: string;
    connected: boolean;
  };
  version: string;
}

export default function SystemPage() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      // Health check
      const health = await fetch("http://localhost:8000/health");
      const healthData = await health.json();

      // Dashboard stats for DB info
      const stats = await api.get<{
        total_councilors: number;
        total_tweets: number;
        total_profiles: number;
      }>("/dashboard/overview");

      setStatus({
        database: {
          connected: true,
          councilors: stats.total_councilors || 0,
          tweets: stats.total_tweets || 0,
          profiles: stats.total_profiles || 0,
        },
        llm: {
          provider: healthData.llm_provider || "openai",
          model: healthData.llm_model || "gpt-3.5-turbo",
          connected: true,
        },
        version: healthData.version || "3.2.0",
      });
      setError(null);
    } catch (err) {
      console.error("Durum alinamadi:", err);
      setError("Sistem durumu alinamadi");
      setStatus({
        database: {
          connected: false,
          councilors: 0,
          tweets: 0,
          profiles: 0,
        },
        llm: {
          provider: "bilinmiyor",
          model: "bilinmiyor",
          connected: false,
        },
        version: "bilinmiyor",
      });
    } finally {
      setLoading(false);
    }
  };

  const StatusBadge = ({ ok }: { ok: boolean }) => (
    <span
      className={`flex items-center gap-1 text-sm ${
        ok ? "text-emerald-400" : "text-red-400"
      }`}
    >
      {ok ? (
        <>
          <CheckCircle className="h-4 w-4" /> Aktif
        </>
      ) : (
        <>
          <XCircle className="h-4 w-4" /> Kapali
        </>
      )}
    </span>
  );

  return (
    <div className="min-h-screen bg-[#0B0B0B] text-white">
      {/* Arka plan */}
      <div className="fixed inset-0 bg-[url('/grid.svg')] opacity-5 pointer-events-none" />
      <div className="fixed inset-0 bg-gradient-to-br from-blue-500/5 via-transparent to-emerald-500/5 pointer-events-none" />

      <div className="relative max-w-7xl mx-auto px-4 py-8 space-y-6">
        {/* Baslik */}
        <div className="relative p-8 rounded-2xl bg-gradient-to-br from-[#1A1A1A] via-[#151515] to-[#0F0F0F] border border-white/10 overflow-hidden shadow-2xl">
          <div className="absolute inset-0 opacity-10 bg-[url('/neural-network.svg')]" />

          <div className="relative flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2.5 rounded-xl bg-gradient-to-br from-blue-500/20 to-blue-600/10 border border-blue-500/30 shadow-lg shadow-blue-500/20">
                  <Settings className="h-6 w-6 text-blue-400" />
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-blue-400 tracking-wider uppercase">Sistem Kontrol</span>
                  <div className="h-1 w-1 rounded-full bg-blue-400 animate-pulse" />
                </div>
              </div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-white via-gray-200 to-gray-400 bg-clip-text text-transparent mb-2">
                Sistem Durumu
              </h1>
              <p className="text-gray-500 text-sm font-mono">Sistem durumu ve yapilandirma // Canli izleme</p>
            </div>

            <button
              onClick={fetchStatus}
              disabled={loading}
              className="group flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-xl hover:from-blue-500 hover:to-blue-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : "group-hover:rotate-180 transition-transform duration-500"}`} />
              <span className="font-medium">Yenile</span>
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 flex items-start gap-3 backdrop-blur-sm">
            <XCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-red-400 font-medium font-mono">HATA</p>
              <p className="text-red-300/80 text-sm mt-1">{error}</p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* API Durumu */}
          <div className="group relative bg-[#1A1A1A]/80 backdrop-blur-xl rounded-2xl border border-white/10 p-6 shadow-2xl hover:border-blue-500/30 transition-all duration-300 overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/0 to-blue-500/0 group-hover:from-blue-500/5 group-hover:to-transparent transition-all duration-300" />

            <div className="relative">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500/20 to-blue-600/10 rounded-xl flex items-center justify-center border border-blue-500/30 shadow-lg shadow-blue-500/10 group-hover:shadow-blue-500/30 transition-all">
                    <Server className="h-6 w-6 text-blue-400" />
                  </div>
                  <h3 className="font-semibold text-white">Backend API</h3>
                </div>
                <StatusBadge ok={status?.database.connected || false} />
              </div>
              <div className="text-sm text-gray-400 space-y-2">
                <div className="flex justify-between items-center p-2 rounded-lg bg-[#0B0B0B]/50 border border-white/5">
                  <span className="text-gray-500">Adres:</span>
                  <span className="font-mono text-gray-300">localhost:8000</span>
                </div>
                <div className="flex justify-between items-center p-2 rounded-lg bg-[#0B0B0B]/50 border border-white/5">
                  <span className="text-gray-500">Surum:</span>
                  <span className="font-mono text-blue-400">{status?.version || "..."}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Veritabani Durumu */}
          <div className="group relative bg-[#1A1A1A]/80 backdrop-blur-xl rounded-2xl border border-white/10 p-6 shadow-2xl hover:border-emerald-500/30 transition-all duration-300 overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/0 to-emerald-500/0 group-hover:from-emerald-500/5 group-hover:to-transparent transition-all duration-300" />

            <div className="relative">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 rounded-xl flex items-center justify-center border border-emerald-500/30 shadow-lg shadow-emerald-500/10 group-hover:shadow-emerald-500/30 transition-all">
                    <Database className="h-6 w-6 text-emerald-400" />
                  </div>
                  <h3 className="font-semibold text-white">Veritabani</h3>
                </div>
                <StatusBadge ok={status?.database.connected || false} />
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between items-center p-2 rounded-lg bg-[#0B0B0B]/50 border border-white/5">
                  <span className="text-gray-500">Kullanicilar:</span>
                  <span className="font-mono font-medium text-emerald-400">{status?.database.councilors.toLocaleString('tr-TR') || 0}</span>
                </div>
                <div className="flex justify-between items-center p-2 rounded-lg bg-[#0B0B0B]/50 border border-white/5">
                  <span className="text-gray-500">Tweetler:</span>
                  <span className="font-mono font-medium text-emerald-400">{status?.database.tweets.toLocaleString('tr-TR') || 0}</span>
                </div>
                <div className="flex justify-between items-center p-2 rounded-lg bg-[#0B0B0B]/50 border border-white/5">
                  <span className="text-gray-500">Profiller:</span>
                  <span className="font-mono font-medium text-emerald-400">{status?.database.profiles.toLocaleString('tr-TR') || 0}</span>
                </div>
              </div>
            </div>
          </div>

          {/* LLM Durumu */}
          <div className="group relative bg-[#1A1A1A]/80 backdrop-blur-xl rounded-2xl border border-white/10 p-6 shadow-2xl hover:border-purple-500/30 transition-all duration-300 overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-purple-500/0 to-purple-500/0 group-hover:from-purple-500/5 group-hover:to-transparent transition-all duration-300" />

            <div className="relative">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-gradient-to-br from-purple-500/20 to-purple-600/10 rounded-xl flex items-center justify-center border border-purple-500/30 shadow-lg shadow-purple-500/10 group-hover:shadow-purple-500/30 transition-all">
                    <Brain className="h-6 w-6 text-purple-400" />
                  </div>
                  <h3 className="font-semibold text-white">Yapay Zeka</h3>
                </div>
                <StatusBadge ok={status?.llm.connected || false} />
              </div>
              <div className="text-sm text-gray-400 space-y-2">
                <div className="flex justify-between items-center p-2 rounded-lg bg-[#0B0B0B]/50 border border-white/5">
                  <span className="text-gray-500">Saglayici:</span>
                  <span className="font-mono text-purple-400 capitalize">{status?.llm.provider || "..."}</span>
                </div>
                <div className="flex justify-between items-center p-2 rounded-lg bg-[#0B0B0B]/50 border border-white/5">
                  <span className="text-gray-500">Model:</span>
                  <span className="font-mono text-purple-400">{status?.llm.model || "..."}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Sistem Bilgileri */}
        <div className="bg-[#1A1A1A]/80 backdrop-blur-xl rounded-2xl border border-white/10 p-6 shadow-2xl">
          <h3 className="font-semibold text-white mb-6 flex items-center gap-2">
            <Activity className="h-5 w-5 text-blue-400" />
            <span>Sistem Bilgileri</span>
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div className="p-4 rounded-xl bg-[#0B0B0B]/50 border border-white/5">
              <span className="text-gray-500 text-xs uppercase tracking-wider">Platform</span>
              <p className="font-medium text-white mt-1">FastAPI + Next.js 14</p>
            </div>
            <div className="p-4 rounded-xl bg-[#0B0B0B]/50 border border-white/5">
              <span className="text-gray-500 text-xs uppercase tracking-wider">Veritabani</span>
              <p className="font-medium text-white mt-1">SQLite / PostgreSQL</p>
            </div>
            <div className="p-4 rounded-xl bg-[#0B0B0B]/50 border border-white/5">
              <span className="text-gray-500 text-xs uppercase tracking-wider">Yapay Zeka</span>
              <p className="font-medium text-white mt-1">OpenAI / Ollama</p>
            </div>
            <div className="p-4 rounded-xl bg-[#0B0B0B]/50 border border-white/5">
              <span className="text-gray-500 text-xs uppercase tracking-wider">Veri Toplama</span>
              <p className="font-medium text-white mt-1">Selenium + Chrome</p>
            </div>
          </div>
        </div>

        {/* Ozellikler */}
        <div className="bg-[#1A1A1A]/80 backdrop-blur-xl rounded-2xl border border-white/10 p-6 shadow-2xl">
          <h3 className="font-semibold text-white mb-6 flex items-center gap-2">
            <Shield className="h-5 w-5 text-emerald-400" />
            <span>Sistem Ozellikleri</span>
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="flex items-center gap-3 p-3 rounded-lg bg-[#0B0B0B]/50 border border-white/5">
              <CheckCircle className="h-5 w-5 text-emerald-400" />
              <span className="text-gray-300">Kullanici yonetimi (ekleme/silme)</span>
            </div>
            <div className="flex items-center gap-3 p-3 rounded-lg bg-[#0B0B0B]/50 border border-white/5">
              <CheckCircle className="h-5 w-5 text-emerald-400" />
              <span className="text-gray-300">Coklu kullanici raporu</span>
            </div>
            <div className="flex items-center gap-3 p-3 rounded-lg bg-[#0B0B0B]/50 border border-white/5">
              <CheckCircle className="h-5 w-5 text-emerald-400" />
              <span className="text-gray-300">Parti raporu (LLM destekli)</span>
            </div>
            <div className="flex items-center gap-3 p-3 rounded-lg bg-[#0B0B0B]/50 border border-white/5">
              <CheckCircle className="h-5 w-5 text-emerald-400" />
              <span className="text-gray-300">Kullanici karsilastirma modulu</span>
            </div>
            <div className="flex items-center gap-3 p-3 rounded-lg bg-[#0B0B0B]/50 border border-white/5">
              <CheckCircle className="h-5 w-5 text-emerald-400" />
              <span className="text-gray-300">Takipci ve etkilesim analizleri</span>
            </div>
            <div className="flex items-center gap-3 p-3 rounded-lg bg-[#0B0B0B]/50 border border-white/5">
              <CheckCircle className="h-5 w-5 text-emerald-400" />
              <span className="text-gray-300">Excel/Markdown rapor indirme</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
