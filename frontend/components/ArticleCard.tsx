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
      {article.image_url && !imageError && (
        <div className="aspect-video bg-gray-200 rounded-t-lg overflow-hidden relative">
          <img
            src={article.image_url}
            alt={article.title}
            className="w-full h-full object-cover"
            onError={() => setImageError(true)}
          />
          {isLoading && (
            <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
              <Loader2 className="h-6 w-6 text-white animate-spin" />
            </div>
          )}
        </div>
      )}
      
      <div className="p-6">
        <div className="flex items-center justify-between mb-3">
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(article.category)}`}>
            {getCategoryIcon(article.category)} {article.category.replace('_', ' ')}
          </span>
          <span className="text-xs text-gray-500 dark:text-gray-400">
            {formatRelativeTime(article.published_date || article.created_at)}
          </span>
        </div>
        
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-200 mb-2 line-clamp-2">
          {article.title}
        </h2>
        
        {article.summary && (
          <p className="text-gray-600 dark:text-gray-300 text-sm mb-4 line-clamp-3">
            {article.summary}
          </p>
        )}
        
        <div className="flex items-center justify-between text-sm font-medium text-gray-700 dark:text-gray-300 ">
          <div className="flex items-center space-x-2">
            <span className="text-lg">{getSourceIcon(article.source_name)}</span>
            <span >{article.source_name}</span>
          </div>
          
          <div className="flex items-center space-x-2">
            {isLoading && (
              <Loader2 className="h-4 w-4 text-primary-600 animate-spin" />
            )}
            {hasContent && readTime > 0 && (
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4" />
              <span>{readTime} min read</span>
            </div>
          )}
          </div>
        </div>
      </div>
    </article>
  );
} 