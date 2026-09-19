"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { AUTH_EVENT, getSessionUser, migrateLegacyKeys } from "@/lib/auth";
import { APP_NAME } from "@/lib/copy";
import { FontSizeControl } from "@/components/FontSizeControl";

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
    migrateLegacyKeys();
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
      <aside className="sidebar no-print">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            ⇢
          </span>
          <strong>{APP_NAME}</strong>
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
        <FontSizeControl />
        <div className="side-foot">Nije eUprava. Nije overa papira.</div>
      </aside>
      <div className="main">
        <div className="topbar no-print">
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
