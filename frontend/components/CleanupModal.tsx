'use client';

import { useState, useEffect } from 'react';
import { Trash2, AlertTriangle, X, Loader2 } from 'lucide-react';
import { newsApi } from '@/lib/api';

interface CleanupModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCleanupComplete: () => void;
}

export default function CleanupModal({ isOpen, onClose, onCleanupComplete }: CleanupModalProps) {
  const [feedNames, setFeedNames] = useState<string[]>([]);
  const [selectedFeed, setSelectedFeed] = useState<string>('');
  const [cleanupType, setCleanupType] = useState<'all' | 'feed'>('all');
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingFeeds, setLoadingFeeds] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadFeedNames();
    }
  }, [isOpen]);

  const loadFeedNames = async () => {
    try {
      setLoadingFeeds(true);
      const names = await newsApi.getFeedNames();
      setFeedNames(names);
    } catch (error) {
      console.error('Error loading feed names:', error);
    } finally {
      setLoadingFeeds(false);
    }
  };

  const handleCleanup = async () => {
    try {
      setIsLoading(true);
      
      if (cleanupType === 'all') {
        await newsApi.cleanupAllData();
      } else if (cleanupType === 'feed' && selectedFeed) {
        await newsApi.cleanupFeedData(selectedFeed);
      }
      
      onCleanupComplete();
      onClose();
    } catch (error) {
      console.error('Error during cleanup:', error);
      alert('Failed to cleanup data. Please try again.');
    } finally {
      setIsLoading(false);
      setShowConfirmation(false);
    }
  };

  const getConfirmationMessage = () => {
    if (cleanupType === 'all') {
      return 'Are you sure you want to delete ALL articles, raw feed data, and fetch logs? This action cannot be undone.';
    } else {
      return `Are you sure you want to delete all data for the feed "${selectedFeed}"? This action cannot be undone.`;
    }
  };

  const getCleanupButtonText = () => {
    if (cleanupType === 'all') {
      return 'Delete All Data';
    } else {
      return `Delete ${selectedFeed} Data`;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <Trash2 className="h-6 w-6 text-red-600" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900">Database Cleanup</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {!showConfirmation ? (
            <>
              <div className="mb-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Select cleanup type:</h3>
                
                {/* Cleanup Type Selection */}
                <div className="space-y-3">
                  <label className="flex items-center space-x-3 cursor-pointer">
                    <input
                      type="radio"
                      name="cleanupType"
                      value="all"
                      checked={cleanupType === 'all'}
                      onChange={(e) => setCleanupType(e.target.value as 'all' | 'feed')}
                      className="text-red-600 focus:ring-red-500"
                    />
                    <div>
                      <span className="font-medium text-gray-900">Clean up all data</span>
                      <p className="text-sm text-gray-500">Delete all articles, raw feed data, and fetch logs</p>
                    </div>
                  </label>
                  
                  <label className="flex items-center space-x-3 cursor-pointer">
                    <input
                      type="radio"
                      name="cleanupType"
                      value="feed"
                      checked={cleanupType === 'feed'}
                      onChange={(e) => setCleanupType(e.target.value as 'all' | 'feed')}
                      className="text-red-600 focus:ring-red-500"
                    />
                    <div>
                      <span className="font-medium text-gray-900">Clean up specific feed</span>
                      <p className="text-sm text-gray-500">Delete data for a specific feed only</p>
                    </div>
                  </label>
                </div>
              </div>

              {/* Feed Selection */}
              {cleanupType === 'feed' && (
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Feed:
                  </label>
                  {loadingFeeds ? (
                    <div className="flex items-center space-x-2 text-gray-500">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Loading feeds...</span>
                    </div>
                  ) : (
                    <select
                      value={selectedFeed}
                      onChange={(e) => setSelectedFeed(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
                    >
                      <option value="">Select a feed...</option>
                      {feedNames.map((feedName) => (
                        <option key={feedName} value={feedName}>
                          {feedName}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              )}

              {/* Warning */}
              <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
                <div className="flex items-start space-x-3">
                  <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <h4 className="text-sm font-medium text-red-800">Warning</h4>
                    <p className="text-sm text-red-700 mt-1">
                      This action will permanently delete data from the database. This action cannot be undone.
                    </p>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex space-x-3">
                <button
                  onClick={onClose}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => setShowConfirmation(true)}
                  disabled={cleanupType === 'feed' && !selectedFeed}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Continue
                </button>
              </div>
            </>
          ) : (
            <>
              {/* Confirmation */}
              <div className="mb-6">
                <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
                  <div className="flex items-start space-x-3">
                    <AlertTriangle className="h-6 w-6 text-red-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <h4 className="text-lg font-medium text-red-800">Final Confirmation</h4>
                      <p className="text-red-700 mt-2">{getConfirmationMessage()}</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowConfirmation(false)}
                  disabled={isLoading}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Go Back
                </button>
                <button
                  onClick={handleCleanup}
                  disabled={isLoading}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Cleaning...</span>
                    </>
                  ) : (
                    <span>{getCleanupButtonText()}</span>
                  )}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
} 