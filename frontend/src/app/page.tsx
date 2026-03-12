"use client";

import { useQuery } from "@tanstack/react-query";
import { api, DashboardStats } from "@/lib/api";
import { MetricCard } from "@/components/features/metric-card";
import {
  BarChart3,
  Users,
  Heart,
  Eye,
  MessageCircle,
  Repeat2,
  TrendingUp,
  Activity,
} from "lucide-react";
import { PartyBarChart } from "@/components/charts/party-bar-chart";
import { EngagementPieChart } from "@/components/charts/engagement-pie-chart";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { SkeletonMetricCard, SkeletonCard } from "@/components/ui/skeleton";
import { PartyBadge } from "@/components/ui/badge";

export default function DashboardPage() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["dashboard-overview"],
    queryFn: () => api.get<DashboardStats>("/dashboard/overview"),
  });

  const { data: parties, isLoading: partiesLoading } = useQuery({
    queryKey: ["analytics-parties"],
    queryFn: () => api.get<any[]>("/analytics/parties"),
  });

  const { data: topUsers, isLoading: topUsersLoading } = useQuery({
    queryKey: ["analytics-engagement-top5"],
    queryFn: () => api.get<any[]>("/analytics/engagement?limit=5"),
  });

  // Engagement breakdown for pie chart
  const engagementData = stats
    ? [
        { name: "Begeniler", value: stats.total_likes || 0 },
        { name: "Retweetler", value: (stats as any).total_retweets_count || 0 },
        { name: "Yorumlar", value: stats.total_replies || 0 },
      ]
    : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500">Sistem genel durumu ve ozet istatistikler</p>
      </div>

      {/* Main Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statsLoading ? (
          <>
            <SkeletonMetricCard />
            <SkeletonMetricCard />
            <SkeletonMetricCard />
            <SkeletonMetricCard />
          </>
        ) : (
          <>
            <MetricCard
              title="Toplam Tweet"
              value={stats?.total_tweets?.toLocaleString("tr-TR") || "0"}
              icon={<BarChart3 className="h-5 w-5" />}
              description={`${stats?.total_original?.toLocaleString("tr-TR") || 0} orijinal`}
            />
            <MetricCard
              title="Meclis Uyesi"
              value={stats?.total_councilors?.toLocaleString("tr-TR") || "0"}
              icon={<Users className="h-5 w-5" />}
              description={`${stats?.active_users || 0} aktif`}
            />
            <MetricCard
              title="Toplam Like"
              value={stats?.total_likes?.toLocaleString("tr-TR") || "0"}
              icon={<Heart className="h-5 w-5" />}
            />
            <MetricCard
              title="Toplam Gorus"
              value={stats?.total_views?.toLocaleString("tr-TR") || "0"}
              icon={<Eye className="h-5 w-5" />}
            />
          </>
        )}
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {statsLoading ? (
          <>
            <SkeletonMetricCard />
            <SkeletonMetricCard />
            <SkeletonMetricCard />
          </>
        ) : (
          <>
            <MetricCard
              title="Toplam Yorum"
              value={stats?.total_replies?.toLocaleString("tr-TR") || "0"}
              icon={<MessageCircle className="h-5 w-5" />}
              className="bg-gradient-to-br from-blue-50 to-white"
            />
            <MetricCard
              title="Toplam Retweet"
              value={(stats as any)?.total_retweets_count?.toLocaleString("tr-TR") || "0"}
              icon={<Repeat2 className="h-5 w-5" />}
              className="bg-gradient-to-br from-green-50 to-white"
            />
            <MetricCard
              title="Ort. Engagement"
              value={
                stats?.total_tweets && stats.total_tweets > 0
                  ? Math.round(
                      ((stats.total_likes || 0) +
                        (stats.total_replies || 0) +
                        ((stats as any).total_retweets_count || 0)) /
                        stats.total_tweets
                    ).toLocaleString("tr-TR")
                  : "0"
              }
              icon={<TrendingUp className="h-5 w-5" />}
              description="tweet basina"
              className="bg-gradient-to-br from-purple-50 to-white"
            />
          </>
        )}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Party Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5 text-blue-600" />
              Parti Dagilimi
            </CardTitle>
          </CardHeader>
          <CardContent>
            {partiesLoading ? (
              <div className="h-[300px] flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
              </div>
            ) : (
              <PartyBarChart
                data={parties?.slice(0, 8) || []}
                dataKey="member_count"
                height={300}
              />
            )}
          </CardContent>
        </Card>

        {/* Engagement Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-blue-600" />
              Etkilesim Dagilimi
            </CardTitle>
          </CardHeader>
          <CardContent>
            {statsLoading ? (
              <div className="h-[300px] flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
              </div>
            ) : (
              <EngagementPieChart data={engagementData} height={300} />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Top Performers */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-blue-600" />
            En Aktif Uyeler
          </CardTitle>
        </CardHeader>
        <CardContent>
          {topUsersLoading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="flex items-center gap-4">
                  <div className="w-8 h-8 bg-gray-200 rounded-full animate-pulse" />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-gray-200 rounded w-1/3 animate-pulse" />
                    <div className="h-3 bg-gray-200 rounded w-1/4 animate-pulse" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              {topUsers?.map((user: any, index: number) => (
                <div
                  key={user.username}
                  className="flex items-center gap-4 p-3 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600 font-bold text-sm">
                    {index + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-gray-900 truncate">
                        {user.name}
                      </p>
                      <PartyBadge party={user.party || "BAGIMSIZ"} />
                    </div>
                    <p className="text-sm text-gray-500">@{user.username}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-blue-600">
                      {user.total_engagement?.toLocaleString("tr-TR")}
                    </p>
                    <p className="text-xs text-gray-500">etkilesim</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
