"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "../../../context/AuthContext";
import { useCopilot } from "../../../context/CopilotContext";
import { Card } from "../../../components/Card";
import { Button } from "../../../components/Button";
import { api } from "../../../services/api";
import {
  Sparkles,
  Shield,
  TrendingUp,
  AlertTriangle,
  Layers,
  Database,
  ArrowRight,
  RefreshCw,
  Clock,
  Info
} from "lucide-react";

interface ObjectConformanceEntry {
  object_id: string;
  object_type: string;
  fitness_score: number;
  severity: string;
  deviation_count: number;
  lifecycle_length: number;
}

interface Deviation {
  object_id: string;
  deviation_type: string;
  expected: string | null;
  actual: string | null;
}

interface ObjectTypeSummary {
  count: number;
  average_fitness: number;
  critical_count: number;
}

interface ConformanceRun {
  object_conformance_version: number;
  object_conformance_run_id: string;
  snapshot_timestamp: string;
  object_count: number;
  average_fitness: number;
  critical_objects: number;
  high_objects: number;
  medium_objects: number;
  low_objects: number;
  object_type_summary: Record<string, ObjectTypeSummary>;
  worst_object_type: {
    object_type: string;
    average_fitness: number;
    critical_count: number;
  };
}

export default function ObjectConformancePage() {
  const { activeWorkspace } = useAuth();
  const { selectedAnalysisId } = useCopilot();

  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [latestData, setLatestData] = useState<any>(null);
  const [objects, setObjects] = useState<ObjectConformanceEntry[]>([]);
  const [deviations, setDeviations] = useState<Deviation[]>([]);
  const [history, setHistory] = useState<ConformanceRun[]>([]);
  const [worstObject, setWorstObject] = useState<any>(null);

  const loadData = useCallback(async (analysisId: string) => {
    setLoading(true);
    setError(null);
    try {
      // 1. Get latest conformance
      const latestRes = await api.get(`/api/v1/object-conformance/${analysisId}`);
      setLatestData(latestRes.data);

      // 2. Get worst object
      const worstRes = await api.get(`/api/v1/object-conformance/${analysisId}/worst`);
      setWorstObject(worstRes.data);

      // 3. Get history
      const historyRes = await api.get(`/api/v1/object-conformance/${analysisId}/history`);
      setHistory(historyRes.data);

      // 4. Get objects
      const objectsRes = await api.get(`/api/v1/object-conformance/${analysisId}/objects`);
      setObjects(objectsRes.data);

      // 5. Get deviations
      const deviationsRes = await api.get(`/api/v1/object-conformance/${analysisId}/deviations`);
      setDeviations(deviationsRes.data);
    } catch (err: any) {
      console.error(err);
      setError("Failed to load object conformance metrics.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedAnalysisId) {
      loadData(selectedAnalysisId);
    } else {
      setLatestData(null);
      setObjects([]);
      setDeviations([]);
      setHistory([]);
      setWorstObject(null);
    }
  }, [selectedAnalysisId, loadData]);

  const handleGenerate = async () => {
    if (!selectedAnalysisId) return;
    setGenerating(true);
    setError(null);
    try {
      await api.post(`/api/v1/object-conformance/${selectedAnalysisId}/generate`);
      await loadData(selectedAnalysisId);
    } catch (err: any) {
      console.error(err);
      setError("Error generating object conformance snapshot.");
    } finally {
      setGenerating(false);
    }
  };

  if (!selectedAnalysisId) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6">
        <Info className="w-16 h-16 text-gray-300 mb-4" />
        <h3 className="text-xl font-bold text-gray-800">No Analysis Selected</h3>
        <p className="text-gray-500 mt-2">Please select a Process Analysis in the Copilot pane to view Object-Centric Conformance.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
        <RefreshCw className="w-10 h-10 text-blue-500 animate-spin mb-4" />
        <p className="text-gray-500 font-medium">Loading object-centric conformance matrices...</p>
      </div>
    );
  }

  // Fallbacks if latestData is empty
  const totalObjects = latestData?.object_count || 0;
  const avgFitness = latestData?.average_fitness || 0;
  const criticalCount = latestData?.critical_objects || 0;
  const highRiskCount = latestData?.high_objects || 0;
  const mediumCount = latestData?.medium_objects || 0;
  const lowCount = latestData?.low_objects || 0;
  const worstType = latestData?.worst_object_type || {};
  const typeSummaries = latestData?.object_type_summary || {};

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-black text-gray-900 tracking-tight">Object-Centric Conformance Center</h1>
          <p className="text-sm text-gray-500 font-medium mt-1">
            Validate process compliance and detect execution anomalies at the object level.
          </p>
        </div>
        <Button onClick={handleGenerate} disabled={generating} className="flex items-center gap-2">
          {generating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          {generating ? "Generating..." : "Generate Snapshot"}
        </Button>
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-md text-sm font-semibold flex items-center gap-2 border border-red-200">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* KPI Overview Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4 flex flex-col justify-between">
          <div className="text-xs font-bold text-gray-500 uppercase tracking-wider">Total Objects</div>
          <div className="text-3xl font-black text-gray-900 mt-2">{totalObjects}</div>
          <div className="text-xs text-gray-400 mt-1">Cross-linked entities</div>
        </Card>
        <Card className="p-4 flex flex-col justify-between">
          <div className="text-xs font-bold text-gray-500 uppercase tracking-wider">Average Fitness</div>
          <div className="text-3xl font-black text-blue-600 mt-2">{(avgFitness * 100).toFixed(0)}%</div>
          <div className="text-xs text-gray-400 mt-1">LCS alignment ratio</div>
        </Card>
        <Card className="p-4 flex flex-col justify-between border-l-4 border-red-500">
          <div className="text-xs font-bold text-gray-500 uppercase tracking-wider">Critical Objects</div>
          <div className="text-3xl font-black text-red-600 mt-2">{criticalCount}</div>
          <div className="text-xs text-gray-400 mt-1">Fitness score &lt; 60%</div>
        </Card>
        <Card className="p-4 flex flex-col justify-between border-l-4 border-amber-500">
          <div className="text-xs font-bold text-gray-500 uppercase tracking-wider">High Risk Objects</div>
          <div className="text-3xl font-black text-amber-600 mt-2">{highRiskCount}</div>
          <div className="text-xs text-gray-400 mt-1">Fitness score &lt; 75%</div>
        </Card>
      </div>

      {/* Worst Performers Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Worst Performing Object Type */}
        <Card className="p-5 space-y-4">
          <div className="flex justify-between items-center border-b border-gray-100 pb-2">
            <h3 className="font-extrabold text-gray-900 text-base">Worst Performing Object Type</h3>
            <span className="bg-red-50 text-red-700 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider">
              {worstType.object_type ? "Critical" : "No Data"}
            </span>
          </div>
          {worstType.object_type ? (
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="bg-gray-50 p-3 rounded-md">
                <div className="text-xs text-gray-500 font-semibold">Object Type</div>
                <div className="text-lg font-black text-gray-800 mt-1">{worstType.object_type}</div>
              </div>
              <div className="bg-gray-50 p-3 rounded-md">
                <div className="text-xs text-gray-500 font-semibold">Average Fitness</div>
                <div className="text-lg font-black text-red-600 mt-1">{(worstType.average_fitness * 100).toFixed(0)}%</div>
              </div>
              <div className="bg-gray-50 p-3 rounded-md">
                <div className="text-xs text-gray-500 font-semibold">Critical Count</div>
                <div className="text-lg font-black text-gray-800 mt-1">{worstType.critical_count}</div>
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-500 italic">No worst object type metrics generated yet.</p>
          )}
        </Card>

        {/* Worst Performing Object */}
        <Card className="p-5 space-y-4">
          <div className="flex justify-between items-center border-b border-gray-100 pb-2">
            <h3 className="font-extrabold text-gray-900 text-base">Worst Performing Object</h3>
            <span className="bg-red-50 text-red-700 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider">
              {worstObject?.severity || "No Data"}
            </span>
          </div>
          {worstObject?.object_id ? (
            <div className="grid grid-cols-4 gap-4 text-center">
              <div className="bg-gray-50 p-3 rounded-md">
                <div className="text-xs text-gray-500 font-semibold">Object ID</div>
                <div className="text-sm font-black text-gray-800 mt-1">{worstObject.object_id}</div>
              </div>
              <div className="bg-gray-50 p-3 rounded-md">
                <div className="text-xs text-gray-500 font-semibold">Type</div>
                <div className="text-sm font-black text-gray-800 mt-1">{worstObject.object_type}</div>
              </div>
              <div className="bg-gray-50 p-3 rounded-md">
                <div className="text-xs text-gray-500 font-semibold">Fitness</div>
                <div className="text-sm font-black text-red-600 mt-1">{(worstObject.fitness_score * 100).toFixed(0)}%</div>
              </div>
              <div className="bg-gray-50 p-3 rounded-md">
                <div className="text-xs text-gray-500 font-semibold">Deviations</div>
                <div className="text-sm font-black text-gray-800 mt-1">{worstObject.deviation_count}</div>
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-500 italic">No worst object metrics generated yet.</p>
          )}
        </Card>
      </div>

      {/* Fitness Distribution & Object Type Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Fitness Distribution */}
        <Card className="p-5 space-y-4 col-span-1">
          <h3 className="font-extrabold text-gray-900 text-base border-b border-gray-100 pb-2">Fitness Distribution</h3>
          <div className="space-y-3">
            {[
              { label: "Low (>= 90%)", count: lowCount, color: "bg-emerald-500" },
              { label: "Medium (< 90%)", count: mediumCount, color: "bg-blue-500" },
              { label: "High (< 75%)", count: highRiskCount, color: "bg-amber-500" },
              { label: "Critical (< 60%)", count: criticalCount, color: "bg-red-500" }
            ].map((dist) => {
              const pct = totalObjects > 0 ? (dist.count / totalObjects) * 100 : 0;
              return (
                <div key={dist.label} className="space-y-1">
                  <div className="flex justify-between text-xs font-semibold text-gray-600">
                    <span>{dist.label}</span>
                    <span>{dist.count} ({pct.toFixed(0)}%)</span>
                  </div>
                  <div className="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
                    <div className={`${dist.color} h-2`} style={{ width: `${pct}%` }}></div>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        {/* Object Type Summary Table */}
        <Card className="p-5 space-y-4 col-span-2">
          <h3 className="font-extrabold text-gray-900 text-base border-b border-gray-100 pb-2">Object Type Summary</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-gray-500">
              <thead className="text-xs uppercase bg-gray-50 text-gray-700 font-extrabold border-b border-gray-200">
                <tr>
                  <th className="px-4 py-2">Object Type</th>
                  <th className="px-4 py-2">Total Count</th>
                  <th className="px-4 py-2">Avg Fitness</th>
                  <th className="px-4 py-2">Critical Count</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(typeSummaries).map(([type, summary]: [string, any]) => (
                  <tr key={type} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="px-4 py-2.5 font-bold text-gray-800">{type}</td>
                    <td className="px-4 py-2.5">{summary.count}</td>
                    <td className="px-4 py-2.5 font-extrabold text-blue-600">{(summary.average_fitness * 100).toFixed(0)}%</td>
                    <td className="px-4 py-2.5 font-bold text-red-600">{summary.critical_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* Main Tables Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Objects Fitness Table */}
        <Card className="p-5 space-y-4">
          <h3 className="font-extrabold text-gray-900 text-base border-b border-gray-100 pb-2">Individual Object Fitness</h3>
          <div className="overflow-x-auto max-h-[350px] overflow-y-auto">
            <table className="w-full text-left text-sm text-gray-500">
              <thead className="text-xs uppercase bg-gray-50 text-gray-700 font-bold border-b border-gray-200 sticky top-0">
                <tr>
                  <th className="px-4 py-2">Object ID</th>
                  <th className="px-4 py-2">Type</th>
                  <th className="px-4 py-2">Fitness</th>
                  <th className="px-4 py-2">Severity</th>
                  <th className="px-4 py-2">Lifecycle Length</th>
                </tr>
              </thead>
              <tbody>
                {objects.map((obj) => (
                  <tr key={obj.object_id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="px-4 py-2.5 font-mono text-xs text-gray-800">{obj.object_id}</td>
                    <td className="px-4 py-2.5 font-semibold text-gray-700">{obj.object_type}</td>
                    <td className="px-4 py-2.5 font-extrabold text-blue-600">{(obj.fitness_score * 100).toFixed(0)}%</td>
                    <td className="px-4 py-2.5">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                        obj.severity === "Critical" ? "bg-red-50 text-red-700" :
                        obj.severity === "High" ? "bg-amber-50 text-amber-700" :
                        obj.severity === "Medium" ? "bg-blue-50 text-blue-700" :
                        "bg-emerald-50 text-emerald-700"
                      }`}>
                        {obj.severity}
                      </span>
                    </td>
                    <td className="px-4 py-2.5">{obj.lifecycle_length}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Deviations Table */}
        <Card className="p-5 space-y-4">
          <h3 className="font-extrabold text-gray-900 text-base border-b border-gray-100 pb-2">Process Deviations</h3>
          <div className="overflow-x-auto max-h-[350px] overflow-y-auto">
            <table className="w-full text-left text-sm text-gray-500">
              <thead className="text-xs uppercase bg-gray-50 text-gray-700 font-bold border-b border-gray-200 sticky top-0">
                <tr>
                  <th className="px-4 py-2">Object ID</th>
                  <th className="px-4 py-2">Deviation Type</th>
                  <th className="px-4 py-2">Expected Activity</th>
                  <th className="px-4 py-2">Actual Activity</th>
                </tr>
              </thead>
              <tbody>
                {deviations.map((dev, idx) => (
                  <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="px-4 py-2.5 font-mono text-xs text-gray-800">{dev.object_id}</td>
                    <td className="px-4 py-2.5 font-bold text-red-600">{dev.deviation_type}</td>
                    <td className="px-4 py-2.5 font-semibold text-gray-700">{dev.expected || "-"}</td>
                    <td className="px-4 py-2.5 font-semibold text-gray-700">{dev.actual || "-"}</td>
                  </tr>
                ))}
                {deviations.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-4 py-6 text-center text-sm text-emerald-600 font-bold italic">
                      No process compliance deviations found. All paths are fully compliant!
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* Snapshot Run History */}
      <Card className="p-5 space-y-4">
        <h3 className="font-extrabold text-gray-900 text-base border-b border-gray-100 pb-2">Snapshot Run History</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-gray-500">
            <thead className="text-xs uppercase bg-gray-50 text-gray-700 font-bold border-b border-gray-200">
              <tr>
                <th className="px-4 py-2">Version</th>
                <th className="px-4 py-2">Run ID</th>
                <th className="px-4 py-2">Generated At</th>
                <th className="px-4 py-2">Total Objects</th>
                <th className="px-4 py-2">Average Fitness</th>
                <th className="px-4 py-2">Critical Objects</th>
              </tr>
            </thead>
            <tbody>
              {history.map((run) => (
                <tr key={run.object_conformance_version} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-4 py-2.5 font-bold text-gray-800">Version {run.object_conformance_version}</td>
                  <td className="px-4 py-2.5 font-mono text-xs text-gray-500">{run.object_conformance_run_id}</td>
                  <td className="px-4 py-2.5">{new Date(run.snapshot_timestamp).toLocaleString()}</td>
                  <td className="px-4 py-2.5 font-semibold text-gray-700">{run.object_count}</td>
                  <td className="px-4 py-2.5 font-bold text-blue-600">{(run.average_fitness * 100).toFixed(0)}%</td>
                  <td className="px-4 py-2.5 font-bold text-red-600">{run.critical_objects}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
