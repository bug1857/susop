"use client";

import React from "react";
import { TrendingUp } from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip
} from "recharts";

interface CarbonHotspotsProps {
  carbonAttribution: {
    status: string;
    data?: {
      activity_emissions?: any[];
      actual_emissions: number;
    };
  };
}

export function CarbonHotspots({ carbonAttribution }: CarbonHotspotsProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm space-y-4">
      <div>
        <h3 className="font-extrabold text-sm text-slate-800">Emissions attribution Hotspots</h3>
        <p className="text-[10px] text-slate-400 mt-0.5">Calculated actual greenhouse gas weights attributed per activity node.</p>
      </div>

      {carbonAttribution.status === "loading" ? (
        <div className="space-y-3 py-6">
          {[1, 2, 3].map(i => <div key={i} className="h-8 bg-slate-100 rounded-lg animate-pulse" />)}
        </div>
      ) : carbonAttribution.data?.activity_emissions && carbonAttribution.data.activity_emissions.length > 0 ? (
        <div className="space-y-3 max-h-60 overflow-y-auto pr-2">
          {carbonAttribution.data.activity_emissions.map((hotspot: any, idx: number) => {
            const maxVal = Math.max(...(carbonAttribution.data?.activity_emissions || []).map((h: any) => h.emissions));
            const pct = maxVal > 0 ? (hotspot.emissions / maxVal) * 100 : 0;
            
            return (
              <div key={idx} className="space-y-1">
                <div className="flex justify-between text-xs font-semibold text-slate-700">
                  <span className="truncate max-w-[260px]">{hotspot.activity_name}</span>
                  <span className="font-bold">{Number(hotspot.emissions).toFixed(1)} kgCO2e</span>
                </div>
                <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-emerald-600 transition-all duration-500" 
                    style={{ width: `${pct}%` }} 
                  />
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="bg-slate-50 border border-slate-100 p-6 rounded-lg text-center">
          <p className="text-xs text-slate-500 font-semibold leading-relaxed">
            No carbon hotspots generated yet. Run Conformance Analysis and Carbon Attribution with mapped Carbon Emissions column to unlock carbon hotspots.
          </p>
        </div>
      )}
    </div>
  );
}

interface CarbonBudgetTrackerProps {
  carbonAttribution: {
    status: string;
    data?: {
      actual_emissions: number;
      carbon_budget: number;
      excess_emissions: number;
      activity_emissions?: any[];
    };
  };
}

export function CarbonBudgetTracker({ carbonAttribution }: CarbonBudgetTrackerProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm space-y-4">
      <div>
        <h3 className="font-extrabold text-sm text-slate-800">Carbon Leaderboard & Budget Tracker</h3>
        <p className="text-[10px] text-slate-400 mt-0.5">Top emission-producing activities and budget headroom evaluation.</p>
      </div>

      {carbonAttribution.status === "success" && carbonAttribution.data ? (
        <div className="space-y-4">
          {/* Budget Tracker */}
          <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-100 space-y-2">
            <div className="flex justify-between text-xs font-bold">
              <span className="text-slate-500">Actual vs Budget:</span>
              <span className={carbonAttribution.data.actual_emissions > carbonAttribution.data.carbon_budget ? "text-red-600" : "text-green-600"}>
                {Number(carbonAttribution.data.actual_emissions).toFixed(1)} / {Number(carbonAttribution.data.carbon_budget).toFixed(1)} kgCO2e
              </span>
            </div>
            <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
              <div 
                className={`h-full transition-all ${carbonAttribution.data.actual_emissions > carbonAttribution.data.carbon_budget ? "bg-red-600" : "bg-green-600"}`} 
                style={{ width: `${Math.min(100, (carbonAttribution.data.actual_emissions / carbonAttribution.data.carbon_budget) * 100)}%` }}
              />
            </div>
            {carbonAttribution.data.actual_emissions > carbonAttribution.data.carbon_budget && (
              <p className="text-[9px] text-red-500 font-bold">
                ⚠️ Carbon budget exceeded by {Number(carbonAttribution.data.excess_emissions).toFixed(1)} kgCO2e!
              </p>
            )}
          </div>

          {/* Leaderboard */}
          <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
            {carbonAttribution.data.activity_emissions?.map((act: any, idx: number) => (
              <div key={idx} className="flex justify-between text-xs items-center p-2 rounded bg-slate-50 border border-slate-100/60">
                <span className="font-semibold text-slate-700 truncate max-w-[200px]">{act.activity_name}</span>
                <span className="font-bold text-slate-900">{Number(act.emissions).toFixed(1)} kgCO2e</span>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="bg-slate-50 border border-slate-100 p-6 rounded-lg text-center">
          <p className="text-[11px] text-slate-500 leading-relaxed font-semibold">No carbon hotspots identified yet.</p>
          <p className="text-[9px] text-slate-400 mt-1 leading-relaxed">Run Conformance Analysis & Carbon Attribution to calculate hotspot metrics.</p>
        </div>
      )}
    </div>
  );
}

interface CarbonTrendsProps {
  sustainabilityMetrics: {
    monthly_emissions?: any[];
  } | null;
}

export function CarbonTrends({ sustainabilityMetrics }: CarbonTrendsProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm space-y-4">
      <div>
        <h3 className="font-extrabold text-sm text-slate-800">Carbon Trend Progression (Monthly)</h3>
        <p className="text-[10px] text-slate-400 mt-0.5">Aggregated actual carbon footprints mapped per month.</p>
      </div>

      <div className="h-48">
        {sustainabilityMetrics && sustainabilityMetrics.monthly_emissions && sustainabilityMetrics.monthly_emissions.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={sustainabilityMetrics.monthly_emissions}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="month" fontSize={10} />
              <YAxis fontSize={10} />
              <Tooltip />
              <Bar dataKey="emissions" fill="#10b981" name="Monthly emissions (kg)" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex flex-col items-center justify-center p-6 text-center text-slate-400 bg-slate-50 rounded-lg border border-slate-100">
            <TrendingUp className="h-5 w-5 mb-2 text-slate-300" />
            <span className="font-semibold text-slate-500">No Carbon Trends calculated</span>
            <span className="text-[10px] text-slate-400 mt-1 leading-relaxed">
              Please ensure that the **Timestamp** and **Carbon Emissions** fields are correctly mapped to visualize carbon trends.
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
