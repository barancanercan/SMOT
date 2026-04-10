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
  MessageCircle,
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
                  alt="S.A.M Logo"
                  width={48}
                  height={48}
                  className="relative z-10"
                />
              </div>
              <div>
                <h1 className="text-2xl font-black bg-gradient-to-r from-white via-blue-200 to-[#4DA3FF] bg-clip-text text-transparent">
                  S.A.M
                </h1>
                <p className="text-[10px] text-gray-500 tracking-widest uppercase">
                  Stratejik Analiz Merkezi
                </p>
              </div>
            </div>

            <div className="flex items-center gap-6">
              <a href="#ozellikler" className="text-sm text-gray-400 hover:text-white transition-colors">
                Özellikler
              </a>
              <a href="#hakkimizda" className="text-sm text-gray-400 hover:text-white transition-colors">
                Hakkımızda
              </a>
              <a href="#teknoloji" className="text-sm text-gray-400 hover:text-white transition-colors">
                Teknoloji
              </a>
              <Link
                href="/dashboard"
                className="group flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-[#4DA3FF] to-[#00D1B2] text-white text-sm font-medium rounded-lg hover:opacity-90 transition-all shadow-lg shadow-[#4DA3FF]/25"
              >
                Panele Giriş
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
              <span className="text-sm text-[#4DA3FF]">Stratejik Analiz Platformu</span>
            </div>

            {/* Main Title */}
            <h1 className={`text-5xl md:text-7xl font-black mb-6 leading-tight transition-all duration-1000 delay-100 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
              <span className="bg-gradient-to-r from-white via-white to-gray-400 bg-clip-text text-transparent">
                Stratejik Analiz
              </span>
              <br />
              <span className="bg-gradient-to-r from-[#4DA3FF] via-[#00D1B2] to-[#4DA3FF] bg-clip-text text-transparent">
                Merkezi
              </span>
            </h1>

            {/* Subtitle */}
            <p className={`text-xl text-gray-400 mb-10 max-w-2xl mx-auto leading-relaxed transition-all duration-1000 delay-200 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
              Sosyal medya aktivitelerini takip eden ve
              analiz eden, profesyonel gözlem raporlari üreten
              <span className="text-white font-medium"> modern SaaS platformu</span>.
            </p>

            {/* CTA Buttons */}
            <div className={`flex items-center justify-center gap-4 transition-all duration-1000 delay-300 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
              <Link
                href="/dashboard"
                className="group flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-[#4DA3FF] to-[#00D1B2] text-white font-semibold rounded-xl hover:opacity-90 transition-all shadow-2xl shadow-[#4DA3FF]/30 hover:shadow-[#4DA3FF]/50"
              >
                <Shield className="h-5 w-5" />
                Gözlem Paneline Giris
                <ChevronRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
              </Link>
              <a
                href="#ozellikler"
                className="flex items-center gap-2 px-8 py-4 bg-white/5 border border-white/10 text-white font-medium rounded-xl hover:bg-white/10 transition-all"
              >
                <Eye className="h-5 w-5" />
                Özellikleri Incele
              </a>
            </div>

            {/* Stats */}
            <div className={`grid grid-cols-3 gap-8 mt-20 max-w-3xl mx-auto transition-all duration-1000 delay-500 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
              <div className="text-center p-6 rounded-2xl bg-white/[0.02] border border-white/5">
                <p className="text-4xl font-bold bg-gradient-to-r from-[#4DA3FF] to-[#00D1B2] bg-clip-text text-transparent">
                  Gerçek Zamanlı
                </p>
                <p className="text-sm text-gray-500 mt-1">Veri Takibi</p>
              </div>
              <div className="text-center p-6 rounded-2xl bg-white/[0.02] border border-white/5">
                <p className="text-4xl font-bold bg-gradient-to-r from-[#4DA3FF] to-[#00D1B2] bg-clip-text text-transparent">
                  Derin Analiz
                </p>
                <p className="text-sm text-gray-500 mt-1">Tweet İnceleme</p>
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
              <span className="text-sm text-purple-400">Platform Özellikleri</span>
            </div>
            <h2 className="text-4xl font-bold text-white mb-4">
              Güçlü Analiz Araçları
            </h2>
            <p className="text-gray-400 max-w-2xl mx-auto">
              Detaylı analizlerden kapsamlı raporlara, tüm ihtiyaçlarınız için
              güçlü çözümler sunuyoruz.
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
                <h3 className="text-xl font-semibold text-white mb-3">Akıllı İçerik Analizi</h3>
                <p className="text-gray-400 text-sm leading-relaxed">
                  Derin içerik analizi. Yeşil/Kırmızı/Gri Takım framework'ü
                  ile parti sadakati ve muhalefet eğilimlerini tespit.
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
                <h3 className="text-xl font-semibold text-white mb-3">Detaylı Raporlama</h3>
                <p className="text-gray-400 text-sm leading-relaxed">
                  Kullanici, parti ve coklu kullanici raporlari. Bireysel ve toplu
                  analizler ile profesyonel gözlem ciktilari.
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
                <h3 className="text-xl font-semibold text-white mb-3">Karşılaştırma Modülü</h3>
                <p className="text-gray-400 text-sm leading-relaxed">
                  2-10 kullanıcıyı yan yana karşılaştırın. Metrik kartları, grafikler ve
                  otomatik karşılaştırma özeti.
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
                <h3 className="text-xl font-semibold text-white mb-3">Gelişmiş Grafikler</h3>
                <p className="text-gray-400 text-sm leading-relaxed">
                  Parti dağılımı, takipçi sıralamaları, etkileşim analizleri.
                  İnteraktif bar ve radar chartlar ile görsel analiz.
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
                <h3 className="text-xl font-semibold text-white mb-3">Kullanıcı Yönetimi</h3>
                <p className="text-gray-400 text-sm leading-relaxed">
                  Tekli ve toplu kullanıcı ekleme. CSV import desteği, cascade delete
                  ile tam veri yönetimi.
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
                <h3 className="text-xl font-semibold text-white mb-3">Etkileşim Analizi</h3>
                <p className="text-gray-400 text-sm leading-relaxed">
                  Like, retweet, yorum ve görüntülenme metrikleri.
                  En aktif kullanıcılar ve trend analizleri.
                </p>
              </div>
            </div>

            {/* Feature 7 - Sosyal Medya ile Sohbet */}
            <div className="group relative p-8 rounded-2xl bg-gradient-to-br from-white/[0.05] to-transparent border border-white/10 hover:border-emerald-500/30 transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/0 to-emerald-500/0 group-hover:from-emerald-500/5 group-hover:to-transparent rounded-2xl transition-all" />
              <div className="relative">
                <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-emerald-500/20 to-emerald-500/5 border border-emerald-500/30 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                  <MessageCircle className="h-7 w-7 text-emerald-400" />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">Sosyal Medya ile Sohbet</h3>
                <p className="text-gray-400 text-sm leading-relaxed">
                  Türkçe NLP ile içerik arama. Doğal dil sorularıyla
                  tweet ve post'larda akıllı arama yapın.
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
                <span className="text-sm text-[#00D1B2]">Hakkımızda</span>
              </div>
              <h2 className="text-4xl font-bold text-white mb-6">
                Sosyal Medya Gözlemi İçin
                <br />
                <span className="bg-gradient-to-r from-[#4DA3FF] to-[#00D1B2] bg-clip-text text-transparent">
                  Yeni Nesil Platform
                </span>
              </h2>
              <p className="text-gray-400 mb-6 leading-relaxed">
                S.A.M (Stratejik Analiz Merkezi), sosyal medya aktivitelerini
                takip eden ve analiz eden kapsamlı
                bir stratejik analiz platformudur.
              </p>
              <p className="text-gray-400 mb-8 leading-relaxed">
                Analiz motorumuz, her kullanıcının paylaşımlarına
                <span className="text-white font-medium"> Yeşil Takım </span> (parti sadakati),
                <span className="text-white font-medium"> Kırmızı Takım </span> (muhalefet eleştirisi) ve
                <span className="text-white font-medium"> Gri Takım </span> (bağımsız gündem)
                çerçevesinde derinlemesine analiz uygular.
              </p>

              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-[#00D1B2] mt-0.5 flex-shrink-0" />
                  <p className="text-gray-300 text-sm">Gerçek zamanlı sosyal medya takibi ve veri toplama</p>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-[#00D1B2] mt-0.5 flex-shrink-0" />
                  <p className="text-gray-300 text-sm">Otomatik içerik analizi ve sınıflandırma</p>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-[#00D1B2] mt-0.5 flex-shrink-0" />
                  <p className="text-gray-300 text-sm">Profesyonel gözlem raporları ve karşılaştırma modülleri</p>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-[#00D1B2] mt-0.5 flex-shrink-0" />
                  <p className="text-gray-300 text-sm">Tam Türkçe arayüz ve yerel veri işleyici desteği</p>
                </div>
              </div>
            </div>

            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-br from-[#4DA3FF]/20 to-[#00D1B2]/20 rounded-3xl blur-3xl" />
              <div className="relative bg-[#0A0A0A] border border-white/10 rounded-3xl p-8">
                {/* Analysis Framework Visual */}
                <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                  <Activity className="h-5 w-5 text-[#4DA3FF]" />
                  Analiz Framework'ü
                </h3>

                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="w-3 h-3 rounded-full bg-emerald-500" />
                      <span className="font-semibold text-emerald-400">Yeşil Takım</span>
                    </div>
                    <p className="text-sm text-gray-400 pl-6">
                      Parti sadakati, liderlik desteği, parti etkinlikleri, başarıları öne çıkarma
                    </p>
                  </div>

                  <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="w-3 h-3 rounded-full bg-red-500" />
                      <span className="font-semibold text-red-400">Kırmızı Takım</span>
                    </div>
                    <p className="text-sm text-gray-400 pl-6">
                      Rakip parti eleştirisi, hükümet politikaları, siyasi polemik
                    </p>
                  </div>

                  <div className="p-4 rounded-xl bg-gray-500/10 border border-gray-500/20">
                    <div className="flex items-center gap-3 mb-2">
                      <div className="w-3 h-3 rounded-full bg-gray-500" />
                      <span className="font-semibold text-gray-400">Gri Takım</span>
                    </div>
                    <p className="text-sm text-gray-400 pl-6">
                      Yerel hizmetler, kişisel paylaşımlar, apolitik içerik
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
              <span className="text-sm text-cyan-400">Teknoloji Yığını</span>
            </div>
            <h2 className="text-4xl font-bold text-white mb-4">
              Modern Teknoloji Altyapısı
            </h2>
            <p className="text-gray-400 max-w-2xl mx-auto">
              En güncel ve güvenilir teknolojilerle inşa edilmiş, ölçeklenebilir ve
              yüksek performanslı bir platform.
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
              <div className="text-3xl font-bold text-[#00D1B2] mb-2">AI Engine</div>
              <p className="text-sm text-gray-500">Analiz Motoru</p>
            </div>
            <div className="p-6 rounded-2xl bg-white/[0.02] border border-white/5 text-center hover:border-white/10 transition-all">
              <div className="text-3xl font-bold text-purple-400 mb-2">PostgreSQL</div>
              <p className="text-sm text-gray-500">Veritabanı</p>
            </div>
          </div>

          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 rounded-2xl bg-gradient-to-br from-[#4DA3FF]/10 to-transparent border border-[#4DA3FF]/20">
              <Globe className="h-8 w-8 text-[#4DA3FF] mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">Tam Türkçe Destek</h3>
              <p className="text-sm text-gray-400">
                Arayüzden raporlara, tüm sistem Türkçe dil desteği ile çalışır.
              </p>
            </div>
            <div className="p-6 rounded-2xl bg-gradient-to-br from-[#00D1B2]/10 to-transparent border border-[#00D1B2]/20">
              <Lock className="h-8 w-8 text-[#00D1B2] mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">Güvenli Altyapı</h3>
              <p className="text-sm text-gray-400">
                Modern güvenlik standartları ve şifreleme protokolleri ile korunur.
              </p>
            </div>
            <div className="p-6 rounded-2xl bg-gradient-to-br from-purple-500/10 to-transparent border border-purple-500/20">
              <Zap className="h-8 w-8 text-purple-400 mb-4" />
              <h3 className="text-lg font-semibold text-white mb-2">Yüksek Performans</h3>
              <p className="text-sm text-gray-400">
                Optimize edilmiş sorgular ve önbellekleme ile hızlı cevap süreleri.
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
                Sosyal Medya Analizine Başlayın
              </h2>
              <p className="text-gray-400 mb-8 max-w-xl mx-auto">
                Sosyal medya aktivitelerini analiz etmeye hemen başlayabilirsiniz.
                Detaylı raporlar sizi bekliyor.
              </p>
              <Link
                href="/dashboard"
                className="group inline-flex items-center gap-3 px-10 py-5 bg-gradient-to-r from-[#4DA3FF] to-[#00D1B2] text-white font-semibold rounded-xl hover:opacity-90 transition-all shadow-2xl shadow-[#4DA3FF]/30 hover:shadow-[#4DA3FF]/50 text-lg"
              >
                <Shield className="h-6 w-6" />
                Panele Giriş Yap
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
                alt="S.A.M Logo"
                width={32}
                height={32}
              />
              <div className="flex items-center gap-2">
                <span className="font-bold text-white">S.A.M</span>
                <span className="text-[10px] text-[#4DA3FF] font-medium px-1.5 py-0.5 bg-[#4DA3FF]/10 rounded">v3.2</span>
              </div>
            </div>
            <p className="text-gray-500 text-sm">
              S.A.M - Stratejik Analiz Merkezi
            </p>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <div className="w-2 h-2 rounded-full bg-[#00D1B2] animate-pulse" />
              <span>Sistem Aktif</span>
            </div>
          </div>

          {/* Creator Credit */}
          <div className="pt-6 border-t border-white/5 text-center">
            <p className="text-gray-600 text-sm">
              Tasarım ve Geliştirme
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
