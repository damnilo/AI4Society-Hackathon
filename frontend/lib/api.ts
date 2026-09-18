import { documentLabel, institutionLabel } from "./labels";
import { mockGuide, mockMatch } from "./mocks";
import type { DocumentStatus, Guide, MatchResponse } from "./types";

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

function isUuid(value: string): boolean {
  return UUID.test(value);
}

async function requestJson<T>(path: string, init: RequestInit): Promise<T | null> {
  try {
    const response = await fetch(`${API_URL}${path}`, init);
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
