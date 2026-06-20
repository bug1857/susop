"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useAuth } from "../../../context/AuthContext";
import { Card } from "../../../components/Card";
import { Clock } from "lucide-react";

interface AuditLog {
  id: string;
  user_id: string;
  action: string;
  details: string;
  created_at: string;
}

export default function AuditLogsPage() {
  const { token, activeOrg } = useAuth();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchAuditLogs = useCallback(async (orgId: string) => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch(
        `http://localhost:8000/api/audit/?organization_id=${orgId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        setLogs(await res.json());
      }
    } catch (err) {
      console.warn("Error fetching audit logs", err);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    if (activeOrg && token) {
      fetchAuditLogs(activeOrg.id);
    } else {
      setLogs([]);
    }
  }, [activeOrg, token, fetchAuditLogs]);

  return (
    <div className="w-full space-y-6 pb-16 text-foreground">
      {/* Page Header */}
      <div className="border-b border-border-color pb-5">
        <h1 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-3">
          Tenant Audit Logs
        </h1>
        <p className="text-text-muted font-medium text-xs mt-1">
          Complete organizational and copilot audit trail ledger history
        </p>
      </div>

      <Card className="bg-card-bg border-border-color p-6 shadow-sm">
        <div className="border-l-2 border-indigo-500 pl-3 mb-5">
          <h3 className="text-sm font-bold text-foreground uppercase tracking-wider">Activity History</h3>
          <p className="text-xs text-text-muted mt-0.5 font-medium">All logged administrative and assistant updates</p>
        </div>

        {loading ? (
          <div className="text-xs text-text-muted text-center py-10 font-semibold">
            Loading audit logs...
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-foreground">
              <thead className="text-[10px] uppercase bg-background text-text-muted font-bold border-b border-border-color">
                <tr>
                  <th className="px-4 py-3 border-b border-border-color">Timestamp</th>
                  <th className="px-4 py-3 border-b border-border-color">Action</th>
                  <th className="px-4 py-3 border-b border-border-color">Audit Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-color font-medium bg-card-bg">
                {Array.isArray(logs) && logs.map((log) => (
                  <tr key={log?.id || Math.random().toString()} className="hover:bg-background/30 transition-colors">
                    <td className="px-4 py-3 text-text-muted font-mono text-[10px]">
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5" />
                        {log?.created_at ? new Date(log.created_at).toLocaleString() : "—"}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="font-bold text-foreground uppercase">{(log?.action || "").replace(/_/g, " ")}</span>
                    </td>
                    <td className="px-4 py-3 text-text-muted">{log?.details || "—"}</td>
                  </tr>
                ))}
                {(!Array.isArray(logs) || logs.length === 0) && (
                  <tr>
                    <td colSpan={3} className="px-4 py-10 text-center text-text-muted font-semibold">
                      No audit trails logged for this organization context.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
