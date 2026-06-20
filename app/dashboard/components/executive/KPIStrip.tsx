"use client";

import React from "react";
import { Shield, Target, Leaf, Cpu, BarChart2 } from "lucide-react";

interface KPIStripProps {
  esgScore: number | null;
  sustainabilityConformance: number | null;
  carbonFitness: number | null;
  processFitness: number | null;
  budgetUtilization: number | null;
  loading: boolean;
}

export function KPIStrip({
  esgScore,
  sustainabilityConformance,
  carbonFitness,
  processFitness,
  budgetUtilization,
  loading
}: KPIStripProps) {
  
  const formatVal = (val: number | null, isPercentage: boolean = false, multiplier: number = 1) => {
    if (val === null || val === undefined) {
      return "—";
    }
    const finalVal = val * multiplier;
    return isPercentage ? `${finalVal.toFixed(1)}%` : finalVal.toFixed(2);
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
      {/* ESG Score */}
      <div className="bg-[#0f172a] text-[#f8fafc] border border-[#e5e7eb]/10 p-5 rounded-lg flex flex-col justify-between h-32">
        <div className="flex items-center justify-between text-xs text-slate-400 font-medium tracking-wider uppercase">
          <span>ESG Score</span>
          <Target className="h-4 w-4 text-[#4f46e5]" />
        </div>
        <div className="mt-2">
          {loading ? (
            <div className="h-8 w-24 bg-slate-800 animate-pulse rounded" />
          ) : esgScore === null ? (
            <span className="text-sm text-slate-400">ESG score not generated.</span>
          ) : (
            <span className="text-3xl font-mono font-bold">{formatVal(esgScore, false, 100)}</span>
          )}
        </div>
        <div className="text-[10px] text-slate-500">Workspace Overall</div>
      </div>

      {/* Sustainability Conformance */}
      <div className="bg-[#0f172a] text-[#f8fafc] border border-[#e5e7eb]/10 p-5 rounded-lg flex flex-col justify-between h-32">
        <div className="flex items-center justify-between text-xs text-slate-400 font-medium tracking-wider uppercase">
          <span>Sustainability Conformance</span>
          <Shield className="h-4 w-4 text-[#4f46e5]" />
        </div>
        <div className="mt-2">
          {loading ? (
            <div className="h-8 w-24 bg-slate-800 animate-pulse rounded" />
          ) : sustainabilityConformance === null ? (
            <span className="text-sm text-slate-400">Conformance analysis not generated.</span>
          ) : (
            <span className="text-3xl font-mono font-bold">{formatVal(sustainabilityConformance, true, 100)}</span>
          )}
        </div>
        <div className="text-[10px] text-slate-500">Model Alignment</div>
      </div>

      {/* Carbon Fitness */}
      <div className="bg-[#0f172a] text-[#f8fafc] border border-[#e5e7eb]/10 p-5 rounded-lg flex flex-col justify-between h-32">
        <div className="flex items-center justify-between text-xs text-slate-400 font-medium tracking-wider uppercase">
          <span>Carbon Fitness</span>
          <Leaf className="h-4 w-4 text-[#4f46e5]" />
        </div>
        <div className="mt-2">
          {loading ? (
            <div className="h-8 w-24 bg-slate-800 animate-pulse rounded" />
          ) : carbonFitness === null ? (
            <span className="text-sm text-slate-400">Carbon Fitness analysis has not been generated.</span>
          ) : (
            <span className="text-3xl font-mono font-bold">{formatVal(carbonFitness, true, 100)}</span>
          )}
        </div>
        <div className="text-[10px] text-slate-500">GHG Conformance</div>
      </div>

      {/* Process Fitness */}
      <div className="bg-[#0f172a] text-[#f8fafc] border border-[#e5e7eb]/10 p-5 rounded-lg flex flex-col justify-between h-32">
        <div className="flex items-center justify-between text-xs text-slate-400 font-medium tracking-wider uppercase">
          <span>Process Fitness</span>
          <Cpu className="h-4 w-4 text-[#4f46e5]" />
        </div>
        <div className="mt-2">
          {loading ? (
            <div className="h-8 w-24 bg-slate-800 animate-pulse rounded" />
          ) : processFitness === null ? (
            <span className="text-sm text-slate-400">Process fitness analysis not generated.</span>
          ) : (
            <span className="text-3xl font-mono font-bold">{formatVal(processFitness, true, 100)}</span>
          )}
        </div>
        <div className="text-[10px] text-slate-500">Average Path Match</div>
      </div>

      {/* Carbon Budget Utilization */}
      <div className="bg-[#0f172a] text-[#f8fafc] border border-[#e5e7eb]/10 p-5 rounded-lg flex flex-col justify-between h-32">
        <div className="flex items-center justify-between text-xs text-slate-400 font-medium tracking-wider uppercase">
          <span>Carbon Budget Utilization</span>
          <BarChart2 className="h-4 w-4 text-[#4f46e5]" />
        </div>
        <div className="mt-2">
          {loading ? (
            <div className="h-8 w-24 bg-slate-800 animate-pulse rounded" />
          ) : budgetUtilization === null ? (
            <span className="text-sm text-slate-400">Carbon Budget not defined.</span>
          ) : (
            <span className="text-3xl font-mono font-bold">{budgetUtilization.toFixed(1)}%</span>
          )}
        </div>
        <div className="text-[10px] text-slate-500">Of target limit</div>
      </div>
    </div>
  );
}
