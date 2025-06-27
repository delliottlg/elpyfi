'use client'

import React from 'react'
import useSWR from 'swr'
import { fetchStrategies } from '@/lib/api'

export default function StrategiesPage() {
  const { data: strategies, error } = useSWR('/strategies', fetchStrategies, {
    refreshInterval: 5000
  });

  const displayStrategies = strategies || [];

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-7xl mx-auto">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-light tracking-tight mb-2">
            Trading Strategies
          </h1>
          <p className="text-muted">
            Monitor and manage your trading strategies
          </p>
        </div>

        {/* Strategies Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {error && (
            <div className="col-span-full text-center py-12">
              <svg className="w-12 h-12 text-red-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p className="text-red-400 font-medium">Failed to load strategies</p>
              <p className="text-gray-400 text-sm mt-1">Please try refreshing the page</p>
            </div>
          )}
          
          {!strategies && !error && (
            <div className="col-span-full">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="bg-card border border-thin p-6 animate-pulse">
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex-1">
                        <div className="h-6 bg-gray-700 rounded w-3/4 mb-2"></div>
                        <div className="h-4 bg-gray-700 rounded w-full"></div>
                      </div>
                      <div className="h-6 bg-gray-700 rounded w-16 ml-4"></div>
                    </div>
                    <div className="space-y-3">
                      {[1, 2, 3, 4, 5].map((j) => (
                        <div key={j} className="flex justify-between">
                          <div className="h-4 bg-gray-700 rounded w-24"></div>
                          <div className="h-4 bg-gray-700 rounded w-16"></div>
                        </div>
                      ))}
                    </div>
                    <div className="mt-4 pt-4 border-t border-thin">
                      <div className="h-3 bg-gray-700 rounded w-32"></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {strategies && strategies.length === 0 && !error && (
            <div className="col-span-full text-center py-12">
              <svg className="w-12 h-12 text-gray-500 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="text-gray-400">No strategies available</p>
            </div>
          )}

          {strategies && strategies.length > 0 && strategies.map((strategy: any) => (
            <div
              key={strategy.strategy}
              className="bg-card border border-thin p-6 hover:bg-muted transition-colors"
            >
              {/* Strategy Header */}
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h2 className="text-xl font-semibold mb-1">
                    {strategy.strategy}
                  </h2>
                  <p className="text-sm text-muted">
                    {strategy.position_count} open positions
                  </p>
                </div>
                <span className="px-3 py-1 text-xs font-medium bg-green-900/20 text-green-400 border border-green-900/50">
                  active
                </span>
              </div>

              {/* Strategy Info */}
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted">
                    Strategy Name
                  </span>
                  <span className="text-sm font-medium">
                    {strategy.strategy}
                  </span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted">
                    Active Positions
                  </span>
                  <span className="text-sm font-medium">
                    {strategy.position_count}
                  </span>
                </div>

                <div className="text-center mt-4 pt-4 border-t border-thin">
                  <p className="text-xs text-muted">
                    Performance metrics coming soon
                  </p>
                </div>
              </div>

            </div>
          ))}
        </div>
      </div>
    </div>
  );
}