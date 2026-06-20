"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "../context/AuthContext";
import { ChevronDown, ChevronRight, LogOut } from "lucide-react";

export const Sidebar: React.FC = () => {
  const {
    user,
    organizations,
    workspaces,
    activeOrg,
    activeWorkspace,
    selectOrg,
    selectWorkspace,
    logout,
  } = useAuth();
  
  const pathname = usePathname();

  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>({
    "Core": true,
    "Process Mining": true,
    "Sustainability": true,
    "AI Intelligence": true,
    "Governance": true,
  });

  if (!user) return null;

  const toggleGroup = (group: string) => {
    setExpandedGroups(prev => ({ ...prev, [group]: !prev[group] }));
  };

  const navGroups = [
    {
      name: "Core",
      links: [
        { name: "Dashboard", path: "/dashboard" },
        { name: "Projects", path: "/dashboard/projects" },
        { name: "Organizations", path: "/dashboard/organizations" },
        { name: "Workspaces", path: "/dashboard/workspaces" },
      ]
    },
    {
      name: "Process Mining",
      links: [
        { name: "OCEL 2.0", path: "/dashboard/ocel" },
        { name: "Conformance", path: "/dashboard/conformance" },
        { name: "Carbon Fitness", path: "/dashboard/carbon-fitness" },
        { name: "Process Optimization", path: "/dashboard/process-optimization" },
      ]
    },
    {
      name: "Sustainability",
      links: [
        { name: "ESG", path: "/dashboard/esg" },
        { name: "BRSR", path: "/dashboard/brsr" },
        { name: "Rerouting", path: "/dashboard/rerouting" },
        { name: "Recommendations", path: "/dashboard/recommendations" },
      ]
    },
    {
      name: "AI Intelligence",
      links: [
        { name: "Copilot", path: "/dashboard/copilot" },
        { name: "Sustainability Conformance", path: "/dashboard/sustainability-conformance" },
        { name: "Digital Twin", path: "/dashboard/digital-twin" },
        { name: "AI Benchmarking", path: "/dashboard/benchmarking" },
      ]
    },
    {
      name: "Governance",
      links: [
        { name: "Settings", path: "/dashboard/settings" },
        { name: "Audit Logs", path: "/dashboard/audit-logs" },
      ]
    }
  ];

  const renderLink = (link: { name: string; path: string }) => {
    const isActive = pathname === link.path;
    return (
      <Link
        key={link.path}
        href={link.path}
        className={`block px-3 py-1.5 text-xs font-medium transition-all border-l-2 ${
          isActive
            ? "border-[#4f46e5] bg-slate-200 text-foreground font-semibold"
            : "border-transparent text-text-muted hover:bg-slate-100 hover:text-foreground"
        }`}
      >
        {link.name}
      </Link>
    );
  };

  return (
    <aside className="w-56 bg-sidebar-bg border-r border-border-color min-h-screen flex flex-col justify-between text-foreground">
      <div className="flex-1 overflow-y-auto overflow-x-hidden p-4">
        <div className="mb-6">
          <h2 className="text-lg font-black tracking-tight text-foreground">SustainOCPM</h2>
          <p className="text-[10px] text-text-muted mt-0.5 font-medium uppercase tracking-widest">Enterprise Platform</p>
        </div>

        {/* Organization Switcher */}
        <div className="mb-4">
          <label className="block text-[10px] font-bold text-text-muted uppercase tracking-wider mb-1">Organization</label>
          <select
            className="w-full px-2 py-1.5 border border-border-color rounded-md text-xs bg-card-bg text-foreground focus:border-[#4f46e5] focus:ring-1 focus:ring-[#4f46e5] outline-none"
            value={activeOrg?.id || ""}
            onChange={(e) => {
              const selected = organizations.find((o) => o.id === e.target.value);
              if (selected) selectOrg(selected);
            }}
          >
            {organizations.map((org) => (
              <option key={org.id} value={org.id}>
                {org.name}
              </option>
            ))}
            {organizations.length === 0 && <option value="">No Organizations</option>}
          </select>
        </div>

        {/* Workspace Switcher */}
        <div className="mb-6">
          <label className="block text-[10px] font-bold text-text-muted uppercase tracking-wider mb-1">Workspace</label>
          <select
            className="w-full px-2 py-1.5 border border-border-color rounded-md text-xs bg-card-bg text-foreground focus:border-[#4f46e5] focus:ring-1 focus:ring-[#4f46e5] outline-none"
            value={activeWorkspace?.id || ""}
            onChange={(e) => {
              const selected = workspaces.find((w) => w.id === e.target.value);
              if (selected) selectWorkspace(selected);
            }}
          >
            {workspaces.map((ws) => (
              <option key={ws.id} value={ws.id}>
                {ws.name}
              </option>
            ))}
            {workspaces.length === 0 && <option value="">No Workspaces</option>}
          </select>
        </div>

        {/* Navigation Groups */}
        <nav className="space-y-4">
          {navGroups.map((group) => (
            <div key={group.name}>
              <button
                onClick={() => toggleGroup(group.name)}
                className="w-full flex items-center justify-between text-[10px] uppercase font-bold text-text-muted tracking-wider px-2 py-1 hover:text-foreground transition-colors"
              >
                <span>{group.name}</span>
                {expandedGroups[group.name] ? (
                  <ChevronDown className="h-3 w-3" />
                ) : (
                  <ChevronRight className="h-3 w-3" />
                )}
              </button>
              {expandedGroups[group.name] && (
                <div className="mt-1 space-y-0.5">
                  {group.links.map(renderLink)}
                </div>
              )}
            </div>
          ))}
        </nav>
      </div>

      <div className="border-t border-border-color p-4 bg-sidebar-bg">
        <div className="flex items-center justify-between mb-3">
          <div className="overflow-hidden">
            <p className="text-[10px] text-text-muted font-medium truncate">Logged in as</p>
            <p className="text-xs font-bold text-foreground truncate" title={user.email}>{user.email}</p>
          </div>
          <button 
            onClick={logout}
            className="p-1.5 text-text-muted hover:text-foreground hover:bg-slate-100 rounded-md transition-colors"
            title="Sign Out"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
        <div className="text-center pt-2 border-t border-border-color">
          <span className="text-[10px] font-bold text-text-muted">SustainOCPM v1.0</span>
        </div>
      </div>
    </aside>
  );
};
