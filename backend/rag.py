import json
import re
from pathlib import Path

import numpy as np
import pymupdf
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DOCUMENTS_DIR = BASE_DIR / "data" / "documents"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

METADATA_FILE = PROCESSED_DIR / "metadata.json"
VECTORIZER_FILE = PROCESSED_DIR / "tfidf_vectorizer.json"
MATRIX_FILE = PROCESSED_DIR / "tfidf_matrix.npy"
INDEX_INFO_FILE = PROCESSED_DIR / "index_info.json"


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def normalize_text(text):
    """
    Clean extracted PDF text while preserving meaningful
    paragraph and sentence boundaries.
    """

    if not text:
        return ""

    # Normalize unusual whitespace characters.
    text = text.replace("\xa0", " ")
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove excessive spaces around line breaks.
    text = re.sub(r"[ \t]+", " ", text)

    # Collapse excessive blank lines.
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove spaces immediately before/after line breaks.
    text = re.sub(r" *\n *", "\n", text)

    return text.strip()


# =========================================================
# PDF EXTRACTION
# =========================================================

def extract_pdf_pages(pdf_path):
    """
    Extract text page-by-page while preserving page numbers.

    Each page remains a separate evidence source so that
    CivicLens can provide document + page references.
    """

    pages = []

    document = pymupdf.open(pdf_path)

    try:
        for page_number, page in enumerate(
            document,
            start=1
        ):

            raw_text = page.get_text("text")

            text = normalize_text(raw_text)

            if text:
                pages.append({
                    "page": page_number,
                    "text": text
                })

    finally:
        document.close()

    return pages


# =========================================================
# CHUNKING
# =========================================================

def chunk_text(
    text,
    chunk_size=1200,
    overlap=200
):
    """
    Split text into overlapping chunks.

    The chunker prefers paragraph boundaries where possible,
    while retaining overlap so important context is not lost
    between chunks.
    """

    text = normalize_text(text)

    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:

        end = min(
            start + chunk_size,
            text_length
        )

        # Try to end at a natural paragraph/sentence boundary.
        if end < text_length:

            boundary_candidates = [
                text.rfind("\n\n", start, end),
                text.rfind(". ", start, end),
                text.rfind("; ", start, end),
                text.rfind(" ", start, end)
            ]

            best_boundary = max(
                boundary_candidates
            )

            # Avoid creating extremely small chunks.
            if best_boundary > start + int(
                chunk_size * 0.60
            ):
                end = best_boundary + 1

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        next_start = end - overlap

        if next_start <= start:
            next_start = end

        start = next_start

    return chunks


# =========================================================
# INDEX BUILDING
# =========================================================

def build_index():
    """
    Extract all municipal PDFs and create the local TF-IDF
    evidence retrieval index.
    """

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    DOCUMENTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    all_chunks = []

    pdf_files = sorted(
        DOCUMENTS_DIR.glob("*.pdf")
    )

    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF documents found in {DOCUMENTS_DIR}"
        )

    print(
        f"Found {len(pdf_files)} PDF documents."
    )

    successful_documents = []
    failed_documents = []

    for pdf_path in pdf_files:

        print(
            f"Processing: {pdf_path.name}"
        )

        try:
            pages = extract_pdf_pages(
                pdf_path
            )

            document_chunk_count = 0

            for page_data in pages:

                chunks = chunk_text(
                    page_data["text"]
                )

                for chunk in chunks:

                    all_chunks.append({
                        "document": pdf_path.name,
                        "page": page_data["page"],
                        "text": chunk
                    })

                    document_chunk_count += 1

            if document_chunk_count > 0:
                successful_documents.append({
                    "filename": pdf_path.name,
                    "pages": len(pages),
                    "chunks": document_chunk_count
                })

            else:
                failed_documents.append({
                    "filename": pdf_path.name,
                    "reason": "No extractable text"
                })

        except Exception as exc:

            failed_documents.append({
                "filename": pdf_path.name,
                "reason": str(exc)
            })

            print(
                f"Warning: unable to process "
                f"{pdf_path.name}: {exc}"
            )

    if not all_chunks:
        raise ValueError(
            "No text could be extracted from the PDFs."
        )

    print(
        f"Created {len(all_chunks)} text chunks."
    )

    # =====================================================
    # TF-IDF
    # =====================================================

    texts = [
        item["text"]
        for item in all_chunks
    ]

    print(
        "Building local TF-IDF retrieval index..."
    )

    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        max_features=50000,
        sublinear_tf=True
    )

    matrix = vectorizer.fit_transform(
        texts
    )

    matrix_array = matrix.toarray().astype(
        "float32"
    )

    np.save(
        MATRIX_FILE,
        matrix_array
    )

    # =====================================================
    # METADATA
    # =====================================================

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

    # =====================================================
    # VECTORIZER
    # =====================================================

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

    # =====================================================
    # INDEX INFORMATION
    # =====================================================

    index_info = {
        "documents": len(pdf_files),
        "successful_documents": successful_documents,
        "failed_documents": failed_documents,
        "chunks": len(all_chunks),
        "features": len(vectorizer.vocabulary_)
    }

    with open(
        INDEX_INFO_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            index_info,
            file,
            ensure_ascii=False,
            indent=2
        )

    print()
    print(
        "CivicLens local RAG index created successfully."
    )
    print(
        f"Documents: {len(pdf_files)}"
    )
    print(
        f"Chunks: {len(all_chunks)}"
    )
    print(
        f"Features: {len(vectorizer.vocabulary_)}"
    )

    if failed_documents:
        print(
            f"Documents with extraction issues: "
            f"{len(failed_documents)}"
        )

    return {
        "documents": len(pdf_files),
        "chunks": len(all_chunks),
        "features": len(vectorizer.vocabulary_),
        "failed_documents": len(failed_documents)
    }


