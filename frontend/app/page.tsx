'use client';

import { useState, useEffect } from 'react';
import { newsApi, NewsArticle, Stats } from '@/lib/api';
import { formatRelativeTime, getCategoryColor, getCategoryIcon, getSourceIcon } from '@/lib/utils';
import { Newspaper, Search } from 'lucide-react';
import ArticleDetail from '@/components/ArticleDetail';
import CleanupModal from '@/components/CleanupModal';
import SearchBar from '@/components/SearchBar';
import Pagination from '@/components/Pagination';
import FeedSelector from '@/components/FeedSelector';
import ArticleCard from '@/components/ArticleCard';
import DebugEnv from '@/components/DebugEnv';
import StatsCard from '@/components/StatsCard';
import DarkModeToggle from '@/components/DarkModeToggle';

export default function HomePage() {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedArticle, setSelectedArticle] = useState<NewsArticle | null>(null);
  const [showCleanupModal, setShowCleanupModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'rss' | 'search'>('rss');
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
      // Error handling
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
    setActiveTab('rss');
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

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header - Always visible */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
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
              <StatsCard stats={stats} />
              <DarkModeToggle />
            </div>
          </div>
        </div>
      </header>

      {/* Tabs - Only show when not viewing article detail */}
      {!selectedArticle && (
        <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex space-x-8">
              <button
                onClick={() => setActiveTab('rss')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'rss'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <Newspaper className="inline h-4 w-4 mr-2" />
                RSS Feeds
              </button>
              <button
                onClick={() => setActiveTab('search')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'search'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <Search className="inline h-4 w-4 mr-2" />
                Search
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Search - Only show when not viewing article detail */}
      {!selectedArticle && activeTab === 'search' && (
        <div className="bg-gray-50 dark:bg-gray-900 py-6">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <SearchBar
              onSearch={handleSearch}
              onClear={handleSearchClear}
              isLoading={isSearching}
            />
          </div>
        </div>
      )}

      {/* Search Results - Only show when not viewing article detail */}
      {!selectedArticle && activeTab === 'search' && searchQuery && (
        <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Database Search Results for "{searchQuery}"
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Found {searchTotal} articles
                </p>
              </div>
              <button
                onClick={handleSearchClear}
                className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
              >
                Clear Search
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Category Filter (RSS Tab) - Only show when not viewing article detail */}
      {!selectedArticle && activeTab === 'rss' && (
        <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex space-x-4 overflow-x-auto">
              <button
                onClick={() => setSelectedCategory('all')}
                className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap ${
                  selectedCategory === 'all'
                    ? 'bg-primary-100 dark:bg-primary-900 text-primary-800 dark:text-primary-200'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                All News
              </button>
              <button
                onClick={() => setSelectedCategory('tech')}
                className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap ${
                  selectedCategory === 'tech'
                    ? 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                💻 Technology
              </button>
              <button
                onClick={() => setSelectedCategory('finance')}
                className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap ${
                  selectedCategory === 'finance'
                    ? 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                💰 Finance
              </button>
              <button
                onClick={() => setSelectedCategory('global_news')}
                className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap ${
                  selectedCategory === 'global_news'
                    ? 'bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                🌍 Global News
              </button>
              <button
                onClick={() => setSelectedCategory('vietnam_news')}
                className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap ${
                  selectedCategory === 'vietnam_news'
                    ? 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                🇻🇳 Vietnam News
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Show article detail view if an article is selected */}
        {selectedArticle ? (
          <ArticleDetail
            article={selectedArticle}
            onBack={() => setSelectedArticle(null)}
            onExtractContent={handleExtractContent}
          />
        ) : (
          <>
            {/* RSS Feeds Content */}
            {activeTab === 'rss' && (
              <>
                {/* Load Articles Button (if not loaded yet) */}
                {!hasLoadedArticles && (
                  <div className="text-center py-12">
                    <Newspaper className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-xl font-medium text-gray-900 dark:text-white mb-2">Ready to explore news?</h3>
                    <p className="text-gray-600 dark:text-gray-400 mb-6">
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
                            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No articles found</h3>
                            <p className="text-gray-600 dark:text-gray-400">
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
              </>
            )}

            {/* Search Results Content */}
            {activeTab === 'search' && (
              <>
                {isSearching ? (
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
                ) : searchQuery ? (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      {searchResults.map((article) => (
                        <ArticleCard
                          key={article.id}
                          article={article}
                          onArticleClick={handleArticleClick}
                          isLoading={loadingArticleId === article.id}
                        />
                      ))}
                    </div>

                    {searchResults.length === 0 && (
                      <div className="text-center py-12">
                        <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No search results found</h3>
                        <p className="text-gray-600 dark:text-gray-400">
                          Try a different search term or category.
                        </p>
                      </div>
                    )}

                    {/* Search Pagination */}
                    {searchTotal > 12 && (
                      <Pagination
                        currentPage={currentPage}
                        totalPages={Math.ceil(searchTotal / 12)}
                        onPageChange={handleSearchPageChange}
                        totalItems={searchTotal}
                        itemsPerPage={12}
                      />
                    )}
                  </>
                ) : (
                  <div className="text-center py-12">
                    <Search className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-xl font-medium text-gray-900 dark:text-white mb-2">Database Search</h3>
                    <p className="text-gray-600 dark:text-gray-400 mb-6">
                      Use the search bar above to find articles in your local database.
                    </p>
                  </div>
                )}
              </>
            )}
          </>
        )}
      </main>

      {/* Cleanup Modal */}
      <CleanupModal
        isOpen={showCleanupModal}
        onClose={() => setShowCleanupModal(false)}
        onCleanupComplete={handleCleanupComplete}
      />

      {/* Debug Environment Variables (Development Only) */}
      <DebugEnv />
    </div>
  );
} 