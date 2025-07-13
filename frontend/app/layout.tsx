import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { DarkModeProvider } from '@/lib/darkMode';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'News 4U',
  keywords: ['news', 'RSS', 'aggregator', 'technology', 'finance', 'world news'],
  authors: [{ name: 'Quoc Hung' }],
  description: 'Your personal news agent'
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