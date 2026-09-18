"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { AUTH_EVENT, getSessionUser } from "@/lib/auth";

const links = [
  { href: "/", label: "Početna" },
  { href: "/dokumenta", label: "Dokumenta" },
  { href: "/usluge", label: "Usluge" },
  { href: "/pomoc", label: "Pomoć" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const [label, setLabel] = useState("Prijava");

  useEffect(() => {
    const sync = () => {
      const user = getSessionUser();
      setLabel(user?.name || user?.email || "Prijava");
    };
    sync();
    window.addEventListener(AUTH_EVENT, sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener(AUTH_EVENT, sync);
      window.removeEventListener("storage", sync);
    };
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
            {label}
            <span aria-hidden="true"> ◯</span>
          </Link>
        </div>
        {children}
      </div>
    </div>
  );
}
