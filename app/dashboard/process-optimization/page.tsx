"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "../../../context/AuthContext";
import { useCopilot } from "../../../context/CopilotContext";
import { api } from "../../../services/api";
import { Card } from "../../../components/Card";
import { Button } from "../../../components/Button";
import {
  Sparkles,
  TrendingUp,
  AlertTriangle,
  Layers,
  ArrowRight,
  RefreshCw,
  Clock,
  Info,
  CheckCircle,
  Database,
  Award
} from "lucide-react";

interface Hop {
  hop_index: number;
  activity_replaced: string;
  action_applied: string;
  reasoning: string;
  source_reroute_id: string;
  source_reroute_version: number;
}

interface OptimizationPlan {
  plan_id: string;
  strategy_name: string;
  strategy_rank: number;
  strategy_score: number;
  optimization_confidence: number;
  total_carbon_savings_kg: number;
  projected_final_fitness: number;
  ocel_ready: boolean;
  source_object_ids: string[];
  source_event_ids: string[];
  hops: Hop[];
  snapshot_hash: string;
  snapshot_timestamp: string;
  optimization_version: number;
  optimization_run_id: string;
}

interface OptimizationSummary {
  total_strategies: number;
  total_carbon_savings: number;
  best_savings: number;
  average_confidence: number;
  average_projected_fitness: number;
}

interface SnapshotHistory {
  optimization_version: number;
  optimization_run_id: string;
  generated_at: string;
  total_savings: number;
  best_strategy_name: string;
  best_strategy_score: number;
}

