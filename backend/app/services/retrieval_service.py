import json
import threading
import numpy as np
import faiss
from ..config import INDEX_FILE, CHUNKS_FILE, KB, settings
from .embedding_service import embed
from .document_service import extract_chunks

_lock = threading.RLock()
_index = None
_chunks = []

def rebuild_index():
    global _index, _chunks
    cfg = settings()
    chunks = []
    for path in sorted(KB.iterdir()):
        if path.is_file() and path.suffix.lower() in (".pdf", ".txt"):
            try: chunks.extend(extract_chunks(path, cfg))
            except Exception as exc: print(f"Skipping {path.name}: {exc}")
    index = None
    if chunks:
        vectors = embed([c["text"] for c in chunks])
        index = faiss.IndexFlatIP(vectors.shape[1]); index.add(vectors)
        faiss.write_index(index, str(INDEX_FILE))
    elif INDEX_FILE.exists(): INDEX_FILE.unlink()
    CHUNKS_FILE.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    with _lock: _index, _chunks = index, chunks
    return len(chunks)

def load_index():
    global _index, _chunks
    with _lock:
        if _index is not None: return
        if INDEX_FILE.exists() and CHUNKS_FILE.exists():
            try:
                _index = faiss.read_index(str(INDEX_FILE))
                _chunks = json.loads(CHUNKS_FILE.read_text(encoding="utf-8"))
            except Exception: _index, _chunks = None, []

def search(query, vector=None, top_k=None):
    load_index()
    with _lock:
        index, chunks = _index, list(_chunks)
    if index is None or not chunks: return []
    q = vector if vector is not None else embed([query])
    scores, ids = index.search(np.asarray(q, dtype="float32"), min(top_k or settings()["top_k"], len(chunks)))
    return [{**chunks[int(i)], "similarity": round(float(score), 4)} for score, i in zip(scores[0], ids[0]) if i >= 0]

def documents():
    load_index()
    with _lock: chunks = list(_chunks)
    files = {}
    for chunk in chunks:
        row = files.setdefault(chunk["document"], {"id": chunk["document"], "filename": chunk["document"], "category": chunk["category"], "chunks": 0})
        row["chunks"] += 1
    for path in KB.iterdir():
        if path.is_file() and path.suffix.lower() in (".txt", ".pdf"):
            files.setdefault(path.name, {"id": path.name, "filename": path.name, "category": "Pending index", "chunks": 0})
    return list(files.values())

def answer_from(text):
    re = __import__("re")
    lines = [line.strip() for line in text.splitlines() if line.strip() and not re.match(r"(?i)^category\s*:", line.strip())]
    # The first surviving short line is commonly a section title, not answer text.
    while lines and len(lines[0].split()) < 7 and not re.search(r"[.!?]", lines[0]): lines.pop(0)
    content = [s.strip() for s in re.split(r"(?<=[.!?])\s+", " ".join(lines)) if s.strip()]
    return " ".join(content[:3]) or text
