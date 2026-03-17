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
  "AK Parti": "#FF9800",
  MHP: "#C62828",
  IYI: "#1E88E5",
  "IYI Parti": "#1E88E5",
  HDP: "#7B1FA2",
  DEM: "#7B1FA2",
  "DEM Parti": "#7B1FA2",
  SAADET: "#43A047",
  BBP: "#D32F2F",
  DEVA: "#00ACC1",
  GELECEK: "#26A69A",
  ZP: "#EC407A",
  TIP: "#F44336",
  BAGIMSIZ: "#78909C",
};

const getPartyColor = (party: string): string => {
  // Try exact match first, then uppercase
  return PARTY_COLORS[party] || PARTY_COLORS[party.toUpperCase()] || PARTY_COLORS.BAGIMSIZ;
};

// Custom dark tooltip component
const CustomTooltip = ({ active, payload, label, dataKeyLabel }: any) => {
  if (!active || !payload || !payload.length) return null;

  const formatNumber = (num: number) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
    if (num >= 1000) return (num / 1000).toFixed(1) + "K";
    return num.toLocaleString("tr-TR");
  };

  return (
    <div className="bg-[#1A1A1A] border border-white/20 rounded-lg px-4 py-3 shadow-xl">
      <p className="text-white font-semibold mb-1">{label}</p>
      {payload.map((entry: any, index: number) => (
        <p key={index} className="text-gray-300 text-sm">
          <span style={{ color: entry.fill }}>{entry.name}:</span>{" "}
          <span className="font-mono">{formatNumber(entry.value)}</span>
        </p>
      ))}
    </div>
  );
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
        className="flex items-center justify-center bg-[#0B0B0B]/50 border border-white/10 rounded-lg"
        style={{ height }}
      >
        <p className="text-gray-500 font-mono text-sm">Veri bulunamadi</p>
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
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" horizontal />
        <XAxis
          type="number"
          tick={{ fontSize: 12, fill: "#9CA3AF" }}
          tickFormatter={formatNumber}
          tickLine={false}
          axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
        />
        <YAxis
          type="category"
          dataKey="party"
          tick={{ fontSize: 12, fill: "#E5E7EB" }}
          tickLine={false}
          axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
          width={80}
        />
        <Tooltip
          content={<CustomTooltip dataKeyLabel={dataKeyLabel} />}
          cursor={{ fill: "rgba(255,255,255,0.05)" }}
        />
        {showComparison && (
          <Legend
            wrapperStyle={{ color: "#E5E7EB" }}
            formatter={(value) => <span className="text-gray-300">{value}</span>}
          />
        )}
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