export default function ProcessOptimizationPage() {
  const { token } = useAuth();
  const { selectedAnalysisId } = useCopilot();

  const [plans, setPlans] = useState<OptimizationPlan[]>([]);
  const [summary, setSummary] = useState<OptimizationSummary | null>(null);
  const [history, setHistory] = useState<SnapshotHistory[]>([]);
  
  const [activeTab, setActiveTab] = useState<string>("balanced");
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [loadedVersion, setLoadedVersion] = useState<number | null>(null);

  const fetchData = useCallback(async (analysisId: string, customVersion?: number) => {
    setLoading(true);
    setError(null);
    try {
      const url = customVersion 
        ? `/api/v1/optimization/${analysisId}/version/${customVersion}`
        : `/api/v1/optimization/${analysisId}`;
        
      const [resPlans, resSummary, resHistory] = await Promise.all([
        api.get(url),
        api.get(`/api/v1/optimization/${analysisId}/summary`),
        api.get(`/api/v1/optimization/${analysisId}/history`),
      ]);

      const plansData = Array.isArray(resPlans.data) ? resPlans.data : [];
      setPlans(plansData);
      setSummary(resSummary.data);
      setHistory(Array.isArray(resHistory.data) ? resHistory.data : []);
      
      if (plansData.length > 0) {
        setLoadedVersion(plansData[0].optimization_version);
      }
    } catch (err: any) {
      console.error("Error fetching process optimization data:", err);
      setError(err?.response?.data?.detail || "Failed to load optimization plans.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedAnalysisId) {
      fetchData(selectedAnalysisId);
    } else {
      setPlans([]);
      setSummary(null);
      setHistory([]);
      setLoadedVersion(null);
    }
  }, [selectedAnalysisId, fetchData]);

  const generatePlans = async () => {
    if (!selectedAnalysisId) return;
    setGenerating(true);
    setError(null);
    try {
      await api.post(`/api/v1/optimization/${selectedAnalysisId}/generate`);
      await fetchData(selectedAnalysisId);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Failed to generate optimization plans.");
    } finally {
      setGenerating(false);
    }
  };

  const loadVersion = (version: number) => {
    if (selectedAnalysisId) {
      fetchData(selectedAnalysisId, version);
    }
  };

  const getActivePlan = (): OptimizationPlan | undefined => {
    return plans.find(p => p.strategy_name === activeTab);
  };

  if (!token) return null;

  const activePlan = getActivePlan();

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            <span className="w-9 h-9 bg-blue-100 rounded-xl flex items-center justify-center text-blue-700">
              <Sparkles className="w-5 h-5" />
            </span>
            Process Optimization Engine
          </h1>
          <p className="text-slate-500 font-medium mt-1">
            Simulate and rank alternative workflows using multi-hop process path configurations.
          </p>
        </div>
        {selectedAnalysisId && (
          <Button
            variant="primary"
            onClick={generatePlans}
            disabled={generating || loading}
            className="flex items-center gap-2 font-bold"
          >
            {generating ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Optimizing Workflow...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4" />
                Generate Optimization Plan
              </>
            )}
          </Button>
        )}
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2 text-sm">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {!selectedAnalysisId ? (
        <Card className="p-8 text-center bg-slate-50 border-dashed border-slate-200">
          <div className="max-w-md mx-auto space-y-3">
            <div className="w-12 h-12 bg-slate-100 text-slate-400 rounded-full flex items-center justify-center mx-auto">
              <Layers className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-800">No Analysis Active</h3>
            <p className="text-slate-500 text-sm">
              Please select a process analysis in the Copilot Sidebar to generate optimization scenarios.
            </p>
          </div>
        </Card>
      ) : loading && plans.length === 0 ? (
        <div className="py-12 flex flex-col items-center justify-center space-y-2 text-slate-500">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
          <p className="font-semibold text-sm">Loading process optimization configurations...</p>
        </div>
      ) : plans.length === 0 ? (
        <Card className="p-8 text-center bg-slate-50 border-dashed border-slate-200">
          <div className="max-w-md mx-auto space-y-3">
            <div className="w-12 h-12 bg-blue-50 text-blue-500 rounded-full flex items-center justify-center mx-auto">
              <Sparkles className="w-6 h-6 animate-pulse" />
            </div>
            <h3 className="text-lg font-bold text-slate-800 font-black">Process Optimization Available</h3>
            <p className="text-slate-500 text-sm">
              SustainOCPM can evaluate 3 multi-hop strategies based on your active process constraints and green rerouting options.
            </p>
            <Button variant="primary" onClick={generatePlans} disabled={generating} className="mt-2 font-bold">
              Run Process Optimization Engine
            </Button>
          </div>
        </Card>
      ) : (
        <>
          {/* KPI Dashboard */}
          {summary && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider font-bold">Cumulative Reduction</p>
                  <h3 className="text-2xl font-black text-slate-900 mt-1">
                    {summary.total_carbon_savings.toLocaleString()} kg
                  </h3>
                  <span className="text-[10px] text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded font-semibold mt-1 inline-block">
                    Emission Cap Approved
                  </span>
                </div>
                <div className="w-10 h-10 bg-emerald-50 text-emerald-600 rounded-lg flex items-center justify-center">
                  <TrendingUp className="w-5 h-5" />
                </div>
              </Card>

              <Card className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider font-bold">Best Strategy Savings</p>
                  <h3 className="text-2xl font-black text-slate-900 mt-1">
                    {summary.best_savings.toLocaleString()} kg
                  </h3>
                  <span className="text-[10px] text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded font-semibold mt-1 inline-block">
                    Minimization Strategy
                  </span>
                </div>
                <div className="w-10 h-10 bg-blue-50 text-blue-600 rounded-lg flex items-center justify-center">
                  <Award className="w-5 h-5" />
                </div>
              </Card>

              <Card className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider font-bold">Average Confidence</p>
                  <h3 className="text-2xl font-black text-slate-900 mt-1">
                    {summary.average_confidence}%
                  </h3>
                  <span className="text-[10px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded font-semibold mt-1 inline-block">
                    Deterministic Tie-Break
                  </span>
                </div>
                <div className="w-10 h-10 bg-slate-50 text-slate-600 rounded-lg flex items-center justify-center">
                  <CheckCircle className="w-5 h-5" />
                </div>
              </Card>

              <Card className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider font-bold">Avg Projected Fitness</p>
                  <h3 className="text-2xl font-black text-slate-900 mt-1">
                    {(summary.average_projected_fitness * 100).toFixed(1)}%
                  </h3>
                  <span className="text-[10px] text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded font-semibold mt-1 inline-block">
                    Conformance Protected
                  </span>
                </div>
                <div className="w-10 h-10 bg-amber-50 text-amber-600 rounded-lg flex items-center justify-center">
                  <Layers className="w-5 h-5" />
                </div>
              </Card>
            </div>
          )}

          {/* Load History Indicator */}
          {loadedVersion && (
            <div className="flex items-center justify-between bg-blue-50 border border-blue-100 rounded-lg p-3 text-sm text-blue-800">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-blue-600" />
                <span>
                  Viewing snapshot version <strong>v{loadedVersion}</strong> (Run ID:{" "}
                  <code className="text-xs bg-white px-1 py-0.5 rounded border border-blue-200">
                    {plans[0]?.optimization_run_id}
                  </code>
                  )
                </span>
              </div>
              {loadedVersion !== (history[0]?.optimization_version || 0) && (
                <Button variant="outline" onClick={() => fetchData(selectedAnalysisId)} className="bg-white font-bold text-xs px-2.5 py-1">
                  Restore Latest Version
                </Button>
              )}
            </div>
          )}

          {/* Main Layout Tabs */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left & Middle Column: Plan Details */}
            <div className="lg:col-span-2 space-y-6">
              <div className="border-b border-gray-200">
                <nav className="flex space-x-4" aria-label="Tabs">
                  {[
                    { id: "balanced", name: "Balanced Plan" },
                    { id: "carbon_minimization", name: "Carbon Minimization" },
                    { id: "conformance_maximization", name: "Conformance Maximization" },
                  ].map((tab) => {
                    const isSelected = activeTab === tab.id;
                    const count = plans.find(p => p.strategy_name === tab.id)?.hops.length || 0;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`py-3 px-1 border-b-2 font-bold text-sm flex items-center gap-2 transition-all ${
                          isSelected
                            ? "border-blue-600 text-blue-600"
                            : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
                        }`}
                      >
                        {tab.name}
                        <span className={`px-2 py-0.5 text-xs rounded-full ${
                          isSelected ? "bg-blue-100 text-blue-700" : "bg-slate-100 text-slate-600"
                        }`}>
                          {count} {count === 1 ? "hop" : "hops"}
                        </span>
                      </button>
                    );
                  })}
                </nav>
              </div>

              {/* Active Plan Detail */}
              {activePlan ? (
                <div className="space-y-6">
                  {/* Strategy Banner */}
                  <Card className="p-5 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-blue-700 bg-blue-100 px-2 py-0.5 rounded uppercase tracking-wider">
                            Rank #{activePlan.strategy_rank}
                          </span>
                          <span className="text-xs font-bold text-slate-600 bg-white border border-slate-200 px-2 py-0.5 rounded uppercase tracking-wider">
                            Strategy Score: {activePlan.strategy_score}
                          </span>
                        </div>
                        <h2 className="text-xl font-black text-slate-900 mt-2 capitalize font-black">
                          {activePlan.strategy_name.replace("_", " ")}
                        </h2>
                        <p className="text-sm text-slate-600 mt-1">
                          Evaluates {activePlan.hops.length} steps to reduce emissions without compromising standard performance bounds.
                        </p>
                      </div>

                      {/* OCEL Readiness Check */}
                      <div className="flex flex-col items-end">
                        {activePlan.ocel_ready ? (
                          <div className="flex items-center gap-1.5 text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-100 text-xs font-bold">
                            <Database className="w-3.5 h-3.5" />
                            OCEL 2.0 Ready
                          </div>
                        ) : (
                          <div className="flex items-center gap-1.5 text-slate-600 bg-slate-50 px-2.5 py-1 rounded-md border border-slate-200 text-xs font-bold">
                            <Info className="w-3.5 h-3.5" />
                            Classic Event Logs
                          </div>
                        )}
                        <span className="text-[10px] text-slate-500 mt-1 font-medium">
                          Lineage Data: {activePlan.source_event_ids.length} events mapped
                        </span>
                      </div>
                    </div>
                  </Card>

                  {/* Hop Timeline */}
                  <Card className="p-6">
                    <h3 className="text-lg font-bold text-slate-900 mb-6 flex items-center gap-2">
                      Optimization Hop Timeline
                    </h3>
                    <div className="relative border-l border-slate-100 pl-6 ml-3 space-y-8">
                      {activePlan.hops.map((hop) => (
                        <div key={hop.hop_index} className="relative group">
                          {/* Circle Icon Indicator */}
                          <span className="absolute -left-[37px] top-0.5 w-6 h-6 rounded-full bg-blue-100 border-2 border-white flex items-center justify-center text-xs font-bold text-blue-700 shadow-sm transition-all group-hover:scale-110 group-hover:bg-blue-600 group-hover:text-white">
                            {hop.hop_index}
                          </span>
                          
                          <div className="space-y-1">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                                Hop #{hop.hop_index} — {hop.activity_replaced}
                              </span>
                              <span className="text-xs font-semibold text-slate-400 font-mono">
                                Source Reroute v{hop.source_reroute_version}
                              </span>
                            </div>

                            <h4 className="text-base font-bold text-slate-900 flex items-center gap-2">
                              <span>Replace {hop.activity_replaced}</span>
                              <ArrowRight className="w-4 h-4 text-slate-400" />
                              <span className="text-blue-600 font-black">{hop.action_applied.replace("Replace with ", "")}</span>
                            </h4>

                            <p className="text-sm text-slate-600 mt-2 bg-slate-50 p-3 rounded-lg border border-slate-100 italic leading-relaxed">
                              &ldquo;{hop.reasoning}&rdquo;
                            </p>

                            <div className="flex items-center gap-4 pt-2">
                              <span className="text-[10px] text-slate-400 flex items-center gap-1 font-medium">
                                <Info className="w-3.5 h-3.5" />
                                Reroute ID: <code className="bg-slate-100 px-1 py-0.5 rounded text-[9px] font-mono">{hop.source_reroute_id}</code>
                              </span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>
                </div>
              ) : (
                <Card className="p-6 text-center text-slate-500">
                  Select a strategy to display the multi-hop timeline.
                </Card>
              )}
            </div>

            {/* Right Column: Comparative Grid & History */}
            <div className="space-y-6">
              {/* Strategy Comparison Matrix */}
              <Card className="p-5">
                <h3 className="text-base font-black text-slate-900 mb-4 flex items-center gap-1.5">
                  <Layers className="w-4 h-4 text-blue-600" />
                  Strategy Matrix
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="border-b border-slate-100 text-slate-400 uppercase tracking-wider font-bold">
                        <th className="py-2">Rank</th>
                        <th className="py-2">Strategy</th>
                        <th className="py-2 text-right">Score</th>
                        <th className="py-2 text-right">Savings</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                      {plans.map((p) => (
                        <tr
                          key={p.strategy_name}
                          onClick={() => setActiveTab(p.strategy_name)}
                          className={`hover:bg-slate-50 cursor-pointer transition-colors ${
                            activeTab === p.strategy_name ? "bg-slate-50 font-semibold" : ""
                          }`}
                        >
                          <td className="py-3">
                            <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                              p.strategy_rank === 1 ? "bg-amber-100 text-amber-800" : "bg-slate-100 text-slate-600"
                            }`}>
                              #{p.strategy_rank}
                            </span>
                          </td>
                          <td className="py-3 capitalize text-slate-700 truncate max-w-[120px]">
                            {p.strategy_name.replace("_", " ")}
                          </td>
                          <td className="py-3 text-right text-slate-900 font-bold">{p.strategy_score}</td>
                          <td className="py-3 text-right text-emerald-600 font-bold">
                            {p.total_carbon_savings_kg.toLocaleString()} kg
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>

              {/* Version History Log */}
              <Card className="p-5">
                <h3 className="text-base font-black text-slate-900 mb-4 flex items-center gap-1.5">
                  <Clock className="w-4 h-4 text-blue-600" />
                  Snapshot History
                </h3>
                <div className="space-y-3">
                  {history.map((h) => (
                    <div
                      key={h.optimization_run_id}
                      onClick={() => loadVersion(h.optimization_version)}
                      className={`p-3 rounded-lg border text-xs cursor-pointer hover:bg-slate-50 transition-colors ${
                        loadedVersion === h.optimization_version
                          ? "border-blue-200 bg-blue-50/50"
                          : "border-slate-100 bg-white"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-800">
                          v{h.optimization_version} (Run #{h.optimization_version})
                        </span>
                        <span className="text-slate-400">
                          {new Date(h.generated_at).toLocaleString()}
                        </span>
                      </div>
                      
                      <div className="flex items-center justify-between mt-2 text-slate-500">
                        <span>Best: <strong className="capitalize text-slate-700">{h.best_strategy_name.replace("_", " ")}</strong> ({h.best_strategy_score})</span>
                        <span className="text-emerald-600 font-bold">
                          {h.total_savings.toLocaleString()} kg savings
                        </span>
                      </div>
                    </div>
                  ))}
                  
                  {history.length === 0 && (
                    <div className="text-center text-slate-400 py-6 text-xs italic">
                      No snapshots generated yet.
                    </div>
                  )}
                </div>
              </Card>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
