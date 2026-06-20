"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../context/AuthContext";
import { Sidebar } from "../../components/Sidebar";
import { ExecutiveCopilot } from "../../components/copilot/ExecutiveCopilot";
import { Sparkles } from "lucide-react";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { token, loading } = useAuth();
  const router = useRouter();
  const [copilotOpen, setCopilotOpen] = useState(false);

  useEffect(() => {
    if (!loading && !token) {
      router.push("/login");
    }
  }, [token, loading, router]);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-sm text-gray-500 mt-4 font-semibold">Verifying secure session...</p>
        </div>
      </div>
    );
  }

  if (!token) return null;

  return (
    <div className="flex w-full min-h-screen bg-background text-foreground relative">
      <Sidebar />
      <main className="flex-1 p-8 overflow-y-auto w-full">
        {children}
      </main>

      {/* Global Floating AI Copilot Trigger Button */}
      <button
        onClick={() => setCopilotOpen(true)}
        className="fixed bottom-6 right-6 z-40 flex items-center justify-center w-12 h-12 bg-[#4f46e5] text-white rounded-full shadow-md border border-border-color hover:bg-[#4338ca] hover:scale-105 active:scale-95 transition-all duration-200 cursor-pointer"
        title="Open AI Sustainability Assistant"
      >
        <Sparkles className="h-5 w-5" />
      </button>

      {/* Executive Copilot Slide-out Panel */}
      {copilotOpen && (
        <ExecutiveCopilot onClose={() => setCopilotOpen(false)} />
      )}
    </div>
  );
}


