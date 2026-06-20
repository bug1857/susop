"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import { useAuth } from "../../../context/AuthContext";
import { useCopilot } from "../../../context/CopilotContext";
import { Card } from "../../../components/Card";
import { Button } from "../../../components/Button";
import { api } from "../../../services/api";
import {
  Sparkles,
  AlertTriangle,
  RefreshCw,
  Info,
  Network,
  Activity,
  Zap,
  TrendingUp,
  ShieldAlert
} from "lucide-react";

interface GraphNode {
  object_id: string;
  object_type: string;
  bottleneck_score: number;
  risk_score: number;
}

interface GraphEdge {
  source: string;
  target: string;
  interaction_type: string;
  frequency: number;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

interface InteractionSummary {
  total_relationships: number;
  bottleneck_count: number;
  high_risk_objects: number;
  highest_risk_object: {
    object_id: string;
    risk_score: number;
  } | null;
  highest_carbon_path: {
    path: string[];
    total_emissions_kg: number;
  } | null;
}

interface InteractionRun {
  object_interaction_version: number;
  object_interaction_run_id: string;
  snapshot_timestamp: string;
}

const SimpleGraph: React.FC<{ data: GraphData }> = ({ data }) => {
  const width = 800;
  const height = 400;
  const cx = width / 2;
  const cy = height / 2;
  const radius = 150;

  const nodesWithPositions = useMemo(() => {
    if (!data || !data.nodes) return [];
    return data.nodes.map((node, i) => {
      const angle = (i / data.nodes.length) * 2 * Math.PI;
      return {
        ...node,
        x: cx + radius * Math.cos(angle),
        y: cy + radius * Math.sin(angle),
      };
    });
  }, [data]);

  const getNodeColor = (type: string) => {
    const colors: Record<string, string> = {
      PurchaseOrder: "#3b82f6",
      Supplier: "#8b5cf6",
      Material: "#10b981",
      Shipment: "#f59e0b",
      Invoice: "#ec4899",
      Transport: "#6366f1"
    };
    return colors[type] || "#94a3b8";
  };

  if (!data || !data.nodes || data.nodes.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-50 rounded-lg border border-gray-100">
        <p className="text-sm text-gray-400 font-medium">No graph data available</p>
      </div>
    );
  }

