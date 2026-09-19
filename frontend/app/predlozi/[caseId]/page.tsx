"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { ClarifyBox } from "@/components/ClarifyBox";
import { DescribeBox } from "@/components/DescribeBox";
import { ApiError, createCase, fetchCase, isUuid } from "@/lib/api";
import { SERVICES } from "@/lib/catalog";
import type { Candidate, StoredCase } from "@/lib/types";

function withPickedFirst(candidates: Candidate[], pickedSlug?: string): Candidate[] {
  if (!pickedSlug) return candidates;
  const chosen = candidates.find((c) => c.slug === pickedSlug);
  const rest = candidates.filter((c) => c.slug !== pickedSlug);
  if (chosen) return [chosen, ...rest];
  const fromCatalog = SERVICES.find((s) => s.slug === pickedSlug);
  if (!fromCatalog) return candidates;
  return [
    {
      slug: fromCatalog.slug,
      title: fromCatalog.title,
      plain_summary: fromCatalog.summary,
      score: 1,
      rationale: "Ovo ste izabrali sa liste usluga.",
    },
    ...candidates,
  ];
}

export default function PredloziPage() {
  const { caseId } = useParams<{ caseId: string }>();
  const router = useRouter();
  const [stored, setStored] = useState<StoredCase | null>(null);
  const [retryOpen, setRetryOpen] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const raw = sessionStorage.getItem("nasalter-case");
    let cached: StoredCase | null = null;
    if (raw) {
      try {
        const parsed = JSON.parse(raw) as StoredCase;
        if (parsed.case_id === caseId) cached = parsed;
      } catch {
        sessionStorage.removeItem("nasalter-case");
      }
    }
    if (cached) {
      setStored(cached);
      setRetryOpen(cached.need_clarification && cached.source !== "catalog");
    }
    if (!isUuid(caseId)) {
      if (!cached) router.replace("/");
      return;
    }

    async function hydrate() {
      try {
        const row = await fetchCase(caseId);
        if (cancelled) return;
        if (row) {
          const next: StoredCase = {
            ...cached,
            ...row,
            text: row.text || cached?.text || "",
            source: cached?.source ?? "typed",
            fileName: cached?.fileName,
            pickedSlug: cached?.pickedSlug,
            pickedTitle: cached?.pickedTitle,
          };
          sessionStorage.setItem("nasalter-case", JSON.stringify(next));
          setStored(next);
          setRetryOpen(next.need_clarification && next.source !== "catalog");
          return;
        }
        if (!cached) router.replace("/");
      } catch (err) {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 404 && cached?.text) {
          try {
            const result = await createCase(cached.text);
            if (cancelled) return;
            const next: StoredCase = {
              ...result,
              text: cached.text,
              source: cached.source,
              fileName: cached.fileName,
              pickedSlug: cached.pickedSlug,
              pickedTitle: cached.pickedTitle,
            };
            sessionStorage.setItem("nasalter-case", JSON.stringify(next));
            router.replace(`/predlozi/${result.case_id}`);
            return;
          } catch {
            router.replace("/");
            return;
          }
        }
        if (!cached) router.replace("/");
      }
    }
    void hydrate();
    return () => {
      cancelled = true;
    };
  }, [caseId, router]);

  const cards = useMemo(
    () => (stored ? withPickedFirst(stored.candidates, stored.pickedSlug) : []),
    [stored],
  );

  if (!stored) {
    return <p>Učitavanje…</p>;
  }

  const fromCatalog = stored.source === "catalog" && stored.pickedTitle;

  return (
    <>
      <h1>{fromCatalog ? "Potvrdite proceduru" : "Da li je nešto od ovoga?"}</h1>
      <p className="lede">
        {fromCatalog ? (
          <>
            Izabrali ste proceduru „{stored.pickedTitle}“. Ako je to to, kliknite
            tu karticu. Ako je slična druga, izaberite nju. Institucija i adresa
            dolaze posle izbora.
          </>
        ) : (
          <>
            Pisali ste: „{stored.text}“. Izaberite jednu karticu. Institucija i
            adresa dolaze posle izbora — ovde samo procedura.
          </>
        )}
      </p>
      {stored.need_clarification && stored.questions && stored.questions.length > 0 ? (
        <ClarifyBox
          caseId={caseId}
          questions={stored.questions}
          originalText={stored.text}
        />
      ) : null}

      {cards.length === 0 ? (
        <div className="panel">
          <p>
            Nismo sigurni šta treba. Dopunite opis — bez toga ne možemo da
            predložimo proceduru.
          </p>
        </div>
      ) : (
        <div className="cards">
          {cards.map((c) => (
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
              <div className="card-foot">
                <span className="match-pct">
                  Poklapanje {Math.round(c.score * 100)}%
                </span>
                <span className="card-go" aria-hidden="true">
                  Izaberi →
                </span>
              </div>
            </button>
          ))}
        </div>
      )}

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
              heading="Opišite svojim rečima šta treba"
              preset={fromCatalog ? "" : stored.text}
              caseId={caseId}
            />
          </div>
        ) : null}
      </div>
    </>
  );
}
