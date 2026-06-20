"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "../../../context/AuthContext";
import { useCopilot } from "../../../context/CopilotContext";
import { Card } from "../../../components/Card";
import { Button } from "../../../components/Button";
import { api } from "../../../services/api";
import { formatMetric } from "../../../services/format";
import {
  Sparkles,
  Shield,
  TrendingUp,
  AlertTriangle,
  Layers,
  Database,
  ArrowRight,
  RefreshCw,
  X,
  CheckCircle,
  Clock,
  ExternalLink,
  Info
} from "lucide-react";

interface EvidenceRecord {
  metric_name: string;
  metric_value: string;
  metric_threshold: string;
  source_engine: string;
  severity_contribution: number;
}

interface Recommendation {
  recommendation_id: string;
  title: string;
  description: string;
  category: string;
  severity: string;
  priority_score: number;
  confidence_score: number;
  estimated_carbon_reduction: number;
  estimated_cost_reduction: number;
  estimated_compliance_improvement: number;
  source_engine: string;
  evidence: EvidenceRecord[];
  supporting_metrics: Record<string, any>;
}

interface RunHistory {
  recommendation_run_id: string;
  recommendation_version: number;
  generated_at: string;
  recommendation_count: number;
  critical_count: number;
  total_estimated_carbon_reduction: number;
}

