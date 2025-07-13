'use client';

import { useState } from 'react';
import { NewsArticle } from '@/lib/api';
import { formatDate, formatRelativeTime, getCategoryColor, getCategoryIcon, getSourceIcon, calculateReadTime } from '@/lib/utils';
import { ExternalLink, Loader2, Clock, Calendar } from 'lucide-react';
import ArticleContent from './ArticleContent';

interface ArticleDetailProps {
  article: NewsArticle;
  onBack: () => void;
  onExtractContent?: (articleId: number) => Promise<void>;
}

export default function ArticleDetail({ article, onBack, onExtractContent }: ArticleDetailProps) {
  const [isExtracting, setIsExtracting] = useState(false);

  const handleExtractContent = async () => {
    if (!onExtractContent) return;
    
    setIsExtracting(true);
    try {
      await onExtractContent(article.id);
    } catch (error) {
      // Error handling
    } finally {
      setIsExtracting(false);
    }
  };

  const hasContent = article.content && article.content.length > 0;
  const readTime = hasContent && article.content ? calculateReadTime(article.content) : 0;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Article Header and Image Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-4">
        <div className="flex items-center justify-between mb-4">
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getCategoryColor(article.category)}`}>
            {getCategoryIcon(article.category)} {article.category.replace('_', ' ')}
          </span>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {formatRelativeTime(article.published_date || article.created_at)}
          </span>
        </div>

        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">{article.title}</h1>

        {article.summary && (
          <p className="text-lg text-gray-600 dark:text-gray-300 mb-4 leading-relaxed">{article.summary}</p>
        )}

        {/* Article Image */}
        {article.image_url && (
          <div className="mb-6">
            <a
              href={article.image_url}
              target="_blank"
              rel="noopener noreferrer"
              className="block"
            >
              <img
                src={article.image_url}
                alt={article.title}
                className="w-full h-64 object-cover rounded-lg hover:opacity-90 transition-opacity cursor-pointer"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                }}
              />
            </a>
          </div>
        )}

        {/* Article Details */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <span className="text-xl">{getSourceIcon(article.source_name)}</span>
              <span className="font-medium text-gray-700 dark:text-gray-300">{article.source_name}</span>
            </div>
            {article.author && (
              <span className="text-sm text-gray-500 dark:text-gray-400">by {article.author}</span>
            )}
          </div>

          <a
            href={article.link}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center text-primary-600 hover:text-primary-700 font-medium"
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            Read Original
          </a>
        </div>

        {/* Published Date and Read Time */}
        <div className="flex items-center space-x-6 text-sm text-gray-600 dark:text-gray-400 border-t border-gray-200 dark:border-gray-600 pt-4">
          {article.published_date && (
            <div className="flex items-center space-x-2">
              <Calendar className="h-4 w-4" />
              <span>Published: {formatDate(article.published_date)}</span>
            </div>
          )}
          {hasContent && readTime > 0 && (
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4" />
              <span>{readTime} min read</span>
            </div>
          )}
        </div>
      </div>

      {/* Article Content */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        {hasContent ? (
          <div className="prose max-w-none">
            <ArticleContent content={article.content || ''} />
          </div>
        ) : (
          <div className="text-center py-8">
            <Loader2 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No Content Available</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              The full article content hasn't been extracted yet.
            </p>
            {onExtractContent && (
              <button
                onClick={handleExtractContent}
                disabled={isExtracting}
                className="flex items-center mx-auto px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 transition-colors"
              >
                {isExtracting ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Loader2 className="h-4 w-4 mr-2" />
                )}
                {isExtracting ? 'Extracting...' : 'Extract Content'}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
} 