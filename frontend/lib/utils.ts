import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) {
    return 'Just now';
  }

  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) {
    return `${diffInMinutes}m ago`;
  }

  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) {
    return `${diffInHours}h ago`;
  }

  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays < 7) {
    return `${diffInDays}d ago`;
  }

  const diffInWeeks = Math.floor(diffInDays / 7);
  if (diffInWeeks < 4) {
    return `${diffInWeeks}w ago`;
  }

  const diffInMonths = Math.floor(diffInDays / 30);
  if (diffInMonths < 12) {
    return `${diffInMonths}mo ago`;
  }

  const diffInYears = Math.floor(diffInDays / 365);
  return `${diffInYears}y ago`;
}

export function getCategoryColor(category: string): string {
  const colors: Record<string, string> = {
    'tech': 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200',
    'finance': 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200',
    'global_news': 'bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200',
    'vietnam_news': 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200',
    'default': 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
  };
  return colors[category] || colors['default'];
}

export function getCategoryIcon(category: string): string {
  const icons: Record<string, string> = {
    'tech': '💻',
    'finance': '💰',
    'global_news': '🌍',
    'vietnam_news': '🇻🇳',
    'default': '📰'
  };
  return icons[category] || icons['default'];
}

export function getSourceIcon(sourceName: string): string {
  const sourceIcons: Record<string, string> = {
    'Kenh14': '📱',
    'VnExpress': '📰',
    'Tuổi Trẻ': '📖',
    'TechCrunch': '⚡',
    'BBC': '🇬🇧',
    'CNN': '🇺🇸',
    'Vox': '🎯',
    'The Verge': '🔮',
    'default': '📰'
  };
  return sourceIcons[sourceName] || sourceIcons['default'];
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) {
    return text;
  }
  return text.substring(0, maxLength) + '...';
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

export function calculateReadTime(content: string): number {
  const wordsPerMinute = 200;
  const words = content.trim().split(/\s+/).length;
  return Math.ceil(words / wordsPerMinute);
} 