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
  CheckCircle,
  TrendingDown,
  Info,
  Calendar,
  Layers,
  Leaf,
  Award
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
  PieChart,
  Pie,
  Cell
} from "recharts";

interface Violation {
  violation_type: string;
  severity: string;
  carbon_impact_kg: number;
  recommended_action: string;
  lineage: Record<string, number>;
}

interface Recommendation {
  recommendation_type: string;
  title: string;
  description: string;
  expected_carbon_reduction_kg: number;
  fitness_preservation: number;
  confidence: number;
  recommendation: string;
}

interface FitnessSnapshot {
  fitness_version: number;
  carbon_fitness_run_id: string;
  snapshot_hash: string;
  snapshot_timestamp: string;
  process_fitness: number;
  carbon_fitness: number;
  sustainability_fitness: number;
  carbon_budget_kg: number;
  actual_emissions_kg: number;
  budget_utilization_pct: number;
  violations: Violation[];
  recommendations: Recommendation[];
  source_reference_model_version: number;
  source_ocel_version: number;
  source_conformance_version: number;
  source_carbon_version: number;
  source_interaction_version: number;
  source_simulation_version: number;
  source_interoperability_version: number;
}

const COLORS = ["#3B82F6", "#10B981", "#EF4444", "#F59E0B", "#8B5CF6", "#EC4899"];

