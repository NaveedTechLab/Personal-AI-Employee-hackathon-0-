"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { VaultFile } from "@/lib/types";
import LoadingSpinner from "@/components/LoadingSpinner";
import { FolderOpen, FileText, ArrowRight } from "lucide-react";

const folders = ["Needs_Action", "Pending_Approval", "Inbox", "Done", "Approved", "Rejected"];

export default function VaultPage() {
  const [folder, setFolder] = useState("Needs_Action");
  const [files, setFiles] = useState<VaultFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedFile, setSelectedFile] = useState<{ content: string; filename: string } | null>(null);
  const [moveTarget, setMoveTarget] = useState("");

  const load = async (f: string) => {
    setLoading(true);
    setSelectedFile(null);
    try {
      const r = await api.browseVault(f);
      setFiles(r.files || []);
    } catch { setFiles([]); }
    setLoading(false);
  };

  useEffect(() => { load(folder); }, [folder]);

  const viewFile = async (path: string, filename: string) => {
    try {
      const r = await api.getVaultFile(path);
      setSelectedFile({ content: r.content, filename });
    } catch { setSelectedFile({ content: "Error loading file.", filename }); }
  };

  const moveFile = async (filename: string) => {
    if (!moveTarget) return;
    await api.moveVaultFile(filename, folder, moveTarget);
    load(folder);
  };

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center gap-2">
        <FolderOpen className="w-5 h-5 text-purple-400" />
        <h1 className="text-2xl font-bold">Vault</h1>
      </div>

      {/* Folder tabs */}
      <div className="flex gap-1 flex-wrap border-b border-slate-700 pb-1">
        {folders.map((f) => (
          <button key={f} onClick={() => setFolder(f)}
            className={`px-3 py-1.5 text-sm rounded-t transition-colors ${
              folder === f ? "bg-slate-700 text-cyan-400" : "text-slate-400 hover:text-slate-200"
            }`}>
            {f.replace(/_/g, " ")}
          </button>
        ))}
      </div>

      <div className="flex gap-4">
        {/* File list */}
        <div className="w-80 space-y-1 flex-shrink-0">
          {loading ? <LoadingSpinner /> : files.length === 0 ? (
            <p className="text-slate-500 text-sm">No files in this folder.</p>
          ) : files.map((f) => (
            <button key={f.path} onClick={() => viewFile(f.path, f.filename)}
              className={`w-full text-left p-2 rounded hover:bg-slate-700/50 transition-colors ${
                selectedFile?.filename === f.filename ? "bg-slate-700/50" : ""
              }`}>
              <div className="flex items-center gap-2">
                <FileText className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                <span className="text-sm truncate">{f.filename}</span>
              </div>
              <p className="text-xs text-slate-500 ml-5.5">{f.type} &middot; {f.priority}</p>
            </button>
          ))}
        </div>

        {/* File viewer */}
        <div className="flex-1">
          {selectedFile ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold truncate">{selectedFile.filename}</h3>
                <div className="flex items-center gap-2">
                  <select value={moveTarget} onChange={(e) => setMoveTarget(e.target.value)}
                    className="bg-slate-700 border border-slate-600 text-xs rounded px-2 py-1 focus:outline-none">
                    <option value="">Move to...</option>
                    {folders.filter((f) => f !== folder).map((f) => (
                      <option key={f} value={f}>{f.replace(/_/g, " ")}</option>
                    ))}
                  </select>
                  <button onClick={() => moveFile(selectedFile.filename)} disabled={!moveTarget}
                    className="flex items-center gap-1 px-2 py-1 bg-slate-600 hover:bg-slate-500 rounded text-xs disabled:opacity-50">
                    <ArrowRight className="w-3 h-3" /> Move
                  </button>
                </div>
              </div>
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 text-sm whitespace-pre-wrap max-h-[70vh] overflow-y-auto">
                {selectedFile.content}
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-40 text-slate-500 text-sm">
              Select a file to view
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
