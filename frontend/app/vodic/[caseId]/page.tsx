"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";
import {
  ApiError,
  attachCaseDocument,
  fetchCase,
  fetchGuide,
  fetchGuideSpeech,
  refreshGuideDocuments,
  retryCase,
} from "@/lib/api";
import { formatScanExpiry, STATUS_LABEL } from "@/lib/labels";
import type { Guide, RequiredDoc, StoredCase } from "@/lib/types";

const SCAN_PENDING = "Provera skena";
const ACCEPT = ".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf";
const TTS_DISCLAIMER = "Putokaz nije eUprava i ne overava dokumenta.";

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

function awaitingScan(docs: RequiredDoc[]): boolean {
  return docs.some((doc) => (doc.note ?? "").includes(SCAN_PENDING));
}

function needsPlaceQuestion(guide: Guide): boolean {
  return (
    (guide.office_missing || !guide.office) &&
    (guide.office_missing_reason || "").includes("Nedostaje mesto")
  );
}

function guideSpeechText(guide: Guide): string {
  const parts: string[] = [guide.title];
  guide.steps.forEach((step, index) => {
    parts.push(`Korak ${index + 1}. ${step.title}. ${step.description}`);
  });
  if (guide.office) {
    parts.push(
      `Šalter: ${guide.office.name}, ${guide.office.address}. Telefon ${guide.office.phone}.`,
    );
  }
  const missing = guide.documents.filter((doc) => doc.status !== "complete");
  if (missing.length > 0) {
    parts.push(`Šta fali: ${missing.map((doc) => doc.label).join(", ")}.`);
  }
  parts.push(TTS_DISCLAIMER);
  return parts.join(" ");
}

function pickReadableVoice(voices: SpeechSynthesisVoice[]): {
  voice: SpeechSynthesisVoice | null;
  kind: "sr" | "south" | "other";
} {
  const sr =
    voices.find((voice) => {
      const lang = voice.lang.toLowerCase();
      const name = voice.name.toLowerCase();
      return (
        lang.startsWith("sr") ||
        lang.includes("sr-") ||
        name.includes("serbian") ||
        name.includes("srpski")
      );
    }) ?? null;
  if (sr) return { voice: sr, kind: "sr" };
  const south =
    voices.find((voice) => {
      const lang = voice.lang.toLowerCase();
      return lang.startsWith("hr") || lang.startsWith("bs") || lang.startsWith("sl");
    }) ?? null;
  if (south) return { voice: south, kind: "south" };
  return { voice: voices[0] ?? null, kind: "other" };
}

function loadVoices(): Promise<SpeechSynthesisVoice[]> {
  const synth = window.speechSynthesis;
  const existing = synth.getVoices();
  if (existing.length > 0) return Promise.resolve(existing);
  return new Promise((resolve) => {
    const finish = () => resolve(synth.getVoices());
    synth.addEventListener("voiceschanged", finish, { once: true });
    window.setTimeout(finish, 600);
  });
}

