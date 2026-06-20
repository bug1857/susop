"use client";

import React from "react";
import ReactFlow, { Controls, Background } from "reactflow";
import "reactflow/dist/style.css";

interface ProcessGraphCardProps {
  loadingGraph: boolean;
  rfNodes: any[];
  rfEdges: any[];
}

export function ProcessGraphCard({
  loadingGraph,
  rfNodes,
  rfEdges
}: ProcessGraphCardProps) {
  return (
    <div className="lg:col-span-7 bg-white rounded-xl border border-slate-200/80 p-5 shadow-sm flex flex-col h-[400px]">
      <div className="flex justify-between items-center mb-3">
        <div>
          <h3 className="font-extrabold text-sm text-slate-800">Process Discovery Graph</h3>
          <p className="text-[10px] text-slate-400 mt-0.5">Discovered Object-Centric Direct-Follower routes from event logs.</p>
        </div>
      </div>
      
      <div className="flex-1 rounded-lg border border-slate-100 overflow-hidden bg-slate-50">
        {loadingGraph ? (
          <div className="h-full flex items-center justify-center text-xs text-slate-500 font-semibold gap-2">
            <div className="w-5 h-5 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
            Rendering network nodes...
          </div>
        ) : rfNodes.length > 0 ? (
          <ReactFlow
            nodes={rfNodes}
            edges={rfEdges}
            fitView
            className="react-flow-sustain"
            preventScrolling={false}
          >
            <Background color="#cbd5e1" gap={16} />
            <Controls showInteractive={false} />
          </ReactFlow>
        ) : (
          <div className="h-full flex items-center justify-center text-xs text-slate-400 italic">
            No graph nodes generated for this analysis model.
          </div>
        )}
      </div>
    </div>
  );
}
