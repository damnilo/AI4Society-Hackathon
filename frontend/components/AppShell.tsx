"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { getSavedName } from "@/lib/session";

const links = [
  { href: "/", label: "Početna" },
  { href: "/dokumenta", label: "Dokumenta" },
  { href: "/usluge", label: "Usluge" },
  { href: "/pomoc", label: "Pomoć" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const [name, setName] = useState<string | null>(null);

  useEffect(() => {
    setName(getSavedName());
  }, [path]);

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <strong>Putokaz</strong>
          <span>Vodič kroz procedure</span>
        </div>
        <nav className="nav">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={path === l.href ? "active" : ""}
            >
              {l.label}
            </Link>
          ))}
        </nav>
        <div className="side-foot">Nije eUprava. Nije overa papira.</div>
      </aside>
      <div className="main">
        <div className="topbar">
          <span className="note">Velika slova, jedan korak u isto vreme.</span>
          <Link className="guest" href="/prijava">
            {name ?? "Prijava"}
            <span aria-hidden="true"> ◯</span>
          </Link>
        </div>
        {children}
      </div>
    </div>
  );
}
