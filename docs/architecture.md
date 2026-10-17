# CampusAssist AI architecture

## Query path

```text
Student
  ↓
React/Vite interface
  ↓ POST /api/query
FastAPI validation and query handling
  ├─ Sentence Transformer: normalized question embedding
  ├─ Category prototypes: semantic intent similarity
  └─ FAISS IndexFlatIP: top passage similarity search
        ↓
JSON chunk metadata (source, category, page, text)
  ↓ threshold check and extractive answer
Grounded response with source and relevance
  ↓
React result, confidence, and search pathway
```

The embedding model is cached in process and the FAISS index is loaded once and reused. Normalized vectors mean inner product is cosine similarity. The similarity score is a ranking signal, not a calibrated probability. `backend/data/settings.json` controls the threshold and chunk/search settings; `RETRIEVAL_THRESHOLD` can override the threshold.

## Ingestion path

PDF pages are extracted with pypdf and TXT files are read as UTF-8. Whitespace is cleaned, paragraphs are grouped under a maximum chunk size, and long paragraphs are split with overlap. Every chunk records its stable ID, filename/title, inferred category, page where available, and passage text. Sentence Transformer embeddings are normalized and written to a FAISS inner-product index; metadata is kept separately in JSON. The CLI rebuild scans `backend/data/knowledge_base/`; API uploads and removals rebuild the same index.

Pages from PDFs are indexed separately to retain page citations. Text files use a null page. Category hints can be supplied using a `Category: ...` header; otherwise filename terms provide a lightweight hint and unknown documents use General. Query category prediction itself compares embeddings with representative examples for all ten categories.

## Local data and API

Knowledge documents, JSON chunk metadata, FAISS index, settings, evaluation set, and query history live under `backend/data/`. The API is served on port 8000 and Vite on port 5173. CORS allows those local frontend origins. Uploaded files are restricted to PDF/TXT, sanitized, and limited to 10 MB. No user document content is sent to a hosted model API; the public model weights are downloaded on first setup.
