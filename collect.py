"""
Collecte Velib' Metropole : un releve de toutes les stations, ajoute a data/velib_releves.csv.
Lance toutes les 30 min par GitHub Actions (.github/workflows/collect.yml).
Source : flux GBFS ouvert de Velib' Metropole, sans cle d'API.
"""

import os
from datetime import datetime, timezone

import pandas as pd
import requests

BASE = "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole"
OUT = "data/velib_releves.csv"


def read_feed(name):
    """Lit un flux GBFS et renvoie la liste des stations sous forme de DataFrame."""
    resp = requests.get(f"{BASE}/{name}.json", timeout=30, headers={"User-Agent": "projet-ml-albert"})
    resp.raise_for_status()
    return pd.DataFrame(resp.json()["data"]["stations"])


def split_bike_types(types):
    """Le flux donne [{'mechanical': 3}, {'ebike': 2}] : on le transforme en deux colonnes."""
    out = {"mechanical": None, "ebike": None}
    for item in types if isinstance(types, list) else []:
        out.update({k: v for k, v in item.items() if k in out})
    return pd.Series(out)


def main():
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    # 1. Lecture des deux flux
    info = read_feed("station_information")[["station_id", "stationCode", "name", "lat", "lon", "capacity"]]
    status = read_feed("station_status")

    # 2. Detail mecanique / electrique
    status = pd.concat([status, status["num_bikes_available_types"].apply(split_bike_types)], axis=1)
    status = status[[
        "station_id", "num_bikes_available", "mechanical", "ebike", "num_docks_available",
        "is_installed", "is_renting", "is_returning", "last_reported",
    ]]

    # 3. Fusion sur station_id, horodatage du releve
    df = status.merge(info, on="station_id", how="left")
    df["last_reported"] = pd.to_datetime(df["last_reported"], unit="s", utc=True)
    df.insert(0, "collected_at", now)
    df = df.rename(columns={"stationCode": "station_code"})

    # 4. Ajout au CSV (en-tete seulement a la creation du fichier)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    df.to_csv(OUT, mode="a", header=not os.path.exists(OUT), index=False)

    print(f"{now} : {len(df)} stations ajoutees a {OUT}")


if __name__ == "__main__":
    main()
