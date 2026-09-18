export type DocumentStatus =
  | "complete"
  | "missing"
  | "expired"
  | "unreadable"
  | "mismatch";

export type Candidate = {
  slug: string;
  title: string;
  plain_summary: string;
  score: number;
  rationale: string;
};

export type RequiredDoc = {
  type: string;
  label: string;
  how_to_obtain: string;
  status: DocumentStatus;
  note?: string;
};

export type Office = {
  id: string;
  name: string;
  address: string;
  phone: string;
  lat: number;
  lng: number;
} | null;

export type Guide = {
  title: string;
  institution_label: string;
  channel: "online" | "counter" | "both";
  euprava_url?: string;
  office: Office;
  office_missing: boolean;
  steps: { title: string; description: string }[];
  documents: RequiredDoc[];
  related: { slug: string; title: string }[];
  source_name: string;
  source_url: string;
  last_verified_at: string;
  disclaimer: string;
};

export type MatchResponse = {
  case_id: string;
  candidates: Candidate[];
  need_clarification: boolean;
  questions?: string[];
};

export type StoredCase = MatchResponse & {
  text: string;
  fileName?: string;
  source: "typed" | "catalog";
  pickedTitle?: string;
  pickedSlug?: string;
};
