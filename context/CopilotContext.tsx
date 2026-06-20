"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";
import { api } from "../services/api";
import { COPILOT_ENDPOINTS, PROCESS_ENDPOINTS } from "../services/copilotEndpoints";
import { useAuth } from "./AuthContext";

export interface HealthState {
  provider: string | null;
  model: string | null;
  status: "healthy" | "unhealthy" | "loading";
}

export interface ModuleState<T> {
  status: "idle" | "loading" | "error" | "success";
  data: T | null;
  error: string | null;
}

interface Analysis {
  id: string;
  tenant_id: string;
  workspace_id: string;
  project_id: string;
  dataset_id: string;
  analysis_version: number;
  status: string;
  created_at: string;
  completed_at: string | null;
}

interface CopilotContextType {
  // Context selection
  selectedProjectId: string | null;
  selectedAnalysisId: string | null;
  analyses: Analysis[];
  loadingAnalyses: boolean;
  setSelectedProjectId: (id: string | null) => void;
  setSelectedAnalysisId: (id: string | null) => void;
  
  // AI Module States
  health: HealthState;
  insights: ModuleState<any[]>;
  forecasts: ModuleState<any[]>;
  simulations: ModuleState<any[]>;
  recommendations: ModuleState<any[]>;
  explanations: ModuleState<any[]>;
  copilotResponses: ModuleState<any[]>;
  
  // Process Metric States for KPIs
  carbonAttribution: ModuleState<any>;
  conformance: ModuleState<any>;
  deviations: ModuleState<any[]>;
  
  // Fetch / Refresh Actions
  refreshAll: () => void;
  refreshModule: (moduleName: string) => void;
  fetchHealth: () => Promise<void>;
  fetchAnalyses: (workspaceId: string, projectId: string) => Promise<void>;
  
  // Generation Triggers
  generateForecast: (period: string, method: string) => Promise<void>;
  runSimulation: (name: string, description: string, type: string, reductionPercent: number) => Promise<void>;
  generateRecommendations: () => Promise<void>;
  generateExplanation: (entityType: string, entityId: string) => Promise<void>;
  generateCopilotResponse: (requestType: string, entityType: string, entityId: string) => Promise<void>;
  generateInsights: () => Promise<void>; // Handles non-existent endpoint gracefully
}

const CopilotContext = createContext<CopilotContextType | undefined>(undefined);

