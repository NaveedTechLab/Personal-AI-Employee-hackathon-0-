"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import LoadingSpinner from "@/components/LoadingSpinner";
import { Database } from "lucide-react";

const tabs = [
  "summary", "invoices", "orders", "partners", "employees",
  "leads", "expenses", "products", "projects", "payments",
];

export default function OdooPage() {
  const [tab, setTab] = useState("summary");
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getOdoo(tab).then(setData).catch(() => setData(null)).finally(() => setLoading(false));
  }, [tab]);

  const renderTable = (items: Record<string, unknown>[]) => {
    if (!items.length) return <p className="text-slate-500 text-sm">No data.</p>;
    const keys = Object.keys(items[0]);
    return (
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700">
              {keys.map((k) => (
                <th key={k} className="text-left p-2 text-slate-400 font-medium capitalize">{k.replace(/_/g, " ")}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {items.map((item, i) => (
              <tr key={i} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                {keys.map((k) => (
                  <td key={k} className="p-2 text-slate-300">{String(item[k] ?? "")}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderData = () => {
    if (!data) return <p className="text-slate-500">No data available.</p>;
    // If data has an array property, render it as table
    for (const val of Object.values(data)) {
      if (Array.isArray(val) && val.length > 0 && typeof val[0] === "object") {
        return renderTable(val as Record<string, unknown>[]);
      }
    }
    // Otherwise render as key-value
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {Object.entries(data).map(([k, v]) => (
          <div key={k} className="bg-slate-800 border border-slate-700 rounded-lg p-3">
            <p className="text-xs text-slate-500 capitalize">{k.replace(/_/g, " ")}</p>
            <p className="text-lg font-semibold">{typeof v === "object" ? JSON.stringify(v) : String(v)}</p>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center gap-2">
        <Database className="w-5 h-5 text-orange-400" />
        <h1 className="text-2xl font-bold">Odoo ERP</h1>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 flex-wrap border-b border-slate-700 pb-1">
        {tabs.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-1.5 text-sm rounded-t transition-colors ${
              tab === t ? "bg-slate-700 text-cyan-400" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </div>

      {loading ? <LoadingSpinner /> : renderData()}
    </div>
  );
}
