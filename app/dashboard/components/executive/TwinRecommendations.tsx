"use client";

import React from "react";
import { Leaf, Award, Compass, ArrowUpRight, Percent, CheckCircle, ShieldAlert } from "lucide-react";

interface StrategyImpact {
  emissions_saved_kg: number;
  emissions_saved_pct: number;
  esg_improvement: number;
  sustainability_conformance_change: number;
  fitness_change: number;
  risk_change: string;
}

interface StrategyOutputs {
  projected_process_fitness: number;
  projected_carbon_fitness: number;
  projected_sustainability_conformance: number;
  projected_esg_score: number;
  projected_emissions_kg: number;
  projected_budget_utilization: number;
  projected_violation_count: number;
  projected_risk_level: string;
}

interface Strategy {
  scenario_name: string;
  projected_outputs: StrategyOutputs;
  confidence: number;
  confidence_band: string;
  impact_analysis: StrategyImpact;
}

interface TwinRecommendationsProps {
  bestCarbon: Strategy | null;
  bestEsg: Strategy | null;
  bestBalanced: Strategy | null;
  loading: boolean;
}

export function TwinRecommendations({
  bestCarbon,
  bestEsg,
  bestBalanced,
  loading
}: TwinRecommendationsProps) {
  
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-64 bg-slate-900 animate-pulse rounded-lg border border-[#e5e7eb]/10 p-5" />
        ))}
      </div>
    );
  }

  const getConfidenceColor = (band: string) => {
    const b = band?.toUpperCase() || "LOW";
    if (b === "HIGH") return "text-emerald-400";
    if (b === "MEDIUM") return "text-amber-400";
    return "text-red-400";
  };

  const getScenarioTitle = (name: string) => {
    return name
      .replace(/_/g, " ")
      .split(" ")
      .map(w => w.charAt(0).toUpperCase() + w.slice(1))
      .join(" ");
  };

  return (
    <div className="space-y-4">
      <h2 className="text-sm font-semibold tracking-wider uppercase text-slate-400">Digital Twin Recommendations</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Best Carbon Strategy */}
        <div className="bg-[#0f172a] text-[#f8fafc] border border-[#e5e7eb]/10 rounded-lg p-5 flex flex-col justify-between h-72">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400 tracking-wider uppercase mb-3">
              <Leaf className="h-4 w-4" />
              <span>Best Carbon Strategy</span>
            </div>
            
            {bestCarbon ? (
              <div className="space-y-4">
                <h3 className="text-base font-bold text-slate-200">{getScenarioTitle(bestCarbon.scenario_name)}</h3>
                <div className="grid grid-cols-2 gap-4 text-xs">
                  <div>
                    <span className="text-slate-400 block mb-1">Projected Reduction</span>
                    <span className="font-mono text-base font-bold flex items-center gap-0.5 text-emerald-400">
                      -{bestCarbon.impact_analysis.emissions_saved_pct}%
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block mb-1">Emissions Saved</span>
                    <span className="font-mono text-base font-bold text-slate-200">
                      {bestCarbon.impact_analysis.emissions_saved_kg.toLocaleString()} kg
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block mb-1">Confidence</span>
                    <span className={`font-mono text-base font-bold ${getConfidenceColor(bestCarbon.confidence_band)}`}>
                      {bestCarbon.confidence}% ({bestCarbon.confidence_band})
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block mb-1">Risk Change</span>
                    <span className="font-mono text-base font-bold text-slate-200 uppercase">
                      {bestCarbon.impact_analysis.risk_change}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-500">Digital Twin analysis has not been generated.</p>
            )}
          </div>
          <div className="text-[10px] text-slate-500 border-t border-[#e5e7eb]/10 pt-2.5">Carbon Optimization focus</div>
        </div>

        {/* Best ESG Strategy */}
        <div className="bg-[#0f172a] text-[#f8fafc] border border-[#e5e7eb]/10 rounded-lg p-5 flex flex-col justify-between h-72">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold text-indigo-400 tracking-wider uppercase mb-3">
              <Award className="h-4 w-4" />
              <span>Best ESG Strategy</span>
            </div>
            
            {bestEsg ? (
              <div className="space-y-4">
                <h3 className="text-base font-bold text-slate-200">{getScenarioTitle(bestEsg.scenario_name)}</h3>
                <div className="grid grid-cols-2 gap-4 text-xs">
                  <div>
                    <span className="text-slate-400 block mb-1">ESG Improvement</span>
                    <span className="font-mono text-base font-bold text-indigo-400 flex items-center gap-0.5">
                      +{bestEsg.impact_analysis.esg_improvement.toFixed(1)}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block mb-1">Conformance Gain</span>
                    <span className="font-mono text-base font-bold text-slate-200">
                      +{ (bestEsg.impact_analysis.sustainability_conformance_change * 100).toFixed(1) }%
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block mb-1">Confidence</span>
                    <span className={`font-mono text-base font-bold ${getConfidenceColor(bestEsg.confidence_band)}`}>
                      {bestEsg.confidence}% ({bestEsg.confidence_band})
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-500">Digital Twin analysis has not been generated.</p>
            )}
          </div>
          <div className="text-[10px] text-slate-500 border-t border-[#e5e7eb]/10 pt-2.5">ESG Governance focus</div>
        </div>

        {/* Best Balanced Strategy */}
        <div className="bg-[#0f172a] text-[#f8fafc] border border-[#e5e7eb]/10 rounded-lg p-5 flex flex-col justify-between h-72">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-300 tracking-wider uppercase mb-3">
              <Compass className="h-4 w-4" />
              <span>Best Balanced Strategy</span>
            </div>
            
            {bestBalanced ? (
              <div className="space-y-4">
                <h3 className="text-base font-bold text-slate-200">{getScenarioTitle(bestBalanced.scenario_name)}</h3>
                <div className="grid grid-cols-2 gap-4 text-xs">
                  <div>
                    <span className="text-slate-400 block mb-1">Conformance Delta</span>
                    <span className="font-mono text-base font-bold text-slate-200">
                      +{(bestBalanced.impact_analysis.sustainability_conformance_change * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block mb-1">Carbon Reduction</span>
                    <span className="font-mono text-base font-bold text-slate-200">
                      -{bestBalanced.impact_analysis.emissions_saved_pct}%
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block mb-1">Risk Reduction</span>
                    <span className="font-mono text-base font-bold text-slate-200 uppercase">
                      {bestBalanced.impact_analysis.risk_change}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-500">Digital Twin analysis has not been generated.</p>
            )}
          </div>
          <div className="text-[10px] text-slate-500 border-t border-[#e5e7eb]/10 pt-2.5">Combined Tradeoff focus</div>
        </div>

      </div>
    </div>
  );
}
