export type SessionUser = {
  name: string;
  email: string;
};

const ACCESS_KEY = "putokaz-access";
const REFRESH_KEY = "putokaz-refresh";
const USER_KEY = "putokaz-user";
const LEGACY_NAME_KEY = "putokaz-name";

export const AUTH_EVENT = "putokaz-auth";

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
