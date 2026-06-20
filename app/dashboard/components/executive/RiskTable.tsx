"use client";

import React from "react";

interface Deviation {
  type: string;
  severity: string;
  impact_score: number;
  recommended_action: string;
  description?: string;
}

interface RiskTableProps {
  deviations: Deviation[];
  loading: boolean;
}

export function RiskTable({ deviations, loading }: RiskTableProps) {
  const getSeverityStyle = (severity: string) => {
    const s = severity.toUpperCase();
    if (s === "CRITICAL" || s === "HIGH") {
      return "text-[#f8fafc] bg-red-950/60 border border-red-800/40";
    }
    if (s === "MEDIUM") {
      return "text-[#f8fafc] bg-amber-950/60 border border-amber-800/40";
    }
    return "text-[#f8fafc] bg-slate-800/60 border border-slate-700/40";
  };

  return (
    <div className="bg-[#0f172a] text-[#f8fafc] border border-[#e5e7eb]/10 rounded-lg p-5">
      <h2 className="text-sm font-semibold tracking-wider uppercase text-slate-400 mb-4">Executive Risk Register</h2>
      
      {loading ? (
        <div className="space-y-3">
          <div className="h-8 bg-slate-800 animate-pulse rounded" />
          <div className="h-20 bg-slate-800 animate-pulse rounded" />
        </div>
      ) : !deviations || deviations.length === 0 ? (
        <div className="text-center py-8 text-sm text-slate-500 border border-dashed border-[#e5e7eb]/10 rounded-lg">
          No active process or carbon deviations detected. Risk levels within acceptable bounds.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-[#e5e7eb]/10 text-slate-400 font-semibold uppercase">
                <th className="pb-3 pr-4 font-medium">Risk</th>
                <th className="pb-3 px-4 font-medium">Severity</th>
                <th className="pb-3 px-4 font-medium text-right">Impact</th>
                <th className="pb-3 pl-4 font-medium">Recommended Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#e5e7eb]/10">
              {deviations.map((dev, idx) => (
                <tr key={idx} className="hover:bg-slate-800/20">
                  <td className="py-3.5 pr-4 font-mono font-bold text-slate-200">
                    <div>{dev.type}</div>
                    {dev.description && (
                      <div className="text-[10px] font-sans font-normal text-slate-500 mt-0.5">{dev.description}</div>
                    )}
                  </td>
                  <td className="py-3.5 px-4">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase tracking-wider ${getSeverityStyle(dev.severity)}`}>
                      {dev.severity}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 font-mono text-right text-slate-300">
                    {dev.impact_score.toFixed(1)}
                  </td>
                  <td className="py-3.5 pl-4 text-slate-300 font-normal">
                    {dev.recommended_action}
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
