"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { ApiError, createCase } from "@/lib/api";
import { AUTH_EVENT, getSessionUser } from "@/lib/auth";
import {
  accountIsPirot,
  catalogGroupsFor,
  servicesInGroup,
  type GroupId,
} from "@/lib/catalog";
import { clearCaseSession } from "@/lib/session";

function UslugeBody() {
  const params = useSearchParams();
  const router = useRouter();
  const raw = params.get("grupa");
  const [municipality, setMunicipality] = useState<string | null | undefined>(
    undefined,
  );
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const sync = () => setMunicipality(getSessionUser()?.municipality ?? null);
    sync();
    window.addEventListener(AUTH_EVENT, sync);
    return () => window.removeEventListener(AUTH_EVENT, sync);
  }, []);

  useEffect(() => {
    if (municipality === undefined) return;
    if (raw === "pirot" && !accountIsPirot(municipality)) {
      router.replace("/usluge?grupa=dokumenta");
    }
  }, [municipality, raw, router]);

  const groups = catalogGroupsFor(municipality ?? null);
  const group: GroupId =
    raw && groups.some((g) => g.id === raw) ? (raw as GroupId) : "dokumenta";
  const items = servicesInGroup(group);
  const current = groups.find((g) => g.id === group);

  async function start(example: string, slug: string, title: string) {
    if (busy) return;
    setBusy(slug);
    setError("");
    try {
      const result = await createCase(example);
      sessionStorage.setItem(
        "nasalter-case",
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
        {group === "pirot"
          ? " Ove usluge važe za Gradsku upravu Pirot."
          : accountIsPirot(municipality)
            ? ""
            : " Usluge Gradske uprave Pirot nisu na ovoj listi. Ako u opisu na početnoj navedete Pirot, predložićemo ih u rezultatima pretrage."}
      </p>

      <div className="row" style={{ marginBottom: 20 }}>
        {groups.map((g) => (
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
            {current?.title ?? "Ova grupa"} još nije u katalogu.
          </p>
          <p className="note">
            Opišite na početnoj šta treba — ako postoji slična procedura,
            predložićemo je.
          </p>
          <Link className="btn btn-primary" href="/" onClick={clearCaseSession}>
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
