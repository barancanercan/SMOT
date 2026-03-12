import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { Sidebar } from "@/components/layout/sidebar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Meclis Istihbarat Sistemi",
  description: "Siyasi istihbarat analiz platformu",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr">
      <body className={inter.className}>
        <Providers>
          <div className="flex min-h-screen">
            <Sidebar />
            <main className="flex-1 p-6 bg-gray-50">{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
