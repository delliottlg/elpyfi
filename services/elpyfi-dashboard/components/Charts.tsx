"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from "recharts";
import type { 
  PnLDataPoint, 
  WinLossDataPoint, 
  VolumeDataPoint, 
  StrategyDataPoint 
} from "@/types";

// Custom tooltip styling
const customTooltip = {
  contentStyle: {
    backgroundColor: "#1a1a1a",
    border: "1px solid rgba(255, 255, 255, 0.1)",
    borderRadius: "0px",
    padding: "12px",
  },
  labelStyle: {
    color: "#a8a8a8",
    marginBottom: "4px",
  },
  itemStyle: {
    color: "#fafafa",
  },
};

interface PnLChartProps {
  data: PnLDataPoint[];
}

export function PnLChart({ data }: PnLChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-muted">No data available</p>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="colorPnL" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="0" stroke="rgba(255, 255, 255, 0.06)" />
        <XAxis 
          dataKey="date" 
          stroke="#a8a8a8"
          fontSize={12}
          axisLine={{ stroke: "rgba(255, 255, 255, 0.1)" }}
          tickLine={false}
        />
        <YAxis 
          stroke="#a8a8a8"
          fontSize={12}
          axisLine={{ stroke: "rgba(255, 255, 255, 0.1)" }}
          tickLine={false}
          tickFormatter={(value) => `$${value}`}
        />
        <Tooltip {...customTooltip} />
        <Area
          type="monotone"
          dataKey="pnl"
          stroke="#3b82f6"
          strokeWidth={2}
          fillOpacity={1}
          fill="url(#colorPnL)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

interface WinLossChartProps {
  data: WinLossDataPoint[];
}

export function WinLossChart({ data }: WinLossChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-muted">No data available</p>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="0" stroke="rgba(255, 255, 255, 0.06)" />
        <XAxis 
          dataKey="range" 
          stroke="#a8a8a8"
          fontSize={12}
          axisLine={{ stroke: "rgba(255, 255, 255, 0.1)" }}
          tickLine={false}
        />
        <YAxis 
          stroke="#a8a8a8"
          fontSize={12}
          axisLine={{ stroke: "rgba(255, 255, 255, 0.1)" }}
          tickLine={false}
        />
        <Tooltip {...customTooltip} />
        <Bar dataKey="wins" fill="#10b981" />
        <Bar dataKey="losses" fill="#ef4444" />
      </BarChart>
    </ResponsiveContainer>
  );
}

interface VolumeChartProps {
  data: VolumeDataPoint[];
}

export function VolumeChart({ data }: VolumeChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-muted">No data available</p>
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="0" stroke="rgba(255, 255, 255, 0.06)" />
        <XAxis 
          dataKey="date" 
          stroke="#a8a8a8"
          fontSize={12}
          axisLine={{ stroke: "rgba(255, 255, 255, 0.1)" }}
          tickLine={false}
        />
        <YAxis 
          stroke="#a8a8a8"
          fontSize={12}
          axisLine={{ stroke: "rgba(255, 255, 255, 0.1)" }}
          tickLine={false}
        />
        <Tooltip {...customTooltip} />
        <Bar dataKey="volume" fill="#3b82f6" />
      </BarChart>
    </ResponsiveContainer>
  );
}

interface StrategyChartProps {
  data: StrategyDataPoint[];
}

export function StrategyChart({ data }: StrategyChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-muted">No data available</p>
      </div>
    );
  }
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="0" stroke="rgba(255, 255, 255, 0.06)" />
        <XAxis 
          dataKey="name" 
          stroke="#a8a8a8"
          fontSize={12}
          axisLine={{ stroke: "rgba(255, 255, 255, 0.1)" }}
          tickLine={false}
        />
        <YAxis 
          stroke="#a8a8a8"
          fontSize={12}
          axisLine={{ stroke: "rgba(255, 255, 255, 0.1)" }}
          tickLine={false}
          tickFormatter={(value) => `${value}%`}
        />
        <Tooltip {...customTooltip} />
        <Bar dataKey="performance" fill="#3b82f6" />
      </BarChart>
    </ResponsiveContainer>
  );
}