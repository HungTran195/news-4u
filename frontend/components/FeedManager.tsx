'use client';

import { useState, useEffect, useRef } from 'react';
import { newsApi, RSSFeed } from '@/lib/api';
import { RefreshCw, CheckCircle, XCircle, Clock, Settings } from 'lucide-react';

interface FeedManagerProps {
  onFeedFetchComplete?: () => void;
}

interface FeedStatus {
  [feedName: string]: {
    status: 'idle' | 'fetching' | 'success' | 'error';
    message?: string;
    lastFetch?: string;
    articlesFound?: number;
    articlesProcessed?: number;
  };
}

export default function FeedManager({ onFeedFetchComplete }: FeedManagerProps) {
  const [feeds, setFeeds] = useState<RSSFeed[]>([]);
  const [loading, setLoading] = useState(true);
  const [feedStatus, setFeedStatus] = useState<FeedStatus>({});
  const [showManager, setShowManager] = useState(false);
  const managerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadFeeds();
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (managerRef.current && !managerRef.current.contains(event.target as Node)) {
        setShowManager(false);
      }
    };

    if (showManager) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showManager]);

  const loadFeeds = async () => {
    try {
      setLoading(true);
      const [feedsData, feedsStatus] = await Promise.all([
        newsApi.getFeeds(),
        newsApi.getFeedsStatus()
      ]);
      setFeeds(feedsData);
      
      // Initialize status for all feeds with actual data
      const initialStatus: FeedStatus = {};
      feedsData.forEach(feed => {
        const status = feedsStatus.find((s: any) => s.name === feed.name);
        initialStatus[feed.name] = { 
          status: 'idle',
          lastFetch: status?.last_fetch,
          articlesFound: status?.last_articles_found || 0,
          articlesProcessed: status?.last_articles_processed || 0,
          message: status?.last_status === 'error' ? 'Last fetch failed' : undefined
        };
      });
      setFeedStatus(initialStatus);
    } catch (error) {
      console.error('Error loading feeds:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFetchAllFeeds = async () => {
    try {
      setFeedStatus(prev => {
        const newStatus = { ...prev };
        feeds.forEach(feed => {
          newStatus[feed.name] = { status: 'fetching' };
        });
        return newStatus;
      });

      const result = await newsApi.fetchFeeds();
      
      setFeedStatus(prev => {
        const newStatus = { ...prev };
        feeds.forEach(feed => {
          newStatus[feed.name] = { 
            status: 'success',
            lastFetch: new Date().toISOString()
          };
        });
        return newStatus;
      });

      if (onFeedFetchComplete) {
        onFeedFetchComplete();
      }
    } catch (error) {
      console.error('Error fetching all feeds:', error);
      setFeedStatus(prev => {
        const newStatus = { ...prev };
        feeds.forEach(feed => {
          newStatus[feed.name] = { 
            status: 'error',
            message: 'Failed to fetch'
          };
        });
        return newStatus;
      });
    }
  };

  const handleFetchSpecificFeed = async (feedName: string) => {
    try {
      setFeedStatus(prev => ({
        ...prev,
        [feedName]: { status: 'fetching' }
      }));

      const result = await newsApi.fetchSpecificFeed(feedName);
      
      setFeedStatus(prev => ({
        ...prev,
        [feedName]: { 
          status: 'success',
          lastFetch: new Date().toISOString()
        }
      }));

      if (onFeedFetchComplete) {
        onFeedFetchComplete();
      }
    } catch (error) {
      console.error(`Error fetching feed ${feedName}:`, error);
      setFeedStatus(prev => ({
        ...prev,
        [feedName]: { 
          status: 'error',
          message: 'Failed to fetch'
        }
      }));
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'tech':
        return 'bg-blue-100 text-blue-800';
      case 'finance':
        return 'bg-green-100 text-green-800';
      case 'global_news':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'fetching':
        return <RefreshCw className="h-4 w-4 text-blue-600 animate-spin" />;
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-600" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
        <span className="ml-2 text-sm text-gray-600">Loading feeds...</span>
      </div>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={() => setShowManager(!showManager)}
        className="flex items-center space-x-2 px-4 py-2 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
      >
        <Settings className="h-4 w-4 text-gray-600" />
        <span className="text-sm font-medium text-gray-700">
          Feed Manager
        </span>
      </button>

      {showManager && (
        <div className="absolute top-full left-0 mt-1 w-96 bg-white border border-gray-300 rounded-md shadow-lg z-10" ref={managerRef}>
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-gray-900">Feed Management</h3>
              <button
                onClick={handleFetchAllFeeds}
                className="text-xs bg-primary-600 text-white px-2 py-1 rounded hover:bg-primary-700"
              >
                Fetch All
              </button>
            </div>
            <div className="text-xs text-gray-500">
              Manage individual RSS feeds and fetch news
            </div>
          </div>
          
          <div className="max-h-96 overflow-y-auto">
            {feeds.map((feed) => (
              <div
                key={feed.id}
                className="p-3 border-b border-gray-100 last:border-b-0 hover:bg-gray-50"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(feedStatus[feed.name]?.status || 'idle')}
                    <span className="text-sm font-medium text-gray-900">{feed.name}</span>
                  </div>
                  <button
                    onClick={() => handleFetchSpecificFeed(feed.name)}
                    disabled={feedStatus[feed.name]?.status === 'fetching'}
                    className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {feedStatus[feed.name]?.status === 'fetching' ? 'Fetching...' : 'Fetch'}
                  </button>
                </div>
                
                <div className="flex items-center justify-between">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(feed.category)}`}>
                    {feed.category.replace('_', ' ')}
                  </span>
                  
                  <div className="text-right">
                    {feedStatus[feed.name]?.lastFetch && (
                      <div className="text-xs text-gray-500">
                        Last: {new Date(feedStatus[feed.name]?.lastFetch || '').toLocaleString()}
                      </div>
                    )}
                    {(feedStatus[feed.name]?.articlesProcessed || 0) > 0 && (
                      <div className="text-xs text-gray-600">
                        {feedStatus[feed.name]?.articlesProcessed || 0} articles
                      </div>
                    )}
                  </div>
                </div>
                
                {feedStatus[feed.name]?.message && (
                  <div className="mt-1 text-xs text-red-600">
                    {feedStatus[feed.name].message}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
} 