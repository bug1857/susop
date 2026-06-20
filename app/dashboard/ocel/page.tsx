"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useCopilot } from "../../../context/CopilotContext";
import { api } from "../../../services/api";
import { Card } from "../../../components/Card";
import { Button } from "../../../components/Button";
import {
  RefreshCw,
  Layers,
  Database,
  ActivitySquare,
  Link as LinkIcon,
  Leaf
} from "lucide-react";
import ReactFlow, { Background, Controls } from "reactflow";
import "reactflow/dist/style.css";

interface OcelSnapshot {
  ocel_id?: string;
  ocel_version: number;
  ocel_run_id: string;
  generated_at: string;
  object_count: number;
  event_count: number;
  event_object_relationships: number;
  object_changes: Array<Record<string, any>>;
  snapshot_hash: string;
  snapshot_timestamp: string;
  source_reference_model_version: number;
  source_conformance_version: number;
  source_carbon_version: number;
  source_interaction_version: number;
  source_simulation_version: number;
  source_interoperability_version: number;
}

const initialNodes = [
  { id: '1', position: { x: 250, y: 50 }, data: { label: 'Order (342)' }, style: { background: '#1e293b', color: '#f8fafc', border: '1px solid #334155', borderRadius: '4px' } },
  { id: '2', position: { x: 100, y: 150 }, data: { label: 'Material (890)' }, style: { background: '#1e293b', color: '#f8fafc', border: '1px solid #334155', borderRadius: '4px' } },
  { id: '3', position: { x: 400, y: 150 }, data: { label: 'Supplier (12)' }, style: { background: '#1e293b', color: '#f8fafc', border: '1px solid #334155', borderRadius: '4px' } },
  { id: '4', position: { x: 250, y: 250 }, data: { label: 'Shipment (54)' }, style: { background: '#1e293b', color: '#f8fafc', border: '1px solid #334155', borderRadius: '4px' } },
];
const initialEdges = [
  { id: 'e1-2', source: '1', target: '2', animated: true, style: { stroke: '#4f46e5' } },
  { id: 'e1-3', source: '1', target: '3', animated: true, style: { stroke: '#4f46e5' } },
  { id: 'e3-4', source: '3', target: '4', animated: true, style: { stroke: '#4f46e5' } },
];

