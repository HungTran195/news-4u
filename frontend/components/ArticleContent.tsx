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
    <div className="prose prose-lg max-w-none">
      {contentParts.map((part, index) => {
        if (part.type === 'html') {
          // HTML content - render as-is with styling
          return (
            <div 
              key={index} 
              className="article-html-content"
              dangerouslySetInnerHTML={{ __html: part.content }}
            />
          );
        } else if (part.type === 'image') {
          const isExpanded = expandedImages.has(part.content);
          
          return (
            <div key={index} className="my-6">
              <div className="relative group">
                <img
                  src={part.content}
                  alt={part.alt || 'Article image'}
                  className={`w-full rounded-lg shadow-md transition-all duration-300 cursor-pointer ${
                    isExpanded ? 'max-w-none' : 'max-h-96 object-cover'
                  }`}
                  onClick={() => toggleImageExpansion(part.content)}
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                  }}
                />
                
                {/* Image overlay with controls */}
                <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-300 flex items-center justify-center opacity-0 group-hover:opacity-100">
                  <div className="flex space-x-2">
                    <button
                      onClick={() => toggleImageExpansion(part.content)}
                      className="bg-white bg-opacity-90 p-2 rounded-full shadow-lg hover:bg-opacity-100 transition-all"
                      title={isExpanded ? 'Shrink image' : 'Expand image'}
                    >
                      <Image className="h-4 w-4 text-gray-700" />
                    </button>
                    <a
                      href={part.content}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="bg-white bg-opacity-90 p-2 rounded-full shadow-lg hover:bg-opacity-100 transition-all"
                      title="Open image in new tab"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <ExternalLink className="h-4 w-4 text-gray-700" />
                    </a>
                  </div>
                </div>
              </div>
              
              {/* Image description */}
              {part.alt && (
                <p className="text-sm text-gray-600 mt-2 italic">
                  {part.alt}
                </p>
              )}
              
              {/* Image caption */}
              {part.caption && (
                <p className="text-sm text-gray-500 mt-1 text-center">
                  {part.caption}
                </p>
              )}
            </div>
          );
        } else {
          // Text content
          return (
            <div key={index} className="mb-4">
              {part.content.split('\n').map((paragraph, pIndex) => (
                <p key={pIndex} className="mb-3 leading-relaxed">
                  {paragraph}
                </p>
              ))}
            </div>
          );
        }
      })}
    </div>
  );
} 