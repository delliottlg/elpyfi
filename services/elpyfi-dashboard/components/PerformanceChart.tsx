"use client";

import { useEffect, useRef, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { Performance } from "@/lib/api";
import { format } from "date-fns";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface PerformanceChartProps {
  data: Performance[];
  title?: string;
  showBenchmark?: boolean;
  height?: number;
  isLoading?: boolean;
  error?: any;
}

export default function PerformanceChart({
  data,
  title = "Portfolio Performance",
  showBenchmark = true,
  height = 300,
  isLoading,
  error,
}: PerformanceChartProps) {
  // Always use dark mode colors

  if (error) {
    return (
      <div
        className="bg-gray-800 p-6 rounded-lg shadow flex items-center justify-center"
        style={{ height: `${height}px` }}
      >
        <div className="text-center">
          <svg className="w-12 h-12 text-red-400 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-red-400 font-medium">Failed to load chart</p>
          <p className="text-gray-400 text-sm mt-1">Please try refreshing</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div
        className="bg-gray-800 p-6 rounded-lg shadow"
        style={{ height: `${height}px` }}
      >
        <div className="animate-pulse h-full">
          <div className="h-6 bg-gray-700 rounded w-48 mb-4"></div>
          <div className="h-full bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div
        className="bg-gray-800 p-6 rounded-lg shadow flex items-center justify-center"
        style={{ height: `${height}px` }}
      >
        <div className="text-center">
          <svg className="w-12 h-12 text-gray-500 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <p className="text-gray-400">No performance data available</p>
        </div>
      </div>
    );
  }

  const chartData = {
    labels: data.map((d) => format(new Date(d.date), "MMM dd")),
    datasets: [
      {
        label: "Portfolio",
        data: data.map((d) => d.cumulativeReturn * 100),
        borderColor: "rgb(34, 197, 94)",
        backgroundColor: "rgba(34, 197, 94, 0.1)",
        fill: true,
        tension: 0.4,
      },
      ...(showBenchmark
        ? [
            {
              label: "Benchmark",
              data: data.map((d) => d.benchmarkReturn * 100),
              borderColor: "rgb(156, 163, 175)",
              backgroundColor: "rgba(156, 163, 175, 0.1)",
              fill: true,
              tension: 0.4,
            },
          ]
        : []),
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "top" as const,
        labels: {
          color: "#e5e7eb",
          font: {
            size: 12,
          },
        },
      },
      title: {
        display: true,
        text: title,
        color: "#f3f4f6",
        font: {
          size: 16,
          weight: "bold" as const,
        },
      },
      tooltip: {
        backgroundColor: "#374151",
        titleColor: "#f3f4f6",
        bodyColor: "#e5e7eb",
        borderColor: "#4b5563",
        borderWidth: 1,
        callbacks: {
          label: (context: any) => {
            return `${context.dataset.label}: ${context.parsed.y.toFixed(2)}%`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: {
          color: "#374151",
        },
        ticks: {
          color: "#9ca3af",
        },
      },
      y: {
        grid: {
          color: "#374151",
        },
        ticks: {
          color: "#9ca3af",
          callback: function (value: any) {
            return value + "%";
          },
        },
      },
    },
  };

  return (
    <div
      className="bg-gray-800 p-6 rounded-lg shadow"
      style={{ height: `${height}px` }}
    >
      <Line data={chartData} options={options} />
    </div>
  );
}