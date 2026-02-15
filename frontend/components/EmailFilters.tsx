"use client";

interface Props {
  priority: string;
  type: string;
  onPriorityChange: (v: string) => void;
  onTypeChange: (v: string) => void;
}

const priorities = ["all", "urgent", "high", "normal", "low"];
const types = ["all", "security", "payment", "newsletter", "meeting", "other"];

export default function EmailFilters({ priority, type, onPriorityChange, onTypeChange }: Props) {
  return (
    <div className="flex gap-3 items-center">
      <div className="flex items-center gap-2">
        <label className="text-xs text-slate-400 uppercase tracking-wide">Priority</label>
        <select
          value={priority}
          onChange={(e) => onPriorityChange(e.target.value)}
          className="bg-slate-700 border border-slate-600 text-sm rounded px-2 py-1 text-slate-200 focus:border-cyan-500 focus:outline-none"
        >
          {priorities.map((p) => (
            <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
          ))}
        </select>
      </div>
      <div className="flex items-center gap-2">
        <label className="text-xs text-slate-400 uppercase tracking-wide">Type</label>
        <select
          value={type}
          onChange={(e) => onTypeChange(e.target.value)}
          className="bg-slate-700 border border-slate-600 text-sm rounded px-2 py-1 text-slate-200 focus:border-cyan-500 focus:outline-none"
        >
          {types.map((t) => (
            <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
          ))}
        </select>
      </div>
    </div>
  );
}
