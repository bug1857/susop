"use client";

import React, { useState, useEffect } from "react";
import { useAuth } from "../../../context/AuthContext";
import { Card } from "../../../components/Card";
import { Input } from "../../../components/Input";
import { Button } from "../../../components/Button";
import { Modal } from "../../../components/Modal";

interface Member {
  id: string;
  user: {
    id: string;
    email: string;
  };
  role: string;
  created_at: string;
}

export default function OrganizationsPage() {
  const {
    token,
    organizations,
    activeOrg,
    createOrg,
    inviteMember,
  } = useAuth();

  const [newOrgName, setNewOrgName] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("Viewer");
  const [members, setMembers] = useState<Member[]>([]);
  const [isInviteOpen, setIsInviteOpen] = useState(false);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleCreateOrg = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!newOrgName) return;
    try {
      await createOrg(newOrgName);
      setNewOrgName("");
      setIsCreateOpen(false);
    } catch (err: any) {
      setError(err.message || "Failed to create organization.");
    }
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    if (!inviteEmail) return;
    try {
      await inviteMember(inviteEmail, inviteRole);
      setInviteEmail("");
      setIsInviteOpen(false);
      setSuccess("Invitation sent successfully!");
      if (activeOrg) fetchMembers(activeOrg.id);
    } catch (err: any) {
      setError(err.message || "Failed to send invitation.");
    }
  };

  const fetchMembers = async (orgId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/organizations/${orgId}/members`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setMembers(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    if (activeOrg && token) {
      fetchMembers(activeOrg.id);
    }
  }, [activeOrg, token]);

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-black text-foreground tracking-tight">Organizations</h1>
          <p className="text-text-muted font-medium mt-1 font-semibold">Manage multi-tenant organizations and memberships</p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)}>Create Organization</Button>
      </div>

      {success && (
        <div className="bg-green-950/40 border border-green-900/50 text-green-400 text-sm p-3 rounded-md mb-4 font-semibold">
          {success}
        </div>
      )}

      {error && (
        <div className="bg-red-950/40 border border-red-900 text-red-400 text-sm p-3 rounded-md mb-4 font-semibold">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Organizations List */}
        <div className="lg:col-span-1">
          <Card title="Your Organizations">
            <div className="space-y-2">
              {organizations.map((org) => (
                <div
                  key={org.id}
                  className={`p-3 rounded-md border text-sm font-semibold transition-all cursor-pointer ${
                    activeOrg?.id === org.id
                      ? "bg-indigo-950/50 border-indigo-500/50 text-indigo-400"
                      : "bg-background border-border-color text-foreground hover:bg-slate-100"
                  }`}
                >
                  {org.name}
                </div>
              ))}
              {organizations.length === 0 && <p className="text-sm text-text-muted">No organizations found.</p>}
            </div>
          </Card>
        </div>

        {/* Organization Details & Members */}
        <div className="lg:col-span-2">
          {activeOrg ? (
            <Card title={`${activeOrg.name} — Members`}>
              <div className="flex justify-between items-center mb-4">
                <p className="text-sm text-text-muted font-semibold">Manage authorization roles for this organization context.</p>
                <Button variant="secondary" onClick={() => setIsInviteOpen(true)}>Invite Member</Button>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-foreground">
                  <thead className="text-xs uppercase bg-slate-100 text-text-muted font-bold border-b border-border-color">
                    <tr>
                      <th className="px-4 py-3">Member Email</th>
                      <th className="px-4 py-3">Role</th>
                      <th className="px-4 py-3">Assigned Date</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-color font-medium">
                    {members.map((member) => (
                      <tr key={member.id} className="hover:bg-slate-100/20">
                        <td className="px-4 py-3 text-foreground font-bold">{member.user.email}</td>
                        <td className="px-4 py-3">
                          <span className="px-2 py-1 bg-slate-100 rounded text-xs font-semibold text-foreground border border-border-color/50">
                            {member.role}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-text-muted">
                          {new Date(member.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                    {members.length === 0 && (
                      <tr>
                        <td colSpan={3} className="px-4 py-6 text-center text-gray-500">No members listed.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </Card>
          ) : (
            <Card title="No Active Context">
              <p className="text-sm text-text-muted">Select or create an organization to view details.</p>
            </Card>
          )}
        </div>
      </div>

      {/* Invite Member Modal */}
      <Modal isOpen={isInviteOpen} onClose={() => setIsInviteOpen(false)} title="Invite Member">
        <form onSubmit={handleInvite}>
          <Input
            label="Email Address"
            type="email"
            placeholder="colleague@company.com"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            theme="dark"
            required
          />
          <div className="mb-4">
            <label className="block text-sm font-semibold text-foreground mb-1">Access Role</label>
            <select
              className="w-full px-3 py-2 border border-border-color rounded-md text-sm text-foreground bg-background focus:outline-none focus:ring-2 focus:ring-indigo-500 font-semibold"
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
            >
              <option value="Admin">Admin</option>
              <option value="Manager">Manager</option>
              <option value="Analyst">Analyst</option>
              <option value="Viewer">Viewer</option>
            </select>
          </div>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="secondary" type="button" onClick={() => setIsInviteOpen(false)}>Cancel</Button>
            <Button type="submit">Send Invitation</Button>
          </div>
        </form>
      </Modal>

      {/* Create Org Modal */}
      <Modal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} title="Create Organization">
        <form onSubmit={handleCreateOrg}>
          <Input
            label="Organization Name"
            placeholder="SustainOps Ltd"
            value={newOrgName}
            onChange={(e) => setNewOrgName(e.target.value)}
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
