"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useCopilot } from "../../../context/CopilotContext";
import { Card } from "../../../components/Card";
import { Button } from "../../../components/Button";
import { api } from "../../../services/api";
import {
  ShieldAlert,
  AlertTriangle,
  RefreshCw,
  TrendingUp,
  Activity,
  Award,
  CheckCircle,
  TrendingDown,
  Info,
  Calendar,
  Layers,
  Leaf,
  GitBranch,
  ShieldCheck,
  AlertCircle
} from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  Cell
} from "recharts";

interface Deviation {
  type: string;
  severity: string;
  description: string;
  impact_score: number;
  recommended_action: string;
}

interface SustainabilitySnapshot {
  sustainability_conformance_id?: string;
  sustainability_conformance_version: number;
  sustainability_conformance_run_id: string;
  snapshot_hash: string;
  snapshot_timestamp: string;
  process_fitness: number;
  carbon_fitness: number;
  sustainability_conformance: number;
  esg_compliance_score: number;
  sustainability_risk: string;
  deviations: Deviation[];
  source_reference_model_version: number;
  source_ocel_version: number;
  source_conformance_version: number;
  source_carbon_version: number;
  source_interaction_version: number;
  source_simulation_version: number;
  source_interoperability_version: number;
  source_carbon_fitness_version: number;
}

const COLORS = ["#3B82F6", "#10B981", "#EF4444", "#F59E0B", "#8B5CF6", "#EC4899"];