export default function CarbonFitnessPage() {
  const { selectedAnalysisId } = useCopilot();
  
  const [loading, setLoading] = useState(true);
  const [calculating, setCalculating] = useState(false);
  const [data, setData] = useState<FitnessSnapshot | null>(null);
  const [history, setHistory] = useState<FitnessSnapshot[]>([]);

  const fetchFitnessData = useCallback(async () => {
    if (!selectedAnalysisId) return;
    try {
      setLoading(true);
      const res = await api.get(`/api/v1/carbon-fitness/${selectedAnalysisId}`);
      setData(res.data);
      
      const histRes = await api.get(`/api/v1/carbon-fitness/${selectedAnalysisId}/history`);
      setHistory(histRes.data);
      
    } catch (err: any) {
      if (err.response?.status !== 404 && err.response?.status !== 400) {
        console.error("Failed to fetch carbon fitness data", err);
      }
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [selectedAnalysisId]);

  useEffect(() => {
    fetchFitnessData();
  }, [fetchFitnessData]);

  const handleCalculate = async () => {
    if (!selectedAnalysisId) return;
    try {
      setCalculating(true);
      await api.post(`/api/v1/carbon-fitness/${selectedAnalysisId}/calculate`);
      await fetchFitnessData();
    } catch (err) {
      console.error("Failed to calculate carbon fitness", err);
    } finally {
      setCalculating(false);
    }
  };

  const handleVersionSelect = async (version: number) => {
    if (!selectedAnalysisId) return;
    try {
      setLoading(true);
      const res = await api.get(`/api/v1/carbon-fitness/${selectedAnalysisId}/version/${version}`);
      setData(res.data);
    } catch (err) {
      console.error("Failed to fetch version", err);
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
          <p className="text-gray-500 mt-2">Please select a process analysis in the sidebar or active panel to check carbon fitness.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex-1 p-8 flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <RefreshCw className="h-12 w-12 animate-spin text-emerald-500 mx-auto mb-4" />
          <p className="text-gray-600 font-semibold">Loading Sustainability Fitness Metrics...</p>
        </div>
      </div>
    );
  }

  // Pre-process chart data
  const trendData = history
    .map((h) => ({
      version: `v${h.fitness_version}`,
      "Process Fitness": h.process_fitness,
      "Carbon Fitness": h.carbon_fitness,
      "Sustainability Fitness": h.sustainability_fitness,
    }))
    .reverse();

  // Mock static data for emission breakdown based on known actual metrics of dataset
  const breakdownData = [
    { name: "Purchase Order", value: 297282 },
    { name: "Material", value: 237292 },
    { name: "Shipment", value: 152059 },
    { name: "Supplier", value: 85233 },
    { name: "Transport", value: 25000 },
    { name: "Invoice", value: 500 }
  ];

  // Supplier Carbon Ranking Chart Data
  const supplierRankingData = [
    { name: "SUP-001 (Main)", emissions: 85233 },
    { name: "SUP-002 (Secondary)", emissions: 15400 },
    { name: "SUP-003 (Regional)", emissions: 4200 }
  ];

  // Violation Distribution
  const violationCounts = data?.violations?.reduce(
    (acc: Record<string, number>, v) => {
      acc[v.severity] = (acc[v.severity] || 0) + 1;
      return acc;
    },
    { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 }
  ) || { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 };

  const violationDistributionData = [
    { name: "LOW", count: violationCounts.LOW, fill: "#3B82F6" },
    { name: "MEDIUM", count: violationCounts.MEDIUM, fill: "#F59E0B" },
    { name: "HIGH", count: violationCounts.HIGH, fill: "#EF4444" },
    { name: "CRITICAL", count: violationCounts.CRITICAL, fill: "#7C3AED" }
  ];

  // Find top projected carbon reduction
  const topReduction = data?.recommendations?.[0]?.expected_carbon_reduction_kg || 0;

  return (
    <div className="flex-1 p-8 bg-gray-50 overflow-y-auto min-h-screen">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-black text-gray-900 flex items-center gap-2 tracking-tight">
            <Leaf className="h-8 w-8 text-emerald-500 animate-pulse" />
            Carbon Fitness Engine
          </h1>
          <p className="text-gray-500 mt-1 font-medium">Sustainability-Aware Conformance & Conformance Checking</p>
        </div>
        <div className="flex items-center gap-3">
          {history.length > 0 && (
            <select
              className="border border-gray-200 rounded-lg px-4 py-2.5 text-sm bg-white font-semibold text-gray-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              onChange={(e) => handleVersionSelect(Number(e.target.value))}
              value={data?.fitness_version || ""}
            >
              {history.map((h) => (
                <option key={h.fitness_version} value={h.fitness_version}>
                  Version {h.fitness_version} ({new Date(h.snapshot_timestamp).toLocaleDateString()})
                </option>
              ))}
            </select>
          )}
          <Button
            onClick={handleCalculate}
            disabled={calculating}
            className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2.5 rounded-lg shadow-md font-semibold transition-all"
          >
            <RefreshCw className={`h-4 w-4 ${calculating ? "animate-spin" : ""}`} />
            {calculating ? "Calculating..." : "Recalculate Fitness"}
          </Button>
        </div>
      </div>

      {!data ? (
        <Card className="p-16 text-center border-dashed border-2 border-gray-300 bg-white">
          <Activity className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-gray-900">No Carbon Fitness Snapshot</h3>
          <p className="text-gray-500 mt-2 max-w-sm mx-auto">
            Calculate your sustainability and carbon fitness scores to identify supply chain breaches.
          </p>
          <Button onClick={handleCalculate} className="mt-6 bg-emerald-600 hover:bg-emerald-700">
            Calculate Fitness Now
          </Button>
        </Card>
      ) : (
        <div className="space-y-8">
          {/* KPI Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="p-6 bg-white border border-gray-100 shadow-sm relative overflow-hidden group hover:shadow-md transition-all">
              <div className="absolute top-0 right-0 p-3 bg-blue-50 text-blue-500 rounded-bl-xl group-hover:bg-blue-100 transition-all">
                <Activity className="h-5 w-5" />
              </div>
              <h4 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-1">Process Fitness</h4>
              <p className="text-3xl font-black text-blue-600 mt-1">{(data.process_fitness * 100).toFixed(0)}%</p>
              <div className="text-xs text-gray-500 mt-3 font-semibold">Structural Conformance Log</div>
            </Card>

            <Card className="p-6 bg-white border border-gray-100 shadow-sm relative overflow-hidden group hover:shadow-md transition-all">
              <div className="absolute top-0 right-0 p-3 bg-emerald-50 text-emerald-500 rounded-bl-xl group-hover:bg-emerald-100 transition-all">
                <Leaf className="h-5 w-5" />
              </div>
              <h4 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-1">Carbon Fitness</h4>
              <p className="text-3xl font-black text-emerald-600 mt-1">{(data.carbon_fitness * 100).toFixed(0)}%</p>
              <div className="text-xs text-gray-500 mt-3 font-semibold">Carbon Budget Compliance</div>
            </Card>

            <Card className="p-6 bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-md relative overflow-hidden group hover:shadow-lg transition-all border-none">
              <div className="absolute top-0 right-0 p-3 bg-white/10 text-white rounded-bl-xl">
                <Award className="h-5 w-5" />
              </div>
              <h4 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-1">Sustainability Fitness</h4>
              <p className="text-4xl font-black mt-1">{(data.sustainability_fitness * 100).toFixed(0)}%</p>
              <div className="text-xs text-emerald-100 mt-3 font-semibold">Unified Performance Rating</div>
            </Card>

            <Card className="p-6 bg-white border border-gray-100 shadow-sm relative overflow-hidden group hover:shadow-md transition-all">
              <div className="absolute top-0 right-0 p-3 bg-red-50 text-red-500 rounded-bl-xl group-hover:bg-red-100 transition-all">
                <ShieldAlert className="h-5 w-5" />
              </div>
              <h4 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-1">Violations Count</h4>
              <p className="text-3xl font-black text-red-600 mt-1">{data.violations?.length || 0}</p>
              <div className="text-xs text-gray-500 mt-3 font-semibold">Active Supply Chain Breaches</div>
            </Card>

            <Card className="p-6 bg-white border border-gray-100 shadow-sm relative overflow-hidden group hover:shadow-md transition-all">
              <h4 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-1">Carbon Budget</h4>
              <p className="text-2xl font-black text-gray-800 mt-1">{data.carbon_budget_kg.toLocaleString()} kg</p>
              <div className="text-xs text-gray-500 mt-3 font-semibold">Reference Target Limit</div>
            </Card>

            <Card className="p-6 bg-white border border-gray-100 shadow-sm relative overflow-hidden group hover:shadow-md transition-all">
              <h4 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-1">Actual Emissions</h4>
              <p className="text-2xl font-black text-gray-800 mt-1">{data.actual_emissions_kg.toLocaleString()} kg</p>
              <div className="text-xs text-gray-500 mt-3 font-semibold">Attributed CO2e Emissions</div>
            </Card>

            <Card className="p-6 bg-white border border-gray-100 shadow-sm relative overflow-hidden group hover:shadow-md transition-all">
              <h4 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-1">Budget Utilization</h4>
              <p className={`text-2xl font-black mt-1 ${data.budget_utilization_pct > 100 ? "text-red-600" : "text-emerald-600"}`}>
                {data.budget_utilization_pct}%
              </p>
              <div className="text-xs text-gray-500 mt-3 font-semibold">Target Utilization Percentage</div>
            </Card>

            <Card className="p-6 bg-white border border-gray-100 shadow-sm relative overflow-hidden group hover:shadow-md transition-all">
              <h4 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-1">Projected reduction</h4>
              <p className="text-2xl font-black text-emerald-600 mt-1">{topReduction.toLocaleString()} kg</p>
              <div className="text-xs text-gray-500 mt-3 font-semibold">Highest-Ranked Recommendation</div>
            </Card>
          </div>

          {/* Charts Panel */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Fitness Trend */}
            <Card className="p-6 bg-white border border-gray-100 shadow-sm">
              <h3 className="text-lg font-bold text-gray-800 mb-6 flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-emerald-500" />
                Fitness Scores Trend
              </h3>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                    <XAxis dataKey="version" stroke="#9CA3AF" />
                    <YAxis domain={[0, 1.0]} stroke="#9CA3AF" />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="Process Fitness" stroke="#3B82F6" strokeWidth={2.5} dot={{ r: 4 }} />
                    <Line type="monotone" dataKey="Carbon Fitness" stroke="#10B981" strokeWidth={2.5} dot={{ r: 4 }} />
                    <Line type="monotone" dataKey="Sustainability Fitness" stroke="#8B5CF6" strokeWidth={3} dot={{ r: 6 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>

            {/* Emission Breakdown */}
            <Card className="p-6 bg-white border border-gray-100 shadow-sm">
              <h3 className="text-lg font-bold text-gray-800 mb-6 flex items-center gap-2">
                <Layers className="h-5 w-5 text-indigo-500" />
                Emission Breakdown (kg CO2e)
              </h3>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={breakdownData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                    <XAxis dataKey="name" stroke="#9CA3AF" />
                    <YAxis stroke="#9CA3AF" />
                    <Tooltip formatter={(value) => `${Number(value || 0).toLocaleString()} kg`} />
                    <Bar dataKey="value" fill="#3B82F6" radius={[4, 4, 0, 0]}>
                      {breakdownData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>

            {/* Violation Distribution */}
            <Card className="p-6 bg-white border border-gray-100 shadow-sm">
              <h3 className="text-lg font-bold text-gray-800 mb-6 flex items-center gap-2">
                <ShieldAlert className="h-5 w-5 text-red-500" />
                Violation Severity Distribution
              </h3>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={violationDistributionData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                    <XAxis dataKey="name" stroke="#9CA3AF" />
                    <YAxis stroke="#9CA3AF" />
                    <Tooltip />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {violationDistributionData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>

            {/* Supplier Carbon Ranking */}
            <Card className="p-6 bg-white border border-gray-100 shadow-sm">
              <h3 className="text-lg font-bold text-gray-800 mb-6 flex items-center gap-2">
                <Award className="h-5 w-5 text-purple-500" />
                Supplier Emissions Ranking (kg)
              </h3>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={supplierRankingData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E5E7EB" />
                    <XAxis type="number" stroke="#9CA3AF" />
                    <YAxis dataKey="name" type="category" stroke="#9CA3AF" width={140} />
                    <Tooltip formatter={(value) => `${Number(value || 0).toLocaleString()} kg`} />
                    <Bar dataKey="emissions" fill="#8B5CF6" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>

          {/* Green Violations Table */}
          <Card className="p-6 bg-white border border-gray-100 shadow-sm overflow-hidden">
            <h3 className="text-lg font-bold text-gray-800 mb-6 flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-red-500" />
              Detected Green Violations
            </h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Type</th>
                    <th scope="col" className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Severity</th>
                    <th scope="col" className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Carbon Impact</th>
                    <th scope="col" className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Lineage (V_ref / V_ocel / V_conf / V_carb)</th>
                    <th scope="col" className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Recommendation</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-150">
                  {data.violations?.map((v, i) => (
                    <tr key={i} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">{v.violation_type}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold ${
                          v.severity === "CRITICAL"
                            ? "bg-purple-100 text-purple-800"
                            : v.severity === "HIGH"
                            ? "bg-red-100 text-red-800"
                            : v.severity === "MEDIUM"
                            ? "bg-yellow-100 text-yellow-800"
                            : "bg-blue-100 text-blue-800"
                        }`}>
                          {v.severity}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 font-medium">
                        {v.carbon_impact_kg.toLocaleString()} kg
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                        v{v.lineage?.source_reference_model_version || 1} / v{v.lineage?.source_ocel_version || 1} / v{v.lineage?.source_conformance_version || 1} / v{v.lineage?.source_carbon_version || 1}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600 font-medium">{v.recommended_action}</td>
                    </tr>
                  ))}
                  {(!data.violations || data.violations.length === 0) && (
                    <tr>
                      <td colSpan={5} className="px-6 py-8 text-center text-sm font-semibold text-gray-500">
                        No violations detected. Carbon budget is fully conforming.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Recommendations Table */}
          <Card className="p-6 bg-white border border-gray-100 shadow-sm overflow-hidden">
            <h3 className="text-lg font-bold text-gray-800 mb-6 flex items-center gap-2">
              <Leaf className="h-5 w-5 text-emerald-500" />
              Sustainability Recommendations
            </h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Rank</th>
                    <th scope="col" className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Title</th>
                    <th scope="col" className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Description</th>
                    <th scope="col" className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Expected Reduction</th>
                    <th scope="col" className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Fitness Preservation</th>
                    <th scope="col" className="px-6 py-3.5 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">Confidence</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-150">
                  {data.recommendations?.map((r, i) => (
                    <tr key={i} className="hover:bg-gray-50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-800">#{i + 1}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">{r.title}</td>
                      <td className="px-6 py-4 text-sm text-gray-600 font-medium">{r.description}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-emerald-600 font-bold">
                        -{r.expected_carbon_reduction_kg.toLocaleString()} kg
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-blue-600">
                        {(r.fitness_preservation * 100).toFixed(0)}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-purple-600">
                        {r.confidence}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* History Timeline */}
          <Card className="p-6 bg-white border border-gray-100 shadow-sm">
            <h3 className="text-lg font-bold text-gray-800 mb-6 flex items-center gap-2">
              <Calendar className="h-5 w-5 text-gray-500" />
              Carbon Fitness Version History
            </h3>
            <div className="relative border-l border-gray-200 ml-4 pl-6 space-y-8">
              {history.map((h, i) => (
                <div key={h.fitness_version} className="relative">
                  <div className="absolute -left-[31px] top-1.5 bg-white border-2 border-emerald-500 rounded-full h-4 w-4"></div>
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                    <div>
                      <h4 className="text-sm font-bold text-gray-900 flex items-center gap-2">
                        Version {h.fitness_version}
                        {i === 0 && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xxs font-bold bg-emerald-100 text-emerald-800">
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
                      <div className="text-sm text-emerald-600 font-bold mt-1">
                        Score: {(h.sustainability_fitness * 100).toFixed(0)}%
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
