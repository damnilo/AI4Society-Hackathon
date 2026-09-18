"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { DescribeBox } from "@/components/DescribeBox";
import { GROUPS } from "@/lib/catalog";
import { getSavedName } from "@/lib/session";

export default function HomePage() {
  const [name, setName] = useState<string | null>(null);

  useEffect(() => {
    setName(getSavedName());
  }, []);

  return (
    <>
      <h1>Dobrodošli{name ? `, ${name}` : ""}</h1>
      <p className="lede">
        Opišite šta želite da završite. Predložićemo proceduru, šta da ponesete
        i gde da odete. Ne podnosimo zahtev umesto vas i ne pratimo status na
        eUpravi.
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
