"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Email } from "@/lib/types";
import EmailFilters from "@/components/EmailFilters";
import LoadingSpinner from "@/components/LoadingSpinner";
import { classifyEmailType, priorityColor, typeColor, shouldAutoDraft } from "@/lib/utils";
import { Loader2, Send, Save } from "lucide-react";

export default function GmailPage() {
  const [emails, setEmails] = useState<Email[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Email | null>(null);
  const [fileContent, setFileContent] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [draft, setDraft] = useState("");
  const [drafting, setDrafting] = useState(false);
  const [draftSaved, setDraftSaved] = useState(false);

  useEffect(() => {
    api.getEmails().then((r) => { setEmails(r.emails); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const selectEmail = async (em: Email) => {
    setSelected(em);
    setDraft("");
    setDraftSaved(false);
    try {
      const f = await api.getFile(em.filename);
      setFileContent(f.content);
    } catch {
      setFileContent("Could not load email content.");
    }

    const eType = classifyEmailType(em);
    if (shouldAutoDraft(em.priority, eType)) {
      setDrafting(true);
      try {
        const res = await api.aiSuggest(
          `Draft a professional reply to this email. Be concise and actionable.\n\nSubject: ${em.subject}\nFrom: ${em.from}\n\n${em.preview}`,
          "You are a professional email assistant."
        );
        if (res.success && res.response) setDraft(res.response);
      } catch { /* noop */ }
      setDrafting(false);
    }
  };

  const generateReply = async () => {
    if (!selected) return;
    setDrafting(true);
    try {
      const res = await api.aiSuggest(
        `Draft a professional reply to this email. Be concise and actionable.\n\nSubject: ${selected.subject}\nFrom: ${selected.from}\n\n${selected.preview}`,
        "You are a professional email assistant."
      );
      if (res.success && res.response) setDraft(res.response);
    } catch { /* noop */ }
    setDrafting(false);
  };

  const saveDraftToVault = async () => {
    if (!draft.trim() || !selected) return;
    try {
      await api.saveDraft("email_reply", `Re: ${selected.subject}\n\n${draft}`);
      setDraftSaved(true);
    } catch { /* noop */ }
  };

  const filtered = emails.filter((em) => {
    if (priorityFilter !== "all" && em.priority !== priorityFilter) return false;
    if (typeFilter !== "all" && classifyEmailType(em) !== typeFilter) return false;
    return true;
  });

  if (loading) return <div className="p-8"><LoadingSpinner text="Loading emails..." /></div>;

  return (
    <div className="flex h-screen">
      {/* Left: list */}
      <div className="w-96 border-r border-slate-700 flex flex-col">
        <div className="p-4 border-b border-slate-700 space-y-3">
          <h1 className="text-lg font-bold">Gmail</h1>
          <EmailFilters
            priority={priorityFilter}
            type={typeFilter}
            onPriorityChange={setPriorityFilter}
            onTypeChange={setTypeFilter}
          />
          <p className="text-xs text-slate-500">{filtered.length} emails</p>
        </div>
        <div className="flex-1 overflow-y-auto">
          {filtered.map((em) => {
            const eType = classifyEmailType(em);
            return (
              <button
                key={em.filename}
                onClick={() => selectEmail(em)}
                className={`w-full text-left p-3 border-l-2 border-b border-b-slate-700/50 transition-colors hover:bg-slate-700/30 ${
                  selected?.filename === em.filename ? "bg-slate-700/50 " : ""
                }${priorityColor(em.priority)}`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-[10px] px-1.5 py-0.5 rounded ${typeColor(eType)}`}>
                    {eType}
                  </span>
                  {em.priority === "urgent" && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-500/30 text-red-300">URGENT</span>
                  )}
                </div>
                <p className="text-sm font-medium truncate">{em.subject}</p>
                <p className="text-xs text-slate-400 truncate">{em.from}</p>
                <p className="text-xs text-slate-500 truncate mt-0.5">{em.preview?.slice(0, 80)}</p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Right: detail */}
      <div className="flex-1 overflow-y-auto">
        {selected ? (
          <div className="p-6 space-y-4">
            <div>
              <h2 className="text-xl font-bold">{selected.subject}</h2>
              <p className="text-sm text-slate-400">From: {selected.from}</p>
              <p className="text-xs text-slate-500">{selected.date}</p>
            </div>
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 text-sm whitespace-pre-wrap">
              {fileContent}
            </div>

            {/* Draft area */}
            <div className="border-t border-slate-700 pt-4 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-300">Reply Draft</h3>
                {!shouldAutoDraft(selected.priority, classifyEmailType(selected)) && !draft && (
                  <button
                    onClick={generateReply}
                    disabled={drafting}
                    className="flex items-center gap-1 text-xs px-3 py-1.5 bg-purple-600 hover:bg-purple-500 rounded disabled:opacity-50"
                  >
                    {drafting ? <Loader2 className="w-3 h-3 animate-spin" /> : null}
                    Generate Reply
                  </button>
                )}
              </div>
              {drafting && <LoadingSpinner text="AI drafting reply..." />}
              {draft && (
                <>
                  <textarea
                    value={draft}
                    onChange={(e) => { setDraft(e.target.value); setDraftSaved(false); }}
                    rows={6}
                    className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-sm text-slate-200 focus:border-cyan-500 focus:outline-none resize-none"
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={saveDraftToVault}
                      disabled={draftSaved}
                      className="flex items-center gap-1 text-sm px-3 py-1.5 bg-slate-600 hover:bg-slate-500 rounded disabled:opacity-50"
                    >
                      <Save className="w-3.5 h-3.5" />
                      {draftSaved ? "Saved" : "Save Draft"}
                    </button>
                    <button
                      onClick={async () => {
                        if (!selected) return;
                        await api.sendEmail(selected.from, `Re: ${selected.subject}`, draft);
                      }}
                      className="flex items-center gap-1 text-sm px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 rounded"
                    >
                      <Send className="w-3.5 h-3.5" /> Send
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-slate-500">
            Select an email to view
          </div>
        )}
      </div>
    </div>
  );
}
