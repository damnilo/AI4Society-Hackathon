# Katalog Putokaz (Faza 0 — zajednička lista)

Ti = **backend**, kolega = **frontend**. Ovo je ugovor za seed; FE ne hardkodira procedure ni adrese.

`last_verified_at`: 2026-09-18.

## Mesta (`municipalities.json`)

Hijerarhija `parent_id`. Resolver: tekst → `aliases` → id → ide **naglore** dok ne nađe office čiji je `covers_place_id` u tom lancu. LLM i dalje ne piše ulicu.

- `kind`: `district` | `city` | `municipality`
- Palilula u BG = `beograd-palilula`; u Nišu = `nis-palilula` (alias „палилула“ ide na BG jer je češći; za Niš koristi „палилула ниш“)

Primeri:

- Voždovac → `vozdovac` → `beograd` → `pu-beograd-upravni` (Ljermontova 12a)
- „selim se u Beograd“ → `beograd` → ista kancelarija
- Dimitrovgrad → `dimitrovgrad` → `pirotski` → `pu-pirot`
- Medijana → `nis-medijana` → `nis` → `niski` → `pu-nis`
- Nepoznato mesto → `office_missing`

Seed nije cela Srbija: 17 beogradskih opština, 5 niških, 4 pirotske + 3 roditelja (`beograd`, `nis`/`niski`, `pirotski`). Ostalo se doda istim JSON-om.

## Kancelarije (`offices.json`)

`covers_place_id` je koren pokrivenog podstabla. `covers_municipality` ostaje kao stari slug.

| id | mesto | adresa | telefon | lat, lng | demo uloga |
|---|---|---|---|---|---|
| `pu-pirot` | Pirot | Jevrejska 17 | 010/353-077 | 43.1555, 22.5858 | stari grad; **nije** šalter za novo prebivalište u BG |
| `pu-beograd-upravni` | Beograd | Ljermontova 12a | 011/3470-200 | 44.7828, 20.4906 | `new_residence` / `current_residence` na BG |
| `pu-nis` | Niš | Nade Tomić 14 | 018/511-222 | 43.321, 21.8954 | kontrola resolvera |

Resolver: LLM ne piše ulicu. Pirot → Beograd + `prijava-prebivalista` (`jurisdiction_rule=new_residence`) → **samo** `pu-beograd-upravni`.

## Procedure (`procedures.json`) — 15

Namerno bliski parovi za matching: prebivalište vs boravište; LK vs pasoš; prva LK vs zamena; prva vozačka vs zamena.

| slug | naslov | institucija | jurisdiction_rule | kanal | žiri / matching |
|---|---|---|---|---|---|
| `prijava-prebivalista` | Prijava prebivališta | mup | **new_residence** | both | Scenario 2: „selim se iz Pirota u Beograd“ |
| `prijava-boravista` | Prijava boravišta | mup | new_residence | both | Kontrast stalno vs privremeno |
| `uverenje-o-prebivalistu` | Uverenje o prebivalištu | mup | **current_residence** | counter | BG = Ljermontova (MUP tekst) |
| `licna-karta-prvo-izdavanje` | Prvo izdavanje LK | mup | current_residence | both | Prva LK, ne zamena |
| `licna-karta-zamena` | Zamena LK | mup | current_residence | both | Scenario 1: „istekla mi je lična“ |
| `pasos-izdavanje` | Pasoš | mup | current_residence | both | Blizu LK, drugi dokument |
| `vozacka-dozvola-izdavanje` | Prva vozačka | mup | current_residence | counter | Posle auto-škole |
| `vozacka-dozvola-zamena` | Zamena vozačke | mup | current_residence | both | Istekla vozačka |
| `izvod-maticne-rodjenih` | Izvod / rodni list | maticar | applicant_municipality | both | eIzvod `00015`; office često `office_missing` |
| `uverenje-o-drzavljanstvu` | Uverenje o državljanstvu | maticar | applicant_municipality | both | Uz prvu LK |
| `izbor-izabranog-lekara` | Izabrani lekar | rfzo | new_residence | both | Related posle selidbe; nije MUP office |
| `registracija-vozila` | Registracija vozila | mup | applicant_municipality | counter | Nije vozačka |
| `prijava-preduzetnika` | Preduzetnik APR | apr | applicant_municipality | both | `office_missing` + apr.gov.rs |
| `ezakazivanje-licna-pasos` | eZakazivanje LK/pasoš | mup | current_residence | online | Samo termin, usluga `00005` |
| `saglasnost-vlasnika-prebivaliste` | Saglasnost vlasnika | mup | new_residence | online | Related uz prijavu; `01048` |

Kartice na FE: **bez** institucije kao naslova. Institucija i adresa tek u `guide` posle `select`.

## Tipovi dokumenata (za Vision / checklist)

`licna_karta`, `pasos`, `vozacka_dozvola`, `uplatnica_euprava`, `dokaz_pravnog_osnova`, `saglasnost_vlasnika`, `saglasnost_roditelja`, `izvod_rodjeni`, `uverenje_drzavljanstvo`, `lekarsko_vozac`, `dokaz_ispit_voznje`, `zdravstvena_isprava`, `saobracajna_dozvola`, `polisa_osiguranja`, `tehnicki_pregled`, `apr_obrazac`.

Statusi: `complete` | `missing` | `expired` | `unreadable` | `mismatch`. Nikad „overeno“.

## Šta kolega (FE) treba da zna

- Mock `/cases` za „istekla mi je lična“ → kandidati oko `licna-karta-zamena` (+ pasoš / prva LK).
- Mock „selim se iz Pirota u Beograd“ → `prijava-prebivalista` (+ boravište / lekar).
- Guide za scenario 2: office = Ljermontova 12a, ne Jevrejska 17.
