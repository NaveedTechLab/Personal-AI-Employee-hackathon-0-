"use client";
import { useState } from "react";
import { Sparkles, Save, Send, Loader2 } from "lucide-react";
import { api } from "@/lib/api";

interface Props {
  platform: "twitter" | "linkedin";
  maxChars: number;
  postFn: (text: string) => Promise<{ success: boolean; error?: string }>;
}

export default function SocialComposer({ platform, maxChars, postFn }: Props) {
  const [topic, setTopic] = useState("");
  const [content, setContent] = useState("");
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [posting, setPosting] = useState(false);
  const [message, setMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);

  const generate = async () => {
    setGenerating(true);
    setMessage(null);
    try {
      const res = await api.generatePost(platform, topic);
      if (res.success && res.content) {
        setContent(res.content);
      } else {
        setMessage({ text: res.error || "Generation failed", type: "error" });
      }
    } catch (e) {
      setMessage({ text: String(e), type: "error" });
    }
    setGenerating(false);
  };

  const saveDraft = async () => {
    if (!content.trim()) return;
    setSaving(true);
    try {
      const res = await api.saveDraft(platform, content);
      if (res.success) {
        setMessage({ text: `Draft saved: ${res.filename}`, type: "success" });
      } else {
        setMessage({ text: "Save failed", type: "error" });
      }
    } catch (e) {
      setMessage({ text: String(e), type: "error" });
    }
    setSaving(false);
  };

  const post = async () => {
    if (!content.trim()) return;
    setPosting(true);
    try {
      const res = await postFn(content);
      if (res.success) {
        setMessage({ text: "Posted successfully!", type: "success" });
        setContent("");
      } else {
        setMessage({ text: res.error || "Post failed", type: "error" });
      }
    } catch (e) {
      setMessage({ text: String(e), type: "error" });
    }
    setPosting(false);
  };

  const charCount = content.length;
  const overLimit = charCount > maxChars;

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm text-slate-400 mb-1">Topic (optional)</label>
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="e.g. AI productivity, tech trends..."
          className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-sm text-slate-200 focus:border-cyan-500 focus:outline-none"
        />
      </div>

      <div>
        <div className="flex justify-between items-center mb-1">
          <label className="text-sm text-slate-400">Post Content</label>
          <span className={`text-xs ${overLimit ? "text-red-400" : "text-slate-500"}`}>
            {charCount}/{maxChars}
          </span>
        </div>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          rows={6}
          placeholder={`Write your ${platform} post...`}
          className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-2 text-sm text-slate-200 focus:border-cyan-500 focus:outline-none resize-none"
        />
      </div>

      <div className="flex gap-2">
        <button
          onClick={generate}
          disabled={generating}
          className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 rounded text-sm font-medium transition-colors"
        >
          {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          AI Generate
        </button>
        <button
          onClick={saveDraft}
          disabled={saving || !content.trim()}
          className="flex items-center gap-2 px-4 py-2 bg-slate-600 hover:bg-slate-500 disabled:opacity-50 rounded text-sm font-medium transition-colors"
        >
          {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
          Save Draft
        </button>
        <button
          onClick={post}
          disabled={posting || !content.trim() || overLimit}
          className="flex items-center gap-2 px-4 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 rounded text-sm font-medium transition-colors"
        >
          {posting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          Post
        </button>
      </div>

      {message && (
        <div className={`text-sm px-3 py-2 rounded ${
          message.type === "success" ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
        }`}>
          {message.text}
        </div>
      )}
    </div>
  );
}
