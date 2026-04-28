import React, { useState } from "react";
import "./App.css";

const API_URL = "";

// Dictionnaire des codes IATA / aéroports utilisés dans les vols
const AIRPORT_NAMES = {
  ABJ: "Abidjan",
  ADD: "Addis-Abeba",
  JEDD: "Djeddah",
  JED: "Djeddah",
  MED: "Médine",
  CMN: "Casablanca",
  CDG: "Paris",
  IST: "Istanbul",
  CAI: "Le Caire",
  DXB: "Dubaï",
  DOH: "Doha",
  RUH: "Riyad",
};

// Codes compagnies aériennes
const AIRLINE_NAMES = {
  ET: "Ethiopian Airlines",
  AT: "Royal Air Maroc",
  AF: "Air France",
  TK: "Turkish Airlines",
  MS: "EgyptAir",
  EK: "Emirates",
  QR: "Qatar Airways",
  SV: "Saudia",
};

const cityName = (code) =>
  code ? AIRPORT_NAMES[code.toUpperCase()] || code : code;

const airlineName = (code) =>
  code ? AIRLINE_NAMES[code.toUpperCase()] || code : code;

// Convertit "12H00" / "0H10" / "00H10" → minutes depuis minuit (entier)
function timeToMinutes(t) {
  if (!t) return null;
  const m = t.toString().toUpperCase().match(/(\d{1,2})\s*H\s*(\d{1,2})?/);
  if (!m) return null;
  return parseInt(m[1], 10) * 60 + parseInt(m[2] || "0", 10);
}

// Calcule la date d'arrivée à partir d'une date de départ (ex: "18 MAI") et
// des heures départ/arrivée. Si l'arrivée est avant le départ ⇒ jour suivant.
const MOIS_FR = ["JAN", "FEV", "MAR", "AVR", "MAI", "JUN", "JUL", "AOU", "SEP", "OCT", "NOV", "DEC"];
function computeArrivalDate(date, depart, arrival) {
  if (!date) return "";
  const dm = date.toUpperCase().match(/(\d{1,2})\s+([A-ZÉÈÀÂÊÎÔÛ]+)/);
  if (!dm) return date;
  const day = parseInt(dm[1], 10);
  const monthLabel = dm[2].slice(0, 3);
  const monthIdx = MOIS_FR.indexOf(monthLabel);
  if (monthIdx < 0) return date;

  const depMin = timeToMinutes(depart);
  const arrMin = timeToMinutes(arrival);
  const crossesMidnight = depMin != null && arrMin != null && arrMin < depMin;

  if (!crossesMidnight) return date;

  // Vol traverse minuit → +1 jour (gestion fin de mois)
  const daysInMonth = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  let newDay = day + 1;
  let newMonthIdx = monthIdx;
  if (newDay > daysInMonth[monthIdx]) {
    newDay = 1;
    newMonthIdx = (monthIdx + 1) % 12;
  }
  return `${newDay} ${MOIS_FR[newMonthIdx]}`;
}

// Parse une chaîne du type :
//   "ET 934 — 18 MAI — ABJ – ADD 12H00MN – 21H00 MN"
// → { airline: "ET", flight: "934", date: "18 MAI",
//     from: "ABJ", to: "ADD", depart: "12H00", arrival: "21H00",
//     arrivalDate: "18 MAI" (ou jour suivant si vol traverse minuit) }
function parseFlight(str) {
  if (!str || typeof str !== "string") return null;
  const cleaned = str.replace(/\s+/g, " ").trim();
  const parts = cleaned.split(/\s+[—–-]\s+/);

  if (parts.length >= 5) {
    const flightHeader = parts[0].trim().split(/\s+/);
    const airline = flightHeader[0] || "";
    const flight = flightHeader.slice(1).join(" ");
    const date = parts[1].trim();
    const from = parts[2].trim();
    const toAndDep = parts[3].trim().split(/\s+/);
    const to = toAndDep[0] || "";
    const depart = (toAndDep.slice(1).join(" ") || "").replace(/MN$/i, "").trim();
    const arrival = parts[4].trim().replace(/MN$/i, "").trim();
    const arrivalDate = computeArrivalDate(date, depart, arrival);
    return { raw: cleaned, airline, flight, date, from, to, depart, arrival, arrivalDate };
  }
  return { raw: cleaned, airline: "", flight: "", date: "", from: "", to: "", depart: "", arrival: "", arrivalDate: "" };
}

function FlightLeg({ flight, type, index, isLast }) {
  const f = parseFlight(flight);
  if (!f) return null;

  const isAller = type === "aller";

  return (
    <div className="flight-leg">
      <div className="flight-leg-header">
        <span className="flight-step">
          Étape {index}
        </span>
        {f.date && <span className="flight-date">{f.date}</span>}
      </div>

      <div className="flight-route">
        <div className="route-airport">
          <div className="route-code">{f.from}</div>
          <div className="route-city">{cityName(f.from)}</div>
          {f.depart && <div className="route-time">{f.depart}</div>}
          {f.date && <div className="route-date">{f.date}</div>}
        </div>

        <div className="route-arrow" aria-hidden>
          <span className="route-arrow-line" />
          <span className="route-arrow-icon">{isAller ? "→" : "←"}</span>
        </div>

        <div className="route-airport">
          <div className="route-code">{f.to}</div>
          <div className="route-city">{cityName(f.to)}</div>
          {f.arrival && <div className="route-time">{f.arrival}</div>}
          {f.arrivalDate && <div className="route-date">{f.arrivalDate}</div>}
        </div>
      </div>

      {(f.airline || f.flight) && (
        <div className="flight-meta">
          <span className="meta-tag">
            {airlineName(f.airline)}{f.flight ? ` · vol ${f.airline} ${f.flight}` : ""}
          </span>
        </div>
      )}

      {!isLast && (
        <div className="layover-divider">
          <span className="layover-line" />
          <span className="layover-label">⏱ Escale à {cityName(f.to)}</span>
          <span className="layover-line" />
        </div>
      )}
    </div>
  );
}

