"use client";
import { Twitter } from "lucide-react";
import SocialComposer from "@/components/SocialComposer";
import { api } from "@/lib/api";

export default function TwitterPage() {
  return (
    <div className="p-6 max-w-2xl">
      <div className="flex items-center gap-2 mb-6">
        <Twitter className="w-5 h-5 text-sky-400" />
        <h1 className="text-2xl font-bold">Twitter</h1>
      </div>
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-5">
        <SocialComposer platform="twitter" maxChars={280} postFn={api.postTwitter} />
      </div>
    </div>
  );
}
