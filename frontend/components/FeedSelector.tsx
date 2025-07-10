'use client';

import { useState, useEffect, useRef } from 'react';
import { newsApi, RSSFeed } from '@/lib/api';
import { Check, Globe, Settings } from 'lucide-react';

interface FeedSelectorProps {
  selectedFeeds: string[];
  onFeedSelectionChange: (feeds: string[]) => void;
}

export default function FeedSelector({ selectedFeeds, onFeedSelectionChange }: FeedSelectorProps) {
  const [feeds, setFeeds] = useState<RSSFeed[]>([]);
  const [loading, setLoading] = useState(true);
  const [showSelector, setShowSelector] = useState(false);
  const selectorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadFeeds();
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (selectorRef.current && !selectorRef.current.contains(event.target as Node)) {
        setShowSelector(false);
      }
    };

    if (showSelector) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showSelector]);

  const loadFeeds = async () => {
    try {
      setLoading(true);
      const feedsData = await newsApi.getFeeds();
      setFeeds(feedsData);
    } catch (error) {
      console.error('Error loading feeds:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFeedToggle = (feedName: string) => {
    const newSelection = selectedFeeds.includes(feedName)
      ? selectedFeeds.filter(feed => feed !== feedName)
      : [...selectedFeeds, feedName];
    onFeedSelectionChange(newSelection);
  };

  const handleSelectAll = () => {
    const allFeedNames = feeds.map(feed => feed.name);
    onFeedSelectionChange(allFeedNames);
  };

  const handleSelectNone = () => {
    onFeedSelectionChange([]);
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

  if (loading) {
    return (
      <div className="flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
        <span className="ml-2 text-sm text-gray-600">Loading feeds...</span>
      </div>
    );
  }

  return (
    <div className="relative" ref={selectorRef}>
      <button
        onClick={() => setShowSelector(!showSelector)}
        className="flex items-center space-x-2 px-4 py-2 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
      >
        <Settings className="h-4 w-4 text-gray-600" />
        <span className="text-sm font-medium text-gray-700">
          Feeds ({selectedFeeds.length}/{feeds.length})
        </span>
      </button>

      {showSelector && (
        <div className="absolute top-full left-0 mt-1 w-80 bg-white border border-gray-300 rounded-md shadow-lg z-10">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-gray-900">Select Feeds</h3>
              <div className="flex space-x-2">
                <button
                  onClick={handleSelectAll}
                  className="text-xs text-primary-600 hover:text-primary-700"
                >
                  Select All
                </button>
                <button
                  onClick={handleSelectNone}
                  className="text-xs text-gray-600 hover:text-gray-700"
                >
                  Clear
                </button>
              </div>
            </div>
            <div className="text-xs text-gray-500">
              Selected feeds will be used to filter articles
            </div>
          </div>
          
          <div className="max-h-64 overflow-y-auto">
            {feeds.map((feed) => (
              <label
                key={feed.id}
                className="flex items-center p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-b-0"
              >
                <input
                  type="checkbox"
                  checked={selectedFeeds.includes(feed.name)}
                  onChange={() => handleFeedToggle(feed.name)}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <div className="ml-3 flex-1">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-900">{feed.name}</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(feed.category)}`}>
                      {feed.category.replace('_', ' ')}
                    </span>
                  </div>
                  {feed.description && (
                    <p className="text-xs text-gray-500 mt-1 line-clamp-2">{feed.description}</p>
                  )}
                </div>
              </label>
            ))}
          </div>
        </div>
      )}
    </div>
  );
} 