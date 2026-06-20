"use client";

import React, { useState, useRef, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { useCopilot } from "../context/CopilotContext";
import { Button } from "./Button";
import { Card } from "./Card";

interface UploadWizardProps {
  onSuccess: () => void;
  onClose: () => void;
}

interface DatasetResponse {
  id: string;
  workspace_id: string;
  name: string;
  file_size: number;
  status: string;
  dataset_type: string;
  version: number;
  row_count: number | null;
  headers: string[] | null;
  schema_confidence: Record<string, { role: string; confidence: number }> | null;
  mappings: Record<string, string> | null;
  validation_errors: Array<{ row: number; error: string }> | null;
}

export const UploadWizard: React.FC<UploadWizardProps> = ({ onSuccess, onClose }) => {
  const { token, activeWorkspace, projects } = useAuth();
  const { fetchAnalyses, setSelectedProjectId, setSelectedAnalysisId } = useCopilot();
  const [currentStep, setCurrentStep] = useState(1);
  
  // State for upload
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dataset, setDataset] = useState<DatasetResponse | null>(null);
  const [uploadError, setUploadError] = useState("");

  // State for preview
  const [previewData, setPreviewData] = useState<{
    headers: string[];
    preview: string[][];
    mappings: Record<string, string>;
    validation_errors: Array<{ row: number; error: string }>;
  } | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [previewError, setPreviewError] = useState("");

  // State for mapping
  const [mappings, setMappings] = useState<Record<string, string>>({});
  const [mappingError, setMappingError] = useState("");

  // State for confirmation & project selection
  const [selectedProjectIdLocal, setSelectedProjectIdLocal] = useState<string>("");
  const [savingMapping, setSavingMapping] = useState(false);
  const [confirmError, setConfirmError] = useState("");

  // State for running analysis
  const [runningAnalysis, setRunningAnalysis] = useState(false);
  const [analysisError, setAnalysisError] = useState("");
  const [analysisProgress, setAnalysisProgress] = useState(0);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Initialize project selection once projects load
  useEffect(() => {
    if (projects && projects.length > 0 && !selectedProjectIdLocal) {
      setSelectedProjectIdLocal(projects[0].id);
    }
  }, [projects, selectedProjectIdLocal]);

  // Auto-detect and populate mappings when dataset is loaded
  useEffect(() => {
    if (dataset && dataset.headers) {
      const initialMappings: Record<string, string> = {};
      const selectRoles = [
        "case_id", "activity", "timestamp", "event_id", "supplier_id",
        "supplier_name", "supplier_country", "cost", "energy_kwh", "water_liters",
        "waste_kg", "transport_mode", "distance_km", "purchase_category", "risk_level"
      ];
      
      dataset.headers.forEach((header) => {
        if (dataset.schema_confidence && dataset.schema_confidence[header]) {
          const role = dataset.schema_confidence[header].role;
          if (selectRoles.includes(role)) {
            initialMappings[header] = role;
          } else if (role === "carbon_fields") {
            initialMappings[header] = "carbon_emissions";
          } else {
            initialMappings[header] = "ignore";
          }
        } else {
          initialMappings[header] = "ignore";
        }
      });
      setMappings(initialMappings);
    }
  }, [dataset]);

  // Run validation on mappings
  const validateMappings = (currentMappings: Record<string, string>) => {
    const values = Object.values(currentMappings);
    
    // Check if required roles are mapped
    const requiredRoles = ["case_id", "activity", "timestamp"];
    for (const role of requiredRoles) {
      if (!values.includes(role)) {
        return `Missing required mapping for: ${role.replace("_", " ").toUpperCase()}`;
      }
    }

    // Uniqueness constraints are restricted strictly to primary identifiers: case_id, activity, timestamp, resource
    const primaryRoles = ["case_id", "activity", "timestamp", "resource"];
    const mappedPrimary = values.filter((v) => primaryRoles.includes(v));
    const uniquePrimary = new Set(mappedPrimary);
    if (mappedPrimary.length !== uniquePrimary.size) {
      const duplicates = mappedPrimary.filter((item, index) => mappedPrimary.indexOf(item) !== index);
      return `Multiple columns cannot be mapped to the same primary identifier role: ${duplicates[0].replace("_", " ").toUpperCase()}`;
    }

    return "";
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      handleFileSelected(droppedFile);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
  };

  const handleFileSelected = (selectedFile: File) => {
    setUploadError("");
    if (!selectedFile.name.endsWith(".csv")) {
      setUploadError("Only CSV file format is supported.");
      return;
    }
    if (selectedFile.size > 50 * 1024 * 1024) {
      setUploadError("File size exceeds the 50MB limit.");
      return;
    }
    setFile(selectedFile);
  };

  const startUpload = async () => {
    if (!file || !activeWorkspace) return;

    setUploading(true);
    setUploadProgress(10);
    setUploadError("");

    const formData = new FormData();
    formData.append("file", file);
    formData.append("workspace_id", activeWorkspace.id);

    try {
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => (prev < 90 ? prev + 10 : prev));
      }, 200);

      const res = await fetch("http://localhost:8000/api/ingestion/upload", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Upload and validation failed.");
      }

      const data = await res.json();
      setDataset(data);
      
      const fatalErrors = data.validation_errors?.filter((e: any) => e.row === 0);
      if (fatalErrors && fatalErrors.length > 0) {
        setUploadError(`Validation failed: ${fatalErrors[0].error}`);
      } else {
        // Move to Step 2: Preview Dataset
        await loadPreview(data.id);
        setCurrentStep(2);
      }
    } catch (err: any) {
      setUploadError(err.message || "Failed to upload file.");
    } finally {
      setUploading(false);
    }
  };

  const loadPreview = async (datasetId: string) => {
    setLoadingPreview(true);
    setPreviewError("");
    try {
      const res = await fetch(`http://localhost:8000/api/ingestion/datasets/${datasetId}/preview`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to load dataset preview.");
      }
      const data = await res.json();
      setPreviewData(data);
    } catch (err: any) {
      setPreviewError(err.message || "Could not retrieve table preview.");
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleMappingChange = (header: string, role: string) => {
    const updated = { ...mappings, [header]: role };
    setMappings(updated);
    setMappingError(validateMappings(updated));
  };

  const submitMappings = async () => {
    if (!dataset) return;
    const errorMsg = validateMappings(mappings);
    if (errorMsg) {
      setMappingError(errorMsg);
      return;
    }

    setSavingMapping(true);
    setConfirmError("");

    try {
      const res = await fetch(`http://localhost:8000/api/ingestion/datasets/${dataset.id}/map`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ mappings }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to save mapping.");
      }

      const updatedDataset = await res.json();
      setDataset(updatedDataset);
      
      // Reload preview to include mappings representation
      await loadPreview(dataset.id);
      
      // Move to Step 4: Confirm Mapping
      setCurrentStep(4);
    } catch (err: any) {
      setConfirmError(err.message || "Failed to save column mappings.");
    } finally {
      setSavingMapping(false);
    }
  };

  // Run Process Discovery Analysis
  const executeAnalysis = async () => {
    if (!dataset || !activeWorkspace || !selectedProjectIdLocal) return;

    setRunningAnalysis(true);
    setCurrentStep(5);
    setAnalysisProgress(15);
    setAnalysisError("");

    try {
      const progressInterval = setInterval(() => {
        setAnalysisProgress((prev) => (prev < 90 ? prev + 15 : prev));
      }, 300);

      const res = await fetch("http://localhost:8000/api/process/discover", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          workspace_id: activeWorkspace.id,
          project_id: selectedProjectIdLocal,
          dataset_id: dataset.id,
        }),
      });

      clearInterval(progressInterval);
      setAnalysisProgress(100);

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Process discovery failed.");
      }

      const analysisResult = await res.json();

      // Update active selections in the context
      setSelectedProjectId(selectedProjectIdLocal);
      setSelectedAnalysisId(analysisResult.id);

      // Refresh analyses list
      await fetchAnalyses(activeWorkspace.id, selectedProjectIdLocal);

      // Move to Step 6: Success
      setCurrentStep(6);
    } catch (err: any) {
      setAnalysisError(err.message || "An error occurred during process discovery.");
      setRunningAnalysis(false);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto bg-white rounded-xl shadow-2xl border border-gray-100 overflow-hidden transition-all duration-300">
      {/* Wizard Header with Progress Steps */}
      <div className="bg-gradient-to-r from-emerald-950 via-slate-900 to-emerald-950 px-8 py-6 text-white border-b border-emerald-800/20">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-xl font-extrabold tracking-tight flex items-center gap-2">
              <span className="w-3 h-3 bg-emerald-500 rounded-full animate-pulse"></span>
              Sustainability Ingestion Pipeline
            </h2>
            <p className="text-emerald-300/80 text-xs mt-1">Upload, map headers, and execute carbon-aware process discovery</p>
          </div>
          <button 
            onClick={onClose}
            className="text-emerald-300 hover:text-white p-1.5 rounded-full hover:bg-white/10 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Steps Visual Progress Tracker */}
        <div className="flex items-center justify-between max-w-3xl mx-auto relative px-4 py-2">
          <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-slate-800 -translate-y-1/2 z-0" />
          <div 
            className="absolute top-1/2 left-0 h-0.5 bg-emerald-500 -translate-y-1/2 z-0 transition-all duration-500" 
            style={{ width: `${((currentStep - 1) / 5) * 100}%` }} 
          />
          
          {[
            { step: 1, label: "Upload" },
            { step: 2, label: "Preview" },
            { step: 3, label: "Map" },
            { step: 4, label: "Confirm" },
            { step: 5, label: "Analyze" },
            { step: 6, label: "Success" }
          ].map((item) => (
            <div key={item.step} className="relative z-10 flex flex-col items-center">
              <div 
                className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs transition-all duration-500 ${
                  currentStep === item.step
                    ? "bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/30 scale-110 ring-4 ring-emerald-950"
                    : currentStep > item.step
                      ? "bg-emerald-600 text-white"
                      : "bg-slate-900 text-slate-400 border border-slate-700"
                }`}
              >
                {item.step}
              </div>
              <span className={`text-[10px] font-semibold mt-2 transition-colors duration-300 ${currentStep >= item.step ? "text-emerald-400 font-bold" : "text-slate-500"}`}>
                {item.label}
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="p-8 bg-slate-50/50 min-h-[400px] flex flex-col justify-between">
        
        {/* STEP 1: UPLOAD CSV */}
        {currentStep === 1 && (
          <div className="space-y-6 flex-1 flex flex-col justify-center">
            <div className="text-center max-w-md mx-auto mb-2">
              <h3 className="text-lg font-bold text-slate-800">Select Event Log Source</h3>
              <p className="text-slate-500 text-xs mt-1">Upload a sustainability log containing Case, Activity, and Timestamp data.</p>
            </div>
            
            {!file ? (
              <div 
                onDragEnter={handleDrag}
                onDragOver={handleDrag}
                onDragLeave={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all duration-300 flex flex-col items-center justify-center min-h-[220px] ${
                  dragActive 
                    ? "border-emerald-500 bg-emerald-50/20 scale-[1.01]" 
                    : "border-slate-200 hover:border-emerald-400 bg-white"
                }`}
              >
                <input 
                  ref={fileInputRef}
                  type="file" 
                  accept=".csv"
                  onChange={handleFileInput}
                  className="hidden" 
                />
                <div className="w-14 h-14 bg-emerald-50 rounded-full flex items-center justify-center mb-4 text-emerald-600 border border-emerald-100">
                  <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
                <h3 className="font-bold text-slate-700 text-sm">Drag & Drop CSV file here</h3>
                <p className="text-slate-400 text-[11px] mt-1">Support for standard tabular CSV format (Max 50MB).</p>
                <div className="mt-4">
                  <Button type="button" className="!bg-emerald-600 hover:!bg-emerald-700 text-xs py-1.5 px-3">Browse Files</Button>
                </div>
              </div>
            ) : (
              <Card className="p-6 border border-slate-100 shadow-sm bg-white">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="w-12 h-12 bg-emerald-50 text-emerald-600 rounded-lg flex items-center justify-center border border-emerald-100">
                      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <div>
                      <h4 className="font-bold text-slate-800 text-sm truncate max-w-md">{file.name}</h4>
                      <p className="text-slate-400 text-xs">{(file.size / 1024 / 1024).toFixed(2)} MB • Ready to verify</p>
                    </div>
                  </div>
                  {!uploading && (
                    <button 
                      onClick={() => setFile(null)}
                      className="text-slate-400 hover:text-red-500 p-1.5 hover:bg-slate-50 rounded-md transition-all"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  )}
                </div>

                {uploading && (
                  <div className="mt-5 space-y-2">
                    <div className="flex justify-between text-xs text-slate-500 font-semibold">
                      <span>Uploading log file and scanning structure...</span>
                      <span>{uploadProgress}%</span>
                    </div>
                    <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full bg-emerald-600 transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
                    </div>
                  </div>
                )}

                {uploadError && (
                  <div className="bg-red-50 border border-red-200 text-red-700 text-xs p-4 rounded-lg mt-5 flex items-start gap-2.5 leading-relaxed font-medium">
                    <svg className="w-4 h-4 text-red-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <div>
                      <span className="font-bold">Scan Error:</span> {uploadError}
                    </div>
                  </div>
                )}

                {!uploading && !uploadError && (
                  <div className="flex justify-end gap-3 mt-6">
                    <Button variant="secondary" onClick={() => setFile(null)} className="text-xs">Cancel</Button>
                    <Button onClick={startUpload} className="!bg-emerald-600 hover:!bg-emerald-700 text-xs">Upload & Parse</Button>
                  </div>
                )}
              </Card>
            )}
          </div>
        )}

        {/* STEP 2: PREVIEW DATASET */}
        {currentStep === 2 && dataset && (
          <div className="space-y-6 flex-1">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-slate-800 text-base">Raw Data Preview</h3>
                <p className="text-slate-400 text-xs mt-0.5">Showing the first 10 rows from the parsed CSV structure before column mappings are defined.</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase font-bold px-2 py-0.5 bg-slate-200 text-slate-700 rounded-md">UNMAPPED</span>
              </div>
            </div>

            {previewError && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-xs p-4 rounded-lg flex items-start gap-2.5 font-medium">
                <svg className="w-4 h-4 text-red-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div>
                  <span className="font-bold">Error:</span> {previewError}
                </div>
              </div>
            )}

            {loadingPreview ? (
              <div className="py-16 text-center text-xs text-slate-500 font-semibold flex flex-col items-center gap-3">
                <div className="w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
                Loading data preview rows...
              </div>
            ) : previewData ? (
              <div className="space-y-4">
                <div className="border border-slate-100 rounded-lg overflow-hidden shadow-sm overflow-x-auto max-w-full bg-white">
                  <table className="w-full text-left border-collapse min-w-[500px]">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-100">
                        {previewData.headers.map((header) => (
                          <th key={header} className="px-4 py-2.5 text-[11px] font-bold text-slate-600 font-mono">
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-[11px] font-mono text-slate-600">
                      {previewData.preview.map((row, rowIdx) => (
                        <tr key={rowIdx} className="hover:bg-slate-50/30">
                          {previewData.headers.map((_, colIdx) => (
                            <td key={colIdx} className="px-4 py-2 max-w-[180px] truncate">
                              {row[colIdx] !== undefined ? row[colIdx] : <span className="text-slate-300">NULL</span>}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-100/50 rounded-lg p-3 border border-slate-200/50">
                    <div className="text-[10px] text-slate-400 uppercase font-bold">Log Record Count</div>
                    <div className="text-base font-bold text-slate-700 mt-0.5">{dataset.row_count} rows</div>
                  </div>
                  <div className="bg-slate-100/50 rounded-lg p-3 border border-slate-200/50">
                    <div className="text-[10px] text-slate-400 uppercase font-bold">Columns Scanned</div>
                    <div className="text-base font-bold text-slate-700 mt-0.5">{dataset.headers?.length} fields</div>
                  </div>
                </div>
              </div>
            ) : null}

            <div className="flex justify-between items-center pt-4 border-t border-slate-200/50">
              <Button variant="secondary" onClick={() => setCurrentStep(1)} className="text-xs">Back</Button>
              <Button onClick={() => setCurrentStep(3)} className="!bg-emerald-600 hover:!bg-emerald-700 text-xs">Proceed to Mapping</Button>
            </div>
          </div>
        )}

        {/* STEP 3: MAP FIELDS */}
        {currentStep === 3 && dataset && (
          <div className="space-y-6 flex-1">
            <div className="bg-emerald-50/50 border border-emerald-100 text-emerald-800 text-xs p-4 rounded-lg flex items-start gap-3">
              <svg className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <h4 className="font-bold text-emerald-950">Field Mapping Guidelines</h4>
                <p className="mt-1 leading-relaxed text-emerald-800/95">
                  Associate your CSV column headers with standard OCPM schema fields. You must map at least the **Case ID**, **Activity**, and **Timestamp** parameters to generate conformance and bottlenecks analysis.
                </p>
              </div>
            </div>

            <div className="border border-slate-100 rounded-lg overflow-hidden shadow-sm bg-white">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-100 text-[10px] uppercase font-bold text-slate-500">
                    <th className="px-6 py-3">CSV Column Name</th>
                    <th className="px-6 py-3">Confidence Match</th>
                    <th className="px-6 py-3">Target Schema Role</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs">
                  {dataset.headers?.map((header) => {
                    const detectDetail = dataset.schema_confidence?.[header];
                    const selectedRole = mappings[header] || "ignore";
                    
                    return (
                      <tr key={header} className="hover:bg-slate-50/20">
                        <td className="px-6 py-3.5 font-mono text-slate-700 font-bold">{header}</td>
                        <td className="px-6 py-3.5">
                          {detectDetail ? (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-100">
                              {detectDetail.role.replace("_", " ")} ({Math.round(detectDetail.confidence * 100)}%)
                            </span>
                          ) : (
                            <span className="text-slate-400">—</span>
                          )}
                        </td>
                        <td className="px-6 py-3.5">
                          <select 
                            value={selectedRole}
                            onChange={(e) => handleMappingChange(header, e.target.value)}
                            className="bg-white border border-slate-200 text-slate-700 text-xs rounded-md px-2 py-1 focus:ring-1 focus:ring-emerald-500 focus:border-emerald-500 outline-none w-52 font-semibold"
                          >
                            <option value="ignore">Ignore Column</option>
                            <option value="case_id">Case ID (Required)</option>
                            <option value="activity">Activity (Required)</option>
                            <option value="timestamp">Timestamp (Required)</option>
                            <option value="event_id">Event ID</option>
                            <option value="carbon_emissions">Carbon Emissions</option>
                            <option value="supplier_id">Supplier ID</option>
                            <option value="supplier_name">Supplier Name</option>
                            <option value="supplier_country">Supplier Country</option>
                            <option value="cost">Cost / Spend</option>
                            <option value="energy_kwh">Energy Consumption (kWh)</option>
                            <option value="water_liters">Water Usage (Liters)</option>
                            <option value="waste_kg">Waste Generated (kg)</option>
                            <option value="transport_mode">Transport Mode</option>
                            <option value="distance_km">Transport Distance (km)</option>
                            <option value="purchase_category">Purchase Category</option>
                            <option value="risk_level">Risk Level</option>
                            <option value="custom">Custom Attribute</option>
                          </select>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {mappingError && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-xs p-4 rounded-lg flex items-start gap-2.5 leading-relaxed font-medium">
                <svg className="w-4 h-4 text-red-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div>
                  <span className="font-bold">Mapping Validation Error:</span> {mappingError}
                </div>
              </div>
            )}

            <div className="flex justify-between items-center pt-4 border-t border-slate-200/50">
              <Button variant="secondary" onClick={() => setCurrentStep(2)} className="text-xs">Back</Button>
              <Button 
                onClick={submitMappings} 
                disabled={savingMapping || !!mappingError}
                className="!bg-emerald-600 hover:!bg-emerald-700 text-xs"
              >
                {savingMapping ? "Saving Profile..." : "Validate & Preview Mappings"}
              </Button>
            </div>
          </div>
        )}

        {/* STEP 4: CONFIRM MAPPING */}
        {currentStep === 4 && dataset && (
          <div className="space-y-6 flex-1">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-slate-800 text-base">Confirm Mappings & Select Project</h3>
                <p className="text-slate-400 text-xs mt-0.5">Verify your schema mapping profile and select target workspace project context.</p>
              </div>
            </div>

            {confirmError && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-xs p-4 rounded-lg flex items-start gap-2.5 font-medium">
                <svg className="w-4 h-4 text-red-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div>
                  <span className="font-bold">Error:</span> {confirmError}
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Mapping Summary */}
              <Card className="p-5 border border-slate-100 bg-white">
                <h4 className="font-bold text-slate-700 text-xs uppercase mb-3 tracking-wider">Mapping Profile Summary</h4>
                <div className="space-y-2.5 max-h-56 overflow-y-auto pr-2">
                  {Object.entries(mappings).map(([col, role]) => {
                    if (role === "ignore") return null;
                    return (
                      <div key={col} className="flex justify-between items-center text-xs border-b border-slate-50 pb-1.5">
                        <span className="font-mono text-slate-600 truncate max-w-[160px]" title={col}>{col}</span>
                        <span className="px-2 py-0.5 bg-emerald-50 text-emerald-800 border border-emerald-100 rounded text-[10px] font-bold">
                          {role.toUpperCase()}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </Card>

              {/* Target Project Selection */}
              <Card className="p-5 border border-slate-100 bg-white flex flex-col justify-between">
                <div className="space-y-4">
                  <h4 className="font-bold text-slate-700 text-xs uppercase tracking-wider">Target Project Context</h4>
                  
                  <div className="space-y-1.5">
                    <label className="text-[11px] font-bold text-slate-400 uppercase">Target Project</label>
                    <select
                      value={selectedProjectIdLocal}
                      onChange={(e) => setSelectedProjectIdLocal(e.target.value)}
                      className="bg-white border border-slate-200 text-slate-700 text-xs rounded-md px-3 py-2 focus:ring-1 focus:ring-emerald-500 focus:border-emerald-500 outline-none w-full font-semibold"
                    >
                      {projects && projects.length > 0 ? (
                        projects.map((proj) => (
                          <option key={proj.id} value={proj.id}>
                            {proj.name} {proj.description ? `— ${proj.description}` : ""}
                          </option>
                        ))
                      ) : (
                        <option value="">No Projects Available</option>
                      )}
                    </select>
                  </div>

                  <p className="text-[10px] text-slate-400 leading-relaxed">
                    Executing analysis will map the dataset parameters, attribute carbon footprint weights, and generate a conformance report within this project.
                  </p>
                </div>
              </Card>
            </div>

            <div className="flex justify-between items-center pt-4 border-t border-slate-200/50">
              <Button variant="secondary" onClick={() => setCurrentStep(3)} className="text-xs">Back to Mapping</Button>
              <Button onClick={executeAnalysis} className="!bg-emerald-600 hover:!bg-emerald-700 text-xs">Confirm & Run Analysis</Button>
            </div>
          </div>
        )}

        {/* STEP 5: RUN ANALYSIS */}
        {currentStep === 5 && (
          <div className="space-y-6 flex-1 flex flex-col justify-center items-center py-10">
            <div className="w-16 h-16 rounded-full bg-emerald-50 border border-emerald-100 flex items-center justify-center relative mb-4">
              <div className="absolute inset-0 rounded-full border-2 border-emerald-500 border-t-transparent animate-spin"></div>
              <svg className="w-6 h-6 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
              </svg>
            </div>

            <div className="text-center max-w-sm space-y-1.5">
              <h3 className="text-slate-800 font-bold text-sm">Process Discovery & Carbon Attribution</h3>
              <p className="text-slate-400 text-[11px] leading-relaxed">
                Discovering DFG network routes, validating conformances, and running ESG metrics calculations on event logs.
              </p>
            </div>

            <div className="w-full max-w-md space-y-2">
              <div className="flex justify-between text-[10px] text-slate-500 font-semibold uppercase tracking-wider">
                <span>Computational Progress</span>
                <span>{analysisProgress}%</span>
              </div>
              <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full bg-emerald-500 transition-all duration-500" style={{ width: `${analysisProgress}%` }} />
              </div>
            </div>

            {analysisError && (
              <div className="bg-red-50 border border-red-200 text-red-700 text-xs p-4 rounded-lg max-w-md flex items-start gap-2.5 font-medium leading-relaxed">
                <svg className="w-4 h-4 text-red-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div>
                  <span className="font-bold">Analysis Error:</span> {analysisError}
                  <div className="mt-2.5 flex justify-end">
                    <Button onClick={() => { setAnalysisError(""); setCurrentStep(4); }} className="!bg-slate-700 text-white text-[10px] py-1 px-2">Adjust Context</Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* STEP 6: SUCCESS & REDIRECT */}
        {currentStep === 6 && (
          <div className="space-y-6 flex-1 flex flex-col justify-center items-center py-10">
            <div className="w-16 h-16 rounded-full bg-emerald-50 border border-emerald-100 flex items-center justify-center mb-4 text-emerald-600 scale-110 animate-bounce">
              <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
              </svg>
            </div>

            <div className="text-center max-w-sm space-y-1.5">
              <h3 className="text-slate-800 font-extrabold text-base">Analysis Execution Completed</h3>
              <p className="text-slate-500 text-xs leading-relaxed">
                Your dataset was ingested, mapped successfully, and carbon fitness has been calculated. The dashboard is now loaded with the active analysis metrics.
              </p>
            </div>

            <div className="mt-4">
              <Button onClick={onSuccess} className="!bg-emerald-600 hover:!bg-emerald-700 text-xs px-6 py-2">
                Open Executive Dashboard
              </Button>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};
