"use client";

import React, { useState } from "react";
import { useAuth } from "../../../context/AuthContext";
import { Card } from "../../../components/Card";
import { Input } from "../../../components/Input";
import { Button } from "../../../components/Button";
import { Modal } from "../../../components/Modal";

export default function WorkspacesPage() {
  const {
    activeOrg,
    workspaces,
    activeWorkspace,
    createWorkspace,
    selectWorkspace,
  } = useAuth();

  const [newWorkspaceName, setNewWorkspaceName] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [error, setError] = useState("");

  const handleCreateWorkspace = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!newWorkspaceName) return;
    try {
      await createWorkspace(newWorkspaceName);
      setNewWorkspaceName("");
      setIsCreateOpen(false);
    } catch (err: any) {
      setError(err.message || "Failed to create workspace.");
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-black text-foreground tracking-tight">Workspaces</h1>
          <p className="text-text-muted font-medium mt-1 font-semibold">Group projects and workflows under your active organization</p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)} disabled={!activeOrg}>Create Workspace</Button>
      </div>

      {error && (
        <div className="bg-red-950/40 border border-red-900 text-red-400 text-sm p-3 rounded-md mb-4 font-semibold">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <Card title="Available Workspaces">
            <div className="space-y-2">
              {workspaces.map((ws) => (
                <div
                  key={ws.id}
                  onClick={() => selectWorkspace(ws)}
                  className={`p-3 rounded-md border text-sm font-semibold transition-all cursor-pointer ${
                    activeWorkspace?.id === ws.id
                      ? "bg-indigo-950/50 border-indigo-500/50 text-indigo-400"
                      : "bg-background border-border-color text-foreground hover:bg-slate-100"
                  }`}
                >
                  {ws.name}
                </div>
              ))}
              {workspaces.length === 0 && <p className="text-sm text-text-muted">No workspaces found.</p>}
            </div>
          </Card>
        </div>

        <div className="lg:col-span-2">
          {activeWorkspace ? (
            <Card title={`${activeWorkspace.name} — Workspace Overview`}>
              <div className="border border-border-color rounded-md p-4 bg-background">
                <p className="text-sm font-semibold text-text-muted mb-1">Workspace Identity Key</p>
                <p className="text-xs text-text-muted font-mono mb-4">{activeWorkspace.id}</p>
                
                <p className="text-sm text-foreground font-medium leading-relaxed">
                  This workspace holds your projects, imported event files, and analytical runs. Use the sidebar to switch workspaces, or the navigation to inspect active projects.
                </p>
              </div>
            </Card>
          ) : (
            <Card title="No Selected Workspace">
              <p className="text-sm text-text-muted">Select or create a workspace to see options.</p>
            </Card>
          )}
        </div>
      </div>

      {/* Create Workspace Modal */}
      <Modal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} title="Create Workspace">
        <form onSubmit={handleCreateWorkspace}>
          <Input
            label="Workspace Name"
            placeholder="Manufacturing Plant A"
            value={newWorkspaceName}
            onChange={(e) => setNewWorkspaceName(e.target.value)}
            theme="dark"
            required
          />
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="secondary" type="button" onClick={() => setIsCreateOpen(false)}>Cancel</Button>
            <Button type="submit">Create</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
