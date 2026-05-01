from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from contextlib import asynccontextmanager
from models import Pelerin
from database import init_db, get_session
from import_word import import_docx
import tempfile
import os

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
def search_pelerin(passeport: str, session: Session = Depends(get_session)):
    if not passeport or len(passeport.strip()) < 2:
        raise HTTPException(status_code=400, detail="Numéro de passeport trop court")

    # Exclut les pèlerins marqués comme masqués
    query = select(Pelerin).where(
        Pelerin.numero_passeport.ilike(f"%{passeport.strip()}%"),
        Pelerin.masque == False,  # noqa: E712 (SQLAlchemy boolean compare)
    )
    results = session.exec(query).all()

    return {
        "count": len(results),
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
