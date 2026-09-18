"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getSessionUser } from "@/lib/auth";
import { ApiError, loginAccount, logoutAccount, registerAccount } from "@/lib/api";

const GDPR =
  "Nalog nije obavezan da biste našli proceduru. Čuvamo email, ime i skenove koje sami otpremite, da ih ne unosite svaki put. Prilog gosta se briše posle 48 sati ako ga nalogom ne preuzmete. Putokaz nije eUprava i ne šalje zahtev umesto vas.";

export default function PrijavaPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [user, setUser] = useState<{ name: string; email: string } | null>(null);

  useEffect(() => {
    setUser(getSessionUser());
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "register") {
        await registerAccount({ email, password, name });
      } else {
        await loginAccount({ email, password });
      }
      router.push("/dokumenta");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Prijava nije uspela.");
    } finally {
      setBusy(false);
    }
  }

  if (user) {
    return (
      <>
        <h1>Nalog</h1>
        <p className="lede">
          Prijavljeni ste. Matching i dalje radi i bez naloga — nalog je
          novčanik dokumenata.
        </p>
        <div className="panel">
          <p>
            {user.name ? <strong>{user.name}</strong> : "Nalog"}
            <br />
            <span className="note">{user.email}</span>
          </p>
          <div className="row">
            <button
              className="btn btn-ghost"
              type="button"
              onClick={() => {
                logoutAccount();
                setUser(null);
              }}
            >
              Odjavi se
            </button>
            <Link className="btn btn-primary" href="/dokumenta">
              Dokumenta
            </Link>
          </div>
        </div>
        <p className="disclaimer">{GDPR}</p>
      </>
    );
  }

  return (
    <>
      <h1>{mode === "login" ? "Prijava" : "Napravite nalog"}</h1>
      <p className="lede">
        Nalog nije obavezan. Služi da sačuvate skenove za sledeći put.
      </p>

      <div className="row" style={{ marginBottom: 16 }}>
        <button
          className={`btn ${mode === "login" ? "btn-primary" : "btn-ghost"}`}
          type="button"
          onClick={() => setMode("login")}
        >
          Prijava
        </button>
        <button
          className={`btn ${mode === "register" ? "btn-primary" : "btn-ghost"}`}
          type="button"
          onClick={() => setMode("register")}
        >
          Novi nalog
        </button>
      </div>

      <form className="panel" onSubmit={submit}>
        {mode === "register" ? (
          <>
            <label className="big" htmlFor="ime">
              Ime
            </label>
            <input
              id="ime"
              className="describe"
              value={name}
              onChange={(e) => setName(e.target.value)}
              autoComplete="name"
            />
          </>
        ) : null}

        <label className="big" htmlFor="email">
          Email
        </label>
        <input
          id="email"
          className="describe"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="email"
          required
        />

        <label className="big" htmlFor="lozinka">
          Lozinka
        </label>
        <input
          id="lozinka"
          className="describe"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete={mode === "register" ? "new-password" : "current-password"}
          minLength={8}
          required
        />
        {mode === "register" ? (
          <p className="note">Najmanje 8 karaktera.</p>
        ) : null}

        {error ? <p className="alert">{error}</p> : null}

        <div className="row">
          <button className="btn btn-primary" type="submit" disabled={busy}>
            {busy ? "Sačekajte…" : mode === "login" ? "Prijavi se" : "Napravi nalog"}
          </button>
        </div>
      </form>

      <p className="disclaimer">{GDPR}</p>
    </>
  );
}
