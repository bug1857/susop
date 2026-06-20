import axios from "axios";
import { API_BASE_URL } from "./copilotEndpoints";

// Create Axios instance
export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 120 seconds (2 minutes)
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to attach Bearer token from localStorage
api.interceptors.request.use(
  (config) => {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interface for custom AxiosRequestConfig extensions
interface CustomRequestConfig {
  _retryCount?: number;
  _retry?: boolean;
}

// Response interceptor for transient failure retries & error normalization
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error;
    const customConfig = config as CustomRequestConfig & typeof config;
    
    // Check if configuration exists and is retryable
    if (customConfig && customConfig._retry !== true) {
      customConfig._retryCount = customConfig._retryCount || 0;
      
      // Determine if the error is transient:
      // - Network issues (no response)
      // - Timeout errors (ECONNABORTED)
      // - Server status code 503 (Service Unavailable) or 504 (Gateway Timeout)
      const isNetworkError = !response;
      const isTimeout = error.code === "ECONNABORTED";
      const isTransientStatus = response && (response.status === 503 || response.status === 504);
      
      if ((isNetworkError || isTimeout || isTransientStatus) && customConfig._retryCount < 2) {
        customConfig._retryCount += 1;
        if (customConfig._retryCount >= 2) {
          customConfig._retry = true; // Mark as done retrying
        }
        
        // Wait 1 second before retrying
        await new Promise((resolve) => setTimeout(resolve, 1000));
        return api(customConfig);
      }
    }
    
    // Normalize errors to prevent leakage of internal details (stack traces, raw IDs)
    const normalizedError = {
      message: "An error occurred while connecting to the sustainability services. Please retry.",
      status: response ? response.status : 500,
      errors: [] as any[],
    };
    
    if (response && response.data) {
      if (response.data.errors && response.data.errors.length > 0) {
        normalizedError.message = response.data.errors[0].message || normalizedError.message;
        normalizedError.errors = response.data.errors;
      } else if (response.data.detail) {
        normalizedError.message = typeof response.data.detail === "string" 
          ? response.data.detail 
          : JSON.stringify(response.data.detail);
      }
    } else if (error.message) {
      normalizedError.message = error.message;
    }
    
    return Promise.reject(normalizedError);
  }
);
