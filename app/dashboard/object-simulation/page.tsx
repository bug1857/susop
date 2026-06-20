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
  RefreshCw,
  Info,
  TrendingUp,
  Activity,
  CheckCircle,
  Zap
} from "lucide-react";

interface ScenarioChange {
  change_type: string;
  target_object: string;
  action: string;
  reasoning: string;
  expected_impact: string;
  confidence: number;
}

interface Scenario {
  simulation_id: string;
  strategy: string;
  impact_score: number;
  confidence: number;
  projected_carbon_change_kg: number;
  projected_fitness_change: number;
  projected_risk_change: number;
  changes: ScenarioChange[];
  rank: number;
}

interface SimulationData {
  simulation_version: number;
  simulation_run_id: string;
  snapshot_timestamp: string;
  scenarios: Scenario[];
}

interface HistoryItem {
  simulation_version: number;
  snapshot_timestamp: string;
  total_simulations: number;
}

export default function ObjectSimulationPage() {
  const { selectedAnalysisId } = useCopilot();
  
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [data, setData] = useState<SimulationData | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [activeStrategy, setActiveStrategy] = useState<string>("carbon_reduction");

  const fetchSimulation = useCallback(async () => {
    if (!selectedAnalysisId) return;
    try {
      setLoading(true);
      const res = await api.get(`/api/v1/object-simulation/${selectedAnalysisId}`);
      setData(res.data);
      
      const histRes = await api.get(`/api/v1/object-simulation/${selectedAnalysisId}/history`);
      setHistory(histRes.data);
      
    } catch (err: any) {
      if (err.response?.status !== 404 && err.response?.status !== 400) {
        console.error("Failed to fetch object simulation", err);
      }
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [selectedAnalysisId]);

  useEffect(() => {
    fetchSimulation();
  }, [fetchSimulation]);

  const handleGenerate = async () => {
    if (!selectedAnalysisId) return;
    try {
      setGenerating(true);
      await api.post(`/api/v1/object-simulation/${selectedAnalysisId}/generate`);
      await fetchSimulation();
    } catch (err) {
      console.error("Failed to generate simulation", err);
    } finally {
      setGenerating(false);
    }
  };

  const handleVersionSelect = async (version: number) => {
    if (!selectedAnalysisId) return;
    try {
      setLoading(true);
      const res = await api.get(`/api/v1/object-simulation/${selectedAnalysisId}/version/${version}`);
      setData(res.data);
    } catch (err) {
      console.error("Failed to fetch version", err);
    } finally {
      setLoading(false);
    }
  };

  if (!selectedAnalysisId) {
    return (
      <div className="flex-1 p-8 bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-800">No Analysis Selected</h2>
          <p className="text-gray-500 mt-2">Please select an analysis from the dashboard.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex-1 p-8 flex items-center justify-center">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="flex-1 p-8 bg-gray-50 overflow-y-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Zap className="h-6 w-6 text-blue-500" />
            Object-Centric Simulation
          </h1>
          <p className="text-gray-500 mt-1">What-If Analysis & Process Projections</p>
        </div>
        <div className="flex items-center gap-4">
          {history.length > 0 && (
            <select 
              className="border border-gray-300 rounded-md px-3 py-2 text-sm"
              onChange={(e) => handleVersionSelect(Number(e.target.value))}
              value={data?.simulation_version || ""}
            >
              {history.map(h => (
                <option key={h.simulation_version} value={h.simulation_version}>
                  Version {h.simulation_version} ({new Date(h.snapshot_timestamp).toLocaleDateString()})
                </option>
              ))}
            </select>
          )}
          <Button onClick={handleGenerate} disabled={generating} className="flex items-center gap-2">
            <RefreshCw className={`h-4 w-4 ${generating ? 'animate-spin' : ''}`} />
            {generating ? 'Generating...' : 'Generate Scenarios'}
          </Button>
        </div>
      </div>

      {!data ? (
        <Card className="p-12 text-center">
          <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900">No Simulations Found</h3>
          <p className="text-gray-500 mt-2">Generate your first object-centric simulation batch to project future states.</p>
          <Button onClick={handleGenerate} className="mt-6">Generate Scenarios</Button>
        </Card>
      ) : (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card className="p-6">
              <div className="flex items-center gap-3 mb-2">
                <Activity className="h-5 w-5 text-indigo-500" />
                <h3 className="font-medium text-gray-900">Total Simulations</h3>
              </div>
              <p className="text-3xl font-bold text-indigo-600">{data.scenarios?.length || 0}</p>
            </Card>
            
            <Card className="p-6">
              <div className="flex items-center gap-3 mb-2">
                <Sparkles className="h-5 w-5 text-blue-500" />
                <h3 className="font-medium text-gray-900">Best Impact Score</h3>
              </div>
              <p className="text-3xl font-bold text-blue-600">
                {data.scenarios?.find(s => s.rank === 1)?.impact_score || 0}
              </p>
            </Card>
            
            <Card className="p-6">
              <div className="flex items-center gap-3 mb-2">
                <TrendingUp className="h-5 w-5 text-emerald-500" />
                <h3 className="font-medium text-gray-900">Projected Carbon Drop</h3>
              </div>
              <p className="text-3xl font-bold text-emerald-600">
                {data.scenarios?.find(s => s.rank === 1)?.projected_carbon_change_kg || 0} kg
              </p>
            </Card>
            
            <Card className="p-6">
              <div className="flex items-center gap-3 mb-2">
                <CheckCircle className="h-5 w-5 text-purple-500" />
                <h3 className="font-medium text-gray-900">Confidence</h3>
              </div>
              <p className="text-3xl font-bold text-purple-600">
                {data.scenarios?.find(s => s.rank === 1)?.confidence || 0}%
              </p>
            </Card>
          </div>

          <Card className="overflow-hidden">
            <div className="border-b border-gray-200">
              <nav className="flex -mb-px px-6">
                {data.scenarios?.map((s) => (
                  <button
                    key={s.strategy}
                    onClick={() => setActiveStrategy(s.strategy)}
                    className={`mr-8 py-4 px-1 border-b-2 font-medium text-sm ${
                      activeStrategy === s.strategy
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    {s.strategy.replace('_', ' ').toUpperCase()} {s.rank === 1 && '🏆'}
                  </button>
                ))}
              </nav>
            </div>
            
            <div className="p-6">
              {data.scenarios?.filter(s => s.strategy === activeStrategy).map(s => (
                <div key={s.simulation_id}>
                  <div className="flex items-start justify-between mb-8">
                    <div>
                      <h2 className="text-xl font-semibold text-gray-900 mb-2">Simulation Impact Panel</h2>
                      <div className="flex gap-4">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          Impact: {s.impact_score}
                        </span>
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          Confidence: {s.confidence}%
                        </span>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-500">Projected Carbon Change</div>
                      <div className={`text-xl font-bold ${s.projected_carbon_change_kg < 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {s.projected_carbon_change_kg > 0 ? '+' : ''}{s.projected_carbon_change_kg} kg
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-500">Projected Fitness Change</div>
                      <div className={`text-xl font-bold ${s.projected_fitness_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {s.projected_fitness_change > 0 ? '+' : ''}{s.projected_fitness_change}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-500">Projected Risk Change</div>
                      <div className={`text-xl font-bold ${s.projected_risk_change < 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {s.projected_risk_change > 0 ? '+' : ''}{s.projected_risk_change}
                      </div>
                    </div>
                  </div>

                  <h3 className="text-lg font-medium text-gray-900 mb-4">Scenario Timeline</h3>
                  <div className="space-y-4">
                    {s.changes.map((c, i) => (
                      <div key={i} className="border border-gray-200 rounded-lg p-4 bg-white">
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex items-center gap-2">
                            <span className="bg-blue-100 text-blue-800 text-xs font-bold px-2 py-1 rounded uppercase tracking-wider">
                              {c.change_type.replace('_', ' ')}
                            </span>
                            <span className="font-medium text-gray-900">{c.target_object}</span>
                          </div>
                          <span className="text-sm text-gray-500 font-medium">Confidence: {c.confidence}%</span>
                        </div>
                        <p className="text-gray-800 font-medium mb-1">{c.action}</p>
                        <div className="flex gap-4 text-sm mt-3 bg-gray-50 p-3 rounded">
                          <div className="flex-1">
                            <strong className="text-gray-700 block mb-1">Reasoning</strong>
                            <span className="text-gray-600">{c.reasoning}</span>
                          </div>
                          <div className="flex-1 border-l pl-4 border-gray-200">
                            <strong className="text-gray-700 block mb-1">Expected Impact</strong>
                            <span className="text-gray-600">{c.expected_impact}</span>
                          </div>
                        </div>
                      </div>
                    ))}
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
