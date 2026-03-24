import React, { useState } from "react";
import "./App.css";

const API_URL = "";

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
            <h2>✅ {results.count} résultat(s) trouvé(s)</h2>
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

                  <div className="flight-section">
                    <h3>✈️ Vols Aller</h3>
                    <div className="flight-leg">
                      <span className="leg-label">Aller 1</span>
                      <span className="leg-value">{p.vol_aller_1}</span>
                    </div>
                    <div className="flight-leg">
                      <span className="leg-label">Aller 2</span>
                      <span className="leg-value">{p.vol_aller_2}</span>
                    </div>
                  </div>

                  <div className="flight-section">
                    <h3>🔙 Vols Retour</h3>
                    <div className="flight-leg">
                      <span className="leg-label">Retour 1</span>
                      <span className="leg-value">{p.vol_retour_1}</span>
                    </div>
                    {p.vol_retour_2 && (
                      <div className="flight-leg">
                        <span className="leg-label">Retour 2</span>
                        <span className="leg-value">{p.vol_retour_2}</span>
                      </div>
                    )}
                  </div>
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
