"use client";

import React, { useMemo } from "react";
import { Sparkles, Terminal } from "lucide-react";

interface ExecutiveSummaryProps {
  esgScore: number | null;
  sustainabilityConformance: number | null;
  carbonFitness: number | null;
  processFitness: number | null;
  budgetUtilization: number | null;
  deviations: Array<{ type: string; severity: string }>;
  loading: boolean;
}

export function ExecutiveSummary({
  esgScore,
  sustainabilityConformance,
  carbonFitness,
  processFitness,
  budgetUtilization,
  deviations,
  loading
}: ExecutiveSummaryProps) {
  
  const summaryText = useMemo(() => {
    if (loading) return "Analyzing platform metrics...";
    
    if (sustainabilityConformance === null && carbonFitness === null) {
      return "Sustainability conformance and carbon fitness snapshots have not been calculated yet. Upstream process mining logs must be analyzed to generate executive insights.";
    }

    const fitnessVal = sustainabilityConformance !== null ? sustainabilityConformance : 0;
    const isBelowThreshold = fitnessVal < 0.70;

    let text = isBelowThreshold
      ? `Sustainability performance remains below target thresholds (currently at ${(fitnessVal * 100).toFixed(1)}%). `
      : `Sustainability performance is tracking successfully against target thresholds at ${(fitnessVal * 100).toFixed(1)}%. `;

    const activeRisks = deviations && deviations.length > 0
      ? deviations.map(d => d.type).filter((value, index, self) => self.indexOf(value) === index)
      : [];

    if (activeRisks.length > 0) {
      const riskList = activeRisks.join(" and ").replace(/_/g, " ");
      text += `Primary risk factors originate from active ${riskList}. `;
    } else {
      text += "No critical compliance deviations or process anomalies have been flagged in this period. ";
    }

    if (budgetUtilization !== null) {
      if (budgetUtilization > 100) {
        text += `Carbon budget utilization is currently exceeding thresholds at ${budgetUtilization.toFixed(1)}%, driving non-compliance penalty. `;
      } else if (budgetUtilization > 75) {
        text += `Carbon budget utilization is stable but approaching limits at ${budgetUtilization.toFixed(1)}%. `;
      } else {
        text += `Carbon budget utilization is optimal at ${budgetUtilization.toFixed(1)}%, indicating high emission efficiency. `;
      }
    }

    text += "Implementing supplier swaps and transitioning high-emission logistics channels represent the highest priority correction paths.";
    
    return text;
  }, [sustainabilityConformance, carbonFitness, budgetUtilization, deviations, loading]);

  return (
    <div className="bg-[#0f172a] text-[#f8fafc] border border-[#e5e7eb]/10 rounded-lg p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold tracking-wider uppercase text-slate-400 flex items-center gap-2">
          <Terminal className="h-4 w-4 text-[#4f46e5]" />
          <span>Executive AI Summary</span>
        </h2>
        <div className="flex items-center gap-1.5 text-[9px] font-mono bg-slate-900 border border-[#e5e7eb]/10 px-2 py-0.5 rounded text-slate-400 uppercase tracking-widest">
          <Sparkles className="h-3 w-3 text-indigo-400" />
          <span>Deterministic NLG Engine</span>
        </div>
      </div>
      <p className="text-xs leading-relaxed text-slate-300 font-normal">
        {summaryText}
      </p>
    </div>
  );
}
