export const ACCOUNT_PLACES = [
  { id: "pirot", label: "Pirot" },
  { id: "beograd", label: "Beograd" },
  { id: "nis", label: "Niš" },
] as const;

export type AccountPlaceId = (typeof ACCOUNT_PLACES)[number]["id"];

export function isAccountPlaceId(value: string): value is AccountPlaceId {
  return ACCOUNT_PLACES.some((place) => place.id === value);
}

export function placeLabel(id: string | null | undefined): string {
  if (!id) return "";
  return ACCOUNT_PLACES.find((place) => place.id === id)?.label ?? id;
}
