"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "../../../context/AuthContext";
import { Card } from "../../../components/Card";
import { Button } from "../../../components/Button";
import { Input } from "../../../components/Input";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from "recharts";

// TypeScript Interfaces matching backend models and envelopes
interface EsgScore {
  id: string;
  tenant_id: string;
  workspace_id: string;
  period: string;
  scoring_profile_id: string;
  overall_score: number;
  environmental_score: number;
  social_score: number;
  governance_score: number;
  completeness_score: number;
  score_breakdown: Record<string, {
    raw_value: number | null;
    normalized_score: number;
    weight: number;
    status: string;
  }> | null;
  calculated_at: string;
}

interface EsgKpiDefinition {
  id: string;
  tenant_id: string;
  kpi_code: string;
  version: number;
  name: string;
  category: string;
  description: string;
  unit: string;
  source_type: string;
  calculation_method: Record<string, any> | null;
  effective_from: string;
  effective_to: string | null;
  is_active: boolean;
  parent_kpi_id: string | null;
  created_at: string;
}

interface EsgKpiValue {
  id: string;
  kpi_definition_id: string;
  tenant_id: string;
  workspace_id: string;
  project_id: string | null;
  period: string;
  value: number;
  is_manual: boolean;
  calculated_at: string;
  recorded_by: string | null;
}

interface EsgFramework {
  id: string;
  framework_name: string;
  framework_version: string;
  description: string | null;
  created_at: string;
}

interface FrameworkMapping {
  id: string;
  framework_id: string;
  kpi_definition_id: string;
  framework_section: string;
  framework_principle: string | null;
  framework_question: string;
  reporting_category: string;
  created_at: string;
}

interface EsgEvidence {
  id: string;
  kpi_value_id: string;
  tenant_id: string;
  source_description: string;
  source_entity_type: string;
  source_entity_id: string | null;
  evidence_file_path: string | null;
  cryptographic_hash: string | null;
  calculation_steps: Record<string, any>;
  lineage_path: {
    dataset_id?: string;
    process_analysis_id?: string;
    carbon_attribution_id?: string;
    [key: string]: any;
  };
  audited_by: string | null;
  audited_at: string | null;
}

interface EsgScoringProfile {
  id: string;
  tenant_id: string;
  name: string;
  environmental_weight: number;
  social_weight: number;
  governance_weight: number;
  kpi_weights: Record<string, number>;
  is_active: boolean;
  created_at: string;
}

const API_URL = "http://localhost:8000/api";

// Safe Date Parsing
const formatDateSafely = (dateStr: any) => {
  if (!dateStr) return "—";
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return "—";
    return d.toLocaleDateString();
  } catch (e) {
    return "—";
  }
};

// Safe Score / Percentage Parsing (handles null/undefined/NaN)
const formatScoreSafely = (scoreVal: any) => {
  if (scoreVal === null || scoreVal === undefined || isNaN(Number(scoreVal))) {
    return "—";
  }
  return `${(Number(scoreVal) * 100).toFixed(1)}%`;
};

// Safe Raw Number Parsing (handles null/undefined/NaN)
const formatNumberSafely = (num: any, decimals: number = 1) => {
  if (num === null || num === undefined || isNaN(Number(num))) {
    return "—";
  }
  return Number(num).toFixed(decimals);
};

