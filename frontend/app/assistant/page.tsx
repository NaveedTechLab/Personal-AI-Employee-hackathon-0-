"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { Bot, Send, Loader2 } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  text: string;
}

export default function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const send = async () => {
    const prompt = input.trim();
    if (!prompt) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text: prompt }]);
    setLoading(true);
    try {
      const res = await api.aiSuggest(prompt, "You are a helpful AI business assistant.");
      setMessages((m) => [
        ...m,
        { role: "assistant", text: res.success ? (res.response || "No response.") : (res.error || "Error") },
      ]);
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", text: `Error: ${e}` }]);
    }
    setLoading(false);
  };

  return (
    <div className="flex flex-col h-screen">
      <div className="p-4 border-b border-slate-700 flex items-center gap-2">
        <Bot className="w-5 h-5 text-cyan-400" />
        <h1 className="text-lg font-bold">AI Assistant</h1>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <p className="text-slate-500 text-sm text-center mt-12">Ask anything about your business...</p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[70%] px-4 py-2 rounded-lg text-sm whitespace-pre-wrap ${
              m.role === "user"
                ? "bg-cyan-600 text-white"
                : "bg-slate-800 border border-slate-700 text-slate-200"
            }`}>
              {m.text}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 flex items-center gap-2 text-sm text-slate-400">
              <Loader2 className="w-4 h-4 animate-spin" /> Thinking...
            </div>
          </div>
        )}
      </div>

      <div className="p-4 border-t border-slate-700">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
            placeholder="Type a message..."
            className="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-sm focus:border-cyan-500 focus:outline-none"
          />
          <button onClick={send} disabled={loading || !input.trim()}
            className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 rounded-lg disabled:opacity-50">
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
