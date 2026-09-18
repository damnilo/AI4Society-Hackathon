import {
  authHeaders,
  clearSession,
  getRefreshToken,
  setSessionUser,
  setTokens,
} from "./auth";
import { documentLabel, institutionLabel } from "./labels";
import { mockGuide, mockMatch } from "./mocks";
import type { DocumentStatus, Guide, MatchResponse, WalletDocument } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const UUID =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

type BackendCandidate = {
  slug: string;
  title: string;
  plain_summary: string;
  score: number;
  rationale: string;
};

type BackendCase = {
  case_id: string;
  candidates: BackendCandidate[];
  need_clarification: boolean;
  questions?: string[];
};

type BackendStep = {
  title: string;
  description: string;
  url?: string;
};

type BackendRequiredDoc = {
  type: string;
  how_to_obtain?: string;
  notes?: string;
};

type BackendGuide = {
  title: string;
  institution: string;
  channel: string;
  steps: BackendStep[];
  required_documents: BackendRequiredDoc[];
  related: { slug: string; title: string }[];
  source_name: string;
  source_url: string;
  last_verified_at: string;
  office: {
    id: string;
    name: string;
    address: string;
    phone: string;
    lat: number;
    lng: number;
  } | null;
  office_missing: boolean;
  disclaimer: string;
};

export function isUuid(value: string): boolean {
  return UUID.test(value);
}

type TokenResponse = {
  access_token: string;
  refresh_token: string;
  name?: string;
  email?: string;
};

type MeProfile = {
  name: string;
  email: string;
  gdpr_note?: string;
};

type BackendDocument = {
  id: string;
  original_filename: string;
  content_type: string;
  case_id: string | null;
  status: string | null;
  purge_at?: string | null;
};

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function explainError(status: number, detail: string): string {
  if (detail === "Email already registered") return "Ovaj email je već registrovan.";
  if (detail === "Invalid credentials") return "Pogrešan email ili lozinka.";
  if (detail === "Not authenticated" || detail === "Invalid token") {
    return "Prijava je istekla. Prijavite se ponovo.";
  }
  if (status === 401) return "Prijava je istekla. Prijavite se ponovo.";
  if (detail) return detail;
  return "Nešto nije u redu. Pokušajte ponovo.";
}

async function readDetail(response: Response): Promise<string> {
  const data: unknown = await response.json().catch(() => null);
  if (data && typeof data === "object" && "detail" in data) {
    const detail = (data as { detail: unknown }).detail;
    if (typeof detail === "string") return explainError(response.status, detail);
    if (Array.isArray(detail) && detail[0] && typeof detail[0] === "object") {
      const first = detail[0] as { msg?: string };
      if (first.msg === "String should have at least 8 characters") {
        return "Lozinka mora imati najmanje 8 karaktera.";
      }
      if (first.msg) return first.msg;
    }
  }
  return explainError(response.status, "");
}

async function requestJson<T>(path: string, init: RequestInit): Promise<T | null> {
  const headers = new Headers(init.headers);
  for (const [key, value] of Object.entries(authHeaders())) {
    headers.set(key, value);
  }
  try {
    let response = await fetch(`${API_URL}${path}`, { ...init, headers });
    if (response.status === 401) {
      const refreshed = await tryRefresh();
      const retryHeaders = new Headers(init.headers);
      if (refreshed) {
        for (const [key, value] of Object.entries(authHeaders())) {
          retryHeaders.set(key, value);
        }
      } else {
        clearSession();
      }
      response = await fetch(`${API_URL}${path}`, { ...init, headers: retryHeaders });
    }
    if (!response.ok) return null;
    return (await response.json()) as T;
  } catch {
    return null;
  }
}

function toMatch(row: BackendCase): MatchResponse {
  return {
    case_id: String(row.case_id),
    candidates: row.candidates,
    need_clarification: row.need_clarification,
    questions: row.questions ?? [],
  };
}

function toStatus(value: string | undefined): DocumentStatus {
  if (
    value === "complete" ||
    value === "missing" ||
    value === "expired" ||
    value === "unreadable" ||
    value === "mismatch"
  ) {
    return value;
  }
  return "missing";
}

function toGuide(row: BackendGuide): Guide {
  const euprava = row.steps.find((step) => step.url?.includes("euprava.gov.rs"))?.url;
  const channel =
    row.channel === "online" || row.channel === "counter" || row.channel === "both"
      ? row.channel
      : "counter";
  return {
    title: row.title,
    institution_label: institutionLabel(row.institution),
    channel,
    euprava_url: euprava,
    office: row.office
      ? {
          id: row.office.id,
          name: row.office.name,
          address: row.office.address,
          phone: row.office.phone,
          lat: row.office.lat,
          lng: row.office.lng,
        }
      : null,
    office_missing: row.office_missing || !row.office,
    steps: row.steps.map((step) => ({
      title: step.title,
      description: step.description,
    })),
    documents: row.required_documents.map((doc) => ({
      type: doc.type,
      label: documentLabel(doc.type),
      how_to_obtain: doc.how_to_obtain ?? "",
      status: toStatus("missing"),
      note: doc.notes || undefined,
    })),
    related: row.related,
    source_name: row.source_name,
    source_url: row.source_url,
    last_verified_at: row.last_verified_at,
    disclaimer: row.disclaimer,
  };
}

