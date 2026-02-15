"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import LoadingSpinner from "@/components/LoadingSpinner";
import { MessageCircle, Play, PlusCircle } from "lucide-react";

export default function WhatsAppPage() {
  const [messages, setMessages] = useState<{ filename: string; sender: string; text: string; priority: string; created: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState<string | null>(null);
  const [testSender, setTestSender] = useState("");
  const [testText, setTestText] = useState("");

  const load = async () => {
    try {
      const r = await api.getWhatsApp();
      setMessages(r.messages || []);
    } catch { /* noop */ }
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const process = async (filename: string) => {
    setProcessing(filename);
    await api.processWhatsApp(filename);
    await load();
    setProcessing(null);
  };

  const sendTest = async () => {
    if (!testSender.trim() || !testText.trim()) return;
    await api.testWhatsApp(testSender, testText);
    setTestSender("");
    setTestText("");
    await load();
  };

  if (loading) return <div className="p-8"><LoadingSpinner /></div>;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-2">
        <MessageCircle className="w-5 h-5 text-green-400" />
        <h1 className="text-2xl font-bold">WhatsApp</h1>
      </div>

      {/* Test message */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 space-y-3">
        <h3 className="text-sm font-semibold text-slate-300">Send Test Message</h3>
        <div className="flex gap-2">
          <input value={testSender} onChange={(e) => setTestSender(e.target.value)} placeholder="Sender"
            className="bg-slate-700 border border-slate-600 rounded px-3 py-1.5 text-sm flex-1 focus:border-cyan-500 focus:outline-none" />
          <input value={testText} onChange={(e) => setTestText(e.target.value)} placeholder="Message text"
            className="bg-slate-700 border border-slate-600 rounded px-3 py-1.5 text-sm flex-[2] focus:border-cyan-500 focus:outline-none" />
          <button onClick={sendTest} className="flex items-center gap-1 px-3 py-1.5 bg-green-600 hover:bg-green-500 rounded text-sm">
            <PlusCircle className="w-4 h-4" /> Create
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="space-y-2">
        {messages.length === 0 && <p className="text-slate-500 text-sm">No WhatsApp messages.</p>}
        {messages.map((m) => (
          <div key={m.filename} className="bg-slate-800 border border-slate-700 rounded-lg p-4 flex items-start gap-4">
            <div className="flex-1">
              <p className="text-sm font-medium">{m.sender}</p>
              <p className="text-sm text-slate-400">{m.text}</p>
              <p className="text-xs text-slate-500 mt-1">{m.created} &middot; {m.priority}</p>
            </div>
            <button
              onClick={() => process(m.filename)}
              disabled={processing === m.filename}
              className="flex items-center gap-1 px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 rounded text-sm disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5" /> Process
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
