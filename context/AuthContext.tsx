"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter } from "next/navigation";

interface User {
  id: string;
  email: string;
}

interface Organization {
  id: string;
  name: string;
}

interface Workspace {
  id: string;
  organization_id: string;
  name: string;
}

interface Project {
  id: string;
  workspace_id: string;
  name: string;
  description?: string;
  is_archived: boolean;
}

interface AuthContextType {
  token: string | null;
  user: User | null;
  organizations: Organization[];
  workspaces: Workspace[];
  projects: Project[];
  activeOrg: Organization | null;
  activeWorkspace: Workspace | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  createOrg: (name: string) => Promise<void>;
  createWorkspace: (name: string) => Promise<void>;
  createProject: (name: string, description?: string) => Promise<void>;
  archiveProject: (projectId: string, isArchived: boolean) => Promise<void>;
  deleteProject: (projectId: string) => Promise<void>;
  inviteMember: (email: string, role: string) => Promise<void>;
  selectOrg: (org: Organization) => void;
  selectWorkspace: (ws: Workspace) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_URL = "http://localhost:8000/api";

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeOrg, setActiveOrg] = useState<Organization | null>(null);
  const [activeWorkspace, setActiveWorkspace] = useState<Workspace | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const storedToken = localStorage.getItem("token");
    const storedUser = localStorage.getItem("user");
    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    if (token) {
      fetchOrganizations();
    } else {
      setOrganizations([]);
      setWorkspaces([]);
      setProjects([]);
      setActiveOrg(null);
      setActiveWorkspace(null);
    }
  }, [token]);

  useEffect(() => {
    if (activeOrg) {
      fetchWorkspaces(activeOrg.id);
    } else {
      setWorkspaces([]);
      setActiveWorkspace(null);
    }
  }, [activeOrg]);

  useEffect(() => {
    if (activeWorkspace) {
      fetchProjects(activeWorkspace.id);
    } else {
      setProjects([]);
    }
  }, [activeWorkspace]);

  const fetchOrganizations = async () => {
    try {
      const res = await fetch(`${API_URL}/organizations/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setOrganizations(data);
        if (data.length > 0 && !activeOrg) {
          setActiveOrg(data[0]);
        }
      }
    } catch (err) {
      console.error("Error fetching organizations", err);
    }
  };

  const fetchWorkspaces = async (orgId: string) => {
    try {
      const res = await fetch(`${API_URL}/workspaces/?organization_id=${orgId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setWorkspaces(data);
        if (data.length > 0) {
          setActiveWorkspace(data[0]);
        } else {
          setActiveWorkspace(null);
        }
      }
    } catch (err) {
      console.error("Error fetching workspaces", err);
    }
  };

  const fetchProjects = async (wsId: string) => {
    try {
      const res = await fetch(`${API_URL}/projects/?workspace_id=${wsId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setProjects(data);
      }
    } catch (err) {
      console.error("Error fetching projects", err);
    }
  };

  const login = async (email: string, password: string) => {
    const res = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Login failed");
    }
    const data = await res.json();
    localStorage.setItem("token", data.access_token);
    // Decode user info roughly from token or set user structure
    const decodedUser = { id: "", email }; // Simple mock user structure derived on client
    localStorage.setItem("user", JSON.stringify(decodedUser));
    setToken(data.access_token);
    setUser(decodedUser);
    router.push("/dashboard");
  };

  const signup = async (email: string, password: string) => {
    const res = await fetch(`${API_URL}/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Signup failed");
    }
  };

  const logout = async () => {
    try {
      await fetch(`${API_URL}/auth/logout`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch (err) {
      console.error(err);
    }
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setToken(null);
    setUser(null);
    router.push("/login");
  };

  const createOrg = async (name: string) => {
    const res = await fetch(`${API_URL}/organizations/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ name }),
    });
    if (!res.ok) throw new Error("Failed to create organization");
    await fetchOrganizations();
  };

  const createWorkspace = async (name: string) => {
    if (!activeOrg) return;
    const res = await fetch(`${API_URL}/workspaces/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ organization_id: activeOrg.id, name }),
    });
    if (!res.ok) throw new Error("Failed to create workspace");
    await fetchWorkspaces(activeOrg.id);
  };

  const createProject = async (name: string, description?: string) => {
    if (!activeWorkspace) return;
    const res = await fetch(`${API_URL}/projects/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ workspace_id: activeWorkspace.id, name, description }),
    });
    if (!res.ok) throw new Error("Failed to create project");
    await fetchProjects(activeWorkspace.id);
  };

  const archiveProject = async (projectId: string, isArchived: boolean) => {
    const res = await fetch(`${API_URL}/projects/${projectId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ is_archived: isArchived }),
    });
    if (!res.ok) throw new Error("Failed to archive project");
    if (activeWorkspace) await fetchProjects(activeWorkspace.id);
  };

  const deleteProject = async (projectId: string) => {
    const res = await fetch(`${API_URL}/projects/${projectId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || "Failed to delete project");
    }
    if (activeWorkspace) await fetchProjects(activeWorkspace.id);
  };

  const inviteMember = async (email: string, role: string) => {
    if (!activeOrg) return;
    const res = await fetch(`${API_URL}/organizations/${activeOrg.id}/invite`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ email, role }),
    });
    if (!res.ok) throw new Error("Failed to invite member");
  };

  const selectOrg = (org: Organization) => {
    setActiveOrg(org);
    setActiveWorkspace(null);
  };

  const selectWorkspace = (ws: Workspace) => {
    setActiveWorkspace(ws);
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        organizations,
        workspaces,
        projects,
        activeOrg,
        activeWorkspace,
        loading,
        login,
        signup,
        logout,
        createOrg,
        createWorkspace,
        createProject,
        archiveProject,
        deleteProject,
        inviteMember,
        selectOrg,
        selectWorkspace,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
