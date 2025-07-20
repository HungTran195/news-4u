'use client';

import { useState, useEffect, useRef } from 'react';
import { newsApi, RSSFeed } from '@/lib/api';
import { Settings } from 'lucide-react';
import { CATEGORY_COLORS } from '@/lib/constants';

interface FeedManagerProps {
  selectedFeeds: string[];
  onFeedSelectionApply: (feeds: string[]) => void;
}

export default function FeedManager({ selectedFeeds, onFeedSelectionApply }: FeedManagerProps) {
  const [feeds, setFeeds] = useState<RSSFeed[]>([]);
  const [loading, setLoading] = useState(true);
  const [showSelector, setShowSelector] = useState(false);
  const [localSelection, setLocalSelection] = useState<string[]>(selectedFeeds);
  const [applying, setApplying] = useState(false);
  const selectorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadFeeds();
  }, []);

  useEffect(() => {
    setLocalSelection(selectedFeeds);
  }, [selectedFeeds]);

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
    setLocalSelection((prev) =>
      prev.includes(feedName)
        ? prev.filter(feed => feed !== feedName)
        : [...prev, feedName]
    );
  };

  const handleSelectAll = () => {
    const allFeedNames = feeds.map(feed => feed.name);
    setLocalSelection(allFeedNames);
  };

  const handleSelectNone = () => {
    setLocalSelection([]);
  };

  const handleApply = async () => {
    setApplying(true);
    try {
      await onFeedSelectionApply(localSelection);
      setShowSelector(false);
    } catch (err) {
      console.error(err);
    } finally {
      setApplying(false);
    }
  };

  const getCategoryColor = (category: string) => {
    const normalizedCategory = category.toLowerCase().replace(/\s/g, '_');
    return CATEGORY_COLORS[normalizedCategory] || CATEGORY_COLORS['default'];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
        <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">Loading feeds...</span>
      </div>
    );
  }

  return (
    <div className="relative" ref={selectorRef}>
      <button
        onClick={() => setShowSelector(!showSelector)}
        className="flex items-center space-x-2 px-2 sm:px-4 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
      >
        <Settings className="h-4 w-4 text-gray-600 dark:text-gray-400" />
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Feeds ({selectedFeeds.length}/{feeds.length})
        </span>
      </button>

      {showSelector && (
        <div className="absolute top-full mt-1 w-80 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-md shadow-lg z-10" style={{ left: '-100%' }}>
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-medium text-gray-900 dark:text-white">Select Feeds</h3>
              <div className="flex space-x-2">
                <button
                  onClick={handleSelectAll}
                  className="text-xs text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300"
                >
                  Select All
                </button>
                <button
                  onClick={handleSelectNone}
                  className="text-xs text-gray-600 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                >
                  Clear
                </button>
              </div>
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Selected feeds will be used to filter articles
            </div>
          </div>
          <div className="max-h-64 overflow-y-auto bg-white dark:bg-gray-800">
            {feeds.map((feed) => (
              <label
                key={feed.id}
                className="flex items-center p-3 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer border-b border-gray-100 dark:border-gray-700 last:border-b-0"
              >
                <input
                  type="checkbox"
                  checked={localSelection.includes(feed.name)}
                  onChange={() => handleFeedToggle(feed.name)}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-900"
                />
                <div className="ml-3 flex-1">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-900 dark:text-white">{feed.name}</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(feed.category)}`}>
                      {feed.category.replace('_', ' ')}
                    </span>
                  </div>
                </div>
              </label>
            ))}
          </div>
          <div className="flex justify-end p-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
            <button
              onClick={handleApply}
              disabled={applying || (localSelection.sort().join(',') === selectedFeeds.sort().join(','))}
              className={`px-2 py-1 rounded-md text-sm font-medium bg-primary-600 text-white hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {applying ? 'Applying...' : 'Apply'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
} 