import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import DATA
from app.services.embedding_service import embed
from app.services.classification_service import classify
from app.services.retrieval_service import search, load_index

def main():
    dataset = DATA / "evaluation.json"
    rows = json.loads(dataset.read_text(encoding="utf-8"))
    load_index()
    if not search("index readiness"):
        print("No indexed chunks. Run backend/scripts/build_index.py first."); return 2
    category_hits = 0; recalls = {1: 0, 3: 0, 5: 0}; sims = []; top_scores = []; low_total = low_correct = 0; retrieval_total = 0
    from app.config import settings
    threshold = settings()["retrieval_threshold"]
    for row in rows:
        pred = classify(row["query"])
        category_hits += pred["category"] == row["category"]
        results = search(row["query"], top_k=5)
        scores = [r["similarity"] for r in results]
        sims.append(scores[0] if scores else 0)
        top_scores.append(scores[0] if scores else 0)
        if row.get("document"):
            retrieval_total += 1
            for k in recalls: recalls[k] += any(r["document"] == row["document"] for r in results[:k])
        if "expect_low_confidence" in row:
            low_total += 1
            low_correct += bool(scores and scores[0] < threshold) == bool(row["expect_low_confidence"])
    n = len(rows) or 1; retrieval_n = retrieval_total or 1
    print(f"Evaluation examples: {len(rows)}")
    print(f"Category accuracy: {category_hits/n:.1%}")
    for k, hits in recalls.items(): print(f"Recall@{k}: {hits/retrieval_n:.1%} (n={retrieval_total})")
    print(f"Mean top similarity: {sum(sims)/n:.3f}")
    withheld = sum(score < threshold for score in top_scores)
    print(f"Low-confidence rate @ configured threshold ({threshold:.2f}): {withheld}/{n} ({withheld/n:.1%})")
    # All bundled examples have an expected source, so this measures answer coverage
    # on known-answerable queries, not detection accuracy on genuinely unanswerable ones.
    cutoffs = list(dict.fromkeys([0.30, 0.38, 0.45, 0.50, round(threshold, 2)]))
    print("Threshold sensitivity (known-answerable examples withheld):")
    for cutoff in cutoffs:
        count = sum(score < cutoff for score in top_scores)
        print(f"  {cutoff:.2f}: {count}/{n} withheld ({count/n:.1%})")
    if low_total: print(f"Low-confidence detection accuracy: {low_correct/low_total:.1%} (n={low_total})")
    else: print("Low-confidence detection: not measured (no labeled low-confidence cases)")
    return 0

if __name__ == "__main__": sys.exit(main())
