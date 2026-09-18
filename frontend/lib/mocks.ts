import type { Guide, MatchResponse } from "./types";

function includesAny(text: string, words: string[]): boolean {
  const t = text.toLowerCase();
  return words.some((w) => t.includes(w.toLowerCase()));
}

export function mockMatch(text: string): MatchResponse {
  const case_id = `case-${Date.now()}`;

  if (
    includesAny(text, [
      "ličn",
      "licn",
      "личн",
      "istekla",
      "истекл",
      "izgubio",
      "изгуб",
    ])
  ) {
    return {
      case_id,
      candidates: [
        {
          slug: "licna-karta-zamena",
          title: "Zamena lične karte",
          plain_summary:
            "Nova lična karta kada je stara istekla, oštećena ili izgubljena.",
          score: 0.86,
          rationale:
            "Pominjete ličnu kartu i rok ili gubitak — to je zamena, ne prvo izdavanje.",
        },
        {
          slug: "pasos-izdavanje",
          title: "Izdavanje / zamena pasoša",
          plain_summary:
            "Putna isprava. Nije zamena za ličnu kartu u zemlji.",
          score: 0.41,
          rationale:
            "Često se meša sa ličnom kartom, ali pasoš je za putovanje.",
        },
        {
          slug: "licna-karta-prvo-izdavanje",
          title: "Prvo izdavanje lične karte",
          plain_summary: "Prva lična karta, obično za dete ili prvi put.",
          score: 0.33,
          rationale: "Ako već imate ličnu, ovo nije vaš slučaj.",
        },
      ],
      need_clarification: false,
    };
  }

  if (
    includesAny(text, [
      "selim",
      "сели",
      "prebival",
      "пребивал",
      "pirot",
      "пирот",
      "beograd",
      "београд",
      "adres",
      "адрес",
    ])
  ) {
    return {
      case_id,
      candidates: [
        {
          slug: "prijava-prebivalista",
          title: "Prijava prebivališta",
          plain_summary:
            "Stalna selidba: prijava na NOVOJ adresi, ne u starom gradu.",
          score: 0.88,
          rationale:
            "Opisujete selidbu ili promenu adrese. To je prijava prebivališta.",
        },
        {
          slug: "prijava-boravista",
          title: "Prijava boravišta",
          plain_summary:
            "Privremeni boravak, bez promene stalnog prebivališta.",
          score: 0.47,
          rationale:
            "Ako se seliš samo na par meseci, možda je boravište, ne prebivalište.",
        },
        {
          slug: "izbor-izabranog-lekara",
          title: "Izbor izabranog lekara",
          plain_summary:
            "Posle selidbe često treba novi lekar. To je sledeći korak, ne prvi.",
          score: 0.29,
          rationale: "Povezano sa selidbom, ali nije prijava adrese.",
        },
      ],
      need_clarification: false,
    };
  }

  return {
    case_id,
    candidates: [
      {
        slug: "licna-karta-zamena",
        title: "Zamena lične karte",
        plain_summary: "Ako je problem isprava koja ističe ili se menja.",
        score: 0.38,
        rationale: "Česta potreba, ali nismo sigurni da je ovo to.",
      },
      {
        slug: "prijava-prebivalista",
        title: "Prijava prebivališta",
        plain_summary: "Ako menjate adresu ili grad.",
        score: 0.34,
        rationale: "Česta potreba kod selidbe.",
      },
      {
        slug: "izvod-maticne-rodjenih",
        title: "Izvod iz matične knjige rođenih",
        plain_summary: "Rodni list / izvod, često preko eUprave.",
        score: 0.31,
        rationale: "Čest papir, ako trebate izvod a ne ličnu ili selidbu.",
      },
    ],
    need_clarification: true,
  };
}

