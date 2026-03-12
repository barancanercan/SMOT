"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Cell,
} from "recharts";

interface PartyData {
  party: string;
  member_count: number;
  total_tweets?: number;
  total_followers?: number;
}

interface PartyBarChartProps {
  data: PartyData[];
  dataKey?: "member_count" | "total_tweets" | "total_followers";
  height?: number;
  showComparison?: boolean;
}

// Turkish party colors
const PARTY_COLORS: Record<string, string> = {
  CHP: "#E53935",
  AKP: "#FF9800",
  MHP: "#C62828",
  IYI: "#1E88E5",
  HDP: "#7B1FA2",
  DEM: "#7B1FA2",
  SAADET: "#43A047",
  BBP: "#D32F2F",
  DEVA: "#00ACC1",
  GELECEK: "#26A69A",
  ZP: "#EC407A",
  TIP: "#F44336",
  BAGIMSIZ: "#78909C",
};

const getPartyColor = (party: string): string => {
  return PARTY_COLORS[party.toUpperCase()] || PARTY_COLORS.BAGIMSIZ;
};

export function PartyBarChart({
  data,
  dataKey = "member_count",
  height = 300,
  showComparison = false,
}: PartyBarChartProps) {
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

  const formatNumber = (num: number) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
    if (num >= 1000) return (num / 1000).toFixed(1) + "K";
    return num.toLocaleString("tr-TR");
  };

  const dataKeyLabel: Record<string, string> = {
    member_count: "Uye Sayisi",
    total_tweets: "Tweet Sayisi",
    total_followers: "Takipci Sayisi",
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={data}
        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        layout="vertical"
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" horizontal />
        <XAxis
          type="number"
          tick={{ fontSize: 12, fill: "#6B7280" }}
          tickFormatter={formatNumber}
          tickLine={false}
          axisLine={{ stroke: "#E5E7EB" }}
        />
        <YAxis
          type="category"
          dataKey="party"
          tick={{ fontSize: 12, fill: "#374151" }}
          tickLine={false}
          axisLine={{ stroke: "#E5E7EB" }}
          width={80}
        />
        <Tooltip
          formatter={(value: number) => [formatNumber(value), dataKeyLabel[dataKey]]}
          contentStyle={{
            backgroundColor: "white",
            border: "1px solid #E5E7EB",
            borderRadius: "8px",
            boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
          }}
        />
        {showComparison && <Legend />}
        <Bar
          dataKey={dataKey}
          name={dataKeyLabel[dataKey]}
          radius={[0, 4, 4, 0]}
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={getPartyColor(entry.party)} />
          ))}
        </Bar>
        {showComparison && dataKey === "member_count" && (
          <Bar
            dataKey="total_tweets"
            name="Tweet Sayisi"
            fill="#60A5FA"
            radius={[0, 4, 4, 0]}
          />
        )}
      </BarChart>
    </ResponsiveContainer>
  );
}
