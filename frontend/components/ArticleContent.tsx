'use client';

interface ArticleContentProps {
  content: string;
}

export default function ArticleContent({ content }: ArticleContentProps) {
  if (!content) {
    return (
      <div className="text-gray-500 italic">
        No content available for this article.
      </div>
    );
  }

  return (
    <div className="prose prose-lg max-w-none article-html-content">
      <div
        dangerouslySetInnerHTML={{ __html: content }}
      />
    </div>
  );
} 