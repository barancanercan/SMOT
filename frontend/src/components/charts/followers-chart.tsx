"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

interface DataPoint {
  date: string;
  followers: number;
  following?: number;
}

interface FollowersChartProps {
  data: DataPoint[];
  showFollowing?: boolean;
  height?: number;
}

export function FollowersChart({
  data,
  showFollowing = false,
  height = 300,
}: FollowersChartProps) {
  if (!data || data.length === 0) {
    return (
      <div
        className="flex items-center justify-center bg-gray-50 rounded-lg"
        style={{ height }}
      >
        <p className="text-gray-500">Veri bulunamadi</p>
      </div>
    );
  }

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString("tr-TR", {
        day: "2-digit",
        month: "short",
      });
    } catch {
      return dateStr;
    }
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
    if (num >= 1000) return (num / 1000).toFixed(1) + "K";
    return num.toLocaleString("tr-TR");
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart
        data={data}
        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 12, fill: "#6B7280" }}
          tickFormatter={formatDate}
          tickLine={false}
          axisLine={{ stroke: "#E5E7EB" }}
        />
        <YAxis
          tick={{ fontSize: 12, fill: "#6B7280" }}
          tickFormatter={formatNumber}
          tickLine={false}
          axisLine={{ stroke: "#E5E7EB" }}
        />
        <Tooltip
          labelFormatter={(value) => {
            try {
              return new Date(value).toLocaleDateString("tr-TR", {
                day: "numeric",
                month: "long",
                year: "numeric",
              });
            } catch {
              return value;
            }
          }}
          formatter={(value: number, name: string) => [
            formatNumber(value),
            name === "followers" ? "Takipci" : "Takip",
          ]}
          contentStyle={{
            backgroundColor: "white",
            border: "1px solid #E5E7EB",
            borderRadius: "8px",
            boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
          }}
        />
        {showFollowing && <Legend />}
        <Line
          type="monotone"
          dataKey="followers"
          name="Takipci"
          stroke="#2563EB"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4, fill: "#2563EB" }}
        />
        {showFollowing && (
          <Line
            type="monotone"
            dataKey="following"
            name="Takip"
            stroke="#10B981"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: "#10B981" }}
          />
        )}
      </LineChart>
    </ResponsiveContainer>
  );
}
