import { mockGuide, mockMatch } from "./mocks";
import type { Guide, MatchResponse } from "./types";

const delay = (ms = 280) => new Promise((r) => setTimeout(r, ms));

export async function createCase(text: string): Promise<MatchResponse> {
  await delay();
  return mockMatch(text);
}

export async function retryCase(
  _caseId: string,
  text: string,
): Promise<MatchResponse> {
  await delay();
  return mockMatch(text);
}

export async function fetchGuide(
  _caseId: string,
  slug: string,
): Promise<Guide> {
  await delay();
  return mockGuide(slug);
}
