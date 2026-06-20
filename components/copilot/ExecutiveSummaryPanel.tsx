"use client";

import React, { useMemo } from "react";
import { 
  FileText, 
  TrendingDown, 
  AlertTriangle, 
  CheckCircle, 
  Award,
  Zap,
  Globe
} from "lucide-react";
import { formatMetric, formatValue } from "../../services/format";

interface ExecutiveSummaryPanelProps {
  conformanceData: any;
  carbonData: any;
  summaryMetrics: any;
  variants: any[];
  bottlenecks: any[];
  deviations: any[];
  recommendations: any[];
  esgScore: any;
}

export const ExecutiveSummaryPanel: React.FC<ExecutiveSummaryPanelProps> = ({
  conformanceData,
  carbonData,
  summaryMetrics,
  variants,
  bottlenecks,
  deviations,
  recommendations,
  esgScore
}) => {
  
  // Calculate maximum values and hotspots safely
  const largestHotspot = useMemo(() => {
    if (!carbonData?.activity_emissions || carbonData.activity_emissions.length === 0) return null;
    const sorted = [...carbonData.activity_emissions].sort((a: any, b: any) => b.emissions - a.emissions);
    return sorted[0];
  }, [carbonData]);

  const largestBottleneck = useMemo(() => {
    if (!bottlenecks || bottlenecks.length === 0) return null;
    const sorted = [...bottlenecks].sort((a: any, b: any) => b.average_wait_time - a.average_wait_time);
    return sorted[0];
  }, [bottlenecks]);

  const keyDeviation = useMemo(() => {
    if (!deviations || deviations.length === 0) return null;
    // Group by deviation type
    const counts: Record<string, number> = {};
    deviations.forEach((d: any) => {
      const type = d.deviation_type || "Undefined Drift";
      counts[type] = (counts[type] || 0) + 1;
    });
    const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    return sorted[0]?.[0] || null;
  }, [deviations]);

  const potentialReduction = useMemo(() => {
    // If no real scenario simulation estimate exists, return "Reduction estimate unavailable."
    return "Reduction estimate unavailable.";
  }, []);

  const primaryRiskArea = useMemo(() => {
    if (conformanceData?.fitness_score !== undefined && conformanceData.fitness_score < 0.85) {
      return "Process Compliance Deviations";
    }
    if (largestBottleneck && Number(largestBottleneck.average_wait_time) > 24) {
      return "Procurement Delays";
    }
    if (carbonData && Number(carbonData.actual_emissions) > Number(carbonData.carbon_budget)) {
      return "Carbon Budget Excess";
    }
    if (esgScore === undefined || esgScore === null || Number(esgScore) === 0) {
      return "Sustainability Reporting Gaps";
    }
    return "None Identified";
  }, [conformanceData, largestBottleneck, carbonData, esgScore]);

  return (
    <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden flex flex-col h-full bg-gradient-to-b from-white to-slate-50/20">
      
      {/* Report Header */}
      <div className="bg-slate-900 px-6 py-5 text-white flex justify-between items-center border-b border-slate-800">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-emerald-600 flex items-center justify-center text-white font-extrabold shadow-md">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-extrabold text-sm tracking-tight">Executive Summary Report Card</h3>
            <p className="text-[10px] text-slate-400 uppercase tracking-widest font-semibold">Post-Analysis Compliance & Carbon Scorecard</p>
          </div>
        </div>
        <span className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded px-2 py-0.5 font-bold uppercase">
          Audit-Ready
        </span>
      </div>

      {/* Report Body */}
      <div className="p-6 flex-1 space-y-6">
        
        {/* Top-line Scores Grid */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-slate-50 border border-slate-100 p-3.5 rounded-lg text-center">
            <div className="flex justify-center text-slate-400 mb-1">
              <CheckCircle className="w-4 h-4 text-emerald-600" />
            </div>
            <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider block">Compliance</span>
            <div className="text-lg font-black text-slate-800 mt-0.5">
              {formatMetric(conformanceData?.fitness_score, "percent")}
            </div>
          </div>
          <div className="bg-slate-50 border border-slate-100 p-3.5 rounded-lg text-center">
            <div className="flex justify-center text-slate-400 mb-1">
              <Award className="w-4 h-4 text-blue-600" />
            </div>
            <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider block">Carbon Fitness</span>
            <div className="text-lg font-black text-slate-800 mt-0.5">
              {formatMetric(carbonData?.carbon_fitness_score, "percent")}
            </div>
          </div>
          <div className="bg-slate-50 border border-slate-100 p-3.5 rounded-lg text-center">
            <div className="flex justify-center text-slate-400 mb-1">
              <Globe className="w-4 h-4 text-purple-600" />
            </div>
            <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wider block">ESG Score</span>
            <div className="text-lg font-black text-slate-800 mt-0.5">
              {formatMetric(esgScore, "percent")}
            </div>
          </div>
        </div>

        {/* Process High-Impact Findings */}
        <div className="space-y-3 pt-2">
          <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Key Inefficiencies & Hotspots</h4>
          
          <div className="space-y-2.5">
            <div className="flex items-start justify-between border-b border-slate-100 pb-2">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />
                <span className="text-xs font-semibold text-slate-700">Largest Bottleneck</span>
              </div>
              <span className="text-xs font-bold text-slate-900 text-right">
                {largestBottleneck 
                  ? `${formatValue(largestBottleneck.activity_name || largestBottleneck.activity)} (${formatValue(Number(largestBottleneck.average_wait_time).toFixed(1))} hrs)` 
                  : "None Detected"}
              </span>
            </div>

            <div className="flex items-start justify-between border-b border-slate-100 pb-2">
              <div className="flex items-center space-x-2">
                <TrendingDown className="w-4 h-4 text-red-500 shrink-0" />
                <span className="text-xs font-semibold text-slate-700">Largest Carbon Hotspot</span>
              </div>
              <span className="text-xs font-bold text-slate-900 text-right">
                {largestHotspot 
                  ? `${formatValue(largestHotspot.activity_name)} (${formatValue(Number(largestHotspot.emissions).toFixed(1))} kg)` 
                  : "None Detected"}
              </span>
            </div>

            <div className="flex items-start justify-between border-b border-slate-100 pb-2">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-purple-500 shrink-0" />
                <span className="text-xs font-semibold text-slate-700">Primary Deviation Drift</span>
              </div>
              <span className="text-xs font-bold text-slate-900 text-right truncate max-w-[200px]" title={formatValue(keyDeviation, "")}>
                {formatValue(keyDeviation, "No Deviations Found")}
              </span>
            </div>

            <div className="flex items-start justify-between border-b border-slate-100 pb-2">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0" />
                <span className="text-xs font-semibold text-slate-700">Primary Risk Area</span>
              </div>
              <span className="text-xs font-bold text-red-650 text-right">
                {primaryRiskArea}
              </span>
            </div>

            <div className="flex items-start justify-between border-b border-slate-100 pb-2">
              <div className="flex items-center space-x-2">
                <Zap className="w-4 h-4 text-emerald-500 shrink-0" />
                <span className="text-xs font-semibold text-slate-700">Estimated Reduction Potential</span>
              </div>
              <span className="text-xs font-black text-emerald-600 text-right">
                {potentialReduction}
              </span>
            </div>
          </div>
        </div>

        {/* Executive Narrative */}
        <div className="bg-emerald-950/[0.03] border border-emerald-900/10 p-3.5 rounded-lg space-y-1">
          <h4 className="text-[9px] font-extrabold text-emerald-800 uppercase tracking-wider">Executive Narrative Summary</h4>
          <p className="text-[10.5px] text-slate-600 leading-relaxed font-semibold">
            This workspace process has a compliance conformance rating of{" "}
            <strong className="text-slate-900">
              {formatMetric(conformanceData?.fitness_score, "percent")}
            </strong>{" "}
            and carbon fitness of{" "}
            <strong className="text-slate-900">
              {formatMetric(carbonData?.carbon_fitness_score, "percent")}
            </strong>.{" "}
            The primary bottleneck delaying cycle times is{" "}
            <strong className="text-slate-900">
              {largestBottleneck
                ? formatValue(largestBottleneck.activity_name || largestBottleneck.activity)
                : "Not Available"}
            </strong>.{" "}
            Supply chain attribution identifies{" "}
            <strong className="text-slate-900">
              {largestHotspot ? formatValue(largestHotspot.activity_name) : "Not Available"}
            </strong>{" "}
            as the largest carbon hotspot. The primary risk area identified is{" "}
            <strong className="text-red-700">{primaryRiskArea}</strong>.{" "}
            Resolving the key deviation drift{" "}
            <strong className="text-slate-900">
              "{formatValue(keyDeviation, "None Detected")}"
            </strong>{" "}
            presents a potential carbon footprint reduction of{" "}
            <strong className="text-emerald-700">{potentialReduction}</strong>.
          </p>
        </div>

        {/* AI Recommendations Summary */}
        <div className="bg-slate-50 border border-slate-100/60 p-4 rounded-lg space-y-2">
          <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Top Recommendation Action</h4>
          {recommendations && recommendations.length > 0 ? (
            <div className="space-y-1">
              <div className="text-xs font-bold text-slate-800">{recommendations[0].title}</div>
              <p className="text-[10px] text-slate-500 leading-relaxed mt-0.5">{recommendations[0].description}</p>
            </div>
          ) : (
            <p className="text-[10px] text-slate-400 italic">No recommendations calculated. Select or refresh analysis to generate AI mitigations.</p>
          )}
        </div>

      </div>

      {/* Report Footer */}
      <div className="bg-slate-50 border-t border-slate-200/60 px-6 py-4 flex justify-between items-center text-[10px] text-slate-400 font-semibold uppercase">
        <span>Total Process Cases: {formatMetric(summaryMetrics?.total_cases || summaryMetrics?.summary_metrics?.total_cases, "number")}</span>
        <span>Version: {summaryMetrics?.analysis_version ? `v${summaryMetrics.analysis_version}` : "—"}</span>
      </div>

    </div>
  );
};
