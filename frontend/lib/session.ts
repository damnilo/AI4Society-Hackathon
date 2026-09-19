export const CASE_STORAGE_KEY = "nasalter-case";

export function clearCaseSession(): void {
  if (typeof window === "undefined") return;
  sessionStorage.removeItem(CASE_STORAGE_KEY);
}
