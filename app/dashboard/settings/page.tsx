"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "../../../context/AuthContext";
import { api } from "../../../services/api";
import { COPILOT_ENDPOINTS } from "../../../services/copilotEndpoints";
import { useCopilot } from "../../../context/CopilotContext";
import {
  Cpu,
  Zap,
  Brain,
  Server,
  Shield,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  Save,
  Activity,
  HardDrive,
  Wifi,
  Clock,
  Settings,
  Layers,
  Play,
  Package,
} from "lucide-react";

// ─── Types ─────────────────────────────────────────────────────────────────

interface AuditLog {
  id: string;
  user_id: string;
  action: string;
  details: string;
  created_at: string;
}

interface HardwareInfo {
  cpu: string;
  ram_gb: number;
  recommended_model: string;
  max_supported_model: string;
  safe_models?: string[];
  heavy_models?: string[];
}

interface ProviderHealth {
  ollama: "connected" | "offline" | "missing_key";
  openai: "connected" | "offline" | "missing_key";
  anthropic: "connected" | "offline" | "missing_key";
}

interface AiSettings {
  provider: string;
  model_name: string;
  quality_mode: string;
  prompt_style: string;
  response_style: string;
  settings_version: number;
}

interface OllamaModelMeta {
  name: string;
  size_gb: number;
  family: string;
  capability: string;
  recommended: boolean;
  safe: boolean;
  heavy: boolean;
}

// ─── Live Test Prompt Panel ───────────────────────────────────────────────────

interface TestResponseMetadata {
  provider: string;
  model: string;
  prompt_style: string;
  response_style: string;
  quality_mode: string;
  latency_ms: number;
}

