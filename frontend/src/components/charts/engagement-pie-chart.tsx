"use client";

import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";

interface EngagementData {
  name: string;
  value: number;
}

interface EngagementPieChartProps {
  data: EngagementData[];
  height?: number;
  showLegend?: boolean;
}

const COLORS = ["#4DA3FF", "#00D1B2", "#F59E0B", "#EF4444", "#8B5CF6"];

// Custom dark tooltip
const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload || !payload.length) return null;

  const formatNumber = (num: number) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
    if (num >= 1000) return (num / 1000).toFixed(1) + "K";
    return num.toLocaleString("tr-TR");
  };

  const entry = payload[0];
  return (
    <div className="bg-[#1A1A1A] border border-white/20 rounded-lg px-4 py-3 shadow-xl">
      <p className="text-white font-semibold mb-1">{entry.name}</p>
      <p className="text-gray-300 text-sm font-mono">{formatNumber(entry.value)}</p>
    </div>
  );
};

export function EngagementPieChart({
  data,
  height = 300,
  showLegend = true,
}: EngagementPieChartProps) {
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

  const total = data.reduce((sum, item) => sum + item.value, 0);

  const renderCustomLabel = ({
    cx,
    cy,
    midAngle,
    innerRadius,
    outerRadius,
    percent,
  }: {
    cx: number;
    cy: number;
    midAngle: number;
    innerRadius: number;
    outerRadius: number;
    percent: number;
  }) => {
    if (percent < 0.05) return null; // Don't show label for small slices

    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text
        x={x}
        y={y}
        fill="white"
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={12}
        fontWeight={600}
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={renderCustomLabel}
          outerRadius={100}
          innerRadius={40}
          fill="#8884d8"
          dataKey="value"
          paddingAngle={2}
          stroke="rgba(255,255,255,0.1)"
          strokeWidth={1}
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        {showLegend && (
          <Legend
            verticalAlign="bottom"
            height={36}
            formatter={(value) => (
              <span className="text-sm text-gray-300">{value}</span>
            )}
          />
        )}
      </PieChart>
    </ResponsiveContainer>
  );
}

// Simplified variant for small spaces
export function MiniEngagementChart({
  likes,
  retweets,
  replies,
}: {
  likes: number;
  retweets: number;
  replies: number;
}) {
  const data = [
    { name: "Begeniler", value: likes },
    { name: "Retweetler", value: retweets },
    { name: "Yorumlar", value: replies },
  ];

  return <EngagementPieChart data={data} height={200} showLegend={false} />;
}
