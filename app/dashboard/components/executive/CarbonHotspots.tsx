"use client";

import React, { useMemo } from "react";

interface Hotspot {
  activity_name: string;
  emissions: number;
  contribution_percentage: number;
  severity: string;
}

interface CarbonHotspotsProps {
  hotspots: Hotspot[];
  loading: boolean;
}

export function CarbonHotspots({ hotspots, loading }: CarbonHotspotsProps) {
  const sortedHotspots = useMemo(() => {
    if (!hotspots) return [];
    return [...hotspots]
      .sort((a, b) => b.emissions - a.emissions)
      .slice(0, 5);
  }, [hotspots]);

  const getSeverityStyle = (severity: string) => {
    const s = severity.toUpperCase();
    if (s === "CRITICAL" || s === "HIGH") {
      return "text-red-400";
    }
    if (s === "MEDIUM") {
      return "text-amber-400";
    }
    return "text-slate-400";
  };

  return (
    <div className="bg-[#0f172a] text-[#f8fafc] border border-[#e5e7eb]/10 rounded-lg p-5">
      <h2 className="text-sm font-semibold tracking-wider uppercase text-slate-400 mb-4">Carbon Hotspots (Top 5)</h2>
      
      {loading ? (
        <div className="space-y-3">
          <div className="h-8 bg-slate-800 animate-pulse rounded" />
          <div className="h-20 bg-slate-800 animate-pulse rounded" />
        </div>
      ) : !hotspots || hotspots.length === 0 ? (
        <div className="text-center py-8 text-sm text-slate-500 border border-dashed border-[#e5e7eb]/10 rounded-lg">
          No hotspot data available.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-[#e5e7eb]/10 text-slate-400 font-semibold uppercase">
                <th className="pb-3 pr-4 font-medium">Entity</th>
                <th className="pb-3 px-4 font-medium text-right">Emissions (kg CO₂e)</th>
                <th className="pb-3 px-4 font-medium text-right">Share %</th>
                <th className="pb-3 pl-4 font-medium">Risk</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#e5e7eb]/10">
              {sortedHotspots.map((hs, idx) => (
                <tr key={idx} className="hover:bg-slate-800/20">
                  <td className="py-3.5 pr-4 font-semibold text-slate-200">
                    {hs.activity_name}
                  </td>
                  <td className="py-3.5 px-4 font-mono text-right text-slate-300">
                    {hs.emissions.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}
                  </td>
                  <td className="py-3.5 px-4 font-mono text-right text-slate-300">
                    {hs.contribution_percentage.toFixed(1)}%
                  </td>
                  <td className={`py-3.5 pl-4 font-mono font-bold uppercase tracking-wider ${getSeverityStyle(hs.severity)}`}>
                    {hs.severity}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
