"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "../../../context/AuthContext";
import { useCopilot } from "../../../context/CopilotContext";
import { Card } from "../../../components/Card";
import { Button } from "../../../components/Button";
import { api } from "../../../services/api";
import {
  Sparkles,
  AlertTriangle,
  Layers,
  Database,
  RefreshCw,
  Clock,
  Info,
  Leaf,
  Flame,
  User
} from "lucide-react";

interface ObjectCarbonEntry {
  object_id: string;
  object_type: string;
  emissions: number;
  event_count: number;
  severity: string;
  contribution_percentage: number;
  top_emission_events: Array<{
    event_name: string;
    emissions_kg: number;
  }>;
  carbon_reasoning: string;
}

interface Hotspot {
  object_id: string;
  object_type: string;
  total_emissions_kg: number;
  contribution_percentage: number;
  severity: string;
}

interface CarbonRun {
  object_carbon_version: number;
  object_carbon_run_id: string;
  source_ocel_version: number;
  source_carbon_version: number;
  snapshot_timestamp: string;
  total_object_emissions: number;
  critical_objects: number;
  high_objects: number;
}

export default function ObjectCarbonPage() {
  const { activeWorkspace } = useAuth();
  const { selectedAnalysisId } = useCopilot();

  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [latestData, setLatestData] = useState<any>(null);
  const [objects, setObjects] = useState<ObjectCarbonEntry[]>([]);
  const [hotspots, setHotspots] = useState<Hotspot[]>([]);
  const [history, setHistory] = useState<CarbonRun[]>([]);
  const [worstObject, setWorstObject] = useState<any>(null);
  const [selectedObject, setSelectedObject] = useState<ObjectCarbonEntry | null>(null);

  const loadData = useCallback(async (analysisId: string) => {
    setLoading(true);
    setError(null);
    try {
      // 1. Get latest carbon attribution
      const latestRes = await api.get(`/api/v1/object-carbon/${analysisId}`);
      setLatestData(latestRes.data);

      // 2. Get worst performing carbon object
      const worstRes = await api.get(`/api/v1/object-carbon/${analysisId}/worst`);
      setWorstObject(worstRes.data);

      // 3. Get history
      const historyRes = await api.get(`/api/v1/object-carbon/${analysisId}/history`);
      setHistory(historyRes.data);

      // 4. Get objects
      const objectsRes = await api.get(`/api/v1/object-carbon/${analysisId}/objects`);
      const objsData = objectsRes.data;
      setObjects(objsData);

      // Set default selected object to the first one or worst one
      if (objsData && objsData.length > 0) {
        setSelectedObject(objsData[0]);
      } else {
        setSelectedObject(null);
      }

      // 5. Get hotspots
      const hotspotsRes = await api.get(`/api/v1/object-carbon/${analysisId}/hotspots`);
      setHotspots(hotspotsRes.data);
    } catch (err: any) {
      console.error(err);
      setError("Failed to load object-centric carbon attribution metrics.");
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
      setHotspots([]);
      setHistory([]);
      setWorstObject(null);
      setSelectedObject(null);
    }
  }, [selectedAnalysisId, loadData]);

  const handleGenerate = async () => {
    if (!selectedAnalysisId) return;
    setGenerating(true);
    setError(null);
    try {
      await api.post(`/api/v1/object-carbon/${selectedAnalysisId}/generate`);
      await loadData(selectedAnalysisId);
    } catch (err: any) {
      console.error(err);
      setError("Error generating object carbon attribution snapshot.");
    } finally {
      setGenerating(false);
    }
  };

  if (!selectedAnalysisId) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6">
        <Info className="w-16 h-16 text-gray-300 mb-4" />
        <h3 className="text-xl font-bold text-gray-800">No Analysis Selected</h3>
        <p className="text-gray-500 mt-2">Please select a Process Analysis in the Copilot pane to view Object-Centric Carbon Attribution.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
        <RefreshCw className="w-10 h-10 text-emerald-500 animate-spin mb-4" />
        <p className="text-gray-500 font-medium">Loading object-centric carbon attribution profiles...</p>
      </div>
    );
  }

  // Fallbacks if latestData is empty
  const totalEmissions = latestData?.total_object_emissions || 0;
  const worstType = latestData?.worst_object_type || {};

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-black text-gray-900 tracking-tight flex items-center gap-2">
            <Leaf className="w-7 h-7 text-emerald-600" /> Object-Centric Carbon Attribution
          </h1>
          <p className="text-sm text-gray-500 font-medium mt-1">
            Analyze and trace carbon footprint contribution profiles down to individual process objects.
          </p>
        </div>
        <Button onClick={handleGenerate} disabled={generating} className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white border-0">
          {generating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          {generating ? "Attributing..." : "Calculate Carbon"}
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
        {/* Total Object Emissions */}
        <Card className="p-4 flex flex-col justify-between bg-white border border-gray-100 shadow-sm">
          <div className="text-xs font-bold text-gray-500 uppercase tracking-wider">Total Object Emissions</div>
          <div className="text-2xl font-black text-gray-900 mt-2">{totalEmissions.toLocaleString()} kg CO₂e</div>
          <div className="text-xs text-emerald-600 mt-1 font-semibold">Attributed Footprint</div>
        </Card>

        {/* Critical Hotspots */}
        <Card className="p-4 flex flex-col justify-between border-l-4 border-red-500 bg-white shadow-sm">
          <div className="text-xs font-bold text-gray-500 uppercase tracking-wider">Critical Hotspots</div>
          <div className="text-2xl font-black text-red-600 mt-2">{hotspots.length}</div>
          <div className="text-xs text-gray-400 mt-1">&ge; 15% contribution</div>
        </Card>

        {/* Worst Carbon Object */}
        <Card className="p-4 flex flex-col justify-between border-l-4 border-orange-500 bg-white shadow-sm">
          <div className="text-xs font-bold text-gray-500 uppercase tracking-wider">Worst Carbon Object</div>
          <div className="text-xl font-black text-orange-600 mt-2 truncate" title={worstObject?.object_id}>
            {worstObject?.object_id || "N/A"}
          </div>
          <div className="text-xs text-gray-400 mt-1">
            {worstObject?.emissions ? `${worstObject.emissions.toLocaleString()} kg` : "No emissions"}
          </div>
        </Card>

        {/* Worst Carbon Object Type */}
        <Card className="p-4 flex flex-col justify-between bg-white border border-gray-100 shadow-sm">
          <div className="text-xs font-bold text-gray-500 uppercase tracking-wider">Worst Carbon Object Type</div>
          <div className="text-xl font-black text-blue-600 mt-2 truncate" title={worstType?.object_type}>
            {worstType?.object_type || "N/A"}
          </div>
          <div className="text-xs text-gray-400 mt-1">
            {worstType?.average_emissions ? `${worstType.average_emissions.toLocaleString()} kg avg` : "No emissions"}
          </div>
        </Card>
      </div>

      {/* Main Inventory & Details Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Table Column */}
        <Card className="p-6 bg-white border border-gray-100 shadow-sm lg:col-span-2">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-black text-gray-900 tracking-tight">Object Emissions Inventory</h2>
            <span className="text-xs bg-emerald-50 text-emerald-800 font-bold px-3 py-1 rounded-full flex items-center gap-1">
              <Database className="w-3.5 h-3.5" /> Total {objects.length} entities
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-gray-400 font-bold uppercase text-[11px] tracking-wider">
                  <th className="pb-3">Object ID</th>
                  <th className="pb-3">Type</th>
                  <th className="pb-3">Total Emissions (kg CO₂e)</th>
                  <th className="pb-3">Contribution Percentage (%)</th>
                  <th className="pb-3">Severity</th>
                  <th className="pb-3">Event Count</th>
                </tr>
              </thead>
              <tbody>
                {objects.map((obj) => (
                  <tr
                    key={obj.object_id}
                    onClick={() => setSelectedObject(obj)}
                    className={`border-b border-gray-50 hover:bg-gray-50/80 transition duration-150 cursor-pointer ${
                      selectedObject?.object_id === obj.object_id ? "bg-emerald-50/40 hover:bg-emerald-50/50" : ""
                    }`}
                  >
                    <td className="py-4 font-black text-gray-900">{obj.object_id}</td>
                    <td className="py-4 text-gray-500 font-medium">{obj.object_type}</td>
                    <td className="py-4 text-emerald-700 font-bold">{obj.emissions.toLocaleString()} kg</td>
                    <td className="py-4 text-gray-600 font-medium">{obj.contribution_percentage}%</td>
                    <td className="py-4">
                      <span className={`px-2 py-0.5 rounded text-[11px] font-bold uppercase ${
                        obj.severity === "Critical" ? "bg-red-50 text-red-700 border border-red-200" :
                        obj.severity === "High" ? "bg-orange-50 text-orange-700 border border-orange-200" :
                        obj.severity === "Medium" ? "bg-amber-50 text-amber-700 border border-amber-200" :
                        "bg-emerald-50 text-emerald-700 border border-emerald-200"
                      }`}>
                        {obj.severity}
                      </span>
                    </td>
                    <td className="py-4 text-gray-500 font-semibold">{obj.event_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Details Panel Column */}
        <Card className="p-6 bg-white border border-gray-100 shadow-sm lg:col-span-1 flex flex-col justify-between min-h-[400px]">
          {selectedObject ? (
            <div className="space-y-6">
              <div className="border-b border-gray-100 pb-4">
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                  selectedObject.severity === "Critical" ? "bg-red-100 text-red-800" :
                  selectedObject.severity === "High" ? "bg-orange-100 text-orange-800" :
                  selectedObject.severity === "Medium" ? "bg-amber-100 text-amber-800" :
                  "bg-emerald-100 text-emerald-800"
                }`}>
                  {selectedObject.severity} Hotspot
                </span>
                <h3 className="text-2xl font-black text-gray-900 mt-2">{selectedObject.object_id}</h3>
                <p className="text-xs text-gray-400 mt-0.5 uppercase font-bold tracking-wider">{selectedObject.object_type}</p>
              </div>

              {/* Object Details */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-50/60 p-3 rounded-lg border border-gray-100">
                  <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Total Emissions</div>
                  <div className="text-base font-black text-gray-800 mt-1">{selectedObject.emissions.toLocaleString()} kg</div>
                </div>
                <div className="bg-gray-50/60 p-3 rounded-lg border border-gray-100">
                  <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Contribution</div>
                  <div className="text-base font-black text-gray-800 mt-1">{selectedObject.contribution_percentage}%</div>
                </div>
                <div className="bg-gray-50/60 p-3 rounded-lg border border-gray-100 col-span-2">
                  <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Lifecycle Events</div>
                  <div className="text-base font-black text-gray-800 mt-1">{selectedObject.event_count} actions</div>
                </div>
              </div>

              {/* Top Emission Events */}
              <div>
                <h4 className="font-extrabold text-gray-700 text-xs uppercase tracking-wider mb-2">Top Emission Events</h4>
                {selectedObject.top_emission_events && selectedObject.top_emission_events.length > 0 ? (
                  <ul className="space-y-1.5 pl-1">
                    {selectedObject.top_emission_events.map((ev, index) => (
                      <li key={index} className="flex justify-between items-center text-xs text-gray-600 font-medium">
                        <span className="flex items-center gap-1.5">
                          <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></span>
                          {ev.event_name}
                        </span>
                        <span className="font-bold text-gray-800">{ev.emissions_kg.toLocaleString()} kg</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-xs text-gray-400 italic">No event emissions recorded.</p>
                )}
              </div>

              {/* Carbon Reasoning */}
              <div className="pt-2">
                <h4 className="font-extrabold text-gray-700 text-xs uppercase tracking-wider mb-2">Carbon Reasoning</h4>
                <div className="bg-emerald-50/60 border border-emerald-100/50 p-3 rounded-lg text-emerald-800 text-xs font-semibold leading-relaxed">
                  "{selectedObject.carbon_reasoning}"
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center text-gray-400 py-10 my-auto">
              <Info className="w-12 h-12 mb-3 text-gray-300" />
              <h3 className="font-bold text-gray-700">No Object Selected</h3>
              <p className="text-xs text-gray-400 mt-1 max-w-[200px] mx-auto">
                Select an object from the inventory to inspect detailed carbon attribution and explainability.
              </p>
            </div>
          )}
        </Card>
      </div>

      {/* Hotspots Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="p-6 md:col-span-2 bg-white shadow-sm border border-gray-100">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-black text-gray-900 tracking-tight flex items-center gap-2">
              <Flame className="w-5 h-5 text-red-600 animate-pulse" /> Active Carbon Hotspots
            </h2>
          </div>
          {hotspots.length === 0 ? (
            <div className="text-center py-10 text-gray-400 font-medium">No objects meet the critical/high risk hotspot threshold (&ge;15%).</div>
          ) : (
            <div className="space-y-4">
              {hotspots.map((hot) => (
                <div key={hot.object_id} className="flex justify-between items-center p-4 rounded-lg bg-red-50/30 border border-red-100/50 hover:bg-red-50/50 transition">
                  <div>
                    <span className="text-xs bg-red-100 text-red-800 px-2 py-0.5 rounded font-bold uppercase mr-2">{hot.severity}</span>
                    <span className="font-bold text-gray-900">{hot.object_id}</span>
                    <span className="text-gray-500 text-xs ml-2">({hot.object_type})</span>
                  </div>
                  <div className="text-right">
                    <div className="font-black text-red-600">{hot.total_emissions_kg.toLocaleString()} kg</div>
                    <div className="text-[11px] text-gray-400 font-semibold">{hot.contribution_percentage}% of total</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* History / Run log */}
        <Card className="p-6 bg-white shadow-sm border border-gray-100">
          <h2 className="text-lg font-black text-gray-900 tracking-tight mb-6">Calculation Logs</h2>
          {history.length === 0 ? (
            <div className="text-center py-10 text-gray-400 font-medium">No history runs found.</div>
          ) : (
            <div className="space-y-4">
              {history.map((run) => (
                <div key={run.object_carbon_run_id} className="border-b border-gray-50 pb-3 last:border-0 last:pb-0">
                  <div className="flex justify-between text-sm font-semibold text-gray-800">
                    <span>Version v{run.object_carbon_version}</span>
                    <span className="text-xs text-gray-400 font-normal">{new Date(run.snapshot_timestamp).toLocaleDateString()}</span>
                  </div>
                  <div className="flex justify-between text-xs text-gray-400 mt-1">
                    <span>Emissions: {run.total_object_emissions.toLocaleString()} kg</span>
                    <span className="text-red-500 font-bold">{run.critical_objects} Critical</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
