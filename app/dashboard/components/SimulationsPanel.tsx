"use client";

import React from "react";
import { AlertTriangle, TrendingUp, Sparkles } from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  AreaChart,
  Area
} from "recharts";

interface SimulationsPanelProps {
  carbonAttribution: {
    status: string;
    data?: {
      variant_emissions?: any[];
    } | null;
  };
  forecasts: {
    status: string;
    error?: string | null;
    data?: any[] | null;
  };
  generateForecast: (period: string, method: string) => void;
  simulations: {
    status: string;
    data?: any[] | null;
  };
  runSimulation: (
    scenarioName: string,
    description: string,
    metricType: string,
    projectedPct: number
  ) => void;
}

export function SimulationsPanel({
  carbonAttribution,
  forecasts,
  generateForecast,
  simulations,
  runSimulation
}: SimulationsPanelProps) {
  return (
    <div className="space-y-6">
      
      {/* Line charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Emissions Trend Chart */}
        <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm space-y-4">
          <div>
            <h3 className="font-extrabold text-sm text-slate-800">Emissions historical Trend</h3>
            <p className="text-[10px] text-slate-400 mt-0.5">Calculated carbon emission allocations across discovered event variants.</p>
          </div>
          
          <div className="h-64">
            {carbonAttribution.status === "loading" ? (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">Loading chart...</div>
            ) : carbonAttribution.data?.variant_emissions && carbonAttribution.data.variant_emissions.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={carbonAttribution.data.variant_emissions}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="variant_index" label={{ value: 'Variant Index', position: 'insideBottom', offset: -5, fontSize: 10 }} />
                  <YAxis label={{ value: 'kgCO2e', angle: -90, position: 'insideLeft', fontSize: 10 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="emissions" stroke="#16a34a" strokeWidth={2.5} name="Calculated Emissions" />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-xs text-slate-400 italic">No trend data.</div>
            )}
          </div>
        </div>

        {/* AI Forecast Panel */}
        <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="font-extrabold text-sm text-slate-800">AI Carbon Forecast projections</h3>
              <p className="text-[10px] text-slate-400 mt-0.5">Linear projection calculations based on historical parameters.</p>
            </div>
            <button
              onClick={() => generateForecast("2026-Q4", "LINEAR_TREND")}
              className="text-xs px-2.5 py-1 bg-slate-900 hover:bg-slate-800 text-white rounded font-bold transition-colors shadow-sm"
            >
              Trigger Forecast
            </button>
          </div>

          <div className="h-64">
            {forecasts.status === "loading" ? (
              <div className="h-full flex items-center justify-center text-xs text-slate-400">Running projection algorithms...</div>
            ) : forecasts.status === "error" ? (
              <div className="h-full flex flex-col items-center justify-center p-6 text-center text-xs text-amber-700 bg-amber-50 rounded-lg">
                <AlertTriangle className="h-5 w-5 mb-2 text-amber-600" />
                <span className="font-bold">Forecast execution message:</span>
                <span className="mt-1 leading-relaxed font-semibold">{forecasts.error}</span>
              </div>
            ) : forecasts.data && forecasts.data.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={forecasts.data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="period" />
                  <YAxis />
                  <Tooltip />
                  <Area type="monotone" dataKey="forecasted_emissions" stroke="#3b82f6" fill="#eff6ff" name="Projected Footprint" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center p-6 text-center text-slate-400 bg-slate-50 rounded-lg border border-slate-100">
                <TrendingUp className="h-5 w-5 mb-2 text-slate-300" />
                <span className="font-semibold text-slate-500">Insufficient Historical data</span>
                <span className="text-[10px] text-slate-400 mt-1 leading-relaxed">
                  Forecast calculations require at least two preceding historical analysis versions in the active project.
                </span>
              </div>
            )}
          </div>
        </div>

      </div>

      {/* Simulations grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Simulations card */}
        <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="font-extrabold text-sm text-slate-800">Scenario Simulation trials</h3>
              <p className="text-[10px] text-slate-400 mt-0.5">Simulate the impact of carbon optimization actions before deployment.</p>
            </div>
          </div>

          <div className="space-y-4">
            <button
              onClick={() => runSimulation("Optimize Procurement Routing", "Shift supplier procurement closer to hubs", "EMISSION_REDUCTION", 25)}
              className="w-full py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-bold text-xs transition-colors shadow-sm"
            >
              Run Supplier optimization Scenario (25% Reduction)
            </button>

            {simulations.status === "loading" ? (
              <div className="py-6 text-center text-xs text-slate-500 font-semibold">Running simulation model...</div>
            ) : simulations.data && simulations.data.length > 0 ? (
              <div className="space-y-3 max-h-48 overflow-y-auto">
                {simulations.data.map((sim: any, idx: number) => (
                  <div key={idx} className="bg-slate-50 border border-slate-100 p-3 rounded-lg flex justify-between items-center text-xs">
                    <div>
                      <div className="font-bold text-slate-800">{sim.scenario_name}</div>
                      <p className="text-[10px] text-slate-400 mt-0.5">{sim.description}</p>
                    </div>
                    <div className="text-right">
                      <span className="inline-block px-1.5 py-0.5 bg-green-100 text-green-800 font-bold text-[9px] rounded">
                        -{sim.projected_reduction_pct}% CO2
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-6 text-center text-xs text-slate-400 italic">
                No simulations run yet in this workspace session context.
              </div>
            )}
          </div>
        </div>

        {/* AI Explainability card */}
        <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm space-y-4">
          <div>
            <h3 className="font-extrabold text-sm text-slate-800">Ollama Explainability Ledger</h3>
            <p className="text-[10px] text-slate-400 mt-0.5">Model accountability logs justifying conformance scores and parameters.</p>
          </div>

          <div className="bg-slate-50 border border-slate-100/60 p-4 rounded-lg text-xs leading-relaxed space-y-2 max-h-48 overflow-y-auto">
            <h4 className="font-bold text-slate-700 flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5 text-emerald-600" />
              LLM Accountability statement
            </h4>
            <p className="text-slate-500 text-[10.5px]">
              Conformances and emission scores are derived using deterministic process mining token replay rules and validated carbon attribution factors. Local Ollama LLM provides conversational summaries but does not alter primary calculation parameters.
            </p>
          </div>
        </div>

      </div>

    </div>
  );
}
