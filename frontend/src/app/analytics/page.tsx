"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { BarChart3, Users, TrendingUp, MapPin, AlertCircle } from "lucide-react";
import { PartyBarChart } from "@/components/charts/party-bar-chart";
import { EngagementPieChart } from "@/components/charts/engagement-pie-chart";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Badge, PartyBadge } from "@/components/ui/badge";
import { SkeletonTable, SkeletonCard } from "@/components/ui/skeleton";

type Tab = "followers" | "parties" | "engagement" | "districts";

interface TabConfig {
  id: Tab;
  label: string;
  icon: React.ReactNode;
}

const tabs: TabConfig[] = [
  { id: "followers", label: "Takipci Siralamasi", icon: <Users className="h-4 w-4" /> },
  { id: "parties", label: "Parti Analizi", icon: <BarChart3 className="h-4 w-4" /> },
  { id: "engagement", label: "Etkilesim", icon: <TrendingUp className="h-4 w-4" /> },
  { id: "districts", label: "Ilce Analizi", icon: <MapPin className="h-4 w-4" /> },
];

export default function AnalyticsPage() {
  const [activeTab, setActiveTab] = useState<Tab>("followers");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <BarChart3 className="h-6 w-6 text-blue-600" />
          Grafikler
        </h1>
        <p className="text-gray-500">Analitik veriler ve gorsellestirmeler</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-1" aria-label="Tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "flex items-center gap-2 px-4 py-3 border-b-2 font-medium text-sm transition-colors",
                activeTab === tab.id
                  ? "border-blue-500 text-blue-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              )}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
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
  const { data, isLoading, error } = useQuery({
    queryKey: ["analytics-followers"],
    queryFn: () => api.get<any[]>("/analytics/followers?limit=20"),
  });

  if (isLoading) return <SkeletonTable rows={10} cols={4} />;
  if (error) return <ErrorState message="Takipci verileri yuklenemedi" />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Top 20 - Takipci Sayisina Gore</h3>
        <Badge variant="info">{data?.length || 0} kullanici</Badge>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12">#</TableHead>
            <TableHead>Isim</TableHead>
            <TableHead>Parti</TableHead>
            <TableHead className="text-right">Takipci</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data?.map((user: any, index: number) => (
            <TableRow key={user.username}>
              <TableCell className="font-medium text-gray-500">
                {index + 1}
              </TableCell>
              <TableCell>
                <div>
                  <div className="font-medium text-gray-900">{user.name}</div>
                  <div className="text-sm text-gray-500">@{user.username}</div>
                </div>
              </TableCell>
              <TableCell>
                <PartyBadge party={user.party || "BAGIMSIZ"} />
              </TableCell>
              <TableCell className="text-right font-semibold text-blue-600">
                {user.followers_count?.toLocaleString("tr-TR")}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function PartiesTab() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["analytics-parties"],
    queryFn: () => api.get<any[]>("/analytics/parties"),
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SkeletonCard className="h-[350px]" />
        <SkeletonCard className="h-[350px]" />
      </div>
    );
  }

  if (error) return <ErrorState message="Parti verileri yuklenemedi" />;

  // Prepare data for pie chart
  const pieData = data?.map((p: any) => ({
    name: p.party || "Bagimsiz",
    value: p.member_count,
  })) || [];

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold">Parti Istatistikleri</h3>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bar Chart */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-700 mb-4">Uye Sayisi</h4>
          <PartyBarChart
            data={data || []}
            dataKey="member_count"
            height={300}
          />
        </div>

        {/* Pie Chart */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-700 mb-4">Dagilim</h4>
          <EngagementPieChart data={pieData} height={300} />
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {data?.map((party: any) => (
          <div
            key={party.party}
            className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors"
          >
            <PartyBadge party={party.party || "BAGIMSIZ"} className="mb-2" />
            <p className="text-2xl font-bold text-gray-900 mt-2">
              {party.member_count}
            </p>
            <p className="text-sm text-gray-500">uye</p>
            <div className="mt-2 pt-2 border-t border-gray-200">
              <p className="text-xs text-gray-600">
                {party.total_followers?.toLocaleString("tr-TR")} takipci
              </p>
              <p className="text-xs text-gray-600">
                {party.total_tweets?.toLocaleString("tr-TR")} tweet
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function EngagementTab() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["analytics-engagement"],
    queryFn: () => api.get<any[]>("/analytics/engagement?limit=15"),
  });

  if (isLoading) return <SkeletonTable rows={10} cols={5} />;
  if (error) return <ErrorState message="Etkilesim verileri yuklenemedi" />;

  // Calculate totals for pie chart
  const totals = data?.reduce(
    (acc: any, user: any) => ({
      likes: acc.likes + (user.total_likes || 0),
      retweets: acc.retweets + (user.total_retweets || 0),
      replies: acc.replies + (user.total_replies || 0),
    }),
    { likes: 0, retweets: 0, replies: 0 }
  ) || { likes: 0, retweets: 0, replies: 0 };

  const pieData = [
    { name: "Begeniler", value: totals.likes },
    { name: "Retweetler", value: totals.retweets },
    { name: "Yorumlar", value: totals.replies },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Top 15 - Etkilesim</h3>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Table */}
        <div className="lg:col-span-2">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Isim</TableHead>
                <TableHead className="text-right">Tweet</TableHead>
                <TableHead className="text-right">Like</TableHead>
                <TableHead className="text-right">RT</TableHead>
                <TableHead className="text-right">Toplam</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data?.map((user: any) => (
                <TableRow key={user.username}>
                  <TableCell>
                    <div>
                      <div className="font-medium text-gray-900">{user.name}</div>
                      <div className="text-xs text-gray-500">
                        <PartyBadge party={user.party || "BAGIMSIZ"} />
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="text-right text-gray-600">
                    {user.tweet_count}
                  </TableCell>
                  <TableCell className="text-right text-gray-600">
                    {user.total_likes?.toLocaleString("tr-TR")}
                  </TableCell>
                  <TableCell className="text-right text-gray-600">
                    {user.total_retweets?.toLocaleString("tr-TR")}
                  </TableCell>
                  <TableCell className="text-right font-semibold text-blue-600">
                    {user.total_engagement?.toLocaleString("tr-TR")}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* Pie Chart */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-700 mb-4">Etkilesim Dagilimi</h4>
          <EngagementPieChart data={pieData} height={250} />
        </div>
      </div>
    </div>
  );
}

function DistrictsTab() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["analytics-districts"],
    queryFn: () => api.get<any[]>("/analytics/districts"),
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {[...Array(12)].map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (error) return <ErrorState message="Ilce verileri yuklenemedi" />;

  // Sort by member count
  const sortedData = [...(data || [])].sort(
    (a: any, b: any) => b.member_count - a.member_count
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Ilce Dagilimi</h3>
        <Badge variant="secondary">{data?.length || 0} ilce</Badge>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        {sortedData.map((district: any, index: number) => (
          <div
            key={district.district}
            className={cn(
              "rounded-lg p-4 transition-colors",
              index < 3
                ? "bg-blue-50 border border-blue-200"
                : "bg-gray-50 hover:bg-gray-100"
            )}
          >
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-medium text-gray-900 truncate" title={district.district}>
                {district.district}
              </h4>
              {index < 3 && (
                <Badge variant="primary" className="text-xs">
                  #{index + 1}
                </Badge>
              )}
            </div>
            <p className="text-2xl font-bold text-blue-600">
              {district.member_count}
            </p>
            <p className="text-sm text-gray-500">uye</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-64 text-center">
      <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
      <p className="text-gray-700 font-medium">{message}</p>
      <p className="text-sm text-gray-500 mt-1">
        API baglantisini kontrol edin ve sayfayi yenileyin
      </p>
    </div>
  );
}