export function mockGuide(slug: string): Guide {
  const disclaimer =
    "Ovo nije zvanična overa dokumenta niti podnošenje zahteva na eUpravu. Provera važenja je na osnovu datuma na skenu.";

  if (slug === "prijava-prebivalista") {
    return {
      title: "Prijava prebivališta",
      institution_label: "MUP",
      channel: "both",
      euprava_url: "https://euprava.gov.rs/usluge/01048",
      office: {
        id: "pu-beograd-upravni",
        name: "PU za grad Beograd — Uprava za upravne poslove",
        address: "Ljermontova 12a, 11107 Beograd (Voždovac)",
        phone: "011/3470-200",
        lat: 44.7828,
        lng: 20.4906,
      },
      office_missing: false,
      steps: [
        {
          title: "Pripremi dokumenta i uplatnicu",
          description:
            "Na eUpravi generiši uplatnicu. Ponesi važeću ličnu, dokaz o stanu i saglasnost vlasnika ako stan nije tvoj.",
        },
        {
          title: "Idi na šalter po NOVOJ adresi",
          description:
            "Ako se seliš iz Pirota u Beograd, ne ideš u PU Pirot. U Beogradu: Ljermontova 12a.",
        },
        {
          title: "Ažuriraj adresu na ličnoj karti",
          description:
            "Posle prijave, adresa se upisuje u čip ili ide nova lična karta.",
        },
      ],
      documents: [
        {
          type: "licna_karta",
          label: "Lična karta",
          how_to_obtain: "Mora biti važeća.",
          status: "missing",
        },
        {
          type: "uplatnica_euprava",
          label: "Uplatnica sa eUprave",
          how_to_obtain: "Generiši na portalu pre odlaska.",
          status: "missing",
        },
        {
          type: "dokaz_pravnog_osnova",
          label: "Dokaz o stanu",
          how_to_obtain: "Ugovor, list nepokretnosti i sl.",
          status: "missing",
        },
        {
          type: "saglasnost_vlasnika",
          label: "Saglasnost vlasnika",
          how_to_obtain: "Samo ako nisi vlasnik stana.",
          status: "missing",
        },
      ],
      related: [
        { slug: "licna-karta-zamena", title: "Zamena lične karte" },
        { slug: "izbor-izabranog-lekara", title: "Izbor lekara" },
      ],
      source_name: "MUP — Prebivalište",
      source_url:
        "https://www.mup.gov.rs/wps/portal/sr/gradjani/dokumenta/prebivaliste",
      last_verified_at: "18.09.2026",
      disclaimer,
    };
  }

  return {
    title: "Zamena lične karte",
    institution_label: "MUP",
    channel: "both",
    euprava_url: "https://euprava.gov.rs/usluge/00005",
    office: {
      id: "pu-pirot",
      name: "Policijska uprava u Pirotu",
      address: "Jevrejska 17, 18300 Pirot",
      phone: "010/353-077",
      lat: 43.1555,
      lng: 22.5858,
    },
    office_missing: false,
    steps: [
      {
        title: "Proveri datum na ličnoj",
        description:
          "Ako je rok prošao, treba zamena. Ako je nestala, ponesi pasoš ili vozačku.",
      },
      {
        title: "Uplatnica i termin",
        description: "Na eUpravi možeš da generišeš uplatnicu i da zakažeš.",
      },
      {
        title: "Šalter po prebivalištu",
        description: "Idi lično. Staru ličnu ponesi čak i ako je istekla.",
      },
    ],
    documents: [
      {
        type: "licna_karta",
        label: "Stara lična karta",
        how_to_obtain: "Ponesi je i ako je istekla.",
        status: "expired",
        note: "Na skenu piše da važi do datuma u prošlosti — rok je istekao. Ovo nije overa da je dokument originalan.",
      },
      {
        type: "uplatnica_euprava",
        label: "Uplatnica sa eUprave",
        how_to_obtain: "Portal eUprava.",
        status: "missing",
      },
    ],
    related: [{ slug: "pasos-izdavanje", title: "Pasoš" }],
    source_name: "MUP — Lična karta",
    source_url:
      "https://www.mup.gov.rs/wps/portal/sr/gradjani/dokumenta/licna%20karta",
    last_verified_at: "18.09.2026",
    disclaimer,
  };
}
