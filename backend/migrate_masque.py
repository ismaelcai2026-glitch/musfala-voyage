"""
Migration : ajoute la colonne `masque` à la table `pelerin` (si absente),
puis marque comme masqués les 24 pèlerins du fichier "EN SOURDINE.docx"
(liste VOL 3 à mettre en sourdine).

Idempotent — peut être relancé sans risque (réinitialise toujours la liste
masqués pour ne marquer que ceux fournis ici).

Usage :
    cd backend && python migrate_masque.py
"""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "pelerins.db")

# Liste des numéros de passeport à masquer (extraits de EN SOURDINE.docx)
PASSPORTS_TO_HIDE = [
    "25AC50978",  # SIDIME AISSATA
    "21AH52173",  # SIMPARA ALIMA LAETITIA
    "22AK22012",  # SONGUE ALPHA SISSOU
    "25AC33625",  # MANGARA HALIMATA
    "25AC53626",  # BAMBA MARIAM
    "25AC73704",  # CAMARA MARIAM
    "23AP03194",  # DIALLO MARIAM
    "25AA41779",  # TRAORE MARIAM
    "25AD24271",  # TRAORE SITTA
    "25AC42271",  # TRAORE MOUSSA
    "25AC74342",  # SANOGO MOUSTAPHA
    "25AA90205",  # DIOURI NABIL
    "25AD09033",  # TRAORE SAFIATOU
    "24AV33876",  # BAMA SANOGO
    "25AC52063",  # DIAKITE SANOUSSI
    "25AC24903",  # SANA SAYOUBA
    "24AA27493",  # GNAN TRAORE
    "25AC37467",  # TUO YOVONGO
    "24AV36557",  # DIOMANDE BANGALY
    "25AC35454",  # SOUARE HADI
    "25AC75073",  # SAKO HOUSSOUMANE
    "25AC69067",  # YAO KOFFI
    "24AC23620",  # KONE FATOUMATA
]

# Pèlerins sans numéro de passeport, à matcher par nom + prénom
NAMES_TO_HIDE = [
    ("NIMAGA", "ABASS"),
]

# Pèlerins listés "EN SOURDINE" mais absents de la base.
# On les INSÈRE comme pèlerins du VOYAGE 3, déjà masqués.
# Les vols correspondent au template VOYAGE 3 standard.
VOYAGE_3_TEMPLATE = {
    "numero_vol": "VOYAGE 3",
    "vol_aller_1": "ET 934S — 20 MAI — ABJ – ADD 12H00MN – 21H00MN",
    "vol_aller_2": "ET402S — 21 MAI — ADD – JEDD 00H10MN – 2H40MN",
    "vol_retour_1": "ET 443B — 11 JUN — MED – ADD 3H50MN – 6H50MN",
    "vol_retour_2": "ET935B — 11 JUN — ADD – ABJ 10H50MN – 13H45MN",
    "statut": "PELERIN",
    "source_fichier": "EN SOURDINE.docx",
}
MISSING_TO_INSERT = [
    {"nom": "TRAORE",   "prenom": "SITTA",    "numero_passeport": "25AD24271"},
    {"nom": "TRAORE",   "prenom": "SAFIATOU", "numero_passeport": "25AD09033"},
    {"nom": "DIOMANDE", "prenom": "BANGALY",  "numero_passeport": "24AV36557"},
    {"nom": "SOUARE",   "prenom": "HADI",     "numero_passeport": "25AC35454"},
]


