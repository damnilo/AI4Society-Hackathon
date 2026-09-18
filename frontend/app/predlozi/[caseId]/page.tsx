"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { DescribeBox } from "@/components/DescribeBox";
import type { MatchResponse } from "@/lib/types";

type Stored = MatchResponse & { text: string; fileName?: string };

export default function PredloziPage() {
  const { caseId } = useParams<{ caseId: string }>();
  const router = useRouter();
  const [stored, setStored] = useState<Stored | null>(null);
  const [retryOpen, setRetryOpen] = useState(false);

  useEffect(() => {
    const raw = sessionStorage.getItem("putokaz-case");
    if (!raw) {
      router.replace("/");
      return;
    }
    const parsed = JSON.parse(raw) as Stored;
    setStored(parsed);
    setRetryOpen(parsed.need_clarification);
  }, [router]);

  if (!stored) {
    return <p>Učitavanje…</p>;
  }

  return (
    <>
      <h1>Da li je nešto od ovoga?</h1>
      <p className="lede">
        Pisali ste: „{stored.text}“. Izaberite jednu karticu. Institucija i
        adresa dolaze posle izbora — ovde samo procedura.
      </p>

      <div className="cards">
        {stored.candidates.map((c) => (
          <button
            key={c.slug}
            className="card"
            type="button"
            onClick={() => router.push(`/vodic/${caseId}?slug=${c.slug}`)}
          >
            <h2>{c.title}</h2>
            <p>{c.plain_summary}</p>
            <div
              className="score"
              aria-label={`Poklapanje ${Math.round(c.score * 100)} posto`}
            >
              <span style={{ width: `${Math.round(c.score * 100)}%` }} />
            </div>
            <p className="why">Zašto: {c.rationale}</p>
          </button>
        ))}
      </div>

      <div className="panel" style={{ marginTop: 24 }}>
        <button
          className="btn btn-ghost"
          type="button"
          onClick={() => setRetryOpen((v) => !v)}
        >
          Nijedna nije to — dopuni opis
        </button>
        {retryOpen ? (
          <div style={{ marginTop: 18 }}>
            <DescribeBox
              heading="Dopunite ili promenite opis"
              preset={stored.text}
            />
          </div>
        ) : null}
      </div>
    </>
  );
}
