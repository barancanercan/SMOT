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
  default: "bg-gray-100 text-gray-800",
  primary: "bg-blue-100 text-blue-800",
  secondary: "bg-gray-100 text-gray-600",
  success: "bg-green-100 text-green-800",
  warning: "bg-yellow-100 text-yellow-800",
  danger: "bg-red-100 text-red-800",
  info: "bg-cyan-100 text-cyan-800",
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
  CHP: "bg-red-100 text-red-800",
  AKP: "bg-orange-100 text-orange-800",
  MHP: "bg-red-200 text-red-900",
  IYI: "bg-blue-100 text-blue-800",
  HDP: "bg-purple-100 text-purple-800",
  DEM: "bg-purple-100 text-purple-800",
  BBP: "bg-red-100 text-red-700",
  SAADET: "bg-green-100 text-green-800",
  DEVA: "bg-teal-100 text-teal-800",
  GELECEK: "bg-cyan-100 text-cyan-800",
  ZP: "bg-pink-100 text-pink-800",
  TIP: "bg-rose-100 text-rose-800",
  BAGIMSIZ: "bg-gray-100 text-gray-600",
};

export function PartyBadge({
  party,
  className,
}: {
  party: PartyType;
  className?: string;
}) {
  const colorClass = partyColors[party.toUpperCase()] || partyColors.BAGIMSIZ;

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
  active: "bg-green-100 text-green-800",
  inactive: "bg-gray-100 text-gray-600",
  pending: "bg-yellow-100 text-yellow-800",
  error: "bg-red-100 text-red-800",
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