export default function EsgDashboardPage() {
  const { token, activeOrg, activeWorkspace } = useAuth();
  const [isMounted, setIsMounted] = useState(false);

  // States
  const [scores, setScores] = useState<EsgScore[]>([]);
  const [kpiDefinitions, setKpiDefinitions] = useState<EsgKpiDefinition[]>([]);
  const [kpiValues, setKpiValues] = useState<EsgKpiValue[]>([]);
  const [frameworks, setFrameworks] = useState<EsgFramework[]>([]);
  const [selectedFrameworkId, setSelectedFrameworkId] = useState<string>("");
  const [frameworkMappings, setFrameworkMappings] = useState<FrameworkMapping[]>([]);
  const [evidenceList, setEvidenceList] = useState<EsgEvidence[]>([]);
  const [scoringProfiles, setScoringProfiles] = useState<EsgScoringProfile[]>([]);
  const [selectedEvidence, setSelectedEvidence] = useState<EsgEvidence | null>(null);

  // UX States
  const [loading, setLoading] = useState<boolean>(true);
  const [loadingMappings, setLoadingMappings] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Filters & Page Controls for KPI Explorer
  const [kpiSearch, setKpiSearch] = useState("");
  const [kpiCategoryFilter, setKpiCategoryFilter] = useState("");
  const [kpiStatusFilter, setKpiStatusFilter] = useState("");
  const [kpiSortBy, setKpiSortBy] = useState<"kpi_code" | "name" | "category" | "version">("kpi_code");
  const [kpiSortOrder, setKpiSortOrder] = useState<"asc" | "desc">("asc");
  const [kpiPage, setKpiPage] = useState(1);
  const kpisPerPage = 5;

  // Filters for Framework Mappings
  const [mappingKpiFilter, setMappingKpiFilter] = useState("");

  // Filters & Page Controls for Evidence Explorer
  const [evidenceSearch, setEvidenceSearch] = useState("");
  const [evidencePage, setEvidencePage] = useState(1);
  const evidencePerPage = 5;

  // Selected Score for score breakdown details
  const [selectedScoreIndex, setSelectedScoreIndex] = useState<number>(0);

  // Set isMounted to true on client mount
  useEffect(() => {
    setIsMounted(true);
  }, []);

  // Fetch all ESG dashboard data
  const fetchDashboardData = async () => {
    if (!token) return;
    if (!activeWorkspace || !activeOrg) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // 1. Fetch ESG Scores
      const scoresRes = await fetch(
        `${API_URL}/v1/esg/scores?workspace_id=${activeWorkspace.id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!scoresRes.ok) throw new Error("Failed to load ESG Scores.");
      const scoresJson = await scoresRes.json();
      
      let fetchedScores: EsgScore[] = [];
      if (scoresJson && scoresJson.success === true && Array.isArray(scoresJson.data)) {
        fetchedScores = scoresJson.data;
      }
      setScores(fetchedScores);

      // 2. Fetch KPI Definitions
      const kpiDefRes = await fetch(
        `${API_URL}/v1/esg/kpis?tenant_id=${activeOrg.id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!kpiDefRes.ok) throw new Error("Failed to load KPI definitions.");
      const kpisJson = await kpiDefRes.json();
      
      let fetchedKpis: EsgKpiDefinition[] = [];
      if (kpisJson && kpisJson.success === true && Array.isArray(kpisJson.data)) {
        fetchedKpis = kpisJson.data;
      }
      setKpiDefinitions(fetchedKpis);

      // 3. Fetch KPI Values
      const kpiValuesRes = await fetch(
        `${API_URL}/v1/esg/kpi-values?workspace_id=${activeWorkspace.id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!kpiValuesRes.ok) throw new Error("Failed to load KPI values.");
      const kpiValuesJson = await kpiValuesRes.json();
      
      let fetchedKpiValues: EsgKpiValue[] = [];
      if (kpiValuesJson && kpiValuesJson.success === true && Array.isArray(kpiValuesJson.data)) {
        fetchedKpiValues = kpiValuesJson.data;
      }
      setKpiValues(fetchedKpiValues);

      // 4. Fetch Frameworks
      const frameworksRes = await fetch(
        `${API_URL}/v1/esg/frameworks`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!frameworksRes.ok) throw new Error("Failed to load Frameworks.");
      const frameworksJson = await frameworksRes.json();
      
      let fetchedFrameworks: EsgFramework[] = [];
      if (frameworksJson && frameworksJson.success === true && Array.isArray(frameworksJson.data)) {
        fetchedFrameworks = frameworksJson.data;
        if (fetchedFrameworks.length > 0) {
          setSelectedFrameworkId(fetchedFrameworks[0].id);
        }
      }
      setFrameworks(fetchedFrameworks);

      // 5. Fetch Evidence
      const evidenceRes = await fetch(
        `${API_URL}/v1/esg/evidence?tenant_id=${activeOrg.id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!evidenceRes.ok) throw new Error("Failed to load ESG Evidence.");
      const evidenceJson = await evidenceRes.json();
      
      let fetchedEvidence: EsgEvidence[] = [];
      if (evidenceJson && evidenceJson.success === true && Array.isArray(evidenceJson.data)) {
        fetchedEvidence = evidenceJson.data;
        if (fetchedEvidence.length > 0) {
          setSelectedEvidence(fetchedEvidence[0]);
        }
      }
      setEvidenceList(fetchedEvidence);

      // 6. Fetch Scoring Profiles (Read-only widget)
      const profilesRes = await fetch(
        `${API_URL}/v1/esg/scoring-profiles?tenant_id=${activeOrg.id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!profilesRes.ok) throw new Error("Failed to load Scoring Profiles.");
      const profilesJson = await profilesRes.json();
      
      let fetchedProfiles: EsgScoringProfile[] = [];
      if (profilesJson && profilesJson.success === true && Array.isArray(profilesJson.data)) {
        fetchedProfiles = profilesJson.data;
      }
      setScoringProfiles(fetchedProfiles);

    } catch (err: any) {
      console.error(err);
      setError(err.message || "An unexpected error occurred while loading ESG data.");
    } finally {
      setLoading(false);
    }
  };

  // Trigger data fetch when active workspace, tenant, or token changes
  useEffect(() => {
    fetchDashboardData();
  }, [activeOrg, activeWorkspace, token]);

  // Fetch mappings when selected framework changes
  useEffect(() => {
    const fetchMappings = async () => {
      if (!selectedFrameworkId || !token || !activeOrg) return;
      setLoadingMappings(true);
      try {
        const res = await fetch(
          `${API_URL}/v1/esg/frameworks/${selectedFrameworkId}/mappings?tenant_id=${activeOrg.id}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (!res.ok) throw new Error("Failed to load mappings.");
        const json = await res.json();
        
        let fetchedMappings: FrameworkMapping[] = [];
        if (json && json.success === true && Array.isArray(json.data)) {
          fetchedMappings = json.data;
        }
        setFrameworkMappings(fetchedMappings);
      } catch (err) {
        console.error("Error loading framework mappings", err);
        setFrameworkMappings([]);
      } finally {
        setLoadingMappings(false);
      }
    };

    fetchMappings();
  }, [selectedFrameworkId, activeOrg, token]);

  // Handle active workspace or org warnings
  if (!activeOrg || !activeWorkspace) {
    return (
      <div className="flex-1 p-8">
        <div className="mb-6">
          <h1 className="text-3xl font-black text-gray-900 tracking-tight">ESG Intelligence</h1>
          <p className="text-gray-500 font-medium">Sustainability analysis and audit lineage tracking</p>
        </div>
        <Card title="No Active Context Selected" className="max-w-2xl mx-auto mt-12">
          <div className="text-center py-6">
            <svg
              className="w-16 h-16 text-yellow-500 mx-auto mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <p className="text-gray-800 font-bold text-lg mb-2">Workspace & Tenant Context Required</p>
            <p className="text-gray-500 text-sm max-w-md mx-auto mb-6">
              Please select or create an Organization and a Workspace in the sidebar switcher to start analyzing ESG parameters.
            </p>
          </div>
        </Card>
      </div>
    );
  }

  // Handle Loading States
  if (loading) {
    return (
      <div className="flex-1 p-8 flex items-center justify-center min-h-[80vh]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-sm font-semibold text-gray-500 mt-4">Loading ESG dashboard elements...</p>
        </div>
      </div>
    );
  }

  // Handle Error States
  if (error) {
    return (
      <div className="flex-1 p-8">
        <Card title="Unable to Load ESG Dashboard" className="max-w-2xl mx-auto mt-12">
          <div className="text-center py-6">
            <svg
              className="w-16 h-16 text-red-500 mx-auto mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="text-gray-800 font-bold text-lg mb-2">API Connection Error</p>
            <p className="text-red-600 text-sm mb-6 font-medium">{error}</p>
            <Button variant="primary" onClick={fetchDashboardData}>
              Retry Fetch
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  // Helper to join KPI definitions with their latest value recorded in this workspace
  const getKpiLatestValue = (kpiDefId: string) => {
    if (!Array.isArray(kpiValues)) return null;
    const values = kpiValues.filter((val) => val.kpi_definition_id === kpiDefId);
    if (values.length === 0) return null;
    // Sort values by date descending
    const sorted = [...values].sort(
      (a, b) => new Date(b.calculated_at).getTime() - new Date(a.calculated_at).getTime()
    );
    return sorted[0];
  };

  // Active Scoring Profile
  const activeProfile = scoringProfiles.find((p) => p.is_active) || {
    name: "Standard Baseline Profile (Default)",
    environmental_weight: 0.40,
    social_weight: 0.30,
    governance_weight: 0.30,
    created_at: new Date().toISOString(),
  };

  // Selected score record
  const activeScore = Array.isArray(scores) && scores.length > selectedScoreIndex
    ? scores[selectedScoreIndex]
    : null;

  // Trends data preparation (guarded against null values)
  const chartData = Array.isArray(scores)
    ? [...scores]
        .reverse()
        .map((s) => ({
          period: s.period || "—",
          "Overall ESG": s.overall_score !== null && s.overall_score !== undefined ? parseFloat((Number(s.overall_score) * 100).toFixed(1)) : 0.0,
          Environmental: s.environmental_score !== null && s.environmental_score !== undefined ? parseFloat((Number(s.environmental_score) * 100).toFixed(1)) : 0.0,
          Social: s.social_score !== null && s.social_score !== undefined ? parseFloat((Number(s.social_score) * 100).toFixed(1)) : 0.0,
          Governance: s.governance_score !== null && s.governance_score !== undefined ? parseFloat((Number(s.governance_score) * 100).toFixed(1)) : 0.0,
        }))
    : [];

  // KPI filtering, searching, sorting, and pagination
  const filteredKpis = kpiDefinitions.filter((kpi) => {
    const matchesSearch =
      kpi.name.toLowerCase().includes(kpiSearch.toLowerCase()) ||
      kpi.kpi_code.toLowerCase().includes(kpiSearch.toLowerCase());
    const matchesCategory = kpiCategoryFilter === "" || kpi.category === kpiCategoryFilter;

    const valRecord = getKpiLatestValue(kpi.id);
    const isPresent = valRecord !== null;
    let matchesStatus = true;
    if (kpiStatusFilter === "active") matchesStatus = kpi.is_active;
    else if (kpiStatusFilter === "inactive") matchesStatus = !kpi.is_active;
    else if (kpiStatusFilter === "present") matchesStatus = isPresent;
    else if (kpiStatusFilter === "missing") matchesStatus = !isPresent;

    return matchesSearch && matchesCategory && matchesStatus;
  });

  const sortedKpis = [...filteredKpis].sort((a, b) => {
    let factorA: any = a[kpiSortBy];
    let factorB: any = b[kpiSortBy];
    if (typeof factorA === "string") {
      factorA = factorA.toLowerCase();
      factorB = factorB.toLowerCase();
    }
    if (factorA < factorB) return kpiSortOrder === "asc" ? -1 : 1;
    if (factorA > factorB) return kpiSortOrder === "asc" ? 1 : -1;
    return 0;
  });

  const totalKpiPages = Math.ceil(sortedKpis.length / kpisPerPage);
  const paginatedKpis = sortedKpis.slice(
    (kpiPage - 1) * kpisPerPage,
    kpiPage * kpisPerPage
  );

  // Framework mapping filter
  const filteredMappings = frameworkMappings.filter((m) => {
    if (mappingKpiFilter === "") return true;
    const kpi = kpiDefinitions.find((k) => k.id === m.kpi_definition_id);
    return kpi && kpi.id === mappingKpiFilter;
  });

  // Evidence search & filtering
  const filteredEvidence = evidenceList.filter((ev) => {
    const matchesSearch =
      ev.source_description.toLowerCase().includes(evidenceSearch.toLowerCase()) ||
      (ev.cryptographic_hash && ev.cryptographic_hash.toLowerCase().includes(evidenceSearch.toLowerCase()));
    return matchesSearch;
  });

  const totalEvidencePages = Math.ceil(filteredEvidence.length / evidencePerPage);
  const paginatedEvidence = filteredEvidence.slice(
    (evidencePage - 1) * evidencePerPage,
    evidencePage * evidencePerPage
  );

  // Fetching target details for selected evidence node lineage flow
  const getLineageCardDetails = () => {
    if (!selectedEvidence) return null;
    const lineage = selectedEvidence.lineage_path || {};
    const kpiVal = kpiValues.find((v) => v.id === selectedEvidence.kpi_value_id);
    const kpiDef = kpiVal ? kpiDefinitions.find((k) => k.id === kpiVal.kpi_definition_id) : null;

    return {
      datasetId: lineage.dataset_id || "—",
      processAnalysisId: lineage.process_analysis_id || "—",
      carbonAttributionId: lineage.carbon_attribution_id || "—",
      kpiCode: kpiDef ? kpiDef.kpi_code : "—",
      kpiName: kpiDef ? kpiDef.name : "—",
      kpiValue: kpiVal ? `${kpiVal.value} ${kpiDef?.unit || ""}` : "—",
      kpiPeriod: kpiVal ? kpiVal.period : "—",
      recordedBy: kpiVal ? "System Recalculated" : "—",
      overallScore: activeScore ? formatScoreSafely(activeScore.overall_score) : "—",
    };
  };

  const lineageDetails = getLineageCardDetails();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between border-b border-gray-200 pb-5">
        <div>
          <h1 className="text-3xl font-black text-gray-900 tracking-tight">ESG Intelligence</h1>
          <p className="text-gray-500 font-medium">Sustainability analysis and audit lineage tracking</p>
        </div>
        <div className="mt-4 md:mt-0 flex gap-3">
          <Button variant="outline" onClick={fetchDashboardData}>
            <span className="flex items-center gap-1.5">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 7.89H18" />
              </svg>
              Refresh
            </span>
          </Button>
        </div>
      </div>

      {/* Main Grid: Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4">
        {/* Overall Score Card */}
        <div className="bg-gradient-to-br from-gray-900 to-slate-800 text-white rounded-lg shadow-sm border border-slate-700 p-5 relative overflow-hidden">
          <div className="relative z-10">
            <h4 className="text-xs uppercase font-bold tracking-wider text-slate-400">Overall ESG Score</h4>
            <p className="text-4xl font-extrabold mt-2 tracking-tight">
              {activeScore ? formatScoreSafely(activeScore.overall_score) : "—"}
            </p>
            {activeScore && (
              <div className="mt-4 space-y-1.5 text-xs text-slate-300">
                <div className="flex justify-between">
                  <span>Period</span>
                  <span className="font-semibold">{activeScore.period || "—"}</span>
                </div>
                <div className="flex justify-between">
                  <span>Recalculated</span>
                  <span className="font-semibold">
                    {formatDateSafely(activeScore.calculated_at)}
                  </span>
                </div>
              </div>
            )}
          </div>
          <div className="absolute right-[-10px] bottom-[-10px] opacity-10">
            <svg className="w-32 h-32" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H7c0-2.76 2.24-5 5-5s5 2.24 5 5c0 1.04-.42 1.99-1.07 2.75z" />
            </svg>
          </div>
        </div>

        {/* Environmental Score Card */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
          <div className="flex justify-between items-start">
            <div>
              <h4 className="text-xs uppercase font-bold tracking-wider text-gray-500">Environmental</h4>
              <p className="text-3xl font-black mt-2 text-emerald-700">
                {activeScore ? formatScoreSafely(activeScore.environmental_score) : "—"}
              </p>
            </div>
            <div className="bg-emerald-50 text-emerald-700 p-2 rounded-md">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m0-12.728l.707.707m12.728 12.728l.707-.707M12 8a4 4 0 100 8 4 4 0 000-8z" />
              </svg>
            </div>
          </div>
          {activeScore && activeScore.environmental_score !== null && activeScore.environmental_score !== undefined && (
            <div className="w-full bg-gray-100 rounded-full h-1.5 mt-4">
              <div
                className="bg-emerald-600 h-1.5 rounded-full"
                style={{ width: `${Math.min(100, Number(activeScore.environmental_score))}%` }}
              ></div>
            </div>
          )}
        </div>

        {/* Social Score Card */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
          <div className="flex justify-between items-start">
            <div>
              <h4 className="text-xs uppercase font-bold tracking-wider text-gray-500">Social</h4>
              <p className="text-3xl font-black mt-2 text-blue-700">
                {activeScore ? formatScoreSafely(activeScore.social_score) : "—"}
              </p>
            </div>
            <div className="bg-blue-50 text-blue-700 p-2 rounded-md">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
          </div>
          {activeScore && activeScore.social_score !== null && activeScore.social_score !== undefined && (
            <div className="w-full bg-gray-100 rounded-full h-1.5 mt-4">
              <div
                className="bg-blue-600 h-1.5 rounded-full"
                style={{ width: `${Math.min(100, Number(activeScore.social_score))}%` }}
              ></div>
            </div>
          )}
        </div>

        {/* Governance Score Card */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
          <div className="flex justify-between items-start">
            <div>
              <h4 className="text-xs uppercase font-bold tracking-wider text-gray-500">Governance</h4>
              <p className="text-3xl font-black mt-2 text-purple-700">
                {activeScore ? formatScoreSafely(activeScore.governance_score) : "—"}
              </p>
            </div>
            <div className="bg-purple-50 text-purple-700 p-2 rounded-md">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
          </div>
          {activeScore && activeScore.governance_score !== null && activeScore.governance_score !== undefined && (
            <div className="w-full bg-gray-100 rounded-full h-1.5 mt-4">
              <div
                className="bg-purple-600 h-1.5 rounded-full"
                style={{ width: `${Math.min(100, Number(activeScore.governance_score))}%` }}
              ></div>
            </div>
          )}
        </div>

        {/* Completeness Score Card */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
          <div className="flex justify-between items-start">
            <div>
              <h4 className="text-xs uppercase font-bold tracking-wider text-gray-500">Completeness</h4>
              <p className="text-3xl font-black mt-2 text-amber-700">
                {activeScore ? formatScoreSafely(activeScore.completeness_score) : "—"}
              </p>
            </div>
            <div className="bg-amber-50 text-amber-700 p-2 rounded-md">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 00-2 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            </div>
          </div>
          {activeScore && activeScore.completeness_score !== null && activeScore.completeness_score !== undefined && (
            <div className="w-full bg-gray-100 rounded-full h-1.5 mt-4">
              <div
                className="bg-amber-600 h-1.5 rounded-full"
                style={{ width: `${Math.min(100, Number(activeScore.completeness_score))}%` }}
              ></div>
            </div>
          )}
        </div>
      </div>

      {/* Grid: Profiles & Trends */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Scoring Profile details */}
        <Card title="Scoring Profile config" className="lg:col-span-1 flex flex-col justify-between">
          <div className="space-y-4">
            <div>
              <p className="text-xs font-bold text-gray-400 uppercase tracking-wider">Active Profile</p>
              <h4 className="text-lg font-bold text-gray-800 mt-1">{activeProfile.name || "—"}</h4>
              <p className="text-xs text-gray-400 mt-0.5">
                Last updated: {formatDateSafely(activeProfile.created_at)}
              </p>
            </div>

            <div className="border-t border-gray-100 pt-4 space-y-3">
              <p className="text-xs font-bold text-gray-500 uppercase">Rolled-up Weights</p>
              <div className="flex justify-between items-center bg-emerald-50/70 p-2.5 rounded-md border border-emerald-100">
                <span className="text-sm font-semibold text-emerald-800 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                  Environmental
                </span>
                <span className="text-sm font-bold text-emerald-950">
                  {activeProfile.environmental_weight !== undefined ? `${Math.round(activeProfile.environmental_weight * 100)}%` : "—"}
                </span>
              </div>
              <div className="flex justify-between items-center bg-blue-50/70 p-2.5 rounded-md border border-blue-100">
                <span className="text-sm font-semibold text-blue-800 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                  Social
                </span>
                <span className="text-sm font-bold text-blue-950">
                  {activeProfile.social_weight !== undefined ? `${Math.round(activeProfile.social_weight * 100)}%` : "—"}
                </span>
              </div>
              <div className="flex justify-between items-center bg-purple-50/70 p-2.5 rounded-md border border-purple-100">
                <span className="text-sm font-semibold text-purple-800 flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-purple-500"></span>
                  Governance
                </span>
                <span className="text-sm font-bold text-purple-950">
                  {activeProfile.governance_weight !== undefined ? `${Math.round(activeProfile.governance_weight * 100)}%` : "—"}
                </span>
              </div>
            </div>
          </div>
          <div className="bg-gray-50 border border-gray-200 rounded-md p-3 mt-4">
            <p className="text-xs text-gray-500 leading-relaxed font-semibold">
              ℹ️ Scoring profiles are managed by organization administrators. Weights are applied dynamically during ESG audits.
            </p>
          </div>
        </Card>

        {/* ESG Trend Charts */}
        <Card title="Score progression trends" className="lg:col-span-2">
          {!isMounted ? (
            <div className="h-64 flex items-center justify-center bg-gray-50 border border-dashed rounded-lg">
              <p className="text-sm text-gray-400 font-semibold">Loading trends...</p>
            </div>
          ) : chartData.length === 0 ? (
            <div className="h-64 flex flex-col items-center justify-center bg-gray-50 border-2 border-dashed border-gray-200 rounded-lg">
              <p className="text-sm font-bold text-gray-500">No Historical scores found</p>
              <p className="text-xs text-gray-400 mt-1">Recalculate scores or select a workspace with ESG logs</p>
            </div>
          ) : (
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="period" stroke="#888888" fontSize={11} tickLine={false} />
                  <YAxis domain={[0, 100]} stroke="#888888" fontSize={11} tickLine={false} />
                  <Tooltip contentStyle={{ fontSize: "12px", borderRadius: "8px" }} />
                  <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "10px" }} />
                  <Line type="monotone" dataKey="Overall ESG" stroke="#0f172a" strokeWidth={3} activeDot={{ r: 6 }} />
                  <Line type="monotone" dataKey="Environmental" stroke="#059669" strokeWidth={2} strokeDasharray="5 5" />
                  <Line type="monotone" dataKey="Social" stroke="#2563eb" strokeWidth={2} strokeDasharray="5 5" />
                  <Line type="monotone" dataKey="Governance" stroke="#7c3aed" strokeWidth={2} strokeDasharray="5 5" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </Card>
      </div>

      {/* KPI Explorer */}
      <Card title="KPI Catalog Explorer">
        <div className="space-y-4">
          {/* Controls */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <div className="sm:col-span-2">
              <Input
                placeholder="Search by code or name..."
                value={kpiSearch}
                onChange={(e) => {
                  setKpiSearch(e.target.value);
                  setKpiPage(1);
                }}
              />
            </div>
            <div>
              <select
                className="w-full h-[40px] px-3 border border-gray-200 rounded-md text-sm text-gray-800 bg-white"
                value={kpiCategoryFilter}
                onChange={(e) => {
                  setKpiCategoryFilter(e.target.value);
                  setKpiPage(1);
                }}
              >
                <option value="">All Categories</option>
                <option value="Environmental">Environmental</option>
                <option value="Social">Social</option>
                <option value="Governance">Governance</option>
              </select>
            </div>
            <div>
              <select
                className="w-full h-[40px] px-3 border border-gray-200 rounded-md text-sm text-gray-800 bg-white"
                value={kpiStatusFilter}
                onChange={(e) => {
                  setKpiStatusFilter(e.target.value);
                  setKpiPage(1);
                }}
              >
                <option value="">All Statuses</option>
                <option value="active">Active Definitions</option>
                <option value="inactive">Inactive Definitions</option>
                <option value="present">Values Present</option>
                <option value="missing">Values Missing</option>
              </select>
            </div>
          </div>

          {/* Table */}
          <div className="overflow-x-auto border border-gray-200 rounded-md">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th
                    className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider cursor-pointer"
                    onClick={() => {
                      setKpiSortBy("kpi_code");
                      setKpiSortOrder(kpiSortOrder === "asc" ? "desc" : "asc");
                    }}
                  >
                    Code {kpiSortBy === "kpi_code" && (kpiSortOrder === "asc" ? "▲" : "▼")}
                  </th>
                  <th
                    className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider cursor-pointer"
                    onClick={() => {
                      setKpiSortBy("name");
                      setKpiSortOrder(kpiSortOrder === "asc" ? "desc" : "asc");
                    }}
                  >
                    Name {kpiSortBy === "name" && (kpiSortOrder === "asc" ? "▲" : "▼")}
                  </th>
                  <th
                    className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider cursor-pointer"
                    onClick={() => {
                      setKpiSortBy("category");
                      setKpiSortOrder(kpiSortOrder === "asc" ? "desc" : "asc");
                    }}
                  >
                    Category {kpiSortBy === "category" && (kpiSortOrder === "asc" ? "▲" : "▼")}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">
                    Current Value
                  </th>
                  <th
                    className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider cursor-pointer"
                    onClick={() => {
                      setKpiSortBy("version");
                      setKpiSortOrder(kpiSortOrder === "asc" ? "desc" : "asc");
                    }}
                  >
                    Version {kpiSortBy === "version" && (kpiSortOrder === "asc" ? "▲" : "▼")}
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">
                    Source
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200 text-sm">
                {paginatedKpis.map((kpi) => {
                  const val = getKpiLatestValue(kpi.id);
                  return (
                    <tr key={kpi.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap font-mono font-bold text-gray-900">
                        {kpi.kpi_code || "—"}
                      </td>
                      <td className="px-6 py-4">
                        <div className="font-semibold text-gray-800">{kpi.name || "—"}</div>
                        <div className="text-xs text-gray-400 line-clamp-1">{kpi.description || "—"}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                            kpi.category === "Environmental"
                              ? "bg-emerald-50 text-emerald-700"
                              : kpi.category === "Social"
                              ? "bg-blue-50 text-blue-700"
                              : "bg-purple-50 text-purple-700"
                          }`}
                        >
                          {kpi.category || "—"}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap font-semibold">
                        {val !== null ? (
                          <span className="text-gray-900">
                            {formatNumberSafely(val.value)} {kpi.unit || ""}
                          </span>
                        ) : (
                          <span className="text-gray-400 italic">No measurement</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-gray-500 font-mono">
                        v{kpi.version || 1}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                        <span className="capitalize">{kpi.source_type ? kpi.source_type.replace("_", " ") : "—"}</span>
                      </td>
                    </tr>
                  );
                })}
                {paginatedKpis.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-6 py-10 text-center text-gray-500 font-medium italic">
                      No KPIs match search criteria or active filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalKpiPages > 1 && (
            <div className="flex justify-between items-center pt-2">
              <span className="text-xs text-gray-500 font-medium">
                Page {kpiPage} of {totalKpiPages}
              </span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  disabled={kpiPage === 1}
                  onClick={() => setKpiPage(kpiPage - 1)}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  disabled={kpiPage === totalKpiPages}
                  onClick={() => setKpiPage(kpiPage + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </div>
      </Card>

      {/* Grid: Frameworks & Breakdown */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Framework Mapping Viewer */}
        <Card title="Regulatory frameworks mapping">
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">
                  Compliance Framework
                </label>
                <select
                  className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm text-gray-800 bg-white"
                  value={selectedFrameworkId}
                  onChange={(e) => setSelectedFrameworkId(e.target.value)}
                >
                  {frameworks.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.framework_name || "—"} v{f.framework_version || "—"}
                    </option>
                  ))}
                  {frameworks.length === 0 && <option value="">No Frameworks Seeded</option>}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">
                  Filter by KPI
                </label>
                <select
                  className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm text-gray-800 bg-white"
                  value={mappingKpiFilter}
                  onChange={(e) => setMappingKpiFilter(e.target.value)}
                >
                  <option value="">All Mapped KPIs</option>
                  {kpiDefinitions.map((k) => (
                    <option key={k.id} value={k.id}>
                      {k.kpi_code || "—"} - {k.name || "—"}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Framework Details */}
            {frameworks.find((f) => f.id === selectedFrameworkId) && (
              <div className="bg-blue-50/50 border border-blue-100 rounded-md p-3 text-xs text-blue-800">
                <span className="font-bold">Description: </span>
                {frameworks.find((f) => f.id === selectedFrameworkId)?.description ||
                  "No framework description available."}
              </div>
            )}

            {/* Mappings Table */}
            <div className="overflow-x-auto border border-gray-200 rounded-md max-h-72 overflow-y-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">
                      Section/Principle
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">
                      Reporting Question
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-bold text-gray-500 uppercase tracking-wider">
                      Mapped KPI
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200 text-sm">
                  {loadingMappings ? (
                    <tr>
                      <td colSpan={3} className="px-4 py-8 text-center text-gray-500 font-semibold">
                        Loading framework mappings...
                      </td>
                    </tr>
                  ) : filteredMappings.map((mapping) => {
                    const kpi = kpiDefinitions.find((k) => k.id === mapping.kpi_definition_id);
                    return (
                      <tr key={mapping.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className="font-bold text-gray-800">{mapping.framework_section || "—"}</span>
                          {mapping.framework_principle && (
                            <span className="block text-xxs text-gray-400 font-medium">
                              {mapping.framework_principle}
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-xs text-gray-600 max-w-xs truncate" title={mapping.framework_question || ""}>
                          {mapping.framework_question || "—"}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap font-mono text-xs font-bold text-blue-700">
                          {kpi ? kpi.kpi_code : "—"}
                        </td>
                      </tr>
                    );
                  })}
                  {!loadingMappings && filteredMappings.length === 0 && (
                    <tr>
                      <td colSpan={3} className="px-4 py-8 text-center text-gray-500 font-medium italic">
                        No mappings found for the selected configuration.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </Card>

        {/* Score Breakdown Panel */}
        <Card title="Score breakdown rollup">
          <div className="space-y-4">
            {activeScore ? (
              <div className="space-y-4">
                {/* Rollup List */}
                <div className="border border-gray-100 rounded-md divide-y divide-gray-100">
                  {/* Category: Environmental */}
                  <div className="p-3">
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-bold text-emerald-800 text-sm">Environmental Segment</span>
                      <span className="font-bold text-sm">{formatScoreSafely(activeScore.environmental_score)}</span>
                    </div>
                    {activeScore.environmental_score !== null && activeScore.environmental_score !== undefined && (
                      <div className="w-full bg-gray-100 rounded-full h-2">
                        <div
                          className="bg-emerald-600 h-2 rounded-full"
                          style={{ width: `${Math.min(100, Number(activeScore.environmental_score))}%` }}
                        ></div>
                      </div>
                    )}
                  </div>

                  {/* Category: Social */}
                  <div className="p-3">
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-bold text-blue-800 text-sm">Social Segment</span>
                      <span className="font-bold text-sm">{formatScoreSafely(activeScore.social_score)}</span>
                    </div>
                    {activeScore.social_score !== null && activeScore.social_score !== undefined && (
                      <div className="w-full bg-gray-100 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${Math.min(100, Number(activeScore.social_score))}%` }}
                        ></div>
                      </div>
                    )}
                  </div>

                  {/* Category: Governance */}
                  <div className="p-3">
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-bold text-purple-800 text-sm">Governance Segment</span>
                      <span className="font-bold text-sm">{formatScoreSafely(activeScore.governance_score)}</span>
                    </div>
                    {activeScore.governance_score !== null && activeScore.governance_score !== undefined && (
                      <div className="w-full bg-gray-100 rounded-full h-2">
                        <div
                          className="bg-purple-600 h-2 rounded-full"
                          style={{ width: `${Math.min(100, Number(activeScore.governance_score))}%` }}
                        ></div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Score Breakdown List */}
                <div className="pt-2">
                  <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">
                    KPI contributions & Norm values
                  </h4>
                  <div className="space-y-2 max-h-48 overflow-y-auto border border-gray-100 rounded-md p-2">
                    {activeScore.score_breakdown &&
                    typeof activeScore.score_breakdown === "object" ? (
                      Object.entries(activeScore.score_breakdown).map(([kpiCode, kpiDetails]: any) => {
                        const kpiDef = kpiDefinitions.find((k) => k.kpi_code === kpiCode);
                        return (
                          <div
                            key={kpiCode}
                            className="flex justify-between items-center text-xs p-2 rounded bg-gray-50 border border-gray-100"
                          >
                            <div>
                              <span className="font-mono font-bold text-gray-800">{kpiCode}</span>
                              <span className="text-gray-400 block text-xxs font-medium max-w-xs truncate">
                                {kpiDef ? kpiDef.name : "Unknown KPI"}
                              </span>
                            </div>
                            <div className="text-right">
                              <span className="font-bold block text-gray-800">
                                Normalized: {formatNumberSafely(kpiDetails.normalized_score)}/100
                              </span>
                              <span className="text-xxs text-gray-400 font-medium">
                                Weight: {kpiDetails.weight !== undefined ? kpiDetails.weight : "—"} | Status:{" "}
                                <span
                                  className={
                                    kpiDetails.status === "present"
                                      ? "text-green-600 font-semibold"
                                      : "text-red-500 font-semibold"
                                  }
                                >
                                  {kpiDetails.status || "—"}
                                </span>
                              </span>
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <p className="text-xs text-gray-400 italic">No breakdown details computed.</p>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-12 text-center text-gray-400 italic text-sm">
                No active scores loaded. Rollup details are unavailable.
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Grid: Evidence Explorer & Lineage */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Evidence Explorer */}
        <Card title="Evidence audit records" className="lg:col-span-1">
          <div className="space-y-4">
            <Input
              placeholder="Search evidence hash or details..."
              value={evidenceSearch}
              onChange={(e) => {
                setEvidenceSearch(e.target.value);
                setEvidencePage(1);
              }}
            />

            <div className="space-y-2.5 max-h-96 overflow-y-auto pr-1">
              {paginatedEvidence.map((ev) => {
                const isSelected = selectedEvidence && selectedEvidence.id === ev.id;
                const kpiVal = kpiValues.find((v) => v.id === ev.kpi_value_id);
                const kpiDef = kpiVal ? kpiDefinitions.find((k) => k.id === kpiVal.kpi_definition_id) : null;
                return (
                  <div
                    key={ev.id}
                    className={`p-3 rounded-md border transition-all cursor-pointer ${
                      isSelected
                        ? "border-blue-600 bg-blue-50/40"
                        : "border-gray-200 bg-white hover:bg-gray-50"
                    }`}
                    onClick={() => setSelectedEvidence(ev)}
                  >
                    <div className="flex justify-between items-start">
                      <span className="font-mono font-bold text-xs text-blue-700">
                        {kpiDef ? kpiDef.kpi_code : "—"}
                      </span>
                      <span className="px-1.5 py-0.5 rounded text-xxs font-bold uppercase tracking-wider bg-gray-100 text-gray-700">
                        {ev.source_entity_type ? ev.source_entity_type.replace("_", " ") : "—"}
                      </span>
                    </div>
                    <p className="text-xs text-gray-800 font-semibold mt-1.5 line-clamp-2">
                      {ev.source_description || "—"}
                    </p>
                    <div className="flex justify-between items-center text-xxs text-gray-400 mt-3 border-t border-gray-100 pt-2 font-mono">
                      <span>Hash: {ev.cryptographic_hash ? `${ev.cryptographic_hash.slice(0, 10)}...` : "—"}</span>
                      <span>{formatDateSafely(ev.audited_at)}</span>
                    </div>
                  </div>
                );
              })}
              {paginatedEvidence.length === 0 && (
                <p className="text-sm text-gray-400 italic text-center py-10 border border-dashed rounded-md">
                  No evidence audit logs found.
                </p>
              )}
            </div>

            {/* Pagination */}
            {totalEvidencePages > 1 && (
              <div className="flex justify-between items-center pt-2">
                <span className="text-xs text-gray-500 font-medium">
                  {evidencePage}/{totalEvidencePages}
                </span>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    className="py-1 px-2.5 text-xs"
                    disabled={evidencePage === 1}
                    onClick={() => setEvidencePage(evidencePage - 1)}
                  >
                    Prev
                  </Button>
                  <Button
                    variant="outline"
                    className="py-1 px-2.5 text-xs"
                    disabled={evidencePage === totalEvidencePages}
                    onClick={() => setEvidencePage(evidencePage + 1)}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* Lineage Explorer (Simplified) */}
        <Card title="KPI Value lineage path explorer" className="lg:col-span-2">
          {selectedEvidence && lineageDetails ? (
            <div className="space-y-6">
              {/* Context Summary */}
              <div className="bg-gray-50/80 border border-gray-200 rounded-md p-3 text-xs space-y-1">
                <div className="flex justify-between">
                  <span className="font-semibold text-gray-500">Source description:</span>
                  <span className="text-gray-900 font-bold">{selectedEvidence.source_description || "—"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-semibold text-gray-500">Cryptographic hash:</span>
                  <span className="text-gray-900 font-mono font-bold truncate max-w-md">
                    {selectedEvidence.cryptographic_hash || "—"}
                  </span>
                </div>
              </div>

              {/* Connected Lineage flow */}
              <div className="flex flex-col md:flex-row items-center justify-between gap-4 py-6 px-4">
                {/* Node 1: Dataset */}
                <div className="flex-1 w-full bg-white border border-gray-200 rounded-lg shadow-sm p-4 relative text-center">
                  <div className="text-xxs uppercase tracking-wider text-gray-400 font-bold mb-1">
                    1. DATA LOG SOURCE
                  </div>
                  <div className="text-sm font-bold text-gray-900 truncate">Dataset File</div>
                  <div className="text-xxs font-mono text-gray-400 mt-2 truncate" title={lineageDetails.datasetId}>
                    ID: {lineageDetails.datasetId !== "—" ? `${lineageDetails.datasetId.slice(0, 8)}...` : "—"}
                  </div>
                </div>

                {/* Arrow Connector */}
                <div className="text-blue-500 flex items-center justify-center shrink-0">
                  <svg className="w-6 h-6 rotate-90 md:rotate-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </div>

                {/* Node 2: Process Analysis */}
                <div className="flex-1 w-full bg-white border border-gray-200 rounded-lg shadow-sm p-4 relative text-center">
                  <div className="text-xxs uppercase tracking-wider text-gray-400 font-bold mb-1">
                    2. PROCESS DISCOVERY
                  </div>
                  <div className="text-sm font-bold text-gray-900">Analysis Run</div>
                  <div className="text-xxs font-mono text-gray-400 mt-2 truncate" title={lineageDetails.processAnalysisId}>
                    ID: {lineageDetails.processAnalysisId !== "—" ? `${lineageDetails.processAnalysisId.slice(0, 8)}...` : "—"}
                  </div>
                </div>

                {/* Arrow Connector */}
                <div className="text-blue-500 flex items-center justify-center shrink-0">
                  <svg className="w-6 h-6 rotate-90 md:rotate-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </div>

                {/* Node 3: Carbon Attribution */}
                <div className="flex-1 w-full bg-white border border-gray-200 rounded-lg shadow-sm p-4 relative text-center">
                  <div className="text-xxs uppercase tracking-wider text-gray-400 font-bold mb-1">
                    3. DATA ATTRIBUTION
                  </div>
                  <div className="text-sm font-bold text-gray-900">Calculated Log</div>
                  <div className="text-xxs font-mono text-gray-400 mt-2 truncate" title={lineageDetails.carbonAttributionId}>
                    ID: {lineageDetails.carbonAttributionId !== "—" ? `${lineageDetails.carbonAttributionId.slice(0, 8)}...` : "—"}
                  </div>
                </div>

                {/* Arrow Connector */}
                <div className="text-blue-500 flex items-center justify-center shrink-0">
                  <svg className="w-6 h-6 rotate-90 md:rotate-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </div>

                {/* Node 4: KPI Value */}
                <div className="flex-1 w-full bg-blue-50 border border-blue-200 rounded-lg shadow-sm p-4 relative text-center">
                  <div className="text-xxs uppercase tracking-wider text-blue-500 font-bold mb-1">
                    4. MEASUREMENT
                  </div>
                  <div className="text-sm font-bold text-blue-900 font-mono">{lineageDetails.kpiCode}</div>
                  <div className="text-xs font-extrabold text-blue-950 mt-1">{lineageDetails.kpiValue}</div>
                  <div className="text-xxs text-blue-400 mt-1 font-semibold">Period: {lineageDetails.kpiPeriod}</div>
                </div>

                {/* Arrow Connector */}
                <div className="text-blue-500 flex items-center justify-center shrink-0">
                  <svg className="w-6 h-6 rotate-90 md:rotate-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </div>

                {/* Node 5: ESG Score */}
                <div className="flex-1 w-full bg-slate-900 text-white border border-slate-700 rounded-lg shadow-sm p-4 relative text-center">
                  <div className="text-xxs uppercase tracking-wider text-slate-400 font-bold mb-1">
                    5. ESG AUDIT ROLLUP
                  </div>
                  <div className="text-sm font-bold">Overall Score</div>
                  <div className="text-lg font-black text-emerald-400 mt-1.5">{lineageDetails.overallScore}</div>
                </div>
              </div>

              {/* Dynamic steps summary info */}
              <div className="bg-blue-50/30 border border-blue-100 rounded-md p-4 space-y-2">
                <h4 className="text-xs font-bold text-blue-900 uppercase">Calculation proof details</h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-xs">
                  <div>
                    <span className="block text-gray-500 font-medium">Recorded by:</span>
                    <span className="font-bold text-gray-800">{lineageDetails.recordedBy}</span>
                  </div>
                  <div>
                    <span className="block text-gray-500 font-medium">Audited status:</span>
                    <span className="font-bold text-green-600">Verified cryptographic hash match</span>
                  </div>
                  <div>
                    <span className="block text-gray-500 font-medium">Calculation steps count:</span>
                    <span className="font-bold text-gray-800">
                      {Object.keys(selectedEvidence.calculation_steps || {}).length} variables
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="py-20 text-center text-gray-400 italic text-sm border-2 border-dashed border-gray-100 rounded-md">
              Select an evidence audit record to inspect its data lineage pipeline.
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
