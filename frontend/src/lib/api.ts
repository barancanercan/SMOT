const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
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
}

export const api = new ApiClient();

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
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
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
