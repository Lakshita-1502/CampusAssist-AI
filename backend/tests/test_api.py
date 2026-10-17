from fastapi.testclient import TestClient
from app.main import app
from app.services.retrieval_service import answer_from

client = TestClient(app)

def test_health():
    assert client.get("/api/health").status_code == 200

def test_categories():
    categories = client.get("/api/categories").json()["categories"]
    assert len(categories) == 10
    assert "Examination" in categories

def test_extractive_answer_omits_category_and_heading():
    passage = "Category: Examination\nExamination Form Submission\n\nStudents must submit the form by 15 October."
    assert answer_from(passage) == "Students must submit the form by 15 October."

def test_query_validation():
    assert client.post("/api/query", json={"query": "  "}).status_code == 422
    assert client.post("/api/query", json={"query": "x" * 1001}).status_code == 422

def test_documents_and_analytics():
    assert "documents" in client.get("/api/documents").json()
    assert "total_queries" in client.get("/api/analytics").json()

def test_retrieval_has_source_or_safe_fallback():
    response = client.post("/api/query", json={"query": "When is the examination registration form due?"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in {"success", "low_confidence"}
    if data["status"] == "success": assert data["source"] and data["answer"]
    else: assert "No sufficiently relevant" in data["answer"]

def test_low_confidence_is_withheld(monkeypatch):
    import app.main as main
    original = main.settings
    monkeypatch.setattr(main, "settings", lambda: {**original(), "retrieval_threshold": 1.1})
    data = client.post("/api/query", json={"query": "When is the examination form due?"}).json()
    assert data["status"] == "low_confidence"
    assert data["source"] is None
    assert "No sufficiently relevant" in data["answer"]

def test_upload_and_remove_document():
    filename = "test_upload_campusassist.txt"
    response = client.post("/api/documents/upload", files={"file": (filename, b"Category: General\nTemporary upload verification text.", "text/plain")})
    assert response.status_code == 200
    assert any(d["filename"] == filename for d in client.get("/api/documents").json()["documents"])
    assert client.delete(f"/api/documents/{filename}").status_code == 200
    assert not any(d["filename"] == filename for d in client.get("/api/documents").json()["documents"])

def test_invalid_pdf_upload_is_rejected():
    response = client.post("/api/documents/upload", files={"file": ("broken.pdf", b"not a PDF", "application/pdf")})
    assert response.status_code == 400

def test_reindex_endpoint():
    response = client.post("/api/documents/reindex")
    assert response.status_code == 200
    assert response.json()["chunks"] >= 1

def test_delete_rejects_parent_directory():
    assert client.delete("/api/documents/..%2Fattendance_policy.txt").status_code in {400, 404}
