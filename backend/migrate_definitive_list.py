"""
Migration : aligne la DB sur la "LISTE DEFINITIVE DES VOLS 1-2-3.docx".

Actions :
1. Masquer 6 pèlerins qui ne sont plus dans la liste définitive
2. Corriger MEITE MAMADOU (passeport + vol)
3. Démasquer KONE FATOUMATA (présente dans la liste définitive Vol 2)
4. Ajouter 12 nouveaux pèlerins (présents dans le docx, absents de DB)

Idempotent — peut être relancé sans risque (UPDATE/INSERT conditionnels).

Usage :
    cd backend && python migrate_definitive_list.py
"""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "pelerins.db")

# Templates de vols par voyage (extraits de la DB de prod, doivent rester cohérents)
VOL_TEMPLATES = {
    "VOYAGE 1": {
        "vol_aller_1": "ET 934 — 18 MAI — ABJ – ADD  12H00MN – 21H00 MN",
        "vol_aller_2": "ET 402 — 19 MAI — ADD – JEDD 00H10MN – 2H40MN",
        "vol_retour_1": "ET 443 — 09 JUN — MED – ADD 03H50MN – 6H50 MN",
        "vol_retour_2": "ET 935 — 09 JUN — ADD – ABJ  10H30MN – 13H 45MN",
    },
    "VOYAGE 2": {
        "vol_aller_1": "ET 513S — 19 MAI — ABJ - ADD  12H35MN – 21H35MN",
        "vol_aller_2": "ET 402S — 20 MAI — ADD – JEDD 00H10MN – 2H40MN",
        "vol_retour_1": "ET 443B — 10 JUN — MED – ADD 03H50MN – 6H50MN",
        "vol_retour_2": "ET 512B — 10 JUN — ADD – ABJ 09H00MN – 12H40MN",
    },
    "VOYAGE 3": {
        "vol_aller_1": "ET 934S — 20 MAI — ABJ – ADD 12H00MN – 21H00MN",
        "vol_aller_2": "ET402S — 21 MAI — ADD – JEDD 00H10MN – 2H40MN",
        "vol_retour_1": "ET 443B — 11 JUN — MED – ADD 3H50MN – 6H50MN",
        "vol_retour_2": "ET935B — 11 JUN — ADD – ABJ 10H50MN – 13H45MN",
    },
}

# 1) Pèlerins encore visibles en DB mais absents de la liste définitive → à masquer
TO_HIDE_BY_PASSPORT = [
    "23AP29095",  # FOFANA SORY (Vol 1)
    "23AP00699",  # CISSE AMED (Vol 3)
    "25AC23723",  # OUATTARA LACINA (Vol 3)
    "25AC63724",  # TOURE MARIAME (Vol 3)
    "22AI64472",  # DIALLO MOHAMED LAMINE (Vol 3)
    "23AP01175",  # DIALLO OUMAR (Vol 3)
]

# 2) Démasquer les pèlerins présents dans la liste définitive
#    Inclut KONE FATOUMATA + 17 pèlerins du VOYAGE 3 listés à la fois dans
#    EN SOURDINE et dans la liste définitive (la liste définitive prévaut)
TO_UNHIDE_BY_PASSPORT = [
    "24AC23620",  # KONE FATOUMATA (Vol 2)
    # ----- VOYAGE 3 -----
    "25AC50978",  # SIDIME AISSATA
    "22AK22012",  # SONGUE ALPHA SISSOU
    "25AC33625",  # MANGARA HALIMATA
    "25AC69067",  # YAO KOFFI
    "25AC53626",  # BAMBA MARIAM
    "25AC73704",  # CAMARA MARIAM
    "23AP03194",  # DIALLO MARIAM
    "25AC74342",  # SANOGO MOUSTAPHA
    "25AA90205",  # DIOURI NABIL
    "24AV33876",  # BAMA SANOGO
    "25AC24903",  # SANA SAYOUBA
    "24AA27493",  # GNAN TRAORE
    "25AC37467",  # TUO YOVONGO
    "25AD24271",  # TRAORE SITTA
    "25AD09033",  # TRAORE SAFIATOU
    "24AV36557",  # DIOMANDE BANGALY (statut PELERIN MB dans docx)
    "25AC35454",  # SOUARE HADI (statut PELERIN MB dans docx)
]

# Mises à jour de statut depuis la liste définitive
STATUT_UPDATES = [
    {"passport": "24AV36557", "statut": "PELERIN MB"},  # DIOMANDE BANGALY
    {"passport": "25AC35454", "statut": "PELERIN MB"},  # SOUARE HADI
]

