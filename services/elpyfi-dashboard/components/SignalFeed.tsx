'use client';

import React from 'react';
import { Signal } from '@/lib/api';

// Shield Check Icon Component
function ShieldCheckIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  );
}

interface SignalFeedProps {
  signals: Signal[];
  isLoading?: boolean;
  error?: any;
}

export default function SignalFeed({ signals, isLoading, error }: SignalFeedProps) {
  const getSignalIcon = (type: Signal['type']) => {
    switch (type) {
      case 'BUY':
        return (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
          </svg>
        );
      case 'SELL':
        return (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        );
      case 'HOLD':
        return (
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
          </svg>
        );
    }
  };

  const getSignalColorClasses = (type: Signal['type']) => {
    switch (type) {
      case 'BUY':
        return {
          bg: 'bg-green-900/20',
          border: 'border-green-800',
          text: 'text-green-400',
          icon: 'text-green-400',
          badge: 'bg-green-500 text-white'
        };
      case 'SELL':
        return {
          bg: 'bg-red-900/20',
          border: 'border-red-800',
          text: 'text-red-400',
          icon: 'text-red-400',
          badge: 'bg-red-500 text-white'
        };
      case 'HOLD':
        return {
          bg: 'bg-yellow-900/20',
          border: 'border-yellow-800',
          text: 'text-yellow-400',
          icon: 'text-yellow-400',
          badge: 'bg-yellow-500 text-white'
        };
    }
  };

  const getStrengthBadgeColor = (strength: Signal['strength']) => {
    switch (strength) {
      case 'STRONG':
        return 'bg-purple-500 text-white';
      case 'MODERATE':
        return 'bg-blue-500 text-white';
      case 'WEAK':
        return 'bg-gray-500 text-white';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 60) {
      return `${diffInMinutes}m ago`;
    } else if (diffInMinutes < 1440) {
      return `${Math.floor(diffInMinutes / 60)}h ago`;
    } else {
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    }
  };

  const formatNumber = (value: number | undefined) => {
    if (value === undefined) return 'N/A';
    return value.toLocaleString('en-US', { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 2 
    });
  };

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <svg className="w-12 h-12 text-red-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p className="text-red-400 font-medium">Failed to load signals</p>
        <p className="text-gray-400 text-sm mt-1">Please try refreshing the page</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-gray-800 border border-gray-700 rounded-lg p-4 animate-pulse">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gray-700 rounded-full"></div>
                <div>
                  <div className="h-5 bg-gray-700 rounded w-20 mb-2"></div>
                  <div className="h-3 bg-gray-700 rounded w-16"></div>
                </div>
              </div>
              <div className="h-8 bg-gray-700 rounded w-16"></div>
            </div>
            <div className="grid grid-cols-3 gap-4 mb-3">
              <div className="h-16 bg-gray-700 rounded"></div>
              <div className="h-16 bg-gray-700 rounded"></div>
              <div className="h-16 bg-gray-700 rounded"></div>
            </div>
            <div className="h-4 bg-gray-700 rounded w-full"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {signals.map((signal) => {
        const colors = getSignalColorClasses(signal.type);
        
        return (
          <div
            key={signal.id}
            className={`${colors.bg} ${colors.border} border rounded-lg p-4 transition-all hover:shadow-lg`}
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center space-x-3">
                <div className={`${colors.icon} p-2 rounded-full ${colors.bg}`}>
                  {getSignalIcon(signal.type)}
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="text-lg font-semibold text-white">
                      {signal.symbol}
                    </h3>
                    <span className={`${colors.badge} text-xs font-bold px-2 py-1 rounded-full`}>
                      {signal.type}
                    </span>
                    <span className={`${getStrengthBadgeColor(signal.strength)} text-xs font-medium px-2 py-1 rounded-full`}>
                      {signal.strength}
                    </span>
                  </div>
                  <div className="flex items-center mt-1 text-sm text-gray-400">
                    <svg className="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {formatTimestamp(signal.timestamp)}
                  </div>
                </div>
              </div>
              
              {/* Confidence Score */}
              <div className="text-right">
                <div className="flex items-center space-x-1">
                  <ShieldCheckIcon className="w-4 h-4 text-gray-400" />
                  <span className="text-sm font-medium text-gray-300">
                    Confidence
                  </span>
                </div>
                <div className="text-2xl font-bold text-white">
                  {(signal.confidence * 100).toFixed(0)}%
                </div>
              </div>
            </div>

            {/* Price Information */}
            <div className="grid grid-cols-3 gap-4 mb-3">
              <div className="bg-gray-800 rounded p-2">
                <div className="text-xs text-gray-400 mb-1">Current Price</div>
                <div className="text-sm font-semibold text-white">
                  ${formatNumber(signal.price)}
                </div>
              </div>
              <div className="bg-gray-800 rounded p-2">
                <div className="text-xs text-gray-400 mb-1">Target Price</div>
                <div className="text-sm font-semibold text-green-400">
                  ${formatNumber(signal.targetPrice)}
                </div>
              </div>
              <div className="bg-gray-800 rounded p-2">
                <div className="text-xs text-gray-400 mb-1">Stop Loss</div>
                <div className="text-sm font-semibold text-red-400">
                  ${formatNumber(signal.stopLoss)}
                </div>
              </div>
            </div>

            {/* Key Indicators */}
            <div className="mb-3">
              <div className="flex items-center space-x-1 mb-2">
                <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <span className="text-sm font-medium text-gray-300">
                  Key Indicators
                </span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                {signal.indicators.rsi !== undefined && (
                  <div className="bg-white dark:bg-gray-800 rounded px-2 py-1">
                    <span className="text-gray-400">RSI:</span>
                    <span className={`ml-1 font-medium ${
                      signal.indicators.rsi > 70 ? 'text-red-400' : 
                      signal.indicators.rsi < 30 ? 'text-green-400' : 
                      'text-white'
                    }`}>
                      {signal.indicators.rsi}
                    </span>
                  </div>
                )}
                {signal.indicators.macd !== undefined && (
                  <div className="bg-white dark:bg-gray-800 rounded px-2 py-1">
                    <span className="text-gray-400">MACD:</span>
                    <span className={`ml-1 font-medium ${
                      signal.indicators.macd > 0 ? 'text-green-400' : 
                      'text-red-400'
                    }`}>
                      {signal.indicators.macd.toFixed(2)}
                    </span>
                  </div>
                )}
                {signal.indicators.movingAverage !== undefined && (
                  <div className="bg-white dark:bg-gray-800 rounded px-2 py-1">
                    <span className="text-gray-400">MA:</span>
                    <span className="ml-1 font-medium text-white">
                      ${signal.indicators.movingAverage.toFixed(2)}
                    </span>
                  </div>
                )}
                {signal.indicators.volume !== undefined && (
                  <div className="bg-white dark:bg-gray-800 rounded px-2 py-1">
                    <span className="text-gray-400">Vol:</span>
                    <span className="ml-1 font-medium text-white">
                      {(signal.indicators.volume / 1000000).toFixed(2)}M
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Reason */}
            <div className="border-t border-gray-700 pt-3">
              <p className="text-sm text-gray-300">
                <span className="font-medium">Reason:</span> {signal.reason}
              </p>
            </div>
          </div>
        );
      })}
      
      {signals.length === 0 && (
        <div className="text-center py-12">
          <svg className="w-12 h-12 text-gray-600 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <p className="text-gray-400">No signals available</p>
        </div>
      )}
    </div>
  );
}