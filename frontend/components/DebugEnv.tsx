'use client';

import { useEffect, useState } from 'react';

export default function DebugEnv() {
  const [envVars, setEnvVars] = useState<Record<string, string>>({});

  useEffect(() => {
    // Collect environment variables
    const vars: Record<string, string> = {};
    
    // Check for NEXT_PUBLIC_ variables
    Object.keys(process.env).forEach(key => {
      if (key.startsWith('NEXT_PUBLIC_')) {
        vars[key] = process.env[key] || 'undefined';
      }
    });

    // Add some additional debug info
    vars['NODE_ENV'] = process.env.NODE_ENV || 'undefined';
    vars['API_BASE_URL'] = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    setEnvVars(vars);
  }, []);

  if (process.env.NODE_ENV === 'production') {
    return null; // Don't show in production
  }

  return (
    <div className="fixed bottom-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded z-50 max-w-md">
      <h3 className="font-bold mb-2">🔍 Environment Debug</h3>
      <div className="text-xs space-y-1">
        {Object.entries(envVars).map(([key, value]) => (
          <div key={key}>
            <strong>{key}:</strong> {value}
          </div>
        ))}
      </div>
      <button 
        onClick={() => setEnvVars({})}
        className="mt-2 text-xs bg-red-500 text-white px-2 py-1 rounded"
      >
        Hide
      </button>
    </div>
  );
} 