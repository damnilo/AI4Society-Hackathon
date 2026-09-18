"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { createCase } from "@/lib/api";

export function DescribeBox({
  heading = "Šta želite da završite?",
  preset = "",
}: {
  heading?: string;
  preset?: string;
}) {
  const router = useRouter();
  const [text, setText] = useState(preset);
  const [busy, setBusy] = useState(false);
  const [fileName, setFileName] = useState("");

  async function submit() {
    const value = text.trim();
    if (!value || busy) return;
    setBusy(true);
    try {
      const result = await createCase(value);
      sessionStorage.setItem(
        "putokaz-case",
        JSON.stringify({ ...result, text: value, fileName }),
      );
      router.push(`/predlozi/${result.case_id}`);
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
            onChange={(e) => setFileName(e.target.files?.[0]?.name ?? "")}
          />
        </label>
        {fileName ? <span className="note">Priloženo: {fileName}</span> : null}
      </div>
    </div>
  );
}

type BrowserSpeech = {
  lang: string;
  start: () => void;
  onresult: ((ev: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
};
