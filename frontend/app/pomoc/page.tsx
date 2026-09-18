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
          <li>Pročitajte korake, šta fali i tačnu adresu šaltera.</li>
        </ol>
      </div>

      <div className="panel">
        <h2 style={{ marginTop: 0 }}>Šta ovo nije</h2>
        <ul>
          <li>Ne šaljemo zahtev umesto vas.</li>
          <li>Ne zakazujemo termin i ne pratimo „moji postupci“.</li>
          <li>Ne overavamo da je dokument originalan — samo da li fali ili je istekao datum na skenu.</li>
        </ul>
      </div>

      <div className="disclaimer">
        Ako niste sigurni, opišite problem svojim rečima. Ako nijedna kartica
        nije tačna, dopunite opis.
      </div>
    </>
  );
}
