'use client';

import { Heart, Coffee } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 py-4 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-center text-sm text-gray-600 dark:text-gray-400">
          <span>Made with</span>
          <Heart className="h-4 w-4 mx-1 text-red-500 fill-current" />
          <span>and</span>
          <Coffee className="h-4 w-4 mx-1 text-amber-600" />
          <span>by QT</span>
        </div>
      </div>
    </footer>
  );
} 