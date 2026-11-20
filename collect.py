"""
Collecte Velib' : Velib' collection: downloads the real-time CSV published by the City of Paris (data.gouv.fr)
and appends it to data/velib_releves.csv, with the time of the download.
Run every 30 minutes by GitHub Actions (.github/workflows/collect.yml).
Source: https://www.data.gouv.fr/datasets/stations-velib-disponibilites-en-temps-reel-prs
"""

import io
import os
from datetime import datetime, timezone

import pandas as pd
import requests

URL = "https://www.data.gouv.fr/api/1/datasets/r/b730bbcf-759b-4f5f-849f-a32edcaf5668"
OUT = "data/velib_releves.csv"


def main():
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    # 1. Telechargement du CSV (data.gouv redirige vers le fichier a jour)
    resp = requests.get(URL, timeout=60, headers={"User-Agent": "projet-ml-albert"})
    resp.raise_for_status()

    # 2. Lecture avec pandas : separateur detecte automatiquement (";" ou ","),
    #    utf-8-sig retire un eventuel caractere invisible en debut de fichier
    df = pd.read_csv(io.StringIO(resp.content.decode("utf-8-sig")), sep=None, engine="python")

    # 3. Heure du releve en premiere colonne
    df.insert(0, "collected_at", now)

    # 4. Ajout au CSV (en-tete seulement a la creation du fichier)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    df.to_csv(OUT, mode="a", header=not os.path.exists(OUT), index=False)

    print(f"{now} : {len(df)} stations ajoutees a {OUT}")
    print("Colonnes :", list(df.columns))


if __name__ == "__main__":
    main()
