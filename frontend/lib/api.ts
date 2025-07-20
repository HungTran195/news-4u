import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    console.error('❌ API Request Error:', error);
    return Promise.reject(error);
  }
);

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

export interface NewsArticle {
  article_name: string;
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
  is_processed: boolean;
  created_at: string;
  updated_at?: string;
}

export interface NewsArticleList {
  articles: NewsArticle[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface RSSFeed {
  name: string;
  url: string;
  category: string;
  description?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}


// API functions
export const newsApi = {
  // Get articles
  getArticles: async (params?: {
    category?: string;
    source?: string;
    feeds?: string[];
    limit?: number;
    offset?: number;
  }): Promise<NewsArticleList> => {
    const apiParams: any = { ...params };
    if (params?.feeds && params.feeds.length > 0) {
      apiParams.feeds = params.feeds.join(',');
    }
    const response = await api.get('/api/news/articles', { params: apiParams });
    return response.data;
  },

  // Get article by name
  getArticleByName: async (articleName: string): Promise<NewsArticle> => {
    const response = await api.get(`/api/news/articles/${articleName}`);
    return response.data;
  },

  // Get feeds
  getFeeds: async (): Promise<RSSFeed[]> => {
    const response = await api.get('/api/news/feeds');
    return response.data;
  },

  // Extract article content
  extractArticleContent: async (articleName: string): Promise<any> => {
    const response = await api.post(`/api/news/articles/${articleName}/extract`);
    return response.data;
  },
};
