const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9002';

export interface Position {
  symbol: string;
  quantity: number;
  entry_price: number;
  current_price: number;
  unrealized_pl: number;
  strategy: string;
}

export interface Signal {
  strategy: string;
  symbol: string;
  action: 'buy' | 'sell' | 'hold';
  confidence: number;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface PDTStatus {
  trades_used: number;
  trades_remaining: number;
}

export interface Strategy {
  name: string;
  active: boolean;
  performance: {
    total_return: number;
    win_rate: number;
    sharpe_ratio: number;
    max_drawdown: number;
  };
}

// Fetcher for SWR
export const fetcher = (url: string) => 
  fetch(`${API_BASE}${url}`).then(res => res.json());

// API functions
export const fetchPositions = () => fetcher('/positions');
export const fetchRecentSignals = (limit = 50) => fetcher(`/signals/recent?limit=${limit}`);
export const fetchPDTStatus = () => fetcher('/pdt/status');
export const fetchStrategies = () => fetcher('/strategies');
export const fetchMetrics = (strategy: string) => fetcher(`/metrics/${strategy}`);

// WebSocket connection
export const connectWebSocket = (endpoint = '/ws') => {
  const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:9002'}${endpoint}`;
  return new WebSocket(wsUrl);
};