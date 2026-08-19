"""
src/ es una colección de scripts (fetch_*.py / build_*.py / geocode.py), no un
paquete instalable -- no hay setup.py/pyproject con un pip install -e.
Esto agrega src/ al sys.path para que los tests puedan hacer
`import geocode` / `import museum_id` sin duplicar código ni empaquetar nada
nuevo solo para testear.
"""
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