function LiveTestPanel({
  settings,
  activeWorkspace,
  selectedProjectId,
  selectedAnalysisId,
  insights,
  recommendations,
}: {
  settings: AiSettings;
  activeWorkspace: { id: string; name: string } | null;
  selectedProjectId: string | null;
  selectedAnalysisId: string | null;
  insights: { data?: Array<{ id: string; insight_type: string }> | null };
  recommendations: { data?: Array<{ id: string }> | null };
}) {
  const [testQuery, setTestQuery] = useState("Why is my ESG score low?");
  const [testResult, setTestResult] = useState<string>("");
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [testError, setTestError] = useState("");
  const [responseMeta, setResponseMeta] = useState<TestResponseMetadata | null>(null);

  const runTest = async () => {
    if (!selectedAnalysisId || !selectedProjectId || !activeWorkspace) {
      setTestError("No active analysis selected. Please select a project and analysis from the dashboard first.");
      return;
    }
    setIsTesting(true);
    setTestResult("");
    setTestError("");
    setLatencyMs(null);
    setResponseMeta(null);

    // Pick best entity
    let entityType = "INSIGHT";
    let entityId = insights.data?.[0]?.id ?? recommendations.data?.[0]?.id ?? "";
    let requestType = "INSIGHT_SUMMARY";

    if (!entityId && recommendations.data && recommendations.data.length > 0) {
      entityType = "RECOMMENDATION";
      entityId = recommendations.data[0].id;
      requestType = "RECOMMENDATION_SUMMARY";
    }

    if (!entityId) {
      setTestError("No analysis entities found. Run insights or recommendations first.");
      setIsTesting(false);
      return;
    }

    const start = Date.now();
    try {
      const res = await api.post(COPILOT_ENDPOINTS.COPILOT_GENERATE, {
        workspace_id: activeWorkspace.id,
        project_id: selectedProjectId,
        analysis_id: selectedAnalysisId,
        request_type: requestType,
        provider: settings.provider.toUpperCase(),
        entity_type: entityType,
        entity_id: entityId,
        user_query: testQuery,
      });
      const elapsed = Date.now() - start;
      setLatencyMs(elapsed);

      const data = res.data?.data;
      const reply = Array.isArray(data) ? data[0] : data;
      setTestResult(reply?.response_text ?? JSON.stringify(reply));
      if (reply?.response_metadata) {
        setResponseMeta(reply.response_metadata);
      }
    } catch (err: unknown) {
      setTestError((err as Error)?.message ?? "Test failed. Check Ollama connection and active analysis.");
    } finally {
      setIsTesting(false);
    }
  };

  return (
    <div className="bg-card-bg border border-border-color p-6 rounded shadow-sm">
      <div className="border-l-2 border-indigo-500 pl-3 mb-5">
        <h3 className="text-sm font-bold text-foreground uppercase tracking-wider">Live Test Prompt</h3>
        <p className="text-xs text-text-muted mt-0.5 font-medium">Verify your configuration instantly</p>
      </div>

      <div className="flex gap-2 mb-4">
        <input
          id="test-prompt-input"
          type="text"
          value={testQuery}
          onChange={(e) => setTestQuery(e.target.value)}
          placeholder="Why is my ESG score low?"
          className="flex-1 px-3 py-2 bg-background border border-border-color rounded text-sm text-foreground focus:outline-none focus:border-indigo-500 transition-all font-semibold"
        />
        <button
          id="run-test-btn"
          onClick={runTest}
          disabled={isTesting || !testQuery.trim()}
          className="bg-indigo-600 hover:bg-indigo-500 text-foreground font-bold text-xs py-2 px-4 rounded transition-colors disabled:opacity-50 flex items-center gap-2"
        >
          {isTesting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
          {isTesting ? "Testing…" : "Run Test"}
        </button>
      </div>

      {testError && (
        <div className="bg-red-950/40 border border-red-900 rounded p-3 mb-3 flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
          <p className="text-xs font-semibold text-red-400">{testError}</p>
        </div>
      )}

      {testResult && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-4">
          <div className="lg:col-span-2 bg-background border border-border-color rounded p-4">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wide">AI Output Response</span>
            <p className="text-xs text-foreground font-semibold whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto mt-2">
              {testResult}
            </p>
          </div>

          {/* Explainability / Why This Answer Panel */}
          <div className="bg-background border border-border-color rounded p-4 space-y-3">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wide block border-b border-border-color pb-1.5">
              Why This Answer?
            </span>
            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between">
                <span className="text-text-muted font-medium">Provider</span>
                <span className="text-foreground font-bold capitalize">{responseMeta?.provider ?? settings.provider}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted font-medium">Model</span>
                <span className="text-foreground font-mono font-bold">{responseMeta?.model ?? settings.model_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted font-medium">Prompt Persona</span>
                <span className="text-foreground font-bold capitalize">
                  {(responseMeta?.prompt_style ?? settings.prompt_style)?.replace(/_/g, " ")}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted font-medium">Response Style</span>
                <span className="text-foreground font-bold capitalize">
                  {(responseMeta?.response_style ?? settings.response_style)?.replace(/_/g, " ")}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted font-medium">Quality Mode</span>
                <span className="text-foreground font-bold capitalize">
                  {responseMeta?.quality_mode ?? settings.quality_mode}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-muted font-medium">Latency</span>
                <span className="text-emerald-400 font-mono font-bold">
                  {responseMeta?.latency_ms ? `${responseMeta.latency_ms} ms` : latencyMs ? `${latencyMs} ms` : "—"}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {!testResult && !testError && !isTesting && (
        <div className="text-center py-6 text-xs text-text-muted font-semibold border border-dashed border-border-color rounded bg-background/30">
          Response will appear here after running the test
        </div>
      )}
    </div>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────

const PROVIDERS = [
  { id: "ollama", label: "Ollama (Local)", description: "Runs locally on this machine" },
  { id: "openai", label: "OpenAI", description: "Cloud API key required" },
  { id: "anthropic", label: "Anthropic", description: "Cloud API key required" },
];

const QUALITY_MODES = [
  { id: "fast", label: "Fast", description: "Lowest latency mode" },
  { id: "balanced", label: "Balanced", description: "Standard balance settings" },
  { id: "expert", label: "Expert", description: "Maximum depth analysis" },
];

const PROMPT_STYLES = [
  { id: "executive_board", label: "Executive Board", description: "C-suite executive perspective" },
  { id: "sustainability_officer", label: "Sustainability Officer", description: "ESG metric framing" },
  { id: "auditor", label: "Auditor", description: "Compliance-first focus" },
  { id: "process_engineer", label: "Process Engineer", description: "Technical bottleneck focus" },
];

const RESPONSE_STYLES = [
  { id: "executive", label: "Executive", description: "Summary first approach" },
  { id: "technical", label: "Technical", description: "Detailed metric data" },
  { id: "raw_metrics", label: "Raw Metrics", description: "Clean numerical values" },
];

export default function SettingsPage() {
  const { token, activeOrg, activeWorkspace } = useAuth();
  const {
    selectedProjectId,
    selectedAnalysisId,
    insights,
    recommendations,
  } = useCopilot();

  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [hardware, setHardware] = useState<HardwareInfo | null>(null);
  const [providerHealth, setProviderHealth] = useState<ProviderHealth | null>(null);
  const [installedModels, setInstalledModels] = useState<OllamaModelMeta[]>([]);
  const [settings, setSettings] = useState<AiSettings>({
    provider: "ollama",
    model_name: "qwen3:8b",
    quality_mode: "balanced",
    prompt_style: "sustainability_officer",
    response_style: "executive",
    settings_version: 1,
  });
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [isLoadingHardware, setIsLoadingHardware] = useState(false);
  const [isRefreshingModels, setIsRefreshingModels] = useState(false);
  const [activeTab, setActiveTab] = useState<"ai" | "audit">("ai");

  // ── Fetch AI Settings ────────────────────────────────────────────────────
  const fetchAiSettings = useCallback(async () => {
    if (!activeWorkspace?.id || !token) return;
    try {
      const res = await fetch(
        `http://localhost:8000/api/settings/ai?workspace_id=${activeWorkspace.id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        const data = await res.json();
        setSettings(data);
      }
    } catch (err) {
      console.error("Error fetching AI settings", err);
    }
  }, [activeWorkspace, token]);

  // ── Fetch Hardware + Health ──────────────────────────────────────────────
  const fetchHardwareInfo = useCallback(async () => {
    if (!token) return;
    setIsLoadingHardware(true);
    try {
      const res = await fetch(`http://localhost:8000/api/settings/hardware`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setHardware(data.hardware);
        setProviderHealth(data.health);
      }
    } catch (err) {
      console.error("Error fetching hardware info", err);
    } finally {
      setIsLoadingHardware(false);
    }
  }, [token]);

  // ── Fetch Installed Models ─────────────────────────────────────────────
  const fetchInstalledModels = useCallback(async () => {
    if (!token) return;
    setIsRefreshingModels(true);
    try {
      const res = await fetch(`http://localhost:8000/api/settings/models`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setInstalledModels(data.installed_models ?? []);
      }
    } catch (err) {
      console.error("Error fetching installed models", err);
    } finally {
      setIsRefreshingModels(false);
    }
  }, [token]);

  // ── Fetch Audit Logs ───────────────────────────────────────────────────
  const fetchAuditLogs = useCallback(async (orgId: string) => {
    try {
      const res = await fetch(
        `http://localhost:8000/api/audit/?organization_id=${orgId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) setLogs(await res.json());
    } catch (err) {
      console.error("Error fetching audit logs", err);
    }
  }, [token]);

  useEffect(() => {
    if (token) {
      fetchHardwareInfo();
      fetchAiSettings();
    }
  }, [token, fetchHardwareInfo, fetchAiSettings]);

  // Fetch models AFTER hardware is loaded
  useEffect(() => {
    if (token) fetchInstalledModels();
  }, [token, hardware, fetchInstalledModels]);

  useEffect(() => {
    if (activeOrg && token) fetchAuditLogs(activeOrg.id);
    else setLogs([]);
  }, [activeOrg, token, fetchAuditLogs]);

  // ── Save Settings ─────────────────────────────────────────────────────
  const handleSaveSettings = async () => {
    if (!activeWorkspace?.id || !token) return;
    setIsSaving(true);
    setSaveSuccess(false);
    try {
      const res = await fetch(
        `http://localhost:8000/api/settings/ai?workspace_id=${activeWorkspace.id}`,
        {
          method: "PUT",
          headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
          body: JSON.stringify({
            provider: settings.provider,
            model_name: settings.model_name,
            quality_mode: settings.quality_mode,
            prompt_style: settings.prompt_style,
            response_style: settings.response_style,
          }),
        }
      );
      if (res.ok) {
        setSettings(await res.json());
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 3000);
      }
    } catch (err) {
      console.error("Error saving settings", err);
    } finally {
      setIsSaving(false);
    }
  };

  const isModelHeavy = (modelName: string) => {
    const model = installedModels.find((m) => m.name === modelName);
    return model?.heavy ?? false;
  };

  // ─── RENDER ─────────────────────────────────────────────────────────────

  return (
    <div className="w-full space-y-6 pb-16 text-foreground bg-background min-h-screen">
      {/* Page Header */}
      <div className="flex items-start justify-between border-b border-border-color pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-3">
            Settings & Configuration
          </h1>
          <p className="text-text-muted font-medium text-xs mt-1">
            AI model orchestration, provider health, and workspace governance
          </p>
        </div>
        {settings.settings_version > 0 && (
          <span className="text-xs text-text-muted bg-slate-100 border border-border-color px-3 py-1 rounded font-mono">
            Version {settings.settings_version}
          </span>
        )}
      </div>

      {/* Tab Bar */}
      <div className="flex gap-1 bg-card-bg p-1 rounded w-fit border border-border-color">
        <button
          id="tab-ai-settings"
          onClick={() => setActiveTab("ai")}
          className={`flex items-center gap-2 px-5 py-2 rounded text-xs font-bold transition-all ${
            activeTab === "ai" ? "bg-background text-foreground border border-border-color" : "text-text-muted hover:text-foreground"
          }`}
        >
          AI Settings
        </button>
        <button
          id="tab-audit-trail"
          onClick={() => setActiveTab("audit")}
          className={`flex items-center gap-2 px-5 py-2 rounded text-xs font-bold transition-all ${
            activeTab === "audit" ? "bg-background text-foreground border border-border-color" : "text-text-muted hover:text-foreground"
          }`}
        >
          Audit Trail
        </button>
      </div>

      {/* ─── AI SETTINGS TAB ─── */}
      {activeTab === "ai" && (
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">

          {/* LEFT: Main Config */}
          <div className="xl:col-span-2 space-y-6">

            {/* Provider Section */}
            <div className="bg-card-bg border border-border-color p-6 rounded shadow-sm">
              <div className="border-l-2 border-indigo-500 pl-3 mb-5">
                <h3 className="text-sm font-bold text-foreground uppercase tracking-wider">AI Provider</h3>
                <p className="text-xs text-text-muted mt-0.5 font-medium">Select your inference backend</p>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {PROVIDERS.map((p) => (
                  <button
                    key={p.id}
                    id={`provider-${p.id}`}
                    onClick={() => setSettings((s) => ({ ...s, provider: p.id }))}
                    className={`flex flex-col items-start gap-1 p-4 rounded border text-left transition-all ${
                      settings.provider === p.id
                        ? "border-indigo-500 bg-background"
                        : "border-border-color bg-card-bg hover:border-slate-500"
                    }`}
                  >
                    <span className="text-xs font-bold text-foreground uppercase tracking-wider">{p.label}</span>
                    <span className="text-[10px] text-text-muted font-medium leading-relaxed mt-1">{p.description}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Quality Mode Section */}
            <div className="bg-card-bg border border-border-color p-6 rounded shadow-sm">
              <div className="border-l-2 border-indigo-500 pl-3 mb-5">
                <h3 className="text-sm font-bold text-foreground uppercase tracking-wider">Quality Mode</h3>
                <p className="text-xs text-text-muted mt-0.5 font-medium">Adjust inference parameters (does NOT switch model automatically)</p>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {QUALITY_MODES.map((q) => (
                  <button
                    key={q.id}
                    id={`quality-${q.id}`}
                    onClick={() => setSettings((s) => ({ ...s, quality_mode: q.id }))}
                    className={`flex flex-col items-start gap-1 p-4 rounded border text-left transition-all ${
                      settings.quality_mode === q.id
                        ? "border-indigo-500 bg-background"
                        : "border-border-color bg-card-bg hover:border-slate-500"
                    }`}
                  >
                    <span className="text-xs font-bold text-foreground uppercase tracking-wider">{q.label}</span>
                    <span className="text-[10px] text-text-muted font-medium leading-relaxed mt-1">{q.description}</span>
                  </button>
                ))}
              </div>

              {/* Expert warning gate banner */}
              {settings.quality_mode === "expert" && hardware && isModelHeavy(settings.model_name) && (
                <div className="mt-4 p-3 bg-amber-50 border border-amber-200 text-amber-800 rounded text-xs flex gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold">Hardware Resource Warning:</span> Expert mode increases context requirements. 
                    Running model <span className="font-mono font-bold">{settings.model_name}</span> exceeds recommended RAM on this system.
                  </div>
                </div>
              )}
            </div>

            {/* Active Model Selection */}
            <div className="bg-card-bg border border-border-color p-6 rounded shadow-sm">
              <div className="border-l-2 border-indigo-500 pl-3 mb-5">
                <h3 className="text-sm font-bold text-foreground uppercase tracking-wider">Active Model</h3>
                <p className="text-xs text-text-muted mt-0.5 font-medium">Select installed model from local tags repository</p>
              </div>

              {hardware && (
                <div className="flex items-center gap-2 mb-4 bg-background border border-border-color rounded px-4 py-2 text-xs font-medium text-text-muted">
                  <Cpu className="w-3.5 h-3.5" />
                  <span>
                    Detected: <span className="text-foreground">{hardware.cpu}</span> · {hardware.ram_gb} GB RAM · Max Supported: <span className="font-mono text-indigo-400">{hardware.max_supported_model}</span>
                  </span>
                </div>
              )}

              {installedModels.length === 0 ? (
                <div className="text-xs text-text-muted text-center py-6 border border-dashed border-border-color rounded bg-background/20">
                  No Ollama models detected. Confirm service endpoint tags list.
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {installedModels.map((m) => (
                    <button
                      key={m.name}
                      id={`model-card-${m.name.replace(/[:.]/g, "-")}`}
                      onClick={() => setSettings((s) => ({ ...s, model_name: m.name }))}
                      className={`flex flex-col p-4 rounded border text-left transition-all ${
                        settings.model_name === m.name
                          ? "border-indigo-500 bg-background"
                          : "border-border-color bg-card-bg hover:border-slate-500"
                      }`}
                    >
                      <div className="flex justify-between w-full items-start">
                        <span className="font-mono text-xs font-bold text-foreground truncate max-w-[150px]">{m.name}</span>
                        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                          m.recommended ? "bg-emerald-50 text-emerald-700 border border-emerald-250" :
                          m.heavy ? "bg-amber-50 text-amber-700 border border-amber-200" :
                          "bg-slate-100 text-text-muted border border-border-color"
                        }`}>
                          {m.recommended ? "Recommended" : m.heavy ? "Heavy Model" : "Compatible"}
                        </span>
                      </div>
                      <div className="text-[10px] text-text-muted mt-2.5 grid grid-cols-2 gap-1 font-semibold uppercase tracking-wider">
                        <div>Size: {m.size_gb.toFixed(1)} GB</div>
                        <div className="text-right">Family: {m.family}</div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Prompt Persona */}
            <div className="bg-card-bg border border-border-color p-6 rounded shadow-sm">
              <div className="border-l-2 border-indigo-500 pl-3 mb-5">
                <h3 className="text-sm font-bold text-foreground uppercase tracking-wider">Prompt Persona</h3>
                <p className="text-xs text-text-muted mt-0.5 font-medium">AI framing style template selection</p>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {PROMPT_STYLES.map((ps) => (
                  <button
                    key={ps.id}
                    id={`prompt-style-${ps.id}`}
                    onClick={() => setSettings((s) => ({ ...s, prompt_style: ps.id }))}
                    className={`flex flex-col items-start gap-1 p-4 rounded border text-left transition-all ${
                      settings.prompt_style === ps.id
                        ? "border-indigo-500 bg-background"
                        : "border-border-color bg-card-bg hover:border-slate-500"
                    }`}
                  >
                    <span className="text-xs font-bold text-foreground uppercase tracking-wider">{ps.label}</span>
                    <span className="text-[10px] text-text-muted font-medium leading-relaxed mt-1">{ps.description}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Response format */}
            <div className="bg-card-bg border border-border-color p-6 rounded shadow-sm">
              <div className="border-l-2 border-indigo-500 pl-3 mb-5">
                <h3 className="text-sm font-bold text-foreground uppercase tracking-wider">Response Style</h3>
                <p className="text-xs text-text-muted mt-0.5 font-medium">Structure and presentation formats</p>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {RESPONSE_STYLES.map((rs) => (
                  <button
                    key={rs.id}
                    id={`response-style-${rs.id}`}
                    onClick={() => setSettings((s) => ({ ...s, response_style: rs.id }))}
                    className={`flex flex-col items-start gap-1 p-4 rounded border text-left transition-all ${
                      settings.response_style === rs.id
                        ? "border-indigo-500 bg-background"
                        : "border-border-color bg-card-bg hover:border-slate-500"
                    }`}
                  >
                    <span className="text-xs font-bold text-foreground uppercase tracking-wider">{rs.label}</span>
                    <span className="text-[10px] text-text-muted font-medium leading-relaxed mt-1">{rs.description}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Persistence actions */}
            <div className="flex items-center justify-between bg-card-bg border border-border-color rounded px-6 py-4">
              <div className="text-xs text-text-muted font-semibold">
                {saveSuccess
                  ? "Settings successfully updated in workspace settings database."
                  : activeWorkspace
                  ? `Active Workspace: ${activeWorkspace.name}`
                  : "No active workspace select context."}
              </div>
              <button
                id="save-ai-settings-btn"
                onClick={handleSaveSettings}
                disabled={isSaving || !activeWorkspace}
                className="bg-indigo-600 hover:bg-indigo-500 text-foreground font-bold text-xs py-2.5 px-5 rounded transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                {isSaving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                {isSaving ? "Saving…" : "Save Settings"}
              </button>
            </div>

            {/* Live Test Panel */}
            <LiveTestPanel
              settings={settings}
              activeWorkspace={activeWorkspace}
              selectedProjectId={selectedProjectId}
              selectedAnalysisId={selectedAnalysisId}
              insights={insights}
              recommendations={recommendations}
            />
          </div>

          {/* RIGHT: Status / Health Info */}
          <div className="space-y-6">

            {/* Detected Hardware */}
            <div className="bg-card-bg border border-border-color p-5 rounded shadow-sm space-y-4">
              <div className="flex items-center gap-2 border-b border-border-color pb-3">
                <Cpu className="w-4 h-4 text-indigo-400" />
                <span className="text-xs font-bold text-foreground uppercase tracking-wider">Detected Hardware</span>
              </div>
              {hardware ? (
                <div className="space-y-3.5 text-xs">
                  <div className="flex justify-between items-start">
                    <span className="text-text-muted">Processor</span>
                    <span className="text-foreground font-bold max-w-[180px] text-right">{hardware.cpu}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-muted">Memory RAM</span>
                    <span className="text-foreground font-bold">{hardware.ram_gb} GB</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-text-muted">Recommended Model</span>
                    <span className="text-emerald-400 font-mono font-bold">{hardware.recommended_model}</span>
                  </div>
                </div>
              ) : (
                <div className="text-xs text-text-muted text-center py-4">Checking hardware status...</div>
              )}
            </div>

            {/* Provider Health */}
            <div className="bg-card-bg border border-border-color p-5 rounded shadow-sm space-y-4">
              <div className="flex items-center gap-2 border-b border-border-color pb-3">
                <Wifi className="w-4 h-4 text-indigo-400" />
                <span className="text-xs font-bold text-foreground uppercase tracking-wider">Provider Health</span>
              </div>
              {providerHealth ? (
                <div className="space-y-3.5 text-xs">
                  {Object.entries(providerHealth).map(([provider, status]) => (
                    <div key={provider} className="flex items-center justify-between">
                      <span className="text-text-muted capitalize font-medium">{provider}</span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                        status === "connected"
                          ? "bg-emerald-50 text-emerald-700 border-emerald-250"
                          : "bg-red-50 text-red-700 border-red-200"
                      }`}>
                        Status: {status === "connected" ? "Connected" : status === "missing_key" ? "Missing Key" : "Offline"}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-xs text-text-muted text-center py-4">Polling health statuses...</div>
              )}
            </div>

            {/* Configuration Overview summary block */}
            <div className="bg-background border border-border-color rounded p-5 space-y-4">
              <div className="flex items-center gap-2 border-b border-border-color pb-3">
                <Layers className="w-4 h-4 text-indigo-400" />
                <span className="text-xs font-bold text-foreground uppercase tracking-wider">Configuration Summary</span>
              </div>
              <div className="space-y-3 text-xs">
                <div className="flex justify-between">
                  <span className="text-text-muted">Inference Engine</span>
                  <span className="text-foreground font-bold uppercase">{settings.provider}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-muted">Selected Model</span>
                  <span className="text-foreground font-mono font-bold">{settings.model_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-muted">Inference Parameters</span>
                  <span className="text-foreground font-bold uppercase">{settings.quality_mode}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-text-muted">Persona Style</span>
                  <span className="text-foreground font-bold capitalize">{settings.prompt_style.replace(/_/g, " ")}</span>
                </div>
              </div>
            </div>

          </div>
        </div>
      )}

      {/* ─── AUDIT TRAIL TAB ─── */}
      {activeTab === "audit" && (
        <div className="bg-card-bg border border-border-color rounded p-6 shadow-sm">
          <div className="border-l-2 border-indigo-500 pl-3 mb-5 flex justify-between items-center">
            <div>
              <h3 className="text-sm font-bold text-foreground uppercase tracking-wider">Tenant Audit Trail</h3>
              <p className="text-xs text-text-muted mt-0.5 font-medium">All organization and copilot activities logged for auditability</p>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-foreground">
              <thead className="text-[10px] uppercase bg-background text-text-muted font-bold border-b border-border-color">
                <tr>
                  <th className="px-4 py-3 border-b border-border-color">Timestamp</th>
                  <th className="px-4 py-3 border-b border-border-color">Action</th>
                  <th className="px-4 py-3 border-b border-border-color">Audit Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-color font-medium bg-card-bg">
                {Array.isArray(logs) && logs.map((log) => (
                  <tr key={log?.id || Math.random().toString()} className="hover:bg-background/30 transition-colors">
                    <td className="px-4 py-3 text-text-muted font-mono text-[10px]">
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5" />
                        {log?.created_at ? new Date(log.created_at).toLocaleString() : "—"}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="font-bold text-foreground uppercase">{(log?.action || "").replace(/_/g, " ")}</span>
                    </td>
                    <td className="px-4 py-3 text-text-muted">{log?.details || "—"}</td>
                  </tr>
                ))}
                {(!Array.isArray(logs) || logs.length === 0) && (
                  <tr>
                    <td colSpan={3} className="px-4 py-10 text-center text-text-muted font-semibold">
                      No audit trails logged for this organization context.
                    </td>
                  </tr>
                )}
              </tbody>

            </table>
          </div>
        </div>
      )}
    </div>
  );
}
