"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "../../../context/AuthContext";
import { Card } from "../../../components/Card";
import { Input } from "../../../components/Input";
import { Button } from "../../../components/Button";
import { Modal } from "../../../components/Modal";
import { UploadWizard } from "../../../components/UploadWizard";

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
  is_archived: boolean;
  is_deleted: boolean;
  uploaded_at: string;
}

export default function ProjectsPage() {
  const {
    token,
    activeWorkspace,
    projects,
    createProject,
    archiveProject,
    deleteProject,
  } = useAuth();

  const [projectName, setProjectName] = useState("");
  const [projectDesc, setProjectDesc] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [error, setError] = useState("");

  // Ingestion & Datasets state
  const [datasets, setDatasets] = useState<DatasetResponse[]>([]);
  const [loadingDatasets, setLoadingDatasets] = useState(false);
  const [isIngestOpen, setIsIngestOpen] = useState(false);
  const [previewDatasetId, setPreviewDatasetId] = useState<string | null>(null);
  const [previewData, setPreviewData] = useState<{
    headers: string[];
    preview: string[][];
    mappings: Record<string, string>;
  } | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);

  const fetchDatasets = async () => {
    if (!activeWorkspace || !token) return;
    setLoadingDatasets(true);
    try {
      const res = await fetch(`http://localhost:8000/api/ingestion/datasets?workspace_id=${activeWorkspace.id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setDatasets(data);
      }
    } catch (err) {
      console.error("Error fetching datasets", err);
    } finally {
      setLoadingDatasets(false);
    }
  };

  useEffect(() => {
    if (activeWorkspace && token) {
      fetchDatasets();
    } else {
      setDatasets([]);
    }
  }, [activeWorkspace, token]);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!projectName) return;
    try {
      await createProject(projectName, projectDesc);
      setProjectName("");
      setProjectDesc("");
      setIsCreateOpen(false);
    } catch (err: any) {
      setError(err.message || "Failed to create project.");
    }
  };

  const handleDelete = async (projectId: string) => {
    setError("");
    if (!confirm("Are you sure you want to permanently delete this project?")) return;
    try {
      await deleteProject(projectId);
    } catch (err: any) {
      setError(err.message || "Failed to delete project. Check your RBAC roles.");
    }
  };

  const handleToggleArchive = async (projectId: string, currentStatus: boolean) => {
    setError("");
    try {
      await archiveProject(projectId, !currentStatus);
    } catch (err: any) {
      setError(err.message || "Failed to modify project status.");
    }
  };

  // Dataset Actions
  const handleArchiveDataset = async (id: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/ingestion/datasets/${id}/archive`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) fetchDatasets();
    } catch (err) {
      console.error(err);
    }
  };

  const handleRestoreDataset = async (id: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/ingestion/datasets/${id}/restore`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) fetchDatasets();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteDataset = async (id: string) => {
    if (!confirm("Are you sure you want to delete this dataset? This will archive it and preserve the auditing lineage.")) return;
    try {
      const res = await fetch(`http://localhost:8000/api/ingestion/datasets/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) fetchDatasets();
    } catch (err) {
      console.error(err);
    }
  };

  const handleShowPreview = async (id: string) => {
    setPreviewDatasetId(id);
    setLoadingPreview(true);
    try {
      const res = await fetch(`http://localhost:8000/api/ingestion/datasets/${id}/preview`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setPreviewData(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingPreview(false);
    }
  };

  return (
    <div className="space-y-10">
      {/* Projects Section */}
      <div>
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-black text-foreground tracking-tight">Projects</h1>
            <p className="text-text-muted font-medium mt-1 font-semibold">Track carbon-aware process mining pipelines inside your active workspace</p>
          </div>
          <Button onClick={() => setIsCreateOpen(true)} disabled={!activeWorkspace}>Create Project</Button>
        </div>

        {error && (
          <div className="bg-red-950/40 border border-red-900 text-red-400 text-sm p-3 rounded-md mb-4 font-semibold">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <Card key={project.id} className={project.is_archived ? "opacity-60" : ""}>
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-bold text-lg text-foreground">{project.name}</h3>
                {project.is_archived && (
                  <span className="px-2 py-0.5 bg-yellow-950/40 text-yellow-500 border border-yellow-900/40 rounded text-xs font-semibold">
                    Archived
                  </span>
                )}
              </div>
              <p className="text-sm text-text-muted mb-6 min-h-[40px]">{project.description || "No description provided."}</p>
              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  className="flex-1 py-1 text-xs"
                  onClick={() => handleToggleArchive(project.id, project.is_archived)}
                >
                  {project.is_archived ? "Restore" : "Archive"}
                </Button>
                <Button
                  variant="danger"
                  className="flex-1 py-1 text-xs"
                  onClick={() => handleDelete(project.id)}
                >
                  Delete
                </Button>
              </div>
            </Card>
          ))}

          {projects.length === 0 && (
            <div className="col-span-full border-2 border-dashed border-border-color rounded-lg p-12 text-center bg-background/40">
              <p className="text-sm font-bold text-text-muted">No active projects found in this workspace context.</p>
              <p className="text-xs text-text-muted mt-1">Create a new project to initialize your carbon-aware analysis.</p>
            </div>
          )}
        </div>
      </div>

      {/* Datasets / Ingestion Section */}
      <div className="border-t border-border-color pt-10">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-black text-foreground tracking-tight">Workspace Datasets</h2>
            <p className="text-text-muted font-medium mt-1 font-semibold">Upload and manage process logs mapped to carbon and ESG metrics</p>
          </div>
          <Button onClick={() => setIsIngestOpen(true)} disabled={!activeWorkspace} variant="primary">
            Ingest New Dataset
          </Button>
        </div>

        <Card className="p-0 overflow-hidden border border-border-color shadow-none">
          {loadingDatasets ? (
            <div className="p-8 text-center text-sm text-text-muted font-medium">Loading workspace datasets...</div>
          ) : datasets.length > 0 ? (
            <div className="overflow-x-auto w-full">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-100 border-b border-border-color text-xs text-text-muted font-bold uppercase tracking-wider">
                    <th className="px-6 py-3.5">Dataset Name</th>
                    <th className="px-6 py-3.5">Rows</th>
                    <th className="px-6 py-3.5">Size</th>
                    <th className="px-6 py-3.5">Version</th>
                    <th className="px-6 py-3.5">Uploaded</th>
                    <th className="px-6 py-3.5">Status</th>
                    <th className="px-6 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-color text-sm">
                  {datasets.map((ds) => {
                    const isArchived = ds.is_archived;
                    const dateStr = new Date(ds.uploaded_at).toLocaleDateString();
                    
                    return (
                      <tr key={ds.id} className={`hover:bg-slate-100/40 transition-colors ${isArchived ? "opacity-60 bg-slate-50" : ""}`}>
                        <td className="px-6 py-4 font-bold text-foreground">{ds.name}</td>
                        <td className="px-6 py-4 font-semibold text-foreground">{ds.row_count || "—"}</td>
                        <td className="px-6 py-4 text-foreground font-medium">{(ds.file_size / 1024).toFixed(1)} KB</td>
                        <td className="px-6 py-4 font-mono text-xs text-text-muted">v{ds.version}</td>
                        <td className="px-6 py-4 text-text-muted text-xs">{dateStr}</td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${
                            ds.status === "ready" 
                              ? "bg-green-950/40 text-green-400 border border-green-900/50"
                              : ds.status === "mapping_required"
                                ? "bg-yellow-950/40 text-yellow-500 border border-yellow-900/50"
                                : "bg-red-950/40 text-red-400 border border-red-900/50"
                          }`}>
                            {ds.status.replace("_", " ")}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right space-x-2">
                          <Button 
                            variant="secondary" 
                            className="py-1 px-2.5 text-xs font-bold"
                            onClick={() => handleShowPreview(ds.id)}
                          >
                            Preview
                          </Button>
                          <Button 
                            variant="secondary" 
                            className="py-1 px-2.5 text-xs font-bold"
                            onClick={() => isArchived ? handleRestoreDataset(ds.id) : handleArchiveDataset(ds.id)}
                          >
                            {isArchived ? "Restore" : "Archive"}
                          </Button>
                          <Button 
                            variant="danger" 
                            className="py-1 px-2.5 text-xs font-bold"
                            onClick={() => handleDeleteDataset(ds.id)}
                          >
                            Delete
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="border-2 border-dashed border-border-color rounded-lg p-12 text-center bg-background/40">
              <p className="text-sm font-bold text-text-muted">No active process datasets found in this workspace context.</p>
              <p className="text-xs text-text-muted mt-1">Ingest your CSV log files to map business activities, supplier IDs, and carbon fields.</p>
            </div>
          )}
        </Card>
      </div>

      {/* Create Project Modal */}
      <Modal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} title="Create Project">
        <form onSubmit={handleCreateProject}>
          <Input
            label="Project Name"
            placeholder="Logistics Carbon Audit Q2"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            theme="dark"
            required
          />
          <Input
            label="Description (Optional)"
            placeholder="Attributing transport emissions using OCEL 2.0 log inputs."
            value={projectDesc}
            onChange={(e) => setProjectDesc(e.target.value)}
            theme="dark"
          />
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="secondary" type="button" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
            <Button type="submit">Create</Button>
          </div>
        </form>
      </Modal>

      {/* Ingestion Wizard Modal Overlay */}
      {isIngestOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
          <UploadWizard 
            onClose={() => setIsIngestOpen(false)} 
            onSuccess={() => {
              setIsIngestOpen(false);
              fetchDatasets();
            }}
          />
        </div>
      )}

      {/* Preview Dataset Modal */}
      {previewDatasetId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-card-bg rounded-xl shadow-2xl border border-border-color overflow-hidden w-full max-w-4xl">
            <div className="bg-gradient-to-r from-slate-900 to-slate-950 px-6 py-4 text-foreground flex justify-between items-center border-b border-border-color">
              <h3 className="font-bold text-lg">Dataset Schema & Sample Rows</h3>
              <button 
                onClick={() => setPreviewDatasetId(null)} 
                className="text-text-muted hover:text-foreground p-1 hover:bg-slate-100 rounded-full transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6 space-y-6">
              {loadingPreview ? (
                <div className="py-12 text-center text-text-muted font-medium">Loading preview data...</div>
              ) : previewData ? (
                <div className="space-y-6">
                  <div className="border border-border-color rounded-xl overflow-hidden shadow-none overflow-x-auto max-w-full">
                    <table className="w-full text-left border-collapse min-w-[600px]">
                      <thead>
                        <tr className="bg-card-bg border-b border-border-color">
                          {previewData.headers.map((header) => {
                            const role = previewData.mappings?.[header] || "ignore";
                            const isIgnored = role === "ignore";
                            return (
                              <th key={header} className="px-4 py-3 text-xs font-semibold">
                                <div className="text-foreground font-mono font-bold">{header}</div>
                                <div className={`text-[10px] mt-1 inline-block px-1.5 py-0.5 rounded font-bold ${
                                  isIgnored ? "bg-slate-100 text-text-muted" : "bg-blue-950/50 text-blue-400 border border-blue-900/50"
                                }`}>
                                  {role.toUpperCase()}
                                </div>
                              </th>
                            );
                          })}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border-color text-xs font-mono text-foreground">
                        {previewData.preview.map((row, rowIdx) => (
                          <tr key={rowIdx} className="hover:bg-slate-100/30">
                            {previewData.headers.map((_, colIdx) => (
                              <td key={colIdx} className="px-4 py-3 max-w-[200px] truncate">
                                {row[colIdx] !== undefined ? row[colIdx] : <span className="text-slate-600">NULL</span>}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="text-center text-text-muted font-semibold text-sm">Failed to retrieve preview.</div>
              )}
              <div className="flex justify-end pt-4 border-t border-border-color">
                <Button onClick={() => setPreviewDatasetId(null)}>Close</Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
