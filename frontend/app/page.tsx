"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AUTH_EVENT, getSessionUser } from "@/lib/auth";
import { GROUPS } from "@/lib/catalog";
import { DescribeBox } from "@/components/DescribeBox";

export default function HomePage() {
  const [name, setName] = useState<string | null>(null);

  useEffect(() => {
    const sync = () => {
      const user = getSessionUser();
      setName(user?.name || null);
    };
    sync();
    window.addEventListener(AUTH_EVENT, sync);
    return () => window.removeEventListener(AUTH_EVENT, sync);
  }, []);

  return (
    <>
      <h1>Dobrodošli{name ? `, ${name}` : ""}</h1>
      <p className="lede">
        Opišite šta želite da završite. Predložićemo proceduru, šta da ponesete
        i gde da odete. Ne podnosimo zahtev umesto vas. Nalog je opciono — samo
        ako želite da sačuvate skenove.
      </p>

      <DescribeBox />

      <h2 style={{ fontSize: "1.35rem", margin: "8px 0 14px" }}>
        Brzi pristup
      </h2>
      <div className="tiles">
        {GROUPS.map((g) => (
          <Link key={g.id} className="tile" href={`/usluge?grupa=${g.id}`}>
            <strong>{g.title}</strong>
            <span>{g.hint}</span>
          </Link>
        ))}
      </div>
    </>
  );
}
