'use client';

import { useState } from 'react';
import { Stats } from '@/lib/api';
import { BarChart3, X } from 'lucide-react';

interface StatsCardProps {
  stats: Stats | null;
}

export default function StatsCard({ stats }: StatsCardProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (!stats) return null;

  return (
    <div className="relative">
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 px-3 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md transition-colors"
      >
        <BarChart3 className="h-4 w-4" />
        <span className="text-sm font-medium">Stats</span>
      </button>

      {/* Floating Card */}
      {isOpen && (
        <div className="absolute right-0 top-12 w-80 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Statistics</h3>
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">Total Articles</span>
                <span className="text-lg font-bold text-primary-600">{stats.total_articles}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">Active Feeds</span>
                <span className="text-lg font-bold text-green-600">{stats.active_feeds}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">Tech News</span>
                <span className="text-lg font-bold text-blue-600">
                  {stats.articles_by_category.tech || 0}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">Finance News</span>
                <span className="text-lg font-bold text-purple-600">
                  {stats.articles_by_category.finance || 0}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">Global News</span>
                <span className="text-lg font-bold text-purple-600">
                  {stats.articles_by_category.global_news || 0}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 