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
      <section className="hero">
        <h1>Dobrodošli{name ? `, ${name}` : ""}</h1>
        <p className="lede">
          Opišite svojim rečima šta želite da završite. Predložićemo proceduru,
          šta da ponesete i gde da odete. Ne podnosimo zahtev umesto vas.
        </p>
        <div className="hero-steps">
          <span className="hero-step">
            <b>1</b> Opišite nameru
          </span>
          <span className="hero-arrow" aria-hidden="true">
            →
          </span>
          <span className="hero-step">
            <b>2</b> Predložimo proceduru
          </span>
          <span className="hero-arrow" aria-hidden="true">
            →
          </span>
          <span className="hero-step">
            <b>3</b> Idete na šalter
          </span>
        </div>
      </section>

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
