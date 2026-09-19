"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { ApiError, createCase } from "@/lib/api";
import { GROUPS, servicesInGroup, type GroupId } from "@/lib/catalog";

function isGroup(value: string | null): value is GroupId {
  return GROUPS.some((g) => g.id === value);
}

function UslugeBody() {
  const params = useSearchParams();
  const router = useRouter();
  const raw = params.get("grupa");
  const group: GroupId = isGroup(raw) ? raw : "dokumenta";
  const items = servicesInGroup(group);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");
  const current = GROUPS.find((g) => g.id === group);

  async function start(example: string, slug: string, title: string) {
    if (busy) return;
    setBusy(slug);
    setError("");
    try {
      const result = await createCase(example);
      sessionStorage.setItem(
        "putokaz-case",
        JSON.stringify({
          ...result,
          text: example,
          fileName: "",
          source: "catalog",
          pickedTitle: title,
          pickedSlug: slug,
        }),
      );
      router.push(`/vodic/${result.case_id}?slug=${encodeURIComponent(slug)}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Matching nije uspeo.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <h1>Usluge</h1>
      <p className="lede">
        Izaberite grupu, pa stavku. Ako niste sigurni, vratite se na početnu i
        opišite svojim rečima.
      </p>

      <div className="row" style={{ marginBottom: 20 }}>
        {GROUPS.map((g) => (
          <Link
            key={g.id}
            className={`btn ${g.id === group ? "btn-primary" : "btn-ghost"}`}
            href={`/usluge?grupa=${g.id}`}
          >
            {g.title}
          </Link>
        ))}
      </div>

      {error ? <p className="alert">{error}</p> : null}

      {items.length === 0 ? (
        <div className="panel">
          <p>
            {current?.title ?? "Ova grupa"} još nije u katalogu. Nema praćenja
            računa ni zakazivanja kod komunalnih preduzeća.
          </p>
          <p className="note">
            Opišite na početnoj šta treba — ako postoji slična procedura,
            predložićemo je.
          </p>
          <Link className="btn btn-primary" href="/">
            Nazad na početnu
          </Link>
        </div>
      ) : (
        <div className="cards">
          {items.map((s) => (
            <article key={s.slug} className="panel" style={{ margin: 0 }}>
              <h2>{s.title}</h2>
              <p className="note">{s.summary}</p>
              <button
                className="btn btn-primary"
                type="button"
                disabled={busy === s.slug}
                onClick={() => start(s.example, s.slug, s.title)}
              >
                {busy === s.slug ? "Otvaram vodič…" : "Ovo mi treba"}
              </button>
            </article>
          ))}
        </div>
      )}
    </>
  );
}

export default function UslugePage() {
  return (
    <Suspense fallback={<p>Učitavanje…</p>}>
      <UslugeBody />
    </Suspense>
  );
}
