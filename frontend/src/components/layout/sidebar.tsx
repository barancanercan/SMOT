"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  BarChart3,
  FileText,
  Flame,
  Users,
  GitCompare,
  Camera,
  MessageCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard", label: "Genel Bakış", icon: LayoutDashboard },
  { href: "/analytics", label: "Grafikler", icon: BarChart3 },
  { href: "/reports", label: "Raporlar", icon: FileText },
  { href: "/chat", label: "Sosyal Medya Sohbet", icon: MessageCircle },
  { href: "/comparison", label: "Karşılaştırma", icon: GitCompare },
  { href: "/users", label: "Kullanıcılar", icon: Users },
  { href: "/tweets", label: "Top Tweetler", icon: Flame },
  { href: "/instagram", label: "Top Postlar", icon: Camera },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-[#0A0A0A] border-r border-white/10 min-h-screen">
      <div className="p-6 border-b border-white/10">
        <Link href="/dashboard" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
          <div className="relative">
            <div className="absolute inset-0 bg-[#4DA3FF]/20 rounded-xl blur-lg" />
            <Image
              src="/transparan_logo.png"
              alt="SMOT Logo"
              width={44}
              height={44}
              className="object-contain relative z-10"
            />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-black bg-gradient-to-r from-white via-blue-200 to-[#4DA3FF] bg-clip-text text-transparent tracking-tight">
                SMOT
              </h1>
              <div className="h-4 w-px bg-gradient-to-b from-transparent via-[#4DA3FF]/50 to-transparent" />
              <span className="text-[10px] font-medium text-[#4DA3FF] uppercase tracking-widest">v3.2</span>
            </div>
            <p className="text-xs text-gray-500 mt-0.5">Sosyal Medya Gözlem Aracı</p>
          </div>
        </Link>
      </div>

      <nav className="px-4 space-y-1 mt-6">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 relative",
                isActive
                  ? "text-blue-400 bg-blue-500/10 border-l-2 border-blue-500 ml-0"
                  : "text-gray-400 hover:text-white hover:bg-white/5 border-l-2 border-transparent ml-0"
              )}
            >
              <Icon className="h-5 w-5 ml-1" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
