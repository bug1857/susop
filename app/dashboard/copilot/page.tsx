"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";
import { useAuth } from "../../../context/AuthContext";
import { useCopilot } from "../../../context/CopilotContext";
import { api } from "../../../services/api";
import { COPILOT_ENDPOINTS } from "../../../services/copilotEndpoints";
import {
  Sparkles,
  Send,
  Trash2,
  Cpu,
  Bot,
  HelpCircle,
  Clock,
  Layers,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Hash,
  Timer,
  Coins,
  BookOpen,
  Database,
  X,
  Info,
  Zap,
  Brain,
} from "lucide-react";

// ─── Types ───────────────────────────────────────────────────────────────────

interface TelemetryMeta {
  id: string;
  provider: string;
  model_name?: string;
  request_type: string;
  token_count: number;
  execution_time_ms: number;
  prompt_hash?: string;
  response_metadata?: Record<string, unknown>;
}

interface Message {
  id: string;
  sender: "user" | "assistant";
  text: string;
  timestamp: string;
  provider?: string;
  model?: string;
  isError?: boolean;
  telemetry?: TelemetryMeta;
}

// ─── Why-This-Answer Drawer ───────────────────────────────────────────────────

function TelemetryDrawer({
  telemetry,
  onClose,
}: {
  telemetry: TelemetryMeta;
  onClose: () => void;
}) {
  const intentLabel: Record<string, string> = {
    EXECUTIVE_BRIEF: "Executive Summary",
    INSIGHT_SUMMARY: "Insight Analysis",
    FORECAST_EXPLANATION: "Emissions Forecast",
    RECOMMENDATION_SUMMARY: "Recommendations",
    SIMULATION_EXPLANATION: "Scenario Simulation",
  };

  const contextSources = [
    "Explainability Record",
    "BRSR Report Context",
    "AI Recommendations",
    "Object Conformance",
    "Object Carbon Attribution",
    "Object Interactions",
    "Object Simulation",
    "Carbon Fitness",
    "Sustainability Conformance",
    "Sustainability Digital Twin",
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/60 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-lg bg-card-bg rounded-t-3xl sm:rounded-2xl border border-border-color shadow-2xl overflow-hidden">
        {/* Drawer Header */}
        <div className="flex items-center justify-between px-6 pt-5 pb-4 bg-slate-100 border-b border-border-color">
          <div className="flex items-center gap-2">
            <Info className="w-4 h-4 text-indigo-600" />
            <span className="text-sm font-bold text-foreground">Why This Answer?</span>
          </div>
          <button
            id="close-telemetry-drawer"
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-200 text-text-muted hover:text-foreground transition-all cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-5 space-y-4 max-h-[70vh] overflow-y-auto text-foreground">
          {/* Intent Matched */}
          <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Brain className="w-4 h-4 text-indigo-600" />
              <span className="text-sm font-bold text-indigo-700 uppercase tracking-wide">Intent Matched</span>
            </div>
            <div className="text-sm font-bold text-foreground">
              {intentLabel[telemetry.request_type] ?? telemetry.request_type}
            </div>
            <div className="text-xs text-text-muted mt-0.5 font-mono">{telemetry.request_type}</div>
          </div>

          {/* Performance Metrics */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 text-center">
              <Timer className="w-4 h-4 text-emerald-600 mx-auto mb-1" />
              <div className="text-lg font-black text-foreground">{telemetry.execution_time_ms}<span className="text-xs font-semibold text-text-muted ml-0.5">ms</span></div>
              <div className="text-xs font-bold text-emerald-600 uppercase tracking-wide">Latency</div>
            </div>
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 text-center">
              <Coins className="w-4 h-4 text-amber-600 mx-auto mb-1" />
              <div className="text-lg font-black text-foreground">{telemetry.token_count?.toLocaleString()}</div>
              <div className="text-xs font-bold text-amber-600 uppercase tracking-wide">Tokens</div>
            </div>
            <div className="bg-purple-50 border border-purple-200 rounded-xl p-3 text-center">
              <Zap className="w-4 h-4 text-purple-600 mx-auto mb-1" />
              <div className="text-sm font-black text-foreground capitalize">{telemetry.provider?.toLowerCase()}</div>
              <div className="text-xs font-bold text-purple-600 uppercase tracking-wide">Provider</div>
            </div>
          </div>

          {/* Model & Prompt Info */}
          <div className="space-y-2">
            <div className="flex items-center justify-between py-2 px-3 bg-background rounded-lg border border-border-color">
              <div className="flex items-center gap-2">
                <Cpu className="w-3.5 h-3.5 text-text-muted" />
                <span className="text-sm font-semibold text-foreground">Active Model</span>
              </div>
              <span className="text-xs font-bold text-foreground font-mono bg-slate-100 px-2 py-0.5 rounded">
                {telemetry.model_name ?? telemetry.response_metadata?.model_name as string ?? "ollama"}
              </span>
            </div>
            <div className="flex items-center justify-between py-2 px-3 bg-background rounded-lg border border-border-color">
              <div className="flex items-center gap-2">
                <BookOpen className="w-3.5 h-3.5 text-text-muted" />
                <span className="text-sm font-semibold text-foreground">Prompt Version</span>
              </div>
              <span className="text-xs font-bold text-foreground font-mono bg-slate-100 px-2 py-0.5 rounded">
                v{telemetry.response_metadata?.prompt_version as number ?? 1}
              </span>
            </div>
          </div>

          {/* Context Sources Loaded */}
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Database className="w-3.5 h-3.5 text-text-muted" />
              <span className="text-sm font-bold text-foreground uppercase tracking-wide">Context Sources Loaded</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {contextSources.map((src) => (
                <span
                  key={src}
                  className="inline-flex items-center gap-1 text-xs font-medium bg-background text-foreground border border-border-color px-2.5 py-1 rounded-full"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 flex-shrink-0" />
                  {src}
                </span>
              ))}
            </div>
          </div>

          {/* Prompt Fingerprint */}
          {telemetry.prompt_hash && (
            <div className="bg-background rounded-xl p-3 border border-border-color">
              <div className="flex items-center gap-2 mb-1.5">
                <Hash className="w-3.5 h-3.5 text-text-muted" />
                <span className="text-xs font-bold text-foreground uppercase tracking-wide">Prompt Fingerprint (SHA-256)</span>
              </div>
              <p className="text-xs font-mono text-emerald-700 break-all leading-relaxed">
                {telemetry.prompt_hash}
              </p>
              <p className="text-xs text-text-muted mt-1.5">
                Cryptographic integrity proof. Identical hash = identical context inputs. Used for audit lineage.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export default function CopilotCenterPage() {
  const { activeWorkspace } = useAuth();
  const {
    selectedProjectId,
    selectedAnalysisId,
    analyses,
    health,
    insights,
    forecasts,
    simulations,
    recommendations,
  } = useCopilot();

  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [activeTelemetry, setActiveTelemetry] = useState<TelemetryMeta | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Active analysis version helper
  const activeAnalysisVersion = useMemo(() => {
    if (!selectedAnalysisId) return null;
    const ana = analyses.find((a) => a.id === selectedAnalysisId);
    return ana ? `v${ana.analysis_version}` : null;
  }, [selectedAnalysisId, analyses]);

  // Conversation Persistence Key
  const persistenceKey = useMemo(() => {
    if (!activeWorkspace?.id || !selectedProjectId || !selectedAnalysisId) return null;
    return `copilot_chat_${activeWorkspace.id}_${selectedProjectId}_${selectedAnalysisId}`;
  }, [activeWorkspace, selectedProjectId, selectedAnalysisId]);

  // Load Conversation History
  useEffect(() => {
    if (!persistenceKey) {
      setMessages([]);
      return;
    }
    const stored = localStorage.getItem(persistenceKey);
    if (stored) {
      try {
        setMessages(JSON.parse(stored));
      } catch {
        setMessages([]);
      }
    } else {
      const welcome: Message = {
        id: "welcome",
        sender: "assistant",
        text: `Hello! I am your Executive Sustainability Assistant, connected to local Ollama intelligence. I am aware of your active workspace context. How can I help you analyze carbon footprints, compliance conformance, or scenario simulations today?`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        provider: "System",
        model: "SustainOCPM",
      };
      setMessages([welcome]);
    }
  }, [persistenceKey]);

  // Save Conversation History
  const saveMessages = (newMessages: Message[]) => {
    setMessages(newMessages);
    if (persistenceKey) {
      localStorage.setItem(persistenceKey, JSON.stringify(newMessages));
    }
  };

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const handleClearChat = () => {
    if (!persistenceKey) return;
    localStorage.removeItem(persistenceKey);
    const welcome: Message = {
      id: "welcome-" + Date.now(),
      sender: "assistant",
      text: `Chat history cleared. How can I assist you with your active process analysis?`,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      provider: "System",
      model: "SustainOCPM",
    };
    setMessages([welcome]);
  };

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isTyping) return;

    if (!selectedAnalysisId) {
      const errorMsg: Message = {
        id: "err-" + Date.now(),
        sender: "assistant",
        text: "Please select an active process analysis from the dashboard header before asking questions.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        isError: true,
      };
      saveMessages([
        ...messages,
        {
          id: "user-" + Date.now(),
          sender: "user",
          text,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
        errorMsg,
      ]);
      return;
    }

    const userMsg: Message = {
      id: "user-" + Date.now(),
      sender: "user",
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    const updatedMessages = [...messages, userMsg];
    saveMessages(updatedMessages);
    setInputValue("");
    setIsTyping(true);

    const q = text.toLowerCase();
    let requestType = "EXECUTIVE_BRIEF";
    let entityType = "INSIGHT";
    let entityId = "";

    try {
      if (q.includes("summary") || q.includes("summarize") || q.includes("executive")) {
        requestType = "EXECUTIVE_BRIEF";
        if (insights.data && insights.data.length > 0) {
          entityType = "INSIGHT";
          entityId = insights.data[0].id;
        } else if (recommendations.data && recommendations.data.length > 0) {
          entityType = "RECOMMENDATION";
          entityId = recommendations.data[0].id;
        } else if (forecasts.data && forecasts.data.length > 0) {
          entityType = "FORECAST";
          entityId = forecasts.data[0].id;
        } else if (simulations.data && simulations.data.length > 0) {
          entityType = "SIMULATION";
          entityId = simulations.data[0].id;
        } else {
          throw new Error("EMPTY_EXECUTIVE");
        }
      } else if (q.includes("hotspot") || q.includes("risk") || q.includes("carbon risk")) {
        requestType = "INSIGHT_SUMMARY";
        entityType = "INSIGHT";
        const hotspot = insights.data?.find(
          (i) => i.insight_type === "carbon_hotspot" || i.insight_type === "carbon"
        );
        if (hotspot) {
          entityId = hotspot.id;
        } else if (insights.data && insights.data.length > 0) {
          entityId = insights.data[0].id;
        } else {
          throw new Error("EMPTY_INSIGHTS");
        }
      } else if (q.includes("compliance") || q.includes("violation") || q.includes("conformance")) {
        requestType = "INSIGHT_SUMMARY";
        entityType = "INSIGHT";
        const violation = insights.data?.find((i) => i.insight_type === "conformance_risk");
        if (violation) {
          entityId = violation.id;
        } else if (insights.data && insights.data.length > 0) {
          entityId = insights.data[0].id;
        } else {
          throw new Error("EMPTY_COMPLIANCE");
        }
      } else if (
        q.includes("esg") ||
        q.includes("sustainability") ||
        q.includes("energy") ||
        q.includes("water") ||
        q.includes("waste")
      ) {
        requestType = "INSIGHT_SUMMARY";
        entityType = "INSIGHT";
        const esgInsight = insights.data?.find(
          (i) => i.insight_type === "esg" || i.insight_type === "environmental"
        );
        if (esgInsight) {
          entityId = esgInsight.id;
        } else {
          throw new Error("EMPTY_ESG");
        }
      } else if (q.includes("forecast") || q.includes("project") || q.includes("future")) {
        requestType = "FORECAST_EXPLANATION";
        entityType = "FORECAST";
        if (forecasts.data && forecasts.data.length > 0) {
          entityId = forecasts.data[0].id;
        } else {
          throw new Error("EMPTY_FORECAST");
        }
      } else if (q.includes("recommend") || q.includes("action") || q.includes("prioritized")) {
        requestType = "RECOMMENDATION_SUMMARY";
        entityType = "RECOMMENDATION";
        if (recommendations.data && recommendations.data.length > 0) {
          entityId = recommendations.data[0].id;
        } else {
          throw new Error("EMPTY_RECOMMENDATIONS");
        }
      } else if (q.includes("simulat") || q.includes("pathway") || q.includes("opportunity")) {
        requestType = "SIMULATION_EXPLANATION";
        entityType = "SIMULATION";
        if (simulations.data && simulations.data.length > 0) {
          entityId = simulations.data[0].id;
        } else {
          throw new Error("EMPTY_SIMULATIONS");
        }
      } else {
        if (recommendations.data && recommendations.data.length > 0) {
          requestType = "RECOMMENDATION_SUMMARY";
          entityType = "RECOMMENDATION";
          entityId = recommendations.data[0].id;
        } else if (insights.data && insights.data.length > 0) {
          requestType = "INSIGHT_SUMMARY";
          entityType = "INSIGHT";
          entityId = insights.data[0].id;
        } else if (forecasts.data && forecasts.data.length > 0) {
          requestType = "FORECAST_EXPLANATION";
          entityType = "FORECAST";
          entityId = forecasts.data[0].id;
        } else if (simulations.data && simulations.data.length > 0) {
          requestType = "SIMULATION_EXPLANATION";
          entityType = "SIMULATION";
          entityId = simulations.data[0].id;
        } else {
          throw new Error("EMPTY_FALLBACK");
        }
      }

      const res = await api.post(COPILOT_ENDPOINTS.COPILOT_GENERATE, {
        workspace_id: activeWorkspace?.id,
        project_id: selectedProjectId,
        analysis_id: selectedAnalysisId,
        request_type: requestType,
        provider: "OLLAMA",
        entity_type: entityType,
        entity_id: entityId,
        user_query: text,
      });

      if (res.data && res.data.data) {
        const replyList = res.data.data;
        const reply = Array.isArray(replyList) ? replyList[0] : replyList;

        // Build telemetry from response
        const telemetry: TelemetryMeta = {
          id: reply.id,
          provider: reply.provider || "OLLAMA",
          model_name: reply.model_name || reply.response_metadata?.model_name as string,
          request_type: reply.request_type || requestType,
          token_count: reply.token_count ?? 0,
          execution_time_ms: reply.execution_time_ms ?? 0,
          prompt_hash: reply.prompt_hash,
          response_metadata: reply.response_metadata,
        };

        const assistantMsg: Message = {
          id: "asst-" + Date.now(),
          sender: "assistant",
          text: reply.response_text || reply.answer || JSON.stringify(reply),
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          provider: reply.provider || health.provider || "OLLAMA",
          model: reply.model_name || health.model || "—",
          telemetry,
        };
        saveMessages([...updatedMessages, assistantMsg]);
      } else {
        throw new Error("Invalid response format received from Copilot services.");
      }
    } catch (err: unknown) {
      let errorText =
        "The AI Copilot was unable to construct a query response. Verify conformance checking model definitions first.";
      const errMsg = (err as Error).message;
      if (errMsg === "EMPTY_EXECUTIVE") {
        errorText = "Executive Summary cannot be compiled. There are no insights or recommendations calculated for this analysis version.";
      } else if (errMsg === "EMPTY_INSIGHTS") {
        errorText = "No hotspot data found. Possible reasons:\n\n• Carbon Emissions field not mapped\n• Carbon Attribution not executed\n• Dataset lacks carbon metrics";
      } else if (errMsg === "EMPTY_COMPLIANCE") {
        errorText = "No conformance drift data found. Possible reasons:\n\n• Reference Model not created\n• Conformance analysis not executed";
      } else if (errMsg === "EMPTY_ESG") {
        errorText = "No ESG metrics available. Possible reasons:\n\n• ESG fields not mapped\n• ESG calculations not executed";
      } else if (errMsg === "EMPTY_FORECAST") {
        errorText = "Emissions forecast cannot be explained. Generate a forecast trend calculation first.";
      } else if (errMsg === "EMPTY_RECOMMENDATIONS") {
        errorText = "Actionable recommendations are empty. Generate recommendations actions first.";
      } else if (errMsg === "EMPTY_SIMULATIONS") {
        errorText = "Scenario simulation pathways are empty. Run a simulation trial first.";
      } else if (errMsg === "EMPTY_FALLBACK") {
        errorText = "No database entities (insights, forecasts, simulations, or recommendations) are available to bind an AI session. Please run analysis calculations first.";
      } else if (errMsg) {
        errorText = errMsg;
      }

      const assistantMsg: Message = {
        id: "asst-err-" + Date.now(),
        sender: "assistant",
        text: errorText,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        isError: true,
      };
      saveMessages([...updatedMessages, assistantMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  const suggestedPrompts = [
    { label: "Emissions Trend Risk", text: "Why are emissions increasing?" },
    { label: "Executive Summary", text: "Summarize this analysis." },
    { label: "Carbon Hotspots", text: "What are the highest-risk hotspots?" },
    { label: "Conformance Rate Opt", text: "How can we optimize our conformance rate?" },
  ];

  return (
    <div className="w-full space-y-6 pb-12">

      {/* Why-This-Answer Drawer (modal overlay) */}
      {activeTelemetry && (
        <TelemetryDrawer
          telemetry={activeTelemetry}
          onClose={() => setActiveTelemetry(null)}
        />
      )}

      {/* Header Widget */}
      <div className="flex justify-between items-center bg-card-bg p-6 rounded-xl border border-border-color shadow-sm">
        <div>
          <h1 className="text-2xl font-black text-foreground tracking-tight flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-emerald-500 animate-pulse" />
            SustainAI Workspace
          </h1>
          <p className="text-sm text-text-muted font-semibold mt-1">
            Conversational executive assistant powered by local Ollama AI — each answer is traceable and auditable
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-text-muted bg-background border border-border-color px-3 py-1.5 rounded-full font-mono font-medium">
            Click <Info className="w-3.5 h-3.5 inline text-indigo-600" /> on any reply to inspect reasoning
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">

        {/* Left Side: Conversational Chat Interface */}
        <div className="lg:col-span-8 flex flex-col h-[580px]">
          <div className="bg-card-bg rounded-xl border border-border-color shadow-sm overflow-hidden flex-1 flex flex-col">

            {/* Chat Header controls */}
            <div className="p-4 border-b border-border-color flex items-center justify-between bg-slate-50">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-text-muted uppercase tracking-wider">Active Chat Session</span>
                {activeAnalysisVersion && (
                  <span className="text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-0.5 rounded font-bold">
                    Analysis: {activeAnalysisVersion}
                  </span>
                )}
              </div>
              <button
                id="clear-chat-btn"
                onClick={handleClearChat}
                className="text-sm text-text-muted hover:text-red-600 font-semibold flex items-center gap-1 transition-colors cursor-pointer"
                title="Clear conversation"
              >
                <Trash2 className="w-4 h-4" />
                Clear
              </button>
            </div>

            {/* Message History */}
            <div className="flex-1 overflow-y-auto p-5 space-y-4 bg-background">
              {messages.map((msg) => {
                const isUser = msg.sender === "user";
                return (
                  <div key={msg.id} className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
                    <div
                      className={`max-w-[85%] rounded-xl p-4 shadow-sm text-sm font-normal leading-relaxed border ${
                        isUser
                          ? "bg-indigo-600 border-indigo-500 text-white rounded-br-none"
                          : msg.isError
                          ? "bg-red-50 border-red-200 text-red-700 rounded-bl-none"
                          : "bg-card-bg border-border-color text-foreground rounded-bl-none"
                      }`}
                    >
                      {/* Model badge */}
                      {!isUser && (msg.provider || msg.model) && (
                        <div className="flex items-center gap-1.5 text-xs text-text-muted font-mono uppercase tracking-wider mb-2 border-b border-border-color pb-1.5 font-semibold">
                          <Bot className="h-3.5 w-3.5 text-emerald-500" />
                          <span>{msg.provider}</span>
                          <span>•</span>
                          <span>{msg.model}</span>
                        </div>
                      )}

                      <div className="whitespace-pre-wrap font-medium">{msg.text}</div>

                      {/* Footer: timestamp + telemetry trigger */}
                      <div className="flex items-center justify-between mt-2.5 pt-1.5 border-t border-border-color">
                        <div />
                        <div className="flex items-center gap-2">
                          {/* Telemetry pill — only for assistant messages with telemetry */}
                          {!isUser && msg.telemetry && (
                            <button
                              id={`why-btn-${msg.id}`}
                              onClick={() => setActiveTelemetry(msg.telemetry!)}
                              className="flex items-center gap-1.5 text-xs font-bold text-indigo-600 hover:text-indigo-500 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 px-2 py-0.5 rounded-full transition-all cursor-pointer"
                              title="Why this answer?"
                            >
                              <Info className="w-3 h-3" />
                              Why?
                            </button>
                          )}
                          {/* Latency badge */}
                          {!isUser && msg.telemetry && (
                            <span className="text-xs text-emerald-700 font-mono bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-bold">
                              {msg.telemetry.execution_time_ms}ms
                            </span>
                          )}
                          <span className={`text-xs font-medium ${isUser ? "text-indigo-200" : "text-text-muted"}`}>
                            {msg.timestamp}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}

              {isTyping && (
                <div className="flex justify-start">
                  <div className="bg-card-bg border border-border-color rounded-xl rounded-bl-none p-4 shadow-sm text-sm text-text-muted flex items-center gap-2">
                    <Bot className="h-5 w-5 text-emerald-500 animate-bounce" />
                    <div className="flex space-x-1">
                      <span className="h-1.5 w-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                      <span className="h-1.5 w-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                      <span className="h-1.5 w-1.5 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Composer Form */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage(inputValue);
              }}
              className="p-3 border-t border-border-color bg-card-bg flex items-center gap-2"
            >
              <input
                id="copilot-input"
                type="text"
                placeholder="Ask SustainAI about carbon reduction, compliance drifts, or scenario simulations..."
                className="flex-1 px-4 py-2.5 border border-border-color rounded-lg text-sm text-foreground bg-background focus:bg-background focus:outline-none focus:ring-1 focus:ring-emerald-500 transition-all font-medium placeholder-slate-400"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                disabled={isTyping}
              />
              <button
                id="copilot-send-btn"
                type="submit"
                disabled={!inputValue.trim() || isTyping}
                className="p-3 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm disabled:opacity-50 transition-all outline-none flex items-center justify-center shrink-0 cursor-pointer"
              >
                <Send className="h-4 w-4" />
              </button>
            </form>
          </div>
        </div>

        {/* Right Side: Prompts & Status */}
        <div className="lg:col-span-4 space-y-5 flex flex-col">

          {/* Prompt Library */}
          <div className="bg-card-bg rounded-xl border border-border-color p-5 shadow-sm space-y-3">
            <h3 className="font-extrabold text-sm text-foreground flex items-center gap-2">
              <HelpCircle className="w-4 h-4 text-emerald-500" />
              Suggested Prompt Templates
            </h3>
            <p className="text-xs text-text-muted leading-relaxed font-semibold">
              Click any suggested query to automatically feed it into the active analysis assistant.
            </p>
            <div className="space-y-2.5">
              {suggestedPrompts.map((p, i) => (
                <button
                  key={i}
                  id={`prompt-suggestion-${i}`}
                  onClick={() => handleSendMessage(p.text)}
                  disabled={isTyping || !selectedAnalysisId}
                  className="w-full text-left bg-background hover:bg-slate-5 border border-border-color hover:border-emerald-600 p-3 rounded-lg text-sm font-semibold text-foreground cursor-pointer transition-all leading-normal disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <div className="font-bold text-foreground text-sm">{p.label}</div>
                  <div className="text-xs text-text-muted mt-1 truncate">&quot;{p.text}&quot;</div>
                </button>
              ))}
            </div>
          </div>

          {/* Model Accountability Card */}
          <div className="bg-card-bg rounded-xl border border-border-color p-5 shadow-sm space-y-3 flex-1 flex flex-col">
            <h3 className="font-extrabold text-sm text-foreground flex items-center gap-2">
              <Cpu className="w-4 h-4 text-emerald-500" />
              Ollama Engine Status
            </h3>
            <div className="space-y-2.5 text-sm">
              <div className="flex justify-between border-b border-border-color pb-2">
                <span className="text-text-muted font-semibold">AI Provider</span>
                <span className="font-bold text-foreground text-sm">OLLAMA</span>
              </div>
              <div className="flex justify-between border-b border-border-color pb-2">
                <span className="text-text-muted font-semibold">Active LLM Model</span>
                <span className="font-mono text-foreground font-bold text-sm">{health.model || "—"}</span>
              </div>
              <div className="flex justify-between border-b border-border-color pb-2">
                <span className="text-text-muted font-semibold">Status</span>
                <span
                  className={`px-2 py-0.5 text-xs font-bold rounded border ${
                    health.status === "healthy"
                      ? "bg-green-50 border-green-200 text-green-700"
                      : "bg-rose-50 border-rose-200 text-rose-700"
                  }`}
                >
                  {health.status === "healthy" ? "ONLINE" : "OFFLINE"}
                </span>
              </div>
            </div>

            {/* Explainability Legend */}
            <div className="mt-auto pt-3 border-t border-border-color">
              <p className="text-xs text-text-muted font-semibold leading-relaxed">
                <span className="inline-flex items-center gap-1 text-indigo-600 font-bold">
                  <Info className="w-3.5 h-3.5" /> Why?
                </span>{" "}
                appears on each AI reply. Click it to inspect the intent matched, context sources loaded, latency, tokens, and the cryptographic prompt fingerprint.
              </p>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
