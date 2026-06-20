"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "../../../context/AuthContext";
import { useCopilot } from "../../../context/CopilotContext";
import { api } from "../../../services/api";
import { Card } from "../../../components/Card";
import { Button } from "../../../components/Button";

interface RerouteSimulation {
  reroute_id: string;
  reroute_version: number;
  reroute_run_id: string;
  candidate_activity: string;
  candidate_action: string;
  candidate_route: string[];
  baseline_emissions: number;
  projected_emissions: number;
  projected_savings: number;
  projected_fitness: number;
  projected_carbon_fitness: number;
  confidence_score: number;
  optimization_ready: boolean;
  snapshot_timestamp: string;
}

interface RerouteSummary {
  total_reroutes: number;
  total_carbon_savings: number;
  best_savings: number;
  average_confidence: number;
  average_projected_fitness: number;
}

interface SnapshotHistory {
  reroute_version: number;
  reroute_run_id: string;
  generated_at: string;
  total_savings: number;
  best_reroute_activity: string;
  best_reroute_savings: number;
}

export default function GreenReroutingCenter() {
  const { token } = useAuth();
  const { selectedAnalysisId } = useCopilot();

  const [reroutes, setReroutes] = useState<RerouteSimulation[]>([]);
  const [summary, setSummary] = useState<RerouteSummary | null>(null);
  const [history, setHistory] = useState<SnapshotHistory[]>([]);
  const [selectedReroute, setSelectedReroute] = useState<RerouteSimulation | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (selectedAnalysisId) {
      fetchData(selectedAnalysisId);
    } else {
      setReroutes([]);
      setSummary(null);
      setHistory([]);
    }
  }, [selectedAnalysisId]);

  const fetchData = async (analysisId: string) => {
    setLoading(true);
    setError(null);
    try {
      const [resReroutes, resSummary, resHistory] = await Promise.all([
        api.get(`/api/v1/rerouting/${analysisId}`),
        api.get(`/api/v1/rerouting/${analysisId}/summary`),
        api.get(`/api/v1/rerouting/${analysisId}/history`),
      ]);

      setReroutes(Array.isArray(resReroutes.data) ? resReroutes.data : []);
      setSummary(resSummary.data);
      setHistory(Array.isArray(resHistory.data) ? resHistory.data : []);
    } catch (err: any) {
      console.error("Error fetching rerouting data:", err);
      setError(err?.message || "Failed to load rerouting data.");
    } finally {
      setLoading(false);
    }
  };

  const generateNewSimulation = async () => {
    if (!selectedAnalysisId) return;
    setGenerating(true);
    setError(null);
    try {
      await api.post(`/api/v1/rerouting/${selectedAnalysisId}/generate`);
      await fetchData(selectedAnalysisId);
    } catch (err: any) {
      setError(err?.message || "Failed to generate simulation.");
    } finally {
      setGenerating(false);
    }
  };

  const openDrawer = (reroute: RerouteSimulation) => {
    setSelectedReroute(reroute);
    setIsDrawerOpen(true);
  };

  if (!token) return null;

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            <span className="w-9 h-9 bg-emerald-100 rounded-xl flex items-center justify-center text-emerald-700">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
              </svg>
            </span>
            Green Rerouting Center
          </h1>
          <p className="text-slate-500 font-medium mt-1">
            Discover compliant alternative execution paths with quantified carbon savings.
          </p>
        </div>
        {selectedAnalysisId && (
          <Button
            variant="primary"
            onClick={generateNewSimulation}
            disabled={generating}
            className="flex items-center gap-2 font-bold"
          >
            {generating ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 7.89H18v3" />
                </svg>
                Generate New Simulation
              </>
            )}
          </Button>
        )}
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-100 rounded-xl text-rose-800 text-sm font-bold">
          {error}
        </div>
      )}

      {/* No Analysis Selected */}
      {!selectedAnalysisId ? (
        <Card title="No Analysis Selected" className="text-center py-12">
          <p className="text-sm font-semibold text-slate-500">
            Please select an active process analysis from the dashboard to generate green rerouting simulations.
          </p>
        </Card>
      ) : loading ? (
        <div className="py-24 text-center space-y-3">
          <div className="w-10 h-10 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm font-bold text-slate-500">Loading Green Rerouting Data...</p>
        </div>
      ) : (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { label: "Total Reroutes", value: `${summary?.total_reroutes || 0}`, color: "text-slate-800" },
              { label: "Total Carbon Savings", value: `${(summary?.total_carbon_savings || 0).toFixed(0)} kg`, color: "text-emerald-600" },
              { label: "Best Route Savings", value: `${(summary?.best_savings || 0).toFixed(0)} kg`, color: "text-emerald-600" },
              { label: "Avg Confidence", value: `${(summary?.average_confidence || 0).toFixed(1)}%`, color: "text-blue-600" },
            ].map((kpi) => (
              <div key={kpi.label} className="p-5 bg-white border border-slate-200/60 rounded-2xl shadow-sm">
                <span className="text-xs font-black text-slate-400 uppercase tracking-wider block">{kpi.label}</span>
                <span className={`text-3xl font-black block mt-1 ${kpi.color}`}>{kpi.value}</span>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Reroute Table */}
            <div className="lg:col-span-2">
              <Card title="Candidate Reroutes (Latest Batch)">
                {reroutes.length === 0 ? (
                  <div className="text-center py-12">
                    <p className="text-sm font-semibold text-slate-400">
                      No reroutes generated yet. Click &quot;Generate New Simulation&quot; to begin.
                    </p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs font-semibold text-slate-600 border-collapse">
                      <thead>
                        <tr className="border-b border-slate-100 text-[10px] text-slate-400 uppercase tracking-wider font-extrabold">
                          <th className="py-2.5 w-12 text-center">Rank</th>
                          <th className="py-2.5">Activity</th>
                          <th className="py-2.5">Alternative Route</th>
                          <th className="py-2.5">Savings (CO₂e)</th>
                          <th className="py-2.5">Fitness</th>
                          <th className="py-2.5 text-right">Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {reroutes.map((reroute, index) => (
                          <tr key={reroute.reroute_id} className="border-b border-slate-50 hover:bg-slate-50/50 cursor-pointer" onClick={() => openDrawer(reroute)}>
                            <td className="py-3.5 text-center font-black text-emerald-600">#{index + 1}</td>
                            <td className="py-3.5 font-bold text-slate-800">{reroute.candidate_activity}</td>
                            <td className="py-3.5 text-slate-600">{reroute.candidate_action}</td>
                            <td className="py-3.5 font-bold text-emerald-600">{reroute.projected_savings.toFixed(0)} kg</td>
                            <td className="py-3.5">{reroute.projected_fitness.toFixed(2)}</td>
                            <td className="py-3.5 text-right">
                              <button
                                onClick={(e) => { e.stopPropagation(); openDrawer(reroute); }}
                                className="px-3 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 rounded-lg text-[10px] font-bold transition-all border border-emerald-100/60"
                              >
                                Compare
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

            {/* Snapshot History */}
            <div>
              <Card title="Snapshot History">
                {history.length === 0 ? (
                  <p className="text-xs font-semibold text-slate-400 text-center py-6">No history available.</p>
                ) : (
                  <div className="space-y-3">
                    {history.map((snap, idx) => (
                      <div key={`${snap.reroute_version}-${idx}`} className="p-3 bg-slate-50 border border-slate-100 rounded-xl space-y-2">
                        <div className="flex justify-between items-center text-xs font-bold text-slate-700">
                          <span className="text-emerald-600">Version {snap.reroute_version}</span>
                          <span className="text-[10px] text-slate-400 font-semibold">
                            {snap.generated_at ? new Date(snap.generated_at).toLocaleDateString("en-GB") : "—"}
                          </span>
                        </div>
                        <div className="text-[10px] text-slate-500 font-semibold space-y-1">
                          <p>Total Savings: <strong className="text-slate-800">{snap.total_savings.toFixed(0)} kg</strong></p>
                          <p>Best Reroute: <strong className="text-slate-800">{snap.best_reroute_activity || "—"}</strong></p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            </div>
          </div>
        </>
      )}

      {/* Comparison Drawer */}
      {isDrawerOpen && selectedReroute && (
        <div className="fixed inset-0 z-50 flex justify-end">
          <div
            className="absolute inset-0 bg-black/40 backdrop-blur-sm"
            onClick={() => setIsDrawerOpen(false)}
          />
          <div className="relative w-full max-w-[520px] bg-white h-full border-l border-slate-200 p-8 overflow-y-auto shadow-2xl">
            <button
              onClick={() => setIsDrawerOpen(false)}
              className="absolute top-4 right-4 w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center text-slate-500 transition-colors"
            >
              ×
            </button>
            <h2 className="text-2xl font-black text-slate-900 mb-1">Route Comparison</h2>
            <p className="text-xs text-slate-400 font-semibold mb-6">
              Projected impact vs current execution path
            </p>

            <div className="p-5 bg-slate-50 border border-slate-200/60 rounded-xl mb-6 space-y-4">
              <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wider">Impact Summary</h3>
              <div className="grid grid-cols-2 gap-4">
                {[
                  { label: "Baseline Emissions", value: `${selectedReroute.baseline_emissions.toFixed(0)} kg`, color: "text-slate-800" },
                  { label: "Projected Emissions", value: `${selectedReroute.projected_emissions.toFixed(0)} kg`, color: "text-emerald-600" },
                  { label: "Carbon Savings", value: `${selectedReroute.projected_savings.toFixed(0)} kg`, color: "text-emerald-700" },
                  { label: "Projected Fitness", value: selectedReroute.projected_fitness.toFixed(2), color: "text-blue-600" },
                  { label: "Confidence", value: `${selectedReroute.confidence_score.toFixed(1)}%`, color: "text-purple-600" },
                  { label: "Carbon Fitness", value: selectedReroute.projected_carbon_fitness.toFixed(2), color: "text-teal-600" },
                ].map(({ label, value, color }) => (
                  <div key={label}>
                    <p className="text-[10px] text-slate-400 font-bold uppercase">{label}</p>
                    <p className={`text-xl font-black mt-0.5 ${color}`}>{value}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-5 bg-slate-50 border border-slate-200/60 rounded-xl mb-6">
              <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wider mb-4">Alternative Path</h3>
              <div className="space-y-3">
                {selectedReroute.candidate_route.map((step, idx) => {
                  const isAlt = step.includes(selectedReroute.candidate_action.replace("Replace with ", ""));
                  return (
                    <div key={idx} className="flex items-center gap-3">
                      <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-black flex-shrink-0 ${isAlt ? "bg-emerald-600 text-white" : "bg-slate-200 text-slate-600"}`}>
                        {idx + 1}
                      </div>
                      <div className={`p-3 rounded-lg border text-xs font-semibold w-full ${isAlt ? "bg-emerald-50 border-emerald-200 text-emerald-800" : "bg-white border-slate-200 text-slate-700"}`}>
                        {step}
                        {isAlt && <span className="ml-2 px-1.5 py-0.5 bg-emerald-600 text-white rounded text-[9px] font-black uppercase">New</span>}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {selectedReroute.optimization_ready && (
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl text-blue-700 text-xs font-semibold">
                <strong className="block font-black mb-1">Optimization Ready ✓</strong>
                This route satisfies the Sprint 3C-C optimization contract and is eligible for multi-hop process optimization.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
