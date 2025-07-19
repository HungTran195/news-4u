import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { DarkModeProvider } from '@/lib/darkMode';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'News 4U - Your Personal News Aggregator',
  keywords: ['news', 'RSS', 'aggregator', 'technology', 'finance', 'world news', 'personal news', 'news reader'],
  authors: [{ name: 'Quoc Hung' }],
  description: 'Stay informed with News 4U - your intelligent news aggregator that brings together the latest stories from multiple RSS feeds. Get personalized news updates on technology, finance, world events, and more in one convenient place.',
  openGraph: {
    title: 'News 4U - Your Personal News Aggregator',
    description: 'Stay informed with News 4U - your intelligent news aggregator that brings together the latest stories from multiple RSS feeds.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'News 4U - Your Personal News Aggregator',
    description: 'Stay informed with News 4U - your intelligent news aggregator that brings together the latest stories from multiple RSS feeds.',
  },
  icons: {
    icon: '/favicon.ico',
    apple: '/favicon.icns',
  },
};

export const viewport = {
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <DarkModeProvider>
          <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
            {children}
          </div>
        </DarkModeProvider>
      </body>
    </html>
  );
} 