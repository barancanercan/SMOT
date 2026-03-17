"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  BarChart3,
  FileText,
  Flame,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/analytics", label: "Grafikler", icon: BarChart3 },
  { href: "/reports", label: "Raporlar", icon: FileText },
  { href: "/tweets", label: "Top Tweets", icon: Flame },
  { href: "/system", label: "Sistem", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-[#0A0A0A] border-r border-white/10 min-h-screen">
      <div className="p-6 border-b border-white/10">
        <div className="flex items-center gap-3 mb-2">
          <Image
            src="/transparan_logo.png"
            alt="Meclis Istihbarat Logo"
            width={40}
            height={40}
            className="object-contain"
          />
          <div>
            <h1 className="text-xl font-bold text-white">
              Meclis Istihbarat
            </h1>
            <p className="text-sm text-gray-500">Analiz Platformu</p>
          </div>
        </div>
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