export async function createCase(text: string): Promise<MatchResponse> {
  const row = await requestJson<BackendCase>("/cases", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (row) return toMatch(row);
  return mockMatch(text);
}

export async function retryCase(caseId: string, text: string): Promise<MatchResponse> {
  if (isUuid(caseId)) {
    const row = await requestJson<BackendCase>(`/cases/${caseId}/retry`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (row) return toMatch(row);
  }
  return mockMatch(text);
}

export async function fetchGuide(caseId: string, slug: string): Promise<Guide> {
  if (isUuid(caseId)) {
    const row = await requestJson<BackendGuide>(`/cases/${caseId}/select`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ slug }),
    });
    if (row) return toGuide(row);
  }
  return mockGuide(slug);
}

export async function attachCaseDocument(
  caseId: string,
  file: File,
): Promise<WalletDocument | null> {
  if (!isUuid(caseId)) return null;
  const body = new FormData();
  body.append("file", file);
  try {
    const headers = authHeaders();
    let response = await fetch(`${API_URL}/cases/${caseId}/documents`, {
      method: "POST",
      headers,
      body,
    });
    if (response.status === 401) {
      const refreshed = await tryRefresh();
      const retryHeaders = refreshed ? authHeaders() : {};
      if (!refreshed) clearSession();
      const retryBody = new FormData();
      retryBody.append("file", file);
      response = await fetch(`${API_URL}/cases/${caseId}/documents`, {
        method: "POST",
        headers: retryHeaders,
        body: retryBody,
      });
    }
    if (!response.ok) return null;
    return toWalletDoc((await response.json()) as BackendDocument);
  } catch {
    return null;
  }
}

let refreshInFlight: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  if (refreshInFlight) return refreshInFlight;
  refreshInFlight = (async () => {
    const refresh = getRefreshToken();
    if (!refresh) return false;
    try {
      const response = await fetch(`${API_URL}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refresh }),
      });
      if (!response.ok) {
        clearSession();
        return false;
      }
      const tokens = (await response.json()) as TokenResponse;
      setTokens(tokens.access_token, tokens.refresh_token);
      return true;
    } catch {
      clearSession();
      return false;
    }
  })();
  try {
    return await refreshInFlight;
  } finally {
    refreshInFlight = null;
  }
}

async function authRequest<T>(path: string, init: RequestInit, retried = false): Promise<T> {
  const headers = new Headers(init.headers);
  const tokenHeaders = authHeaders();
  for (const [key, value] of Object.entries(tokenHeaders)) {
    headers.set(key, value);
  }
  const response = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (response.status === 401 && !retried) {
    const ok = await tryRefresh();
    if (ok) return authRequest<T>(path, init, true);
    clearSession();
    throw new ApiError(401, explainError(401, "Not authenticated"));
  }
  if (!response.ok) {
    if (response.status === 401) clearSession();
    throw new ApiError(response.status, await readDetail(response));
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

function toWalletDoc(row: BackendDocument): WalletDocument {
  return {
    id: String(row.id),
    original_filename: row.original_filename,
    content_type: row.content_type,
    case_id: row.case_id ? String(row.case_id) : null,
    status: row.status,
    purge_at: row.purge_at ?? null,
  };
}

async function claimOpenCase(): Promise<void> {
  if (typeof window === "undefined") return;
  const raw = sessionStorage.getItem("putokaz-case");
  if (!raw) return;
  try {
    const parsed = JSON.parse(raw) as { case_id?: string };
    if (!parsed.case_id || !isUuid(parsed.case_id)) return;
    await authRequest<unknown>("/me/claim", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ case_id: parsed.case_id }),
    });
  } catch {
    // Gostov case nije obavezan — matching ne sme da padne zbog claim-a.
  }
}

async function storeAuth(tokens: TokenResponse, fallbackName: string, fallbackEmail: string): Promise<void> {
  setTokens(tokens.access_token, tokens.refresh_token);
  const fromToken = {
    name: tokens.name || fallbackName,
    email: tokens.email || fallbackEmail,
  };
  try {
    const me = await authRequest<MeProfile>("/me", { method: "GET" });
    setSessionUser({
      name: me.name || fromToken.name,
      email: me.email || fromToken.email,
    });
  } catch {
    setSessionUser(fromToken);
  }
  await claimOpenCase();
}

export async function registerAccount(input: {
  email: string;
  password: string;
  name: string;
}): Promise<void> {
  const response = await fetch(`${API_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: input.email,
      password: input.password,
      name: input.name,
    }),
  });
  if (!response.ok) {
    throw new ApiError(response.status, await readDetail(response));
  }
  const tokens = (await response.json()) as TokenResponse;
  await storeAuth(tokens, input.name, input.email);
}

export async function loginAccount(input: {
  email: string;
  password: string;
}): Promise<void> {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: input.email,
      password: input.password,
    }),
  });
  if (!response.ok) {
    throw new ApiError(response.status, await readDetail(response));
  }
  const tokens = (await response.json()) as TokenResponse;
  await storeAuth(tokens, "", input.email);
}

export function logoutAccount(): void {
  clearSession();
}

export async function listWalletDocuments(): Promise<WalletDocument[]> {
  const rows = await authRequest<BackendDocument[]>("/documents", { method: "GET" });
  return rows.map(toWalletDoc);
}

export async function uploadWalletDocument(file: File): Promise<WalletDocument> {
  const body = new FormData();
  body.append("file", file);
  return toWalletDoc(
    await authRequest<BackendDocument>("/documents", {
      method: "POST",
      body,
    }),
  );
}

export async function deleteWalletDocument(id: string): Promise<void> {
  await authRequest<unknown>(`/documents/${id}`, { method: "DELETE" });
}
