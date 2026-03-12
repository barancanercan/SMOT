export interface User {
  id: number;
  username: string;
  name: string;
  party: string;
  district: string;
}

export interface DashboardStats {
  total_tweets: number;
  total_original: number;
  total_retweets: number;
  total_councilors: number;
  active_users: number;
  total_likes: number;
  total_views: number;
  total_replies: number;
}

export interface Tweet {
  id: number;
  text: string;
  date: string;
  likes: number;
  replies: number;
  retweets: number;
  views: number;
  engagement: number;
}

export interface FollowerData {
  username: string;
  name: string;
  party: string;
  district: string;
  followers_count: number;
  following_count: number;
}

export interface PartyStats {
  party: string;
  member_count: number;
  total_followers: number;
}

export interface EngagementData {
  username: string;
  name: string;
  party: string;
  tweet_count: number;
  total_likes: number;
  total_retweets: number;
  total_replies: number;
  total_views: number;
  total_engagement: number;
}

export interface Report {
  username: string;
  report: string;
  cached: boolean;
  created_at?: string;
}
