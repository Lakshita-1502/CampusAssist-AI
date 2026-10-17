import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import ensure_dirs
from app.services.retrieval_service import rebuild_index, documents
if __name__ == "__main__":
    ensure_dirs()
    chunks = rebuild_index()
    print(f"Indexed {chunks} chunks from {len(documents())} documents.")
