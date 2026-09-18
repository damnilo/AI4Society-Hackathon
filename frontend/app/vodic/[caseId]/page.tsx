"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { fetchGuide } from "@/lib/api";
import { STATUS_LABEL } from "@/lib/labels";
import type { Guide } from "@/lib/types";

function VodicBody() {
  const { caseId } = useParams<{ caseId: string }>();
  const params = useSearchParams();
  const slug = params.get("slug") ?? "licna-karta-zamena";
  const [guide, setGuide] = useState<Guide | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    fetchGuide(caseId, slug)
      .then((g) => {
        if (!cancelled) setGuide(g);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Vodič nije dostupan.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [caseId, slug]);

  if (error) {
    return <p className="alert">{error}</p>;
  }

  if (!guide) {
    return <p>Pripremam vodič…</p>;
  }

  return (
    <>
      <h1>{guide.title}</h1>
      <p className="lede">
        {guide.institution_label}. Ovo je redosled koraka i spisak šta da
        ponesete — nije podnošenje zahteva.
      </p>

      <div className="panel">
        <h2 style={{ marginTop: 0 }}>Koraci</h2>
        <div className="steps">
          {guide.steps.map((s, i) => (
            <div key={s.title} className="step">
              <strong>
                {i + 1}. {s.title}
              </strong>
              <p style={{ margin: "8px 0 0" }}>{s.description}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="panel">
        <h2 style={{ marginTop: 0 }}>Šta da ponesete</h2>
        {guide.documents.map((d) => (
          <div key={d.type} className="doc">
            <div>
              <strong>{d.label}</strong>
              <p className="note" style={{ margin: "6px 0 0" }}>
                {d.how_to_obtain}
                {d.note ? ` ${d.note}` : ""}
              </p>
            </div>
            <span className={`badge ${d.status}`}>{STATUS_LABEL[d.status]}</span>
          </div>
        ))}
        <p className="disclaimer" style={{ marginTop: 18 }}>
          {guide.disclaimer}
        </p>
      </div>

      <div className="panel">
        <h2 style={{ marginTop: 0 }}>Gde da odete</h2>
        {guide.office_missing || !guide.office ? (
          <p>Adresa kancelarije još nije u katalogu za ovaj slučaj.</p>
        ) : (
          <p className="office">
            <strong>{guide.office.name}</strong>
            <br />
            {guide.office.address}
            <br />
            Tel: {guide.office.phone}
          </p>
        )}
        {guide.euprava_url &&
        (guide.channel === "online" || guide.channel === "both") ? (
          <p style={{ marginTop: 16 }}>
            <a
              className="btn btn-primary"
              href={guide.euprava_url}
              target="_blank"
              rel="noreferrer"
            >
              Otvori uslugu na eUpravi
            </a>
          </p>
        ) : null}
      </div>

      <p className="note">
        Izvor:{" "}
        <a href={guide.source_url} target="_blank" rel="noreferrer">
          {guide.source_name}
        </a>
        , provereno {guide.last_verified_at}.
      </p>

      {guide.related.length > 0 ? (
        <p>
          Posle ovoga često treba:{" "}
          {guide.related.map((r) => r.title).join(", ")}.
        </p>
      ) : null}

      <Link className="btn btn-ghost" href="/">
        Nova pretraga
      </Link>
    </>
  );
}

export default function VodicPage() {
  return (
    <Suspense fallback={<p>Učitavanje…</p>}>
      <VodicBody />
    </Suspense>
  );
}
