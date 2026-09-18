"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { ApiError, fetchCase, fetchGuide, retryCase } from "@/lib/api";
import { STATUS_LABEL } from "@/lib/labels";
import type { Guide, StoredCase } from "@/lib/types";

function readStoredText(caseId: string): string {
  if (typeof window === "undefined") return "";
  const raw = sessionStorage.getItem("putokaz-case");
  if (!raw) return "";
  try {
    const parsed = JSON.parse(raw) as StoredCase;
    return parsed.case_id === caseId ? parsed.text : "";
  } catch {
    return "";
  }
}

function VodicBody() {
  const { caseId } = useParams<{ caseId: string }>();
  const params = useSearchParams();
  const slug = params.get("slug") ?? "licna-karta-zamena";
  const [guide, setGuide] = useState<Guide | null>(null);
  const [error, setError] = useState("");
  const [place, setPlace] = useState("");
  const [placeBusy, setPlaceBusy] = useState(false);
  const [placeNote, setPlaceNote] = useState("");

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

  async function submitPlace() {
    const city = place.trim();
    if (!city || placeBusy) return;
    setPlaceBusy(true);
    setPlaceNote("");
    try {
      const stored = readStoredText(caseId);
      const loaded = stored || (await fetchCase(caseId))?.text || "";
      const nextText = loaded.includes(city) ? loaded : `${loaded}\n${city}`.trim();
      if (!nextText) {
        setPlaceNote("Unesite mesto, npr. Pirot ili Beograd.");
        return;
      }
      const result = await retryCase(caseId, nextText);
      sessionStorage.setItem(
        "putokaz-case",
        JSON.stringify({
          ...result,
          text: nextText,
          source: "typed",
        }),
      );
      const nextGuide = await fetchGuide(caseId, slug);
      setGuide(nextGuide);
      if (nextGuide.office_missing || !nextGuide.office) {
        setPlaceNote("To mesto još nije u katalogu šaltera. Probajte Pirot, Beograd ili Niš.");
      } else {
        setPlace("");
      }
    } catch (err) {
      setPlaceNote(err instanceof ApiError ? err.message : "Nismo uspeli da nađemo šalter.");
    } finally {
      setPlaceBusy(false);
    }
  }

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
          <>
            <p>
              Nismo mogli da odredimo šalter — u tekstu nema mesta. Unesite grad
              ili opštinu. Ulicu ne izmišljamo.
            </p>
            <label className="big" htmlFor="mesto">
              U kom mestu ste?
              <input
                id="mesto"
                className="describe"
                value={place}
                onChange={(e) => setPlace(e.target.value)}
                placeholder="Npr. Pirot"
              />
            </label>
            <div className="row">
              <button
                className="btn btn-primary"
                type="button"
                onClick={() => void submitPlace()}
                disabled={placeBusy}
              >
                {placeBusy ? "Tražim šalter…" : "Nađi adresu"}
              </button>
            </div>
            {placeNote ? <p className="alert">{placeNote}</p> : null}
          </>
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
