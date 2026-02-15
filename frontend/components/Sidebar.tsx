"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Mail, Twitter, Linkedin,
  MessageCircle, Database, CheckSquare, FolderOpen, Bot,
} from "lucide-react";

const links = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/gmail", label: "Gmail", icon: Mail },
  { href: "/twitter", label: "Twitter", icon: Twitter },
  { href: "/linkedin", label: "LinkedIn", icon: Linkedin },
  { href: "/whatsapp", label: "WhatsApp", icon: MessageCircle },
  { href: "/odoo", label: "Odoo ERP", icon: Database },
  { href: "/approvals", label: "Approvals", icon: CheckSquare },
  { href: "/vault", label: "Vault", icon: FolderOpen },
  { href: "/assistant", label: "AI Assistant", icon: Bot },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 bg-slate-800 border-r border-slate-700 flex flex-col min-h-screen">
      <div className="p-4 border-b border-slate-700">
        <h1 className="text-lg font-bold text-cyan-400">AI Employee</h1>
        <p className="text-xs text-slate-500">Personal Dashboard</p>
      </div>
      <nav className="flex-1 py-2">
        {links.map(({ href, label, icon: Icon }) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                active
                  ? "text-cyan-400 bg-cyan-500/10 border-r-2 border-cyan-400"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-700/50"
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="p-3 border-t border-slate-700 text-xs text-slate-600">
        v1.0 &middot; Port 9000
      </div>
    </aside>
  );
}
