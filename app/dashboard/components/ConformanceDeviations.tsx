"use client";

import React from "react";

interface ConformanceDeviationsProps {
  deviations: {
    status: string;
    data?: any[] | null;
  };
}

export function ConformanceDeviations({ deviations }: ConformanceDeviationsProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm space-y-4">
      <div>
        <h3 className="font-extrabold text-sm text-slate-800">Conformance Deviations</h3>
        <p className="text-[10px] text-slate-400 mt-0.5">Identified operation slips, skips, and structural model mismatches.</p>
      </div>

      {deviations.status === "loading" ? (
        <div className="space-y-3 py-6">
          {[1, 2, 3].map(i => <div key={i} className="h-8 bg-slate-100 rounded-lg animate-pulse" />)}
        </div>
      ) : deviations.data && deviations.data.length > 0 ? (
        <div className="border border-slate-100 rounded-lg overflow-hidden overflow-x-auto max-h-60">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-100 font-bold text-slate-500 uppercase text-[9px]">
                <th className="px-4 py-2.5">Deviation Type</th>
                <th className="px-4 py-2.5">Details</th>
                <th className="px-4 py-2.5 text-right">Severity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-600 font-medium">
              {deviations.data.map((dev, idx) => (
                <tr key={idx} className="hover:bg-slate-50/20">
                  <td className="px-4 py-2 font-bold text-slate-700">{dev.deviation_type}</td>
                  <td className="px-4 py-2 truncate max-w-[200px]">{dev.details || "Drift detected"}</td>
                  <td className="px-4 py-2 text-right">
                    <span className={`inline-block px-1.5 py-0.5 rounded text-[9px] font-bold ${
                      dev.severity === "high" 
                        ? "bg-red-50 text-red-700 border border-red-100" 
                        : "bg-amber-50 text-amber-700 border border-amber-100"
                    }`}>
                      {dev.severity ? dev.severity.toUpperCase() : "MEDIUM"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="py-10 text-center text-xs text-slate-400 italic">
          Zero operational deviations. Process is 100% conforming!
        </div>
      )}
    </div>
  );
}
