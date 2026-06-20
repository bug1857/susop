export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const COPILOT_ENDPOINTS = {
  // Health check
  HEALTH: "/api/v1/copilot/health",

  // Insights
  INSIGHTS: "/api/v1/copilot/insights",

  // Forecasts
  FORECASTS: "/api/v1/copilot/forecasts",
  GENERATE_FORECAST: "/api/v1/copilot/forecasts/generate",

  // Simulations
  SIMULATIONS: "/api/v1/copilot/simulations",
  RUN_SIMULATION: "/api/v1/copilot/simulations/run",

  // Recommendations
  RECOMMENDATIONS: "/api/v1/copilot/recommendations",
  GENERATE_RECOMMENDATIONS: "/api/v1/copilot/recommendations/generate",
  RECOMMENDATION_EVIDENCE: (id: string) => `/api/v1/copilot/recommendations/${id}/evidence`,

  // Explanations
  EXPLANATIONS: "/api/v1/copilot/explanations",
  GENERATE_EXPLANATION: "/api/v1/copilot/explanations/generate",

  // LLM Copilot Responses
  COPILOT_GENERATE: "/api/v1/copilot/generate",
  COPILOT_RESPONSES: "/api/v1/copilot/responses",
};

export const PROCESS_ENDPOINTS = {
  // Context & History
  HISTORY: "/api/process/history",
  ANALYSIS_DETAILS: (id: string) => `/api/process/${id}`,
  
  // Metrics & Visualizations
  CARBON_ATTRIBUTION: (id: string) => `/api/process/${id}/carbon-attribution`,
  CONFORMANCE: (id: string) => `/api/process/${id}/conformance`,
  DEVIATIONS: (id: string) => `/api/process/${id}/deviations`,
  HOTSPOTS: (id: string) => `/api/process/${id}/hotspots`,
};
