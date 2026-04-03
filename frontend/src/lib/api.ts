const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_PREFIX = "/api/v1";

/**
 * API Error class with status code and details
 */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly details?: Record<string, unknown>
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Type-safe API client for backend communication
 */
class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL + API_PREFIX;
  }

  /**
   * Get authentication headers if token exists
   */
  private getAuthHeaders(): Record<string, string> {
    if (typeof window === "undefined") return {};

    const token = localStorage.getItem("auth_token");
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  /**
   * Handle API response with proper error handling
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let errorMessage = `HTTP Error ${response.status}`;
      let details: Record<string, unknown> | undefined;

      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
        details = errorData;
      } catch {
        // JSON parse failed, use default message
      }

      throw new ApiError(response.status, errorMessage, details);
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  /**
   * GET request
   */
  async get<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        ...this.getAuthHeaders(),
      },
      ...options,
    });

    return this.handleResponse<T>(response);
  }

  /**
   * POST request
   */
  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...this.getAuthHeaders(),
      },
      body: data ? JSON.stringify(data) : undefined,
    });

    return this.handleResponse<T>(response);
  }

  /**
   * PUT request
   */
  async put<T>(endpoint: string, data: unknown): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        ...this.getAuthHeaders(),
      },
      body: JSON.stringify(data),
    });

    return this.handleResponse<T>(response);
  }

  /**
   * DELETE request
   */
  async delete<T = void>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        ...this.getAuthHeaders(),
      },
    });

    return this.handleResponse<T>(response);
  }

  /**
   * Set authentication token
   */
  setToken(token: string): void {
    if (typeof window !== "undefined") {
      localStorage.setItem("auth_token", token);
    }
  }

  /**
   * Clear authentication token
   */
  clearToken(): void {
    if (typeof window !== "undefined") {
      localStorage.removeItem("auth_token");
    }
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    if (typeof window === "undefined") return false;
    return !!localStorage.getItem("auth_token");
  }

  /**
   * Download file (PDF, Excel, etc.)
   */
  async downloadFile(endpoint: string, filename: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "GET",
      headers: {
        ...this.getAuthHeaders(),
      },
    });

    if (!response.ok) {
      let errorMessage = `HTTP Error ${response.status}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        // JSON parse failed
      }
      throw new ApiError(response.status, errorMessage);
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
}

export const api = new ApiClient();

// ============================================================================
// Platform Types
// ============================================================================

export type Platform = "twitter" | "instagram" | "both";

// ============================================================================
// Type definitions for API responses
// ============================================================================

export interface User {
  id: number;
  username: string;
  name: string;
  party: string;
  district?: string;
  tweet_count?: number;
  instagram_username?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages?: number;
  total_pages?: number;
  has_next?: boolean;
  has_prev?: boolean;
}

export interface DashboardStats {
  // Twitter stats
  total_tweets: number;
  total_original: number;
  total_retweets: number;
  total_retweets_count?: number;
  total_councilors: number;
  active_users: number;
  total_likes: number;
  total_views: number;
  total_replies: number;
  total_profiles?: number;
  // Instagram stats (when platform=instagram or both)
  total_posts?: number;
  total_photos?: number;
  total_videos?: number;
  total_instagram_profiles?: number;
  instagram_active_users?: number;
  total_comments?: number;
  instagram_likes?: number;
  twitter_likes?: number;
  twitter_views?: number;
  twitter_replies?: number;
  twitter_active_users?: number;
  // Combined (when platform=both)
  total_content?: number;
  total_engagement?: number;
  // Platform indicator
  platform?: string;
}

export interface ReportResponse {
  username: string;
  content: string;
  cached: boolean;
  created_at?: string;
  report?: string;
}

export interface PartyReportResponse {
  party: string;
  member_count: number;
  content: string;
}

export interface Tweet {
  id: number;
  username: string;
  tweet_text: string;
  tweet_date: string;
  likes: number;
  retweets: number;
  replies: number;
  views: number;
  is_retweet: boolean;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

// User management types
export interface CreateUserRequest {
  username: string;
  name: string;
  party: string;
  district?: string;
}

export interface CreateUserResponse {
  success: boolean;
  user: User;
}

export interface BulkCreateRequest {
  users: CreateUserRequest[];
}

export interface BulkCreateResponse {
  created: number;
  skipped: number;
  errors: string[];
  total: number;
}

export interface DeleteUserResponse {
  success: boolean;
  deleted: string;
  details: {
    tweets_deleted: number;
    profiles_deleted: number;
    cache_deleted: number;
  };
}

// Comparison types
export interface UserMetrics {
  username: string;
  name: string;
  party: string;
  followers: number;
  tweet_count: number;
  total_likes: number;
  total_retweets: number;
  engagement_rate: number;
}

export interface ComparisonResponse {
  users: UserMetrics[];
}

export interface ComparisonLLMResponse {
  users: UserMetrics[];
  analysis: string;
}

// Multi-user report types
export interface MultiUserReportRequest {
  usernames: string[];
  use_llm: boolean;
}

export interface MultiUserReportResponse {
  usernames: string[];
  content: string;
  member_count: number;
}

// Party comparison types
export interface PartyMetrics {
  party: string;
  member_count: number;
  total_followers: number;
  avg_followers: number;
  tweet_count: number;
  total_likes: number;
  total_retweets: number;
  total_engagement: number;
  engagement_rate: number;
}

export interface PartyComparisonResponse {
  parties: PartyMetrics[];
}

export interface PartyComparisonLLMResponse {
  parties: PartyMetrics[];
  analysis: string;
}

// Tweet types for comparison
export interface TweetItem {
  id: number;
  username: string;
  name: string;
  party: string;
  tweet_text: string;
  tweet_date: string;
  likes: number;
  retweets: number;
  replies: number;
  views: number;
  engagement?: number;
}

export interface WeeklyTopTweetsResponse {
  period: string;
  filter: { party?: string; username?: string };
  tweets: TweetItem[];
}

export interface RecentTweetsResponse {
  filter: { party?: string; username?: string };
  tweets: TweetItem[];
}

// Instagram post item (for listings)
export interface InstagramPostItem {
  id: number;
  username: string;
  name: string;
  party: string;
  caption: string;
  post_date: string;
  post_url: string;
  likes: number;
  comments: number;
  is_video: boolean;
  engagement: number;
}

export interface TopPostsResponse {
  filter: { party?: string; username?: string };
  limit: number;
  posts: InstagramPostItem[];
}

export interface WeeklyTopPostsResponse {
  period: string;
  filter: { party?: string; username?: string };
  posts: InstagramPostItem[];
}

// Instagram types
export interface InstagramPost {
  id: number;
  username: string;
  caption: string;
  post_date: string;
  post_url: string;
  likes: number;
  comments: number;
  is_video: boolean;
  engagement?: number;
}

export interface InstagramProfile {
  username: string;
  full_name?: string;
  bio?: string;
  followers: number;
  following: number;
  posts_count: number;
  date?: string;
}

// Multi-platform request types
export interface GenerateReportRequest {
  username: string;
  use_llm: boolean;
  force_refresh?: boolean;
  platform?: Platform;
}

export interface PartyReportRequestBody {
  party: string;
  use_llm: boolean;
  platform?: Platform;
}

export interface MultiUserReportRequestBody {
  usernames: string[];
  use_llm: boolean;
  platform?: Platform;
}

export interface ComparisonRequestBody {
  usernames: string[];
  platform?: Platform;
}

// Engagement ranking with platform
export interface EngagementRankingItem {
  username: string;
  name: string;
  party: string;
  tweet_count?: number;
  post_count?: number;
  content_count?: number;
  total_likes: number;
  total_retweets?: number;
  total_replies?: number;
  total_views?: number;
  total_comments?: number;
  total_engagement: number;
  platform?: string;
}

// Followers ranking with platform
export interface FollowersRankingItem {
  username: string;
  name: string;
  party: string;
  district?: string;
  followers_count: number;
  following_count: number;
  posts_count?: number;
  platform?: string;
}

// ============================================================================
// Chat with Tweets Types
// ============================================================================

export interface ChatQueryRequest {
  query: string;
  max_results?: number;
  include_summary?: boolean;
  platform?: Platform;
  party_filter?: string;  // Filter tweets by party (e.g., "CHP", "AK Parti")
}

export interface ChatTweetResult {
  id: number;
  username: string;
  name?: string;
  party?: string;
  tweet_text: string;
  tweet_date?: string;
  likes: number;
  retweets: number;
  replies: number;
  views: number;
  relevance_score: number;
  // Classification fields (for criticism search)
  criticism_topic?: string;
  criticism_explanation?: string;
}

export interface ChatSummary {
  total_found: number;
  top_topics: string[];
  sentiment: "olumlu" | "olumsuz" | "notr";
  most_active_users: string[];
  date_range?: string;
}

export interface ChatQueryResponse {
  query: string;
  answer: string;
  summary: ChatSummary;
  tweets: ChatTweetResult[];
  filters_applied: Record<string, unknown>;
  confidence_score: number;
  execution_time_ms: number;
  cached: boolean;
  intent_type: string;
}

export interface ChatSuggestionsResponse {
  suggestions: string[];
}

export interface ChatHealthResponse {
  status: "healthy" | "degraded";
  llm_available: boolean;
  services: {
    intent_parser: string;
    response_generator: string;
  };
  error?: string;
}

// =============================================================================
// Chat Session Types (v5.0)
// =============================================================================

export interface CreateSessionRequest {
  platform?: Platform;
  party_filter?: string;
  title?: string;
}

export interface ChatSession {
  id: string;
  title: string;
  platform: string;
  party_filter?: string;
  created_at: string;
  updated_at?: string;
  message_count: number;
}

export interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface SessionDetailResponse extends ChatSession {
  messages: ChatMessage[];
}

export interface SessionListResponse {
  sessions: ChatSession[];
  total: number;
}

export interface UpdateSessionRequest {
  title?: string;
  platform?: Platform;
  party_filter?: string;
}

export interface AddMessageRequest {
  role: "user" | "assistant";
  content: string;
  metadata?: Record<string, unknown>;
}

// ============================================================================
// Chat API Functions
// ============================================================================

export const chatApi = {
  /**
   * Send a natural language query to search tweets
   */
  query: (data: ChatQueryRequest): Promise<ChatQueryResponse> =>
    api.post<ChatQueryResponse>("/chat/query", data),

  /**
   * Get suggested questions for the chat interface
   * @param platform - Platform filter (twitter, instagram, both)
   * @param party - Party filter for context-aware suggestions
   */
  getSuggestions: (platform?: Platform, party?: string): Promise<ChatSuggestionsResponse> => {
    const params = new URLSearchParams();
    if (platform) params.append("platform", platform);
    if (party) params.append("party", party);
    const queryString = params.toString();
    return api.get<ChatSuggestionsResponse>(`/chat/suggestions${queryString ? `?${queryString}` : ""}`);
  },

  /**
   * Check chat service health
   */
  health: (): Promise<ChatHealthResponse> =>
    api.get<ChatHealthResponse>("/chat/health"),

  // ==========================================================================
  // Session Management (v5.0)
  // ==========================================================================

  /**
   * Create a new chat session
   */
  createSession: (data?: CreateSessionRequest): Promise<ChatSession> =>
    api.post<ChatSession>("/chat/sessions", data || {}),

  /**
   * List all chat sessions
   */
  listSessions: (limit?: number, offset?: number): Promise<SessionListResponse> =>
    api.get<SessionListResponse>(`/chat/sessions?limit=${limit || 20}&offset=${offset || 0}`),

  /**
   * Get a session with messages
   */
  getSession: (sessionId: string): Promise<SessionDetailResponse> =>
    api.get<SessionDetailResponse>(`/chat/sessions/${sessionId}`),

  /**
   * Delete a chat session
   */
  deleteSession: (sessionId: string): Promise<{ success: boolean; message: string }> =>
    api.delete<{ success: boolean; message: string }>(`/chat/sessions/${sessionId}`),

  /**
   * Update a chat session
   */
  updateSession: (sessionId: string, data: UpdateSessionRequest): Promise<ChatSession> =>
    api.put<ChatSession>(`/chat/sessions/${sessionId}`, data),

  /**
   * Add a message to a session
   */
  addMessage: (sessionId: string, data: AddMessageRequest): Promise<ChatMessage> =>
    api.post<ChatMessage>(`/chat/sessions/${sessionId}/messages`, data),
};
