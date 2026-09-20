import axios from "axios";

// FastAPI serves this build's static files itself, so every request is
// always same-origin in production: a plain relative baseURL. In local dev
// (`npm run dev`), Vite's own proxy (see vite.config.mjs) forwards the same
// relative "/api/..." calls to the local FastAPI server, so no separate
// backend URL needs to be configured anywhere.
export const api = axios.create({ baseURL: "" });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      if (location.pathname !== "/login") location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export function apiErrorMessage(error: unknown, fallback = "Something went wrong. Please try again."): string {
  const detail = (error as any)?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
  return fallback;
}

export interface Project {
  id: number;
  project_name: string;
  aws_region: string;
  monthly_budget: number;
}

export interface ResourceEstimate {
  resource_type: string;
  resource_name: string;
  region: string;
  attributes: Record<string, unknown>;
  pricing_rate: string;
  pricing_unit: string;
  quantity: string;
  formula: string;
  estimated_cost: string;
  assumptions: string[];
  warnings: { field: string; message: string }[];
}

export interface BudgetPolicy {
  status: "PASS" | "WARNING" | "FAIL" | "NOT_CONFIGURED";
  budget: string;
  estimated_cost: string;
  budget_usage_percentage: number | null;
  remaining_budget: string | null;
  message: string;
}

export interface Recommendation {
  resource_name: string;
  issue: string;
  suggestion: string;
  current_estimated_cost: string;
  alternative_estimated_cost: string | null;
  estimated_savings: string | null;
  confidence: string;
  explanation: string;
}

export interface ScenarioResult {
  resources: ResourceEstimate[];
  total_monthly_cost: string;
}

export interface AnalysisReport {
  analysis_id: number;
  resources: ResourceEstimate[];
  total_monthly_cost: string;
  budget_policy: BudgetPolicy;
  recommendations: Recommendation[];
  unsupported_warnings: string[];
  scenario_comparison: Record<"low" | "medium" | "high", ScenarioResult>;
  pricing_effective_date: string;
  pricing_currency: string;
  pricing_source: string;
}