export const CopilotProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { activeWorkspace, projects, token } = useAuth();

  
  // Context selectors
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<string | null>(null);
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [loadingAnalyses, setLoadingAnalyses] = useState(false);
  
  // States
  const [health, setHealth] = useState<HealthState>({ provider: null, model: null, status: "loading" });
  
  function createInitialState<T>(initialData: T | null = null): ModuleState<T> {
    return {
      status: "idle",
      data: initialData,
      error: null,
    };
  }

  const [insights, setInsights] = useState<ModuleState<any[]>>(createInitialState([]));
  const [forecasts, setForecasts] = useState<ModuleState<any[]>>(createInitialState([]));
  const [simulations, setSimulations] = useState<ModuleState<any[]>>(createInitialState([]));
  const [recommendations, setRecommendations] = useState<ModuleState<any[]>>(createInitialState([]));
  const [explanations, setExplanations] = useState<ModuleState<any[]>>(createInitialState([]));
  const [copilotResponses, setCopilotResponses] = useState<ModuleState<any[]>>(createInitialState([]));
  
  const [carbonAttribution, setCarbonAttribution] = useState<ModuleState<any>>(createInitialState(null));
  const [conformance, setConformance] = useState<ModuleState<any>>(createInitialState(null));
  const [deviations, setDeviations] = useState<ModuleState<any[]>>(createInitialState([]));

  // Request cache and in-flight tracking
  const cache = useRef<{ [key: string]: any }>({});
  const inFlightRequests = useRef<{ [key: string]: Promise<any> | undefined }>({});
  // Health debounce: only flip to unhealthy after N consecutive failures
  const healthFailCount = useRef(0);
  const HEALTH_FAIL_THRESHOLD = 2;

  // Reset context selectors when workspace changes
  useEffect(() => {
    setSelectedProjectId(null);
    setSelectedAnalysisId(null);
    setAnalyses([]);
    cache.current = {};
    inFlightRequests.current = {};
  }, [activeWorkspace]);

  // Set default selected project
  useEffect(() => {
    if (projects && projects.length > 0 && !selectedProjectId) {
      setSelectedProjectId(projects[0].id);
    }
  }, [projects, selectedProjectId]);

  // Centralized request runner with deduplication and caching
  const runRequest = useCallback(async (key: string, fetchFn: () => Promise<any>, useCache = true) => {
    if (useCache && cache.current[key]) {
      return cache.current[key];
    }
    if (inFlightRequests.current[key]) {
      return inFlightRequests.current[key];
    }

    const promise = fetchFn()
      .then((data) => {
        if (useCache) {
          cache.current[key] = data;
        }
        delete inFlightRequests.current[key];
        return data;
      })
      .catch((err) => {
        delete inFlightRequests.current[key];
        throw err;
      });

    inFlightRequests.current[key] = promise;
    return promise;
  }, []);

  // Fetch Health check
  const fetchHealth = useCallback(async () => {
    // Only show "loading" on the very first call (status is still the initial "loading")
    // Never flicker back to loading during polling
    setHealth((h) => (h.status === "loading" ? h : h));
    try {
      const workspaceQuery = activeWorkspace?.id ? `?workspace_id=${activeWorkspace.id}` : "";
      const res = await api.get(`${COPILOT_ENDPOINTS.HEALTH}${workspaceQuery}`);
      if (res.data) {
        healthFailCount.current = 0;
        setHealth((prev) => ({
          provider: res.data.provider || prev.provider || "OLLAMA",
          model: res.data.model || prev.model || null,
          status: res.data.status === "healthy" ? "healthy" : "unhealthy",
        }));
      }
    } catch (err) {
      healthFailCount.current += 1;
      // Only flip to unhealthy after HEALTH_FAIL_THRESHOLD consecutive failures
      // to prevent brief network hiccups from showing as offline
      if (healthFailCount.current >= HEALTH_FAIL_THRESHOLD) {
        setHealth((prev) => ({
          provider: prev.provider || "OLLAMA",
          model: prev.model || null, // keep last-known model name
          status: "unhealthy",
        }));
      }
    }
  }, [activeWorkspace?.id]);

  // Fetch process history analyses
  const fetchAnalyses = useCallback(async (workspaceId: string, projectId: string) => {
    setLoadingAnalyses(true);
    try {
      const cacheKey = `analyses_${workspaceId}_${projectId}`;
      const res = await runRequest(cacheKey, () =>
        api.get(`${PROCESS_ENDPOINTS.HISTORY}?workspace_id=${workspaceId}&project_id=${projectId}`),
        false
      );
      // Backend returns directly array or data payload
      const data = Array.isArray(res.data) ? res.data : (res.data?.data || []);
      const completedAnalyses = data.filter((a: any) => a.status === "completed" || a.status === "ready");
      setAnalyses(completedAnalyses);
      setSelectedAnalysisId((prevId) => {
        if (prevId && completedAnalyses.some((a: any) => a.id === prevId)) {
          return prevId;
        }
        return completedAnalyses.length > 0 ? completedAnalyses[0].id : null;
      });
    } catch (err) {
      setAnalyses([]);
      setSelectedAnalysisId(null);
    } finally {
      setLoadingAnalyses(false);
    }
  }, [runRequest]);

  // Load analyses when project is selected
  useEffect(() => {
    if (activeWorkspace?.id && selectedProjectId) {
      fetchAnalyses(activeWorkspace.id, selectedProjectId);
    } else {
      setAnalyses([]);
      setSelectedAnalysisId(null);
    }
  }, [activeWorkspace, selectedProjectId, fetchAnalyses]);

  // Loader implementations for modules
  const fetchInsights = useCallback(async (analysisId: string) => {
    setInsights((s) => ({ ...s, status: "loading", error: null }));
    try {
      const workspaceQuery = activeWorkspace?.id ? `&workspace_id=${activeWorkspace.id}` : "";
      const projectQuery = selectedProjectId ? `&project_id=${selectedProjectId}` : "";
      const cacheKey = `insights_${analysisId}`;
      const res = await runRequest(cacheKey, () =>
        api.get(`${COPILOT_ENDPOINTS.INSIGHTS}?analysis_id=${analysisId}${workspaceQuery}${projectQuery}`)
      );
      setInsights({ status: "success", data: res.data.data || [], error: null });
    } catch (err: any) {
      setInsights({ status: "error", data: [], error: err.message });
    }
  }, [runRequest, activeWorkspace, selectedProjectId]);

  const fetchForecasts = useCallback(async (analysisId: string) => {
    setForecasts((s) => ({ ...s, status: "loading", error: null }));
    try {
      const workspaceQuery = activeWorkspace?.id ? `&workspace_id=${activeWorkspace.id}` : "";
      const projectQuery = selectedProjectId ? `&project_id=${selectedProjectId}` : "";
      const cacheKey = `forecasts_${analysisId}`;
      const res = await runRequest(cacheKey, () =>
        api.get(`${COPILOT_ENDPOINTS.FORECASTS}?analysis_id=${analysisId}${workspaceQuery}${projectQuery}`)
      );
      const rawData = res.data.data || [];
      const mappedData = rawData.map((item: any) => ({
        ...item,
        period: item.period || item.forecast_period,
        forecasted_emissions: item.forecasted_emissions !== undefined ? item.forecasted_emissions : item.predicted_emissions
      }));
      setForecasts({ status: "success", data: mappedData, error: null });
    } catch (err: any) {
      setForecasts({ status: "error", data: [], error: err.message });
    }
  }, [runRequest, activeWorkspace, selectedProjectId]);

  const fetchSimulations = useCallback(async (analysisId: string) => {
    setSimulations((s) => ({ ...s, status: "loading", error: null }));
    try {
      const workspaceQuery = activeWorkspace?.id ? `&workspace_id=${activeWorkspace.id}` : "";
      const projectQuery = selectedProjectId ? `&project_id=${selectedProjectId}` : "";
      const cacheKey = `simulations_${analysisId}`;
      const res = await runRequest(cacheKey, () =>
        api.get(`${COPILOT_ENDPOINTS.SIMULATIONS}?analysis_id=${analysisId}${workspaceQuery}${projectQuery}`)
      );
      setSimulations({ status: "success", data: res.data.data || [], error: null });
    } catch (err: any) {
      setSimulations({ status: "error", data: [], error: err.message });
    }
  }, [runRequest, activeWorkspace, selectedProjectId]);

  const fetchRecommendations = useCallback(async (analysisId: string) => {
    setRecommendations((s) => ({ ...s, status: "loading", error: null }));
    try {
      const workspaceQuery = activeWorkspace?.id ? `&workspace_id=${activeWorkspace.id}` : "";
      const projectQuery = selectedProjectId ? `&project_id=${selectedProjectId}` : "";
      const cacheKey = `recommendations_${analysisId}`;
      const res = await runRequest(cacheKey, () =>
        api.get(`${COPILOT_ENDPOINTS.RECOMMENDATIONS}?analysis_id=${analysisId}${workspaceQuery}${projectQuery}`)
      );
      setRecommendations({ status: "success", data: res.data.data || [], error: null });
    } catch (err: any) {
      setRecommendations({ status: "error", data: [], error: err.message });
    }
  }, [runRequest, activeWorkspace, selectedProjectId]);

  const fetchExplanations = useCallback(async (analysisId: string) => {
    setExplanations((s) => ({ ...s, status: "loading", error: null }));
    try {
      const workspaceQuery = activeWorkspace?.id ? `&workspace_id=${activeWorkspace.id}` : "";
      const projectQuery = selectedProjectId ? `&project_id=${selectedProjectId}` : "";
      const cacheKey = `explanations_${analysisId}`;
      const res = await runRequest(cacheKey, () =>
        api.get(`${COPILOT_ENDPOINTS.EXPLANATIONS}?analysis_id=${analysisId}${workspaceQuery}${projectQuery}`)
      );
      setExplanations({ status: "success", data: res.data.data || [], error: null });
    } catch (err: any) {
      setExplanations({ status: "error", data: [], error: err.message });
    }
  }, [runRequest, activeWorkspace, selectedProjectId]);

  const fetchCopilotResponses = useCallback(async (analysisId: string) => {
    setCopilotResponses((s) => ({ ...s, status: "loading", error: null }));
    try {
      const workspaceQuery = activeWorkspace?.id ? `&workspace_id=${activeWorkspace.id}` : "";
      const projectQuery = selectedProjectId ? `&project_id=${selectedProjectId}` : "";
      const cacheKey = `responses_${analysisId}`;
      const res = await runRequest(cacheKey, () =>
        api.get(`${COPILOT_ENDPOINTS.COPILOT_RESPONSES}?analysis_id=${analysisId}${workspaceQuery}${projectQuery}`)
      );
      setCopilotResponses({ status: "success", data: res.data.data || [], error: null });
    } catch (err: any) {
      setCopilotResponses({ status: "error", data: [], error: err.message });
    }
  }, [runRequest, activeWorkspace, selectedProjectId]);

  // Process data loaders (KPI row and chart components)
  const fetchCarbonAttribution = useCallback(async (analysisId: string) => {
    setCarbonAttribution((s) => ({ ...s, status: "loading", error: null }));
    try {
      const cacheKey = `carbon_attribution_${analysisId}`;
      const res = await runRequest(cacheKey, () =>
        api.get(PROCESS_ENDPOINTS.CARBON_ATTRIBUTION(analysisId))
      );
      setCarbonAttribution({ status: "success", data: res.data.data || res.data, error: null });
    } catch (err: any) {
      setCarbonAttribution({ status: "error", data: null, error: err.message });
    }
  }, [runRequest]);

  const fetchConformance = useCallback(async (analysisId: string) => {
    setConformance((s) => ({ ...s, status: "loading", error: null }));
    try {
      const cacheKey = `conformance_${analysisId}`;
      const res = await runRequest(cacheKey, () =>
        api.get(PROCESS_ENDPOINTS.CONFORMANCE(analysisId))
      );
      setConformance({ status: "success", data: res.data.data || res.data, error: null });
    } catch (err: any) {
      setConformance({ status: "error", data: null, error: err.message });
    }
  }, [runRequest]);

  const fetchDeviations = useCallback(async (analysisId: string) => {
    setDeviations((s) => ({ ...s, status: "loading", error: null }));
    try {
      const cacheKey = `deviations_${analysisId}`;
      const res = await runRequest(cacheKey, () =>
        api.get(PROCESS_ENDPOINTS.DEVIATIONS(analysisId))
      );
      setDeviations({ status: "success", data: res.data.data?.deviations || res.data.data || [], error: null });
    } catch (err: any) {
      setDeviations({ status: "error", data: [], error: err.message });
    }
  }, [runRequest]);

  // Trigger loading when selected analysis changes
  useEffect(() => {
    if (selectedAnalysisId) {
      fetchInsights(selectedAnalysisId);
      fetchForecasts(selectedAnalysisId);
      fetchSimulations(selectedAnalysisId);
      fetchRecommendations(selectedAnalysisId);
      fetchExplanations(selectedAnalysisId);
      fetchCopilotResponses(selectedAnalysisId);
      fetchCarbonAttribution(selectedAnalysisId);
      fetchConformance(selectedAnalysisId);
      fetchDeviations(selectedAnalysisId);
    } else {
      // Clear states
      setInsights(createInitialState([]));
      setForecasts(createInitialState([]));
      setSimulations(createInitialState([]));
      setRecommendations(createInitialState([]));
      setExplanations(createInitialState([]));
      setCopilotResponses(createInitialState([]));
      setCarbonAttribution(createInitialState(null));
      setConformance(createInitialState(null));
      setDeviations(createInitialState([]));
    }
  }, [
    selectedAnalysisId,
    fetchInsights,
    fetchForecasts,
    fetchSimulations,
    fetchRecommendations,
    fetchExplanations,
    fetchCopilotResponses,
    fetchCarbonAttribution,
    fetchConformance,
    fetchDeviations,
  ]);

  // Poll health status check periodically & re-fetch when token changes
  useEffect(() => {
    if (token) {
      fetchHealth();
      const interval = setInterval(fetchHealth, 10000); // Poll every 10 seconds
      return () => clearInterval(interval);
    }
  }, [fetchHealth, token]);


  // Refresh actions
  const refreshAll = useCallback(() => {
    if (selectedAnalysisId) {
      // Clear cache references
      delete cache.current[`insights_${selectedAnalysisId}`];
      delete cache.current[`forecasts_${selectedAnalysisId}`];
      delete cache.current[`simulations_${selectedAnalysisId}`];
      delete cache.current[`recommendations_${selectedAnalysisId}`];
      delete cache.current[`explanations_${selectedAnalysisId}`];
      delete cache.current[`responses_${selectedAnalysisId}`];
      delete cache.current[`carbon_attribution_${selectedAnalysisId}`];
      delete cache.current[`conformance_${selectedAnalysisId}`];
      delete cache.current[`deviations_${selectedAnalysisId}`];

      fetchInsights(selectedAnalysisId);
      fetchForecasts(selectedAnalysisId);
      fetchSimulations(selectedAnalysisId);
      fetchRecommendations(selectedAnalysisId);
      fetchExplanations(selectedAnalysisId);
      fetchCopilotResponses(selectedAnalysisId);
      fetchCarbonAttribution(selectedAnalysisId);
      fetchConformance(selectedAnalysisId);
      fetchDeviations(selectedAnalysisId);
    }
    fetchHealth();
  }, [
    selectedAnalysisId,
    fetchInsights,
    fetchForecasts,
    fetchSimulations,
    fetchRecommendations,
    fetchExplanations,
    fetchCopilotResponses,
    fetchCarbonAttribution,
    fetchConformance,
    fetchDeviations,
    fetchHealth,
  ]);

  const refreshModule = useCallback((moduleName: string) => {
    if (!selectedAnalysisId) return;

    switch (moduleName) {
      case "insights":
        delete cache.current[`insights_${selectedAnalysisId}`];
        fetchInsights(selectedAnalysisId);
        break;
      case "forecasts":
        delete cache.current[`forecasts_${selectedAnalysisId}`];
        fetchForecasts(selectedAnalysisId);
        break;
      case "simulations":
        delete cache.current[`simulations_${selectedAnalysisId}`];
        fetchSimulations(selectedAnalysisId);
        break;
      case "recommendations":
        delete cache.current[`recommendations_${selectedAnalysisId}`];
        fetchRecommendations(selectedAnalysisId);
        break;
      case "explanations":
        delete cache.current[`explanations_${selectedAnalysisId}`];
        fetchExplanations(selectedAnalysisId);
        break;
      case "responses":
        delete cache.current[`responses_${selectedAnalysisId}`];
        fetchCopilotResponses(selectedAnalysisId);
        break;
      case "metrics":
        delete cache.current[`carbon_attribution_${selectedAnalysisId}`];
        delete cache.current[`conformance_${selectedAnalysisId}`];
        delete cache.current[`deviations_${selectedAnalysisId}`];
        fetchCarbonAttribution(selectedAnalysisId);
        fetchConformance(selectedAnalysisId);
        fetchDeviations(selectedAnalysisId);
        break;
      case "health":
        fetchHealth();
        break;
    }
  }, [
    selectedAnalysisId,
    fetchInsights,
    fetchForecasts,
    fetchSimulations,
    fetchRecommendations,
    fetchExplanations,
    fetchCopilotResponses,
    fetchCarbonAttribution,
    fetchConformance,
    fetchDeviations,
    fetchHealth,
  ]);

  // Generation Actions

  const generateForecast = useCallback(async (period: string, method: string) => {
    if (!selectedAnalysisId || !selectedProjectId || !activeWorkspace?.id) return;
    setForecasts((s) => ({ ...s, status: "loading", error: null }));
    try {
      await api.post(COPILOT_ENDPOINTS.GENERATE_FORECAST, {
        workspace_id: activeWorkspace.id,
        project_id: selectedProjectId,
        analysis_id: selectedAnalysisId,
        forecast_period: period,
        forecast_method: method,
      });
      refreshModule("forecasts");
    } catch (err: any) {
      setForecasts({ status: "error", data: [], error: err.message || "Failed to generate carbon forecast." });
    }
  }, [activeWorkspace, selectedProjectId, selectedAnalysisId, refreshModule]);

  const runSimulation = useCallback(async (name: string, description: string, type: string, reductionPercent: number) => {
    if (!selectedAnalysisId || !selectedProjectId || !activeWorkspace?.id) return;
    try {
      await api.post(COPILOT_ENDPOINTS.RUN_SIMULATION, {
        workspace_id: activeWorkspace.id,
        project_id: selectedProjectId,
        analysis_id: selectedAnalysisId,
        scenario_name: name,
        scenario_description: description,
        scenario_type: type,
        baseline_reduction_percent: reductionPercent,
      });
      refreshModule("simulations");
    } catch (err: any) {
      throw new Error(err.message || "Failed to execute scenario simulation.");
    }
  }, [activeWorkspace, selectedProjectId, selectedAnalysisId, refreshModule]);

  const generateRecommendations = useCallback(async () => {
    if (!selectedAnalysisId || !selectedProjectId || !activeWorkspace?.id) return;
    try {
      await api.post(COPILOT_ENDPOINTS.GENERATE_RECOMMENDATIONS, {
        workspace_id: activeWorkspace.id,
        project_id: selectedProjectId,
        analysis_id: selectedAnalysisId,
      });
      refreshModule("recommendations");
    } catch (err: any) {
      throw new Error(err.message || "Failed to generate recommendations.");
    }
  }, [activeWorkspace, selectedProjectId, selectedAnalysisId, refreshModule]);

  const generateExplanation = useCallback(async (entityType: string, entityId: string) => {
    if (!selectedAnalysisId || !selectedProjectId || !activeWorkspace?.id) return;
    try {
      await api.post(COPILOT_ENDPOINTS.GENERATE_EXPLANATION, {
        workspace_id: activeWorkspace.id,
        project_id: selectedProjectId,
        analysis_id: selectedAnalysisId,
        entity_type: entityType,
        entity_id: entityId,
      });
      refreshModule("explanations");
    } catch (err: any) {
      throw new Error(err.message || "Failed to generate explainability record.");
    }
  }, [activeWorkspace, selectedProjectId, selectedAnalysisId, refreshModule]);

  const generateCopilotResponse = useCallback(async (requestType: string, entityType: string, entityId: string) => {
    if (!selectedAnalysisId || !selectedProjectId || !activeWorkspace?.id) return;
    try {
      await api.post(COPILOT_ENDPOINTS.COPILOT_GENERATE, {
        workspace_id: activeWorkspace.id,
        project_id: selectedProjectId,
        analysis_id: selectedAnalysisId,
        request_type: requestType,
        provider: "OLLAMA",
        entity_type: entityType,
        entity_id: entityId,
      });
      refreshModule("responses");
    } catch (err: any) {
      throw new Error(err.message || "Failed to generate AI Copilot response.");
    }
  }, [activeWorkspace, selectedProjectId, selectedAnalysisId, refreshModule]);

  // Gracefully handles non-existent endpoint for insights generation as requested
  const generateInsights = useCallback(async () => {
    setInsights((s) => ({ ...s, status: "loading", error: null }));
    await new Promise((resolve) => setTimeout(resolve, 800)); // Loading transition simulator
    const normalizedError = {
      message: "The backend does not expose a standalone insights generation route. Insights are calculated automatically during the process discovery analysis.",
      status: 404,
    };
    setInsights((s) => ({
      ...s,
      status: "error",
      error: normalizedError.message,
    }));
    throw new Error(normalizedError.message);
  }, []);

  return (
    <CopilotContext.Provider
      value={{
        selectedProjectId,
        selectedAnalysisId,
        analyses,
        loadingAnalyses,
        setSelectedProjectId,
        setSelectedAnalysisId,
        health,
        insights,
        forecasts,
        simulations,
        recommendations,
        explanations,
        copilotResponses,
        carbonAttribution,
        conformance,
        deviations,
        refreshAll,
        refreshModule,
        fetchHealth,
        fetchAnalyses,
        generateForecast,
        runSimulation,
        generateRecommendations,
        generateExplanation,
        generateCopilotResponse,
        generateInsights,
      }}
    >
      {children}
    </CopilotContext.Provider>
  );
};

export const useCopilot = () => {
  const context = useContext(CopilotContext);
  if (context === undefined) {
    throw new Error("useCopilot must be used within a CopilotProvider");
  }
  return context;
};
