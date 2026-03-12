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
  HardDrive,
} from "lucide-react";

interface SystemStatus {
  database: {
    connected: boolean;
    councilors: number;
    tweets: number;
    profiles: number;
  };
  ollama: {
    connected: boolean;
    model: string;
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
        ollama: {
          connected: false, // Will check separately
          model: "qwen2.5:3b",
        },
        version: healthData.version || "3.0.0",
      });
      setError(null);
    } catch (err) {
      console.error("Failed to fetch status:", err);
      setError("Sistem durumu alinamadi");
      setStatus({
        database: {
          connected: false,
          councilors: 0,
          tweets: 0,
          profiles: 0,
        },
        ollama: {
          connected: false,
          model: "unknown",
        },
        version: "unknown",
      });
    } finally {
      setLoading(false);
    }
  };

  const checkOllama = async () => {
    try {
      const response = await fetch("http://127.0.0.1:11434/api/tags");
      if (response.ok) {
        const data = await response.json();
        const models = data.models || [];
        setStatus((prev) =>
          prev
            ? {
                ...prev,
                ollama: {
                  connected: true,
                  model: models.length > 0 ? models[0].name : "no models",
                },
              }
            : prev
        );
      }
    } catch {
      setStatus((prev) =>
        prev
          ? {
              ...prev,
              ollama: { connected: false, model: "unreachable" },
            }
          : prev
      );
    }
  };

  useEffect(() => {
    if (status) {
      checkOllama();
    }
  }, [status?.database.connected]);

  const StatusBadge = ({ ok }: { ok: boolean }) => (
    <span
      className={`flex items-center gap-1 text-sm ${
        ok ? "text-green-600" : "text-red-600"
      }`}
    >
      {ok ? (
        <>
          <CheckCircle className="h-4 w-4" /> Aktif
        </>
      ) : (
        <>
          <XCircle className="h-4 w-4" /> Kapalı
        </>
      )}
    </span>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Settings className="h-6 w-6 text-gray-600" />
            Sistem
          </h1>
          <p className="text-gray-500">Sistem durumu ve ayarlar</p>
        </div>

        <button
          onClick={fetchStatus}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Yenile
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* API Status */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <Server className="h-5 w-5 text-blue-600" />
              </div>
              <h3 className="font-semibold text-gray-900">Backend API</h3>
            </div>
            <StatusBadge ok={status?.database.connected || false} />
          </div>
          <div className="text-sm text-gray-500">
            <p>URL: http://localhost:8000</p>
            <p>Version: {status?.version || "..."}</p>
          </div>
        </div>

        {/* Database Status */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                <Database className="h-5 w-5 text-green-600" />
              </div>
              <h3 className="font-semibold text-gray-900">Veritabani</h3>
            </div>
            <StatusBadge ok={status?.database.connected || false} />
          </div>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Kullanicilar:</span>
              <span className="font-medium">{status?.database.councilors || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Tweetler:</span>
              <span className="font-medium">{status?.database.tweets || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Profiller:</span>
              <span className="font-medium">{status?.database.profiles || 0}</span>
            </div>
          </div>
        </div>

        {/* Ollama Status */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                <HardDrive className="h-5 w-5 text-purple-600" />
              </div>
              <h3 className="font-semibold text-gray-900">Ollama LLM</h3>
            </div>
            <StatusBadge ok={status?.ollama.connected || false} />
          </div>
          <div className="text-sm text-gray-500">
            <p>URL: http://127.0.0.1:11434</p>
            <p>Model: {status?.ollama.model || "..."}</p>
          </div>
        </div>
      </div>

      {/* Info Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Sistem Bilgileri</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Platform:</span>
            <p className="font-medium">FastAPI + Next.js</p>
          </div>
          <div>
            <span className="text-gray-500">Database:</span>
            <p className="font-medium">SQLite (dev) / PostgreSQL (prod)</p>
          </div>
          <div>
            <span className="text-gray-500">LLM:</span>
            <p className="font-medium">Ollama (Local)</p>
          </div>
          <div>
            <span className="text-gray-500">Scraping:</span>
            <p className="font-medium">Selenium + Undetected Chrome</p>
          </div>
        </div>
      </div>
    </div>
  );
}
