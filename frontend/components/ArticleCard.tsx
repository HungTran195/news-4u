'use client';

import { useState } from 'react';
import { NewsArticle } from '@/lib/api';
import { calculateReadTime, formatRelativeTime, getCategoryColor, getCategoryIcon, getSourceIcon } from '@/lib/utils';
import { ExternalLink, Loader2, Clock } from 'lucide-react';

interface ArticleCardProps {
  article: NewsArticle;
  onArticleClick: (article: NewsArticle) => void;
  isLoading?: boolean;
}

export default function ArticleCard({ article, onArticleClick, isLoading = false }: ArticleCardProps) {
  const [imageError, setImageError] = useState(false);
  const hasContent = article.content && article.content.length > 0;
  const readTime = hasContent && article.content ? calculateReadTime(article.content) : 0;
  const handleClick = () => {
    if (!isLoading) {
      onArticleClick(article);
    }
  };

  return (
    <article 
      className={`card hover:shadow-md transition-all duration-200 cursor-pointer ${
        isLoading ? 'opacity-75 pointer-events-none' : 'hover:scale-[1.02]'
      } bg-white dark:bg-gray-800`}
      onClick={handleClick}
    >
      {/* Mobile: horizontal flex, Desktop: vertical stack */}
      <div className="flex flex-row sm:flex-col items-stretch">
        {/* Desktop: Top row with category and reading time */}
        <div className="hidden sm:flex items-center justify-between p-2">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(article.category)}`}>
            {getCategoryIcon(article.category)} {article.category.replace('_', ' ')}
          </span>
          {/* Reading time on the right (if available) */}
          {hasContent && readTime > 0 && (
            <span className="flex items-center gap-1 text-xs font-medium text-gray-700 dark:text-gray-300">
              <Clock className="h-4 w-4" />{readTime} min read
            </span>
          )}
        </div>
        {/* Image (left on mobile, below top row on desktop) */}
        <div className="px-2 pe-1 sm:px-0 flex justify-center items-center">
          {article.image_url && !imageError && (
            <div className="w-32 flex-shrink-0 rounded overflow-hidden relative bg-white dark:bg-gray-800 sm:w-full sm:h-48 sm:rounded-t-lg sm:rounded-l-none sm:bg-gray-200">
              <img
                src={article.image_url}
                alt={article.title}
                className="w-full h-full object-scale-down sm:object-cover"
                onError={() => setImageError(true)}
              />
              {isLoading && (
                <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
                  <Loader2 className="h-6 w-6 text-white animate-spin" />
                </div>
              )}
            </div>
          )}
        </div>
        {/* Content area */}
        <div className="flex flex-col justify-between p-2 sm:p-4 flex-1">
          {/* Title and summary (always below image) */}
          <div>
            <h2 className="text-base font-semibold text-gray-900 dark:text-gray-200 mb-1 line-clamp-2 sm:text-lg sm:mb-2">
              {article.title}
            </h2>
            {article.summary && (
              <p className="text-gray-600 dark:text-gray-300 text-sm mb-2 line-clamp-3 hidden sm:block">
                {article.summary}
              </p>
            )}
          </div>
          {/* Info row for mobile, below title/summary */}
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs font-medium text-gray-700 dark:text-gray-300 mt-2 sm:hidden">
            {hasContent && readTime > 0 && (
              <span className="flex items-center gap-1"><Clock className="h-4 w-4" />{readTime}m read</span>
            )}
            <span className="flex items-center gap-1"><span className="text-lg">{getSourceIcon(article.source_name)}</span>{article.source_name}</span>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {formatRelativeTime(article.published_date || article.created_at)}
            </span>
          </div>
          {/* Bottom row: source and published date (desktop only) */}
          <div className="hidden sm:flex items-center justify-between text-sm font-medium text-gray-700 dark:text-gray-300 mt-1">
            <div className="flex items-center space-x-2">
              <span className="text-lg">{getSourceIcon(article.source_name)}</span>
              <span>{article.source_name}</span>
            </div>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {formatRelativeTime(article.published_date || article.created_at)}
            </span>
          </div>
        </div>
      </div>
    </article>
  );
} 