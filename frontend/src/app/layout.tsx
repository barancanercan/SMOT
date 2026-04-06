import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "SMOT - Sosyal Medya Gozlem Araci",
  description: "Sosyal Medya Gozlem ve Analiz Platformu",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr">
      <body className={`${inter.className} bg-[#0B0B0B] text-white`}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
