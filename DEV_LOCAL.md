# MUSFALA Voyage — Développement local

Stack actuelle : **FastAPI + Uvicorn + SQLModel + SQLite** (backend Python 3.10/3.11) servant un build React statique.

## Lancement rapide

Dans ton Terminal Mac :

```bash
cd /Users/coulibalylassinaeric/Documents/ProjetIA/musfala-voyage-local
chmod +x run.sh   # première fois seulement
./run.sh
```

L'app sera accessible sur **http://localhost:10000**

Le flag `--reload` est activé : chaque modification d'un fichier `.py` du backend recharge automatiquement le serveur.

## Structure

```
musfala-voyage-local/
├── backend/
│   ├── main.py            # endpoints API + serving frontend
│   ├── models.py          # modèle Pelerin (SQLModel)
│   ├── database.py        # init SQLite
│   ├── import_word.py     # parser .docx → DB
│   └── pelerins.db        # base SQLite (236 pèlerins)
├── frontend/
│   ├── build/             # bundle React déjà compilé (servi statiquement)
│   ├── public/, src/      # source React (à build avec npm run build)
│   └── package.json
├── run.sh                 # script de lancement
└── DEV_LOCAL.md           # ce fichier
```

## Endpoints disponibles

| URL | Description |
|---|---|
| `GET /` | App React (page d'accueil) |
| `GET /api/health` | Health check |
| `GET /api/stats` | Total pèlerins, vols, etc. |
| `GET /api/search?passeport=XXX` | Recherche par passeport |
| `POST /api/import` | Upload d'un .docx pour import |

## Workflow d'amélioration

1. **Modifier le backend** (Python) → uvicorn recharge automatiquement
2. **Modifier le frontend** (React) :
   - `cd frontend && npm install` (1ère fois)
   - `npm start` → dev server React sur http://localhost:3000 avec hot-reload
   - Ou `npm run build` → recompile le bundle dans `frontend/build/` puis recharge la page
3. **Tester localement** avant de déployer
4. **Push sur GitHub** → puis sur le VPS : `cd /opt/musfala-voyage && git pull && docker build -t musfala-voyage:latest . && docker rm -f musfala-voyage && docker run -d --name musfala-voyage --restart=always -w /app/backend -p 127.0.0.1:10000:10000 musfala-voyage:latest uvicorn main:app --host 0.0.0.0 --port 10000`

## Pistes d'amélioration suggérées

- [ ] Title HTML actuel = "React App" → mettre "MUSFALA Voyage"
- [ ] Le `<script defer src="/static/js/main.06e71bfd.js">` est référencé en absolu → OK pour FastAPI mais à vérifier sur sous-chemin
- [ ] Ajouter une auth basique sur `/api/import` (upload sensible)
- [ ] Logger les requêtes dans un fichier (audit)
- [ ] Pagination sur `/api/search`
- [ ] CORS actuellement `allow_origins=["*"]` → restreindre en prod
- [ ] Endpoint `/api/health` pourrait remonter le total de pèlerins (vérification rapide)
- [ ] Renommer la DB de `pelerins.db` vers `data/pelerins.db` et l'exclure du `git`
- [ ] Migration vers Postgres si besoin de scale
