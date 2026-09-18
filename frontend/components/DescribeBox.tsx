"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { attachCaseDocument, createCase, isUuid, retryCase } from "@/lib/api";

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
  const [file, setFile] = useState<File | null>(null);
  const [note, setNote] = useState("");

  async function submit() {
    const value = text.trim();
    if (!value || busy) return;
    setBusy(true);
    setNote("");
    try {
      const result = caseId
        ? await retryCase(caseId, value)
        : await createCase(value);
      let fileName = file?.name ?? "";
      if (file && isUuid(result.case_id)) {
        const attached = await attachCaseDocument(result.case_id, file);
        if (!attached) {
          setNote("Procedura je nađena, ali prilog nije primljen. Možete da nastavite.");
        }
      } else if (file && !isUuid(result.case_id)) {
        fileName = "";
      }
      sessionStorage.setItem(
        "putokaz-case",
        JSON.stringify({
          ...result,
          text: value,
          fileName,
          source: "typed",
        }),
      );
      const next = `/predlozi/${result.case_id}`;
      if (caseId && result.case_id === caseId) {
        window.location.assign(next);
        return;
      }
      router.push(next);
    } finally {
      setBusy(false);
    }
  }

  function listen() {
    const win = window as Window & {
      webkitSpeechRecognition?: new () => BrowserSpeech;
      SpeechRecognition?: new () => BrowserSpeech;
    };
    const Speech = win.SpeechRecognition ?? win.webkitSpeechRecognition;
    if (!Speech) {
      setText((t) => t || "istekla mi je lična");
      return;
    }
    const rec = new Speech();
    rec.lang = "sr-RS";
    rec.onresult = (ev) => {
      const said = ev.results[0]?.[0]?.transcript ?? "";
      setText((t) => (t ? `${t} ${said}` : said));
    };
    rec.start();
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
        <button className="btn btn-primary" type="button" onClick={submit} disabled={busy}>
          {busy ? "Tražim…" : "Nađi proceduru"}
        </button>
        <button className="btn btn-ghost" type="button" onClick={listen}>
          Reci naglas
        </button>
        <label className="file">
          Priloži papir (nije obavezno)
          <input
            type="file"
            accept="image/*,.pdf"
            hidden
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </label>
        {file ? <span className="note">Priloženo: {file.name}</span> : null}
      </div>
      <p className="note" style={{ marginBottom: 0 }}>
        Prijava nije potrebna. Prilog ide uz ovaj zahtev. Da sačuvate sken za
        sledeći put, otvorite Dokumenta posle prijave.
      </p>
      {note ? <p className="alert">{note}</p> : null}
    </div>
  );
}

type BrowserSpeech = {
  lang: string;
  start: () => void;
  onresult: ((ev: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
};
