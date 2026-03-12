"use client";

import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { api, User, Tweet, PaginatedResponse } from "@/lib/api";
import {
  Flame,
  ThumbsUp,
  MessageCircle,
  Repeat2,
  Eye,
  AlertCircle,
} from "lucide-react";

interface TopTweetsResponse {
  username: string;
  tweets: (Tweet & { engagement: number })[];
}

export default function TweetsPage() {
  const [selectedUser, setSelectedUser] = useState<string>("");

  // Fetch users
  const {
    data: usersData,
    isLoading: usersLoading,
    error: usersError,
  } = useQuery({
    queryKey: ["users"],
    queryFn: () => api.get<PaginatedResponse<User>>("/users/"),
    staleTime: 5 * 60 * 1000,
  });

  const users = usersData?.items || [];

  // Set default user when users load
  useMemo(() => {
    if (users.length > 0 && !selectedUser) {
      setSelectedUser(users[0].username);
    }
  }, [users, selectedUser]);

  // Fetch top tweets for selected user
  const {
    data: tweetsData,
    isLoading: tweetsLoading,
    error: tweetsError,
  } = useQuery({
    queryKey: ["top-tweets", selectedUser],
    queryFn: () =>
      api.get<TopTweetsResponse>(`/tweets/${selectedUser}/top?limit=20`),
    enabled: !!selectedUser,
    staleTime: 2 * 60 * 1000,
  });

  const tweets = tweetsData?.tweets || [];

  const formatNumber = (num: number) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + "M";
    if (num >= 1000) return (num / 1000).toFixed(1) + "K";
    return num.toString();
  };

  if (usersError) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          Kullanicilar yuklenemedi
        </h2>
        <p className="text-gray-500">
          API baglantisini kontrol edin ve sayfayi yenileyin.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Flame className="h-6 w-6 text-orange-500" />
            Top Tweets
          </h1>
          <p className="text-gray-500">En cok etkilesim alan tweetler</p>
        </div>

        <select
          value={selectedUser}
          onChange={(e) => setSelectedUser(e.target.value)}
          disabled={usersLoading}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50"
        >
          {usersLoading ? (
            <option>Yukleniyor...</option>
          ) : (
            users.map((user) => (
              <option key={user.username} value={user.username}>
                @{user.username}
              </option>
            ))
          )}
        </select>
      </div>

      {tweetsError && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2">
          <AlertCircle className="h-5 w-5" />
          Tweetler yuklenemedi
        </div>
      )}

      {tweetsLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      ) : tweets.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <Flame className="h-12 w-12 mx-auto mb-3 text-gray-300" />
          <p>Tweet bulunamadi</p>
        </div>
      ) : (
        <div className="space-y-4">
          {tweets.map((tweet, index) => (
            <div
              key={tweet.id || index}
              className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-lg font-bold text-gray-400">
                    #{index + 1}
                  </span>
                  <span className="font-medium text-blue-600">
                    @{tweet.username}
                  </span>
                </div>
                <span className="text-sm text-gray-500">{tweet.tweet_date}</span>
              </div>

              <p className="text-gray-800 mb-4 whitespace-pre-wrap leading-relaxed">
                {tweet.tweet_text}
              </p>

              <div className="flex items-center gap-6 text-sm text-gray-500">
                <div className="flex items-center gap-1" title="Begeniler">
                  <ThumbsUp className="h-4 w-4" />
                  {formatNumber(tweet.likes)}
                </div>
                <div className="flex items-center gap-1" title="Yorumlar">
                  <MessageCircle className="h-4 w-4" />
                  {formatNumber(tweet.replies)}
                </div>
                <div className="flex items-center gap-1" title="Retweetler">
                  <Repeat2 className="h-4 w-4" />
                  {formatNumber(tweet.retweets)}
                </div>
                <div className="flex items-center gap-1" title="Goruntulemeler">
                  <Eye className="h-4 w-4" />
                  {formatNumber(tweet.views)}
                </div>
                <div className="ml-auto font-medium text-orange-600">
                  Engagement: {formatNumber(tweet.engagement)}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
