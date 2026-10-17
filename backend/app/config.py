from pathlib import Path
import json
import os

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
KB = DATA / "knowledge_base"
INDEX_DIR = DATA / "index"
METADATA_DIR = DATA / "metadata"
HISTORY = DATA / "query_history.json"
INDEX_FILE = INDEX_DIR / "campusassist.faiss"
CHUNKS_FILE = METADATA_DIR / "chunks.json"
SETTINGS_FILE = DATA / "settings.json"
DEFAULTS = {"retrieval_threshold": 0.38, "top_k": 5, "chunk_size": 900, "chunk_overlap": 120, "max_upload_mb": 10}

def settings():
    values = DEFAULTS.copy()
    if SETTINGS_FILE.exists():
        try: values.update(json.loads(SETTINGS_FILE.read_text(encoding="utf-8")))
        except (OSError, ValueError): pass
    values["retrieval_threshold"] = float(os.getenv("RETRIEVAL_THRESHOLD", values["retrieval_threshold"]))
    return values

def ensure_dirs():
    for path in (KB, INDEX_DIR, METADATA_DIR): path.mkdir(parents=True, exist_ok=True)