export default function RecommendationsPage() {
  const { activeWorkspace } = useAuth();
  const { selectedAnalysisId } = useCopilot();

  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [history, setHistory] = useState<RunHistory[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>("");
  const [selectedRec, setSelectedRec] = useState<Recommendation | null>(null);

  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [selectedSeverity, setSelectedSeverity] = useState<string>("All");

  const loadData = useCallback(async (analysisId: string) => {
    setLoading(true);
    setError(null);
    try {
      // 1. Load history
      const histRes = await api.get(`/api/v1/recommendations/${analysisId}/history`);
      setHistory(histRes.data);

      // 2. Load latest recommendations
      const recsRes = await api.get(`/api/v1/recommendations/${analysisId}`);
      setRecommendations(recsRes.data);

      if (histRes.data.length > 0) {
        // Default to latest run ID
        const latestRun = histRes.data[histRes.data.length - 1];
        setSelectedRunId(latestRun.recommendation_run_id);
      }
    } catch (err: any) {
      console.error(err);
      setError("Failed to load recommendations context.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedAnalysisId) {
      loadData(selectedAnalysisId);
    } else {
      setRecommendations([]);
      setHistory([]);
      setSelectedRunId("");
      setSelectedRec(null);
    }
  }, [selectedAnalysisId, loadData]);

  const handleRefresh = async () => {
    if (!selectedAnalysisId) return;
    setRefreshing(true);
    setError(null);
    try {
      const res = await api.post(`/api/v1/recommendations/${selectedAnalysisId}/refresh`);
      setRecommendations(res.data);
      // Refresh history run info
      const histRes = await api.get(`/api/v1/recommendations/${selectedAnalysisId}/history`);
      setHistory(histRes.data);
      if (histRes.data.length > 0) {
        const latestRun = histRes.data[histRes.data.length - 1];
        setSelectedRunId(latestRun.recommendation_run_id);
      }
      setSelectedRec(null);
    } catch (err: any) {
      console.error(err);
      setError("Re-computing recommendations failed.");
    } finally {
      setRefreshing(false);
    }
  };

  // KPI Calculations
  const totalCount = recommendations.length;
  const criticalCount = recommendations.filter((r) => r.severity === "Critical").length;
  const potentialCarbonSavings = recommendations.reduce((acc, r) => acc + r.estimated_carbon_reduction, 0);
  const potentialComplianceImprovement = recommendations.reduce((acc, r) => acc + r.estimated_compliance_improvement, 0);

  // Filters setup
  const categories = ["All", "Carbon Reduction", "Conformance", "Bottleneck", "ESG", "Supplier", "Compliance Risk", "Data Quality"];
  const severities = ["All", "Critical", "High", "Medium", "Low"];

  const filteredRecommendations = recommendations.filter((r) => {
    const matchCat = selectedCategory === "All" || r.category === selectedCategory;
    const matchSev = selectedSeverity === "All" || r.severity === selectedSeverity;
    return matchCat && matchSev;
  });

  const getSeverityBadgeClass = (severity: string) => {
    switch (severity) {
      case "Critical":
        return "bg-purple-100 text-purple-800 border-purple-200";
      case "High":
        return "bg-rose-100 text-rose-800 border-rose-200";
      case "Medium":
        return "bg-amber-100 text-amber-800 border-amber-200";
      default:
        return "bg-blue-100 text-blue-800 border-blue-200";
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "Carbon Reduction":
        return <TrendingUp className="w-4 h-4 text-emerald-600" />;
      case "Conformance":
      case "Compliance Risk":
        return <Shield className="w-4 h-4 text-blue-600" />;
      case "Bottleneck":
        return <Clock className="w-4 h-4 text-amber-600" />;
      case "ESG":
        return <Layers className="w-4 h-4 text-purple-600" />;
      default:
        return <Database className="w-4 h-4 text-slate-600" />;
    }
  };

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            <Sparkles className="w-8 h-8 text-purple-600" />
            Recommendation Center
          </h1>
          <p className="text-slate-500 font-medium mt-1">
            Prioritized, explainable, evidence-backed action plans parsed from process metrics and ESG performance.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {selectedAnalysisId && (
            <Button
              variant="primary"
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center gap-2 font-bold"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
              {refreshing ? "Recalculating..." : "Refresh Recommendations"}
            </Button>
          )}
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-100 rounded-xl text-rose-800 text-sm font-bold">
          {error}
        </div>
      )}

      {!selectedAnalysisId ? (
        <Card title="No Analysis Selected" className="text-center py-12">
          <p className="text-sm font-semibold text-slate-500">
            Please select an active process analysis from the dashboard header to discover and rank opportunities.
          </p>
        </Card>
      ) : loading ? (
        <div className="py-24 text-center space-y-3">
          <div className="w-10 h-10 border-4 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-sm font-bold text-slate-500">Generating optimizations dashboard...</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 bg-white border border-slate-200/60 rounded-2xl shadow-sm">
              <span className="text-xs font-black text-slate-400 uppercase tracking-wider block">Total Opportunities</span>
              <span className="text-3xl font-black text-slate-800 block mt-1">{totalCount}</span>
            </div>
            <div className="p-5 bg-white border border-slate-200/60 rounded-2xl shadow-sm">
              <span className="text-xs font-black text-rose-500 uppercase tracking-wider block">Critical Severity</span>
              <span className="text-3xl font-black text-rose-600 block mt-1">{criticalCount}</span>
            </div>
            <div className="p-5 bg-white border border-slate-200/60 rounded-2xl shadow-sm">
              <span className="text-xs font-black text-emerald-500 uppercase tracking-wider block">Est. Carbon Savings</span>
              <span className="text-3xl font-black text-emerald-600 block mt-1">{potentialCarbonSavings.toLocaleString(undefined, {maximumFractionDigits: 1})} kg</span>
            </div>
            <div className="p-5 bg-white border border-slate-200/60 rounded-2xl shadow-sm">
              <span className="text-xs font-black text-blue-500 uppercase tracking-wider block">Avg Compliance Improvement</span>
              <span className="text-3xl font-black text-blue-600 block mt-1">
                {totalCount > 0 ? (potentialComplianceImprovement / totalCount).toFixed(1) : 0}%
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Table */}
            <div className="lg:col-span-2 space-y-4">
              <Card title="Ranked Optimization Opportunities">
                {/* Filters Row */}
                <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4 mb-4">
                  <div className="flex items-center gap-2">
                    <label className="text-xs font-bold text-slate-500">Category:</label>
                    <select
                      className="px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-bold text-slate-700"
                      value={selectedCategory}
                      onChange={(e) => setSelectedCategory(e.target.value)}
                    >
                      {categories.map((c) => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="text-xs font-bold text-slate-500">Severity:</label>
                    <select
                      className="px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-bold text-slate-700"
                      value={selectedSeverity}
                      onChange={(e) => setSelectedSeverity(e.target.value)}
                    >
                      {severities.map((s) => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </div>
                </div>

                {filteredRecommendations.length === 0 ? (
                  <p className="text-sm font-semibold text-slate-400 text-center py-12">
                    No recommendations match the selected filters.
                  </p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs font-semibold text-slate-600 border-collapse">
                      <thead>
                        <tr className="border-b border-slate-100 text-[10px] text-slate-400 uppercase tracking-wider font-extrabold">
                          <th className="py-2.5 w-12 text-center">Rank</th>
                          <th className="py-2.5">Opportunity</th>
                          <th className="py-2.5">Category</th>
                          <th className="py-2.5">Severity</th>
                          <th className="py-2.5 w-24">Priority Score</th>
                          <th className="py-2.5 text-right w-16">Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredRecommendations.map((rec, idx) => (
                          <tr
                            key={rec.recommendation_id}
                            className={`border-b border-slate-50 hover:bg-slate-50/50 cursor-pointer ${selectedRec?.recommendation_id === rec.recommendation_id ? "bg-purple-50/20" : ""}`}
                            onClick={() => setSelectedRec(rec)}
                          >
                            <td className="py-3.5 text-center font-black text-slate-400">#{idx + 1}</td>
                            <td className="py-3.5 pr-2">
                              <span className="font-bold text-slate-800 block">{rec.title}</span>
                              <span className="text-[10px] text-slate-400 font-medium block mt-0.5 truncate max-w-[280px]">
                                {rec.description}
                              </span>
                            </td>
                            <td className="py-3.5">
                              <div className="flex items-center gap-1 text-[11px] font-bold text-slate-700">
                                {getCategoryIcon(rec.category)}
                                {rec.category}
                              </div>
                            </td>
                            <td className="py-3.5">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-black border uppercase tracking-wider ${getSeverityBadgeClass(rec.severity)}`}>
                                {rec.severity}
                              </span>
                            </td>
                            <td className="py-3.5">
                              <div className="flex items-center gap-2">
                                <span className="font-bold text-slate-800">{rec.priority_score}</span>
                                <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                                  <div
                                    className={`h-full rounded-full ${rec.priority_score >= 80 ? "bg-rose-500" : rec.priority_score >= 60 ? "bg-amber-400" : "bg-blue-400"}`}
                                    style={{ width: `${rec.priority_score}%` }}
                                  />
                                </div>
                              </div>
                            </td>
                            <td className="py-3.5 text-right">
                              <button
                                className="p-1 text-slate-400 hover:text-purple-600 transition-colors"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setSelectedRec(rec);
                                }}
                              >
                                <ArrowRight className="w-4 h-4" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </Card>
            </div>

            {/* Right details panel or Run History */}
            <div className="space-y-4">
              {/* Opportunities Details Drawer */}
              {selectedRec ? (
                <Card title="Opportunity Explorer">
                  <div className="relative space-y-5 text-xs font-semibold text-slate-600">
                    <button
                      onClick={() => setSelectedRec(null)}
                      className="absolute -top-[52px] right-0 p-1 text-slate-400 hover:text-slate-600"
                    >
                      <X className="w-4 h-4" />
                    </button>
                    <div>
                      <span className={`px-2 py-0.5 rounded text-[9px] font-black border uppercase tracking-wider ${getSeverityBadgeClass(selectedRec.severity)}`}>
                        {selectedRec.severity} Priority
                      </span>
                      <h3 className="text-base font-black text-slate-800 mt-2">{selectedRec.title}</h3>
                      <p className="text-slate-500 mt-1 font-medium leading-relaxed">{selectedRec.description}</p>
                    </div>

                    {/* Scores side by side */}
                    <div className="grid grid-cols-2 gap-4 border-t border-b border-slate-100 py-3">
                      <div>
                        <span className="block text-[10px] text-slate-400 font-extrabold uppercase">Priority Score</span>
                        <div className="flex items-center gap-1 mt-1">
                          <span className="text-2xl font-black text-slate-800">{selectedRec.priority_score}</span>
                          <span className="text-[10px] text-slate-400 font-medium">/ 100</span>
                        </div>
                      </div>
                      <div>
                        <span className="block text-[10px] text-slate-400 font-extrabold uppercase">Confidence Rating</span>
                        <div className="flex items-center gap-1 mt-1">
                          <span className="text-2xl font-black text-slate-800">{selectedRec.confidence_score}</span>
                          <span className="text-[10px] text-slate-400 font-medium">%</span>
                        </div>
                      </div>
                    </div>

                    {/* Estimated Savings */}
                    <div className="space-y-2.5">
                      <span className="block text-[10px] text-slate-400 font-extrabold uppercase">Estimated Impact</span>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        {selectedRec.estimated_carbon_reduction > 0 && (
                          <div className="p-2 bg-emerald-50 rounded-lg text-emerald-800 border border-emerald-100/50">
                            Carbon Reduction: <strong>-{selectedRec.estimated_carbon_reduction.toFixed(1)} kg</strong>
                          </div>
                        )}
                        {selectedRec.estimated_cost_reduction > 0 && (
                          <div className="p-2 bg-blue-50 rounded-lg text-blue-800 border border-blue-100/50">
                            Cost Savings: <strong>${selectedRec.estimated_cost_reduction.toLocaleString()}</strong>
                          </div>
                        )}
                        {selectedRec.estimated_compliance_improvement > 0 && (
                          <div className="p-2 bg-purple-50 rounded-lg text-purple-800 border border-purple-100/50 col-span-2">
                            Compliance Fitness Lift: <strong>+{selectedRec.estimated_compliance_improvement.toFixed(1)}%</strong>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Mandatory Standardized Evidence Schema checklist */}
                    <div className="space-y-3">
                      <span className="block text-[10px] text-slate-400 font-extrabold uppercase flex items-center gap-1">
                        <CheckCircle className="w-3.5 h-3.5 text-emerald-600" /> Traceable Evidence Checklist
                      </span>
                      <div className="space-y-2">
                        {selectedRec.evidence.map((ev, idx) => (
                          <div key={idx} className="p-3 bg-slate-50 border border-slate-100 rounded-lg space-y-1.5">
                            <div className="flex justify-between font-bold text-slate-800">
                              <span>{ev.metric_name}</span>
                              <span className="text-emerald-700">{ev.metric_value}</span>
                            </div>
                            <div className="flex justify-between text-[10px] text-slate-400 font-medium">
                              <span>Limit/Threshold: {ev.metric_threshold}</span>
                              <span>Severity Contribution: {ev.severity_contribution}%</span>
                            </div>
                            <div className="text-[9px] text-slate-400 font-bold uppercase tracking-wider">
                              Engine: {ev.source_engine}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Traceability Metadata */}
                    <div className="space-y-2.5 pt-3 border-t border-slate-100 text-[10px] font-semibold text-slate-400 leading-normal">
                      <div className="flex justify-between">
                        <span>Originating Engine:</span>
                        <span className="text-slate-700 font-bold">{selectedRec.source_engine}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Source Record ID:</span>
                        <span className="font-mono text-slate-600 select-all">{selectedRec.recommendation_id.slice(0, 8)}...</span>
                      </div>
                    </div>
                  </div>
                </Card>
              ) : (
                <Card title="Run Snapshot History">
                  {history.length === 0 ? (
                    <p className="text-xs font-semibold text-slate-400 text-center py-6">
                      No run history detected.
                    </p>
                  ) : (
                    <div className="space-y-3">
                      {history.map((hist) => (
                        <div key={hist.recommendation_run_id} className="p-3 bg-slate-50 border border-slate-100 rounded-xl space-y-2">
                          <div className="flex justify-between items-center text-xs font-bold text-slate-700">
                            <span>Version {hist.recommendation_version}</span>
                            <span className="text-[10px] text-slate-400 font-semibold">
                              {new Date(hist.generated_at).toLocaleDateString("en-GB")}
                            </span>
                          </div>
                          <div className="grid grid-cols-3 gap-2 text-[10px] text-slate-500 font-semibold">
                            <div>
                              Opportunities: <strong className="text-slate-800">{hist.recommendation_count}</strong>
                            </div>
                            <div>
                              Critical: <strong className="text-slate-800">{hist.critical_count}</strong>
                            </div>
                            <div>
                              Carbon Savings: <strong className="text-slate-800">{hist.total_estimated_carbon_reduction.toFixed(0)} kg</strong>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </Card>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
