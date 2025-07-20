'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { newsApi, NewsArticle } from '@/lib/api';
import { Newspaper, Globe, Laptop, Flag, RefreshCw } from 'lucide-react';
import FeedManager from '../components/FeedManager';
import ArticleCard from '@/components/ArticleCard';
import DarkModeToggle from '@/components/DarkModeToggle';
import { ARTICLES_PER_PAGE, UI_CATEGORY_MAP } from '@/lib/constants';

function HomePageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // State management
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState<{
    articles: boolean;
    articleName: string | null;
  }>({ articles: false, articleName: null });
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedArticle, setSelectedArticle] = useState<NewsArticle | null>(null);
  const [currentOffset, setCurrentOffset] = useState(0);
  const [selectedFeeds, setSelectedFeeds] = useState<string[]>([]);
  const [totalArticles, setTotalArticles] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  // State persistence functions
  const saveStateToStorage = () => {
    const state = {
      selectedCategory,
      currentOffset,
      selectedFeeds
    };
    localStorage.setItem('news4u_state', JSON.stringify(state));
  };

  const loadStateFromStorage = () => {
    try {
      const savedState = localStorage.getItem('news4u_state');
      if (savedState) {
        const state = JSON.parse(savedState);
        setSelectedCategory(state.selectedCategory || 'all');
        setCurrentOffset(state.currentOffset || 0);
        setSelectedFeeds(state.selectedFeeds || []);
        return state;
      }
    } catch (error) {
      console.error('Error loading state from storage:', error);
    }
    return null;
  };

  const updateURLWithState = () => {
    const params = new URLSearchParams();
    if (selectedCategory !== 'all') params.set('category', selectedCategory);
    if (currentOffset > 0) params.set('offset', currentOffset.toString());
    if (selectedFeeds.length > 0) params.set('feeds', selectedFeeds.join(','));

    const newURL = params.toString() ? `/?${params.toString()}` : '/';
    window.history.replaceState({}, '', newURL);
  };

  const loadStateFromURL = () => {
    const category = searchParams.get('category') || 'all';
    const offset = parseInt(searchParams.get('offset') || '0');
    const feeds = searchParams.get('feeds')?.split(',').filter(Boolean) || [];

    setSelectedCategory(category);
    setCurrentOffset(offset);
    setSelectedFeeds(feeds);

    return { category, offset, feeds };
  };

  useEffect(() => {
    const urlState = loadStateFromURL();
    if (!urlState.category && !urlState.offset && !urlState.feeds.length) {
      const storageState = loadStateFromStorage();
      if (storageState) {
        loadArticles(storageState.selectedCategory, storageState.currentOffset, storageState.selectedFeeds);
      } else {
        loadArticles('all', 0, []);
      }
    } else {
      loadArticles(urlState.category, urlState.offset, urlState.feeds);
    }
  }, []);

  useEffect(() => {
    loadArticles(selectedCategory, currentOffset, selectedFeeds);
  }, [currentOffset, selectedCategory, selectedFeeds]);

  useEffect(() => {
    saveStateToStorage();
    updateURLWithState();
  }, [selectedCategory, currentOffset, selectedFeeds]);

  const loadArticles = async (category = 'all', offset = 0, feeds: string[]) => {
    try {
      setLoading(prev => ({ ...prev, articles: true }));
      const params: any = {
        limit: ARTICLES_PER_PAGE,
        offset: offset,
        feeds: feeds,
      };
      if (category !== 'all') {
        params.category = UI_CATEGORY_MAP[category] || category;
      }
      const articlesData = await newsApi.getArticles(params);
      setArticles(articlesData.articles);
      setTotalArticles(articlesData.total);
      setCurrentOffset(offset);
      setHasMore(articlesData.has_more);
    } catch (error) {
      // Error handling
    } finally {
      setLoading(prev => ({ ...prev, articles: false }));
    }
  };

  const handleArticleClick = async (article: NewsArticle) => {
    saveStateToStorage();
    updateURLWithState();
    router.push(`/article/${article.article_name}`);
  };

  const handleExtractContent = async (articleName: string) => {
    try {
      await newsApi.extractArticleContent(articleName);
      const updatedArticle = articles.find(a => a.article_name === articleName);
      if (updatedArticle) {
        const response = await newsApi.getArticles({ limit: 1, offset: 0 });
        if (response.articles.length > 0) {
          const newArticle = response.articles[0];
          setArticles(prev => prev.map(a => a.article_name === articleName ? newArticle : a));
          setSelectedArticle(newArticle);
        }
      }
    } catch (error) {
      throw error;
    }
  };

  const handleRefreshFeeds = async () => {
    try {
      setLoading(prev => ({ ...prev, articles: true }));
      // Trigger feed refresh
      await fetch('/api/news/fetch', { method: 'POST' });
      // Reload articles
      await loadArticles(selectedCategory, 0, selectedFeeds);
    } catch (error) {
      console.error('Error refreshing feeds:', error);
    } finally {
      setLoading(prev => ({ ...prev, articles: false }));
    }
  };

  const handleLoadMore = async () => {
    if (hasMore) {
      const newOffset = currentOffset + ARTICLES_PER_PAGE;
      await loadArticles(selectedCategory, newOffset, selectedFeeds);
    }
  };

  const handleLoadOlder = async () => {
    if (currentOffset > 0) {
      const newOffset = Math.max(0, currentOffset - ARTICLES_PER_PAGE);
      await loadArticles(selectedCategory, newOffset, selectedFeeds);
    }
  };

  const handleFeedSelectionApply = async (feeds: string[]) => {
    setSelectedFeeds(feeds);
    setCurrentOffset(0);
    setSelectedCategory('all');
    try {
      setLoading(prev => ({ ...prev, articles: true }));
      const params: any = {
        limit: ARTICLES_PER_PAGE,
        offset: 0,
        feeds: feeds,
      };

      const articlesData = await newsApi.getArticles(params);
      setArticles(articlesData.articles);
      setTotalArticles(articlesData.total);
      setCurrentOffset(0);
      setHasMore(articlesData.has_more);
      saveStateToStorage();
      updateURLWithState();
    } catch (error) {
      // Error handling
    } finally {
      setLoading(prev => ({ ...prev, articles: false }));
    }
  };



  if (loading.articles) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading news...</p>
        </div>
      </div>
    );
  }

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
        <div className="max-w-7xl mx-auto px-2 sm:px-0 lg:px-6">
          <div className="flex justify-end items-center py-2 sm:py-4">
            <div className="flex items-center space-x-3 ">
              <div className="mx-4">
                <a href="/" className="flex items-center space-x-3 hover:opacity-80 transition-opacity cursor-pointer">
                  <h1 className="text-xl sm:text-2xl font-bold text-primary-800 dark:text-white">News 4U</h1>
                </a>
              </div>
              <FeedManager
                selectedFeeds={selectedFeeds}
                onFeedSelectionApply={handleFeedSelectionApply}
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
                setSelectedFeeds([]);
                setSelectedCategory(cat.key);
                setCurrentOffset(0);
                loadArticles(cat.key, 0, []);
                saveStateToStorage();
                updateURLWithState();
              }}
              className={`flex items-center px-3 py-1.5 rounded-full font-medium focus:outline-none transition-all duration-150 border text-xs whitespace-nowrap shadow-sm
                ${selectedCategory === cat.key
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
          {/* Refresh Button */}
          <button
            onClick={handleRefreshFeeds}
            disabled={loading.articles}
            className="flex items-center px-3 py-1.5 rounded-full font-medium focus:outline-none transition-all duration-150 border-2 text-xs whitespace-nowrap ml-2 border-gray-400 dark:border-gray-600 text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 hover:border-primary-500 hover:text-primary-700 disabled:opacity-50"
            style={{ minWidth: 80 }}
          >
            <RefreshCw className={`inline-block mr-1 h-4 w-4 align-text-bottom ${loading.articles ? 'animate-spin' : ''}`} /> Refresh
          </button>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-0 sm:px-4 lg:px-6 py-6">
        {/* Articles Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 sm:gap-6 gap-3">
          {articles.map((article) => (
            <ArticleCard
              key={article.article_name}
              article={article}
              onArticleClick={handleArticleClick}
              isLoading={loading.articleName === article.article_name}
            />
          ))}
        </div>

        {/* Load More/Older Buttons */}
        <div className="mt-8 flex justify-center space-x-4">
          {currentOffset > 0 && (
            <button
              onClick={handleLoadOlder}
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
            >
              Load Older
            </button>
          )}
          {hasMore && (
            <button
              onClick={handleLoadMore}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              Load More
            </button>
          )}
        </div>

        {/* No Articles Message */}
        {articles.length === 0 && !loading.articles && (
          <div className="text-center py-12">
            <p className="text-gray-600 dark:text-gray-400">
              No articles found. Try refreshing the feeds or selecting different categories.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

export default function HomePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    }>
      <HomePageContent />
    </Suspense>
  );
} 