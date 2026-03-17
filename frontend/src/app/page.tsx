"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  Shield,
  Brain,
  BarChart3,
  Users,
  FileText,
  Zap,
  ChevronRight,
  Activity,
  Target,
  Eye,
  TrendingUp,
  GitCompare,
  Sparkles,
  ArrowRight,
  CheckCircle,
  Globe,
  Lock,
  Cpu,
} from "lucide-react";

export default function LandingPage() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className="min-h-screen bg-[#050505] text-white overflow-hidden">
      {/* Background Effects */}
      <div className="fixed inset-0 pointer-events-none">
        {/* Grid */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `linear-gradient(#4DA3FF 1px, transparent 1px), linear-gradient(90deg, #4DA3FF 1px, transparent 1px)`,
            backgroundSize: "60px 60px",
          }}
        />
        {/* Gradient Orbs */}
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-[#4DA3FF]/10 rounded-full blur-[150px]" />
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-[#00D1B2]/10 rounded-full blur-[150px]" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-purple-500/5 rounded-full blur-[200px]" />
      </div>

      {/* Navigation */}
      <nav className="relative z-50 border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="absolute inset-0 bg-[#4DA3FF]/30 rounded-xl blur-xl" />
                <Image
                  src="/transparan_logo.png"
                  alt="M.I.S Logo"
                  width={48}
                  height={48}
                  className="relative z-10"
                />
              </div>
              <div>
                <h1 className="text-2xl font-black bg-gradient-to-r from-white via-blue-200 to-[#4DA3FF] bg-clip-text text-transparent">
                  M.I.S
                </h1>
                <p className="text-[10px] text-gray-500 tracking-widest uppercase">
                  Meclis Istihbarat Sistemi
                </p>
              </div>
            </div>

            <div className="flex items-center gap-6">
              <a href="#ozellikler" className="text-sm text-gray-400 hover:text-white transition-colors">
                Ozellikler
              </a>
              <a href="#hakkimizda" className="text-sm text-gray-400 hover:text-white transition-colors">
                Hakkimizda
              </a>
              <a href="#teknoloji" className="text-sm text-gray-400 hover:text-white transition-colors">
                Teknoloji
              </a>
              <Link
                href="/dashboard"
                className="group flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-[#4DA3FF] to-[#00D1B2] text-white text-sm font-medium rounded-lg hover:opacity-90 transition-all shadow-lg shadow-[#4DA3FF]/25"
              >
                Panele Giris
                <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform" />
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative z-10 pt-20 pb-32">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-4xl mx-auto">
            {/* Badge */}
            <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#4DA3FF]/10 border border-[#4DA3FF]/20 mb-8 transition-all duration-1000 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
              <Sparkles className="h-4 w-4 text-[#4DA3FF]" />
              <span className="text-sm text-[#4DA3FF]">Yapay Zeka Destekli Istihbarat Platformu</span>
            </div>

            {/* Main Title */}
            <h1 className={`text-5xl md:text-7xl font-black mb-6 leading-tight transition-all duration-1000 delay-100 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
              <span className="bg-gradient-to-r from-white via-white to-gray-400 bg-clip-text text-transparent">
                Meclis Istihbarat
              </span>
              <br />
              <span className="bg-gradient-to-r from-[#4DA3FF] via-[#00D1B2] to-[#4DA3FF] bg-clip-text text-transparent">
                Sistemi
              </span>
            </h1>

            {/* Subtitle */}
            <p className={`text-xl text-gray-400 mb-10 max-w-2xl mx-auto leading-relaxed transition-all duration-1000 delay-200 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
              Turkiye'nin Belediye Meclis uyelerinin sosyal medya aktivitelerini
              analiz eden, yapay zeka destekli profesyonel istihbarat raporlari ureten
              <span className="text-white font-medium"> modern SaaS platformu</span>.
            </p>

            {/* CTA Buttons */}
            <div className={`flex items-center justify-center gap-4 transition-all duration-1000 delay-300 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
              <Link
                href="/dashboard"
                className="group flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-[#4DA3FF] to-[#00D1B2] text-white font-semibold rounded-xl hover:opacity-90 transition-all shadow-2xl shadow-[#4DA3FF]/30 hover:shadow-[#4DA3FF]/50"
              >
                <Shield className="h-5 w-5" />
                Istihbarat Paneline Giris
                <ChevronRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </Link>
              <a
                href="#ozellikler"
                className="flex items-center gap-2 px-8 py-4 bg-white/5 border border-white/10 text-white font-medium rounded-xl hover:bg-white/10 transition-all"
              >
                <Eye className="h-5 w-5" />
                Ozellikleri Incele
              </a>
            </div>

            {/* Stats */}
            <div className={`grid grid-cols-3 gap-8 mt-20 max-w-3xl mx-auto transition-all duration-1000 delay-500 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
              <div className="text-center p-6 rounded-2xl bg-white/[0.02] border border-white/5">
                <p className="text-4xl font-bold bg-gradient-to-r from-[#4DA3FF] to-[#00D1B2] bg-clip-text text-transparent">
                  Gercek Zamanli
                </p>
                <p className="text-sm text-gray-500 mt-1">Veri Takibi</p>
              </div>
              <div className="text-center p-6 rounded-2xl bg-white/[0.02] border border-white/5">
                <p className="text-4xl font-bold bg-gradient-to-r from-[#4DA3FF] to-[#00D1B2] bg-clip-text text-transparent">
                  Derin Analiz
                </p>
                <p className="text-sm text-gray-500 mt-1">Tweet Inceleme</p>
              </div>
              <div className="text-center p-6 rounded-2xl bg-white/[0.02] border border-white/5">
                <p className="text-4xl font-bold bg-gradient-to-r from-[#4DA3FF] to-[#00D1B2] bg-clip-text text-transparent">
                  AI
                </p>
                <p className="text-sm text-gray-500 mt-1">Destekli Raporlar</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="ozellikler" className="relative z-10 py-24 border-t border-white/5">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-purple-500/10 border border-purple-500/20 mb-6">
              <Zap className="h-4 w-4 text-purple-400" />
              <span className="text-sm text-purple-400">Platform Ozellikleri</span>
            </div>
            <h2 className="text-4xl font-bold text-white mb-4">
              Guclu Analiz Araclari
            </h2>
            <p className="text-gray-400 max-w-2xl mx-auto">
              Yapay zeka destekli analizlerden detayli raporlara, tum ihtiyaclariniz icin
              kapsamli cozumler sunuyoruz.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Feature 1 */}
            <div className="group relative p-8 rounded-2xl bg-gradient-to-br from-white/[0.05] to-transparent border border-white/10 hover:border-[#4DA3FF]/30 transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-[#4DA3FF]/0 to-[#4DA3FF]/0 group-hover:from-[#4DA3FF]/5 group-hover:to-transparent rounded-2xl transition-all" />
              <div className="relative">
                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-[#4DA3FF]/20 to-[#4DA3FF]/5 border border-[#4DA3FF]/30 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <Brain className="h-7 w-7 text-[#4DA3FF]" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">Yapay Zeka Analizi</h3>
                <p className="text-gray-400 text-sm leading-relaxed">
                  OpenAI GPT destekli derin icerik analizi. Yesil/Kirmizi/Gri Takim framework'u
                  ile parti sadakati ve muhalefet egilimlerini tespit.
                </p>
              </div>
            </div>

            {/* Feature 2 */}
            <div className="group relative p-8 rounded-2xl bg-gradient-to-br from-white/[0.05] to-transparent border border-white/10 hover:border-[#00D1B2]/30 transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-[#00D1B2]/0 to-[#00D1B2]/0 group-hover:from-[#00D1B2]/5 group-hover:to-transparent rounded-2xl transition-all" />
              <div className="relative">
                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-[#00D1B2]/20 to-[#00D1B2]/5 border border-[#00D1B2]/30 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <FileText className="h-7 w-7 text-[#00D1B2]" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">Detayli Raporlama</h3>
                <p className="text-gray-400 text-sm leading-relaxed">
                  Kullanici, parti ve coklu kullanici raporlari. Bireysel ve toplu LLM
                  analizleri ile profesyonel istihbarat ciktilari.
                </p>
              </div>
            </div>

            {/* Feature 3 */}
            <div className="group relative p-8 rounded-2xl bg-gradient-to-br from-white/[0.05] to-transparent border border-white/10 hover:border-purple-500/30 transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-purple-500/0 to-purple-500/0 group-hover:from-purple-500/5 group-hover:to-transparent rounded-2xl transition-all" />
              <div className="relative">
                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-purple-500/20 to-purple-500/5 border border-purple-500/30 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <GitCompare className="h-7 w-7 text-purple-400" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">Karsilastirma Modulu</h3>
                <p className="text-gray-400 text-sm leading-relaxed">
                  2-10 kullaniciyi yan yana karsilastirin. Metrik kartlari, grafikler ve
                  AI destekli karsilastirma ozeti.
                </p>
              </div>
            </div>

            {/* Feature 4 */}
            <div className="group relative p-8 rounded-2xl bg-gradient-to-br from-white/[0.05] to-transparent border border-white/10 hover:border-orange-500/30 transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-orange-500/0 to-orange-500/0 group-hover:from-orange-500/5 group-hover:to-transparent rounded-2xl transition-all" />
              <div className="relative">
                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-orange-500/20 to-orange-500/5 border border-orange-500/30 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <BarChart3 className="h-7 w-7 text-orange-400" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">Gelismis Grafikler</h3>
                <p className="text-gray-400 text-sm leading-relaxed">
                  Parti dagilimi, takipci siralamalari, etkilesim analizleri.
                  Interaktif bar ve radar chartlar ile gorsel analiz.
                </p>
              </div>
            </div>

            {/* Feature 5 */}
            <div className="group relative p-8 rounded-2xl bg-gradient-to-br from-white/[0.05] to-transparent border border-white/10 hover:border-pink-500/30 transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-pink-500/0 to-pink-500/0 group-hover:from-pink-500/5 group-hover:to-transparent rounded-2xl transition-all" />
              <div className="relative">
                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-pink-500/20 to-pink-500/5 border border-pink-500/30 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <Users className="h-7 w-7 text-pink-400" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">Kullanici Yonetimi</h3>
                <p className="text-gray-400 text-sm leading-relaxed">
                  Tekli ve toplu kullanici ekleme. CSV import destegi, cascade delete
                  ile tam veri yonetimi.
                </p>
              </div>
            </div>

            {/* Feature 6 */}
            <div className="group relative p-8 rounded-2xl bg-gradient-to-br from-white/[0.05] to-transparent border border-white/10 hover:border-cyan-500/30 transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/0 to-cyan-500/0 group-hover:from-cyan-500/5 group-hover:to-transparent rounded-2xl transition-all" />
              <div className="relative">
                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-cyan-500/20 to-cyan-500/5 border border-cyan-500/30 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <TrendingUp className="h-7 w-7 text-cyan-400" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">Etkilesim Analizi</h3>
                <p className="text-gray-400 text-sm leading-relaxed">
                  Like, retweet, yorum ve goruntulenme metrikleri.
                  En aktif kullanicilar ve trend analizleri.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* About Section */}
      <section id="hakkimizda" className="relative z-10 py-24 border-t border-white/5">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div>
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#00D1B2]/10 border border-[#00D1B2]/20 mb-6">
                <Target className="h-4 w-4 text-[#00D1B2]" />
                <span className="text-sm text-[#00D1B2]">Hakkimizda</span>
              </div>
              <h2 className="text-4xl font-bold text-white mb-6">
                Siyasi Istihbarat Icin
                <br />
                <span className="bg-gradient-to-r from-[#4DA3FF] to-[#00D1B2] bg-clip-text text-transparent">
                  Yeni Nesil Platform
                </span>
              </h2>
              <p className="text-gray-400 mb-6 leading-relaxed">
                Meclis Istihbarat Sistemi (M.I.S), Turkiye'deki belediye meclisi
                uyelerinin sosyal medya aktivitelerini takip eden ve analiz eden kapsamli
                bir istihbarat platformudur.
              </p>
              <p className="text-gray-400 mb-8 leading-relaxed">
                Yapay zeka destekli analiz motorumuz, her kullanicinin paylasimlarina
                <span className="text-white font-medium"> Yesil Takim </span> (parti sadakati),
                <span className="text-white font-medium"> Kirmizi Takim </span> (muhalefet elestirisi) ve
                <span className="text-white font-medium"> Gri Takim </span> (bagimsiz gundem)
                cercevesinde derinlemesine analiz uygular.
              </p>

              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-[#00D1B2] mt-0.5 flex-shrink-0" />
                  <p className="text-gray-300 text-sm">Gercek zamanli sosyal medya takibi ve veri toplama</p>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-[#00D1B2] mt-0.5 flex-shrink-0" />
                  <p className="text-gray-300 text-sm">OpenAI GPT ile otomatik icerik analizi ve siniflandirma</p>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-[#00D1B2] mt-0.5 flex-shrink-0" />
                  <p className="text-gray-300 text-sm">Profesyonel istihbarat raporlari ve karsilastirma modulleri</p>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-[#00D1B2] mt-0.5 flex-shrink-0" />
                  <p className="text-gray-300 text-sm">Tam Turkce arayuz ve yerel veri isleyici destegi</p>
                </div>
              </div>
            </div>

            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-br from-[#4DA3FF]/20 to-[#00D1B2]/20 rounded-3xl blur-3xl" />
              <div className="relative bg-[#0A0A0A] border border-white/10 rounded-3xl p-8">
                {/* Analysis Framework Visual */}
                <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                  <Activity className="h-5 w-5 text-[#4DA3FF]" />
                  Analiz Framework'u
                </h3>

                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="w-3 h-3 rounded-full bg-emerald-500" />
                      <span className="font-semibold text-emerald-400">Yesil Takim</span>
                    </div>
                    <p className="text-sm text-gray-400 pl-6">
                      Parti sadakati, liderlik destegi, parti etkinlikleri, basarilari one cikarma
                    </p>
                  </div>

                  <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="w-3 h-3 rounded-full bg-red-500" />
                      <span className="font-semibold text-red-400">Kirmizi Takim</span>
                    </div>
                    <p className="text-sm text-gray-400 pl-6">
                      Rakip parti elestirisi, hukumet politikalari, siyasi polemik
                    </p>
                  </div>

                  <div className="p-4 rounded-xl bg-gray-500/10 border border-gray-500/20">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="w-3 h-3 rounded-full bg-gray-500" />
                      <span className="font-semibold text-gray-400">Gri Takim</span>
                    </div>
                    <p className="text-sm text-gray-400 pl-6">
                      Yerel hizmetler, kisisel paylasimlar, apolitik icerik
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Technology Section */}
      <section id="teknoloji" className="relative z-10 py-24 border-t border-white/5">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-cyan-500/10 border border-cyan-500/20 mb-6">
              <Cpu className="h-4 w-4 text-cyan-400" />
              <span className="text-sm text-cyan-400">Teknoloji Yigini</span>
            </div>
            <h2 className="text-4xl font-bold text-white mb-4">
              Modern Teknoloji Altyapisi
            </h2>
            <p className="text-gray-400 max-w-2xl mx-auto">
              En guncel ve guvenilir teknolojilerle insa edilmis, olceklenebilir ve
              yuksek performansli bir platform.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/5 text-center hover:border-white/10 transition-all">
              <div className="text-3xl font-bold text-[#4DA3FF] mb-2">FastAPI</div>
              <p className="text-sm text-gray-500">Backend API</p>
            </div>
            <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/5 text-center hover:border-white/10 transition-all">
              <div className="text-3xl font-bold text-white mb-2">Next.js 14</div>
              <p className="text-sm text-gray-500">Frontend</p>
            </div>
            <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/5 text-center hover:border-white/10 transition-all">
              <div className="text-3xl font-bold text-[#00D1B2] mb-2">OpenAI</div>
              <p className="text-sm text-gray-500">LLM Provider</p>
            </div>
            <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/5 text-center hover:border-white/10 transition-all">
              <div className="text-3xl font-bold text-purple-400 mb-2">PostgreSQL</div>
              <p className="text-sm text-gray-500">Veritabani</p>
            </div>
          </div>

          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 rounded-2xl bg-gradient-to-br from-[#4DA3FF]/10 to-transparent border border-[#4DA3FF]/20">
              <Globe className="h-8 w-8 text-[#4DA3FF] mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">Tam Turkce Destek</h3>
              <p className="text-sm text-gray-400">
                Arayuzden raporlara, tum sistem Turkce dil destegi ile calisir.
              </p>
            </div>
            <div className="p-6 rounded-2xl bg-gradient-to-br from-[#00D1B2]/10 to-transparent border border-[#00D1B2]/20">
              <Lock className="h-8 w-8 text-[#00D1B2] mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">Guvenli Altyapi</h3>
              <p className="text-sm text-gray-400">
                Modern guvenlik standartlari ve sifreleme protokolleri ile korunur.
              </p>
            </div>
            <div className="p-6 rounded-2xl bg-gradient-to-br from-purple-500/10 to-transparent border border-purple-500/20">
              <Zap className="h-8 w-8 text-purple-400 mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">Yuksek Performans</h3>
              <p className="text-sm text-gray-400">
                Optimize edilmis sorgular ve onbellekleme ile hizli cevap sureleri.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative z-10 py-24 border-t border-white/5">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-r from-[#4DA3FF]/20 via-purple-500/20 to-[#00D1B2]/20 blur-3xl rounded-full" />
            <div className="relative bg-[#0A0A0A] border border-white/10 rounded-3xl p-12">
              <h2 className="text-4xl font-bold text-white mb-4">
                Istihbarat Analizine Baslayin
              </h2>
              <p className="text-gray-400 mb-8 max-w-xl mx-auto">
                Meclis uyelerinin sosyal medya aktivitelerini analiz etmeye hemen baslayabilirsiniz.
                Yapay zeka destekli raporlar sizi bekliyor.
              </p>
              <Link
                href="/dashboard"
                className="group inline-flex items-center gap-3 px-10 py-5 bg-gradient-to-r from-[#4DA3FF] to-[#00D1B2] text-white font-semibold rounded-xl hover:opacity-90 transition-all shadow-2xl shadow-[#4DA3FF]/30 hover:shadow-[#4DA3FF]/50 text-lg"
              >
                <Shield className="h-6 w-6" />
                Panele Giris Yap
                <ChevronRight className="h-6 w-6 group-hover:translate-x-1 transition-transform" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/5 py-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6 mb-8">
            <div className="flex items-center gap-3">
              <Image
                src="/transparan_logo.png"
                alt="M.I.S Logo"
                width={32}
                height={32}
              />
              <div className="flex items-center gap-2">
                <span className="font-bold text-white">M.I.S</span>
                <span className="text-[10px] text-[#4DA3FF] font-medium px-1.5 py-0.5 bg-[#4DA3FF]/10 rounded">v3.2</span>
              </div>
            </div>
            <p className="text-gray-500 text-sm">
              Meclis Istihbarat Sistemi - Yapay Zeka ile Siyasi Analiz
            </p>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <div className="w-2 h-2 rounded-full bg-[#00D1B2] animate-pulse" />
              <span>Sistem Aktif</span>
            </div>
          </div>

          {/* Creator Credit */}
          <div className="pt-6 border-t border-white/5 text-center">
            <p className="text-gray-600 text-sm">
              Tasarim ve Gelistirme
            </p>
            <p className="text-white font-semibold mt-1 bg-gradient-to-r from-[#4DA3FF] to-[#00D1B2] bg-clip-text text-transparent">
              Baran Can Ercan
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
