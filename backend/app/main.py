from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .config import ensure_dirs, HISTORY, KB, INDEX_FILE, CHUNKS_FILE, settings
from .services.embedding_service import embed
from .services.classification_service import classify
from .services.retrieval_service import rebuild_index, search, documents, answer_from
from .services.document_service import read_document
import json, re, uuid
from pathlib import Path

@asynccontextmanager
async def lifespan(app):
    ensure_dirs()
    if not INDEX_FILE.exists() or not CHUNKS_FILE.exists(): rebuild_index()
    yield

app = FastAPI(title="CampusAssist AI", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_methods=["*"], allow_headers=["*"])

class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)

def read_history():
    try: return json.loads(HISTORY.read_text(encoding="utf-8"))
    except (OSError, ValueError): return []

def write_history(items): HISTORY.write_text(json.dumps(items[:200], indent=2), encoding="utf-8")

@app.get("/api/health")
def health(): return {"status": "ok", "documents": len(documents()), "model": "all-MiniLM-L6-v2"}

@app.post("/api/query")
def query(req: QueryRequest):
    text = req.query.strip()
    if not text: raise HTTPException(422, "Query cannot be blank")
    vector = embed([text])
    category = classify(text, vector)
    results = search(text, vector)
    cfg = settings()
    threshold = cfg["retrieval_threshold"]
    good = [r for r in results if r["similarity"] >= threshold]
    if good:
        best = good[0]
        payload = {"status": "success", "query": text, **category, "answer": answer_from(best["text"]), "confidence": best["similarity"], "source": best["document"], "page": best["page"], "related_results": good[1:], "threshold": threshold}
    else:
        payload = {"status": "low_confidence", "query": text, **category, "answer": "No sufficiently relevant information was found in the available college knowledge base.", "confidence": results[0]["similarity"] if results else 0.0, "source": None, "page": None, "related_results": [], "threshold": threshold}
    history = read_history(); history.insert(0, {"id": str(uuid.uuid4()), "query": text, "category": category["category"], "status": payload["status"], "confidence": payload["confidence"], "source": payload["source"]}); write_history(history)
    return payload

@app.get("/api/categories")
def categories(): return {"categories": list(__import__("app.services.classification_service", fromlist=["CATEGORY_EXAMPLES"]).CATEGORY_EXAMPLES.keys())}

@app.get("/api/documents")
def get_documents(): return {"documents": documents()}

@app.post("/api/documents/upload")
async def upload(file: UploadFile = File(...)):
    name = re.sub(r"[^A-Za-z0-9._-]", "_", file.filename or "")
    if not name or Path(name).suffix.lower() not in {".pdf", ".txt"}: raise HTTPException(400, "Upload a PDF or TXT file")
    content = await file.read()
    if not content: raise HTTPException(400, "File is empty")
    max_bytes = settings()["max_upload_mb"] * 1024 * 1024
    if len(content) > max_bytes: raise HTTPException(413, f"File exceeds the {settings()['max_upload_mb']} MB upload limit")
    path = KB / name
    previous = path.read_bytes() if path.exists() else None
    try:
        path.write_bytes(content)
        pages = read_document(path)
        if not any(text.strip() for _, text in pages): raise ValueError("No extractable text was found in this document")
        count = rebuild_index()
    except Exception as exc:
        if previous is None:
            if path.exists(): path.unlink()
        else: path.write_bytes(previous)
        rebuild_index()
        raise HTTPException(400, f"Could not process this document: {exc}")
    return {"message": "Document uploaded and indexed", "filename": name, "chunks": count}

@app.delete("/api/documents/{document_id}")
def delete_document(document_id: str):
    safe_name = Path(document_id).name
    if safe_name != document_id or safe_name in {".", ".."} or Path(safe_name).suffix.lower() not in {".pdf", ".txt"}: raise HTTPException(400, "Invalid document id")
    path = KB / safe_name
    if not path.exists(): raise HTTPException(404, "Document not found")
    path.unlink(); count = rebuild_index()
    return {"message": "Document removed", "chunks": count}

@app.post("/api/documents/reindex")
def reindex(): return {"chunks": rebuild_index(), "documents": len(documents())}

@app.get("/api/analytics")
def analytics():
    history = read_history(); counts = {}
    for item in history: counts[item["category"]] = counts.get(item["category"], 0) + 1
    answered = [item["confidence"] for item in history if item["status"] == "success"]
    return {"total_queries": len(history), "successful_queries": len(answered), "low_confidence": sum(i["status"] == "low_confidence" for i in history), "average_confidence": round(sum(answered) / len(answered), 3) if answered else 0, "by_category": [{"category": k, "count": v} for k, v in counts.items()]}

@app.get("/api/history")
def history(): return {"history": read_history()}

