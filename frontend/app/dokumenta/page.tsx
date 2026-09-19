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
import { DISCLAIMER } from "@/lib/copy";
import { documentLabel, STATUS_LABEL } from "@/lib/labels";
import { clearCaseSession } from "@/lib/session";
import type { DocumentStatus, WalletDocument } from "@/lib/types";

function walletCaption(doc: WalletDocument): { title: string; detail: string } {
  const title = doc.extracted_type
    ? documentLabel(doc.extracted_type)
    : doc.original_filename;
  const parts: string[] = [];
  if (doc.extracted_type) parts.push(doc.original_filename);
  if (doc.extracted_expiry) parts.push(`važi do ${doc.extracted_expiry}`);
  if (doc.status && doc.status in STATUS_LABEL) {
    parts.push(STATUS_LABEL[doc.status as DocumentStatus]);
  }
  if (doc.purge_at) parts.push("gostov prilog, preuzet u nalog");
  if (parts.length === 0) parts.push(doc.content_type || "fajl");
  return { title, detail: parts.join(" · ") };
}

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
            <Link className="btn btn-ghost" href="/" onClick={clearCaseSession}>
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
            docs.map((doc) => {
              const caption = walletCaption(doc);
              return (
                <div key={doc.id} className="doc">
                  <div>
                    <strong>{caption.title}</strong>
                    <p className="note" style={{ margin: "6px 0 0" }}>
                      {caption.detail}
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
              );
            })
          )}
        </div>
      )}

      <p className="disclaimer">
        {DISCLAIMER} Skenovi na nalogu ostaju dok ih ne obrišete. Prilog gosta
        uz zahtev se briše posle 48 sati ako se nalogom ne preuzme.
      </p>
    </>
  );
}
