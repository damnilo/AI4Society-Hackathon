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
        <h2>Šta je Putokaz</h2>
        <p>
          Putokaz je vodič kroz administrativne procedure u Srbiji. Opišete
          svojim rečima šta želite da završite, a Putokaz vam kaže koja je
          procedura, šta treba da ponesete i na koji šalter da odete.
        </p>
        <p>
          Za razliku od eUprave, ne morate unapred da znate naziv usluge.
          Krećete od namere — na primer „istekla mi je lična“ ili „selim se iz
          Pirota u Beograd“ — a Putokaz prepozna proceduru, napravi listu
          potrebnih dokumenata i proveri skenove koje priložite: šta imate, šta
          fali i da li je nešto isteklo.
        </p>
        <p className="note" style={{ marginBottom: 0 }}>
          Putokaz vas usmerava i priprema. Ne podnosi zahtev umesto vas i nije
          zvanična eUprava.
        </p>
      </div>

      <div className="panel">
        <h2>Kako se koristi</h2>
        <ol className="howto">
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
        <h2>Nalog i papiri</h2>
        <p>
          Prijava je opciona. Traženje procedure radi i kao gost. Nalog čuva
          skenove i mesto (Pirot / Beograd / Niš) da ih ne unosite svaki put.
          Prilog gosta se briše posle 48 sati ako ga nalogom ne preuzmete.
          Možete da obrišete papir ili da se odjavite.
        </p>
      </div>

      <div className="panel">
        <h2>Šta ovo nije</h2>
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
