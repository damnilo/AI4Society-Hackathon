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
        <h2 style={{ marginTop: 0 }}>Kako se koristi</h2>
        <ol className="steps" style={{ paddingLeft: 22 }}>
          <li>Na početnoj opišite šta treba, ili izaberite brzi pristup.</li>
          <li>Izaberite jednu od 2–3 ponuđene procedure.</li>
          <li>Pročitajte korake, šta fali / je isteklo i tačnu adresu šaltera.</li>
        </ol>
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

      <div className="panel">
        <h2 style={{ marginTop: 0 }}>Nalog i papiri</h2>
        <p>
          Prijava je opciona. Čuva samo skenove koje vi otpremite, da ih ne
          unosite svaki put. Možete da obrišete papir ili da se odjavite.
          Traženje procedure radi i kao gost.
        </p>
      </div>

      <p className="disclaimer">{DISCLAIMER}</p>
    </>
  );
}
