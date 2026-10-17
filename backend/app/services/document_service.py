import re
from pathlib import Path
from pypdf import PdfReader

def clean(text):
    text = text.replace("\x00", " ").replace("\r", "\n")
    return re.sub(r"[ \t]+", " ", re.sub(r"\n{3,}", "\n\n", text)).strip()

def read_document(path: Path):
    if path.suffix.lower() == ".txt":
        return [(None, clean(path.read_text(encoding="utf-8-sig")))]
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path), strict=False)
        return [(i + 1, clean(page.extract_text() or "")) for i, page in enumerate(reader.pages)]
    raise ValueError("Only PDF and TXT documents are supported")

def infer_category(filename, text):
    match = re.search(r"(?im)^\s*category\s*:\s*([^\n]+)", text)
    if match: return match.group(1).strip().title()
    stem = Path(filename).stem.lower()
    terms = {"Examination": ["exam", "examination"], "Attendance": ["attendance", "absent"], "Fees": ["fee", "fees", "payment"], "Placements": ["placement", "recruit"], "Internship": ["intern"], "Timetable": ["timetable", "schedule"], "Admissions": ["admission", "enrol"], "Events": ["event", "festival"], "Academic": ["academic", "calendar", "course"]}
    return next((category for category, words in terms.items() if any(word in stem for word in words)), "General")

def chunk_text(text, size=900, overlap=120):
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, current = [], ""
    for paragraph in paragraphs:
        while len(paragraph) > size:
            if current: chunks.append(current); current = ""
            split = paragraph.rfind(" ", 0, size)
            split = split if split > size * .6 else size
            chunks.append(paragraph[:split].strip())
            paragraph = paragraph[max(0, split - overlap):].strip()
        if current and len(current) + len(paragraph) + 2 > size:
            chunks.append(current)
            carry = current[-overlap:].strip() if overlap else ""
            current = f"{carry}\n{paragraph}" if carry else paragraph
        else: current = f"{current}\n{paragraph}".strip()
    if current: chunks.append(current)
    return chunks

def extract_chunks(path, settings):
    pages = read_document(path)
    all_text = "\n".join(text for _, text in pages)
    category = infer_category(path.name, all_text)
    result = []
    for page, text in pages:
        for i, chunk in enumerate(chunk_text(text, settings["chunk_size"], settings["chunk_overlap"])):
            result.append({"chunk_id": f"{path.name}:{page or 0}:{i}", "document": path.name, "title": path.stem.replace("_", " ").title(), "category": category, "page": page, "text": chunk})
    return result