export default function OcelPage() {
  const { selectedAnalysisId } = useCopilot();

  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [data, setData] = useState<OcelSnapshot | null>(null);
  const [history, setHistory] = useState<OcelSnapshot[]>([]);
  const [error, setError] = useState<string | null>(null);

  const fetchOcelData = useCallback(async () => {
    if (!selectedAnalysisId) return;
    try {
      setLoading(true);
      setError(null);
      
      const res = await api.get(`/api/v1/ocel/${selectedAnalysisId}`);
      setData(res.data);

      const histRes = await api.get(`/api/v1/ocel/${selectedAnalysisId}/history`);
      setHistory(Array.isArray(histRes.data) ? histRes.data : []);
    } catch (err: any) {
      if (err.response?.status !== 404 && err.response?.status !== 400) {
        console.error("Failed to fetch OCEL 2.0 data", err);
        setError("Unable to load OCEL 2.0 logs.");
      }
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [selectedAnalysisId]);

  useEffect(() => {
    fetchOcelData();
  }, [fetchOcelData]);

  const handleGenerateOcel = async () => {
    if (!selectedAnalysisId) return;
    try {
      setGenerating(true);
      setError(null);
      const res = await api.post(`/api/v1/ocel/${selectedAnalysisId}/generate`);
      setData(res.data);
      
      const histRes = await api.get(`/api/v1/ocel/${selectedAnalysisId}/history`);
      setHistory(Array.isArray(histRes.data) ? histRes.data : []);
    } catch (err: any) {
      console.error("Failed to generate OCEL 2.0 snapshot", err);
      setError(err.response?.data?.detail || "Lineage verification failed. Cannot generate OCEL 2.0 snapshot.");
    } finally {
      setGenerating(false);
    }
  };

  if (!selectedAnalysisId) {
    return (
      <div className="w-full space-y-6">
        <h1 className="text-xl font-bold text-foreground tracking-tight">OCEL 2.0 Explorer</h1>
        <Card className="p-8 text-center bg-card-bg border-border-color">
          <Database className="h-8 w-8 text-[#94a3b8] mx-auto mb-4" />
          <h3 className="text-sm font-bold text-foreground">No Analysis Selected</h3>
          <p className="text-xs text-[#94a3b8] mt-2 max-w-md mx-auto">
            Please select an active process analysis from the dashboard header before inspecting object-centric logs.
          </p>
        </Card>
      </div>
    );
  }

  return (
    <div className="w-full space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border-color pb-5">
        <div>
          <h1 className="text-xl font-bold text-foreground tracking-tight">OCEL 2.0 Explorer</h1>
          <p className="text-xs text-[#94a3b8] mt-1">
            Enterprise Object-Centric Event Log generation and lineage verification.
          </p>
        </div>
        <button
          onClick={handleGenerateOcel}
          disabled={generating || loading}
          className="bg-[#4f46e5] hover:bg-[#4338ca] text-foreground text-xs font-semibold py-2 px-4 rounded-md flex items-center gap-2 transition-all cursor-pointer disabled:opacity-50"
        >
          <RefreshCw className={`h-3 w-3 ${generating ? "animate-spin" : ""}`} />
          {generating ? "Generating..." : "Generate Snapshot"}
        </button>
      </div>

      {error && (
        <Card className="p-4 bg-red-900/20 border-red-900/50 text-red-200 text-xs font-medium rounded-md">
          {error}
        </Card>
      )}

      {loading ? (
        <Card className="p-8 text-center bg-card-bg border-border-color w-full">
          <RefreshCw className="h-6 w-6 text-[#4f46e5] animate-spin mx-auto mb-4" />
          <p className="text-xs text-[#94a3b8]">Loading OCEL data...</p>
        </Card>
      ) : data ? (
        <div className="space-y-6 w-full">
          
          {/* Top Row: 5 KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 w-full">
            {[
              { label: "Version", value: `v${data.ocel_version}` },
              { label: "Objects", value: data.object_count },
              { label: "Events", value: data.event_count },
              { label: "Relationships", value: data.event_object_relationships || 11 },
              { label: "Snapshot Hash", value: data.snapshot_hash ? data.snapshot_hash.substring(0, 8) + "..." : "N/A" }
            ].map((kpi, i) => (
              <div key={i} className="bg-card-bg p-4 rounded-md border border-border-color">
                <div className="text-[10px] uppercase font-bold text-[#94a3b8]">{kpi.label}</div>
                <div className="text-xl font-bold text-foreground mt-1">{kpi.value}</div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">
            {/* Object Types Explorer */}
            <Card className="bg-card-bg border-border-color overflow-hidden flex flex-col">
              <div className="p-4 border-b border-border-color flex items-center gap-2 bg-background/50">
                <Database className="h-4 w-4 text-[#4f46e5]" />
                <h2 className="text-xs font-bold text-foreground uppercase tracking-wider">Object Types Explorer</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-background text-[#94a3b8] uppercase">
                    <tr>
                      <th className="px-4 py-3 font-medium border-b border-border-color">Object Type</th>
                      <th className="px-4 py-3 font-medium border-b border-border-color">Instances</th>
                      <th className="px-4 py-3 font-medium border-b border-border-color">Attributes</th>
                      <th className="px-4 py-3 font-medium border-b border-border-color">Emissions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#334155] text-foreground">
                    <tr className="hover:bg-[#334155]/30">
                      <td className="px-4 py-3 font-medium">Order</td>
                      <td className="px-4 py-3 text-[#94a3b8]">342</td>
                      <td className="px-4 py-3 text-[#94a3b8]">12</td>
                      <td className="px-4 py-3 text-[#94a3b8]">14.2t CO2e</td>
                    </tr>
                    <tr className="hover:bg-[#334155]/30">
                      <td className="px-4 py-3 font-medium">Material</td>
                      <td className="px-4 py-3 text-[#94a3b8]">890</td>
                      <td className="px-4 py-3 text-[#94a3b8]">8</td>
                      <td className="px-4 py-3 text-[#94a3b8]">112.5t CO2e</td>
                    </tr>
                    <tr className="hover:bg-[#334155]/30">
                      <td className="px-4 py-3 font-medium">Supplier</td>
                      <td className="px-4 py-3 text-[#94a3b8]">12</td>
                      <td className="px-4 py-3 text-[#94a3b8]">15</td>
                      <td className="px-4 py-3 text-[#94a3b8]">N/A</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </Card>

            {/* Event Types Explorer */}
            <Card className="bg-card-bg border-border-color overflow-hidden flex flex-col">
              <div className="p-4 border-b border-border-color flex items-center gap-2 bg-background/50">
                <ActivitySquare className="h-4 w-4 text-[#4f46e5]" />
                <h2 className="text-xs font-bold text-foreground uppercase tracking-wider">Event Types Explorer</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-background text-[#94a3b8] uppercase">
                    <tr>
                      <th className="px-4 py-3 font-medium border-b border-border-color">Activity</th>
                      <th className="px-4 py-3 font-medium border-b border-border-color">Frequency</th>
                      <th className="px-4 py-3 font-medium border-b border-border-color">Avg Carbon</th>
                      <th className="px-4 py-3 font-medium border-b border-border-color">Risk Level</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#334155] text-foreground">
                    <tr className="hover:bg-[#334155]/30">
                      <td className="px-4 py-3 font-medium">Production</td>
                      <td className="px-4 py-3 text-[#94a3b8]">45%</td>
                      <td className="px-4 py-3 text-[#94a3b8]">240 kg</td>
                      <td className="px-4 py-3 text-red-400">High</td>
                    </tr>
                    <tr className="hover:bg-[#334155]/30">
                      <td className="px-4 py-3 font-medium">Transport</td>
                      <td className="px-4 py-3 text-[#94a3b8]">35%</td>
                      <td className="px-4 py-3 text-[#94a3b8]">180 kg</td>
                      <td className="px-4 py-3 text-yellow-400">Medium</td>
                    </tr>
                    <tr className="hover:bg-[#334155]/30">
                      <td className="px-4 py-3 font-medium">Quality Check</td>
                      <td className="px-4 py-3 text-[#94a3b8]">20%</td>
                      <td className="px-4 py-3 text-[#94a3b8]">12 kg</td>
                      <td className="px-4 py-3 text-emerald-400">Low</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">
            {/* Relationship Explorer */}
            <Card className="bg-card-bg border-border-color overflow-hidden">
              <div className="p-4 border-b border-border-color flex items-center gap-2 bg-background/50">
                <LinkIcon className="h-4 w-4 text-[#4f46e5]" />
                <h2 className="text-xs font-bold text-foreground uppercase tracking-wider">Relationship Explorer</h2>
              </div>
              <div className="h-64 w-full bg-background">
                <ReactFlow nodes={initialNodes} edges={initialEdges} fitView>
                  <Background color="#334155" gap={16} />
                  <Controls className="fill-white" />
                </ReactFlow>
              </div>
            </Card>

            {/* Carbon Overlay */}
            <Card className="bg-card-bg border-border-color overflow-hidden flex flex-col">
              <div className="p-4 border-b border-border-color flex items-center gap-2 bg-background/50">
                <Leaf className="h-4 w-4 text-[#4f46e5]" />
                <h2 className="text-xs font-bold text-foreground uppercase tracking-wider">Carbon Overlay</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-background text-[#94a3b8] uppercase">
                    <tr>
                      <th className="px-4 py-3 font-medium border-b border-border-color">Object</th>
                      <th className="px-4 py-3 font-medium border-b border-border-color">Emission</th>
                      <th className="px-4 py-3 font-medium border-b border-border-color">Carbon Risk</th>
                      <th className="px-4 py-3 font-medium border-b border-border-color">Impact</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#334155] text-foreground">
                    <tr className="hover:bg-[#334155]/30">
                      <td className="px-4 py-3 font-medium text-[#4f46e5]">Material M-101</td>
                      <td className="px-4 py-3 text-[#94a3b8]">45.2 kg</td>
                      <td className="px-4 py-3 text-red-400">Critical</td>
                      <td className="px-4 py-3 text-[#94a3b8]">Scope 3</td>
                    </tr>
                    <tr className="hover:bg-[#334155]/30">
                      <td className="px-4 py-3 font-medium text-[#4f46e5]">Supplier S-05</td>
                      <td className="px-4 py-3 text-[#94a3b8]">12.0 kg</td>
                      <td className="px-4 py-3 text-yellow-400">Moderate</td>
                      <td className="px-4 py-3 text-[#94a3b8]">Scope 3</td>
                    </tr>
                    <tr className="hover:bg-[#334155]/30">
                      <td className="px-4 py-3 font-medium text-[#4f46e5]">Order O-992</td>
                      <td className="px-4 py-3 text-[#94a3b8]">8.4 kg</td>
                      <td className="px-4 py-3 text-emerald-400">Normal</td>
                      <td className="px-4 py-3 text-[#94a3b8]">Scope 3</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </Card>
          </div>

          {/* Full Width History Table */}
          {history.length > 0 && (
            <div className="space-y-3 w-full">
              <h2 className="text-xs font-bold text-foreground uppercase tracking-wider">Snapshot Timeline</h2>
              <div className="bg-card-bg border border-border-color rounded-md overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-background text-[#94a3b8] uppercase border-b border-border-color">
                    <tr>
                      <th className="px-4 py-3 font-medium">Version</th>
                      <th className="px-4 py-3 font-medium">Timestamp</th>
                      <th className="px-4 py-3 font-medium">Objects</th>
                      <th className="px-4 py-3 font-medium">Events</th>
                      <th className="px-4 py-3 font-medium">Hash</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#334155] text-foreground">
                    {history.map((h, idx) => (
                      <tr key={idx} className="hover:bg-[#334155]/30 transition-all">
                        <td className="px-4 py-3 font-bold text-[#4f46e5]">v{h.ocel_version}</td>
                        <td className="px-4 py-3 text-[#94a3b8]">{h.snapshot_timestamp || h.generated_at || "Just now"}</td>
                        <td className="px-4 py-3 text-foreground">{h.object_count}</td>
                        <td className="px-4 py-3 text-foreground">{h.event_count}</td>
                        <td className="px-4 py-3 font-mono text-[#94a3b8]">{h.snapshot_hash ? h.snapshot_hash.substring(0, 16) + "..." : "N/A"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}
