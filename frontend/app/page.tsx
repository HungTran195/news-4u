'use client';

import { useState, useEffect } from 'react';
import { newsApi, NewsArticle, Stats } from '@/lib/api';
import { formatRelativeTime, getCategoryColor, getCategoryIcon, getSourceIcon } from '@/lib/utils';
import { RefreshCw, TrendingUp, Newspaper, Globe, Zap, Trash2, Search } from 'lucide-react';
import ArticleDetail from '@/components/ArticleDetail';
import CleanupModal from '@/components/CleanupModal';
import SearchBar from '@/components/SearchBar';
import Pagination from '@/components/Pagination';

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

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [articlesData, statsData] = await Promise.all([
        newsApi.getArticles({ per_page: 50 }),
        newsApi.getStats(),
      ]);
      setArticles(articlesData.articles);
      setStats(statsData);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFetchFeeds = async () => {
    try {
      setFetching(true);
      await newsApi.fetchFeeds();
      await loadData(); // Reload data after fetching
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
    loadData();
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
        await loadData();
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

  // Pagination logic
  const itemsPerPage = 12;
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  
  const filteredArticles = selectedCategory === 'all' 
    ? articles 
    : articles.filter(article => article.category === selectedCategory);
  
  const paginatedArticles = filteredArticles.slice(startIndex, endIndex);
  const totalPages = Math.ceil(filteredArticles.length / itemsPerPage);

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
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
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

      {/* Articles Grid */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {paginatedArticles.map((article) => (
            <article 
              key={article.id} 
              className="card hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => setSelectedArticle(article)}
            >
              {article.image_url && (
                <div className="aspect-video bg-gray-200 rounded-t-lg overflow-hidden">
                  <img
                    src={article.image_url}
                    alt={article.title}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                </div>
              )}
              <div className="p-6">
                <div className="flex items-center justify-between mb-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(article.category)}`}>
                    {getCategoryIcon(article.category)} {article.category.replace('_', ' ')}
                  </span>
                  <span className="text-xs text-gray-500">
                    {formatRelativeTime(article.published_date || article.created_at)}
                  </span>
                </div>
                <h2 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
                  {article.title}
                </h2>
                {article.summary && (
                  <p className="text-gray-600 text-sm mb-4 line-clamp-3">
                    {article.summary}
                  </p>
                )}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">{getSourceIcon(article.source_name)}</span>
                    <span className="text-sm font-medium text-gray-700">{article.source_name}</span>
                  </div>
                  <a
                    href={article.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Read More →
                  </a>
                </div>
              </div>
            </article>
          ))}
        </div>

        {paginatedArticles.length === 0 && (
          <div className="text-center py-12">
            <Newspaper className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No articles found</h3>
            <p className="text-gray-600">
              {activeTab === 'google' 
                ? 'Try searching for news or fetching RSS feeds.' 
                : 'Try fetching news or selecting a different category.'
              }
            </p>
          </div>
                )}
      </main>

      {/* Pagination */}
      {totalPages > 1 && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={handlePageChange}
          totalItems={filteredArticles.length}
          itemsPerPage={itemsPerPage}
        />
      )}

      {/* Cleanup Modal */}
      <CleanupModal
        isOpen={showCleanupModal}
        onClose={() => setShowCleanupModal(false)}
        onCleanupComplete={handleCleanupComplete}
      />
    </div>
  );
} 