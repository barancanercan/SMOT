"use client";

import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  chatApi,
  ChatQueryResponse,
  ChatTweetResult,
  ChatSession,
  ChatMessage as ApiChatMessage,
  Platform,
} from "@/lib/api";
import { useToast } from "@/components/ui/toast";
import {
  Send,
  MessageCircle,
  Bot,
  User,
  Sparkles,
  Clock,
  Heart,
  Repeat2,
  Eye,
  MessageSquare,
  Trash2,
  Zap,
  TrendingUp,
  Users,
  Calendar,
  ChevronDown,
  Filter,
  Twitter,
  Instagram,
  Layers,
  Plus,
  History,
  X,
  ChevronLeft,
  Menu,
} from "lucide-react";
import ReactMarkdown from "react-markdown";

// Available parties for filter (from database)
const PARTIES = [
  { value: "", label: "Tüm Partiler" },
  { value: "CHP", label: "CHP (46)" },
  { value: "AKP", label: "AK Parti (32)" },
  { value: "MHP", label: "MHP (3)" },
  { value: "BBP", label: "BBP (2)" },
  { value: "BAGIMSIZ", label: "Bağımsız (2)" },
  { value: "YRP", label: "Yeniden Refah (1)" },
];

// Platform options
const PLATFORMS = [
  { value: "twitter" as Platform, label: "Twitter (X)", icon: Twitter, contentName: "tweet" },
  { value: "instagram" as Platform, label: "Instagram", icon: Instagram, contentName: "post" },
  { value: "both" as Platform, label: "Tümü", icon: Layers, contentName: "içerik" },
];

interface Message {
  id: string;
  type: "user" | "assistant";
  content: string;
  timestamp: Date;
  data?: ChatQueryResponse;
}

