// Core data types for the trading dashboard

export interface Position {
  symbol: string;
  quantity: number;
  entry_price: number;
  current_price?: number;
  unrealized_pl?: number;
  realized_pl?: number;
  timestamp: string;
}

export interface Signal {
  symbol: string;
  action: 'buy' | 'sell' | 'hold';
  confidence: number;
  strategy: string;
  timestamp: string;
  price?: number;
  quantity?: number;
}

export interface PDTStatus {
  current_day_trades: number;
  max_day_trades: number;
  trades_remaining: number;
  reset_time: string;
}

// Chart data types
export interface PnLDataPoint {
  date: string;
  pnl: number;
  value?: number;
}

export interface WinLossDataPoint {
  range: string;
  wins: number;
  losses: number;
}

export interface VolumeDataPoint {
  date: string;
  volume: number;
  value?: number;
}

export interface StrategyDataPoint {
  name: string;
  performance: number;
  trades: number;
}

// Analytics data
export interface MetricData {
  value: string | number;
  change: string | number;
  isPositive: boolean;
}

export interface AnalyticsMetrics {
  totalPnL: MetricData;
  winRate: MetricData;
  avgWinLoss: MetricData;
  sharpeRatio: MetricData;
  totalTrades: MetricData;
  maxDrawdown: MetricData;
}

// Strategy data
export interface Strategy {
  id: string | number;
  name: string;
  status: 'active' | 'inactive' | 'paused';
  description: string;
  performance: {
    totalReturn: number;
    monthlyReturn: number;
    sharpeRatio: number;
    maxDrawdown: number;
    winRate: number;
  };
  lastUpdated: string;
}

// WebSocket message types
export interface WSMessage {
  type: 'position_update' | 'signal' | 'pdt_update' | 'performance_update';
  data: Position | Signal | PDTStatus | any;
  timestamp: string;
}