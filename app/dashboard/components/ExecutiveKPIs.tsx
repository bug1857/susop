"use client";

import React from "react";
import { ShieldCheck, Award, TrendingUp, Layers, Sliders, Globe } from "lucide-react";

interface ExecutiveKPIsProps {
  complianceScoreVal: string;
  carbonFitnessVal: string;
  totalEmissionsVal: string;
  totalCasesVal: string;
  variantsCountVal: string;
  esgScoreVal: string;
  conformanceLoading: boolean;
  carbonLoading: boolean;
  summaryLoading: boolean;
  variantsLoading: boolean;
  esgLoading: boolean;
}

export function ExecutiveKPIs({
  complianceScoreVal,
  carbonFitnessVal,
  totalEmissionsVal,
  totalCasesVal,
  variantsCountVal,
  esgScoreVal,
  conformanceLoading,
  carbonLoading,
  summaryLoading,
  variantsLoading,
  esgLoading
}: ExecutiveKPIsProps) {
  return (
    <section className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      <KPICard 
        title="Compliance Score" 
        value={complianceScoreVal} 
        icon={<ShieldCheck className="h-4 w-4 text-emerald-600" />} 
        subtitle="Model alignment" 
        loading={conformanceLoading}
      />
      <KPICard 
        title="Carbon Fitness" 
        value={carbonFitnessVal} 
        icon={<Award className="h-4 w-4 text-emerald-600" />} 
        subtitle="GHG conformance" 
        loading={carbonLoading}
      />
      <KPICard 
        title="Total Emissions" 
        value={totalEmissionsVal} 
        icon={<TrendingUp className="h-4 w-4 text-emerald-600" />} 
        subtitle="Calculated actual" 
        loading={carbonLoading}
      />
      <KPICard 
        title="Total Cases" 
        value={totalCasesVal} 
        icon={<Layers className="h-4 w-4 text-emerald-600" />} 
        subtitle="Seeded trace logs" 
        loading={summaryLoading}
      />
      <KPICard 
        title="Variants Count" 
        value={variantsCountVal} 
        icon={<Sliders className="h-4 w-4 text-emerald-600" />} 
        subtitle="Unique path routes" 
        loading={variantsLoading}
      />
      <KPICard 
        title="ESG Score" 
        value={esgScoreVal} 
        icon={<Globe className="h-4 w-4 text-emerald-600" />} 
        subtitle="Workspace overall" 
        loading={esgLoading}
      />
    </section>
  );
}

function KPICard({ 
  title, 
  value, 
  icon, 
  subtitle, 
  loading 
}: { 
  title: string; 
  value: string | number; 
  icon: React.ReactNode; 
  subtitle: string;
  loading: boolean;
}) {
  return (
    <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-sm flex items-start gap-3.5">
      <div className="p-2 bg-slate-50 rounded-lg border border-slate-100 text-emerald-600 shrink-0">
        {icon}
      </div>
      <div className="space-y-0.5 truncate flex-1">
        <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest block">{title}</span>
        {loading ? (
          <div className="h-6 bg-slate-100 rounded animate-pulse w-14 mt-1" />
        ) : (
          <div className="text-lg font-black text-slate-800 tracking-tight">{value}</div>
        )}
        <span className="text-[9px] text-slate-400 font-semibold block uppercase tracking-wider">{subtitle}</span>
      </div>
    </div>
  );
}
