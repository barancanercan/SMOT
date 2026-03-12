"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { MetricCard } from "@/components/features/metric-card";
import { BarChart3, Users, Heart, Eye } from "lucide-react";

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ["dashboard-overview"],
    queryFn: () => api.get("/dashboard/overview"),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500">Sistem genel durumu</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Toplam Tweet"
          value={stats?.total_tweets?.toLocaleString() || "0"}
          icon={<BarChart3 className="h-5 w-5" />}
          description={`${stats?.total_original?.toLocaleString() || 0} orijinal`}
        />
        <MetricCard
          title="Meclis Uyesi"
          value={stats?.total_councilors?.toLocaleString() || "0"}
          icon={<Users className="h-5 w-5" />}
          description={`${stats?.active_users || 0} aktif`}
        />
        <MetricCard
          title="Toplam Like"
          value={stats?.total_likes?.toLocaleString() || "0"}
          icon={<Heart className="h-5 w-5" />}
        />
        <MetricCard
          title="Toplam Gorus"
          value={stats?.total_views?.toLocaleString() || "0"}
          icon={<Eye className="h-5 w-5" />}
        />
      </div>
    </div>
  );
}
