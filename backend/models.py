from sqlmodel import SQLModel, Field


class Pelerin(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    nom: str = Field(index=True)
    prenom: str = ""
    numero_passeport: str = Field(default="", index=True)
    numero_vol: str = ""
    vol_aller_1: str = ""
    vol_aller_2: str = ""
    vol_retour_1: str = ""
    vol_retour_2: str = ""
    statut: str = ""
    source_fichier: str | None = None
    masque: bool = Field(default=False, index=True)
