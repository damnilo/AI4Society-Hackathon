export type SessionUser = {
  name: string;
  email: string;
  municipality?: string | null;
};

const ACCESS_KEY = "nasalter-access";
const REFRESH_KEY = "nasalter-refresh";
const USER_KEY = "nasalter-user";
const LEGACY_NAME_KEY = "nasalter-name";
const LEGACY_KEYS: [string, string][] = [
  [ACCESS_KEY, "putokaz-access"],
  [REFRESH_KEY, "putokaz-refresh"],
  [USER_KEY, "putokaz-user"],
  ["nasalter-font-scale", "putokaz-font-scale"],
];

export const AUTH_EVENT = "nasalter-auth";
export const CASE_STORAGE_KEY = "nasalter-case";

export function migrateLegacyKeys(): void {
  if (typeof window === "undefined") return;
  for (const [next, old] of LEGACY_KEYS) {
    if (!window.localStorage.getItem(next)) {
      const value = window.localStorage.getItem(old);
      if (value) window.localStorage.setItem(next, value);
    }
    window.localStorage.removeItem(old);
  }
  window.localStorage.removeItem("putokaz-name");
  if (!window.sessionStorage.getItem(CASE_STORAGE_KEY)) {
    const oldCase = window.sessionStorage.getItem("putokaz-case");
    if (oldCase) window.sessionStorage.setItem(CASE_STORAGE_KEY, oldCase);
  }
  window.sessionStorage.removeItem("putokaz-case");
}

function emitAuth(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(AUTH_EVENT));
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(REFRESH_KEY);
}

export function getSessionUser(): SessionUser | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as SessionUser;
    if (!parsed.email) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function setTokens(access: string, refresh: string): void {
  window.localStorage.setItem(ACCESS_KEY, access);
  window.localStorage.setItem(REFRESH_KEY, refresh);
}

export function setSessionUser(user: SessionUser): void {
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
  window.localStorage.removeItem(LEGACY_NAME_KEY);
  emitAuth();
}

export function clearSession(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(ACCESS_KEY);
  window.localStorage.removeItem(REFRESH_KEY);
  window.localStorage.removeItem(USER_KEY);
  window.localStorage.removeItem(LEGACY_NAME_KEY);
  emitAuth();
}

export function authHeaders(): Record<string, string> {
  const token = getAccessToken();
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}
