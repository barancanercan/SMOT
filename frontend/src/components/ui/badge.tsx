import { ReactNode } from "react";
import { cn } from "@/lib/utils";

type BadgeVariant =
  | "default"
  | "primary"
  | "secondary"
  | "success"
  | "warning"
  | "danger"
  | "info";

interface BadgeProps {
  children: ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  default: "bg-gray-500/20 text-gray-300 border border-gray-500/30",
  primary: "bg-blue-500/20 text-blue-400 border border-blue-500/30",
  secondary: "bg-gray-500/20 text-gray-400 border border-gray-500/30",
  success: "bg-green-500/20 text-green-400 border border-green-500/30",
  warning: "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30",
  danger: "bg-red-500/20 text-red-400 border border-red-500/30",
  info: "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30",
};

export function Badge({
  children,
  variant = "default",
  className,
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
        variantStyles[variant],
        className
      )}
    >
      {children}
    </span>
  );
}

// Party-specific badges for Turkish political parties
type PartyType = "CHP" | "AKP" | "MHP" | "IYI" | "HDP" | "DEM" | "BBP" | "SAADET" | "DEVA" | "GELECEK" | "ZP" | "TIP" | "BAGIMSIZ" | string;

const partyColors: Record<string, string> = {
  "CHP": "bg-red-500/20 text-red-400 border border-red-500/30",
  "AKP": "bg-orange-500/20 text-orange-400 border border-orange-500/30",
  "AK PARTI": "bg-orange-500/20 text-orange-400 border border-orange-500/30",
  "MHP": "bg-red-600/20 text-red-400 border border-red-600/30",
  "IYI": "bg-blue-500/20 text-blue-400 border border-blue-500/30",
  "IYI PARTI": "bg-blue-500/20 text-blue-400 border border-blue-500/30",
  "İYİ PARTI": "bg-blue-500/20 text-blue-400 border border-blue-500/30",
  "HDP": "bg-purple-500/20 text-purple-400 border border-purple-500/30",
  "DEM": "bg-purple-500/20 text-purple-400 border border-purple-500/30",
  "DEM PARTI": "bg-purple-500/20 text-purple-400 border border-purple-500/30",
  "BBP": "bg-rose-500/20 text-rose-400 border border-rose-500/30",
  "BÜYÜK BIRLIK PARTISI": "bg-rose-500/20 text-rose-400 border border-rose-500/30",
  "BUYUK BIRLIK PARTISI": "bg-rose-500/20 text-rose-400 border border-rose-500/30",
  "SAADET": "bg-green-500/20 text-green-400 border border-green-500/30",
  "SAADET PARTISI": "bg-green-500/20 text-green-400 border border-green-500/30",
  "DEVA": "bg-teal-500/20 text-teal-400 border border-teal-500/30",
  "GELECEK": "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30",
  "ZP": "bg-pink-500/20 text-pink-400 border border-pink-500/30",
  "ZAFER PARTISI": "bg-pink-500/20 text-pink-400 border border-pink-500/30",
  "TIP": "bg-rose-500/20 text-rose-400 border border-rose-500/30",
  "TİP": "bg-rose-500/20 text-rose-400 border border-rose-500/30",
  "YENIDEN REFAH PARTISI": "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30",
  "MEMLEKET PARTISI": "bg-green-600/20 text-green-400 border border-green-600/30",
  "BAGIMSIZ": "bg-gray-500/20 text-gray-400 border border-gray-500/30",
  "BAĞIMSIZ": "bg-gray-500/20 text-gray-400 border border-gray-500/30",
};

// Normalize party name for lookup
function normalizePartyName(party: string): string {
  const normalized = party.toUpperCase().trim();
  // Remove Turkish characters for matching
  return normalized
    .replace(/İ/g, 'I')
    .replace(/Ü/g, 'U')
    .replace(/Ö/g, 'O')
    .replace(/Ş/g, 'S')
    .replace(/Ğ/g, 'G')
    .replace(/Ç/g, 'C');
}

export function PartyBadge({
  party,
  className,
}: {
  party: PartyType;
  className?: string;
}) {
  const upperParty = party.toUpperCase().trim();
  const normalizedParty = normalizePartyName(party);

  // Try exact match first, then normalized match
  let colorClass = partyColors[upperParty];
  if (!colorClass) {
    // Try normalized version
    for (const [key, value] of Object.entries(partyColors)) {
      if (normalizePartyName(key) === normalizedParty) {
        colorClass = value;
        break;
      }
    }
  }
  if (!colorClass) {
    colorClass = partyColors.BAGIMSIZ;
  }

  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
        colorClass,
        className
      )}
    >
      {party}
    </span>
  );
}

// Status badges
type StatusType = "active" | "inactive" | "pending" | "error";

const statusStyles: Record<StatusType, string> = {
  active: "bg-green-500/20 text-green-400 border border-green-500/30",
  inactive: "bg-gray-500/20 text-gray-400 border border-gray-500/30",
  pending: "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30",
  error: "bg-red-500/20 text-red-400 border border-red-500/30",
};

const statusLabels: Record<StatusType, string> = {
  active: "Aktif",
  inactive: "Pasif",
  pending: "Beklemede",
  error: "Hata",
};

export function StatusBadge({
  status,
  className,
}: {
  status: StatusType;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
        statusStyles[status],
        className
      )}
    >
      <span
        className={cn(
          "w-1.5 h-1.5 rounded-full mr-1.5",
          status === "active" && "bg-green-500",
          status === "inactive" && "bg-gray-400",
          status === "pending" && "bg-yellow-500",
          status === "error" && "bg-red-500"
        )}
      />
      {statusLabels[status]}
    </span>
  );
}