# 3) Corrections : MEITE MAMADOU (passeport + vol)
PASSPORT_CORRECTIONS = [
    {
        "old_passport": "22AI36468",
        "new_passport": "22AI36168",
        "new_vol": "VOYAGE 1",
        "note": "MEITE MAMADOU - ENCADREMENT (Vol 2 → Vol 1, correction passeport)",
    },
]

# 4) Pèlerins à ajouter (présents dans docx, absents de DB)
NEW_PELERINS = [
    # Vol 2
    {"nom": "DIOMANDE", "prenom": "MONTA",                    "numero_passeport": "25AC47144", "numero_vol": "VOYAGE 2", "statut": "PELERIN"},
    # Vol 3
    {"nom": "BASSOLE",  "prenom": "LASSANE",                  "numero_passeport": "24AT98856", "numero_vol": "VOYAGE 3", "statut": "PELERIN"},
    {"nom": "TRAORE",   "prenom": "FATOUMATA",                "numero_passeport": "25AC23010", "numero_vol": "VOYAGE 3", "statut": "PELERIN"},
    {"nom": "ADAMA",    "prenom": "TRAORE",                   "numero_passeport": "24AT95060", "numero_vol": "VOYAGE 3", "statut": "PELERIN"},
    {"nom": "DJADOU",   "prenom": "MINATTA OUATTARA",         "numero_passeport": "25AD30849", "numero_vol": "VOYAGE 3", "statut": "PELERIN PLT"},
    {"nom": "SREMAN",   "prenom": "KADJO MALICK MAZO",        "numero_passeport": "25AD29982", "numero_vol": "VOYAGE 3", "statut": "PELERIN PLT"},
    {"nom": "DOSSO",    "prenom": "MONKOUROU",                "numero_passeport": "25AC70373", "numero_vol": "VOYAGE 3", "statut": "PELERIN PLT"},
    {"nom": "SANGARE",  "prenom": "MORY",                     "numero_passeport": "24AV29873", "numero_vol": "VOYAGE 3", "statut": "PELERIN PLT"},
    {"nom": "KAMAGATE", "prenom": "NAKOYA",                   "numero_passeport": "24AT86550", "numero_vol": "VOYAGE 3", "statut": "PELERIN"},
    {"nom": "KEITA",    "prenom": "NANOUMOU SEKOU",           "numero_passeport": "24AV13858", "numero_vol": "VOYAGE 3", "statut": "PELERIN"},
    {"nom": "SAMAKE",   "prenom": "EPSE DIAKITE SALIMATA",    "numero_passeport": "25AA36680", "numero_vol": "VOYAGE 3", "statut": "PELERIN"},
    {"nom": "DOSSO",    "prenom": "FATOUMATA",                "numero_passeport": "25AC24131", "numero_vol": "VOYAGE 3", "statut": "PELERIN"},
]


