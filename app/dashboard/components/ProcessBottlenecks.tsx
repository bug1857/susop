"use client";

import React from "react";

interface ProcessBottlenecksProps {
  loadingBottlenecks: boolean;
  bottlenecks: any[];
}

export function ProcessBottlenecks({
  loadingBottlenecks,
  bottlenecks
}: ProcessBottlenecksProps) {
  return (
    <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm space-y-4">
      <div>
        <h3 className="font-extrabold text-sm text-slate-800">Process Bottleneck Delays</h3>
        <p className="text-[10px] text-slate-400 mt-0.5">Average wait and queue duration times across log transaction states.</p>
      </div>

      {loadingBottlenecks ? (
        <div className="space-y-3 py-6">
          {[1, 2, 3].map(i => <div key={i} className="h-8 bg-slate-100 rounded-lg animate-pulse" />)}
        </div>
      ) : bottlenecks.length > 0 ? (
        <div className="border border-slate-100 rounded-lg overflow-hidden overflow-x-auto max-h-60">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-100 font-bold text-slate-500 uppercase text-[9px]">
                <th className="px-4 py-2.5">Activity Name</th>
                <th className="px-4 py-2.5">Occurrences</th>
                <th className="px-4 py-2.5 text-right">Avg Wait Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-600 font-medium">
              {bottlenecks.map((bot, idx) => (
                <tr key={idx} className="hover:bg-slate-50/20">
                  <td className="px-4 py-2 truncate max-w-[200px]">{bot.activity_name || bot.activity}</td>
                  <td className="px-4 py-2">{bot.occurrence_count}</td>
                  <td className="px-4 py-2 text-right font-bold text-slate-900">
                    {Number(bot.average_wait_time).toFixed(1)} hrs
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="py-10 text-center text-xs text-slate-400 italic">
          No process bottleneck metrics identified.
        </div>
      )}
    </div>
  );
}
