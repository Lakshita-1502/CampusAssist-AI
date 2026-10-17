# CampusAssist AI

CampusAssist AI is a locally runnable, document-grounded semantic search app for college information. It embeds uploaded or supplied TXT/PDF documents with `sentence-transformers/all-MiniLM-L6-v2`, stores normalized vectors in FAISS, classifies queries by semantic similarity to category examples, and returns extractive passages with source metadata. It is not a general chatbot and never invents answers when retrieval confidence is low.

## Features

- Natural-language semantic retrieval, top five passages, category prediction, and configurable low-confidence cutoff.
- PDF/TXT ingestion, paragraph-aware chunking, page metadata, FAISS index persistence, upload/list/delete/reindex APIs.
- Responsive React dashboard, query interface, document manager, analytics, history, and AI information.
- Evaluation script calculates category accuracy, Recall@1/3/5, mean similarity, and the rate of known-answerable queries withheld at the configured confidence threshold. Detection accuracy is only reported when low-confidence examples are labeled.
- FastAPI input validation and upload limits.

## Architecture

React/Vite calls FastAPI. The API embeds each question once, compares it to persisted document vectors using FAISS inner product on normalized vectors, and returns retrieved passage and source metadata. Category descriptions/examples are embedded once and compared against the query vector. The backend selects a passage sentence extractively and reports its document and page. If its similarity falls below the configurable threshold, the API returns a safe low-confidence response.

See [docs/architecture.md](docs/architecture.md) and [docs/project_notes.md](docs/project_notes.md).

## Clone, install, and run in VS Code (Windows)

Prerequisites: Git, Python 3.10 or newer, and Node.js 18 or newer. Replace the example GitHub URL and folder name below with the URL and name of your repository. This workspace does not currently have a Git remote configured.

### 1. Clone the repository and open it

In PowerShell:

```powershell
git clone https://github.com/Lakshita-1502/CampusAssist-AI.git
cd CampusAssist-AI
code .
```

In VS Code, open **Terminal → New Terminal**. Check that Python and Node are available:

```powershell
python --version
node --version
git --version
```

### 2. Create the Python environment and install dependencies

Run from the project root (the folder containing this README):

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install --upgrade pip
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

If `python` is not recognized but the Python Launcher is installed, use `py -3` in place of `python` for the virtual environment creation command.

### 3. Install frontend dependencies

Still from the project root:

```powershell
cd frontend
npm.cmd install
cd ..
```

`npm.cmd` works in PowerShell even when script execution policy prevents running `npm.ps1`.

### 4. Build the knowledge index

The sample knowledge documents are in `backend\data\knowledge_base\`. Build the local FAISS index:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\build_index.py
```

The first run downloads the public MiniLM embedding model from Hugging Face and may take a little longer. No API key is required. If you add or change source files later, run this command again; uploads and deletions through the website rebuild the index automatically.

### 5. Start the backend and frontend

Open **two VS Code terminals**, both starting from the project root.

In Terminal 1, start the FastAPI backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

In Terminal 2, start the React development server:

```powershell
cd frontend
npm.cmd run dev
```

Open the website at [http://localhost:5173](http://localhost:5173). The backend API is at [http://127.0.0.1:8000](http://127.0.0.1:8000), with interactive API documentation at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 6. Run evaluation and tests (optional)

Run from the project root:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\evaluate.py
```

To run backend tests, open another terminal and run:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests -q
```

## Add documents and build the index

Put `.pdf` or `.txt` files in `backend/data/knowledge_base/`, or upload them in Documents. Then run from project root:

```powershell
backend/.venv/Scripts/python.exe backend/scripts/build_index.py
```

The index is rebuilt automatically after API upload/delete too. Supported document formats are PDF and UTF-8 TXT; scanned image PDFs require OCR and are not supported. Add category hints to a filename, e.g. `attendance_policy.txt`, or use a heading like `Category: Attendance` for categorization.

## Evaluation

```powershell
backend/.venv/Scripts/python.exe backend/scripts/evaluate.py
```

The script evaluates `backend/data/evaluation.json` against the current index and prints metrics computed from those examples. It reports when the dataset/index is missing rather than inventing results. Expand the labeled examples for meaningful academic results.

## API

- `GET /api/health`
- `POST /api/query` with `{"query":"..."}`
- `GET /api/documents`, `POST /api/documents/upload`, `DELETE /api/documents/{id}`, `POST /api/documents/reindex`
- `GET /api/analytics`, `GET /api/history`, `GET /api/categories`

All data stays in the local backend data directory. Query knowledge is limited to indexed documents. Missing, irrelevant, or unindexed information yields a low-confidence response rather than a generated claim. The embedding model, FAISS index, and metadata persist locally. There is no authentication; bind the development server to localhost for personal use.

## Folder structure

```text
backend/app/       FastAPI routes and NLP/retrieval services
backend/data/      Knowledge base, FAISS index, metadata, local history
backend/scripts/   Index builder and evaluation
backend/tests/     API and service tests
frontend/src/      React app, components, API service, styles
docs/              Architecture and project report notes
```

## Future scope and limitations

Multilingual queries, OCR, authentication, grounded LLM synthesis, automatic document refresh, and cloud deployment are future work. Retrieval quality depends on document quality and a representative evaluation set. The displayed confidence is cosine similarity, a relevance signal—not a calibrated probability.
