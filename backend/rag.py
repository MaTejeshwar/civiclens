import json
from pathlib import Path

import numpy as np
import pymupdf
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


BASE_DIR = Path(__file__).resolve().parent.parent

DOCUMENTS_DIR = BASE_DIR / "data" / "documents"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

METADATA_FILE = PROCESSED_DIR / "metadata.json"
VECTORIZER_FILE = PROCESSED_DIR / "tfidf_vectorizer.json"
MATRIX_FILE = PROCESSED_DIR / "tfidf_matrix.npy"


def extract_pdf_pages(pdf_path):
    """Extract text page-by-page while preserving page numbers."""

    pages = []

    document = pymupdf.open(pdf_path)

    for page_number, page in enumerate(document, start=1):

        text = page.get_text("text").strip()

        if text:
            pages.append({
                "page": page_number,
                "text": text
            })

    document.close()

    return pages


def chunk_text(text, chunk_size=1200, overlap=200):
    """Split text into overlapping chunks."""

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


def build_index():
    """Extract documents and create a local TF-IDF retrieval index."""

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    all_chunks = []

    pdf_files = sorted(DOCUMENTS_DIR.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF documents found in {DOCUMENTS_DIR}"
        )

    print(f"Found {len(pdf_files)} PDF documents.")

    for pdf_path in pdf_files:

        print(f"Processing: {pdf_path.name}")

        pages = extract_pdf_pages(pdf_path)

        for page_data in pages:

            chunks = chunk_text(page_data["text"])

            for chunk in chunks:

                all_chunks.append({
                    "document": pdf_path.name,
                    "page": page_data["page"],
                    "text": chunk
                })

    if not all_chunks:
        raise ValueError("No text could be extracted from the PDFs.")

    print(f"Created {len(all_chunks)} text chunks.")

    texts = [
        item["text"]
        for item in all_chunks
    ]

    print("Building local TF-IDF retrieval index...")

    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        max_features=50000
    )

    matrix = vectorizer.fit_transform(texts)

    # Save sparse matrix as dense float32 for our small hackathon dataset.
    matrix_array = matrix.toarray().astype("float32")

    np.save(
        MATRIX_FILE,
        matrix_array
    )

    with open(
        METADATA_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            all_chunks,
            file,
            ensure_ascii=False,
            indent=2
        )

    # Save vocabulary + IDF so the index can be recreated without
    # processing the PDFs again.
    vectorizer_data = {
        "vocabulary": {
            str(key): int(value)
            for key, value in vectorizer.vocabulary_.items()
        },
        "idf": [
            float(value)
            for value in vectorizer.idf_
        ]
    }

    with open(
        VECTORIZER_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            vectorizer_data,
            file
        )

    print()
    print("CivicLens local RAG index created successfully.")
    print(f"Documents: {len(pdf_files)}")
    print(f"Chunks: {len(all_chunks)}")
    print(f"Matrix: {MATRIX_FILE}")
    print(f"Metadata: {METADATA_FILE}")


def search_documents(query, top_k=5):
    """Retrieve the most relevant evidence chunks for a query."""

    with open(
        METADATA_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        metadata = json.load(file)

    matrix = np.load(MATRIX_FILE)

    with open(
        VECTORIZER_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        vectorizer_data = json.load(file)

    vectorizer = TfidfVectorizer(
        vocabulary=vectorizer_data["vocabulary"],
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2)
    )

    vectorizer.idf_ = np.array(
        vectorizer_data["idf"],
        dtype="float64"
    )

    query_vector = vectorizer.transform([query])

    scores = cosine_similarity(
        query_vector,
        matrix
    )[0]

    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []

    for index in top_indices:

        if scores[index] <= 0:
            continue

        item = metadata[index].copy()

        item["score"] = round(
            float(scores[index]),
            4
        )

        results.append(item)

    return results


if __name__ == "__main__":
    build_index()