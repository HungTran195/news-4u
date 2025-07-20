'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { newsApi, NewsArticle } from '@/lib/api';

export default function ArticlePage() {
  const params = useParams();
  const router = useRouter();
  const [article, setArticle] = useState<NewsArticle | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchArticle = async () => {
      if (!params.slug) return;
      
      try {
        setLoading(true);
        setError(null);
        const articleName = Array.isArray(params.slug) ? params.slug[0] : params.slug;
        const articleData = await newsApi.getArticleByName(articleName);
        setArticle(articleData);
      } catch (err) {
        console.error('Error fetching article:', err);
        setError('Article not found');
      } finally {
        setLoading(false);
      }
    };

    fetchArticle();
  }, [params.slug]);

  const handleGoBack = () => {
    router.back();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
            Loading...
          </h1>
        </div>
      </div>
    );
  }

  if (error || !article) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
        <div className="max-w-4xl mx-auto">
          <button
            onClick={handleGoBack}
            className="mb-4 text-blue-600 hover:text-blue-800"
          >
            ← Back
          </button>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
            {error || 'Article not found'}
          </h1>
          <p className="text-gray-600 dark:text-gray-300">
            The article you're looking for doesn't exist or has been removed.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 sm:p-8 p-2">
      <div className="max-w-4xl mx-auto">
        <button
          onClick={handleGoBack}
          className="mb-2 sm:mb-4 text-blue-600 hover:text-blue-800"
        >
          ← Back to News
        </button>

        {/* image url */}
        {article.image_url && (
          <img src={article.image_url} alt={article.title} className="w-full h-auto mb-4" />
        )}

        <article className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden">
          <div className="p-4 sm:p-6">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              {article.title}
            </h1>
            
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              <p>Source: {article.source_name}</p>
              {article.published_date && (
                <p>Published: {new Date(article.published_date).toLocaleDateString()}</p>
              )}
            </div>
            
            {article.content ? (
              <div 
                className="text-gray-700 dark:text-gray-300 text-md article-html-content"
                dangerouslySetInnerHTML={{ __html: article.content }}
              />
            ) : (
              <p className="text-gray-600 dark:text-gray-400">
                Full content not available. 
                <a 
                  href={article.link} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 ml-2"
                >
                  Read on original site →
                </a>
              </p>
            )}
            
            {/* Original Source Link */}
            <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  <p>Original source: <span className="font-medium">{article.source_name}</span></p>
                  {article.published_date && (
                    <p>Published: {new Date(article.published_date).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}</p>
                  )}
                </div>
                <a 
                  href={article.link} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm font-medium"
                >
                  Visit Original Site
                  <svg className="ml-2 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              </div>
            </div>
          </div>
        </article>
      </div>
    </div>
  );
} 