"""
Descarga objetos de la API del Metropolitan Museum of Art (Open Access).

API pública, sin key, límite ~80 req/seg (igual pedimos con calma para no
pasarnos). Docs: https://metmuseum.github.io/

Uso:
    python src/fetch_met.py --department 10 --limit 50
    python src/fetch_met.py --department 5 --limit 0   # 0 = todos

Todo se guarda mergeado en un único archivo: data/raw/met_objects_raw.json
(lista de objetos, sin duplicados por objectID). Si el objeto ya está en el
archivo no se vuelve a pedir, así que correr el script de nuevo solo baja lo
que falta.
"""

import argparse
import json
import time
from pathlib import Path

import requests
from tqdm import tqdm

API_BASE = "https://collectionapi.metmuseum.org/public/collection/v1"
RAW_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "met_objects_raw.json"
CHECKPOINT_EVERY = 250  # guarda a disco cada N objetos nuevos, por si se corta a mitad de camino

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


def load_existing() -> dict[int, dict]:
    if not RAW_PATH.exists():
        return {}
    data = json.loads(RAW_PATH.read_text())
    return {obj["objectID"]: obj for obj in data}


def save(objects_by_id: dict[int, dict]) -> None:
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    ordered = [objects_by_id[k] for k in sorted(objects_by_id)]
    RAW_PATH.write_text(json.dumps(ordered, ensure_ascii=False, indent=2))


def fetch_department(department_id: int, limit: int = 0, delay: float = 0.05) -> None:
    ids = get_object_ids(department_id)
    if limit:
        ids = ids[:limit]

    dept_name = DEPARTMENTS.get(department_id, str(department_id))
    objects_by_id = load_existing()
    pending = [i for i in ids if i not in objects_by_id]
    print(f"Departamento {department_id} ({dept_name}): {len(ids)} objetos, {len(pending)} nuevos a bajar")

    new_since_checkpoint = 0
    for object_id in tqdm(pending):
        try:
            data = get_object(object_id)
        except requests.RequestException as exc:
            print(f"  error en {object_id}: {exc}")
            continue
        objects_by_id[object_id] = data
        new_since_checkpoint += 1
        if new_since_checkpoint >= CHECKPOINT_EVERY:
            save(objects_by_id)
            new_since_checkpoint = 0
        time.sleep(delay)

    save(objects_by_id)
    print(f"Guardado en {RAW_PATH} ({len(objects_by_id)} objetos totales)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--department", type=int, required=True, help="ID del departamento (ver DEPARTMENTS)")
    parser.add_argument("--limit", type=int, default=0, help="Máximo de objetos a bajar (0 = todos)")
    parser.add_argument("--delay", type=float, default=0.05, help="Segundos entre requests")
    args = parser.parse_args()

    fetch_department(args.department, limit=args.limit, delay=args.delay)
