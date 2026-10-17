# Project report notes

## Abstract

CampusAssist AI is a local semantic information retrieval system that helps students find relevant information in college documents. It uses sentence embeddings, FAISS vector search, semantic category prediction, confidence-aware retrieval, and source citations. Responses are extractive and limited to indexed documents.

## Introduction and problem statement

College information is distributed across notices, policies, calendars, and guides. Keyword search can miss useful passages when a student's wording differs from the document. Students need a simple way to ask natural-language questions and locate the supporting source.

## Objectives

- Convert questions and document passages to comparable semantic embeddings.
- Retrieve and rank relevant passages from local PDF/TXT documents.
- Predict one of ten likely topic categories using example embeddings.
- Return source-grounded extracts and withhold low-relevance matches.
- Provide document management, usage analytics, evaluation, and a usable student interface.

## Existing and proposed systems

An existing manual workflow requires students to search separate notices or ask offices directly. Basic keyword search is sensitive to wording. The proposed system combines paragraph-aware ingestion, Sentence Transformer embeddings, FAISS cosine similarity, source metadata, a configurable confidence threshold, and a React/FastAPI interface.

## Methodology and NLP techniques

PDF/TXT text is cleaned and split into overlapping paragraph-aware chunks. The `all-MiniLM-L6-v2` Sentence Transformer encodes each chunk and query. L2-normalized embeddings are compared with FAISS inner product. Intent classification compares the question embedding to representative category example embeddings. The top passage is used as an extractive response, and passages below the configured threshold are not presented as answers.

## Architecture

React/Vite sends requests to FastAPI. Backend services handle extraction, embeddings, category classification, FAISS retrieval, confidence logic, and local JSON history. See `docs/architecture.md`.

## Novelty

The project demonstrates paraphrase-aware retrieval, semantic intent detection, source/page citations, and explicit low-confidence behavior in an explainable local application. It does not train a large language model or claim to be one.

## Results and evaluation

Run `python backend/scripts/build_index.py` and `python backend/scripts/evaluate.py`. The evaluation script calculates category accuracy, Recall@1/3/5, mean top similarity, and the rate at which known-answerable queries fall below the configured threshold on `backend/data/evaluation.json`. It reports low-confidence detection accuracy only if the dataset includes labeled low-confidence examples. Report the values produced by the actual current corpus and examples; do not copy unmeasured expected scores. The bundled sample notices are synthetic demonstration content, not official college rules.

## Limitations

Answers are limited to indexed documents. Similarity scores are not calibrated probabilities. Scanned PDFs need OCR, category hints may need correction, and sample evaluation labels are not a substitute for a larger institution-specific test set. Internet access is needed once to download model weights unless they are already cached.

## Future scope

Potential extensions include multilingual queries, voice input, OCR, authenticated student dashboards, automatic document refresh, a grounded LLM synthesis option, and deployment beyond the local machine.

## Conclusion

CampusAssist AI provides a practical demonstration of semantic retrieval for campus information. It prioritizes traceable sources and cautious behavior when the local knowledge base cannot support an answer.
