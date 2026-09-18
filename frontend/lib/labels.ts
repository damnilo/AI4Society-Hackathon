import type { DocumentStatus } from "./types";

export const STATUS_LABEL: Record<DocumentStatus, string> = {
  complete: "Imate",
  missing: "Fali",
  expired: "Isteklo",
  unreadable: "Nečitko",
  mismatch: "Ne odgovara",
};

export const INSTITUTION_LABEL: Record<string, string> = {
  mup: "MUP",
  maticar: "Matičar",
  rfzo: "RFZO",
  apr: "APR",
};

export const DOC_LABEL: Record<string, string> = {
  licna_karta: "Lična karta",
  pasos: "Pasoš",
  vozacka_dozvola: "Vozačka dozvola",
  uplatnica_euprava: "Uplatnica sa eUprave",
  dokaz_pravnog_osnova: "Dokaz o stanu",
  saglasnost_vlasnika: "Saglasnost vlasnika",
  saglasnost_roditelja: "Saglasnost roditelja",
  izvod_rodjeni: "Izvod iz matične knjige rođenih",
  uverenje_drzavljanstvo: "Uverenje o državljanstvu",
  lekarsko_vozac: "Lekarsko uverenje",
  dokaz_ispit_voznje: "Dokaz o položenom ispitu",
  zdravstvena_isprava: "Zdravstvena isprava",
  saobracajna_dozvola: "Saobraćajna dozvola",
  polisa_osiguranja: "Polisa osiguranja",
  tehnicki_pregled: "Tehnički pregled",
  apr_obrazac: "APR obrazac",
};

export function institutionLabel(code: string): string {
  return INSTITUTION_LABEL[code] ?? code.toUpperCase();
}

export function documentLabel(type: string): string {
  return DOC_LABEL[type] ?? type.replaceAll("_", " ");
}
