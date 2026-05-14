from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from sqlalchemy import or_
from contextlib import asynccontextmanager
from typing import Optional
from models import Pelerin
from database import init_db, get_session
from import_word import import_docx
import tempfile
import os

MAX_RESULTS = 100  # plafond pour éviter de retourner toute la base sur une recherche courte

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "build")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="MUSFALA Voyage - Recherche Pèlerin", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/search")
def search_pelerin(
    q: Optional[str] = None,
    passeport: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """Recherche un pèlerin par passeport, nom ou prénom (insensible à la casse).

    - `q` : chaîne libre cherchée dans nom OR prénom OR numero_passeport
    - `passeport` : conservé pour rétrocompatibilité (cherche uniquement dans numero_passeport)
    """
    term = (q or passeport or "").strip()
    if len(term) < 2:
        raise HTTPException(
            status_code=400,
            detail="Saisissez au moins 2 caractères (nom, prénom ou numéro de passeport)",
        )

    pattern = f"%{term}%"
    if q is not None:
        # Recherche large : nom OR prénom OR passeport
        condition = or_(
            Pelerin.numero_passeport.ilike(pattern),
            Pelerin.nom.ilike(pattern),
            Pelerin.prenom.ilike(pattern),
        )
    else:
        # Mode legacy : passeport uniquement
        condition = Pelerin.numero_passeport.ilike(pattern)

    # Exclut les pèlerins marqués comme masqués + ordonne par nom puis prénom
    query = (
        select(Pelerin)
        .where(condition, Pelerin.masque == False)  # noqa: E712
        .order_by(Pelerin.nom, Pelerin.prenom)
        .limit(MAX_RESULTS + 1)  # +1 pour détecter le débordement
    )
    rows = session.exec(query).all()

    truncated = len(rows) > MAX_RESULTS
    results = rows[:MAX_RESULTS]

    return {
        "count": len(results),
        "truncated": truncated,
        "max_results": MAX_RESULTS,
        "results": [
            {
                "nom": r.nom,
                "prenom": r.prenom,
                "numero_passeport": r.numero_passeport,
                "numero_vol": r.numero_vol,
                "vol_aller_1": r.vol_aller_1,
                "vol_aller_2": r.vol_aller_2,
                "vol_retour_1": r.vol_retour_1,
                "vol_retour_2": r.vol_retour_2,
                "statut": r.statut,
            }
            for r in results
        ],
    }


@app.post("/api/import")
async def import_file(file: UploadFile = File(...), session: Session = Depends(get_session)):
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Seuls les fichiers .docx sont acceptés")

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        count = import_docx(tmp_path, session)
        return {"message": f"{count} pèlerins importés depuis {file.filename}", "count": count}
    finally:
        os.unlink(tmp_path)


@app.get("/api/stats")
def get_stats(session: Session = Depends(get_session)):
    # Compte uniquement les pèlerins visibles (non masqués)
    visible = session.exec(
        select(Pelerin).where(Pelerin.masque == False)  # noqa: E712
    ).all()
    masques_count = len(session.exec(
        select(Pelerin).where(Pelerin.masque == True)  # noqa: E712
    ).all())
    vols = set(p.numero_vol for p in visible if p.numero_vol)
    return {
        "total_pelerins": len(visible),
        "total_pelerins_masques": masques_count,
        "total_vols": len(vols),
        "vols": sorted(vols),
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Serve React frontend
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static-files")

    @app.get("/{full_path:path}")
    async def serve_react(full_path: str):
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
