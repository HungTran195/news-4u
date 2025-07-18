'use client';

import { useState } from 'react';
import { Image, ExternalLink } from 'lucide-react';

interface ArticleContentProps {
  content: string;
}

export default function ArticleContent({ content }: ArticleContentProps) {
  const [expandedImages, setExpandedImages] = useState<Set<string>>(new Set());

  if (!content) {
    return (
      <div className="text-gray-500 italic">
        No content available for this article.
      </div>
    );
  }

  // Check if content is HTML
  const isHtmlContent = (content: string) => {
    return content.includes('<') && content.includes('>') &&
      (content.includes('<div') || content.includes('<p') || content.includes('<h'));
  };

  // Parse content to extract text and embedded images
  const parseContent = (content: string) => {
    // If it's HTML content, return it as-is
    if (isHtmlContent(content)) {
      return [{ type: 'html' as const, content }];
    }

    const parts: Array<{ type: 'text' | 'image' | 'html'; content: string; alt?: string; caption?: string }> = [];

    // Split content by image markers
    const segments = content.split(/(\[IMAGE: [^\]]+\])/);

    for (let i = 0; i < segments.length; i++) {
      const segment = segments[i].trim();

      if (segment.startsWith('[IMAGE: ') && segment.endsWith(']')) {
        // Extract image URL
        const imageUrl = segment.slice(8, -1); // Remove '[IMAGE: ' and ']'

        // Look for description and caption in next segments
        let alt = '';
        let caption = '';

        if (i + 1 < segments.length && segments[i + 1].startsWith('[Image description: ')) {
          alt = segments[i + 1].slice(19, -1); // Remove '[Image description: ' and ']'
          i++; // Skip this segment
        }

        if (i + 1 < segments.length && segments[i + 1].startsWith('[Image caption: ')) {
          caption = segments[i + 1].slice(16, -1); // Remove '[Image caption: ' and ']'
          i++; // Skip this segment
        }

        parts.push({
          type: 'image',
          content: imageUrl,
          alt,
          caption
        });
      } else if (segment) {
        // Regular text content
        parts.push({
          type: 'text',
          content: segment
        });
      }
    }

    return parts;
  };

  const contentParts = parseContent(content);

  const toggleImageExpansion = (imageUrl: string) => {
    setExpandedImages(prev => {
      const newSet = new Set(prev);
      if (newSet.has(imageUrl)) {
        newSet.delete(imageUrl);
      } else {
        newSet.add(imageUrl);
      }
      return newSet;
    });
  };

  return (
    <div className="prose prose-lg max-w-none article-html-content">
      {contentParts.map((part, index) => {
        return (
          <div key={index}>
            <div
              dangerouslySetInnerHTML={{ __html: part.content }}
            />
          </div>
        );
      }
      )}
    </div>
  );
} 