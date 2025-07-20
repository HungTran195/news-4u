export const ARTICLES_PER_PAGE = 20;

export const CATEGORY_COLORS: Record<string, string> = {
  'tech': 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200',
  'finance': 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200',
  'global_news': 'bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200',
  'vietnam_news': 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200',
  'us_news': 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200',
  'vietnamese_news': 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200',
  'default': 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
};

export const CATEGORY_ICONS: Record<string, string> = {
  'tech': '💻',
  'finance': '💰',
  'global_news': '🌍',
  'vietnam_news': '🇻🇳',
  'us_news': '🇺🇸',
  'vietnamese_news': '🇻🇳',
  'default': '📰'
};

export const SOURCE_ICONS: Record<string, string> = {
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

export const UI_CATEGORY_MAP: Record<string, string> = {
  'all': '',
  'vn': 'Vietnamese News',
  'global': 'Global News',
  'us': 'US News',
  'tech': 'Tech',
}; 