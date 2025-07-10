'use client';

import { useState, useEffect } from 'react';
import { newsApi, NewsArticle, Stats } from '@/lib/api';
import { formatRelativeTime, getCategoryColor, getCategoryIcon, getSourceIcon } from '@/lib/utils';
import { RefreshCw, TrendingUp, Newspaper, Globe, Zap, Trash2, Search } from 'lucide-react';
import ArticleDetail from '@/components/ArticleDetail';
import CleanupModal from '@/components/CleanupModal';
import SearchBar from '@/components/SearchBar';
import Pagination from '@/components/Pagination';
import FeedSelector from '@/components/FeedSelector';
import ArticleCard from '@/components/ArticleCard';

export default function HomePage() {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetching, setFetching] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedArticle, setSelectedArticle] = useState<NewsArticle | null>(null);
  const [showCleanupModal, setShowCleanupModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'rss' | 'google'>('rss');
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
      console.error('Error loading stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadArticles = async () => {
    try {
      setLoadingArticles(true);
      const params: any = {
        page: currentPage,
        per_page: 12
      };
      
      if (selectedCategory !== 'all') {
        params.category = selectedCategory;
      }
      
      if (selectedFeeds.length > 0) {
        params.feeds = selectedFeeds;
      }
      
      const articlesData = await newsApi.getArticles(params);
      setArticles(articlesData.articles);
      setTotalArticles(articlesData.total);
    } catch (error) {
      console.error('Error loading articles:', error);
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
      console.error('Error loading article:', error);
      // Still show the article even if content loading fails
      setSelectedArticle(article);
    } finally {
      setLoadingArticleId(null);
    }
  };

  const handleFetchFeeds = async () => {
    try {
      setFetching(true);
      await newsApi.fetchFeeds();
      await loadStats(); // Reload stats after fetching
      if (hasLoadedArticles) {
        await loadArticles(); // Reload articles if they were already loaded
      }
    } catch (error) {
      console.error('Error fetching feeds:', error);
    } finally {
      setFetching(false);
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
      console.error('Error extracting content:', error);
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
      
      const result = await newsApi.searchGoogleNews({
        query,
        category,
        time_filter: timeFilter,
        max_results: 50
      });
      
      if (result.status === 'success') {
        // Reload articles to show the newly saved ones
        await loadStats();
        if (hasLoadedArticles) {
          await loadArticles();
        }
        setSearchResults([]);
        setSearchTotal(0);
      } else {
        console.error('Search failed:', result.error_message);
      }
    } catch (error) {
      console.error('Error searching Google News:', error);
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

  const handleFeedSelectionChange = (feeds: string[]) => {
    setSelectedFeeds(feeds);
    setCurrentPage(1);
  };

  // Pagination logic
  const itemsPerPage = 12;
  const totalPages = Math.ceil(totalArticles / itemsPerPage);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading news...</p>
        </div>
      </div>
    );
  }

  // Show article detail view if an article is selected
  if (selectedArticle) {
    return (
      <div className="min-h-screen bg-gray-50">
        <ArticleDetail
          article={selectedArticle}
          onBack={() => setSelectedArticle(null)}
          onExtractContent={handleExtractContent}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-3">
              <Newspaper className="h-8 w-8 text-primary-600" />
              <h1 className="text-2xl font-bold text-gray-900">News 4U</h1>
            </div>
            <div className="flex items-center space-x-3">
              <FeedSelector
                selectedFeeds={selectedFeeds}
                onFeedSelectionChange={handleFeedSelectionChange}
              />
              <button
                onClick={handleFetchFeeds}
                disabled={fetching}
                className="btn btn-primary px-4 py-2"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${fetching ? 'animate-spin' : ''}`} />
                {fetching ? 'Fetching...' : 'Fetch News'}
              </button>
              <button
                onClick={() => setShowCleanupModal(true)}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors flex items-center"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Cleanup
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Stats */}
      {stats && (
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-primary-600">{stats.total_articles}</div>
                <div className="text-sm text-gray-600">Total Articles</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{stats.active_feeds}</div>
                <div className="text-sm text-gray-600">Active Feeds</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {stats.articles_by_category.tech || 0}
                </div>
                <div className="text-sm text-gray-600">Tech News</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {stats.articles_by_category.finance || 0}
                </div>
                <div className="text-sm text-gray-600">Finance News</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {stats.articles_by_category.global_news || 0}
                </div>
                <div className="text-sm text-gray-600">Global News</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            <button
              onClick={() => setActiveTab('rss')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'rss'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Newspaper className="inline h-4 w-4 mr-2" />
              RSS Feeds
            </button>
            <button
              onClick={() => setActiveTab('google')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'google'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Search className="inline h-4 w-4 mr-2" />
              Google News Search
            </button>
          </div>
        </div>
      </div>

      {/* Google News Search */}
      {activeTab === 'google' && (
        <div className="bg-gray-50 py-6">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <SearchBar
              onSearch={handleSearch}
              onClear={handleSearchClear}
              isLoading={isSearching}
            />
          </div>
        </div>
      )}

      {/* Category Filter (RSS Tab) */}
      {activeTab === 'rss' && (
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex space-x-4 overflow-x-auto">
              <button
                onClick={() => setSelectedCategory('all')}
                className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap ${
                  selectedCategory === 'all'
                    ? 'bg-primary-100 text-primary-800'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                All News
              </button>
              <button
                onClick={() => setSelectedCategory('tech')}
                className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap ${
                  selectedCategory === 'tech'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                💻 Technology
              </button>
              <button
                onClick={() => setSelectedCategory('finance')}
                className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap ${
                  selectedCategory === 'finance'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                💰 Finance
              </button>
              <button
                onClick={() => setSelectedCategory('global_news')}
                className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap ${
                  selectedCategory === 'global_news'
                    ? 'bg-purple-100 text-purple-800'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                🌍 Global News
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Load Articles Button (if not loaded yet) */}
        {!hasLoadedArticles && activeTab === 'rss' && (
          <div className="text-center py-12">
            <Newspaper className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-medium text-gray-900 mb-2">Ready to explore news?</h3>
            <p className="text-gray-600 mb-6">
              Click the button below to load articles from your selected feeds and categories.
            </p>
            <button
              onClick={handleLoadArticles}
              className="btn btn-primary px-6 py-3 text-lg"
            >
              <Newspaper className="h-5 w-5 mr-2" />
              Load Articles
            </button>
          </div>
        )}

        {/* Articles Grid */}
        {hasLoadedArticles && (
          <>
            {loadingArticles ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {Array.from({ length: 6 }).map((_, index) => (
                  <div key={index} className="card animate-pulse">
                    <div className="aspect-video bg-gray-200 rounded-t-lg"></div>
                    <div className="p-6">
                      <div className="h-4 bg-gray-200 rounded mb-2"></div>
                      <div className="h-4 bg-gray-200 rounded mb-2"></div>
                      <div className="h-4 bg-gray-200 rounded mb-4 w-3/4"></div>
                      <div className="h-3 bg-gray-200 rounded mb-2"></div>
                      <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {articles.map((article) => (
                    <ArticleCard
                      key={article.id}
                      article={article}
                      onArticleClick={handleArticleClick}
                      isLoading={loadingArticleId === article.id}
                    />
                  ))}
                </div>

                {articles.length === 0 && (
                  <div className="text-center py-12">
                    <Newspaper className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No articles found</h3>
                    <p className="text-gray-600">
                      Try fetching news or selecting a different category.
                    </p>
                  </div>
                )}
              </>
            )}
          </>
        )}

        {/* Pagination */}
        {hasLoadedArticles && totalPages > 1 && !loadingArticles && (
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={handlePageChange}
            totalItems={totalArticles}
            itemsPerPage={itemsPerPage}
          />
        )}
      </main>

      {/* Cleanup Modal */}
      <CleanupModal
        isOpen={showCleanupModal}
        onClose={() => setShowCleanupModal(false)}
        onCleanupComplete={handleCleanupComplete}
      />
    </div>
  );
} 