function JourneyBlock({ legs, type }) {
  const validLegs = (legs || []).filter(Boolean);
  if (validLegs.length === 0) return null;

  const isAller = type === "aller";

  return (
    <div className={`trip-block ${isAller ? "aller-block" : "retour-block"}`}>
      <div className="trip-block-title">
        <span className="trip-icon">{isAller ? "✈️" : "🏠"}</span>{" "}
        {isAller ? "Voyage aller" : "Voyage retour"}
      </div>

      <div className={`flight-card ${isAller ? "is-aller" : "is-retour"}`}>
        {validLegs.map((leg, i) => (
          <FlightLeg
            key={i}
            flight={leg}
            type={type}
            index={i + 1}
            isLast={i === validLegs.length - 1}
          />
        ))}
      </div>
    </div>
  );
}

function TripSummary({ pelerin }) {
  const aller1 = parseFlight(pelerin.vol_aller_1);
  const allerLast = parseFlight(pelerin.vol_aller_2 || pelerin.vol_aller_1);
  const retour1 = parseFlight(pelerin.vol_retour_1);
  const retourLast = parseFlight(pelerin.vol_retour_2 || pelerin.vol_retour_1);

  if (!aller1 && !retour1) return null;

  return (
    <div className="trip-summary">
      <p className="trip-summary-line">
        🛫 <strong>Départ</strong> : {aller1?.date || "—"} depuis{" "}
        <strong>{cityName(aller1?.from) || "—"}</strong>, arrivée le{" "}
        <strong>{allerLast?.date || "—"}</strong> à{" "}
        <strong>{cityName(allerLast?.to) || "—"}</strong>
      </p>
      <p className="trip-summary-line">
        🛬 <strong>Retour</strong> : {retour1?.date || "—"} depuis{" "}
        <strong>{cityName(retour1?.from) || "—"}</strong>, arrivée le{" "}
        <strong>{retourLast?.date || "—"}</strong> à{" "}
        <strong>{cityName(retourLast?.to) || "—"}</strong>
      </p>
    </div>
  );
}

function App() {
  const [passport, setPassport] = useState("");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!passport.trim()) return;

    setLoading(true);
    setError("");
    setResults(null);

    try {
      const res = await fetch(
        `${API_URL}/api/search?passeport=${encodeURIComponent(passport.trim())}`
      );
      if (!res.ok) throw new Error("Erreur serveur");
      const data = await res.json();
      setResults(data);
    } catch (err) {
      setError("Erreur de connexion au serveur");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <div className="container">
        <div className="header">
          <div className="logo-area">
            <img src="/logo.jpg" alt="MUSFALA Voyage" className="logo-img" />
            <h1>MUSFALA Voyage</h1>
          </div>
          <p className="welcome-text">
            Bienvenue sur la plateforme de <strong>MUSFALA Voyage</strong>. Cette plateforme vous permet de vérifier si vous êtes sur notre liste de pèlerinage. Elle vous permet aussi de connaître la période approximative de votre voyage.
          </p>
        </div>

        <form onSubmit={handleSearch} className="search-form">
          <input
            type="text"
            value={passport}
            onChange={(e) => setPassport(e.target.value)}
            placeholder="Entrez votre numéro de passeport..."
            className="search-input"
            autoFocus
          />
          <button type="submit" disabled={loading} className="search-btn">
            {loading ? "Recherche..." : "🔍 Rechercher"}
          </button>
        </form>

        {error && <div className="error">{error}</div>}

        {results && results.count === 0 && (
          <div className="no-results">
            <span className="no-results-icon">😕</span>
            <p>Aucun pèlerin trouvé pour ce numéro de passeport.</p>
            <p className="hint">Vérifiez le numéro et réessayez.</p>
          </div>
        )}

        {results && results.count > 0 && (
          <div className="results">
            <h2>✅ {results.count} résultat{results.count > 1 ? "s" : ""} trouvé{results.count > 1 ? "s" : ""}</h2>
            {results.results.map((p, i) => (
              <div key={i} className="card">
                <div className="card-header">
                  <span className="pilgrim-name">{p.prenom} {p.nom}</span>
                  <span className="statut-badge">{p.statut}</span>
                </div>
                <div className="card-body">
                  <div className="card-row">
                    <span className="label">📄 N° Passeport</span>
                    <span className="value">{p.numero_passeport}</span>
                  </div>
                  <div className="card-row">
                    <span className="label">📋 N° Voyage</span>
                    <span className="value">{p.numero_vol}</span>
                  </div>

                  <TripSummary pelerin={p} />

                  <JourneyBlock legs={[p.vol_aller_1, p.vol_aller_2]} type="aller" />
                  <JourneyBlock legs={[p.vol_retour_1, p.vol_retour_2]} type="retour" />
                </div>
              </div>
            ))}
          </div>
        )}

        <footer className="footer">
          <p>© 2026 MUSFALA Voyage — Pèlerinage Hadj</p>
        </footer>
      </div>
    </div>
  );
}

export default App;
