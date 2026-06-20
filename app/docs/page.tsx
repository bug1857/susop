"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { 
  BookOpen, 
  ChevronRight, 
  ArrowLeft, 
  FileText, 
  ShieldCheck, 
  TrendingUp, 
  Database,
  Cpu,
  Layers,
  Code
} from "lucide-react";

export default function DocsPage() {
  const router = useRouter();
  const [activeSection, setActiveSection] = useState("intro");

  const sections = [
    { id: "intro", title: "1. Introduction & Overview", icon: <BookOpen className="w-4 h-4" /> },
    { id: "arch", title: "2. System Architecture", icon: <Layers className="w-4 h-4" /> },
    { id: "schema", title: "3. Database Ledger Schema", icon: <Database className="w-4 h-4" /> },
    { id: "ingestion", title: "4. Data Ingestion Standards", icon: <FileText className="w-4 h-4" /> },
    { id: "heuristics", title: "5. Process Discovery Heuristics", icon: <Cpu className="w-4 h-4" /> },
    { id: "conformance", title: "6. Conformance Checking Engine", icon: <ShieldCheck className="w-4 h-4" /> },
    { id: "carbon", title: "7. Carbon Attribution Math", icon: <TrendingUp className="w-4 h-4" /> },
    { id: "esg", title: "8. ESG Score Calculations", icon: <GlobeIcon className="w-4 h-4" /> },
    { id: "api", title: "9. API Contracts & Routers", icon: <Code className="w-4 h-4" /> },
    { id: "roadmap", title: "10. Product Roadmap & Future", icon: <BookOpen className="w-4 h-4" /> }
  ];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col font-sans">
      
      {/* Doc header */}
      <header className="sticky top-0 z-40 bg-white border-b border-slate-200/60 px-6 py-4 flex justify-between items-center shadow-xs">
        <div className="flex items-center space-x-3">
          <button 
            onClick={() => router.push("/")}
            className="p-1.5 hover:bg-slate-50 text-slate-500 rounded-lg transition-colors border border-slate-200/40"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <span className="font-black text-slate-900 tracking-tight text-base">Sustain<span className="text-emerald-600">OCPM</span> Docs</span>
            <span className="text-[9px] block text-slate-400 uppercase tracking-widest font-bold -mt-0.5">Reference Manual</span>
          </div>
        </div>
        <button 
          onClick={() => router.push("/dashboard")} 
          className="text-xs bg-slate-900 hover:bg-slate-800 text-white font-bold px-4 py-2 rounded-lg transition-all"
        >
          Open Console
        </button>
      </header>

      {/* Docs Body */}
      <div className="flex-1 flex max-w-7xl w-full mx-auto items-stretch">
        
        {/* Left Navigation bar */}
        <aside className="w-72 border-r border-slate-200/60 bg-white p-5 space-y-2 hidden md:block shrink-0">
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3 pl-3">Manual Sections</div>
          {sections.map((sec) => (
            <button
              key={sec.id}
              onClick={() => setActiveSection(sec.id)}
              className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-bold transition-all ${
                activeSection === sec.id 
                  ? "bg-emerald-50 text-emerald-700 border border-emerald-100/50" 
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
              }`}
            >
              <div className="flex items-center space-x-2.5">
                {sec.icon}
                <span>{sec.title}</span>
              </div>
              <ChevronRight className="w-3.5 h-3.5 opacity-60" />
            </button>
          ))}
        </aside>

        {/* Right Content details */}
        <main className="flex-1 bg-white p-8 overflow-y-auto max-w-4xl">
          
          {/* Section 1: Intro */}
          {activeSection === "intro" && (
            <article className="space-y-6">
              <h1 className="text-2xl font-black text-slate-900 tracking-tight border-b pb-3 border-slate-100">
                1. Introduction & Value Proposition
              </h1>
              <p className="text-xs text-slate-600 leading-relaxed font-semibold">
                SustainOCPM is a state-of-the-art sustainability conformance checking and discovery platform designed for modern compliance standards (such as the Indo-Swiss grant evaluations and industry ESG score reporting).
              </p>
              <p className="text-xs text-slate-600 leading-relaxed font-semibold">
                Unlike traditional process mining frameworks that focus strictly on time, cost, or quality, SustainOCPM unifies operational trace sequences with Greenhouse Gas (GHG) accounting ledgers, attributing carbon emission weights directly to transactional process steps.
              </p>
              <div className="bg-slate-50 border border-slate-100 p-4 rounded-lg space-y-2">
                <h3 className="font-extrabold text-xs text-slate-800">Core Value Hooks:</h3>
                <ul className="list-disc list-inside text-[11px] text-slate-500 space-y-1.5 leading-normal">
                  <li><strong>Carbon Attributions:</strong> Track Scope 3 supply chain emissions from process traces.</li>
                  <li><strong>Compliance Auditing:</strong> Run replay check models to prove zero deviation drifts.</li>
                  <li><strong>AI Explanations:</strong> Local Ollama models describe conformance drifts in plain English.</li>
                </ul>
              </div>
            </article>
          )}

          {/* Section 2: Architecture */}
          {activeSection === "arch" && (
            <article className="space-y-6">
              <h1 className="text-2xl font-black text-slate-900 tracking-tight border-b pb-3 border-slate-100">
                2. System Architecture
              </h1>
              <p className="text-xs text-slate-600 leading-relaxed font-semibold">
                SustainOCPM unifies a React Next.js frontend console with a high-performance FastAPI backend using standard PM4Py process mining libraries and a local Ollama AI model interface.
              </p>
              <div className="border border-slate-150 rounded-lg p-5 bg-slate-50 font-mono text-[10px] text-slate-600 space-y-2 leading-relaxed">
                <div>[Frontend UI console] &rarr; Next.js / React Flow / Tailwind CSS</div>
                <div>&nbsp;&nbsp;&nbsp;&nbsp;↓ (Secure JSON API Requests via JWT bearer tokens)</div>
                <div>[FastAPI Backend Router] &rarr; Endpoint validation &amp; Role checking</div>
                <div>&nbsp;&nbsp;&nbsp;&nbsp;↓ (Local Computations)</div>
                <div>[PM4Py Engine] &rarr; Discovery nets, Conformance checking token replay</div>
                <div>[Ollama Engine] &rarr; qwen2.5:1.5b local LLM insight synthesis</div>
                <div>&nbsp;&nbsp;&nbsp;&nbsp;↓ (Persistent Data Stores)</div>
                <div>[SQLite Database] &rarr; sustainocpm.db transactional tables ledger</div>
              </div>
            </article>
          )}

          {/* Section 3: Schema */}
          {activeSection === "schema" && (
            <article className="space-y-6">
              <h1 className="text-2xl font-black text-slate-900 tracking-tight border-b pb-3 border-slate-100">
                3. Database Ledger Schema
              </h1>
              <p className="text-xs text-slate-600 leading-relaxed font-semibold">
                SustainOCPM utilizes a relational database ledger structure to ensure tenant isolation, data lineage tracking, and audit-ready reports.
              </p>
              <div className="border border-slate-100 rounded-lg overflow-hidden bg-white">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-100 font-bold text-slate-500 uppercase text-[9px]">
                      <th className="px-4 py-2">Table Name</th>
                      <th className="px-4 py-2">Key Columns</th>
                      <th className="px-4 py-2">Description</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-600 font-medium">
                    <tr>
                      <td className="px-4 py-2.5 font-bold text-slate-800 font-mono">datasets</td>
                      <td className="px-4 py-2.5 font-mono text-[10px]">id, name, headers, mappings</td>
                      <td className="px-4 py-2.5">Stores uploaded raw log metadata.</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-2.5 font-bold text-slate-800 font-mono">process_analyses</td>
                      <td className="px-4 py-2.5 font-mono text-[10px]">id, status, version</td>
                      <td className="px-4 py-2.5">Discovery run details and status.</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-2.5 font-bold text-slate-800 font-mono">conformance_results</td>
                      <td className="px-4 py-2.5 font-mono text-[10px]">id, fitness_score, actual_emissions</td>
                      <td className="px-4 py-2.5">Token replay conformance fitness score.</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-2.5 font-bold text-slate-800 font-mono">esg_scores</td>
                      <td className="px-4 py-2.5 font-mono text-[10px]">id, overall_score, calculated_at</td>
                      <td className="px-4 py-2.5">Evaluated environmental/social weights.</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </article>
          )}

          {/* Section 4: Ingestion */}
          {activeSection === "ingestion" && (
            <article className="space-y-6">
              <h1 className="text-2xl font-black text-slate-900 tracking-tight border-b pb-3 border-slate-100">
                4. Data Ingestion Standards
              </h1>
              <p className="text-xs text-slate-600 leading-relaxed font-semibold">
                Event logs ingested into SustainOCPM must adhere to standard tabular CSV guidelines containing at least three fundamental process mining attributes:
              </p>
              <ul className="list-decimal list-inside text-xs text-slate-500 space-y-2 leading-relaxed">
                <li><strong>Case ID:</strong> A unique transaction key grouping event trace routes.</li>
                <li><strong>Activity Name:</strong> The descriptive operational state name (e.g. "Create Purchase Order").</li>
                <li><strong>Timestamp:</strong> Execution date and time supporting ISO 8601 formatting strings.</li>
              </ul>
            </article>
          )}

          {/* Section 5: Heuristics */}
          {activeSection === "heuristics" && (
            <article className="space-y-6">
              <h1 className="text-2xl font-black text-slate-900 tracking-tight border-b pb-3 border-slate-100">
                5. Process Discovery Heuristics
              </h1>
              <p className="text-xs text-slate-600 leading-relaxed font-semibold">
                SustainOCPM applies process discovery heuristics to structure direct-follower graphs. For logs containing under 20 unique activity definitions, the system automatically runs the **Inductive Miner** process. For larger nets, the **Heuristics Miner** is executed to clip noise routes.
              </p>
              <div className="bg-slate-50 border border-slate-100 p-4 rounded-lg text-xs leading-relaxed space-y-2">
                <span className="font-bold text-slate-800">Inductive Miner Principle:</span>
                <p className="text-slate-500 text-[10.5px]">
                  Extracts block-structured process trees from direct-following graph (DFG) partitions, guaranteeing sound execution nodes without deadlock loops.
                </p>
              </div>
            </article>
          )}

          {/* Section 6: Conformance */}
          {activeSection === "conformance" && (
            <article className="space-y-6">
              <h1 className="text-2xl font-black text-slate-900 tracking-tight border-b pb-3 border-slate-100">
                6. Conformance Checking Engine
              </h1>
              <p className="text-xs text-slate-600 leading-relaxed font-semibold">
                Operational compliance is calculated using token replay algorithms over PNML nets. The conformance engine matches event traces to state places.
              </p>
              <div className="bg-emerald-50/20 border border-emerald-100 p-4 rounded-lg text-xs leading-relaxed space-y-2">
                <h4 className="font-bold text-emerald-950">Fitness Calculation Formula:</h4>
                <div className="font-mono text-center text-sm my-2 text-emerald-900">
                  Fitness = 0.5 * (1 - m/c) + 0.5 * (1 - r/p)
                </div>
                <p className="text-slate-500 text-[10px] leading-normal mt-1">
                  Where: <strong>m</strong> = missing tokens, <strong>c</strong> = consumed tokens, <strong>r</strong> = remaining tokens, and <strong>p</strong> = produced tokens.
                </p>
              </div>
            </article>
          )}

          {/* Section 7: Carbon */}
          {activeSection === "carbon" && (
            <article className="space-y-6">
              <h1 className="text-2xl font-black text-slate-900 tracking-tight border-b pb-3 border-slate-100">
                7. Carbon Attribution Math
              </h1>
              <p className="text-xs text-slate-600 leading-relaxed font-semibold">
                Emissions are calculated per event by resolving carbon factors from the global or tenant-scoped emission factors ledger:
              </p>
              <div className="bg-slate-50 border border-slate-100 p-4 rounded-lg text-xs leading-relaxed space-y-2">
                <h4 className="font-bold text-slate-800">Carbon Attribution Formula:</h4>
                <div className="font-mono text-center text-slate-700 my-2">
                  Emissions = Event Value * Factor Value
                </div>
                <p className="text-slate-400 text-[10px] leading-normal">
                  Total process emissions correspond to the sum of all individual activity event allocations.
                </p>
              </div>
            </article>
          )}

          {/* Section 8: ESG */}
          {activeSection === "esg" && (
            <article className="space-y-6">
              <h1 className="text-2xl font-black text-slate-900 tracking-tight border-b pb-3 border-slate-100">
                8. ESG Score Calculations
              </h1>
              <p className="text-xs text-slate-600 leading-relaxed font-semibold">
                SustainOCPM scoring profiles evaluate environmental, social, and governance allocations. Overall score unifies completeness scales.
              </p>
              <div className="bg-slate-50 border border-slate-100 p-4 rounded-lg text-xs leading-relaxed space-y-2">
                <h4 className="font-bold text-slate-800">Overall Score Balance:</h4>
                <div className="font-mono text-center text-slate-700 my-2">
                  Overall = (Env * 0.4) + (Soc * 0.3) + (Gov * 0.3)
                </div>
              </div>
            </article>
          )}

          {/* Section 9: API */}
          {activeSection === "api" && (
            <article className="space-y-6">
              <h1 className="text-2xl font-black text-slate-900 tracking-tight border-b pb-3 border-slate-100">
                9. API Contracts & Routers
              </h1>
              <p className="text-xs text-slate-600 leading-relaxed font-semibold">
                The FastAPI backend registers the following core routes consumed by the SustainOCPM console:
              </p>
              <div className="border border-slate-100 rounded-lg overflow-hidden bg-white">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-100 font-bold text-slate-500 uppercase text-[9px]">
                      <th className="px-4 py-2">Method</th>
                      <th className="px-4 py-2">Endpoint</th>
                      <th className="px-4 py-2">Description</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-600 font-medium font-mono text-[10.5px]">
                    <tr>
                      <td className="px-4 py-2 font-bold text-blue-600">GET</td>
                      <td className="px-4 py-2 text-slate-800">/api/process/history</td>
                      <td className="px-4 py-2 font-sans text-xs">Fetch history runs for workspace.</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-2 font-bold text-blue-600">GET</td>
                      <td className="px-4 py-2 text-slate-800">/api/process/&#123;id&#125;</td>
                      <td className="px-4 py-2 font-sans text-xs">Get summary details for analysis.</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-2 font-bold text-blue-600">GET</td>
                      <td className="px-4 py-2 text-slate-800">/api/process/&#123;id&#125;/conformance</td>
                      <td className="px-4 py-2 font-sans text-xs">Run conformance check token replay.</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-2 font-bold text-blue-600">GET</td>
                      <td className="px-4 py-2 text-slate-800">/api/process/&#123;id&#125;/carbon-attribution</td>
                      <td className="px-4 py-2 font-sans text-xs">Calculate carbon allocations per node.</td>
                    </tr>
                    <tr>
                      <td className="px-4 py-2 font-bold text-blue-600">GET</td>
                      <td className="px-4 py-2 text-slate-800">/api/v1/esg/scores</td>
                      <td className="px-4 py-2 font-sans text-xs">Get ESG scores list for workspace.</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </article>
          )}

          {/* Section 10: Roadmap */}
          {activeSection === "roadmap" && (
            <article className="space-y-6">
              <h1 className="text-2xl font-black text-slate-900 tracking-tight border-b pb-3 border-slate-100">
                10. Product Roadmap & Grant Goals
              </h1>
              <p className="text-xs text-slate-600 leading-relaxed font-semibold">
                SustainOCPM aims to evolve into the premier academic and commercial platform demonstrating object-centric process mining novelty. Future roadmap outlines multi-entity resource allocations, blockchain audit trails for GHG evidence, and real-time alerts.
              </p>
              <div className="bg-emerald-50/20 border border-emerald-100 p-4 rounded-lg text-xs leading-relaxed text-emerald-800 font-semibold">
                Indo-Swiss Grant Review Evaluation Benchmarks: 100% compliance verification, validated local LLM qwen2.5:1.5b accountability, and zero layout overflow errors.
              </div>
            </article>
          )}

        </main>

      </div>
    </div>
  );
}

// Simple Globe Icon helper to avoid Lucide resolution differences
function GlobeIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="10" />
      <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" />
      <path d="M2 12h20" />
    </svg>
  );
}
