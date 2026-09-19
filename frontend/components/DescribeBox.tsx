"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import {
  attachCaseDocument,
  createCase,
  isUuid,
  listWalletDocuments,
  retryCase,
} from "@/lib/api";
import { AUTH_EVENT, getAccessToken, getSessionUser } from "@/lib/auth";
import { documentLabel, STATUS_LABEL } from "@/lib/labels";
import type { DocumentStatus, MatchResponse, WalletDocument } from "@/lib/types";

const ACCEPT = ".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf";

function isAllowedFile(file: File): boolean {
  const name = file.name.toLowerCase();
  return (
    file.type === "image/jpeg" ||
    file.type === "image/png" ||
    file.type === "application/pdf" ||
    name.endsWith(".jpg") ||
    name.endsWith(".jpeg") ||
    name.endsWith(".png") ||
    name.endsWith(".pdf")
  );
}

export function DescribeBox({
  heading = "Šta želite da završite?",
  preset = "",
  caseId,
}: {
  heading?: string;
  preset?: string;
  caseId?: string;
}) {
  const router = useRouter();
  const [text, setText] = useState(preset);
  const [busy, setBusy] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [wallet, setWallet] = useState<WalletDocument[]>([]);
  const [pickedWallet, setPickedWallet] = useState<string[]>([]);
  const [loggedIn, setLoggedIn] = useState(false);
  const [note, setNote] = useState("");
  const [pendingPath, setPendingPath] = useState<string | null>(null);
  const [listening, setListening] = useState(false);
  const recRef = useRef<BrowserSpeech | null>(null);

  useEffect(() => {
    function sync() {
      const ok = Boolean(getAccessToken() && getSessionUser());
      setLoggedIn(ok);
      if (!ok) {
        setWallet([]);
        setPickedWallet([]);
        return;
      }
      void listWalletDocuments()
        .then(setWallet)
        .catch(() => {
          setWallet([]);
        });
    }
    sync();
    window.addEventListener(AUTH_EVENT, sync);
    return () => window.removeEventListener(AUTH_EVENT, sync);
  }, []);

  useEffect(() => {
    return () => {
      recRef.current?.stop();
    };
  }, []);

  function persist(result: MatchResponse, value: string, fileName: string) {
    sessionStorage.setItem(
      "nasalter-case",
      JSON.stringify({
        ...result,
        text: value,
        fileName,
        source: "typed",
      }),
    );
  }

  function go(path: string) {
    if (caseId && path === `/predlozi/${caseId}`) {
      window.location.assign(path);
      return;
    }
    router.push(path);
  }

  function addFiles(list: FileList | null) {
    if (!list) return;
    const next = [...files];
    for (const file of Array.from(list)) {
      if (!isAllowedFile(file)) {
        setNote("Samo JPG, PNG ili PDF.");
        continue;
      }
      if (next.some((item) => item.name === file.name && item.size === file.size)) continue;
      next.push(file);
    }
    setFiles(next);
  }

  async function submit() {
    const value = text.trim();
    if (!value || busy) return;
    setBusy(true);
    setNote("");
    setPendingPath(null);
    try {
      const walletIds = loggedIn && !caseId ? pickedWallet : [];
      let result = caseId
        ? await retryCase(caseId, value)
        : await createCase(value, walletIds);
      const names: string[] = [];
      let attachFailed = false;
      if (isUuid(result.case_id)) {
        for (const file of files) {
          const attached = await attachCaseDocument(result.case_id, file);
          if (attached) names.push(file.name);
          else attachFailed = true;
        }
        if (names.length > 0) {
          result = await retryCase(result.case_id, value);
        }
      }
      persist(result, value, names.join(", "));
      const next = `/predlozi/${result.case_id}`;
      if (attachFailed) {
        setNote("Procedura je nađena, ali neki prilog nije primljen. Ostajete ovde dok ne nastavite.");
        setPendingPath(next);
        return;
      }
      go(next);
    } catch (err) {
      setNote(
        err instanceof Error
          ? err.message
          : "Matching nije uspeo. Proverite da li API radi na localhost:8000.",
      );
    } finally {
      setBusy(false);
    }
  }

  function listen() {
    if (listening) {
      recRef.current?.stop();
      setListening(false);
      return;
    }
    const win = window as Window & {
      webkitSpeechRecognition?: new () => BrowserSpeech;
      SpeechRecognition?: new () => BrowserSpeech;
    };
    const Speech = win.SpeechRecognition ?? win.webkitSpeechRecognition;
    if (!Speech) {
      setNote("Glas nije dostupan u ovom pregledaču. Ukucajte šta treba.");
      return;
    }
    setNote("");
    const rec = new Speech();
    recRef.current = rec;
    rec.lang = "sr-RS";
    rec.onresult = (ev) => {
      const said = ev.results[0]?.[0]?.transcript ?? "";
      setText((t) => (t ? `${t} ${said}` : said));
    };
    rec.onerror = () => {
      setListening(false);
      recRef.current = null;
      setNote("Glas nije uspeo. Ukucajte šta treba.");
    };
    rec.onend = () => {
      setListening(false);
      recRef.current = null;
    };
    try {
      rec.start();
      setListening(true);
    } catch {
      setListening(false);
      recRef.current = null;
      setNote("Glas nije dostupan u ovom pregledaču. Ukucajte šta treba.");
    }
  }

  return (
    <div className="panel">
      <label className="big" htmlFor="opis">
        {heading}
      </label>
      <textarea
        id="opis"
        className="describe"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Npr. selim se iz Pirota u Beograd, ili: istekla mi je lična"
      />
      <div className="row">
        <button className="btn btn-primary" type="button" onClick={() => void submit()} disabled={busy}>
          {busy ? "Tražim u katalogu…" : "Nađi proceduru"}
        </button>
        <button className="btn btn-ghost" type="button" onClick={listen}>
          {listening ? "Slušam…" : "Reci naglas"}
        </button>
        <label className="file">
          Priloži papire (nije obavezno)
          <input
            type="file"
            accept={ACCEPT}
            multiple
            hidden
            onChange={(e) => {
              addFiles(e.target.files);
              e.target.value = "";
            }}
          />
        </label>
      </div>
      {files.length > 0 ? (
        <ul className="note" style={{ marginTop: 14 }}>
          {files.map((file, index) => (
            <li key={`${file.name}-${file.size}-${index}`}>
              {file.name}{" "}
              <button
                className="btn btn-ghost"
                type="button"
                style={{ padding: "4px 10px", fontSize: "1rem" }}
                onClick={() => setFiles((current) => current.filter((_, i) => i !== index))}
              >
                X
              </button>
            </li>
          ))}
        </ul>
      ) : null}
      {loggedIn && wallet.length > 0 && !caseId ? (
        <div style={{ marginTop: 18 }}>
          <p className="note">Sačuvano u novčaniku — štiklirajte šta ide uz ovaj zahtev:</p>
          {wallet.map((doc) => {
            const checked = pickedWallet.includes(doc.id);
            return (
              <label key={doc.id} className="note" style={{ display: "block", marginBottom: 8 }}>
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => {
                    setPickedWallet((current) =>
                      checked ? current.filter((id) => id !== doc.id) : [...current, doc.id],
                    );
                  }}
                />{" "}
                {walletLine(doc)}
              </label>
            );
          })}
        </div>
      ) : null}
      <p className="note" style={{ marginBottom: 0 }}>
        Prijava nije potrebna. Prilozi idu uz ovaj zahtev, posle teksta. Da
        sačuvate sken za sledeći put, otvorite Dokumenta posle prijave.
      </p>
      {note ? <p className="alert">{note}</p> : null}
      {pendingPath ? (
        <div className="row">
          <button className="btn btn-primary" type="button" onClick={() => go(pendingPath)}>
            Nastavi bez priloga
          </button>
        </div>
      ) : null}
    </div>
  );
}

function walletLine(doc: WalletDocument): string {
  const parts: string[] = [doc.original_filename];
  if (doc.extracted_type) parts.push(documentLabel(doc.extracted_type));
  if (doc.extracted_expiry) parts.push(`važi do ${doc.extracted_expiry}`);
  if (doc.status && doc.status in STATUS_LABEL) {
    parts.push(STATUS_LABEL[doc.status as DocumentStatus]);
  }
  return parts.join(" · ");
}

type BrowserSpeech = {
  lang: string;
  start: () => void;
  stop: () => void;
  onresult: ((ev: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
};
