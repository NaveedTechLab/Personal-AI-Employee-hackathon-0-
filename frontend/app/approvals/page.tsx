"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import LoadingSpinner from "@/components/LoadingSpinner";
import { CheckSquare, Check, X } from "lucide-react";

export default function ApprovalsPage() {
  const [items, setItems] = useState<{ filename: string; type: string; priority: string; created: string; preview: string }[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const r = await api.getPending();
      setItems(r.items || []);
    } catch { /* noop */ }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const approve = async (filename: string) => {
    await api.approve(filename);
    load();
  };

  const reject = async (filename: string) => {
    await api.reject(filename);
    load();
  };

  if (loading) return <div className="p-8"><LoadingSpinner /></div>;

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center gap-2">
        <CheckSquare className="w-5 h-5 text-yellow-400" />
        <h1 className="text-2xl font-bold">Approvals</h1>
        <span className="text-sm text-slate-500">({items.length} pending)</span>
      </div>

      {items.length === 0 && <p className="text-slate-500 text-sm">No items pending approval.</p>}

      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.filename} className="bg-slate-800 border border-slate-700 rounded-lg p-4 flex gap-4">
            <div className="flex-1">
              <p className="text-sm font-medium">{item.filename}</p>
              <p className="text-xs text-slate-400 mt-1">{item.type} &middot; {item.priority} &middot; {item.created}</p>
              {item.preview && <p className="text-sm text-slate-400 mt-2">{item.preview}</p>}
            </div>
            <div className="flex flex-col gap-2">
              <button onClick={() => approve(item.filename)}
                className="flex items-center gap-1 px-3 py-1.5 bg-green-600 hover:bg-green-500 rounded text-sm">
                <Check className="w-3.5 h-3.5" /> Approve
              </button>
              <button onClick={() => reject(item.filename)}
                className="flex items-center gap-1 px-3 py-1.5 bg-red-600 hover:bg-red-500 rounded text-sm">
                <X className="w-3.5 h-3.5" /> Reject
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
