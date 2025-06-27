import React from 'react';
import { Position } from '@/lib/api';

interface PositionCardProps {
  position: Position;
}

const PositionCard: React.FC<PositionCardProps> = ({ position }) => {
  const isProfit = position.unrealizedPnL >= 0;
  const pnlColor = isProfit ? 'text-green-400' : 'text-red-400';
  const bgHoverColor = isProfit ? 'hover:bg-green-950/20' : 'hover:bg-red-950/20';
  
  // Format currency values
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  // Format percentage values
  const formatPercentage = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  return (
    <div className={`
      bg-gray-800 
      border border-gray-700 
      rounded-lg p-6 
      shadow-sm hover:shadow-md 
      transition-all duration-200 ease-in-out
      ${bgHoverColor}
      cursor-pointer
      transform hover:scale-[1.02]
    `}>
      {/* Header Section */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            {position.symbol}
            {/* Trend Indicator */}
            <span className={`inline-flex items-center ${pnlColor}`}>
              {isProfit ? (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11l5-5m0 0l5 5m-5-5v12" />
                </svg>
              ) : (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 13l-5 5m0 0l-5-5m5 5V6" />
                </svg>
              )}
            </span>
          </h3>
          <p className="text-sm text-gray-400">{position.name}</p>
        </div>
        <div className="text-right">
          <div className={`text-lg font-bold ${pnlColor}`}>
            {formatPercentage(position.unrealizedPnLPercent)}
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Quantity</p>
          <p className="text-base font-medium text-white">{position.quantity.toLocaleString()}</p>
        </div>
        <div>
          <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Current Price</p>
          <p className="text-base font-medium text-white">{formatCurrency(position.currentPrice)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Avg Cost</p>
          <p className="text-base font-medium text-white">{formatCurrency(position.avgPrice)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Market Value</p>
          <p className="text-base font-medium text-white">{formatCurrency(position.marketValue)}</p>
        </div>
      </div>

      {/* P&L Section */}
      <div className="border-t border-gray-700 pt-4">
        <div className="flex justify-between items-center">
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Unrealized P&L</p>
            <p className={`text-lg font-bold ${pnlColor}`}>
              {formatCurrency(position.unrealizedPnL)}
            </p>
          </div>
          {position.realizedPnL !== 0 && (
            <div className="text-right">
              <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">Realized P&L</p>
              <p className="text-sm font-medium text-gray-300">
                {formatCurrency(position.realizedPnL)}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Footer with date info */}
      <div className="mt-4 pt-4 border-t border-gray-700/50">
        <div className="flex justify-between text-xs text-gray-500">
          <span>Opened: {new Date(position.openDate).toLocaleDateString()}</span>
          <span>Updated: {new Date(position.lastUpdated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        </div>
      </div>
    </div>
  );
};

export default PositionCard;