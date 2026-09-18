"use client";

import { useState } from "react";
import { ApiError, clarifyCase } from "@/lib/api";

export function ClarifyBox({
  caseId,
  questions,
  originalText,
}: {
  caseId: string;
  questions: string[];
  originalText: string;
}) {
  const [answers, setAnswers] = useState<string[]>(() => questions.map(() => ""));
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("");

  async function submit() {
    const filled = answers.map((value) => value.trim());
    if (busy || filled.some((value) => !value)) {
      setNote("Odgovorite na svako pitanje, pa pošaljite.");
      return;
    }
    setBusy(true);
    setNote("");
    try {
      const payload: Record<string, string> = {};
      questions.forEach((question, index) => {
        payload[`q${index + 1}`] = `${question} ${filled[index]}`;
      });
      const result = await clarifyCase(caseId, payload);
      sessionStorage.setItem(
        "putokaz-case",
        JSON.stringify({
          ...result,
          text: originalText,
          source: "typed",
        }),
      );
      window.location.assign(`/predlozi/${result.case_id}`);
    } catch (err) {
      setNote(
        err instanceof ApiError
          ? err.message
          : "Dopuna nije uspela. Proverite da li API radi.",
      );
      setBusy(false);
    }
  }

  return (
    <div className="panel" style={{ marginBottom: 24 }}>
      <p className="lede" style={{ marginBottom: 16 }}>
        Nismo sigurni. Odgovorite kratko, pa ćemo ponovo predložiti procedure.
      </p>
      {questions.map((question, index) => (
        <label className="big" key={question} htmlFor={`clarify-${index}`}>
          {question}
          <input
            id={`clarify-${index}`}
            className="describe"
            value={answers[index] ?? ""}
            onChange={(event) => {
              const next = [...answers];
              next[index] = event.target.value;
              setAnswers(next);
            }}
          />
        </label>
      ))}
      <div className="row">
        <button className="btn btn-primary" type="button" onClick={() => void submit()} disabled={busy}>
          {busy ? "Tražim u katalogu…" : "Pošalji odgovore"}
        </button>
      </div>
      {note ? <p className="alert">{note}</p> : null}
    </div>
  );
}
