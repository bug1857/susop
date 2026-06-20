"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "../../../context/AuthContext";
import { useCopilot } from "../../../context/CopilotContext";
import { Card } from "../../../components/Card";
import { Button } from "../../../components/Button";
import { api } from "../../../services/api";
import { formatMetric } from "../../../services/format";
import {
  Sparkles,
  FileText,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Map,
  Shield,
  Layers,
  Database,
  Zap,
  Download,
  FileDown,
  Loader2,
  Info,
  ChevronDown,
  ChevronUp
} from "lucide-react";

// ─── Safe Date Formatter ────────────────────────────────────────────────────
function safeDateFormat(
  raw: string | null | undefined,
  options: Intl.DateTimeFormatOptions = { day: "2-digit", month: "short", year: "numeric" }
): string {
  if (!raw) return "Date Unavailable";
  // Normalize: remove trailing Z after +00:00 (e.g. "+00:00Z" → "Z")
  const cleaned = raw
    .replace(/\+00:00Z$/i, "Z")
    .replace(/\+00:00$/, "Z");
  const d = new Date(cleaned);
  if (isNaN(d.getTime())) return "Date Unavailable";
  return d.toLocaleDateString("en-GB", options);
}

function safeTimeFormat(raw: string | null | undefined): string {
  if (!raw) return "Timestamp Unavailable";
  const cleaned = raw.replace(/\+00:00Z$/i, "Z").replace(/\+00:00$/, "Z");
  const d = new Date(cleaned);
  if (isNaN(d.getTime())) return "Timestamp Unavailable";
  return d.toLocaleString("en-GB", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit", timeZone: "UTC", timeZoneName: "short"
  });
}

// ─── Local Interfaces ────────────────────────────────────────────────────────
interface BRSRReport {
  report_id: string;
  analysis_id: string;
  workspace_id: string;
  tenant_id: string;
  generated_at: string;
  report_version: number;
  status: string;
  report_completeness_score: number;
  report_completeness_breakdown?: {
    section_a: number;
    section_b: number;
    section_c: number;
    recommendations: number;
  };
  audit_readiness?: string;
  executive_summary?: string;
  sha256_hash?: string;
  export_ready: boolean;
  report_type: string;
  schema_version: string;
  pdf_available?: boolean;
  docx_available?: boolean;
  pdf_path?: string | null;
  docx_path?: string | null;
  last_exported_at?: string | null;
  generated_from_analysis_version: number;
  generated_from_dataset_id: string;
  generated_from_dataset_name?: string;
  generated_from_project_id: string;
  snapshot_timestamp: string;
  section_a: {
    organization_id: string;
    organization_name: string;
    workspace_id: string;
    workspace_name: string;
    project_id: string;
    project_name: string;
    dataset_id: string;
    dataset_name: string;
    reporting_period: string;
    report_boundary: string;
  };
  section_b: {
    compliance_score: number;
    carbon_fitness: number;
    actual_emissions: number;
    conformance_method: string;
    total_trace_count: number;
    non_conforming_trace_count: number;
    reference_model_id: string;
    reference_model_version: number;
    deviations_count: number;
    deviations: Array<{
      case_id: string;
      activity_name: string;
      deviation_type: string;
      expected_transition: string | null;
      actual_transition: string | null;
      severity: string;
    }>;
    bottlenecks: Array<{
      activity_name: string;
      average_wait_time_sec: number;
      occurrence_count: number;
    }>;
    bottleneck_summary?: { total_bottlenecks: number; activities_impacted: number };
    variant_statistics?: { total_variants: number; variant_distribution: Array<{ variant_id: string; frequency: number; percentage: number }> };
    deviation_summary?: { total_deviations: number; by_severity: { High: number; Medium: number; Low: number } };
  };
  section_c: {
    esg_overall_score: number;
    environmental_score: number;
    social_score: number;
    governance_score: number;
    completeness_score: number;
    total_energy_consumption_kwh: number;
    total_water_consumption_liters: number;
    total_waste_generation_kg: number;
    total_actual_emissions_kg: number;
    carbon_budget_limit_kg: number;
    carbon_budget_exceeded: boolean;
    total_suppliers_tracked: number;
    supplier_esg_rankings: Array<{
      supplier_id: string; supplier_name: string; supplier_country: string;
      emissions: number; spend: number; risk_level: string; esg_score: number;
    }>;
    supplier_risk_rankings: Array<{
      supplier_id: string; supplier_name: string; supplier_country: string;
      emissions: number; spend: number; risk_level: string; esg_score: number;
    }>;
    carbon_hotspots: Array<{
      activity_name: string; emissions_kg: number; contribution_percentage: number; severity: string;
    }>;
  };
  section_d: {
    traceability_matrix: Array<{
      brsr_metric: string; originating_engine: string; database_source: string; reference_field: string;
    }>;
  };
  recommendations: Array<{
    id: string; title: string; description: string; priority: string;
    estimated_emission_reduction: number; estimated_cost_reduction: number; confidence_score: number;
  }>;
}