def main():
    if not os.path.isfile(DB_PATH):
        raise SystemExit(f"DB introuvable : {DB_PATH}")

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # 1) Ajouter la colonne `masque` si elle n'existe pas
    cur.execute("PRAGMA table_info(pelerin)")
    cols = [row[1] for row in cur.fetchall()]
    if "masque" not in cols:
        cur.execute("ALTER TABLE pelerin ADD COLUMN masque BOOLEAN NOT NULL DEFAULT 0")
        con.commit()
        print("✓ Colonne `masque` ajoutée à la table pelerin")
    else:
        print("· Colonne `masque` déjà présente")

    # 2) Insertion des pèlerins manquants (idempotent : on vérifie d'abord)
    inserted = 0
    for p in MISSING_TO_INSERT:
        cur.execute(
            "SELECT id FROM pelerin WHERE UPPER(TRIM(numero_passeport)) = ?",
            (p["numero_passeport"].upper().strip(),),
        )
        if cur.fetchone() is None:
            cur.execute(
                "INSERT INTO pelerin "
                "(nom, prenom, numero_passeport, numero_vol, "
                "vol_aller_1, vol_aller_2, vol_retour_1, vol_retour_2, "
                "statut, source_fichier, masque) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,1)",
                (
                    p["nom"], p["prenom"], p["numero_passeport"],
                    VOYAGE_3_TEMPLATE["numero_vol"],
                    VOYAGE_3_TEMPLATE["vol_aller_1"],
                    VOYAGE_3_TEMPLATE["vol_aller_2"],
                    VOYAGE_3_TEMPLATE["vol_retour_1"],
                    VOYAGE_3_TEMPLATE["vol_retour_2"],
                    VOYAGE_3_TEMPLATE["statut"],
                    VOYAGE_3_TEMPLATE["source_fichier"],
                ),
            )
            inserted += 1
            print(f"  + INSERT {p['nom']} {p['prenom']} ({p['numero_passeport']})")
    if inserted:
        print(f"✓ {inserted} pèlerin(s) ajouté(s) en DB (déjà masqués)")
    else:
        print("· Aucun pèlerin à insérer (tous déjà présents)")
    con.commit()

    # 3) Reset à 0 (idempotent : on ne masque que la liste actuelle)
    cur.execute("UPDATE pelerin SET masque = 0")
    print(f"· Reset : {cur.rowcount} pèlerins remis à masque=0")

    # 4) Marquer par numéro de passeport (UPPER pour ignorer la casse)
    placeholders = ",".join("?" * len(PASSPORTS_TO_HIDE))
    cur.execute(
        f"UPDATE pelerin SET masque = 1 "
        f"WHERE UPPER(TRIM(numero_passeport)) IN ({placeholders})",
        [p.upper().strip() for p in PASSPORTS_TO_HIDE],
    )
    by_passport = cur.rowcount
    print(f"✓ {by_passport} pèlerins masqués par passeport "
          f"(sur {len(PASSPORTS_TO_HIDE)} dans la liste)")

    # 5) Marquer par nom + prénom pour les cas sans passeport
    by_name = 0
    for nom, prenom in NAMES_TO_HIDE:
        cur.execute(
            "UPDATE pelerin SET masque = 1 "
            "WHERE UPPER(TRIM(nom)) = ? AND UPPER(TRIM(prenom)) = ?",
            (nom.upper(), prenom.upper()),
        )
        if cur.rowcount > 0:
            by_name += cur.rowcount
            print(f"  · {nom} {prenom} → matché ({cur.rowcount})")
        else:
            print(f"  ⚠ {nom} {prenom} → AUCUN match en DB")

    con.commit()

    # 6) Bilan
    cur.execute("SELECT COUNT(*) FROM pelerin WHERE masque = 1")
    masked_total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM pelerin")
    grand_total = cur.fetchone()[0]
    expected = len(PASSPORTS_TO_HIDE) + len(NAMES_TO_HIDE)
    print()
    print(f"=== Bilan ===")
    print(f"  Pèlerins en DB    : {grand_total}")
    print(f"  Masqués           : {masked_total}")
    print(f"  Visibles          : {grand_total - masked_total}")
    print(f"  Attendu masqué    : {expected}")
    if masked_total != expected:
        print(f"  ⚠ Écart de {expected - masked_total} — vérifier les non-matchés ci-dessus")

    # Détail des passeports non trouvés (pour debug)
    cur.execute(
        f"SELECT numero_passeport FROM pelerin "
        f"WHERE UPPER(TRIM(numero_passeport)) IN ({placeholders})",
        [p.upper().strip() for p in PASSPORTS_TO_HIDE],
    )
    found_passports = {r[0].upper().strip() for r in cur.fetchall()}
    not_found = [p for p in PASSPORTS_TO_HIDE if p.upper().strip() not in found_passports]
    if not_found:
        print(f"  ⚠ Passeports non trouvés en DB : {not_found}")

    con.close()
    print("\n✓ Migration terminée")


if __name__ == "__main__":
    main()
