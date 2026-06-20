"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";
import { useAuth } from "../../context/AuthContext";
import { useCopilot, HealthState } from "../../context/CopilotContext";
import { api } from "../../services/api";
import { COPILOT_ENDPOINTS } from "../../services/copilotEndpoints";
import {
  Sparkles,
  Send,
  X,
  RefreshCw,
  Trash2,
  Cpu,
  User,
  Info,
  Calendar,
  Layers,
  Compass,
  AlertTriangle,
  Clock,
  Coins,
  Bot
} from "lucide-react";

interface Message {
  id: string;
  sender: "user" | "assistant";
  text: string;
  timestamp: string;
  provider?: string;
  model?: string;
  isError?: boolean;
}

interface ExecutiveCopilotProps {
  onClose: () => void;
}

export const ExecutiveCopilot: React.FC<ExecutiveCopilotProps> = ({ onClose }) => {
  const { activeOrg, activeWorkspace } = useAuth();
  const {
    selectedProjectId,
    selectedAnalysisId,
    analyses,
    health,
    insights,
    forecasts,
    simulations,
    recommendations
  } = useCopilot();

  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Active project name helper
  const activeProjectName = useMemo(() => {
    const proj = activeWorkspace?.id ? localStorage.getItem(`proj_${selectedProjectId}`) : null;
    return proj || "Active Project";
  }, [selectedProjectId, activeWorkspace]);

  // Active analysis version helper
  const activeAnalysisVersion = useMemo(() => {
    if (!selectedAnalysisId) return null;
    const ana = analyses.find((a) => a.id === selectedAnalysisId);
    return ana ? `v${ana.analysis_version}` : null;
  }, [selectedAnalysisId, analyses]);

  // 1. Conversation Persistence Key
  const persistenceKey = useMemo(() => {
    if (!activeWorkspace?.id || !selectedProjectId || !selectedAnalysisId) return null;
    return `copilot_chat_${activeWorkspace.id}_${selectedProjectId}_${selectedAnalysisId}`;
  }, [activeWorkspace, selectedProjectId, selectedAnalysisId]);

  // 2. Load Conversation History
  useEffect(() => {
    if (!persistenceKey) {
      setMessages([]);
      return;
    }
    const stored = localStorage.getItem(persistenceKey);
    if (stored) {
      try {
        setMessages(JSON.parse(stored));
      } catch (err) {
        setMessages([]);
      }
    } else {
      // Default welcome message
      const welcome: Message = {
        id: "welcome",
        sender: "assistant",
        text: `Hello! I am your Executive Sustainability Assistant, connected to local Ollama intelligence. I am aware of your active workspace context. How can I help you analyze carbon footprints, compliance conformance, or scenario simulations today?`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        provider: "System",
        model: "SustainOCPM"
      };
      setMessages([welcome]);
    }
  }, [persistenceKey]);

  // 3. Save Conversation History
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

  // Session Controls
  const handleClearChat = () => {
    if (!persistenceKey) return;
    localStorage.removeItem(persistenceKey);
    const welcome: Message = {
      id: "welcome-" + Date.now(),
      sender: "assistant",
      text: `Chat history cleared. How can I assist you with your active process analysis?`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      provider: "System",
      model: "SustainOCPM"
    };
    setMessages([welcome]);
  };

  // 4. AI Generation Logic mapping to backend route contracts
  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isTyping) return;

    // Verify context
    if (!selectedAnalysisId) {
      const errorMsg: Message = {
        id: "err-" + Date.now(),
        sender: "assistant",
        text: "Please select an active process analysis from the dashboard header before asking questions.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isError: true
      };
      saveMessages([...messages, {
        id: "user-" + Date.now(),
        sender: "user",
        text,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }, errorMsg]);
      return;
    }

    const userMsg: Message = {
      id: "user-" + Date.now(),
      sender: "user",
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    const updatedMessages = [...messages, userMsg];
    saveMessages(updatedMessages);
    setInputValue("");
    setIsTyping(true);

    const q = text.toLowerCase();
    let requestType = "EXECUTIVE_BRIEF";
    let entityType = "INSIGHT";
    let entityId = "";

    // Context analysis scans available frontend states to find matching entities
    try {
      if (q.includes("summary") || q.includes("summarize") || q.includes("executive")) {
        requestType = "EXECUTIVE_BRIEF";
        // Target first insight, or first recommendation, or first forecast
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
          // Empty state handling
          throw new Error("EMPTY_EXECUTIVE");
        }
      } 
      else if (q.includes("hotspot") || q.includes("risk") || q.includes("carbon risk")) {
        requestType = "INSIGHT_SUMMARY";
        entityType = "INSIGHT";
        const hotspot = insights.data?.find((i) => i.insight_type === "carbon_hotspot" || i.insight_type === "carbon");
        if (hotspot) {
          entityId = hotspot.id;
        } else if (insights.data && insights.data.length > 0) {
          entityId = insights.data[0].id;
        } else {
          throw new Error("EMPTY_INSIGHTS");
        }
      } 
      else if (q.includes("compliance") || q.includes("violation") || q.includes("conformance")) {
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
      } 
      else if (q.includes("forecast") || q.includes("project") || q.includes("future")) {
        requestType = "FORECAST_EXPLANATION";
        entityType = "FORECAST";
        if (forecasts.data && forecasts.data.length > 0) {
          entityId = forecasts.data[0].id;
        } else {
          throw new Error("EMPTY_FORECAST");
        }
      } 
      else if (q.includes("recommend") || q.includes("action") || q.includes("prioritized")) {
        requestType = "RECOMMENDATION_SUMMARY";
        entityType = "RECOMMENDATION";
        if (recommendations.data && recommendations.data.length > 0) {
          entityId = recommendations.data[0].id;
        } else {
          throw new Error("EMPTY_RECOMMENDATIONS");
        }
      } 
      else if (q.includes("simulat") || q.includes("pathway") || q.includes("opportunity")) {
        requestType = "SIMULATION_EXPLANATION";
        entityType = "SIMULATION";
        if (simulations.data && simulations.data.length > 0) {
          entityId = simulations.data[0].id;
        } else {
          throw new Error("EMPTY_SIMULATIONS");
        }
      } 
      else {
        // Fallback matching to any available entity to trigger the Ollama backend
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
        } else {
          throw new Error("EMPTY_FALLBACK");
        }
      }

      // 5. Exclusively invoke the verified backend generate route contract
      const res = await api.post(COPILOT_ENDPOINTS.COPILOT_GENERATE, {
        workspace_id: activeWorkspace?.id,
        project_id: selectedProjectId,
        analysis_id: selectedAnalysisId,
        request_type: requestType,
        provider: "OLLAMA",
        entity_type: entityType,
        entity_id: entityId,
        user_query: text
      });

      const data = res.data.data?.[0] || res.data.data || res.data;

      // Typing reveal simulator for smooth assistant responses
      await new Promise((resolve) => setTimeout(resolve, 600));

      const assistantMsg: Message = {
        id: "assistant-" + Date.now(),
        sender: "assistant",
        text: data.response_text || "The local intelligence engine generated an empty response.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        provider: "OLLAMA",
        model: health.model || "—"
      };
      saveMessages([...updatedMessages, assistantMsg]);

    } catch (err: any) {
      let friendlyText = "An unexpected error occurred while communicating with the local Ollama service.";

      // Empty state handling alignment as requested
      if (err.message === "EMPTY_EXECUTIVE") {
        friendlyText = "No AI insights, recommendations, forecasts, or simulations are currently available for this analysis. Please process a process mining log to generate analysis data before requesting an executive brief.";
      } else if (err.message === "EMPTY_INSIGHTS") {
        friendlyText = "No AI carbon hotspot insights are currently available for this analysis.";
      } else if (err.message === "EMPTY_COMPLIANCE") {
        friendlyText = "No compliance violations or conformance risk insights are currently available for this analysis.";
      } else if (err.message === "EMPTY_FORECAST") {
        friendlyText = "No carbon forecast is currently available for this analysis. You can generate a forecast using the action button in the Carbon Forecast panel.";
      } else if (err.message === "EMPTY_RECOMMENDATIONS") {
        friendlyText = "No recommendations are currently available for this analysis. Please generate recommendations using the Recommendation Center.";
      } else if (err.message === "EMPTY_SIMULATIONS") {
        friendlyText = "No simulations are currently available for this analysis. You can run simulations using the Scenario Simulation Panel.";
      } else if (err.message === "EMPTY_FALLBACK") {
        friendlyText = "No database entities (insights, forecasts, simulations, or recommendations) are available to bind an AI session. Please run analysis calculations first.";
      } else {
        // Ollama offline / timeout error alignment
        friendlyText = `AI Copilot is currently unavailable because the local Ollama service is offline or timed out. Please verify Ollama is running and hosting model '${health.model || "the configured model"}'.`;
      }

      const assistantMsg: Message = {
        id: "assistant-err-" + Date.now(),
        sender: "assistant",
        text: friendlyText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isError: true
      };
      saveMessages([...updatedMessages, assistantMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  // Suggested Prompts
  const suggestedPrompts = [
    { label: "Executive Summary", text: "Summarize this process analysis and provide the executive brief." },
    { label: "Top Carbon Risks", text: "What are the biggest carbon hotspots and carbon risks identified?" },
    { label: "Compliance Overview", text: "What are the highest-risk compliance violations and conformance deviations?" },
    { label: "Recommended Actions", text: "What recommendations exist for mitigating carbon hotspots?" },
    { label: "Simulation Opportunities", text: "What scenario simulation opportunities should management consider?" }
  ];

  return (
    <>
      {/* Drawer Overlay Backdrop */}
      <div className="fixed inset-0 bg-black/60 backdrop-blur-xs z-40 transition-opacity" onClick={onClose}></div>

      {/* Slide-out Sidebar Panel */}
      <div className="fixed inset-y-0 right-0 w-full sm:w-[420px] bg-card-bg border-l border-border-color shadow-2xl z-50 flex flex-col h-full animate-slideIn">
        
        {/* Header */}
        <div className="p-4 border-b border-border-color flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-blue-50 border border-blue-200 text-blue-600 rounded-lg">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-black text-foreground uppercase tracking-wider flex items-center gap-1.5">
                Executive Copilot
              </h3>
              {/* Context chips */}
              <div className="flex items-center gap-1.5 mt-1">
                <span className="text-xs font-semibold text-foreground bg-background border border-border-color px-2 py-0.5 rounded truncate max-w-[120px]">
                  {activeProjectName}
                </span>
                {activeAnalysisVersion && (
                  <span className="text-xs font-bold text-blue-700 bg-blue-50 border border-blue-250 px-2 py-0.5 rounded">
                    Analysis: {activeAnalysisVersion}
                  </span>
                )}
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => handleSendMessage("Generate Executive Summary")}
              disabled={isTyping}
              className="p-1.5 text-blue-600 hover:text-blue-500 hover:bg-slate-100 rounded disabled:opacity-50 transition-all cursor-pointer"
              title="Generate Executive Summary"
            >
              <Sparkles className="h-4 w-4" />
            </button>
            <button
              onClick={handleClearChat}
              className="p-1.5 text-text-muted hover:text-red-600 rounded hover:bg-slate-100 transition-all cursor-pointer"
              title="Clear Conversation"
            >
              <Trash2 className="h-4 w-4" />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-text-muted hover:text-foreground rounded hover:bg-slate-100 transition-all cursor-pointer"
              title="Close Panel"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Conversation Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-background">
          
          {messages.map((msg) => {
            const isUser = msg.sender === "user";
            return (
              <div key={msg.id} className={`flex ${isUser ? "justify-end" : "justify-start"} animate-fadeIn`}>
                <div className={`max-w-[85%] rounded-2xl p-3.5 shadow-sm text-sm font-medium leading-relaxed border ${
                  isUser
                    ? "bg-blue-600 border-blue-500 text-white rounded-br-none"
                    : msg.isError
                      ? "bg-amber-50 border-amber-200 text-amber-900 rounded-bl-none"
                      : "bg-white border-gray-150 text-gray-800 rounded-bl-none"
                }`}>
                  
                  {/* Message Header (Assistant metadata) */}
                  {!isUser && (msg.provider || msg.model) && (
                    <div className="flex items-center gap-1.5 text-xs text-gray-500 font-mono uppercase tracking-wider mb-1.5 border-b border-gray-50 pb-1 font-semibold">
                      <Bot className="h-3.5 w-3.5 text-blue-500" />
                      <span>{msg.provider}</span>
                      <span>•</span>
                      <span>{msg.model}</span>
                    </div>
                  )}

                  {/* Message Body */}
                  <div className="whitespace-pre-wrap font-medium">{msg.text}</div>

                  {/* Message Timestamp */}
                  <div className={`text-xs mt-1.5 text-right font-medium ${isUser ? "text-blue-200" : "text-gray-500"}`}>
                    {msg.timestamp}
                  </div>

                </div>
              </div>
            );
          })}

          {/* Typing Indicator */}
          {isTyping && (
            <div className="flex justify-start animate-fadeIn">
              <div className="bg-white border border-gray-150 rounded-2xl rounded-bl-none p-3.5 shadow-sm text-sm text-gray-500 flex items-center gap-1.5 font-medium">
                <Bot className="h-4.5 w-4.5 text-blue-500 animate-bounce" />
                <div className="flex space-x-1">
                  <span className="h-1.5 w-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></span>
                  <span className="h-1.5 w-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></span>
                  <span className="h-1.5 w-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Suggested Prompts Library */}
        {messages.length <= 1 && !isTyping && (
          <div className="p-4 border-t border-border-color bg-card-bg space-y-3">
            <button
              onClick={() => handleSendMessage("Generate Executive Summary")}
              className="w-full flex items-center justify-center gap-2.5 p-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl shadow-md font-bold text-sm hover:scale-[1.01] transition-all cursor-pointer"
            >
              <Sparkles className="h-4.5 w-4.5 text-blue-100 animate-pulse" />
              Generate Executive Summary
            </button>

            <span className="text-xs font-bold uppercase text-text-muted tracking-wider block pt-1">Suggested Actions</span>
            <div className="grid grid-cols-2 gap-2.5">
              {suggestedPrompts.map((p) => (
                <button
                  key={p.label}
                  onClick={() => handleSendMessage(p.text)}
                  className="p-2.5 border border-border-color hover:border-blue-200 hover:bg-blue-50/20 text-left rounded-lg transition-all focus:outline-none cursor-pointer"
                >
                  <div className="text-xs font-bold text-foreground">{p.label}</div>
                  <div className="text-xs text-text-muted mt-1 truncate">{p.text}</div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input Composer Form */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage(inputValue);
          }}
          className="p-3 border-t border-border-color bg-card-bg flex items-center gap-2"
        >
          <input
            type="text"
            placeholder="Ask Copilot about carbon hotspots or compliance..."
            className="flex-1 px-4 py-2.5 border border-border-color rounded-xl text-sm text-foreground bg-background focus:bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 transition-all font-medium"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isTyping}
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || isTyping}
            className="p-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white shadow-sm disabled:opacity-50 transition-all focus:outline-none flex items-center justify-center shrink-0 cursor-pointer"
          >
            <Send className="h-4 w-4" />
          </button>
        </form>

      </div>
    </>
  );
};