interface HistoryItem {
  report_id: string;
  report_version: number;
  generated_at: string;
  status: string;
  completeness_score: number;
  audit_readiness?: string;
  total_deviations?: number;
  total_emissions_kg?: number;
}

// ─── Audit Readiness Badge ───────────────────────────────────────────────────
function AuditReadinessBadge({ readiness }: { readiness: string }) {
  const variants: Record<string, string> = {
    "Audit Ready": "bg-emerald-100 text-emerald-800 border-emerald-200",
    "Near Audit Ready": "bg-blue-100 text-blue-800 border-blue-200",
    "Partial Evidence": "bg-amber-100 text-amber-800 border-amber-200",
    "Insufficient Evidence": "bg-rose-100 text-rose-800 border-rose-200",
  };
  const cls = variants[readiness] ?? "bg-slate-100 text-slate-700 border-slate-200";
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider border ${cls}`}>
      <Shield className="w-2.5 h-2.5" />
      {readiness || "N/A"}
    </span>
  );
}

// ─── Completeness Breakdown ──────────────────────────────────────────────────
function CompletenessBreakdown({ breakdown, total }: {
  breakdown?: { section_a: number; section_b: number; section_c: number; recommendations: number };
  total: number;
}) {
  const [open, setOpen] = useState(false);
  if (!breakdown) return null;

  const items = [
    { label: "Section A — General Disclosures", score: breakdown.section_a, max: 25 },
    { label: "Section B — Process Disclosures", score: breakdown.section_b, max: 25 },
    { label: "Section C — ESG Performance", score: breakdown.section_c, max: 25 },
    { label: "Recommendations", score: breakdown.recommendations, max: 25 },
  ];

  return (
    <div className="w-full mt-3">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center justify-between w-full text-xs font-bold text-slate-500 hover:text-slate-700 transition-colors pb-1"
      >
        <span>Score Breakdown</span>
        {open ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
      </button>
      {open && (
        <div className="space-y-2 pt-2">
          {items.map((item) => (
            <div key={item.label}>
              <div className="flex justify-between text-[10px] font-semibold text-slate-500 mb-0.5">
                <span>{item.label}</span>
                <span className={item.score === item.max ? "text-emerald-600 font-black" : "text-amber-600 font-black"}>
                  {item.score}/{item.max}
                </span>
              </div>
              <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${item.score === item.max ? "bg-emerald-500" : item.score > 0 ? "bg-amber-400" : "bg-rose-400"}`}
                  style={{ width: `${(item.score / item.max) * 100}%` }}
                />
              </div>
            </div>
          ))}
          <div className="flex justify-between text-xs font-black text-slate-700 pt-1 border-t border-slate-100 mt-1">
            <span>Total</span>
            <span>{total}/100</span>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────────────────────