  return (
    <div className="w-full overflow-auto bg-gray-50 rounded-lg border border-gray-100 flex justify-center items-center">
      <svg width={width} height={height} className="max-w-full">
        <defs>
          <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#cbd5e1" />
          </marker>
        </defs>
        {/* Edges */}
        {data.edges && data.edges.map((edge, i) => {
          const sourceNode = nodesWithPositions.find(n => n.object_id === edge.source);
          const targetNode = nodesWithPositions.find(n => n.object_id === edge.target);
          if (!sourceNode || !targetNode) return null;
          return (
            <g key={`edge-${i}`}>
              <line
                x1={sourceNode.x}
                y1={sourceNode.y}
                x2={targetNode.x}
                y2={targetNode.y}
                stroke="#cbd5e1"
                strokeWidth={Math.max(1, Math.min(4, edge.frequency / 5))}
                markerEnd="url(#arrowhead)"
              />
            </g>
          );
        })}
        {/* Nodes */}
        {nodesWithPositions.map((node) => (
          <g key={node.object_id} transform={`translate(${node.x}, ${node.y})`}>
            <circle
              r={12 + (node.risk_score / 10)}
              fill={getNodeColor(node.object_type)}
              stroke={node.bottleneck_score > 3 ? "#ef4444" : "#ffffff"}
              strokeWidth={node.bottleneck_score > 3 ? 3 : 2}
              className="transition-all hover:scale-110 cursor-pointer"
            >
              <title>{`${node.object_id} (${node.object_type})\nRisk: ${node.risk_score}\nBottleneck: ${node.bottleneck_score}`}</title>
            </circle>
            <text
              y={24 + (node.risk_score / 10)}
              textAnchor="middle"
              className="text-[10px] font-bold fill-gray-600 pointer-events-none"
            >
              {node.object_id}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
};

export default function ObjectInteractionPage() {
  const { selectedAnalysisId } = useCopilot();

  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [summary, setSummary] = useState<InteractionSummary | null>(null);
  const [bottlenecks, setBottlenecks] = useState<any[]>([]);
  const [riskPaths, setRiskPaths] = useState<any[]>([]);
  const [history, setHistory] = useState<InteractionRun[]>([]);

  const loadData = useCallback(async (analysisId: string) => {
    setLoading(true);
    setError(null);
    try {
      const summaryRes = await api.get(`/api/v1/object-interactions/${analysisId}/summary`);
      setSummary(summaryRes.data);

      const graphRes = await api.get(`/api/v1/object-interactions/${analysisId}`);
      setGraphData(graphRes.data);

      const botRes = await api.get(`/api/v1/object-interactions/${analysisId}/bottlenecks`);
      setBottlenecks(botRes.data);

      const riskRes = await api.get(`/api/v1/object-interactions/${analysisId}/risk-paths`);
      setRiskPaths(riskRes.data);

      const histRes = await api.get(`/api/v1/object-interactions/${analysisId}/history`);
      setHistory(histRes.data);

    } catch (err: any) {
      console.error(err);
      setError("Failed to load object interaction analytics.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedAnalysisId) {
      loadData(selectedAnalysisId);
    } else {
      setSummary(null);
      setGraphData(null);
      setBottlenecks([]);
      setRiskPaths([]);
      setHistory([]);
    }
  }, [selectedAnalysisId, loadData]);

  const handleGenerate = async () => {
    if (!selectedAnalysisId) return;
    setGenerating(true);
    setError(null);
    try {
      await api.post(`/api/v1/object-interactions/${selectedAnalysisId}/generate`);
      await loadData(selectedAnalysisId);
    } catch (err: any) {
      console.error(err);
      setError("Error generating object interaction analytics snapshot.");
    } finally {
      setGenerating(false);
    }
  };

  if (!selectedAnalysisId) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center p-6">
        <Info className="w-16 h-16 text-gray-300 mb-4" />
        <h3 className="text-xl font-bold text-gray-800">No Analysis Selected</h3>
        <p className="text-gray-500 mt-2">Please select a Process Analysis in the Copilot pane to view Object Interactions.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
        <RefreshCw className="w-10 h-10 text-blue-500 animate-spin mb-4" />
        <p className="text-gray-500 font-medium">Loading object interaction topology...</p>
      </div>
    );
  }

  const highestRiskId = summary?.highest_risk_object?.object_id || "N/A";
  const highestCarbonPathNodes = summary?.highest_carbon_path?.path || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-black text-gray-900 tracking-tight flex items-center gap-2">
            <Network className="w-7 h-7 text-blue-600" /> Object Interaction Analytics
          </h1>
          <p className="text-sm text-gray-500 font-medium mt-1">
            Analyze bottlenecks, risks, and carbon propagation across object relationship chains.
          </p>
        </div>
        <Button onClick={handleGenerate} disabled={generating} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white border-0">
          {generating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          {generating ? "Analyzing..." : "Analyze Interactions"}
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
        {/* Total Relationships */}
        <Card className="p-4 flex flex-col justify-between bg-white border border-gray-100 shadow-sm">
          <div className="text-xs font-bold text-gray-500 uppercase tracking-wider">Total Relationships</div>
          <div className="text-2xl font-black text-gray-900 mt-2">{summary?.total_relationships || 0}</div>
          <div className="text-xs text-blue-600 mt-1 font-semibold flex items-center gap-1"><Activity className="w-3 h-3" /> Object Edges Found</div>
        </Card>

        {/* Bottleneck Count */}
        <Card className="p-4 flex flex-col justify-between border-l-4 border-amber-500 bg-white shadow-sm">
          <div className="text-xs font-bold text-gray-500 uppercase tracking-wider">Bottleneck Objects</div>
          <div className="text-2xl font-black text-amber-600 mt-2">{summary?.bottleneck_count || 0}</div>
          <div className="text-xs text-gray-400 mt-1 flex items-center gap-1"><Zap className="w-3 h-3" /> Based on flow propagation</div>
        </Card>

        {/* Highest Risk Object */}
        <Card className="p-4 flex flex-col justify-between border-l-4 border-red-500 bg-white shadow-sm">
          <div className="text-xs font-bold text-gray-500 uppercase tracking-wider">Highest Risk Object</div>
          <div className="text-xl font-black text-red-600 mt-2 truncate" title={highestRiskId}>
            {highestRiskId}
          </div>
          <div className="text-xs text-gray-400 mt-1">
            {summary?.highest_risk_object?.risk_score ? `Score: ${summary.highest_risk_object.risk_score.toFixed(1)}` : "No risk calculated"}
          </div>
        </Card>

        {/* Highest Carbon Path */}
        <Card className="p-4 flex flex-col justify-between bg-white border border-gray-100 shadow-sm">
          <div className="text-xs font-bold text-gray-500 uppercase tracking-wider">Top Carbon Pathway</div>
          <div className="text-sm font-black text-emerald-600 mt-2 line-clamp-2" title={highestCarbonPathNodes.join(" → ")}>
            {highestCarbonPathNodes.length > 0 ? highestCarbonPathNodes.join(" → ") : "N/A"}
          </div>
          <div className="text-xs text-gray-400 mt-1 font-semibold flex items-center gap-1">
            <TrendingUp className="w-3 h-3 text-emerald-500" />
            {summary?.highest_carbon_path?.total_emissions_kg ? `${summary.highest_carbon_path.total_emissions_kg.toLocaleString()} kg CO₂e` : "0 kg"}
          </div>
        </Card>
      </div>

      {/* Main Graph & Paths Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Graph Column */}
        <Card className="p-6 bg-white border border-gray-100 shadow-sm lg:col-span-2">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-black text-gray-900 tracking-tight">Topology Visualization</h2>
            <span className="text-xs bg-blue-50 text-blue-800 font-bold px-3 py-1 rounded-full flex items-center gap-1">
              <Network className="w-3.5 h-3.5" /> SVG Rendering
            </span>
          </div>
          {graphData && <SimpleGraph data={graphData} />}
        </Card>

        {/* Hotspots / Top Paths Column */}
        <div className="space-y-6 lg:col-span-1">
          <Card className="p-5 bg-white border border-gray-100 shadow-sm">
            <h3 className="text-sm font-black text-gray-900 tracking-tight flex items-center gap-2 border-b border-gray-100 pb-2 mb-3">
              <Zap className="w-4 h-4 text-amber-500" /> Top Bottlenecks
            </h3>
            {bottlenecks.length === 0 ? (
              <p className="text-xs text-gray-400 italic">No bottlenecks detected.</p>
            ) : (
              <div className="space-y-3">
                {bottlenecks.slice(0, 5).map((bot, i) => (
                  <div key={i} className="flex justify-between items-center bg-gray-50 p-2 rounded">
                    <div>
                      <div className="text-xs font-bold text-gray-800">{bot.object_id}</div>
                      <div className="text-[10px] text-gray-500 uppercase">{bot.object_type}</div>
                    </div>
                    <div className="text-xs font-black text-amber-600 bg-amber-50 px-2 py-0.5 rounded">
                      {bot.bottleneck_score.toFixed(1)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card className="p-5 bg-white border border-gray-100 shadow-sm">
            <h3 className="text-sm font-black text-gray-900 tracking-tight flex items-center gap-2 border-b border-gray-100 pb-2 mb-3">
              <ShieldAlert className="w-4 h-4 text-red-500" /> High-Risk Paths
            </h3>
            {riskPaths.length === 0 ? (
              <p className="text-xs text-gray-400 italic">No high-risk paths detected.</p>
            ) : (
              <div className="space-y-3">
                {riskPaths.slice(0, 5).map((rp, i) => (
                  <div key={i} className="flex flex-col bg-red-50/50 border border-red-100 p-2 rounded">
                    <div className="text-[10px] font-bold text-gray-600 mb-1 leading-tight flex flex-wrap gap-1">
                      {rp.path.map((nodeId: string, idx: number) => (
                        <span key={idx} className="flex items-center">
                          {idx > 0 && <span className="mx-0.5 text-gray-400">→</span>}
                          <span className="bg-white px-1 border border-gray-200 rounded">{nodeId}</span>
                        </span>
                      ))}
                    </div>
                    <div className="flex justify-between mt-1 items-center">
                      <span className="text-[10px] text-gray-500 font-semibold">{rp.total_emissions_kg.toLocaleString()} kg</span>
                      <span className="text-xs font-black text-red-600">Risk: {(rp.average_risk_score ?? 0).toFixed(1)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
