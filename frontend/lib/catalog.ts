export const GROUPS = [
  {
    id: "dokumenta",
    title: "Lična dokumenta",
    hint: "Lična karta, pasoš, termin",
  },
  {
    id: "gradjanske",
    title: "Građanske usluge",
    hint: "Prebivalište, izvodi, uverenja",
  },
  {
    id: "vozila",
    title: "Vozila i saobraćaj",
    hint: "Vozačka dozvola, registracija",
  },
  {
    id: "zdravlje",
    title: "Zdravlje",
    hint: "Izabrani lekar, overa knjižice",
  },
  {
    id: "ostalo",
    title: "Privreda i ostalo",
    hint: "Preduzetnik (APR)",
  },
  {
    id: "pirot",
    title: "Grad Pirot",
    hint: "Lokalne usluge Gradske uprave",
  },
] as const;

export type GroupId = (typeof GROUPS)[number]["id"];

export function accountIsPirot(municipality: string | null | undefined): boolean {
  return (municipality ?? "").trim().toLowerCase() === "pirot";
}

export function catalogGroupsFor(municipality: string | null | undefined) {
  if (accountIsPirot(municipality)) return GROUPS;
  return GROUPS.filter((group) => group.id !== "pirot");
}

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
    summary:
      "Nova lična karta kada je stara istekla, oštećena, izgubljena ili su se promenili podaci. Najčešći slučaj — „istekla mi je lična“. Podnosi se lično u policijskoj upravi po mestu prebivališta, uz uplatnicu sa eUprave.",
    group: "dokumenta",
    example: "istekla mi je lična",
  },
  {
    slug: "licna-karta-prvo-izdavanje",
    title: "Prvo izdavanje lične karte",
    summary:
      "Prva biometrijska lična karta — za dete koje je napunilo godine ili ako je prvi put vadite. Izvod iz matične i uverenje o državljanstvu MUP često pribavlja po službenoj dužnosti.",
    group: "dokumenta",
    example: "treba mi prva lična karta",
  },
  {
    slug: "pasos-izdavanje",
    title: "Izdavanje / zamena pasoša",
    summary:
      "Biometrijski pasoš za putovanja van Srbije — prvo izdavanje ili zamena isteklog. Nije zamena za ličnu kartu u zemlji. Termin se najčešće zakazuje online, a za dete treba saglasnost roditelja.",
    group: "dokumenta",
    example: "treba mi pasoš",
  },
  {
    slug: "ezakazivanje-licna-pasos",
    title: "eZakazivanje za ličnu / pasoš",
    summary:
      "Online zakazivanje termina u MUP-u za ličnu kartu i/ili pasoš. Ovo je samo termin, ne i samo izdavanje dokumenta. Potreban je eID nalog na portalu eUprava.",
    group: "dokumenta",
    example: "hoću da zakažem termin za ličnu kartu",
  },
  {
    slug: "prijava-prebivalista",
    title: "Prijava prebivališta",
    summary:
      "Prijava stalne adrese posle selidbe. Radi se u policijskoj upravi po NOVOJ adresi, ne po starom gradu. Ako stan nije vaš, vlasnik daje saglasnost — može i preko eUprave.",
    group: "gradjanske",
    example: "selim se iz Pirota u Beograd",
  },
  {
    slug: "prijava-boravista",
    title: "Prijava boravišta",
    summary:
      "Prijava privremenog boravka (studije, sezona, privremeni posao) bez menjanja stalnog prebivališta. Nije ista procedura kao prijava prebivališta.",
    group: "gradjanske",
    example: "privremeno živim u drugom gradu",
  },
  {
    slug: "uverenje-o-prebivalistu",
    title: "Uverenje o prebivalištu",
    summary:
      "Potvrda o tome gde ste prijavljeni — za banku, školu ili sud. U Beogradu se izdaje u Upravi za upravne poslove (Ljermontova 12a), ne u lokalnoj stanici.",
    group: "gradjanske",
    example: "treba mi uverenje o prebivalištu",
  },
  {
    slug: "saglasnost-vlasnika-prebivaliste",
    title: "Saglasnost vlasnika za prebivalište",
    summary:
      "Kada se prijavljujete na tuđi stan, vlasnik elektronski daje saglasnost (preko eUprave) i dobija EGN broj. Taj broj nosite na šalter — vlasnik ne mora da ide sa vama.",
    group: "gradjanske",
    example: "gazda treba da da saglasnost za prijavu",
  },
  {
    slug: "izvod-maticne-rodjenih",
    title: "Izvod iz matične knjige rođenih",
    summary:
      "Rodni list — osnovni izvod o rođenju. Može elektronski (eIzvod u eSanduče, e-oblik bez takse) ili papirno kod matičara po mestu upisa.",
    group: "gradjanske",
    example: "treba mi izvod iz matične knjige rođenih",
  },
  {
    slug: "izvod-maticne-vencanih",
    title: "Izvod iz matične knjige venčanih",
    summary:
      "Venčani list — dokaz o zaključenom braku, za banku, sud ili promenu prezimena. Online preko eUprave ili kod matičara po mestu upisa braka.",
    group: "gradjanske",
    example: "treba mi izvod iz matične knjige venčanih",
  },
  {
    slug: "izvod-maticne-umrlih",
    title: "Izvod iz matične knjige umrlih",
    summary:
      "Umrli list — potreban za ostavinski postupak, penziju i zatvaranje računa. Izdaje matičar po mestu upisa ili se preuzima kao eIzvod na eUpravi.",
    group: "gradjanske",
    example: "treba mi izvod iz matične knjige umrlih",
  },
  {
    slug: "uverenje-o-drzavljanstvu",
    title: "Uverenje o državljanstvu",
    summary:
      "Potvrda da ste državljanin Srbije — često uz prvu ličnu kartu ili pasoš, i za konkurse. Izdaje matičar; za prvu LK MUP često pribavi podatke po službenoj dužnosti.",
    group: "gradjanske",
    example: "treba mi uverenje o državljanstvu",
  },
  {
    slug: "uverenje-slobodno-bracno-stanje",
    title: "Uverenje o slobodnom bračnom stanju",
    summary:
      "Potvrda da niste u braku — najčešće za venčanje u inostranstvu ili sa strancem. Izdaje matičar po mestu rođenja; za inostranstvo može trebati Apostille pečat suda.",
    group: "gradjanske",
    example: "treba mi uverenje da nisam u braku",
  },
  {
    slug: "vozacka-dozvola-izdavanje",
    title: "Prva vozačka dozvola",
    summary:
      "Prva vozačka dozvola posle položenog ispita u auto-školi. Treba važeće lekarsko uverenje za vozače, dokaz o položenom ispitu i uplatnica sa eUprave.",
    group: "vozila",
    example: "položio sam vožnju, treba mi vozačka",
  },
  {
    slug: "vozacka-dozvola-zamena",
    title: "Zamena vozačke dozvole",
    summary:
      "Zamena istekle ili oštećene vozačke, ili promena podataka. Za istekle dozvole često treba novo lekarsko. Postoji i elektronski zahtev na eUpravi.",
    group: "vozila",
    example: "istekla mi je vozačka",
  },
  {
    slug: "registracija-vozila",
    title: "Registracija vozila",
    summary:
      "Registracija ili produženje registracije vozila. Prvo tehnički pregled i obavezno osiguranje, pa šalter registracije. Nije isto što i vozačka dozvola.",
    group: "vozila",
    example: "treba da registrujem auto",
  },
  {
    slug: "izbor-izabranog-lekara",
    title: "Izbor izabranog lekara",
    summary:
      "Izbor ili promena izabranog lekara u domu zdravlja (RFZO). Posle selidbe u novi grad obično treba novi lekar. Ponesite ličnu kartu i zdravstvenu ispravu.",
    group: "zdravlje",
    example: "selio sam se, treba mi novi lekar",
  },
  {
    slug: "overa-zdravstvene-knjizice",
    title: "Overa zdravstvene knjižice",
    summary:
      "Produženje overe zdravstvenog osiguranja u filijali RFZO ili domu zdravlja. Bez važeće overe usluge se ne priznaju na teret osiguranja. Za mnoge kategorije overa ide automatski.",
    group: "zdravlje",
    example: "treba da overim zdravstvenu knjižicu",
  },
  {
    slug: "prijava-preduzetnika",
    title: "Prijava preduzetnika (APR)",
    summary:
      "Otvaranje preduzetničke radnje u Agenciji za privredne registre (APR). Može elektronski ili na šalteru APR. Nije MUP i nije prijava prebivališta.",
    group: "ostalo",
    example: "hoću da otvorim preduzetničku radnju",
  },
  {
    slug: "biracki-spisak-pirot",
    title: "Birački spisak (Pirot)",
    summary:
      "Upis, ispravka ili potvrda o biračkom pravu u Gradskoj upravi Pirot — kancelarija 20, Srpskih vladara 82. Takse nema. Važi samo za birače u Pirotu.",
    group: "pirot",
    example: "nisam na biračkom spisku u Pirotu",
  },
  {
    slug: "promena-licnog-imena-pirot",
    title: "Promena ličnog imena (Pirot)",
    summary:
      "Zahtev za promenu imena ili prezimena pred Gradskom upravom Pirot. Obrazac je na pirot.rs (Građanska stanja). Posle rešenja ide zamena lične karte.",
    group: "pirot",
    example: "hoću da promenim prezime u Pirotu",
  },
  {
    slug: "zakljucenje-braka-pirot",
    title: "Venčanje u sali Gradske uprave Pirot",
    summary:
      "Zakazivanje venčanja pred matičarem u sali Gradske uprave — radnim danom, van radnog vremena ili vikendom. Nije isto što i izvod venčanih.",
    group: "pirot",
    example: "hoćemo da se venčamo u Pirotu",
  },
  {
    slug: "porez-na-imovinu-pirot",
    title: "Porez na imovinu (LPA Pirot)",
    summary:
      "Prijava poreza na kuću ili stan kod Lokalne poreske administracije Grada Pirota (PPI-2 za građane). Možete i da zatražite uverenje da je porez plaćen.",
    group: "pirot",
    example: "treba da prijavim porez na kuću u Pirotu",
  },
  {
    slug: "informacija-o-lokaciji-pirot",
    title: "Informacija o lokaciji (Pirot)",
    summary:
      "Pre gradnje u Pirotu, Gradska uprava kaže šta sme da se gradi na parceli. To nije građevinska dozvola — prvi korak pre objedinjene procedure.",
    group: "pirot",
    example: "šta smem da gradim na parceli u Pirotu",
  },
];

export function servicesInGroup(group: GroupId) {
  return SERVICES.filter((s) => s.group === group);
}
