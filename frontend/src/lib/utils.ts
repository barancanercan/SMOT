import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const PARTY_COLORS: Record<string, string> = {
  CHP: "#e31b23",
  AKP: "#ffa500",
  MHP: "#c8102e",
  BBP: "#1e3a8a",
  YRP: "#006400",
  BAGIMSIZ: "#808080",
};

export function getPartyColor(party: string): string {
  const normalized = party?.toUpperCase().trim() || "BAGIMSIZ";

  if (normalized.includes("CHP") || normalized.includes("CUMHURIYET")) {
    return PARTY_COLORS.CHP;
  }
  if (normalized.includes("AKP") || normalized.includes("ADALET")) {
    return PARTY_COLORS.AKP;
  }
  if (normalized.includes("MHP")) {
    return PARTY_COLORS.MHP;
  }
  if (normalized.includes("BBP")) {
    return PARTY_COLORS.BBP;
  }
  if (normalized.includes("YRP") || normalized.includes("YENIDEN")) {
    return PARTY_COLORS.YRP;
  }

  return PARTY_COLORS.BAGIMSIZ;
}

export function formatNumber(num: number): string {
  return new Intl.NumberFormat("tr-TR").format(num);
}
