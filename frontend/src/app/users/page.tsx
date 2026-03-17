"use client";

import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  api,
  User,
  PaginatedResponse,
  CreateUserRequest,
  CreateUserResponse,
  BulkCreateResponse,
  DeleteUserResponse,
} from "@/lib/api";
import { useToast } from "@/components/ui/toast";
import {
  Users,
  UserPlus,
  Upload,
  Trash2,
  Search,
  RefreshCw,
  AlertCircle,
  X,
  Check,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

// All parties for dropdown
const ALL_PARTIES = [
  "AK Parti",
  "CHP",
  "MHP",
  "DEM Parti",
  "BBP",
  "Memleket Partisi",
  "Saadet Partisi",
  "TIP",
  "Yeniden Refah Partisi",
  "Zafer Partisi",
  "IYI Parti",
  "Bagimsiz",
];

export default function UsersPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [partyFilter, setPartyFilter] = useState("");
  const [page, setPage] = useState(1);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isBulkModalOpen, setIsBulkModalOpen] = useState(false);
  const [deleteUsername, setDeleteUsername] = useState<string | null>(null);

  const toast = useToast();
  const queryClient = useQueryClient();

  // Fetch users
  const {
    data: usersData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["users", page, searchTerm, partyFilter],
    queryFn: () => {
      const params = new URLSearchParams();
      params.set("page", page.toString());
      params.set("page_size", "20");
      if (searchTerm) params.set("search", searchTerm);
      if (partyFilter) params.set("party", partyFilter);
      return api.get<PaginatedResponse<User>>(`/users/?${params.toString()}`);
    },
    staleTime: 30 * 1000,
  });

  const users = usersData?.items || [];
  const totalPages = usersData?.total_pages || 1;

  // Create user mutation
  const createUserMutation = useMutation({
    mutationFn: (data: CreateUserRequest) =>
      api.post<CreateUserResponse>("/users/", data),
    onSuccess: () => {
      toast.success("Kullanici basariyla eklendi");
      setIsAddModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (error: Error) => {
      toast.error(`Kullanici eklenemedi: ${error.message}`);
    },
  });

  // Bulk create mutation
  const bulkCreateMutation = useMutation({
    mutationFn: (data: { users: CreateUserRequest[] }) =>
      api.post<BulkCreateResponse>("/users/bulk", data),
    onSuccess: (data) => {
      toast.success(
        `${data.created} kullanici eklendi, ${data.skipped} atlanidi`
      );
      setIsBulkModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (error: Error) => {
      toast.error(`Toplu ekleme basarisiz: ${error.message}`);
    },
  });

  // Delete user mutation
  const deleteUserMutation = useMutation({
    mutationFn: (username: string) =>
      api.delete<DeleteUserResponse>(`/users/${username}`),
    onSuccess: (data) => {
      toast.success(`@${data.deleted} basariyla silindi`);
      setDeleteUsername(null);
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (error: Error) => {
      toast.error(`Silme basarisiz: ${error.message}`);
    },
  });

  // Handle search with debounce
  const handleSearch = (value: string) => {
    setSearchTerm(value);
    setPage(1);
  };

  if (error) {
    return (
      <div className="min-h-screen bg-[#0B0B0B] text-white p-8">
        <div className="max-w-6xl mx-auto">
          <div className="bg-[#1A1A1A]/80 rounded-2xl border border-red-500/30 p-12 text-center">
            <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-white mb-2">Sistem Hatasi</h2>
            <p className="text-gray-400 mb-4">Kullanicilar yuklenemedi</p>
            <button
              onClick={() => refetch()}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl"
            >
              <RefreshCw className="inline-block h-4 w-4 mr-2" />
              Yeniden Dene
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B0B0B] text-white">
      <div className="fixed inset-0 bg-[url('/grid.svg')] opacity-5 pointer-events-none" />

      <div className="relative max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="relative mb-8 p-8 rounded-2xl bg-gradient-to-br from-[#1A1A1A] via-[#151515] to-[#0F0F0F] border border-white/10 overflow-hidden shadow-2xl">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2.5 rounded-xl bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 border border-emerald-500/30">
                  <Users className="h-6 w-6 text-emerald-400" />
                </div>
                <span className="text-xs font-mono text-emerald-400 tracking-wider uppercase">
                  Kullanici Yonetimi
                </span>
              </div>
              <h1 className="text-3xl font-bold text-white mb-2">
                Kullanici Yonetimi
              </h1>
              <p className="text-gray-500 text-sm font-mono">
                Meclis uyelerini ekleyin, duzenleyin veya silin
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setIsAddModalOpen(true)}
                className="flex items-center gap-2 px-5 py-3 bg-gradient-to-r from-emerald-600 to-emerald-500 text-white rounded-xl hover:from-emerald-500 hover:to-emerald-400 transition-all font-medium shadow-lg shadow-emerald-500/25"
              >
                <UserPlus className="h-5 w-5" />
                <span>Kullanici Ekle</span>
              </button>
              <button
                onClick={() => setIsBulkModalOpen(true)}
                className="flex items-center gap-2 px-5 py-3 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-xl hover:from-blue-500 hover:to-blue-400 transition-all font-medium shadow-lg shadow-blue-500/25"
              >
                <Upload className="h-5 w-5" />
                <span>Toplu Ekle</span>
              </button>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-[#1A1A1A]/80 backdrop-blur-xl rounded-xl border border-white/10 p-4 mb-6">
          <div className="flex gap-4 flex-wrap">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-500" />
                <input
                  type="text"
                  placeholder="Kullanici ara..."
                  value={searchTerm}
                  onChange={(e) => handleSearch(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-[#0B0B0B] border border-white/10 rounded-lg text-white placeholder-gray-500 focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20"
                />
              </div>
            </div>
            <div className="w-48">
              <select
                value={partyFilter}
                onChange={(e) => {
                  setPartyFilter(e.target.value);
                  setPage(1);
                }}
                className="w-full px-4 py-2.5 bg-[#0B0B0B] border border-white/10 rounded-lg text-white focus:border-blue-500/50"
              >
                <option value="">Tum Partiler</option>
                {ALL_PARTIES.map((party) => (
                  <option key={party} value={party}>
                    {party}
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={() => refetch()}
              className="px-4 py-2.5 bg-[#0B0B0B] border border-white/10 rounded-lg text-gray-400 hover:text-white hover:border-white/20 transition-all"
            >
              <RefreshCw className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Users Table */}
        <div className="bg-[#1A1A1A]/80 backdrop-blur-xl rounded-xl border border-white/10 overflow-hidden">
          {isLoading ? (
            <div className="p-12 text-center">
              <div className="w-12 h-12 mx-auto mb-4 rounded-full border-2 border-blue-500 border-t-transparent animate-spin" />
              <p className="text-gray-500 font-mono">Yukleniyor...</p>
            </div>
          ) : users.length === 0 ? (
            <div className="p-12 text-center">
              <Users className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400">Kullanici bulunamadi</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-white/10 bg-[#0B0B0B]/50">
                    <th className="text-left py-4 px-6 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                      Kullanici
                    </th>
                    <th className="text-left py-4 px-6 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                      Ad Soyad
                    </th>
                    <th className="text-left py-4 px-6 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                      Parti
                    </th>
                    <th className="text-left py-4 px-6 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                      Ilce
                    </th>
                    <th className="text-left py-4 px-6 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                      Tweet
                    </th>
                    <th className="text-right py-4 px-6 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                      Islem
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr
                      key={user.id}
                      className="border-b border-white/5 hover:bg-white/5 transition-colors"
                    >
                      <td className="py-4 px-6">
                        <span className="text-blue-400 font-mono">
                          @{user.username}
                        </span>
                      </td>
                      <td className="py-4 px-6">
                        <span className="text-white font-medium">
                          {user.name}
                        </span>
                      </td>
                      <td className="py-4 px-6">
                        <span className="px-2.5 py-1 bg-emerald-500/20 text-emerald-400 rounded-full text-sm font-medium border border-emerald-500/30">
                          {user.party}
                        </span>
                      </td>
                      <td className="py-4 px-6">
                        <span className="text-gray-400">
                          {user.district || "-"}
                        </span>
                      </td>
                      <td className="py-4 px-6">
                        <span className="text-gray-300 font-mono">
                          {user.tweet_count?.toLocaleString() || 0}
                        </span>
                      </td>
                      <td className="py-4 px-6 text-right">
                        <button
                          onClick={() => setDeleteUsername(user.username)}
                          className="p-2 text-red-400 hover:bg-red-500/20 rounded-lg transition-colors"
                          title="Kullaniciyi Sil"
                        >
                          <Trash2 className="h-5 w-5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-6 py-4 border-t border-white/10">
              <p className="text-sm text-gray-500">
                Sayfa {page} / {totalPages} (Toplam:{" "}
                {usersData?.total || 0} kullanici)
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 bg-[#0B0B0B] border border-white/10 rounded-lg text-white disabled:opacity-50 disabled:cursor-not-allowed hover:border-white/20 transition-all"
                >
                  <ChevronLeft className="h-5 w-5" />
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-4 py-2 bg-[#0B0B0B] border border-white/10 rounded-lg text-white disabled:opacity-50 disabled:cursor-not-allowed hover:border-white/20 transition-all"
                >
                  <ChevronRight className="h-5 w-5" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Add User Modal */}
      {isAddModalOpen && (
        <AddUserModal
          onClose={() => setIsAddModalOpen(false)}
          onSubmit={(data) => createUserMutation.mutate(data)}
          isLoading={createUserMutation.isPending}
        />
      )}

      {/* Bulk Add Modal */}
      {isBulkModalOpen && (
        <BulkAddModal
          onClose={() => setIsBulkModalOpen(false)}
          onSubmit={(users) => bulkCreateMutation.mutate({ users })}
          isLoading={bulkCreateMutation.isPending}
        />
      )}

      {/* Delete Confirmation Modal */}
      {deleteUsername && (
        <DeleteConfirmModal
          username={deleteUsername}
          onClose={() => setDeleteUsername(null)}
          onConfirm={() => deleteUserMutation.mutate(deleteUsername)}
          isLoading={deleteUserMutation.isPending}
        />
      )}
    </div>
  );
}

// Add User Modal Component
function AddUserModal({
  onClose,
  onSubmit,
  isLoading,
}: {
  onClose: () => void;
  onSubmit: (data: CreateUserRequest) => void;
  isLoading: boolean;
}) {
  const [formData, setFormData] = useState<CreateUserRequest>({
    username: "",
    name: "",
    party: "",
    district: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.username || !formData.name || !formData.party) return;
    onSubmit(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-[#1A1A1A] border border-white/10 rounded-2xl p-6 w-full max-w-md shadow-2xl">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-white">Kullanici Ekle</h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Kullanici Adi *
            </label>
            <input
              type="text"
              value={formData.username}
              onChange={(e) =>
                setFormData({ ...formData, username: e.target.value })
              }
              placeholder="ornek: ahmetyilmaz"
              className="w-full px-4 py-3 bg-[#0B0B0B] border border-white/10 rounded-xl text-white focus:border-blue-500/50"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Ad Soyad *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
              placeholder="ornek: Ahmet Yilmaz"
              className="w-full px-4 py-3 bg-[#0B0B0B] border border-white/10 rounded-xl text-white focus:border-blue-500/50"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Parti *
            </label>
            <select
              value={formData.party}
              onChange={(e) =>
                setFormData({ ...formData, party: e.target.value })
              }
              className="w-full px-4 py-3 bg-[#0B0B0B] border border-white/10 rounded-xl text-white focus:border-blue-500/50"
              required
            >
              <option value="">Parti Secin</option>
              {ALL_PARTIES.map((party) => (
                <option key={party} value={party}>
                  {party}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              Ilce (Opsiyonel)
            </label>
            <input
              type="text"
              value={formData.district || ""}
              onChange={(e) =>
                setFormData({ ...formData, district: e.target.value })
              }
              placeholder="ornek: Kadikoy"
              className="w-full px-4 py-3 bg-[#0B0B0B] border border-white/10 rounded-xl text-white focus:border-blue-500/50"
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-3 bg-[#0B0B0B] border border-white/10 text-gray-400 rounded-xl hover:bg-white/5"
            >
              Iptal
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 px-4 py-3 bg-gradient-to-r from-emerald-600 to-emerald-500 text-white rounded-xl hover:from-emerald-500 hover:to-emerald-400 disabled:opacity-50"
            >
              {isLoading ? "Ekleniyor..." : "Ekle"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Bulk Add Modal Component
function BulkAddModal({
  onClose,
  onSubmit,
  isLoading,
}: {
  onClose: () => void;
  onSubmit: (users: CreateUserRequest[]) => void;
  isLoading: boolean;
}) {
  const [csvText, setCsvText] = useState("");
  const [parseError, setParseError] = useState<string | null>(null);
  const [parsedUsers, setParsedUsers] = useState<CreateUserRequest[]>([]);

  const parseCSV = (text: string) => {
    setParseError(null);
    const lines = text.trim().split("\n").filter(Boolean);
    const users: CreateUserRequest[] = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;

      const parts = line.split(",").map((p) => p.trim());
      if (parts.length < 3) {
        setParseError(`Satir ${i + 1}: En az 3 alan gerekli (username, ad, parti)`);
        return;
      }

      users.push({
        username: parts[0],
        name: parts[1],
        party: parts[2],
        district: parts[3] || undefined,
      });
    }

    setParsedUsers(users);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (parsedUsers.length === 0) return;
    onSubmit(parsedUsers);
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-[#1A1A1A] border border-white/10 rounded-2xl p-6 w-full max-w-2xl shadow-2xl">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-white">Toplu Kullanici Ekle</h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">
              CSV Formati
            </label>
            <p className="text-xs text-gray-500 mb-3 font-mono">
              username,Ad Soyad,Parti,Ilce (her satir bir kullanici)
            </p>
            <textarea
              value={csvText}
              onChange={(e) => {
                setCsvText(e.target.value);
                parseCSV(e.target.value);
              }}
              placeholder={`ahmetyilmaz,Ahmet Yilmaz,CHP,Kadikoy\nmehmetdemir,Mehmet Demir,AK Parti,Uskudar`}
              rows={8}
              className="w-full px-4 py-3 bg-[#0B0B0B] border border-white/10 rounded-xl text-white font-mono text-sm focus:border-blue-500/50 resize-none"
            />
          </div>

          {parseError && (
            <div className="p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 text-sm">
              {parseError}
            </div>
          )}

          {parsedUsers.length > 0 && !parseError && (
            <div className="p-3 bg-emerald-500/20 border border-emerald-500/30 rounded-lg text-emerald-400 text-sm">
              <Check className="inline-block h-4 w-4 mr-2" />
              {parsedUsers.length} kullanici parse edildi
            </div>
          )}

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-3 bg-[#0B0B0B] border border-white/10 text-gray-400 rounded-xl hover:bg-white/5"
            >
              Iptal
            </button>
            <button
              type="submit"
              disabled={isLoading || parsedUsers.length === 0 || !!parseError}
              className="flex-1 px-4 py-3 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-xl hover:from-blue-500 hover:to-blue-400 disabled:opacity-50"
            >
              {isLoading ? "Ekleniyor..." : `${parsedUsers.length} Kullanici Ekle`}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Delete Confirmation Modal
function DeleteConfirmModal({
  username,
  onClose,
  onConfirm,
  isLoading,
}: {
  username: string;
  onClose: () => void;
  onConfirm: () => void;
  isLoading: boolean;
}) {
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-[#1A1A1A] border border-white/10 rounded-2xl p-6 w-full max-w-md shadow-2xl">
        <div className="text-center">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-500/20 border border-red-500/30 flex items-center justify-center">
            <Trash2 className="h-8 w-8 text-red-400" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">
            Kullaniciyi Sil
          </h2>
          <p className="text-gray-400 mb-6">
            <span className="text-blue-400 font-mono">@{username}</span> ve tum
            iliskili verileri (tweetler, profil gecmisi, raporlar) silinecek. Bu
            islem geri alinamaz.
          </p>

          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-3 bg-[#0B0B0B] border border-white/10 text-gray-400 rounded-xl hover:bg-white/5"
            >
              Iptal
            </button>
            <button
              onClick={onConfirm}
              disabled={isLoading}
              className="flex-1 px-4 py-3 bg-gradient-to-r from-red-600 to-red-500 text-white rounded-xl hover:from-red-500 hover:to-red-400 disabled:opacity-50"
            >
              {isLoading ? "Siliniyor..." : "Sil"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
