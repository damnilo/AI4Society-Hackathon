"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { clearName, getSavedName, saveName } from "@/lib/session";

export default function PrijavaPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [saved, setSaved] = useState<string | null>(null);

  useEffect(() => {
    setSaved(getSavedName());
  }, []);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    saveName(name);
    router.push("/");
    router.refresh();
  }

  return (
    <>
      <h1>Prijava</h1>
      <p className="lede">
        Nalog nije obavezan da biste našli proceduru. Služi da sačuvate skenove
        za sledeći put. Ovo je privremeni lokalni unos, bez prave lozinke.
      </p>

      {saved ? (
        <div className="panel">
          <p>
            Trenutno: <strong>{saved}</strong>
          </p>
          <button
            className="btn btn-ghost"
            type="button"
            onClick={() => {
              clearName();
              setSaved(null);
            }}
          >
            Odjavi se
          </button>
        </div>
      ) : (
        <form className="panel" onSubmit={submit}>
          <label className="big" htmlFor="ime">
            Kako da vas zovemo?
          </label>
          <input
            id="ime"
            className="describe"
            style={{ minHeight: 0 }}
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoComplete="name"
          />
          <div className="row">
            <button className="btn btn-primary" type="submit">
              Sačuvaj ime
            </button>
          </div>
        </form>
      )}
    </>
  );
}
