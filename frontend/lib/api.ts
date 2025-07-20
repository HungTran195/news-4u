import axios from 'axios';


const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    console.error('❌ API Request Error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for debugging
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('❌ API Response Error:');
    console.error('  Status:', error.response?.status);
    console.error('  URL:', error.config?.url);
    console.error('  Message:', error.message);
    return Promise.reject(error);
  }
);

// Types
export interface NewsArticle {
  id: number;
  title: string;
  summary?: string;
  content?: string;
  link: string;
  author?: string;
  published_date?: string;
  category: string;
  source_name: string;
  source_url?: string;
  image_url?: string;
  slug?: string;
  is_processed: boolean;
  created_at: string;
  updated_at?: string;
}

export interface NewsArticleList {
  articles: NewsArticle[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface RSSFeed {
  id: number;
  name: string;
  url: string;
  category: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface FeedFetchLog {
  id: number;
  feed_name: string;
  fetch_timestamp: string;
  status: string;
  articles_found: number;
  articles_processed: number;
  error_message?: string;
  execution_time?: number;
}

export interface HealthCheck {
  status: string;
  timestamp: string;
  database_connected: boolean;
  feeds_count: number;
  articles_count: number;
}

export interface Stats {
  total_articles: number;
  articles_by_category: Record<string, number>;
  articles_by_source: Record<string, number>;
  recent_articles: NewsArticle[];
  active_feeds: number;
  total_feeds: number;
  last_updated: string;
}

export interface ContentExtractionResult {
  success: boolean;
  url: string;
  content: string;
  content_length: number;
  embedded_images: number;
  standalone_images: string[];
  standalone_image_count: number;
  extracted_at: string;
}

// API functions
export const newsApi = {
  // Health check
  health: async (): Promise<HealthCheck> => {
    const response = await api.get('/api/news/health');
    return response.data;
  },

  // Get articles
  getArticles: async (params?: {
    category?: string;
    source?: string;
    feeds?: string[];
    page?: number;
    per_page?: number;
    article_id?: number;
  }): Promise<NewsArticleList> => {
    const apiParams: any = { ...params };
    if (params?.feeds && params.feeds.length > 0) {
      apiParams.feeds = params.feeds.join(',');
    }
    const response = await api.get('/api/news/articles', { params: apiParams });
    return response.data;
  },

  // Get article by ID
  getArticle: async (id: number): Promise<NewsArticle> => {
    const response = await api.get(`/api/news/articles/${id}`);
    return response.data;
  },

  // Get article by slug
  getArticleBySlug: async (slug: string): Promise<NewsArticle> => {
    const response = await api.get(`/api/news/articles/slug/${slug}`);
    return response.data;
  },

  // Get articles by category
  getArticlesByCategory: async (
    category: string,
    page: number = 1,
    per_page: number = 20
  ): Promise<NewsArticleList> => {
    const response = await api.get(`/api/news/categories/${category}`, {
      params: { page, per_page },
    });
    return response.data;
  },

  // Get feeds
  getFeeds: async (): Promise<RSSFeed[]> => {
    const response = await api.get('/api/news/feeds');
    return response.data;
  },

  // Get fetch logs
  getLogs: async (limit: number = 50): Promise<FeedFetchLog[]> => {
    const response = await api.get('/api/news/logs', { params: { limit } });
    return response.data;
  },

  // Get feeds status
  getFeedsStatus: async (): Promise<any[]> => {
    const response = await api.get('/api/news/feeds/status');
    return response.data;
  },

  // Fetch all feeds
  fetchFeeds: async (redoExtraction: boolean = false): Promise<any> => {
    const response = await api.post('/api/news/fetch', null, {
      params: { redo_extraction: redoExtraction }
    });
    return response.data;
  },

  // Fetch specific feed
  fetchSpecificFeed: async (feedName: string): Promise<any> => {
    const response = await api.post(`/api/news/fetch/${encodeURIComponent(feedName)}`);
    return response.data;
  },

  // Get stats
  getStats: async (): Promise<Stats> => {
    const response = await api.get('/api/news/stats');
    return response.data;
  },

  // Extract article content
  extractArticleContent: async (articleId: number): Promise<any> => {
    const response = await api.post(`/api/news/articles/${articleId}/extract`);
    return response.data;
  },

  // Cleanup all data
  cleanupAllData: async (): Promise<any> => {
    const response = await api.delete('/api/news/cleanup/all');
    return response.data;
  },

  // Cleanup specific feed data
  cleanupFeedData: async (feedName: string): Promise<any> => {
    const response = await api.delete(`/api/news/cleanup/feed/${encodeURIComponent(feedName)}`);
    return response.data;
  },

  // Get feed names
  getFeedNames: async (): Promise<string[]> => {
    const response = await api.get('/api/news/feeds/names');
    return response.data.feed_names;
  },

  // Search articles in local database
  searchArticles: async (params: {
    query: string;
    category?: string;
    time_filter?: string;
    page?: number;
    per_page?: number;
  }): Promise<NewsArticleList> => {
    const response = await api.get('/api/news/search', { params });
    return response.data;
  },
};
