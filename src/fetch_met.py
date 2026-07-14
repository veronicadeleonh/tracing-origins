"""
Descarga objetos de la API del Metropolitan Museum of Art (Open Access).

API pública, sin key, límite ~80 req/seg (igual pedimos con calma para no
pasarnos). Docs: https://metmuseum.github.io/

Uso:
    python src/fetch_met.py --department 10 --limit 50
    python src/fetch_met.py --department 5 --limit 0   # 0 = todos

Guarda un JSON por objeto en data/raw/<objectID>.json
"""

import argparse
import json
import time
from pathlib import Path

import requests
from tqdm import tqdm

API_BASE = "https://collectionapi.metmuseum.org/public/collection/v1"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

# Departamentos con mayor relevancia para proveniencia colonial/arqueológica.
DEPARTMENTS = {
    3: "Ancient West Asian Art",
    5: "Arts of Africa, Oceania, and the Americas",
    6: "Asian Art",
    10: "Egyptian Art",
    13: "Greek and Roman Art",
    14: "Islamic Art",
}


def get_object_ids(department_id: int) -> list[int]:
    resp = requests.get(f"{API_BASE}/objects", params={"departmentIds": department_id}, timeout=30)
    resp.raise_for_status()
    return resp.json().get("objectIDs") or []


def get_object(object_id: int) -> dict:
    resp = requests.get(f"{API_BASE}/objects/{object_id}", timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_department(department_id: int, limit: int = 0, delay: float = 0.05) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    ids = get_object_ids(department_id)
    if limit:
        ids = ids[:limit]

    dept_name = DEPARTMENTS.get(department_id, str(department_id))
    print(f"Departamento {department_id} ({dept_name}): {len(ids)} objetos a bajar")

    for object_id in tqdm(ids):
        out_path = RAW_DIR / f"{object_id}.json"
        if out_path.exists():
            continue
        try:
            data = get_object(object_id)
        except requests.RequestException as exc:
            print(f"  error en {object_id}: {exc}")
            continue
        out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        time.sleep(delay)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--department", type=int, required=True, help="ID del departamento (ver DEPARTMENTS)")
    parser.add_argument("--limit", type=int, default=0, help="Máximo de objetos a bajar (0 = todos)")
    parser.add_argument("--delay", type=float, default=0.05, help="Segundos entre requests")
    args = parser.parse_args()

    fetch_department(args.department, limit=args.limit, delay=args.delay)
