"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { StatusResponse } from "@/lib/types";
import LoadingSpinner from "@/components/LoadingSpinner";
import {
  Mail, MessageCircle, Database, Twitter, Linkedin,
  Bot, CheckCircle2, XCircle, RefreshCw,
} from "lucide-react";

export default function DashboardPage() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      setStatus(await api.getStatus());
    } catch {
      /* backend down */
    }
    setLoading(false);
  };

  useEffect(() => {
    load();
    const iv = setInterval(load, 30000);
    return () => clearInterval(iv);
  }, []);

  if (loading) return <div className="p-8"><LoadingSpinner text="Loading dashboard..." /></div>;

  const counts = status?.counts || {};
  const services = status?.services || {};

  const statCards = [
    { label: "Needs Action", value: counts.needs_action ?? 0, color: "text-amber-400" },
    { label: "Pending Approval", value: counts.pending_approval ?? 0, color: "text-cyan-400" },
    { label: "Approved", value: counts.approved ?? 0, color: "text-green-400" },
    { label: "Rejected", value: counts.rejected ?? 0, color: "text-red-400" },
    { label: "Done", value: counts.done ?? 0, color: "text-slate-400" },
  ];

  const serviceIcons: Record<string, React.ReactNode> = {
    gmail: <Mail className="w-4 h-4" />,
    twitter: <Twitter className="w-4 h-4" />,
    linkedin: <Linkedin className="w-4 h-4" />,
    whatsapp: <MessageCircle className="w-4 h-4" />,
    odoo: <Database className="w-4 h-4" />,
    ai_assistant: <Bot className="w-4 h-4" />,
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <button onClick={load} className="flex items-center gap-1 text-sm text-slate-400 hover:text-slate-200">
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {statCards.map((c) => (
          <div key={c.label} className="bg-slate-800 border border-slate-700 rounded-lg p-4">
            <p className="text-xs text-slate-500 uppercase tracking-wide">{c.label}</p>
            <p className={`text-3xl font-bold mt-1 ${c.color}`}>{c.value}</p>
          </div>
        ))}
      </div>

      {/* Services */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Services</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {Object.entries(services).map(([name, s]) => (
            <div key={name} className="bg-slate-800 border border-slate-700 rounded-lg p-3 flex items-center gap-3">
              <div className="text-slate-400">{serviceIcons[name] || <Bot className="w-4 h-4" />}</div>
              <div className="flex-1">
                <p className="text-sm font-medium capitalize">{name.replace("_", " ")}</p>
              </div>
              {s === "connected" ? (
                <CheckCircle2 className="w-4 h-4 text-green-400" />
              ) : (
                <XCircle className="w-4 h-4 text-slate-500" />
              )}
              <span className={`text-xs ${s === "connected" ? "text-green-400" : "text-slate-500"}`}>
                {s}
              </span>
            </div>
          ))}
        </div>
      </div>

      {status && (
        <p className="text-xs text-slate-600">
          Last updated: {new Date(status.timestamp).toLocaleString()} &middot; {status.environment}
        </p>
      )}
    </div>
  );
}
