import type { DocumentStatus } from "./types";

export const STATUS_LABEL: Record<DocumentStatus, string> = {
  complete: "Imate",
  missing: "Fali",
  expired: "Isteklo",
  unreadable: "Nečitko",
  mismatch: "Ne odgovara",
};
