'use client';

import { useState } from 'react';
import { NewsArticle } from '@/lib/api';
import { formatDate, formatRelativeTime, getCategoryColor, getCategoryIcon, getSourceIcon } from '@/lib/utils';
import { ExternalLink, Download, ArrowLeft, Loader2 } from 'lucide-react';

interface ArticleDetailProps {
  article: NewsArticle;
  onBack: () => void;
  onExtractContent?: (articleId: number) => Promise<void>;
}

export default function ArticleDetail({ article, onBack, onExtractContent }: ArticleDetailProps) {
  const [isExtracting, setIsExtracting] = useState(false);
  const [showFullContent, setShowFullContent] = useState(false);

  const handleExtractContent = async () => {
    if (!onExtractContent) return;
    
    setIsExtracting(true);
    try {
      await onExtractContent(article.id);
      setShowFullContent(true);
    } catch (error) {
      console.error('Failed to extract content:', error);
    } finally {
      setIsExtracting(false);
    }
  };

  const hasContent = article.content && article.content.length > 0;
  const contentPreview = article.content ? article.content.substring(0, 500) + '...' : '';

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Back Button */}
      <button
        onClick={onBack}
        className="flex items-center text-gray-600 hover:text-gray-900 mb-6 transition-colors"
      >
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to Articles
      </button>

      {/* Article Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getCategoryColor(article.category)}`}>
            {getCategoryIcon(article.category)} {article.category.replace('_', ' ')}
          </span>
          <span className="text-sm text-gray-500">
            {formatRelativeTime(article.published_date || article.created_at)}
          </span>
        </div>

        <h1 className="text-3xl font-bold text-gray-900 mb-4">{article.title}</h1>

        {article.summary && (
          <p className="text-lg text-gray-600 mb-4 leading-relaxed">{article.summary}</p>
        )}

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <span className="text-xl">{getSourceIcon(article.source_name)}</span>
              <span className="font-medium text-gray-700">{article.source_name}</span>
            </div>
            {article.author && (
              <span className="text-sm text-gray-500">by {article.author}</span>
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
      </div>

      {/* Article Image */}
      {article.image_url && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
          <img
            src={article.image_url}
            alt={article.title}
            className="w-full h-64 object-cover rounded-lg"
            onError={(e) => {
              e.currentTarget.style.display = 'none';
            }}
          />
        </div>
      )}

      {/* Content Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Article Content</h2>
          {!hasContent && onExtractContent && (
            <button
              onClick={handleExtractContent}
              disabled={isExtracting}
              className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 transition-colors"
            >
              {isExtracting ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Download className="h-4 w-4 mr-2" />
              )}
              {isExtracting ? 'Extracting...' : 'Extract Content'}
            </button>
          )}
        </div>

        {hasContent ? (
          <div className="prose max-w-none">
            {showFullContent ? (
              <div className="whitespace-pre-wrap text-gray-700 leading-relaxed">
                {article.content}
              </div>
            ) : (
              <div>
                <div className="whitespace-pre-wrap text-gray-700 leading-relaxed mb-4">
                  {contentPreview}
                </div>
                <button
                  onClick={() => setShowFullContent(true)}
                  className="text-primary-600 hover:text-primary-700 font-medium"
                >
                  Read Full Article →
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-8">
            <Download className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Content Available</h3>
            <p className="text-gray-600 mb-4">
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
                  <Download className="h-4 w-4 mr-2" />
                )}
                {isExtracting ? 'Extracting...' : 'Extract Content'}
              </button>
            )}
          </div>
        )}
      </div>

      {/* Article Metadata */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mt-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Article Details</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium text-gray-700">Published:</span>
            <span className="ml-2 text-gray-600">
              {article.published_date ? formatDate(article.published_date) : 'Unknown'}
            </span>
          </div>
          <div>
            <span className="font-medium text-gray-700">Source:</span>
            <span className="ml-2 text-gray-600">{article.source_name}</span>
          </div>
          <div>
            <span className="font-medium text-gray-700">Category:</span>
            <span className="ml-2 text-gray-600">{article.category.replace('_', ' ')}</span>
          </div>
          <div>
            <span className="font-medium text-gray-700">Content Length:</span>
            <span className="ml-2 text-gray-600">
              {article.content ? `${article.content.length} characters` : 'Not extracted'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
} 