"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getSavedName } from "@/lib/session";

export default function DokumentaPage() {
  const [name, setName] = useState<string | null>(null);

  useEffect(() => {
    setName(getSavedName());
  }, []);

  return (
    <>
      <h1>Dokumenta</h1>
      <p className="lede">
        Ovde će stajati papiri koje sačuvate za sledeći put. Matching radi i
        bez naloga — nalog je samo novčanik.
      </p>

      <div className="panel">
        {name ? (
          <>
            <p>
              Prijavljeni ste kao <strong>{name}</strong>. Lista je prazna —
              backend još nije povezan. Možete da priložite sken uz konkretan
              zahtev na početnoj.
            </p>
            <Link className="btn btn-primary" href="/">
              Priloži uz novi zahtev
            </Link>
          </>
        ) : (
          <>
            <p>
              Niste prijavljeni. Dokumenta se ne čuvaju između poseta. Ako
              želite novčanik, prijavite se (opciono).
            </p>
            <div className="row">
              <Link className="btn btn-primary" href="/prijava">
                Prijava
              </Link>
              <Link className="btn btn-ghost" href="/">
                Nastavi kao gost
              </Link>
            </div>
          </>
        )}
      </div>
    </>
  );
}
