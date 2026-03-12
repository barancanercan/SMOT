"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

type Tab = "followers" | "parties" | "engagement" | "districts";

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState<Tab>("followers");

  const tabs = [
    { id: "followers" as Tab, label: "Takipci Siralamasi" },
    { id: "parties" as Tab, label: "Parti Analizi" },
    { id: "engagement" as Tab, label: "Etkilesim" },
    { id: "districts" as Tab, label: "Ilce Analizi" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Grafikler</h1>
        <p className="text-gray-500">Analitik veriler ve gorsellestirmeler</p>
      </div>

      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "py-4 px-1 border-b-2 font-medium text-sm transition-colors",
                activeTab === tab.id
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              )}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 p-6">
        {activeTab === "followers" && <FollowersTab />}
        {activeTab === "parties" && <PartiesTab />}
        {activeTab === "engagement" && <EngagementTab />}
        {activeTab === "districts" && <DistrictsTab />}
      </div>
    </div>
  );
}

function FollowersTab() {
  const { data, isLoading } = useQuery({
    queryKey: ["analytics-followers"],
    queryFn: () => api.get("/analytics/followers?limit=20"),
  });

  if (isLoading) return <LoadingSpinner />;

  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">Top 20 Takipci Sayisina Gore</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">#</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Isim</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Parti</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Takipci</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {(data as any[])?.map((user: any, index: number) => (
              <tr key={user.username}>
                <td className="px-4 py-3 text-sm text-gray-500">{index + 1}</td>
                <td className="px-4 py-3 text-sm font-medium text-gray-900">{user.name}</td>
                <td className="px-4 py-3 text-sm text-gray-500">{user.party}</td>
                <td className="px-4 py-3 text-sm text-gray-900">{user.followers_count?.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function PartiesTab() {
  const { data, isLoading } = useQuery({
    queryKey: ["analytics-parties"],
    queryFn: () => api.get("/analytics/parties"),
  });

  if (isLoading) return <LoadingSpinner />;

  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">Parti Istatistikleri</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {(data as any[])?.map((party: any) => (
          <div key={party.party} className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-medium text-gray-900">{party.party || "Bagimsiz"}</h4>
            <p className="text-2xl font-bold text-blue-600 mt-2">{party.member_count}</p>
            <p className="text-sm text-gray-500">uye</p>
            <p className="text-sm text-gray-600 mt-2">
              {party.total_followers?.toLocaleString()} toplam takipci
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

function EngagementTab() {
  const { data, isLoading } = useQuery({
    queryKey: ["analytics-engagement"],
    queryFn: () => api.get("/analytics/engagement?limit=15"),
  });

  if (isLoading) return <LoadingSpinner />;

  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">Top 15 Etkilesim</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Isim</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tweet</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Like</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">RT</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Toplam</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {(data as any[])?.map((user: any) => (
              <tr key={user.username}>
                <td className="px-4 py-3 text-sm font-medium text-gray-900">{user.name}</td>
                <td className="px-4 py-3 text-sm text-gray-500">{user.tweet_count}</td>
                <td className="px-4 py-3 text-sm text-gray-500">{user.total_likes?.toLocaleString()}</td>
                <td className="px-4 py-3 text-sm text-gray-500">{user.total_retweets?.toLocaleString()}</td>
                <td className="px-4 py-3 text-sm font-medium text-blue-600">{user.total_engagement?.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function DistrictsTab() {
  const { data, isLoading } = useQuery({
    queryKey: ["analytics-districts"],
    queryFn: () => api.get("/analytics/districts"),
  });

  if (isLoading) return <LoadingSpinner />;

  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">Ilce Dagilimi</h3>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {(data as any[])?.slice(0, 16).map((district: any) => (
          <div key={district.district} className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 truncate">{district.district}</h4>
            <p className="text-xl font-bold text-blue-600 mt-1">{district.member_count}</p>
            <p className="text-sm text-gray-500">uye</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center h-32">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>
  );
}