# =========================================================
# REBUILD INDEX
# =========================================================

def rebuild_index():
    """
    Public helper used after uploading documents.
    """

    return build_index()


# =========================================================
# DOCUMENT INVENTORY
# =========================================================

def get_document_inventory():
    """
    Return the PDFs currently available to CivicLens.

    The frontend uses this to display the live evidence
    library.
    """

    DOCUMENTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    documents = []

    for pdf_path in sorted(
        DOCUMENTS_DIR.glob("*.pdf")
    ):

        try:
            document = pymupdf.open(
                pdf_path
            )

            page_count = len(document)

            document.close()

        except Exception:
            page_count = None

        documents.append({
            "filename": pdf_path.name,
            "pages": page_count,
            "size_bytes": pdf_path.stat().st_size
        })

    return documents


# =========================================================
# INDEX STATUS
# =========================================================

def get_index_info():
    """
    Return information about the current local RAG index.
    """

    if not INDEX_INFO_FILE.exists():
        return {
            "ready": False,
            "documents": 0,
            "chunks": 0,
            "features": 0
        }

    try:
        with open(
            INDEX_INFO_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            info = json.load(file)

        return {
            "ready": True,
            **info
        }

    except Exception:
        return {
            "ready": False,
            "documents": 0,
            "chunks": 0,
            "features": 0
        }


# =========================================================
# SEARCH
# =========================================================

def search_documents(query, top_k=5):
    """
    Retrieve the most relevant evidence chunks for a query.

    Uses local TF-IDF + cosine similarity.

    No external embedding API is used.
    """

    if not query or not query.strip():
        return []

    if not METADATA_FILE.exists():
        raise FileNotFoundError(
            "RAG metadata index does not exist. "
            "Build the index first."
        )

    if not MATRIX_FILE.exists():
        raise FileNotFoundError(
            "RAG matrix does not exist. "
            "Build the index first."
        )

    if not VECTORIZER_FILE.exists():
        raise FileNotFoundError(
            "RAG vectorizer does not exist. "
            "Build the index first."
        )

    with open(
        METADATA_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        metadata = json.load(file)

    matrix = np.load(
        MATRIX_FILE
    )

    with open(
        VECTORIZER_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        vectorizer_data = json.load(file)

    # Reconstruct the same TF-IDF vectorizer used during
    # index creation.
    vectorizer = TfidfVectorizer(
        vocabulary={
            str(key): int(value)
            for key, value in
            vectorizer_data["vocabulary"].items()
        },
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        sublinear_tf=True
    )

    vectorizer.idf_ = np.array(
        vectorizer_data["idf"],
        dtype="float64"
    )

    # Ensure sklearn has the internal IDF transformer state.
    if hasattr(vectorizer, "_tfidf"):
        vectorizer._tfidf.idf_ = vectorizer.idf_

    normalized_query = normalize_text(
        query
    )

    query_vector = vectorizer.transform(
        [normalized_query]
    )

    scores = cosine_similarity(
        query_vector,
        matrix
    )[0]

    # Retrieve more candidates first so we can remove duplicate
    # document/page combinations before returning the final set.
    candidate_count = min(
        max(top_k * 3, 10),
        len(scores)
    )

    candidate_indices = np.argsort(
        scores
    )[::-1][:candidate_count]

    results = []

    seen_pages = set()

    for index in candidate_indices:

        score = float(
            scores[index]
        )

        if score <= 0:
            continue

        item = metadata[index].copy()

        document = item.get(
            "document",
            "Unknown document"
        )

        page = item.get(
            "page",
            None
        )

        # Avoid flooding the result set with multiple chunks
        # from the exact same document/page.
        page_key = (
            document,
            page
        )

        if page_key in seen_pages:
            continue

        seen_pages.add(
            page_key
        )

        item["score"] = round(
            score,
            4
        )

        results.append(
            item
        )

        if len(results) >= top_k:
            break

    return results


# =========================================================
# COMMAND-LINE INDEX BUILD
# =========================================================

if __name__ == "__main__":
    build_index()