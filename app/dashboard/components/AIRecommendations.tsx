"use client";

import React from "react";
import { Card } from "../../../components/Card";

interface AIRecommendationsProps {
  recommendations: {
    status: string;
    data?: any[] | null;
  };
  generateRecommendations: () => void;
}

export function AIRecommendations({
  recommendations,
  generateRecommendations
}: AIRecommendationsProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm space-y-4">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="font-extrabold text-sm text-slate-800">SustainAI Recommendation Cards</h3>
          <p className="text-[10px] text-slate-400 mt-0.5">Ollama-generated sustainability improvements and mitigation paths.</p>
        </div>
        <button
          onClick={generateRecommendations}
          className="text-xs px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-bold transition-colors shadow-sm"
        >
          Regenerate Recommendations
        </button>
      </div>

      {recommendations.status === "loading" ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 py-4">
          {[1, 2].map(i => <div key={i} className="h-24 bg-slate-100 rounded-lg animate-pulse" />)}
        </div>
      ) : recommendations.data && recommendations.data.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {recommendations.data.map((rec: any, idx: number) => (
            <Card key={idx} className="p-4 border border-slate-100 hover:border-emerald-200 transition-colors bg-white">
              <div className="flex justify-between items-start">
                <div className="font-extrabold text-xs text-slate-800">{rec.title}</div>
                <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                  rec.priority === "high" 
                    ? "bg-red-50 text-red-700 border border-red-100" 
                    : "bg-amber-50 text-amber-700 border border-amber-100"
                }`}>
                  {rec.priority ? rec.priority.toUpperCase() : "MEDIUM"}
                </span>
              </div>
              <p className="text-[10px] text-slate-500 mt-2 leading-relaxed">{rec.description}</p>
            </Card>
          ))}
        </div>
      ) : (
        <div className="bg-slate-50 border border-slate-100 p-6 rounded-lg text-center">
          <p className="text-xs text-slate-500 font-semibold leading-relaxed">
            No sustainability recommendations generated yet. Run Conformance Analysis and Carbon Attribution to unlock AI recommendations.
          </p>
        </div>
      )}
    </div>
  );
}
