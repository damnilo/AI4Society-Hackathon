const NAME_KEY = "putokaz-name";

export function getSavedName(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(NAME_KEY);
}

export function saveName(name: string): void {
  window.localStorage.setItem(NAME_KEY, name.trim());
}

export function clearName(): void {
  window.localStorage.removeItem(NAME_KEY);
}
