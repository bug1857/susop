"use client";

import React from "react";
import { Truck } from "lucide-react";
import { formatMetric } from "../../../services/format";

interface SupplierSimpleCardProps {
  carbonAttribution: {
    status: string;
    data?: any;
  };
  supplierBreakdowns: any[];
}

export function SupplierSimpleCard({
  carbonAttribution,
  supplierBreakdowns
}: SupplierSimpleCardProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="font-extrabold text-sm text-slate-800">Supplier Intelligence</h3>
          <p className="text-[10px] text-slate-400 mt-0.5">Emissions breakdowns attributed to supply-chain partner activities.</p>
        </div>
        <Truck className="h-5 w-5 text-emerald-600" />
      </div>

      {carbonAttribution.status === "loading" ? (
        <div className="space-y-3 py-6">
          {[1, 2, 3].map(i => <div key={i} className="h-8 bg-slate-100 rounded-lg animate-pulse" />)}
        </div>
      ) : supplierBreakdowns.length > 0 ? (
        <div className="space-y-3">
          {supplierBreakdowns.map((supp: any) => (
            <div key={supp.id} className="space-y-1">
              <div className="flex justify-between text-xs font-semibold text-slate-700">
                <span className="truncate max-w-[260px]">{supp.name}</span>
                <span className="font-bold">{Number(supp.emissions).toFixed(1)} kg ({supp.percentage.toFixed(0)}%)</span>
              </div>
              <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-emerald-600 transition-all duration-500" 
                  style={{ width: `${supp.percentage}%` }} 
                />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-slate-50 border border-slate-100 p-6 rounded-lg text-center">
          <p className="text-[11px] text-slate-500 leading-relaxed font-semibold">
            No supplier-specific transaction fields identified in log.
          </p>
          <p className="text-[10px] text-slate-400 mt-1 leading-relaxed">
            Map a column to **Supplier ID** in the guided wizard to attribute supply chain emissions directly.
          </p>
        </div>
      )}
    </div>
  );
}

interface SupplierAdvancedPanelProps {
  sustainabilityMetrics: any;
}

export function SupplierAdvancedPanel({
  sustainabilityMetrics
}: SupplierAdvancedPanelProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm space-y-6">
      <div>
        <h3 className="font-extrabold text-sm text-slate-800">Supplier Intelligence Analytics</h3>
        <p className="text-[10px] text-slate-400 mt-0.5">Advanced supplier carbon footprint, spend, and risk analysis metrics.</p>
      </div>

      {sustainabilityMetrics && sustainabilityMetrics.suppliers && sustainabilityMetrics.suppliers.length > 0 ? (
        <div className="space-y-6">
          {/* Top lists grids */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
            
            {/* Top by Emissions */}
            <div className="space-y-3">
              <h4 className="font-bold text-xs text-slate-700 uppercase tracking-wider">Top by Emissions</h4>
              <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                {sustainabilityMetrics.top_suppliers_emissions?.map((supp: any, idx: number) => (
                  <div key={idx} className="p-2.5 rounded-lg bg-slate-50 border border-slate-100/60 text-xs flex justify-between items-center">
                    <span className="font-bold text-slate-800 truncate max-w-[120px]" title={supp.supplier_name}>{supp.supplier_name}</span>
                    <span className="font-extrabold text-red-600">{Number(supp.emissions).toLocaleString()} kg</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Top by Spend */}
            <div className="space-y-3">
              <h4 className="font-bold text-xs text-slate-700 uppercase tracking-wider">Top by Spend</h4>
              <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                {sustainabilityMetrics.top_suppliers_spend?.map((supp: any, idx: number) => (
                  <div key={idx} className="p-2.5 rounded-lg bg-slate-50 border border-slate-100/60 text-xs flex justify-between items-center">
                    <span className="font-bold text-slate-800 truncate max-w-[120px]" title={supp.supplier_name}>{supp.supplier_name}</span>
                    <span className="font-extrabold text-blue-600">${Number(supp.spend).toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Supplier Risk Rankings */}
            <div className="space-y-3">
              <h4 className="font-bold text-xs text-slate-700 uppercase tracking-wider">Risk Rankings</h4>
              <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                {sustainabilityMetrics.supplier_risk_rankings?.map((supp: any, idx: number) => (
                  <div key={idx} className="p-2.5 rounded-lg bg-slate-50 border border-slate-100/60 text-xs flex justify-between items-center">
                    <span className="font-bold text-slate-800 truncate max-w-[120px]" title={supp.supplier_name}>{supp.supplier_name}</span>
                    <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                      supp.risk_level === "High" ? "bg-red-50 text-red-700 border border-red-100" :
                      supp.risk_level === "Medium" ? "bg-amber-50 text-amber-700 border border-amber-100" :
                      "bg-green-50 text-green-700 border border-green-100"
                    }`}>{supp.risk_level}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Supplier ESG Rankings */}
            <div className="space-y-3">
              <h4 className="font-bold text-xs text-slate-700 uppercase tracking-wider">ESG Rankings</h4>
              <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                {sustainabilityMetrics.supplier_esg_rankings?.map((supp: any, idx: number) => (
                  <div key={idx} className="p-2.5 rounded-lg bg-slate-50 border border-slate-100/60 text-xs flex justify-between items-center">
                    <span className="font-bold text-slate-800 truncate max-w-[120px]" title={supp.supplier_name}>{supp.supplier_name}</span>
                    <span className="font-black text-emerald-600">{formatMetric(supp.esg_score, "percent")}</span>
                  </div>
                ))}
              </div>
            </div>

          </div>

          {/* Comparison Cards */}
          <div className="space-y-3 pt-2">
            <h4 className="font-bold text-xs text-slate-700 uppercase tracking-wider">Supplier Overview Cards</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {sustainabilityMetrics.suppliers?.slice(0, 3).map((supp: any, idx: number) => (
                <div key={idx} className="bg-slate-50 rounded-xl p-4 border border-slate-100 space-y-3.5 shadow-xs">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-[10px] text-slate-400 font-extrabold uppercase">{supp.supplier_id}</span>
                      <div className="font-bold text-sm text-slate-800 truncate max-w-[160px]">{supp.supplier_name}</div>
                      <span className="text-[9px] font-semibold text-slate-400 uppercase tracking-wider">{supp.supplier_country}</span>
                    </div>
                    <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 border border-emerald-100 rounded text-xs font-black">
                      ESG: {formatMetric(supp.esg_score, "percent")}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-xs font-semibold">
                    <div>
                      <span className="block text-slate-400 text-[10px] uppercase">Emissions</span>
                      <span className="font-bold text-slate-800">{Number(supp.emissions).toLocaleString()} kg</span>
                    </div>
                    <div>
                      <span className="block text-slate-400 text-[10px] uppercase">Spend</span>
                      <span className="font-bold text-slate-800">${Number(supp.spend).toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      ) : (
        <div className="bg-slate-50 border border-slate-100 p-6 rounded-lg text-center">
          <p className="text-xs text-slate-500 font-semibold leading-relaxed">
            No supplier intelligence data generated yet. Run Conformance Analysis and Carbon Attribution with mapped Supplier ID, Supplier Name, and Cost columns to unlock Supplier Analytics.
          </p>
        </div>
      )}
    </div>
  );
}
