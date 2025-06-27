"use client";

import { useState } from "react";
import { PnLChart, WinLossChart, VolumeChart, StrategyChart } from "@/components/Charts";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import type { PnLDataPoint, WinLossDataPoint, VolumeDataPoint, StrategyDataPoint, AnalyticsMetrics } from "@/types";

type TimeFrame = "daily" | "weekly" | "monthly";

export default function AnalyticsPage() {
  const [timeFrame, setTimeFrame] = useState<TimeFrame>("daily");

  // TODO: Replace with real data from API
  const pnlData: PnLDataPoint[] = [];
  const winLossData: WinLossDataPoint[] = [];
  const volumeData: VolumeDataPoint[] = [];
  const strategyData: StrategyDataPoint[] = [];

  // TODO: Replace with real metrics from API
  const metrics: AnalyticsMetrics = {
    totalPnL: {
      value: "+$12,543.87",
      change: "+15.3%",
      isPositive: true,
    },
    winRate: {
      value: "67.8%",
      change: "+2.4%",
      isPositive: true,
    },
    avgWinLoss: {
      value: "2.34",
      change: "+0.12",
      isPositive: true,
    },
    sharpeRatio: {
      value: "1.87",
      change: "-0.05",
      isPositive: false,
    },
    totalTrades: {
      value: "342",
      change: "+28",
      isPositive: true,
    },
    maxDrawdown: {
      value: "-8.2%",
      change: "-1.2%",
      isPositive: false,
    },
  };

  return (
    <main className="min-h-screen py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-light tracking-tight">
            Analytics
          </h1>
          <p className="mt-2 text-muted">
            Track your trading performance and key metrics
          </p>
        </div>

        {/* Time Frame Toggle */}
        <div className="mb-8 flex justify-center">
          <div className="inline-flex  bg-card border border-thin p-1">
            {(["daily", "weekly", "monthly"] as TimeFrame[]).map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeFrame(tf)}
                className={`
                  px-6 py-2  text-sm font-medium transition-colors duration-200
                  ${
                    timeFrame === tf
                      ? "bg-muted text-white"
                      : "text-muted hover:text-white"
                  }
                `}
              >
                {tf.charAt(0).toUpperCase() + tf.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Key Metrics Cards */}
        <div className="mb-8 border border-thin overflow-hidden">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 divide-y md:divide-y-0 md:divide-x lg:divide-x divide-white/10">
          {/* Total P&L Card */}
          <MetricCard
            title="Total P&L"
            value={metrics.totalPnL.value}
            change={metrics.totalPnL.change}
            isPositive={metrics.totalPnL.isPositive}
          />

          {/* Win Rate Card */}
          <MetricCard
            title="Win Rate"
            value={metrics.winRate.value}
            change={metrics.winRate.change}
            isPositive={metrics.winRate.isPositive}
          />

          {/* Average Win/Loss Card */}
          <MetricCard
            title="Avg Win/Loss Ratio"
            value={metrics.avgWinLoss.value}
            change={metrics.avgWinLoss.change}
            isPositive={metrics.avgWinLoss.isPositive}
          />

          {/* Sharpe Ratio Card */}
          <MetricCard
            title="Sharpe Ratio"
            value={metrics.sharpeRatio.value}
            change={metrics.sharpeRatio.change}
            isPositive={metrics.sharpeRatio.isPositive}
          />

          {/* Total Trades Card */}
          <MetricCard
            title="Total Trades"
            value={metrics.totalTrades.value}
            change={metrics.totalTrades.change}
            isPositive={metrics.totalTrades.isPositive}
          />

          {/* Max Drawdown Card */}
          <MetricCard
            title="Max Drawdown"
            value={metrics.maxDrawdown.value}
            change={metrics.maxDrawdown.change}
            isPositive={metrics.maxDrawdown.isPositive}
          />
          </div>
        </div>

        {/* Performance Charts Placeholder */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* P&L Chart Placeholder */}
          <div className="bg-card p-6 border border-thin">
            <h3 className="text-lg font-semibold mb-4">
              P&L Over Time
            </h3>
            <ErrorBoundary
              fallback={
                <div className="h-64 flex items-center justify-center">
                  <div className="text-center">
                    <svg className="w-8 h-8 text-red-400 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-red-400 text-sm">Error loading P&L chart</p>
                  </div>
                </div>
              }
            >
              <div className="h-64">
                <PnLChart data={pnlData} />
              </div>
            </ErrorBoundary>
          </div>

          {/* Win/Loss Distribution Chart Placeholder */}
          <div className="bg-card  p-6 border border-thin">
            <h3 className="text-lg font-semibold mb-4">
              Win/Loss Distribution
            </h3>
            <ErrorBoundary
              fallback={
                <div className="h-64 flex items-center justify-center">
                  <div className="text-center">
                    <svg className="w-8 h-8 text-red-400 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-red-400 text-sm">Error loading Win/Loss chart</p>
                  </div>
                </div>
              }
            >
              <div className="h-64">
                <WinLossChart data={winLossData} />
              </div>
            </ErrorBoundary>
          </div>

          {/* Trade Volume Chart Placeholder */}
          <div className="bg-card  p-6 border border-thin">
            <h3 className="text-lg font-semibold mb-4">
              Trade Volume
            </h3>
            <ErrorBoundary
              fallback={
                <div className="h-64 flex items-center justify-center">
                  <div className="text-center">
                    <svg className="w-8 h-8 text-red-400 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-red-400 text-sm">Error loading Volume chart</p>
                  </div>
                </div>
              }
            >
              <div className="h-64">
                <VolumeChart data={volumeData} />
              </div>
            </ErrorBoundary>
          </div>

          {/* Strategy Performance Chart Placeholder */}
          <div className="bg-card  p-6 border border-thin">
            <h3 className="text-lg font-semibold mb-4">
              Strategy Performance
            </h3>
            <ErrorBoundary
              fallback={
                <div className="h-64 flex items-center justify-center">
                  <div className="text-center">
                    <svg className="w-8 h-8 text-red-400 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-red-400 text-sm">Error loading Strategy chart</p>
                  </div>
                </div>
              }
            >
              <div className="h-64">
                <StrategyChart data={strategyData} />
              </div>
            </ErrorBoundary>
          </div>
        </div>
      </div>
    </main>
  );
}

// Metric Card Component
interface MetricCardProps {
  title: string;
  value: string;
  change: string;
  isPositive: boolean;
}

function MetricCard({ title, value, change, isPositive }: MetricCardProps) {
  return (
    <div className="bg-card p-8">
      <h3 className="text-sm font-medium text-muted">
        {title}
      </h3>
      <div className="mt-2 flex items-baseline justify-between">
        <p className="text-2xl font-semibold">
          {value}
        </p>
        <div
          className={`flex items-center text-sm ${
            isPositive ? "text-green-400" : "text-red-400"
          }`}
        >
          {isPositive ? (
            <svg
              className="h-4 w-4 mr-1"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 15l7-7 7 7"
              />
            </svg>
          ) : (
            <svg
              className="h-4 w-4 mr-1"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          )}
          <span>{change}</span>
        </div>
      </div>
    </div>
  );
}