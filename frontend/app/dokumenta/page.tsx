"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { getAccessToken, getSessionUser } from "@/lib/auth";
import {
  ApiError,
  deleteWalletDocument,
  listWalletDocuments,
  uploadWalletDocument,
} from "@/lib/api";
import type { WalletDocument } from "@/lib/types";

export default function DokumentaPage() {
  const [ready, setReady] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);
  const [docs, setDocs] = useState<WalletDocument[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setError("");
    try {
      setDocs(await listWalletDocuments());
    } catch (err) {
      setDocs([]);
      setError(err instanceof ApiError ? err.message : "Lista dokumenata nije dostupna.");
      if (err instanceof ApiError && err.status === 401) {
        setLoggedIn(false);
      }
    }
  }, []);

  useEffect(() => {
    const token = getAccessToken();
    setLoggedIn(Boolean(token && getSessionUser()));
    setReady(true);
    if (token) {
      void load();
    }
  }, [load]);

  async function onUpload(file: File | undefined) {
    if (!file || busy) return;
    setBusy(true);
    setError("");
    try {
      const saved = await uploadWalletDocument(file);
      setDocs((current) => [saved, ...current]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Otpremanje nije uspelo.");
    } finally {
      setBusy(false);
    }
  }

  async function onDelete(id: string) {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      await deleteWalletDocument(id);
      setDocs((current) => current.filter((doc) => doc.id !== id));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Brisanje nije uspelo.");
    } finally {
      setBusy(false);
    }
  }

  if (!ready) {
    return <p>Učitavanje…</p>;
  }

  return (
    <>
      <h1>Dokumenta</h1>
      <p className="lede">
        Novčanik skenova za sledeći put. Traženje procedure radi i bez naloga.
      </p>

      {!loggedIn ? (
        <div className="panel">
          <p>
            Niste prijavljeni. Papiri se ne čuvaju između poseta. Možete da
            priložite sken uz konkretan zahtev na početnoj, kao gost.
          </p>
          <div className="row">
            <Link className="btn btn-primary" href="/prijava">
              Prijava
            </Link>
            <Link className="btn btn-ghost" href="/">
              Nastavi kao gost
            </Link>
          </div>
        </div>
      ) : (
        <div className="panel">
          <div className="row" style={{ marginTop: 0 }}>
            <label className="file">
              {busy ? "Otpremanje…" : "Dodaj sken"}
              <input
                type="file"
                accept="image/*,.pdf"
                hidden
                disabled={busy}
                onChange={(e) => {
                  const chosen = e.target.files?.[0];
                  e.target.value = "";
                  void onUpload(chosen);
                }}
              />
            </label>
          </div>

          {error ? <p className="alert">{error}</p> : null}

          {docs.length === 0 ? (
            <p className="note">Još nema sačuvanih papira.</p>
          ) : (
            docs.map((doc) => (
              <div key={doc.id} className="doc">
                <div>
                  <strong>{doc.original_filename}</strong>
                  <p className="note" style={{ margin: "6px 0 0" }}>
                    {doc.content_type || "fajl"}
                    {doc.status ? ` · ${doc.status}` : ""}
                  </p>
                </div>
                <button
                  className="btn btn-ghost"
                  type="button"
                  disabled={busy}
                  onClick={() => void onDelete(doc.id)}
                >
                  Obriši
                </button>
              </div>
            ))
          )}
        </div>
      )}

      <p className="disclaimer">
        Skenovi ostaju na vašem nalogu dok ih ne obrišete. Ovo nije overa da je
        dokument originalan, niti slanje na eUpravu.
      </p>
    </>
  );
}