def main():
    if not os.path.isfile(DB_PATH):
        raise SystemExit(f"DB introuvable : {DB_PATH}")

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    print("=" * 60)
    print("MIGRATION : alignement sur LISTE DEFINITIVE DES VOLS 1-2-3")
    print("=" * 60)

    # ---- 1) MASQUER les 6 pèlerins qui ne sont plus dans la liste ----
    print("\n[1] Masquage des pèlerins absents de la liste définitive")
    placeholders = ",".join("?" * len(TO_HIDE_BY_PASSPORT))
    cur.execute(
        f"UPDATE pelerin SET masque = 1 "
        f"WHERE UPPER(TRIM(numero_passeport)) IN ({placeholders})",
        [p.upper().strip() for p in TO_HIDE_BY_PASSPORT],
    )
    print(f"  ✓ {cur.rowcount} pèlerins masqués (sur {len(TO_HIDE_BY_PASSPORT)} dans la liste)")

    # ---- 2) DÉMASQUER KONE FATOUMATA ----
    print("\n[2] Démasquage des pèlerins remis dans la liste définitive")
    placeholders2 = ",".join("?" * len(TO_UNHIDE_BY_PASSPORT))
    cur.execute(
        f"UPDATE pelerin SET masque = 0 "
        f"WHERE UPPER(TRIM(numero_passeport)) IN ({placeholders2})",
        [p.upper().strip() for p in TO_UNHIDE_BY_PASSPORT],
    )
    print(f"  ✓ {cur.rowcount} pèlerin(s) démasqué(s)")

    # ---- 2bis) Mise à jour des statuts ----
    print("\n[2bis] Mise à jour des statuts (PELERIN MB, etc.)")
    for s in STATUT_UPDATES:
        cur.execute(
            "UPDATE pelerin SET statut = ? WHERE UPPER(TRIM(numero_passeport)) = ?",
            (s["statut"], s["passport"].upper().strip()),
        )
        if cur.rowcount > 0:
            print(f"  ✓ {s['passport']} → statut = {s['statut']}")
        else:
            print(f"  ⚠ {s['passport']} introuvable, statut non mis à jour")

    # ---- 3) CORRECTIONS de passeports + vol ----
    print("\n[3] Corrections de passeport/vol")
    for c in PASSPORT_CORRECTIONS:
        # Vérif que le old_passport existe
        cur.execute(
            "SELECT id, nom, prenom FROM pelerin WHERE UPPER(TRIM(numero_passeport)) = ?",
            (c["old_passport"].upper().strip(),),
        )
        row = cur.fetchone()
        if row:
            cur.execute(
                "UPDATE pelerin SET numero_passeport = ?, numero_vol = ?, "
                "vol_aller_1 = ?, vol_aller_2 = ?, vol_retour_1 = ?, vol_retour_2 = ? "
                "WHERE id = ?",
                (
                    c["new_passport"],
                    c["new_vol"],
                    VOL_TEMPLATES[c["new_vol"]]["vol_aller_1"],
                    VOL_TEMPLATES[c["new_vol"]]["vol_aller_2"],
                    VOL_TEMPLATES[c["new_vol"]]["vol_retour_1"],
                    VOL_TEMPLATES[c["new_vol"]]["vol_retour_2"],
                    row[0],
                ),
            )
            print(f"  ✓ {row[1]} {row[2]} : {c['old_passport']} → {c['new_passport']} ({c['new_vol']})")
        else:
            print(f"  ⚠ Passeport {c['old_passport']} introuvable, correction sautée — {c['note']}")

    # ---- 4) INSERT des 12 nouveaux pèlerins ----
    print("\n[4] Ajout des nouveaux pèlerins")
    inserted = 0
    for p in NEW_PELERINS:
        cur.execute(
            "SELECT id FROM pelerin WHERE UPPER(TRIM(numero_passeport)) = ?",
            (p["numero_passeport"].upper().strip(),),
        )
        if cur.fetchone() is None:
            tpl = VOL_TEMPLATES[p["numero_vol"]]
            cur.execute(
                "INSERT INTO pelerin "
                "(nom, prenom, numero_passeport, numero_vol, "
                "vol_aller_1, vol_aller_2, vol_retour_1, vol_retour_2, "
                "statut, source_fichier, masque) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,0)",
                (
                    p["nom"], p["prenom"], p["numero_passeport"], p["numero_vol"],
                    tpl["vol_aller_1"], tpl["vol_aller_2"],
                    tpl["vol_retour_1"], tpl["vol_retour_2"],
                    p["statut"], "LISTE DEFINITIVE DES VOLS 1-2-3.docx",
                ),
            )
            inserted += 1
            print(f"  + {p['nom']} {p['prenom']} ({p['numero_passeport']}) — {p['numero_vol']} [{p['statut']}]")
        else:
            print(f"  · {p['nom']} {p['prenom']} déjà en DB — sauté")
    print(f"  ✓ {inserted} pèlerin(s) ajouté(s)")

    con.commit()

    # ---- BILAN ----
    cur.execute("SELECT COUNT(*) FROM pelerin")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM pelerin WHERE masque = 1")
    masques = cur.fetchone()[0]
    cur.execute("SELECT DISTINCT numero_vol FROM pelerin")
    vols = [r[0] for r in cur.fetchall()]

    print("\n" + "=" * 60)
    print("BILAN")
    print("=" * 60)
    print(f"  Total pèlerins   : {total}")
    print(f"  Visibles         : {total - masques}")
    print(f"  Masqués          : {masques}")
    print(f"  Vols distincts   : {sorted(vols)}")

    # Détail par vol
    print("\n  Détail par vol :")
    for v in sorted(vols):
        cur.execute(
            "SELECT COUNT(*) FROM pelerin WHERE numero_vol = ? AND masque = 0",
            (v,),
        )
        visible = cur.fetchone()[0]
        cur.execute(
            "SELECT COUNT(*) FROM pelerin WHERE numero_vol = ? AND masque = 1",
            (v,),
        )
        masque = cur.fetchone()[0]
        print(f"    {v}: {visible} visibles + {masque} masqués = {visible + masque}")

    con.close()
    print("\n✓ Migration terminée")


if __name__ == "__main__":
    main()
