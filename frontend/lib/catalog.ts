export const GROUPS = [
  {
    id: "dokumenta",
    title: "Lična dokumenta",
    hint: "Lična karta, pasoš, vozačka",
  },
  {
    id: "gradjanske",
    title: "Građanske usluge",
    hint: "Prebivalište, izvodi, lekar",
  },
  {
    id: "komunalne",
    title: "Komunalne usluge",
    hint: "Još nije u ovom vodiču",
  },
  {
    id: "ostalo",
    title: "Ostalo",
    hint: "Vozilo, preduzetnik, termin",
  },
] as const;

export type GroupId = (typeof GROUPS)[number]["id"];

export const SERVICES: {
  slug: string;
  title: string;
  summary: string;
  group: GroupId;
  example: string;
}[] = [
  {
    slug: "licna-karta-zamena",
    title: "Zamena lične karte",
    summary: "Istekla, oštećena ili izgubljena lična karta.",
    group: "dokumenta",
    example: "istekla mi je lična",
  },
  {
    slug: "licna-karta-prvo-izdavanje",
    title: "Prvo izdavanje lične karte",
    summary: "Prva lična karta, obično za dete ili prvi put.",
    group: "dokumenta",
    example: "treba mi prva lična karta",
  },
  {
    slug: "pasos-izdavanje",
    title: "Izdavanje / zamena pasoša",
    summary: "Putna isprava. Nije zamena za ličnu kartu.",
    group: "dokumenta",
    example: "treba mi pasoš",
  },
  {
    slug: "vozacka-dozvola-izdavanje",
    title: "Prva vozačka dozvola",
    summary: "Posle auto-škole, prva dozvola.",
    group: "dokumenta",
    example: "položio sam vožnju, treba mi vozačka",
  },
  {
    slug: "vozacka-dozvola-zamena",
    title: "Zamena vozačke dozvole",
    summary: "Istekla ili oštećena vozačka.",
    group: "dokumenta",
    example: "istekla mi je vozačka",
  },
  {
    slug: "prijava-prebivalista",
    title: "Prijava prebivališta",
    summary: "Stalna selidba na novu adresu.",
    group: "gradjanske",
    example: "selim se iz Pirota u Beograd",
  },
  {
    slug: "prijava-boravista",
    title: "Prijava boravišta",
    summary: "Privremeni boravak, bez promene stalnog prebivališta.",
    group: "gradjanske",
    example: "privremeno živim u drugom gradu",
  },
  {
    slug: "uverenje-o-prebivalistu",
    title: "Uverenje o prebivalištu",
    summary: "Potvrda gde ste prijavljeni.",
    group: "gradjanske",
    example: "treba mi uverenje o prebivalištu",
  },
  {
    slug: "izvod-maticne-rodjenih",
    title: "Izvod iz matične knjige rođenih",
    summary: "Rodni list / izvod.",
    group: "gradjanske",
    example: "treba mi izvod iz matične knjige rođenih",
  },
  {
    slug: "uverenje-o-drzavljanstvu",
    title: "Uverenje o državljanstvu",
    summary: "Često uz prvu ličnu kartu.",
    group: "gradjanske",
    example: "treba mi uverenje o državljanstvu",
  },
  {
    slug: "izbor-izabranog-lekara",
    title: "Izbor izabranog lekara",
    summary: "Posle selidbe često treba novi lekar.",
    group: "gradjanske",
    example: "selio sam se, treba mi novi lekar",
  },
  {
    slug: "saglasnost-vlasnika-prebivaliste",
    title: "Saglasnost vlasnika za prebivalište",
    summary: "Kad se prijavljuješ na tuđi stan, vlasnik daje saglasnost (i preko eUprave).",
    group: "gradjanske",
    example: "gazda treba da da saglasnost za prijavu",
  },
  {
    slug: "registracija-vozila",
    title: "Registracija vozila",
    summary: "Registracija ili produženje registracije.",
    group: "ostalo",
    example: "treba da registrujem auto",
  },
  {
    slug: "prijava-preduzetnika",
    title: "Prijava preduzetnika (APR)",
    summary: "Otvaranje preduzetničke radnje.",
    group: "ostalo",
    example: "hoću da otvorim preduzetničku radnju",
  },
  {
    slug: "ezakazivanje-licna-pasos",
    title: "eZakazivanje za ličnu / pasoš",
    summary: "Samo zakazivanje termina, nije sama usluga.",
    group: "ostalo",
    example: "hoću da zakažem termin za ličnu kartu",
  },
];

export function servicesInGroup(group: GroupId) {
  return SERVICES.filter((s) => s.group === group);
}
