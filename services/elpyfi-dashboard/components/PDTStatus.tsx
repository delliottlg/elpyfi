import React from 'react';

interface PDTStatusProps {
  tradesUsed: number;
  tradesRemaining: number;
  className?: string;
}

const PDTStatus: React.FC<PDTStatusProps> = ({ 
  tradesUsed, 
  tradesRemaining,
  className = ''
}) => {
  const maxDayTrades = tradesUsed + tradesRemaining;
  const riskPercentage = (tradesUsed / maxDayTrades) * 100;
  
  // Determine risk level and colors
  const getRiskLevel = () => {
    if (riskPercentage >= 100) return { level: 'critical', color: 'red', bg: 'red' };
    if (riskPercentage >= 67) return { level: 'caution', color: 'yellow', bg: 'yellow' };
    return { level: 'safe', color: 'green', bg: 'green' };
  };
  
  const risk = getRiskLevel();
  
  
  // Color classes based on risk level
  const colorClasses = {
    green: {
      text: 'text-green-400',
      bg: 'bg-green-900/20',
      border: 'border-green-800',
      indicator: 'bg-green-500'
    },
    yellow: {
      text: 'text-yellow-400',
      bg: 'bg-yellow-900/20',
      border: 'border-yellow-800',
      indicator: 'bg-yellow-500'
    },
    red: {
      text: 'text-red-400',
      bg: 'bg-red-900/20',
      border: 'border-red-800',
      indicator: 'bg-red-500'
    }
  };
  
  const colors = colorClasses[risk.color];
  
  return (
    <div className={`${className} ${colors.bg} ${colors.border} border rounded-lg p-3 transition-all duration-200`}>
      <div className="flex items-center justify-between gap-3">
        {/* Status Indicator */}
        <div className="flex items-center gap-2">
          <div className="relative">
            <div className={`w-2 h-2 ${colors.indicator} rounded-full`} />
            {risk.level === 'critical' && (
              <div className={`absolute inset-0 w-2 h-2 ${colors.indicator} rounded-full animate-ping`} />
            )}
          </div>
          <span className="text-xs font-medium text-gray-400">PDT Status</span>
        </div>
        
        {/* Trade Count */}
        <div className="flex items-center gap-3">
          <div className="flex flex-col items-end">
            <div className="flex items-baseline gap-1">
              <span className={`text-lg font-bold ${colors.text}`}>{tradesUsed}</span>
              <span className="text-xs text-gray-400">/ {maxDayTrades}</span>
            </div>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {tradesRemaining > 0 ? `${tradesRemaining} left` : 'Limit reached'}
            </span>
          </div>
          
        </div>
      </div>
      
      {/* Progress Bar */}
      <div className="mt-2">
        <div className="h-1 bg-gray-700 rounded-full overflow-hidden">
          <div 
            className={`h-full ${colors.indicator} transition-all duration-300`}
            style={{ width: `${Math.min(riskPercentage, 100)}%` }}
          />
        </div>
      </div>
    </div>
  );
};

export default PDTStatus;