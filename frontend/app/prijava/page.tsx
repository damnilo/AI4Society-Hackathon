"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  ApiError,
  fetchMe,
  loginAccount,
  logoutAccount,
  registerAccount,
  updateMunicipality,
} from "@/lib/api";
import { AUTH_EVENT, getSessionUser, setSessionUser } from "@/lib/auth";
import {
  ACCOUNT_PLACES,
  isAccountPlaceId,
  placeLabel,
  type AccountPlaceId,
} from "@/lib/places";

const GDPR =
  "Nalog nije obavezan da biste našli proceduru. Čuvamo email, ime, mesto i skenove koje sami otpremite, da ih ne unosite svaki put. Prilog gosta se briše posle 48 sati ako ga nalogom ne preuzmete. NaŠalter nije eUprava i ne šalje zahtev umesto vas.";

export default function PrijavaPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [municipality, setMunicipality] = useState<AccountPlaceId | "">("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [user, setUser] = useState<{
    name: string;
    email: string;
    municipality?: string | null;
  } | null>(null);

  useEffect(() => {
    function sync() {
      const next = getSessionUser();
      setUser(next);
      const place = next?.municipality ?? "";
      if (isAccountPlaceId(place)) setMunicipality(place);
    }
    sync();
    window.addEventListener(AUTH_EVENT, sync);
    return () => window.removeEventListener(AUTH_EVENT, sync);
  }, []);

  useEffect(() => {
    if (!getSessionUser()) return;
    void fetchMe()
      .then((me) => {
        setSessionUser({
          name: me.name,
          email: me.email,
          municipality: me.municipality ?? null,
        });
      })
      .catch(() => {
        /* nalog i dalje važi iz sessionStorage */
      });
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "register") {
        if (!isAccountPlaceId(municipality)) {
          setError("Izaberite mesto: Pirot, Beograd ili Niš.");
          return;
        }
        await registerAccount({
          email,
          password,
          name,
          municipality,
        });
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

  async function savePlace() {
    if (!isAccountPlaceId(municipality) || busy) return;
    setBusy(true);
    setError("");
    try {
      await updateMunicipality(municipality);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Mesto nije sačuvano.");
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
          novčanik dokumenata i mesto za šalter kad u tekstu nema grada.
        </p>
        <div className="panel">
          <p>
            {user.name ? <strong>{user.name}</strong> : "Nalog"}
            <br />
            <span className="note">{user.email}</span>
            <br />
            <span className="note">
              Mesto: {placeLabel(user.municipality) || "nije izabrano"}
            </span>
          </p>
          <label className="big" htmlFor="mesto-nalog">
            Mesto (za šalter kad u opisu nema grada)
          </label>
          <select
            id="mesto-nalog"
            className="describe"
            value={municipality}
            onChange={(e) => {
              const value = e.target.value;
              if (isAccountPlaceId(value)) setMunicipality(value);
            }}
          >
            <option value="">Izaberite mesto</option>
            {ACCOUNT_PLACES.map((place) => (
              <option key={place.id} value={place.id}>
                {place.label}
              </option>
            ))}
          </select>
          {error ? <p className="alert">{error}</p> : null}
          <div className="row">
            <button
              className="btn btn-primary"
              type="button"
              disabled={busy || !isAccountPlaceId(municipality)}
              onClick={() => void savePlace()}
            >
              {busy ? "Čuvam…" : "Sačuvaj mesto"}
            </button>
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
            <Link className="btn btn-ghost" href="/dokumenta">
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
        Nalog nije obavezan. Služi da sačuvate skenove i mesto za sledeći put.
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
          <>
            <p className="note">Najmanje 8 karaktera.</p>
            <label className="big" htmlFor="mesto">
              Mesto
            </label>
            <select
              id="mesto"
              className="describe"
              value={municipality}
              onChange={(e) => {
                const value = e.target.value;
                setMunicipality(isAccountPlaceId(value) ? value : "");
              }}
              required
            >
              <option value="">Pirot, Beograd ili Niš</option>
              {ACCOUNT_PLACES.map((place) => (
                <option key={place.id} value={place.id}>
                  {place.label}
                </option>
              ))}
            </select>
            <p className="note">
              Koristi se za šalter samo ako u opisu namere nema grada. Selidba
              Pirot→Beograd i dalje ide na Ljermontovu.
            </p>
          </>
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
