"use client";
import { Linkedin } from "lucide-react";
import SocialComposer from "@/components/SocialComposer";
import { api } from "@/lib/api";

export default function LinkedInPage() {
  return (
    <div className="p-6 max-w-2xl">
      <div className="flex items-center gap-2 mb-6">
        <Linkedin className="w-5 h-5 text-blue-400" />
        <h1 className="text-2xl font-bold">LinkedIn</h1>
      </div>
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-5">
        <SocialComposer platform="linkedin" maxChars={3000} postFn={api.postLinkedIn} />
      </div>
    </div>
  );
}
