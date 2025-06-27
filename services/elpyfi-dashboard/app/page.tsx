'use client';

import { useEffect, useState } from 'react';
import useSWR from 'swr';
import { 
  fetchPositions, 
  fetchRecentSignals, 
  fetchPDTStatus,
  connectWebSocket,
  Position,
  Signal,
  PDTStatus 
} from '@/lib/api';
import { ErrorBoundary } from '@/components/ErrorBoundary';

export default function Home() {
  const [wsConnected, setWsConnected] = useState(false);
  
  // Fetch data with SWR
  const { data: positions, error: posError } = useSWR('/positions', fetchPositions, {
    refreshInterval: 5000
  });
  
  const { data: signals, error: sigError } = useSWR('/signals', () => fetchRecentSignals(10), {
    refreshInterval: 3000
  });
  
  const { data: pdtStatus, error: pdtError } = useSWR('/pdt/status', fetchPDTStatus, {
    refreshInterval: 10000
  });

  // WebSocket for real-time updates
  useEffect(() => {
    const ws = connectWebSocket('/ws');
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setWsConnected(true);
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('Real-time update:', data);
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setWsConnected(false);
    };
    
    return () => ws.close();
  }, []);

  const totalPnL = positions?.reduce((sum: number, pos: Position) => sum + (pos.unrealized_pl || 0), 0) || 0;

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-light tracking-tight">
            elPyFi Dashboard
          </h1>
          <div className="flex items-center gap-4">
            <div className={`w-2 h-2 ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-sm text-muted">
              {wsConnected ? 'Live' : 'Disconnected'}
            </span>
          </div>
        </div>
        
        {/* PDT Status Bar */}
        {pdtError && (
          <div className="mb-6 p-4 bg-red-900/20 border border-red-900/50">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-red-400 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-sm text-red-400">Unable to load PDT status</span>
            </div>
          </div>
        )}
        {!pdtStatus && !pdtError && (
          <div className="mb-6 p-4 bg-card border border-thin">
            <div className="flex items-center">
              <div className="animate-pulse bg-gray-700 h-4 w-48 rounded"></div>
            </div>
          </div>
        )}
        {pdtStatus && (
          <div className="mb-6 p-4 bg-card border border-thin">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-muted">
                PDT Status: {pdtStatus.trades_used} trades used
              </span>
              <span className={`text-sm font-bold ${
                pdtStatus.trades_remaining > 1 ? 'text-green-400' : 'text-red-400'
              }`}>
                {pdtStatus.trades_remaining} remaining
              </span>
            </div>
          </div>
        )}
        
        {/* Connected Cards Container */}
        <div className="overflow-hidden border border-thin">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 divide-y md:divide-y-0 md:divide-x lg:divide-x divide-white/10">
            {/* Positions Card */}
            <div className="bg-card p-8">
            <h2 className="text-lg font-medium mb-6 text-muted uppercase tracking-wider text-xs">
              Positions <span className="text-muted font-normal">({positions?.length || 0})</span>
            </h2>
            <ErrorBoundary
              fallback={
                <div className="flex flex-col items-center justify-center py-8">
                  <svg className="w-8 h-8 text-red-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <p className="text-red-400 text-sm">Error loading positions</p>
                  <p className="text-muted text-xs mt-1">Component crashed</p>
                </div>
              }
            >
              <div className="space-y-3 max-h-64 overflow-y-auto">
              {posError && (
                <div className="flex flex-col items-center justify-center py-8">
                  <svg className="w-8 h-8 text-red-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-red-400 text-sm">Failed to load positions</p>
                  <p className="text-muted text-xs mt-1">Please try refreshing</p>
                </div>
              )}
              {!positions && !posError && (
                <div className="flex flex-col items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-400 mb-2"></div>
                  <p className="text-muted text-sm">Loading positions...</p>
                </div>
              )}
              {positions?.length === 0 && !posError && (
                <div className="flex flex-col items-center justify-center py-8">
                  <svg className="w-8 h-8 text-gray-500 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                  </svg>
                  <p className="text-muted text-sm">No positions</p>
                </div>
              )}
              {positions && positions.length > 0 && positions.map((pos: Position) => (
                <div key={pos.symbol} className="flex justify-between items-center">
                  <div>
                    <span className="font-medium">{pos.symbol}</span>
                    <span className="text-sm text-muted ml-2">
                      {pos.quantity}@${pos.entry_price ? pos.entry_price.toFixed(2) : 'N/A'}
                    </span>
                  </div>
                  <span className={`font-medium ${
                    (pos.unrealized_pl || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    ${pos.unrealized_pl ? pos.unrealized_pl.toFixed(2) : '0.00'}
                  </span>
                </div>
              ))}
              </div>
            </ErrorBoundary>
          </div>

            {/* Signals Card */}
            <div className="bg-card p-8">
            <h2 className="text-lg font-medium mb-6 text-muted uppercase tracking-wider text-xs">
              Recent Signals
            </h2>
            <ErrorBoundary
              fallback={
                <div className="flex flex-col items-center justify-center py-8">
                  <svg className="w-8 h-8 text-red-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <p className="text-red-400 text-sm">Error loading signals</p>
                  <p className="text-muted text-xs mt-1">Component crashed</p>
                </div>
              }
            >
              <div className="space-y-3 max-h-64 overflow-y-auto">
              {sigError && (
                <div className="flex flex-col items-center justify-center py-8">
                  <svg className="w-8 h-8 text-red-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-red-400 text-sm">Failed to load signals</p>
                  <p className="text-muted text-xs mt-1">Please try refreshing</p>
                </div>
              )}
              {!signals && !sigError && (
                <div className="flex flex-col items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-400 mb-2"></div>
                  <p className="text-muted text-sm">Loading signals...</p>
                </div>
              )}
              {signals?.length === 0 && !sigError && (
                <div className="flex flex-col items-center justify-center py-8">
                  <svg className="w-8 h-8 text-gray-500 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <p className="text-muted text-sm">No recent signals</p>
                </div>
              )}
              {signals && signals.length > 0 && signals.map((signal: Signal, index: number) => (
                <div key={`${signal.symbol}-${signal.timestamp}-${index}`} className={`p-3 border-l-4 ${
                  signal.action === 'buy' ? 'bg-green-900/10 border-green-500' : 
                  signal.action === 'sell' ? 'bg-red-900/10 border-red-500' : 
                  'bg-yellow-900/10 border-yellow-500'
                }`}>
                  <div className={`font-medium ${
                    signal.action === 'buy' ? 'text-green-400' :
                    signal.action === 'sell' ? 'text-red-400' :
                    'text-yellow-400'
                  }`}>
                    {signal.action.toUpperCase()}: {signal.symbol}
                  </div>
                  <div className="text-sm text-muted">
                    {((signal.confidence || 0) * 100).toFixed(0)}% conf • {signal.strategy}
                  </div>
                </div>
              ))}
              </div>
            </ErrorBoundary>
          </div>

            {/* Performance Card */}
            <div className="bg-card p-8 md:col-span-2 lg:col-span-1">
            <h2 className="text-lg font-medium mb-6 text-muted uppercase tracking-wider text-xs">
              Performance
            </h2>
            <ErrorBoundary
              fallback={
                <div className="flex flex-col items-center justify-center py-8">
                  <svg className="w-8 h-8 text-red-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <p className="text-red-400 text-sm">Error loading performance</p>
                  <p className="text-muted text-xs mt-1">Component crashed</p>
                </div>
              }
            >
              <div className="space-y-4">
              <div>
                <div className="text-sm text-muted">Total P&L</div>
                <div className={`text-2xl font-bold ${
                  totalPnL >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  ${totalPnL.toFixed(2)}
                </div>
              </div>
              <div>
                <div className="text-sm text-muted">Active Positions</div>
                <div className="text-lg font-semibold">
                  {positions?.length || 0}
                </div>
              </div>
              <div>
                <div className="text-sm text-muted">Connection</div>
                <div className="text-lg font-semibold">
                  {wsConnected ? 'Live' : 'Offline'}
                </div>
              </div>
              </div>
            </ErrorBoundary>
          </div>
        </div>
        </div>
      </div>
    </main>
  );
}