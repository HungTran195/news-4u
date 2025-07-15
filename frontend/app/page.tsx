'use client';

import { useState, useEffect } from 'react';
import { newsApi, NewsArticle, Stats } from '@/lib/api';
import { formatRelativeTime, getCategoryColor, getCategoryIcon, getSourceIcon } from '@/lib/utils';
import { Newspaper, Search, Globe, Laptop, Flag } from 'lucide-react';
import ArticleDetail from '@/components/ArticleDetail';
import SearchBar from '@/components/SearchBar';
import Pagination from '@/components/Pagination';
import FeedSelector from '@/components/FeedSelector';
import ArticleCard from '@/components/ArticleCard';
import DarkModeToggle from '@/components/DarkModeToggle';

export default function HomePage() {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedArticle, setSelectedArticle] = useState<NewsArticle | null>(null);
  const [showCleanupModal, setShowCleanupModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'news' | 'search'>('news');
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchCategory, setSearchCategory] = useState('all');
  const [searchTimeFilter, setSearchTimeFilter] = useState('24h');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<NewsArticle[]>([]);
  const [searchTotal, setSearchTotal] = useState(0);
  
  // New state for feed selection and lazy loading
  const [selectedFeeds, setSelectedFeeds] = useState<string[]>([]);
  const [totalArticles, setTotalArticles] = useState(0);
  const [loadingArticles, setLoadingArticles] = useState(false);
  const [loadingArticleId, setLoadingArticleId] = useState<number | null>(null);
  const [hasLoadedArticles, setHasLoadedArticles] = useState(false);

  useEffect(() => {
    loadStats();
    // Automatically load articles on mount
    loadArticles('all', 1);
  }, []);

  useEffect(() => {
    if (hasLoadedArticles) {
      loadArticles();
    }
  }, [currentPage, selectedCategory, selectedFeeds, hasLoadedArticles]);

  const loadStats = async () => {
    try {
      setLoading(true);
      const statsData = await newsApi.getStats();
      setStats(statsData);
    } catch (error) {
      // Error handling
    } finally {
      setLoading(false);
    }
  };

  // Update loadArticles to accept category and page
  const loadArticles = async (category = 'all', page = 1) => {
    try {
      setLoadingArticles(true);
      const params: any = {
        page,
        per_page: 12,
      };
      if (category !== 'all') {
        // Map UI category to backend value
        const categoryMap: Record<string, string> = {
          all: '',
          vn: 'Vietnamese News',
          global: 'Global News',
          us: 'US News',
          tech: 'Tech',
        };
        params.category = categoryMap[category] || category;
      }
      const articlesData = await newsApi.getArticles(params);
      setArticles(articlesData.articles);
      setTotalArticles(articlesData.total);
      setCurrentPage(page);
    } catch (error) {
      // Error handling
    } finally {
      setLoadingArticles(false);
    }
  };

  const handleLoadArticles = () => {
    setHasLoadedArticles(true);
    setCurrentPage(1);
  };

  const handleArticleClick = async (article: NewsArticle) => {
    setLoadingArticleId(article.id);
    try {
      // Load full article content if not already loaded
      if (!article.content) {
        const fullArticle = await newsApi.getArticle(article.id);
        setArticles(prev => prev.map(a => a.id === article.id ? fullArticle : a));
        setSelectedArticle(fullArticle);
      } else {
        setSelectedArticle(article);
      }
    } catch (error) {
      // Still show the article even if content loading fails
      setSelectedArticle(article);
    } finally {
      setLoadingArticleId(null);
    }
  };

  const handleExtractContent = async (articleId: number) => {
    try {
      await newsApi.extractArticleContent(articleId);
      // Reload the specific article to get updated content
      const updatedArticle = articles.find(a => a.id === articleId);
      if (updatedArticle) {
        const response = await newsApi.getArticles({ per_page: 1, article_id: articleId });
        if (response.articles.length > 0) {
          const newArticle = response.articles[0];
          setArticles(prev => prev.map(a => a.id === articleId ? newArticle : a));
          setSelectedArticle(newArticle);
        }
      }
    } catch (error) {
      throw error;
    }
  };

  const handleCleanupComplete = () => {
    // Reload data after cleanup
    loadStats();
    if (hasLoadedArticles) {
      loadArticles();
    }
  };

  const handleSearch = async (query: string, category: string, timeFilter: string) => {
    try {
      setIsSearching(true);
      setSearchQuery(query);
      setSearchCategory(category);
      setSearchTimeFilter(timeFilter);
      setCurrentPage(1);
      
      const result = await newsApi.searchArticles({
        query,
        category,
        time_filter: timeFilter,
        page: 1,
        per_page: 12
      });
      
      if (result.status === 'success') {
        setSearchResults(result.articles);
        setSearchTotal(result.total);
      } else {
        setSearchResults([]);
        setSearchTotal(0);
      }
    } catch (error) {
      setSearchResults([]);
      setSearchTotal(0);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSearchClear = () => {
    setSearchQuery('');
    setSearchCategory('all');
    setSearchTimeFilter('24h');
    setSearchResults([]);
    setSearchTotal(0);
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const handleSearchPageChange = async (page: number) => {
    if (!searchQuery) return;
    
    try {
      setIsSearching(true);
      const result = await newsApi.searchArticles({
        query: searchQuery,
        category: searchCategory,
        time_filter: searchTimeFilter,
        page,
        per_page: 12
      });
      
      if (result.status === 'success') {
        setSearchResults(result.articles);
        setSearchTotal(result.total);
        setCurrentPage(page);
      }
    } catch (error) {
      // Error handling
    } finally {
      setIsSearching(false);
    }
  };

  const handleFeedSelectionChange = (feeds: string[]) => {
    setSelectedFeeds(feeds);
    setCurrentPage(1);
  };

  const handleGoHome = () => {
    setSelectedArticle(null);
    setActiveTab('news');
    setSearchQuery('');
    setSearchResults([]);
    setSearchTotal(0);
  };

  // Pagination logic
  const itemsPerPage = 12;
  const totalPages = Math.ceil(totalArticles / itemsPerPage);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading news...</p>
        </div>
      </div>
    );
  }

  // Tab bar for categories and search
  const categories = [
    { key: 'all', label: 'All News', icon: <Newspaper className="h-4 w-4 mr-1" />, color: 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200' },
    { key: 'vn', label: 'VN', icon: <Flag className="h-4 w-4 mr-1 text-green-600 dark:text-green-300" />, color: 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200' },
    { key: 'global', label: 'Global', icon: <Globe className="h-4 w-4 mr-1 text-purple-600 dark:text-purple-300" />, color: 'bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200' },
    { key: 'us', label: 'US', icon: <Flag className="h-4 w-4 mr-1 text-red-600 dark:text-red-300" />, color: 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200' },
    { key: 'tech', label: 'Tech', icon: <Laptop className="h-4 w-4 mr-1 text-blue-600 dark:text-blue-300" />, color: 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header - Always visible */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-0 lg:px-6">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-3">
              <button
                onClick={handleGoHome}
                className="flex items-center space-x-3 hover:opacity-80 transition-opacity cursor-pointer"
              >
                <Newspaper className="h-8 w-8 text-primary-600" />
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">News 4U</h1>
              </button>
            </div>
            <div className="flex items-center space-x-3">
              <FeedSelector
                selectedFeeds={selectedFeeds}
                onFeedSelectionChange={handleFeedSelectionChange}
              />
              <DarkModeToggle />
            </div>
          </div>
        </div>
      </header>

      {/* Category Tabs */}
      <nav className="max-w-7xl mx-auto px-4 sm:px-0 lg:px-6 mt-4">
        <div className="flex items-center space-x-2 overflow-x-auto pb-2">
          {categories.map((cat) => (
            <button
              key={cat.key}
              onClick={() => {
                setActiveTab('news');
                setSelectedCategory(cat.key);
                loadArticles(cat.key, 1);
              }}
              className={`flex items-center px-3 py-1.5 rounded-full font-medium focus:outline-none transition-all duration-150 border text-xs whitespace-nowrap shadow-sm
                ${activeTab === 'news' && selectedCategory === cat.key
                  ? `${cat.color} border-primary-600 ring-2 ring-primary-200 dark:ring-primary-700`
                  : `${cat.color} border-transparent hover:border-primary-400 hover:ring-1 hover:ring-primary-100 dark:hover:ring-primary-700`}
              `}
              style={{ minWidth: 80 }}
            >
              {cat.icon}
              {cat.label}
            </button>
          ))}
          <div className="flex-1" />
          {/* Search Tab on the far right */}
          <button
            onClick={() => setActiveTab('search')}
            className={`flex items-center px-3 py-1.5 rounded-full font-medium focus:outline-none transition-all duration-150 border-2 text-xs whitespace-nowrap ml-2
              ${activeTab === 'search'
                ? 'border-primary-600 text-primary-700 dark:text-primary-300 bg-primary-50 dark:bg-gray-800 shadow-md'
                : 'border-gray-400 dark:border-gray-600 text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 hover:border-primary-500 hover:text-primary-700'}
            `}
            style={{ minWidth: 80 }}
          >
            <Search className="inline-block mr-1 h-4 w-4 align-text-bottom" /> Search
          </button>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-0 lg:px-6 py-6">
        {activeTab === 'search' ? (
          <SearchBar
            onSearch={handleSearch}
            onClear={handleSearchClear}
            isLoading={isSearching}
          />
        ) : (
          // Article list and pagination
          <>
            {/* Remove Load Articles button and UI */}
            {/* Article List */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {articles.map((article) => (
                <ArticleCard
                  key={article.id}
                  article={article}
                  onArticleClick={handleArticleClick}
                  isLoading={loadingArticleId === article.id}
                />
              ))}
            </div>
            {/* Pagination */}
            {totalArticles > 12 && (
              <Pagination
                currentPage={currentPage}
                totalPages={totalPages}
                totalItems={totalArticles}
                itemsPerPage={itemsPerPage}
                onPageChange={(page) => loadArticles(selectedCategory, page)}
              />
            )}
          </>
        )}
      </main>
      {/* Article Detail Modal (unchanged) */}
      {selectedArticle && (
        <ArticleDetail
          article={selectedArticle}
          onBack={() => setSelectedArticle(null)}
          onExtractContent={handleExtractContent}
        />
      )}
    </div>
  );
} 