export default function BRSRPage() {
  const { token, activeWorkspace } = useAuth();
  const { selectedAnalysisId } = useCopilot();

  const [activeTab, setActiveTab] = useState<"overview" | "section_a" | "section_b" | "section_c" | "section_d" | "recommendations">("overview");
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [selectedReportId, setSelectedReportId] = useState<string>("");
  const [report, setReport] = useState<BRSRReport | null>(null);

  const [generating, setGenerating] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Export states
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [downloadingDocx, setDownloadingDocx] = useState(false);
  const [exportSuccess, setExportSuccess] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  // Load history list
  const loadHistory = useCallback(async (analysisId: string) => {
    try {
      const res = await api.get(`/api/v1/brsr/history/${analysisId}`);
      setHistory(res.data);
      if (res.data.length > 0) {
        // Default select latest version (newest first)
        setSelectedReportId(res.data[0].report_id);
      } else {
        setSelectedReportId("");
        setReport(null);
      }
    } catch (err: any) {
      console.error("Error loading BRSR history:", err);
      setHistory([]);
    }
  }, []);

  // Load specific report contents
  const loadReport = useCallback(async (reportId: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get(`/api/v1/brsr/${reportId}`);
      setReport(res.data);
    } catch (err: any) {
      console.error("Error loading report:", err);
      setError("Failed to load selected BRSR report version.");
      setReport(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedAnalysisId) {
      loadHistory(selectedAnalysisId);
    } else {
      setHistory([]);
      setSelectedReportId("");
      setReport(null);
    }
  }, [selectedAnalysisId, loadHistory]);

  useEffect(() => {
    if (selectedReportId) {
      loadReport(selectedReportId);
    }
  }, [selectedReportId, loadReport]);

  const handleGenerateReport = async () => {
    if (!selectedAnalysisId) return;
    setGenerating(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await api.post("/api/v1/brsr/generate", { analysis_id: selectedAnalysisId });
      setSuccess(`Successfully generated BRSR Report Version ${res.data.report_version} (${res.data.audit_readiness})!`);
      await loadHistory(selectedAnalysisId);
      setSelectedReportId(res.data.report_id);
    } catch (err: any) {
      setError(
        err?.response?.data?.detail ||
        err.message ||
        "Analysis is not eligible for BRSR generation. Please ensure conformance and carbon attribution checks are completed first."
      );
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = async (format: "pdf" | "docx") => {
    if (!report) return;
    const setter = format === "pdf" ? setDownloadingPdf : setDownloadingDocx;
    setter(true);
    setExportError(null);
    setExportSuccess(null);
    try {
      const res = await api.get(`/api/v1/brsr/${report.report_id}/${format}`, {
        responseType: "blob"
      });
      const mimeType = format === "pdf" ? "application/pdf"
        : "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
      const url = URL.createObjectURL(new Blob([res.data], { type: mimeType }));
      const link = document.createElement("a");
      link.href = url;
      link.download = `BRSR_Report_v${report.report_version}_${report.report_id.slice(0, 8)}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      setExportSuccess(`${format.toUpperCase()} report downloaded successfully.`);
      // Refresh to pick up updated pdf_available / docx_available flags
      loadReport(report.report_id);
    } catch (err: any) {
      const detail = err?.response?.data?.error || err.message || `Failed to generate ${format.toUpperCase()} export.`;
      setExportError(detail);
    } finally {
      setter(false);
    }
  };

  const getCompletenessColor = (score: number) => {
    if (score >= 95) return "text-emerald-500 stroke-emerald-500";
    if (score >= 80) return "text-blue-500 stroke-blue-500";
    if (score >= 60) return "text-amber-500 stroke-amber-500";
    return "text-rose-500 stroke-rose-500";
  };

  // Version selector label
  const versionLabel = (h: HistoryItem) => {
    const dateStr = safeDateFormat(h.generated_at);
    const readiness = h.audit_readiness ? ` • ${h.audit_readiness}` : "";
    return `v${h.report_version} • ${dateStr} • ${h.completeness_score}% Complete${readiness}`;
  };

  return (
    <div className="w-full space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            <FileText className="w-8 h-8 text-blue-600" />
            BRSR Compliance Center
          </h1>
          <p className="text-slate-500 font-medium mt-1">
            Compile SEBI-aligned Business Responsibility and Sustainability Reports dynamically from operational logs.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          {history.length > 0 && (
            <div className="flex items-center gap-2">
              <label className="text-xs font-black text-slate-500 uppercase tracking-wider">Report Version:</label>
              <select
                className="px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs font-bold text-slate-700 shadow-xs focus:ring-2 focus:ring-blue-500 focus:outline-none max-w-xs"
                value={selectedReportId}
                onChange={(e) => setSelectedReportId(e.target.value)}
              >
                {history.map((h) => (
                  <option key={h.report_id} value={h.report_id}>
                    {versionLabel(h)}
                  </option>
                ))}
              </select>
            </div>
          )}
          <Button
            variant="primary"
            onClick={handleGenerateReport}
            disabled={generating || !selectedAnalysisId}
            className="flex items-center gap-2 font-bold"
          >
            <Sparkles className="w-4 h-4" />
            {generating ? "Compiling Disclosures..." : "Generate BRSR Report"}
          </Button>
        </div>
      </div>

      {/* Notifications */}
      {success && (
        <div className="p-4 bg-emerald-50 border border-emerald-100 rounded-xl flex items-center gap-3 text-emerald-800 text-sm font-bold shadow-xs">
          <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
          <span>{success}</span>
        </div>
      )}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-100 rounded-xl flex items-center gap-3 text-rose-800 text-sm font-bold shadow-xs">
          <AlertCircle className="w-5 h-5 text-rose-500 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
      {exportSuccess && (
        <div className="p-3 bg-blue-50 border border-blue-100 rounded-xl flex items-center gap-3 text-blue-800 text-xs font-bold">
          <FileDown className="w-4 h-4 flex-shrink-0" />
          <span>{exportSuccess}</span>
        </div>
      )}
      {exportError && (
        <div className="p-3 bg-amber-50 border border-amber-100 rounded-xl flex items-center gap-3 text-amber-800 text-xs font-bold">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{exportError}</span>
        </div>
      )}

      {/* Main Content */}
      {!selectedAnalysisId ? (
        <Card title="No Analysis Selected" className="text-center py-12">
          <p className="text-sm font-semibold text-slate-500">
            Please select an active process analysis run from the dashboard header to generate or view compliance reports.
          </p>
        </Card>
      ) : loading ? (
        <div className="py-24 text-center space-y-3">
          <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-sm font-bold text-slate-500">Retrieving report snapshots...</p>
        </div>
      ) : !report ? (
        <Card title="Ready to Generate" className="text-center py-12 max-w-2xl mx-auto space-y-4">
          <FileText className="w-16 h-16 text-slate-300 mx-auto" />
          <h2 className="text-xl font-bold text-slate-800">No BRSR report generated yet</h2>
          <p className="text-sm text-slate-500 font-semibold leading-relaxed">
            Generate an automated disclosure mapping for Section A (General), Section B (Process and Compliance), and Section C (Performance ESG details) of the SEBI framework for this analysis run.
          </p>
          <Button variant="primary" onClick={handleGenerateReport} disabled={generating} className="mx-auto">
            Generate Version 1 Report
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-4">
            {/* Completeness Scorecard */}
            <Card title="Compliance Scorecard" className="flex flex-col items-center py-6">
              <div className="relative w-32 h-32 flex items-center justify-center">
                <svg className="absolute w-full h-full transform -rotate-90">
                  <circle cx="64" cy="64" r="54" className="stroke-slate-100 fill-none" strokeWidth="8" />
                  <circle
                    cx="64" cy="64" r="54"
                    className={`fill-none transition-all duration-500 ${getCompletenessColor(report.report_completeness_score)}`}
                    strokeWidth="8"
                    strokeDasharray={2 * Math.PI * 54}
                    strokeDashoffset={2 * Math.PI * 54 * (1 - report.report_completeness_score / 100)}
                    strokeLinecap="round"
                  />
                </svg>
                <div className="text-center">
                  <span className="text-2xl font-black text-slate-800">{report.report_completeness_score}%</span>
                  <span className="block text-[10px] text-slate-400 font-bold uppercase tracking-wider mt-0.5">Ready</span>
                </div>
              </div>

              {/* Audit Readiness Badge */}
              {report.audit_readiness && (
                <div className="mt-3">
                  <AuditReadinessBadge readiness={report.audit_readiness} />
                </div>
              )}

              {/* Metadata */}
              <div className="w-full border-t border-slate-100 my-4 pt-3 space-y-2 text-xs font-semibold text-slate-600">
                <div className="flex justify-between">
                  <span>Report Version:</span>
                  <span className="font-bold text-slate-800">v{report.report_version}</span>
                </div>
                <div className="flex justify-between">
                  <span>Report Status:</span>
                  <span className="font-bold text-emerald-600 capitalize">{report.status}</span>
                </div>
                <div className="flex justify-between">
                  <span>Snapshot Time:</span>
                  <span className="font-bold text-slate-800">{safeDateFormat(report.snapshot_timestamp)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Generated:</span>
                  <span className="font-bold text-slate-800">{safeDateFormat(report.generated_at)}</span>
                </div>
              </div>

              {/* Completeness Breakdown */}
              <CompletenessBreakdown
                breakdown={report.report_completeness_breakdown}
                total={report.report_completeness_score}
              />
            </Card>

            {/* Export Actions */}
            <Card title="Export Report">
              <div className="space-y-2">
                <p className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider mb-3">Download As</p>
                <button
                  onClick={() => handleDownload("pdf")}
                  disabled={downloadingPdf}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-rose-600 hover:bg-rose-700 disabled:bg-rose-300 text-white text-xs font-black rounded-lg transition-all shadow-sm"
                >
                  {downloadingPdf ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> Generating PDF...</>
                  ) : (
                    <><Download className="w-4 h-4" /> Download PDF</>
                  )}
                </button>
                <button
                  onClick={() => handleDownload("docx")}
                  disabled={downloadingDocx}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white text-xs font-black rounded-lg transition-all shadow-sm"
                >
                  {downloadingDocx ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> Generating DOCX...</>
                  ) : (
                    <><FileDown className="w-4 h-4" /> Download DOCX</>
                  )}
                </button>

                {/* Export Status */}
                {(report.pdf_available || report.docx_available) && (
                  <div className="pt-2 space-y-1 text-[10px] font-semibold text-slate-500">
                    {report.pdf_available && (
                      <div className="flex items-center gap-1.5 text-emerald-600">
                        <CheckCircle className="w-3 h-3" /> PDF generated
                      </div>
                    )}
                    {report.docx_available && (
                      <div className="flex items-center gap-1.5 text-emerald-600">
                        <CheckCircle className="w-3 h-3" /> DOCX generated
                      </div>
                    )}
                    {report.last_exported_at && (
                      <div className="text-slate-400">
                        Last exported: {safeTimeFormat(report.last_exported_at)}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </Card>

            {/* Navigation Tabs */}
            <div className="flex flex-col gap-1.5">
              {[
                { id: "overview", label: "Executive Overview", icon: <Layers className="w-4 h-4" /> },
                { id: "section_a", label: "Section A: General", icon: <Shield className="w-4 h-4" /> },
                { id: "section_b", label: "Section B: Process", icon: <Map className="w-4 h-4" /> },
                { id: "section_c", label: "Section C: Performance", icon: <TrendingUp className="w-4 h-4" /> },
                { id: "section_d", label: "Section D: Traceability", icon: <Database className="w-4 h-4" /> },
                {
                  id: "recommendations",
                  label: `Recommendations (${report.recommendations.length})`,
                  icon: <Sparkles className="w-4 h-4" />
                },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as typeof activeTab)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all text-left ${
                    activeTab === tab.id
                      ? "bg-blue-600 text-white shadow-md shadow-blue-200"
                      : "bg-white text-slate-600 hover:bg-slate-50 border border-slate-100/60"
                  }`}
                >
                  {tab.icon}
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Tab Content */}
          <div className="lg:col-span-3 space-y-6">

            {/* OVERVIEW */}
            {activeTab === "overview" && (
              <div className="space-y-6">
                <Card title="Executive Audit Readiness Summary" className="space-y-4">
                  {report.executive_summary ? (
                    <div className="p-4 rounded-xl bg-blue-50 border border-blue-100/40 text-slate-700 text-sm font-medium leading-relaxed">
                      {report.executive_summary}
                    </div>
                  ) : (
                    <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 text-slate-500 text-xs font-semibold">
                      💡 This BRSR Report (v{report.report_version}) aggregates transaction-level proofs from workspace <strong>{report.section_a.workspace_name}</strong>. 
                      Completeness: <strong>{report.report_completeness_score}%</strong>.
                    </div>
                  )}

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[
                      { label: "Overall ESG", value: formatMetric(report.section_c.esg_overall_score, "percent") },
                      { label: "Process Fitness", value: formatMetric(report.section_b.compliance_score, "percent") },
                      { label: "Carbon Fitness", value: formatMetric(report.section_b.carbon_fitness, "percent") },
                      { label: "Total Emissions", value: `${Number(report.section_c.total_actual_emissions_kg).toLocaleString()} kg` },
                    ].map((kpi) => (
                      <div key={kpi.label} className="p-4 rounded-xl border border-slate-100 bg-slate-50/50">
                        <span className="block text-[10px] text-slate-400 font-extrabold uppercase tracking-wider">{kpi.label}</span>
                        <span className="text-xl font-black text-slate-800">{kpi.value}</span>
                      </div>
                    ))}
                  </div>
                </Card>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Snapshot Integrity */}
                  <Card title="Snapshot Integrity Verification">
                    <div className="space-y-2.5 text-xs font-semibold text-slate-600">
                      {[
                        { label: "Report ID:", value: report.report_id, mono: true },
                        { label: "Report Version:", value: `Version ${report.report_version}` },
                        { label: "Analysis Run Version:", value: `Version ${report.generated_from_analysis_version}` },
                        { label: "Analysis ID:", value: report.analysis_id, mono: true },
                        { label: "Source Dataset:", value: report.generated_from_dataset_name || report.generated_from_dataset_id, mono: true },
                        { label: "Project Context ID:", value: report.generated_from_project_id, mono: true },
                        { label: "Workspace ID:", value: report.workspace_id, mono: true },
                        { label: "Generated Timestamp:", value: safeTimeFormat(report.generated_at) },
                        { label: "SHA256 Hash:", value: report.sha256_hash || "N/A", mono: true },
                      ].map(({ label, value, mono }) => (
                        <div key={label} className="flex justify-between border-b border-slate-50 pb-2">
                          <span>{label}</span>
                          <span
                            className={`font-bold text-slate-800 truncate max-w-[180px] ${mono ? "font-mono text-[9px]" : ""}`}
                            title={value}
                          >
                            {value}
                          </span>
                        </div>
                      ))}
                      <div className="flex justify-between pt-1">
                        <span>Audit Immutability Proof:</span>
                        <span className="font-bold text-emerald-600 flex items-center gap-1">
                          <Zap className="w-3.5 h-3.5" /> Immutable Snapshot
                        </span>
                      </div>
                    </div>
                  </Card>

                  {/* Compliance Flags */}
                  <Card title="Pre-Export Compliance Metrics">
                    <div className="space-y-3 text-xs font-semibold">
                      <div className="flex justify-between items-center p-2 rounded-lg bg-slate-50">
                        <span>Export Payload Status:</span>
                        <span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded font-black uppercase text-[10px]">Sprint 3B Ready</span>
                      </div>
                      <div className="flex justify-between items-center p-2 rounded-lg bg-slate-50">
                        <span>Regulatory Framework:</span>
                        <span className="font-black text-slate-800">SEBI BRSR</span>
                      </div>
                      <div className="flex justify-between items-center p-2 rounded-lg bg-slate-50">
                        <span>Carbon Budget Conformance:</span>
                        <span className={`px-2 py-0.5 rounded font-black text-[10px] ${report.section_c.carbon_budget_exceeded ? "bg-rose-50 text-rose-700" : "bg-emerald-50 text-emerald-700"}`}>
                          {report.section_c.carbon_budget_exceeded ? "EXCEEDED LIMIT" : "CONFORMING"}
                        </span>
                      </div>
                      <div className="flex justify-between items-center p-2 rounded-lg bg-slate-50">
                        <span>PDF Export Ready:</span>
                        <span className={`px-2 py-0.5 rounded font-black text-[10px] ${report.pdf_available ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>
                          {report.pdf_available ? "Generated" : "Not yet exported"}
                        </span>
                      </div>
                      <div className="flex justify-between items-center p-2 rounded-lg bg-slate-50">
                        <span>DOCX Export Ready:</span>
                        <span className={`px-2 py-0.5 rounded font-black text-[10px] ${report.docx_available ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>
                          {report.docx_available ? "Generated" : "Not yet exported"}
                        </span>
                      </div>
                    </div>
                  </Card>
                </div>
              </div>
            )}

            {/* SECTION A */}
            {activeTab === "section_a" && (
              <Card title="Section A: General Disclosures">
                <div className="space-y-4 text-xs font-semibold text-slate-600">
                  <h3 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-2">I. Details of the Listed Entity</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[
                      { label: "Corporate Entity Name", value: report.section_a.organization_name },
                      { label: "Reporting Workspace Context", value: report.section_a.workspace_name },
                      { label: "Reporting Year / Period", value: report.section_a.reporting_period },
                      { label: "Operational Boundary", value: report.section_a.report_boundary },
                    ].map(({ label, value }) => (
                      <div key={label}>
                        <span className="block text-[10px] text-slate-400 font-bold uppercase">{label}:</span>
                        <span className="font-bold text-slate-800 text-sm mt-0.5 block">{value}</span>
                      </div>
                    ))}
                  </div>
                  <h3 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-2 pt-4">II. Project & Ingest Source Context</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[
                      { label: "Project Identifier", value: report.section_a.project_name },
                      { label: "Source Dataset / Log File", value: report.section_a.dataset_name },
                    ].map(({ label, value }) => (
                      <div key={label}>
                        <span className="block text-[10px] text-slate-400 font-bold uppercase">{label}:</span>
                        <span className="font-bold text-slate-800 text-sm mt-0.5 block truncate" title={value}>{value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>
            )}

            {/* SECTION B */}
            {activeTab === "section_b" && (
              <div className="space-y-6">
                <Card title="Section B: Management and Process Disclosures">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 border-b border-slate-100 pb-4">
                    <div>
                      <span className="block text-[10px] text-slate-400 font-extrabold uppercase">Conformance Method:</span>
                      <span className="font-black text-slate-800 text-sm block mt-1">{report.section_b.conformance_method}</span>
                    </div>
                    <div>
                      <span className="block text-[10px] text-slate-400 font-extrabold uppercase">Total Process Traces:</span>
                      <span className="font-black text-slate-800 text-sm block mt-1">{Number(report.section_b.total_trace_count).toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="block text-[10px] text-slate-400 font-extrabold uppercase">Total Deviations Detected:</span>
                      <span className="font-black text-rose-600 text-sm block mt-1">{report.section_b.deviations_count}</span>
                    </div>
                  </div>
                  {report.section_b.bottlenecks.length > 0 && (
                    <div className="space-y-3 pt-2">
                      <h4 className="font-bold text-xs text-slate-700 uppercase tracking-wider">Process Bottlenecks & Occurrence</h4>
                      <div className="space-y-2">
                        {report.section_b.bottlenecks.map((bot, idx) => (
                          <div key={idx} className="p-3 bg-slate-50 border border-slate-100 rounded-lg flex justify-between items-center text-xs font-semibold text-slate-700">
                            <span className="font-bold text-slate-800">{bot.activity_name}</span>
                            <div className="flex gap-4">
                              <span>Occurrences: <strong className="text-slate-900">{bot.occurrence_count}</strong></span>
                              <span>Avg Wait: <strong className="text-slate-900">{bot.average_wait_time_sec.toFixed(1)}s</strong></span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </Card>
                {report.section_b.deviations.length > 0 && (
                  <Card title="Conformance Violations Audit Trail (Sample)">
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs font-semibold text-slate-600 border-collapse">
                        <thead>
                          <tr className="border-b border-slate-100 text-[10px] text-slate-400 uppercase tracking-wider font-extrabold">
                            <th className="py-2.5">Case ID</th>
                            <th className="py-2.5">Activity</th>
                            <th className="py-2.5">Violation Type</th>
                            <th className="py-2.5">Severity</th>
                          </tr>
                        </thead>
                        <tbody>
                          {report.section_b.deviations.slice(0, 5).map((dev, idx) => (
                            <tr key={idx} className="border-b border-slate-50 hover:bg-slate-50/50">
                              <td className="py-2.5 font-mono text-slate-500">{dev.case_id}</td>
                              <td className="py-2.5 font-bold text-slate-800">{dev.activity_name}</td>
                              <td className="py-2.5">{dev.deviation_type}</td>
                              <td className="py-2.5">
                                <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${dev.severity === "High" ? "bg-rose-50 text-rose-700" : dev.severity === "Medium" ? "bg-amber-50 text-amber-700" : "bg-blue-50 text-blue-700"}`}>
                                  {dev.severity}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </Card>
                )}
              </div>
            )}

            {/* SECTION C */}
            {activeTab === "section_c" && (
              <div className="space-y-6">
                <Card title="Section C: Principle-wise Performance Disclosures">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 border-b border-slate-100 pb-5">
                    {[
                      { label: "Total Energy Draw", value: `${report.section_c.total_energy_consumption_kwh.toLocaleString()} kWh` },
                      { label: "Total Water Ingest", value: `${report.section_c.total_water_consumption_liters.toLocaleString()} Liters` },
                      { label: "Total Waste Volume", value: `${report.section_c.total_waste_generation_kg.toLocaleString()} kg` },
                    ].map(({ label, value }) => (
                      <div key={label}>
                        <span className="block text-[10px] text-slate-400 font-extrabold uppercase">{label}:</span>
                        <span className="font-black text-slate-800 text-sm block mt-1">{value}</span>
                      </div>
                    ))}
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-3">
                    {/* Hotspots */}
                    <div className="space-y-3">
                      <h4 className="font-bold text-xs text-slate-700 uppercase tracking-wider flex items-center gap-1">
                        <TrendingUp className="w-4 h-4 text-rose-500" /> Carbon Hotspots
                      </h4>
                      <div className="space-y-2">
                        {report.section_c.carbon_hotspots.map((hot, idx) => (
                          <div key={idx} className="p-3 bg-slate-50 border border-slate-100 rounded-lg flex justify-between items-center text-xs font-semibold">
                            <div>
                              <span className="font-bold text-slate-800 block">{hot.activity_name}</span>
                              <span className="text-[10px] text-slate-400 uppercase mt-0.5 block">{hot.contribution_percentage.toFixed(1)}% contribution</span>
                            </div>
                            <span className="font-black text-slate-800">{hot.emissions_kg.toLocaleString()} kg</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    {/* Supplier Risk */}
                    <div className="space-y-3">
                      <h4 className="font-bold text-xs text-slate-700 uppercase tracking-wider flex items-center gap-1">
                        <Shield className="w-4 h-4 text-emerald-500" /> Supplier Risk Rankings
                      </h4>
                      <div className="space-y-2">
                        {report.section_c.supplier_risk_rankings.map((supp, idx) => (
                          <div key={idx} className="p-3 bg-slate-50 border border-slate-100 rounded-lg flex justify-between items-center text-xs font-semibold">
                            <div>
                              <span className="font-bold text-slate-800 block">{supp.supplier_name}</span>
                              <span className="text-[10px] text-slate-400 uppercase mt-0.5 block">{supp.supplier_country}</span>
                            </div>
                            <div className="text-right">
                              <span className="font-black text-slate-800 block">ESG: {formatMetric(supp.esg_score, "percent")}</span>
                              <span className={`text-[10px] font-black ${supp.risk_level === "High" ? "text-rose-600" : supp.risk_level === "Medium" ? "text-amber-600" : "text-emerald-600"}`}>
                                {supp.risk_level} Risk
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </Card>
              </div>
            )}

            {/* SECTION D */}
            {activeTab === "section_d" && (
              <Card title="Section D: SustainOCPM Analytics Traceability Matrix">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-semibold text-slate-600 border-collapse">
                    <thead>
                      <tr className="border-b border-slate-100 text-[10px] text-slate-400 uppercase tracking-wider font-extrabold">
                        <th className="py-2.5">BRSR Report Metric</th>
                        <th className="py-2.5">Originating Engine</th>
                        <th className="py-2.5">Source Database Table / File</th>
                        <th className="py-2.5">Database Column Ref</th>
                      </tr>
                    </thead>
                    <tbody>
                      {report.section_d.traceability_matrix.map((row, idx) => (
                        <tr key={idx} className="border-b border-slate-50 hover:bg-slate-50/50">
                          <td className="py-3 font-bold text-slate-800">{row.brsr_metric}</td>
                          <td className="py-3 text-blue-700 font-bold">{row.originating_engine}</td>
                          <td className="py-3 text-slate-500 font-mono">{row.database_source}</td>
                          <td className="py-3 text-slate-500 font-mono">{row.reference_field}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            )}

            {/* RECOMMENDATIONS */}
            {activeTab === "recommendations" && (
              <Card title={`Prioritized Compliance & ESG Recommendations (${report.recommendations.length})`}>
                {report.recommendations.length === 0 ? (
                  <p className="text-sm font-semibold text-slate-500 text-center py-6">
                    No recommendations found. Run ESG checks or discovery first.
                  </p>
                ) : (
                  <div className="space-y-4">
                    {report.recommendations.map((rec, idx) => (
                      <div key={idx} className="p-4 bg-slate-50 border border-slate-100 rounded-xl space-y-2">
                        <div className="flex justify-between items-start">
                          <div>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase ${rec.priority === "CRITICAL" ? "bg-purple-50 text-purple-700" : rec.priority === "HIGH" ? "bg-rose-50 text-rose-700" : rec.priority === "MEDIUM" ? "bg-amber-50 text-amber-700" : "bg-blue-50 text-blue-700"}`}>
                              {rec.priority} Priority
                            </span>
                            <h4 className="font-bold text-slate-800 text-sm mt-1">{rec.title}</h4>
                          </div>
                          <span className="text-xs font-black text-slate-400">Confidence: {(rec.confidence_score).toFixed(0)}%</span>
                        </div>
                        <p className="text-xs font-semibold text-slate-500 leading-relaxed">{rec.description}</p>
                        <div className="flex gap-4 pt-1 text-xs font-bold">
                          {rec.estimated_emission_reduction > 0 && (
                            <span className="text-emerald-700">Est. Reduction: -{rec.estimated_emission_reduction} kg CO2e</span>
                          )}
                          {rec.estimated_cost_reduction !== null && rec.estimated_cost_reduction > 0 && (
                            <span className="text-blue-700">Est. Cost Savings: ${rec.estimated_cost_reduction.toLocaleString()}</span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            )}

          </div>
        </div>
      )}
    </div>
  );
}
