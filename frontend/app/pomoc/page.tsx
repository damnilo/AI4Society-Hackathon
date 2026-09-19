import { DISCLAIMER } from "@/lib/copy";

export default function PomocPage() {
  return (
    <>
      <h1>Pomoć</h1>
      <p className="lede">
        Putokaz je vodič, nije četbot i nije eUprava. Jedan ekran, velika slova,
        jedan korak.
      </p>

      <div className="panel">
        <h2 style={{ marginTop: 0 }}>Pitch za žiri</h2>
        <p>
          eUprava pomaže kad već znaš ime usluge. Putokaz kreće od namere i
          papira: predloži proceduru, checklist sa skena i nadležni šalter —
          bez eID-a, bez podnošenja zahteva.
        </p>
        <p className="note" style={{ marginBottom: 0 }}>
          Demo rečenice: „istekla mi je lična“ · „selim se iz Pirota u Beograd“
          (Ljermontova 12a).
        </p>
      </div>

      <div className="panel">
        <h2 style={{ marginTop: 0 }}>Kako se koristi</h2>
        <ol className="steps" style={{ paddingLeft: 22 }}>
          <li>
            Na početnoj opišite šta treba, recite naglas („Reci naglas“ /
            „Slušam…“), ili izaberite brzi pristup.
          </li>
          <li>Po želji priložite sken (JPG, PNG, PDF) uz zahtev.</li>
          <li>Izaberite jednu od 2–3 ponuđene procedure.</li>
          <li>
            Na vodiču: koraci, šta fali / je isteklo, adresa šaltera, mapa ako
            ima koordinate, „Pročitaj vodič“ (OpenAI ili glas pregledača) i
            „Štampaj vodič“.
          </li>
        </ol>
      </div>

      <div className="panel">
        <h2 style={{ marginTop: 0 }}>Nalog i papiri</h2>
        <p>
          Prijava je opciona. Traženje procedure radi i kao gost. Nalog čuva
          skenove i mesto (Pirot / Beograd / Niš) da ih ne unosite svaki put.
          Prilog gosta se briše posle 48 sati ako ga nalogom ne preuzmete.
          Možete da obrišete papir ili da se odjavite.
        </p>
      </div>

      <div className="panel">
        <h2 style={{ marginTop: 0 }}>Šta ovo nije</h2>
        <ul>
          <li>Ne šaljemo zahtev umesto vas.</li>
          <li>Ne zakazujemo termin i ne pratimo „moji postupci“.</li>
          <li>
            Checklist jeste provera polja sa skena (ima, fali, datum). Nije
            pravna overa niti dokaz da je papir originalan.
          </li>
        </ul>
      </div>

      <p className="disclaimer">{DISCLAIMER}</p>
    </>
  );
}