function DocRow({ doc }: { doc: RequiredDoc }) {
  const expiry = formatScanExpiry(doc.extracted_expiry);
  const showHow = doc.status === "missing" && doc.how_to_obtain;
  const showNote = doc.status !== "complete" && Boolean(doc.note);
  const showExpiry = Boolean(expiry) && !(doc.note && expiry && doc.note.includes(doc.extracted_expiry ?? ""));
  return (
    <div className="doc">
      <div>
        <strong>{doc.label}</strong>
        {showNote ? (
          <p className="note" style={{ margin: "6px 0 0" }}>
            {doc.note}
          </p>
        ) : null}
        {showHow ? (
          <p className="note" style={{ margin: "6px 0 0" }}>
            {doc.how_to_obtain}
          </p>
        ) : null}
        {showExpiry ? (
          <p className="note" style={{ margin: "6px 0 0" }}>
            {expiry}
          </p>
        ) : null}
      </div>
      <span className={`badge ${doc.status}`}>{STATUS_LABEL[doc.status]}</span>
    </div>
  );
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
  const [attachNote, setAttachNote] = useState("");
  const [attachBusy, setAttachBusy] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [speechLoading, setSpeechLoading] = useState(false);
  const [speechNote, setSpeechNote] = useState("");
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const objectUrlRef = useRef<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  function releaseAudio() {
    abortRef.current?.abort();
    abortRef.current = null;
    const audio = audioRef.current;
    if (audio) {
      audio.onended = null;
      audio.onerror = null;
      audio.pause();
      audio.removeAttribute("src");
      audio.load();
      audioRef.current = null;
    }
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
    }
    window.speechSynthesis?.cancel();
  }

  useEffect(() => {
    return () => {
      releaseAudio();
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    fetchGuide(caseId, slug)
      .then(async (g) => {
        if (cancelled) return;
        setGuide(g);
        if (!awaitingScan(g.documents)) return;
        await new Promise((resolve) => window.setTimeout(resolve, 2000));
        if (cancelled) return;
        const next = await refreshGuideDocuments(g, caseId);
        if (!cancelled) setGuide(next);
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

  async function onAttach(file: File | undefined) {
    if (!file || attachBusy || !guide) return;
    setAttachBusy(true);
    setAttachNote("");
    try {
      const saved = await attachCaseDocument(caseId, file);
      if (!saved) {
        setAttachNote("Prilog nije primljen. Možete da nastavite bez njega.");
        return;
      }
      let next = await refreshGuideDocuments(guide, caseId);
      setGuide(next);
      if (awaitingScan(next.documents)) {
        await new Promise((resolve) => window.setTimeout(resolve, 2000));
        next = await refreshGuideDocuments(next, caseId);
        setGuide(next);
      }
    } catch (err) {
      setAttachNote(err instanceof Error ? err.message : "Prilog nije primljen.");
    } finally {
      setAttachBusy(false);
    }
  }

  async function speakWithBrowser(current: Guide) {
    if (!window.speechSynthesis) {
      setSpeechLoading(false);
      setSpeaking(false);
      setSpeechNote("Glas nije dostupan. Pročitajte vodič na ekranu.");
      return;
    }
    const voices = await loadVoices();
    const picked = pickReadableVoice(voices);
    setSpeechNote(
      picked.kind === "sr"
        ? "Serverski glas nije dostupan — čitam glasom pregledača."
        : picked.kind === "south"
          ? "Serverski glas nije dostupan — čitam srodnim jezikom pregledača."
          : "Serverski glas nije dostupan — čitam podrazumevanim glasom pregledača.",
    );
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(guideSpeechText(current));
    utterance.lang = picked.voice?.lang || "sr-RS";
    if (picked.voice) utterance.voice = picked.voice;
    utterance.onend = () => {
      setSpeechLoading(false);
      setSpeaking(false);
    };
    utterance.onerror = () => {
      setSpeechLoading(false);
      setSpeaking(false);
      setSpeechNote("Čitanje nije uspelo. Pročitajte vodič na ekranu.");
    };
    setSpeechLoading(false);
    setSpeaking(true);
    window.speechSynthesis.speak(utterance);
  }

  async function speakGuide() {
    if (!guide) return;
    releaseAudio();
    setSpeechNote("");
    setSpeechLoading(true);
    setSpeaking(true);
    const abort = new AbortController();
    abortRef.current = abort;
    const audio = new Audio();
    audioRef.current = audio;
    try {
      const blob = await fetchGuideSpeech(caseId, slug, abort.signal);
      if (abort.signal.aborted || audioRef.current !== audio) {
        setSpeechLoading(false);
        setSpeaking(false);
        return;
      }
      if (!blob.size) {
        throw new ApiError(503, "Glas trenutno nije dostupan");
      }
      const url = URL.createObjectURL(blob);
      objectUrlRef.current = url;
      audio.src = url;
      audio.onended = () => {
        setSpeechLoading(false);
        setSpeaking(false);
        releaseAudio();
      };
      audio.onerror = () => {
        void speakWithBrowser(guide);
      };
      await audio.play();
      setSpeechLoading(false);
    } catch (err) {
      if (abort.signal.aborted || audioRef.current !== audio) {
        setSpeechLoading(false);
        setSpeaking(false);
        return;
      }
      const canFallback =
        err instanceof ApiError && (err.status === 503 || err.status === 0);
      if (canFallback || !(err instanceof ApiError)) {
        await speakWithBrowser(guide);
        return;
      }
      setSpeechLoading(false);
      setSpeaking(false);
      setSpeechNote(err.message || "Čitanje nije uspelo.");
    }
  }

  function stopSpeech() {
    releaseAudio();
    setSpeechLoading(false);
    setSpeaking(false);
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
      <div className="row" style={{ marginTop: 0, marginBottom: 24 }}>
        <button className="btn btn-primary" type="button" onClick={() => void speakGuide()}>
          Pročitaj vodič
        </button>
        <button className="btn btn-ghost" type="button" onClick={stopSpeech}>
          Stani
        </button>
      </div>
      {speechNote ? <p className="alert">{speechNote}</p> : null}
      {speechLoading ? <p className="note">Pripremam glas…</p> : null}
      {speaking && !speechLoading ? <p className="note">Čitam vodič…</p> : null}

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
          <DocRow key={d.type} doc={d} />
        ))}
        <div className="row">
          <label className="file">
            {attachBusy ? "Šaljem sken…" : "Priloži papir uz ovaj vodič"}
            <input
              type="file"
              accept={ACCEPT}
              hidden
              disabled={attachBusy}
              onChange={(e) => {
                const chosen = e.target.files?.[0];
                e.target.value = "";
                void onAttach(chosen);
              }}
            />
          </label>
        </div>
        {attachNote ? <p className="alert">{attachNote}</p> : null}
        <p className="disclaimer" style={{ marginTop: 18 }}>
          {guide.disclaimer}
        </p>
      </div>

      <div className="panel">
        <h2 style={{ marginTop: 0 }}>Gde da odete</h2>
        {guide.office_missing || !guide.office ? (
          <>
            <p>
              {guide.office_missing_reason ||
                "Nismo mogli da odredimo šalter — u tekstu nema mesta. Unesite grad ili opštinu. Ulicu ne izmišljamo."}
            </p>
            {needsPlaceQuestion(guide) ? (
              <>
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
            ) : null}
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