export default function ChatPage() {
  const queryClient = useQueryClient();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [selectedParty, setSelectedParty] = useState("");
  const [selectedPlatform, setSelectedPlatform] = useState<Platform>("twitter");
  const [partyDropdownOpen, setPartyDropdownOpen] = useState(false);
  const [platformDropdownOpen, setPlatformDropdownOpen] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sessionFilters, setSessionFilters] = useState<{
    platform: Platform;
    party: string;
  } | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const toast = useToast();

  // Fetch sessions
  const { data: sessionsData, refetch: refetchSessions } = useQuery({
    queryKey: ["chat-sessions"],
    queryFn: () => chatApi.listSessions(20, 0),
    staleTime: 30 * 1000, // 30 seconds
  });

  const sessions = sessionsData?.sessions || [];

  // Fetch suggestions - dynamic based on platform and party
  const { data: suggestionsData } = useQuery({
    queryKey: ["chat-suggestions", selectedPlatform, selectedParty],
    queryFn: () => chatApi.getSuggestions(selectedPlatform, selectedParty || undefined),
    staleTime: 5 * 60 * 1000,
  });

  // Dinamik öneriler - platform ve parti bazlı
  const dynamicSuggestions = useMemo(() => {
    const contentName = PLATFORMS.find(p => p.value === selectedPlatform)?.contentName || "içerik";
    const contentNamePlural = contentName === "içerik" ? "içerikler" : `${contentName}ler`;

    // Karşı parti belirleme
    const oppositeParty = selectedParty === "CHP" ? "AK Parti"
      : selectedParty === "AKP" ? "CHP"
      : selectedParty === "MHP" ? "CHP"
      : selectedParty === "BBP" ? "CHP"
      : selectedParty === "YRP" ? "CHP"
      : null;

    const baseSuggestions = [
      `Belediye hizmetleriyle ilgili ${contentNamePlural}`,
      `Son dönemde en çok etkileşim alan ${contentNamePlural}`,
      `Ekonomi hakkında atılan ${contentNamePlural}`,
      `Ulaşım konulu ${contentNamePlural}`,
    ];

    // Parti seçiliyse parti-spesifik öneriler
    if (selectedParty && oppositeParty) {
      baseSuggestions.push(
        `${oppositeParty} eleştirisi içeren ${contentNamePlural}`,
        `Hükümet politikalarını destekleyen ${contentNamePlural}`
      );
    } else {
      baseSuggestions.push(
        `Hükümet eleştirisi içeren ${contentNamePlural}`,
        `Muhalefet partilerini eleştiren ${contentNamePlural}`
      );
    }

    // Platform-spesifik öneriler
    if (selectedPlatform === "instagram") {
      baseSuggestions.push(`En çok beğeni alan fotoğraflar`);
    } else if (selectedPlatform === "twitter") {
      baseSuggestions.push(`Viral olan tweetler`);
    }

    return baseSuggestions.slice(0, 6);
  }, [selectedPlatform, selectedParty]);

  // Backend'den gelen öneriler öncelikli, yoksa frontend fallback
  const suggestions = suggestionsData?.suggestions?.length
    ? suggestionsData.suggestions
    : dynamicSuggestions;

  // Create session mutation
  const createSessionMutation = useMutation({
    mutationFn: () => chatApi.createSession({
      platform: selectedPlatform,
      party_filter: selectedParty || undefined,
    }),
    onSuccess: (session) => {
      setCurrentSessionId(session.id);
      setMessages([]);
      refetchSessions();
      toast.success("Yeni sohbet başlatıldı");
    },
    onError: (error: Error) => {
      toast.error(`Sohbet oluşturulamadı: ${error.message}`);
    },
  });

  // Delete session mutation
  const deleteSessionMutation = useMutation({
    mutationFn: (sessionId: string) => chatApi.deleteSession(sessionId),
    onSuccess: () => {
      refetchSessions();
      if (currentSessionId) {
        setCurrentSessionId(null);
        setMessages([]);
      }
      toast.success("Sohbet silindi");
    },
    onError: (error: Error) => {
      toast.error(`Sohbet silinemedi: ${error.message}`);
    },
  });

  // Load session mutation
  const loadSession = useCallback(async (sessionId: string) => {
    try {
      const session = await chatApi.getSession(sessionId);
      setCurrentSessionId(session.id);
      const loadedPlatform = session.platform as Platform || "twitter";
      const loadedParty = session.party_filter || "";
      setSelectedPlatform(loadedPlatform);
      setSelectedParty(loadedParty);
      setSessionFilters({ platform: loadedPlatform, party: loadedParty });

      // Convert API messages to local format
      const loadedMessages: Message[] = session.messages.map((msg) => ({
        id: msg.id.toString(),
        type: msg.role as "user" | "assistant",
        content: msg.content,
        timestamp: new Date(msg.created_at),
        data: msg.metadata?.response as ChatQueryResponse | undefined,
      }));

      setMessages(loadedMessages);
      setSidebarOpen(false);
    } catch (error) {
      toast.error("Sohbet yüklenemedi");
    }
  }, [toast]);

  // Save message to session
  const saveMessage = useCallback(async (
    sessionId: string,
    role: "user" | "assistant",
    content: string,
    metadata?: Record<string, unknown>
  ) => {
    try {
      await chatApi.addMessage(sessionId, { role, content, metadata });
    } catch (error) {
      console.error("Failed to save message:", error);
    }
  }, []);

  // Chat mutation
  const chatMutation = useMutation({
    mutationFn: async (params: { query: string; party: string; platform: Platform }) => {
      // Create session if not exists
      let sessionId = currentSessionId;
      if (!sessionId) {
        const session = await chatApi.createSession({
          platform: params.platform,
          party_filter: params.party || undefined,
        });
        sessionId = session.id;
        setCurrentSessionId(session.id);
        refetchSessions();
      }

      // Save user message
      await saveMessage(sessionId, "user", params.query);

      // Execute query
      const result = await chatApi.query({
        query: params.query,
        max_results: 30,
        include_summary: true,
        party_filter: params.party || undefined,
        platform: params.platform,
      });

      // Save assistant response
      await saveMessage(sessionId, "assistant", result.answer, { response: result });

      return result;
    },
    onSuccess: (data) => {
      const assistantMessage: Message = {
        id: Date.now().toString(),
        type: "assistant",
        content: data.answer,
        timestamp: new Date(),
        data,
      };
      setMessages((prev) => [...prev, assistantMessage]);
      refetchSessions();
      // İlk mesajda session filtrelerini kaydet
      if (!sessionFilters) {
        setSessionFilters({ platform: selectedPlatform, party: selectedParty });
      }
    },
    onError: (error: Error) => {
      toast.error(`Soru işlenemedi: ${error.message}`);
      const errorMessage: Message = {
        id: Date.now().toString(),
        type: "assistant",
        content: `Hata: ${error.message}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    },
  });

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Focus input
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || chatMutation.isPending) return;

    const filterInfo = [];
    if (selectedParty) filterInfo.push(getPartyLabel(selectedParty));
    if (selectedPlatform !== "both") filterInfo.push(selectedPlatform === "twitter" ? "X" : "IG");

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: inputValue.trim() + (filterInfo.length > 0 ? ` [${filterInfo.join(", ")}]` : ""),
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    chatMutation.mutate({
      query: inputValue.trim(),
      party: selectedParty,
      platform: selectedPlatform,
    });
    setInputValue("");
  };

  const handleSuggestionClick = (suggestion: string) => {
    if (chatMutation.isPending) return;

    const filterInfo = [];
    if (selectedParty) filterInfo.push(getPartyLabel(selectedParty));
    if (selectedPlatform !== "both") filterInfo.push(selectedPlatform === "twitter" ? "X" : "IG");

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: suggestion + (filterInfo.length > 0 ? ` [${filterInfo.join(", ")}]` : ""),
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    chatMutation.mutate({
      query: suggestion,
      party: selectedParty,
      platform: selectedPlatform,
    });
  };

  const handleNewChat = () => {
    setCurrentSessionId(null);
    setMessages([]);
    setSelectedParty("");
    setSelectedPlatform("twitter");
    setSessionFilters(null);
    setSidebarOpen(false);
  };

  const handleDeleteSession = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm("Bu sohbeti silmek istediğinizden emin misiniz?")) {
      deleteSessionMutation.mutate(sessionId);
    }
  };

  const handlePartySelect = useCallback((value: string) => {
    // Aktif sohbette filtre değişiyorsa otomatik yeni sohbet başlat
    if (messages.length > 0 && sessionFilters && value !== sessionFilters.party) {
      setCurrentSessionId(null);
      setMessages([]);
      setSessionFilters(null);
      toast.info("Parti filtresi değişti - yeni sohbet başlatıldı");
    }
    setSelectedParty(value);
    setPartyDropdownOpen(false);
  }, [messages.length, sessionFilters, toast]);

  const handlePlatformSelect = useCallback((value: Platform) => {
    // Aktif sohbette filtre değişiyorsa otomatik yeni sohbet başlat
    if (messages.length > 0 && sessionFilters && value !== sessionFilters.platform) {
      setCurrentSessionId(null);
      setMessages([]);
      setSessionFilters(null);
      toast.info("Platform değişti - yeni sohbet başlatıldı");
    }
    setSelectedPlatform(value);
    setPlatformDropdownOpen(false);
  }, [messages.length, sessionFilters, toast]);

  const getPartyColor = (party: string) => {
    switch (party) {
      case "AKP": return "bg-orange-500/20 border-orange-500/50 text-orange-400";
      case "CHP": return "bg-red-500/20 border-red-500/50 text-red-400";
      case "MHP": return "bg-red-700/20 border-red-700/50 text-red-300";
      case "BBP": return "bg-yellow-500/20 border-yellow-500/50 text-yellow-400";
      case "YRP": return "bg-green-500/20 border-green-500/50 text-green-400";
      case "BAGIMSIZ": return "bg-gray-500/20 border-gray-500/50 text-gray-400";
      default: return "bg-gray-500/20 border-gray-500/50 text-gray-400";
    }
  };

  const getPlatformInfo = () => {
    const platform = PLATFORMS.find(p => p.value === selectedPlatform);
    return platform || PLATFORMS[0];
  };

  const getContentName = () => {
    return getPlatformInfo().contentName;
  };

  const getPartyLabel = (value: string) => {
    const party = PARTIES.find(p => p.value === value);
    return party ? party.label.split(" (")[0] : value;
  };

  const formatSessionDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return "Bugün";
    if (days === 1) return "Dün";
    if (days < 7) return `${days} gün önce`;
    return date.toLocaleDateString("tr-TR");
  };

  return (
    <div className="min-h-screen bg-[#0B0B0B] text-white flex">
      {/* Background */}
      <div className="fixed inset-0 bg-[url('/grid.svg')] opacity-5 pointer-events-none" />
      <div className="fixed inset-0 bg-gradient-to-br from-blue-500/5 via-transparent to-emerald-500/5 pointer-events-none" />

      {/* Session Sidebar - Mobile Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Session Sidebar */}
      <aside className={`
        fixed lg:relative inset-y-0 left-0 z-50
        w-72 bg-[#0B0B0B] border-r border-white/10
        transform transition-transform duration-200 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        flex flex-col
      `}>
        {/* Sidebar Header */}
        <div className="p-4 border-b border-white/10">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 text-white hover:from-blue-500 hover:to-blue-400 transition-all"
          >
            <Plus className="h-4 w-4" />
            <span className="font-medium">Yeni Sohbet</span>
          </button>
        </div>

        {/* Session List */}
        <div className="flex-1 overflow-y-auto py-2">
          {sessions.length === 0 ? (
            <div className="px-4 py-8 text-center text-gray-500">
              <History className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Henüz sohbet yok</p>
            </div>
          ) : (
            <div className="space-y-1 px-2">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  onClick={() => loadSession(session.id)}
                  className={`
                    group flex items-start gap-3 px-3 py-2.5 rounded-lg cursor-pointer
                    transition-all hover:bg-white/5
                    ${currentSessionId === session.id ? 'bg-blue-500/10 border border-blue-500/30' : 'border border-transparent'}
                  `}
                >
                  <MessageCircle className={`h-4 w-4 mt-0.5 flex-shrink-0 ${
                    currentSessionId === session.id ? 'text-blue-400' : 'text-gray-500'
                  }`} />
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm truncate ${
                      currentSessionId === session.id ? 'text-white' : 'text-gray-300'
                    }`}>
                      {session.title}
                    </p>
                    <p className="text-xs text-gray-600 mt-0.5">
                      {formatSessionDate(session.created_at)}
                      {session.message_count > 0 && ` • ${session.message_count} mesaj`}
                    </p>
                  </div>
                  <button
                    onClick={(e) => handleDeleteSession(session.id, e)}
                    className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-500/20 text-gray-500 hover:text-red-400 transition-all"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-white/10">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Sparkles className="h-3 w-3" />
            <span>GPT-4o ile çalışır</span>
          </div>
        </div>
      </aside>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="relative border-b border-white/10 bg-[#0B0B0B]/80 backdrop-blur-xl z-30">
          <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              {/* Mobile menu button */}
              <button
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5"
              >
                <Menu className="h-5 w-5" />
              </button>

              <div className="p-2 rounded-xl bg-gradient-to-br from-blue-500/20 to-blue-600/10 border border-blue-500/30">
                <MessageCircle className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-white">
                  Sosyal Medya ile Sohbet
                </h1>
                <p className="text-xs text-gray-500 font-mono">
                  GPT-4o destekli içerik arama
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {/* Platform Filter */}
              <div className="relative">
                <button
                  onClick={() => {
                    setPlatformDropdownOpen(!platformDropdownOpen);
                    setPartyDropdownOpen(false);
                  }}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg border bg-[#1A1A1A] border-white/10 text-gray-300 hover:border-white/20 transition-all"
                >
                  {(() => {
                    const PlatformIcon = getPlatformInfo().icon;
                    return <PlatformIcon className="h-4 w-4" />;
                  })()}
                  <span className="text-sm font-medium hidden sm:inline">
                    {getPlatformInfo().label}
                  </span>
                  <ChevronDown className={`h-3 w-3 transition-transform ${platformDropdownOpen ? "rotate-180" : ""}`} />
                </button>

                {platformDropdownOpen && (
                  <>
                    <div className="fixed inset-0 z-40" onClick={() => setPlatformDropdownOpen(false)} />
                    <div className="absolute right-0 mt-2 w-40 bg-[#1A1A1A] border border-white/10 rounded-xl shadow-2xl z-50 overflow-hidden">
                      {PLATFORMS.map((platform) => {
                        const Icon = platform.icon;
                        return (
                          <button
                            key={platform.value}
                            onClick={() => handlePlatformSelect(platform.value)}
                            className={`w-full px-4 py-2.5 text-left text-sm hover:bg-white/5 transition-colors flex items-center gap-2 ${
                              selectedPlatform === platform.value ? "bg-blue-500/10 text-blue-400" : "text-gray-300"
                            }`}
                          >
                            <Icon className="h-4 w-4" />
                            {platform.label}
                            {selectedPlatform === platform.value && (
                              <span className="ml-auto text-blue-400">✓</span>
                            )}
                          </button>
                        );
                      })}
                    </div>
                  </>
                )}
              </div>

              {/* Party Filter */}
              <div className="relative">
                <button
                  onClick={() => {
                    setPartyDropdownOpen(!partyDropdownOpen);
                    setPlatformDropdownOpen(false);
                  }}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-all ${
                    selectedParty
                      ? getPartyColor(selectedParty)
                      : "bg-[#1A1A1A] border-white/10 text-gray-400 hover:border-white/20"
                  }`}
                >
                  <Filter className="h-4 w-4" />
                  <span className="text-sm font-medium hidden sm:inline">
                    {selectedParty ? getPartyLabel(selectedParty) : "Parti"}
                  </span>
                  <ChevronDown className={`h-3 w-3 transition-transform ${partyDropdownOpen ? "rotate-180" : ""}`} />
                </button>

                {partyDropdownOpen && (
                  <>
                    <div className="fixed inset-0 z-40" onClick={() => setPartyDropdownOpen(false)} />
                    <div className="absolute right-0 mt-2 w-48 bg-[#1A1A1A] border border-white/10 rounded-xl shadow-2xl z-50 overflow-hidden">
                      {PARTIES.map((party) => (
                        <button
                          key={party.value}
                          onClick={() => handlePartySelect(party.value)}
                          className={`w-full px-4 py-2.5 text-left text-sm hover:bg-white/5 transition-colors flex items-center justify-between ${
                            selectedParty === party.value ? "bg-blue-500/10 text-blue-400" : "text-gray-300"
                          }`}
                        >
                          {party.label}
                          {selectedParty === party.value && (
                            <span className="text-blue-400">✓</span>
                          )}
                        </button>
                      ))}
                    </div>
                  </>
                )}
              </div>

              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30">
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-xs font-medium text-emerald-400 font-mono hidden sm:inline">
                  GPT-4o
                </span>
              </div>
            </div>
          </div>
        </header>

        {/* Messages Area */}
        <main className="relative flex-1 overflow-hidden">
          <div className="h-full overflow-y-auto px-4 py-6">
            <div className="max-w-4xl mx-auto space-y-6">
              {/* Welcome message */}
              {messages.length === 0 && (
                <div className="text-center py-12">
                  <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-blue-500/20 via-blue-600/10 to-emerald-500/10 flex items-center justify-center border border-white/10 mb-6">
                    <Bot className="w-10 h-10 text-blue-400" />
                  </div>
                  <h2 className="text-xl font-semibold text-white mb-2">
                    Merhaba! Size nasıl yardımcı olabilirim?
                  </h2>
                  <p className="text-gray-500 text-sm mb-2">
                    Türkçe sorular sorarak {getContentName()}leri arayabilirsiniz
                  </p>
                  {sessions.length > 0 && (
                    <p className="text-gray-600 text-xs mb-4">
                      {sessions.length} kayıtlı sohbet • Sol panelden geçmiş sohbetlerinize ulaşabilirsiniz
                    </p>
                  )}
                  {sessions.length === 0 && <div className="mb-4" />}

                  {/* Active filters hint */}
                  {(selectedParty || selectedPlatform !== "both") && (
                    <div className="flex items-center justify-center gap-2 mb-6 p-3 rounded-xl bg-white/5 border border-white/10">
                      <span className="text-xs text-gray-500">Aktif Filtreler:</span>
                      {selectedPlatform !== "both" && (
                        <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/30">
                          {selectedPlatform === "twitter" ? (
                            <Twitter className="h-3 w-3 text-blue-400" />
                          ) : (
                            <Instagram className="h-3 w-3 text-pink-400" />
                          )}
                          <span className="text-xs text-blue-400">
                            {selectedPlatform === "twitter" ? "Twitter" : "Instagram"}
                          </span>
                        </div>
                      )}
                      {selectedParty && (
                        <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full ${getPartyColor(selectedParty)}`}>
                          <Filter className="h-3 w-3" />
                          <span className="text-xs">{getPartyLabel(selectedParty)}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Suggestions */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-w-2xl mx-auto">
                    {suggestions.map((suggestion, index) => (
                      <button
                        key={index}
                        onClick={() => handleSuggestionClick(suggestion)}
                        disabled={chatMutation.isPending}
                        className="px-4 py-3 rounded-xl bg-[#1A1A1A] border border-white/10 text-sm text-gray-300 hover:border-blue-500/50 hover:bg-blue-500/5 hover:text-blue-400 transition-all disabled:opacity-50 text-left"
                      >
                        <span className="text-blue-400 mr-2">→</span>
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Message list */}
              {messages.map((message) => (
                <div key={message.id}>
                  {message.type === "user" ? (
                    <UserMessage content={message.content} />
                  ) : (
                    <AssistantMessage
                      content={message.content}
                      data={message.data}
                    />
                  )}
                </div>
              ))}

              {/* Loading */}
              {chatMutation.isPending && (
                <div className="flex justify-start">
                  <div className="flex items-start gap-3 max-w-[80%]">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500/20 to-blue-600/10 border border-blue-500/30 flex items-center justify-center flex-shrink-0">
                      <Bot className="h-4 w-4 text-blue-400" />
                    </div>
                    <div className="bg-[#1A1A1A] rounded-2xl rounded-tl-sm px-4 py-3 border border-white/10">
                      <div className="flex items-center gap-2">
                        <div className="flex gap-1">
                          <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                          <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                          <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                        </div>
                        <span className="text-sm text-gray-500">GPT-4o ile analiz ediliyor...</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </div>
        </main>

        {/* Input Area */}
        <footer className="relative border-t border-white/10 bg-[#0B0B0B]/80 backdrop-blur-xl">
          <div className="max-w-4xl mx-auto px-4 py-4">
            <form onSubmit={handleSubmit} className="flex gap-3">
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder={
                  selectedParty
                    ? `${getPartyLabel(selectedParty)} ${getContentName()}leri hakkında soru sorun...`
                    : `${getContentName().charAt(0).toUpperCase() + getContentName().slice(1)}ler hakkında soru sorun...`
                }
                disabled={chatMutation.isPending}
                className="flex-1 px-4 py-3 bg-[#1A1A1A] border border-white/10 rounded-xl text-white placeholder:text-gray-600 focus:border-blue-500/50 focus:ring-2 focus:ring-blue-500/20 transition-all disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={!inputValue.trim() || chatMutation.isPending}
                className="px-4 py-3 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-xl hover:from-blue-500 hover:to-blue-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-blue-500/25"
              >
                <Send className="h-5 w-5" />
              </button>
            </form>

            <div className="flex items-center justify-center gap-4 mt-3 text-xs text-gray-600">
              <div className="flex items-center gap-1">
                <Sparkles className="h-3 w-3" />
                <span>GPT-4o ile analiz</span>
              </div>
              <div className="flex items-center gap-1">
                <Zap className="h-3 w-3" />
                <span>Türkçe dil desteği</span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}

// User message
function UserMessage({ content }: { content: string }) {
  return (
    <div className="flex justify-end">
      <div className="flex items-start gap-3 max-w-[80%]">
        <div className="bg-gradient-to-r from-blue-600 to-blue-500 rounded-2xl rounded-tr-sm px-4 py-3 text-white">
          <p>{content}</p>
        </div>
        <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center flex-shrink-0">
          <User className="h-4 w-4 text-gray-300" />
        </div>
      </div>
    </div>
  );
}

// Assistant message with markdown support
function AssistantMessage({
  content,
  data,
}: {
  content: string;
  data?: ChatQueryResponse;
}) {
  const [showAllTweets, setShowAllTweets] = useState(false);

  const tweets = data?.tweets || [];
  const summary = data?.summary;
  const displayTweets = showAllTweets ? tweets : tweets.slice(0, 3);

  return (
    <div className="flex justify-start">
      <div className="flex items-start gap-3 max-w-[90%] w-full">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500/20 to-blue-600/10 border border-blue-500/30 flex items-center justify-center flex-shrink-0">
          <Bot className="h-4 w-4 text-blue-400" />
        </div>

        <div className="flex-1 space-y-3">
          {/* Main answer with markdown */}
          <div className="bg-[#1A1A1A] rounded-2xl rounded-tl-sm px-4 py-3 border border-white/10">
            <div className="prose prose-invert prose-sm max-w-none prose-headings:text-white prose-headings:font-semibold prose-h2:text-base prose-h2:mt-4 prose-h2:mb-2 prose-h3:text-sm prose-h3:mt-3 prose-h3:mb-1 prose-p:text-gray-300 prose-p:my-1 prose-li:text-gray-300 prose-li:my-0.5 prose-strong:text-white prose-blockquote:border-l-blue-500 prose-blockquote:text-gray-400 prose-blockquote:italic prose-em:text-gray-400">
              <ReactMarkdown>{content}</ReactMarkdown>
            </div>

            {data?.execution_time_ms && (
              <div className="flex items-center gap-1 mt-3 pt-2 border-t border-white/5 text-xs text-gray-600">
                <Clock className="h-3 w-3" />
                <span>{(data.execution_time_ms / 1000).toFixed(1)}s</span>
                {data.confidence_score > 0 && (
                  <>
                    <span className="mx-1">|</span>
                    <span>Güven: {(data.confidence_score * 100).toFixed(0)}%</span>
                  </>
                )}
              </div>
            )}
          </div>

          {/* Summary card */}
          {summary && summary.total_found > 0 && (
            <div className="bg-[#1A1A1A]/50 rounded-xl px-4 py-3 border border-white/5">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-blue-400" />
                  <div>
                    <div className="text-gray-500 text-xs">Bulunan</div>
                    <div className="text-white font-medium">{summary.total_found}</div>
                  </div>
                </div>

                {summary.sentiment && (
                  <div className="flex items-center gap-2">
                    <Heart className={`h-4 w-4 ${
                      summary.sentiment === "olumlu" ? "text-emerald-400" :
                      summary.sentiment === "olumsuz" ? "text-red-400" : "text-gray-400"
                    }`} />
                    <div>
                      <div className="text-gray-500 text-xs">Duygu</div>
                      <div className="text-white font-medium capitalize">{summary.sentiment}</div>
                    </div>
                  </div>
                )}

                {summary.most_active_users?.length > 0 && (
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-purple-400" />
                    <div>
                      <div className="text-gray-500 text-xs">Aktif</div>
                      <div className="text-white font-medium">{summary.most_active_users[0]}</div>
                    </div>
                  </div>
                )}

                {summary.date_range && (
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-amber-400" />
                    <div>
                      <div className="text-gray-500 text-xs">Tarih</div>
                      <div className="text-white font-medium text-xs">{summary.date_range}</div>
                    </div>
                  </div>
                )}
              </div>

              {summary.top_topics?.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {summary.top_topics.map((topic, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 rounded-full bg-blue-500/10 border border-blue-500/30 text-xs text-blue-400"
                    >
                      {topic}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Tweet results */}
          {tweets.length > 0 && (
            <div className="space-y-2">
              {displayTweets.map((tweet) => (
                <TweetCard key={tweet.id} tweet={tweet} />
              ))}

              {tweets.length > 3 && (
                <button
                  onClick={() => setShowAllTweets(!showAllTweets)}
                  className="w-full py-2 text-sm text-blue-400 hover:text-blue-300 transition-colors"
                >
                  {showAllTweets
                    ? "Daha az göster"
                    : `+${tweets.length - 3} daha göster`}
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Tweet card
function TweetCard({ tweet }: { tweet: ChatTweetResult }) {
  const [expanded, setExpanded] = useState(false);
  const isLongTweet = tweet.tweet_text.length > 280;

  return (
    <div className="bg-[#1A1A1A]/70 rounded-xl px-4 py-3 border border-white/5 hover:border-white/10 transition-all">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gray-700 to-gray-800 flex items-center justify-center flex-shrink-0">
          <span className="text-sm font-bold text-gray-300">
            {tweet.name?.[0] || tweet.username[0].toUpperCase()}
          </span>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-white">
              {tweet.name || tweet.username}
            </span>
            <span className="text-gray-500 text-sm">@{tweet.username}</span>
            {tweet.party && (
              <span className="px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-xs text-blue-400">
                {tweet.party}
              </span>
            )}
            {tweet.criticism_topic && (
              <span className="px-2 py-0.5 rounded-full bg-red-500/10 border border-red-500/30 text-xs text-red-400">
                {tweet.criticism_topic}
              </span>
            )}
          </div>

          <p className="text-gray-300 mt-2 text-sm leading-relaxed whitespace-pre-wrap">
            {expanded || !isLongTweet
              ? tweet.tweet_text
              : tweet.tweet_text.substring(0, 280) + "..."}
          </p>

          {isLongTweet && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-blue-400 text-xs mt-1 hover:text-blue-300"
            >
              {expanded ? "Daha az göster" : "Devamını göster"}
            </button>
          )}

          {tweet.criticism_explanation && (
            <div className="mt-2 px-3 py-2 bg-red-500/5 border-l-2 border-red-500/30 rounded-r">
              <p className="text-xs text-red-300/80 italic">
                {tweet.criticism_explanation}
              </p>
            </div>
          )}

          <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
            {tweet.tweet_date && (
              <span>{tweet.tweet_date.substring(0, 10)}</span>
            )}
            <div className="flex items-center gap-1">
              <Heart className="h-3 w-3" />
              <span>{tweet.likes.toLocaleString()}</span>
            </div>
            <div className="flex items-center gap-1">
              <Repeat2 className="h-3 w-3" />
              <span>{tweet.retweets.toLocaleString()}</span>
            </div>
            {tweet.replies > 0 && (
              <div className="flex items-center gap-1">
                <MessageSquare className="h-3 w-3" />
                <span>{tweet.replies.toLocaleString()}</span>
              </div>
            )}
            {tweet.views > 0 && (
              <div className="flex items-center gap-1">
                <Eye className="h-3 w-3" />
                <span>{(tweet.views / 1000).toFixed(1)}K</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