export default function SustainabilityConformancePage() {
  const { selectedAnalysisId } = useCopilot();
  
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [calculateError, setCalculateError] = useState<string | null>(null);
  const [data, setData] = useState<SustainabilitySnapshot | null>(null);
  const [history, setHistory] = useState<SustainabilitySnapshot[]>([]);

  const fetchConformanceData = useCallback(async () => {
    if (!selectedAnalysisId) return;
    try {
      setLoading(true);
      const res = await api.get(`/api/v1/sustainability-conformance/${selectedAnalysisId}`);
      setData(res.data);
      
      const histRes = await api.get(`/api/v1/sustainability-conformance/${selectedAnalysisId}/history`);
      setHistory(histRes.data);
      
    } catch (err: any) {
      if (err.response?.status !== 404 && err.response?.status !== 400) {
        console.warn("Failed to fetch sustainability conformance data", err);
      }
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [selectedAnalysisId]);

  useEffect(() => {
    fetchConformanceData();
  }, [fetchConformanceData]);

  const handleCalculate = async () => {
    if (!selectedAnalysisId) return;
    try {
      setCalculating(true);
      setCalculateError(null);
      await api.post(`/api/v1/sustainability-conformance/${selectedAnalysisId}/calculate`);
      await fetchConformanceData();
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message || "Unknown error";
      setCalculateError(detail);
      console.warn("Failed to calculate sustainability conformance", err);
    } finally {
      setCalculating(false);
    }
  };

  const handleVersionSelect = async (version: number) => {
    if (!selectedAnalysisId) return;
    try {
      setLoading(true);
      const res = await api.get(`/api/v1/sustainability-conformance/${selectedAnalysisId}/version/${version}`);
      setData(res.data);
    } catch (err) {
      console.warn("Failed to fetch version", err);
    } finally {
      setLoading(false);
    }
  };

  if (!selectedAnalysisId) {
    return (
      <div className="flex-1 p-8 bg-gray-50 flex items-center justify-center min-h-screen">
        <div className="text-center p-8 max-w-md bg-white rounded-xl shadow-md border border-gray-100">
          <AlertTriangle className="h-16 w-16 text-yellow-500 mx-auto mb-4 animate-bounce" />
          <h2 className="text-2xl font-bold text-gray-800">No Analysis Selected</h2>
          <p className="text-gray-500 mt-2">Please select a process analysis in the sidebar or active panel to check sustainability conformance.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex-1 p-8 flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <RefreshCw className="h-12 w-12 animate-spin text-emerald-500 mx-auto mb-4" />
          <p className="text-gray-600 font-semibold">Loading Sustainability Conformance metrics...</p>
        </div>
      </div>
    );
  }

  // Pre-process chart data
  const trendData = history
    .map((h) => ({
      version: `v${h.sustainability_conformance_version}`,
      "Sustainability Conformance": h.sustainability_conformance,
      "ESG Compliance": h.esg_compliance_score / 100.0,
      "Process Fitness": h.process_fitness,
      "Carbon Fitness": h.carbon_fitness,
    }))
    .reverse();

  // Deviation Distribution
  const deviationCounts = data?.deviations?.reduce(
    (acc: Record<string, number>, d) => {
      acc[d.severity] = (acc[d.severity] || 0) + 1;
      return acc;
    },
    { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 }
  ) || { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 };

  const deviationDistributionData = [
    { name: "LOW", count: deviationCounts.LOW, fill: "#3B82F6" },
    { name: "MEDIUM", count: deviationCounts.MEDIUM, fill: "#F59E0B" },
    { name: "HIGH", count: deviationCounts.HIGH, fill: "#EF4444" },
    { name: "CRITICAL", count: deviationCounts.CRITICAL, fill: "#7C3AED" }
  ];

  return (
    <div className="flex-1 p-8 bg-gray-50 overflow-y-auto min-h-screen">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-black text-gray-900 flex items-center gap-2 tracking-tight">
            <ShieldCheck className="h-8 w-8 text-blue-600 animate-pulse" />
            Sustainability Conformance
          </h1>
          <p className="text-gray-500 mt-1 font-medium">Unified Process Fitness, Carbon Penalties, & ESG Auditing</p>
        </div>
        <div className="flex items-center gap-3">
          {history.length > 0 && (
            <select
              className="border border-gray-200 rounded-lg px-4 py-2.5 text-sm bg-white font-semibold text-gray-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              onChange={(e) => handleVersionSelect(Number(e.target.value))}
              value={data?.sustainability_conformance_version || ""}
            >
              {history.map((h) => (
                <option key={h.sustainability_conformance_version} value={h.sustainability_conformance_version}>
                  Version {h.sustainability_conformance_version} ({new Date(h.snapshot_timestamp).toLocaleDateString()})
                </option>
              ))}
            </select>
          )}
          <Button
            onClick={handleCalculate}
            disabled={calculating}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-foreground px-5 py-2.5 rounded-lg shadow-md font-semibold transition-all"
          >
            <RefreshCw className={`h-4 w-4 ${calculating ? "animate-spin" : ""}`} />
            {calculating ? "Analyzing..." : "Run Conformance Check"}
          </Button>
        </div>
      </div>

      {calculateError && (
        <div className="mb-6 p-4 bg-amber-50 border border-amber-300 rounded-xl text-sm">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-amber-800 mb-1">Cannot Run Conformance Check</p>
              <p className="text-amber-700 leading-relaxed">{calculateError}</p>
            </div>
          </div>
        </div>
      )}

      {!data ? (
        <Card className="p-16 text-center border-dashed border-2 border-gray-300 bg-white">
          <ShieldAlert className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-gray-900">No Sustainability Conformance Report</h3>
          <p className="text-gray-500 mt-2 max-w-sm mx-auto">
            Evaluate your processes for unified process conformance and carbon penalties.
            All upstream analyses (OCEL, Conformance, Carbon Attribution, etc.) must be completed first.
          </p>
          <Button onClick={handleCalculate} disabled={calculating} className="mt-6 bg-blue-600 hover:bg-blue-700">
            {calculating ? "Analyzing..." : "Run Conformance Now"}
          </Button>
        </Card>
      ) : (
        <div className="space-y-8">
          {/* Main Scoring KPIs */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="p-6 bg-gradient-to-br from-blue-600 to-indigo-700 text-foreground shadow-md relative overflow-hidden group hover:shadow-lg transition-all border-none">
              <div className="absolute top-0 right-0 p-3 bg-white/10 text-foreground rounded-bl-xl">
                <ShieldCheck className="h-6 w-6" />
              </div>
              <h4 className="text-xs font-black text-blue-200 uppercase tracking-widest mb-1">Sustainability Conformance</h4>
              <p className="text-5xl font-black mt-1">{(data.sustainability_conformance * 100).toFixed(0)}%</p>
              <div className="text-xs text-blue-100 mt-4 font-semibold">Base Score (0.6*Process + 0.4*Carbon) - Penalties</div>
            </Card>

            <Card className="p-6 bg-gradient-to-br from-emerald-500 to-teal-600 text-foreground shadow-md relative overflow-hidden group hover:shadow-lg transition-all border-none">
              <div className="absolute top-0 right-0 p-3 bg-white/10 text-foreground rounded-bl-xl">
                <Award className="h-6 w-6" />
              </div>
              <h4 className="text-xs font-black text-emerald-100 uppercase tracking-widest mb-1">ESG Compliance Score</h4>
              <p className="text-5xl font-black mt-1">{data.esg_compliance_score.toFixed(0)}</p>
              <div className="text-xs text-emerald-500 bg-white/90 px-2.5 py-1 rounded mt-3 inline-block font-black">
                40% Process | 40% Carbon | 20% Supplier
              </div>
            </Card>

            <Card className={`p-6 shadow-md relative overflow-hidden group hover:shadow-lg transition-all border-none text-foreground ${
              data.sustainability_risk === "CRITICAL"
                ? "bg-gradient-to-br from-purple-600 to-deep-purple-800"
                : data.sustainability_risk === "HIGH"
                ? "bg-gradient-to-br from-red-500 to-rose-600"
                : data.sustainability_risk === "MEDIUM"
                ? "bg-gradient-to-br from-yellow-500 to-amber-600"
                : "bg-gradient-to-br from-sky-500 to-blue-600"
            }`}>
              <div className="absolute top-0 right-0 p-3 bg-white/10 text-foreground rounded-bl-xl">
                <AlertCircle className="h-6 w-6" />
              </div>
              <h4 className="text-xs font-black uppercase tracking-widest mb-1 text-foreground/80">Sustainability Risk Level</h4>
              <p className="text-4xl font-black mt-2 tracking-wide">{data.sustainability_risk}</p>
              <div className="text-xs mt-4 font-semibold text-foreground/90">Based on Critical Violations & Conformance</div>
            </Card>
          </div>

          {/* Upstream Components KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="p-5 bg-white border border-gray-100 shadow-sm relative overflow-hidden group hover:shadow-md transition-all">
              <div className="absolute top-0 right-0 p-2 text-blue-500 bg-blue-50 rounded-bl-xl">
                <Activity className="h-4 w-4" />
              </div>
              <h4 className="text-xs font-black text-gray-400 uppercase tracking-wider mb-1">Process Fitness</h4>
              <p className="text-2xl font-black text-blue-600">{(data.process_fitness * 100).toFixed(0)}%</p>
              <div className="text-xs text-gray-500 mt-2 font-medium">Source: Object Conformance</div>
            </Card>

            <Card className="p-5 bg-white border border-gray-100 shadow-sm relative overflow-hidden group hover:shadow-md transition-all">
              <div className="absolute top-0 right-0 p-2 text-emerald-500 bg-emerald-50 rounded-bl-xl">
                <Leaf className="h-4 w-4" />
              </div>
              <h4 className="text-xs font-black text-gray-400 uppercase tracking-wider mb-1">Carbon Fitness</h4>
              <p className="text-2xl font-black text-emerald-600">{(data.carbon_fitness * 100).toFixed(0)}%</p>
              <div className="text-xs text-gray-500 mt-2 font-medium">Source: Carbon Fitness Engine</div>
            </Card>

            <Card className="p-5 bg-white border border-gray-100 shadow-sm relative overflow-hidden group hover:shadow-md transition-all">
              <div className="absolute top-0 right-0 p-2 text-red-500 bg-red-50 rounded-bl-xl">
                <ShieldAlert className="h-4 w-4" />
              </div>
              <h4 className="text-xs font-black text-gray-400 uppercase tracking-wider mb-1">Total Deviations</h4>
              <p className="text-2xl font-black text-red-600">{data.deviations?.length || 0}</p>
              <div className="text-xs text-gray-500 mt-2 font-medium">Process & Carbon Breaches</div>
            </Card>

            <Card className="p-5 bg-white border border-gray-100 shadow-sm relative overflow-hidden group hover:shadow-md transition-all">
              <div className="absolute top-0 right-0 p-2 text-purple-500 bg-purple-50 rounded-bl-xl">
                <GitBranch className="h-4 w-4" />
              </div>
              <h4 className="text-xs font-black text-gray-400 uppercase tracking-wider mb-1">Lineage Version</h4>
              <p className="text-2xl font-black text-purple-600">v{data.sustainability_conformance_version}</p>
              <div className="text-xs text-gray-500 mt-2 font-medium">Deterministic Snapshot Hash</div>
            </Card>
          </div>

          {/* Lineage Traceability Drawer */}
          <Card className="p-6 bg-card-bg text-foreground border-none shadow-lg relative overflow-hidden">
            <div className="absolute top-0 right-0 bg-blue-600/10 px-4 py-2 text-xxs font-mono text-blue-400 rounded-bl-xl select-none uppercase tracking-widest font-black">
              Lineage Contract Active
            </div>
            <h3 className="text-lg font-black tracking-tight mb-6 flex items-center gap-2 text-foreground">
              <GitBranch className="h-5 w-5 text-blue-400 animate-spin" style={{ animationDuration: '6s' }} />
              Upstream Ledger & Immutability Trace
            </h3>
            
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-4 mb-6 text-center">
              <div className="p-3.5 bg-slate-100 rounded-xl border border-border-color hover:border-slate-600 transition-all">
                <div className="text-[10px] uppercase font-bold text-text-muted tracking-wider">Ref Model</div>
                <div className="text-xl font-black text-foreground mt-1">v{data.source_reference_model_version}</div>
              </div>
              <div className="p-3.5 bg-slate-100 rounded-xl border border-border-color hover:border-slate-600 transition-all">
                <div className="text-[10px] uppercase font-bold text-text-muted tracking-wider">OCEL</div>
                <div className="text-xl font-black text-foreground mt-1">v{data.source_ocel_version}</div>
              </div>
              <div className="p-3.5 bg-slate-100 rounded-xl border border-border-color hover:border-slate-600 transition-all">
                <div className="text-[10px] uppercase font-bold text-text-muted tracking-wider">Conformance</div>
                <div className="text-xl font-black text-foreground mt-1">v{data.source_conformance_version}</div>
              </div>
              <div className="p-3.5 bg-slate-100 rounded-xl border border-border-color hover:border-slate-600 transition-all">
                <div className="text-[10px] uppercase font-bold text-text-muted tracking-wider">Carbon</div>
                <div className="text-xl font-black text-foreground mt-1">v{data.source_carbon_version}</div>
              </div>
              <div className="p-3.5 bg-slate-100 rounded-xl border border-border-color hover:border-slate-600 transition-all">
                <div className="text-[10px] uppercase font-bold text-text-muted tracking-wider">Interactions</div>
                <div className="text-xl font-black text-foreground mt-1">v{data.source_interaction_version}</div>
              </div>
              <div className="p-3.5 bg-slate-100 rounded-xl border border-border-color hover:border-slate-600 transition-all">
                <div className="text-[10px] uppercase font-bold text-text-muted tracking-wider">Simulation</div>
                <div className="text-xl font-black text-foreground mt-1">v{data.source_simulation_version}</div>
              </div>
              <div className="p-3.5 bg-slate-100 rounded-xl border border-border-color hover:border-slate-600 transition-all">
                <div className="text-[10px] uppercase font-bold text-text-muted tracking-wider">Interop</div>
                <div className="text-xl font-black text-foreground mt-1">v{data.source_interoperability_version}</div>
              </div>
              <div className="p-3.5 bg-slate-100 rounded-xl border border-border-color hover:border-slate-600 transition-all">
                <div className="text-[10px] uppercase font-bold text-text-muted tracking-wider">Fitness</div>
                <div className="text-xl font-black text-foreground mt-1">v{data.source_carbon_fitness_version}</div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 bg-slate-950 rounded-xl border border-border-color text-xs font-mono">
              <div className="flex-1 min-w-0">
                <div className="text-text-muted uppercase font-black tracking-wider text-[9px] mb-1">Snapshot SHA-256 Signature</div>
                <div className="text-blue-400 truncate font-semibold">{data.snapshot_hash}</div>
              </div>
              <div className="text-left sm:text-right shrink-0">
                <div className="text-text-muted uppercase font-black tracking-wider text-[9px] mb-1">Generated UTC</div>
                <div className="text-foreground">{new Date(data.snapshot_timestamp).toUTCString()}</div>
              </div>
            </div>
          </Card>

          {/* Charts Panel */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Unified Fitness & ESG Trends */}
            <Card className="p-6 bg-white border border-gray-100 shadow-sm">
              <h3 className="text-lg font-bold text-gray-800 mb-6 flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-blue-500" />
                Conformance & ESG Trend
              </h3>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                    <XAxis dataKey="version" stroke="#9CA3AF" />
                    <YAxis domain={[0, 1.0]} stroke="#9CA3AF" />
                    <Tooltip formatter={(value) => `${(Number(value) * 100).toFixed(0)}%`} />
                    <Legend />
                    <Line type="monotone" dataKey="Sustainability Conformance" stroke="#2563EB" strokeWidth={3} dot={{ r: 6 }} />
                    <Line type="monotone" dataKey="ESG Compliance" stroke="#10B981" strokeWidth={2.5} dot={{ r: 4 }} />
                    <Line type="monotone" dataKey="Process Fitness" stroke="#F59E0B" strokeWidth={2} dot={{ r: 4 }} />
                    <Line type="monotone" dataKey="Carbon Fitness" stroke="#8B5CF6" strokeWidth={2} dot={{ r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>

            {/* Severity Distribution */}
            <Card className="p-6 bg-white border border-gray-100 shadow-sm">
              <h3 className="text-lg font-bold text-gray-800 mb-6 flex items-center gap-2">
                <ShieldAlert className="h-5 w-5 text-red-500" />
                Deviation Severity Distribution
              </h3>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={deviationDistributionData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                    <XAxis dataKey="name" stroke="#9CA3AF" />
                    <YAxis stroke="#9CA3AF" />
                    <Tooltip />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {deviationDistributionData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>

          {/* Sustainability Deviations Catalog */}
          <Card className="p-6 bg-white border border-gray-100 shadow-sm overflow-hidden">
            <h3 className="text-lg font-bold text-gray-800 mb-6 flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-red-500 animate-pulse" />
              Sustainability Deviations Catalog
            </h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Type</th>
                    <th scope="col" className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Severity</th>
                    <th scope="col" className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Impact Score</th>
                    <th scope="col" className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Description</th>
                    <th scope="col" className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Recommended Action</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-150">
                  {data.deviations?.map((dev, i) => (
                    <tr key={i} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">{dev.type}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold ${
                          dev.severity === "CRITICAL"
                            ? "bg-purple-100 text-purple-800"
                            : dev.severity === "HIGH"
                            ? "bg-red-100 text-red-800"
                            : dev.severity === "MEDIUM"
                            ? "bg-yellow-100 text-yellow-800"
                            : "bg-blue-100 text-blue-800"
                        }`}>
                          {dev.severity}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 font-bold">
                        {dev.impact_score.toFixed(1)}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600 font-medium">{dev.description}</td>
                      <td className="px-6 py-4 text-sm text-slate-800 font-semibold">{dev.recommended_action}</td>
                    </tr>
                  ))}
                  {(!data.deviations || data.deviations.length === 0) && (
                    <tr>
                      <td colSpan={5} className="px-6 py-8 text-center text-sm font-semibold text-gray-500">
                        No deviations detected. Sustainability compliance is perfectly conforming!
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </Card>

          {/* History / Audit Log of Snapshots */}
          <Card className="p-6 bg-white border border-gray-100 shadow-sm">
            <h3 className="text-lg font-bold text-gray-800 mb-6 flex items-center gap-2">
              <Calendar className="h-5 w-5 text-gray-500" />
              Immutability Version History
            </h3>
            <div className="relative border-l border-gray-200 ml-4 pl-6 space-y-8">
              {history.map((h, i) => (
                <div key={h.sustainability_conformance_version} className="relative">
                  <div className="absolute -left-[31px] top-1.5 bg-white border-2 border-blue-600 rounded-full h-4 w-4"></div>
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                    <div>
                      <h4 className="text-sm font-bold text-gray-900 flex items-center gap-2">
                        Version {h.sustainability_conformance_version}
                        {i === 0 && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xxs font-bold bg-blue-100 text-blue-800">
                            Active
                          </span>
                        )}
                      </h4>
                      <p className="text-xs text-gray-500 font-mono mt-1">Hash: {h.snapshot_hash}</p>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-gray-500 font-semibold">
                        Timestamp: {new Date(h.snapshot_timestamp).toLocaleString()}
                      </div>
                      <div className="text-sm text-blue-600 font-bold mt-1">
                        Conformance: {(h.sustainability_conformance * 100).toFixed(0)}% | ESG: {h.esg_compliance_score.toFixed(0)}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
