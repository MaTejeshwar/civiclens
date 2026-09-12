from pathlib import Path

from fastapi import (
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.agent import run_agent
from backend.database import (
    get_investigation,
    list_investigations,
    save_investigation,
)
from backend.rag import (
    get_document_inventory,
    get_index_info,
    rebuild_index,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DOCUMENTS_DIR = (
    BASE_DIR
    / "data"
    / "documents"
)


ALLOWED_EXTENSIONS = {
    ".pdf"
}


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="CivicLens API",
    description=(
        "Agentic municipal policy "
        "impact intelligence"
    ),
    version="1.2.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST MODELS
# ============================================================

class AnalysisRequest(BaseModel):
    question: str


# ============================================================
# HELPERS
# ============================================================

def empty_evidence_graph():
    """Return a consistent empty evidence graph."""

    return {
        "nodes": [],
        "edges": [],
    }


def normalize_tools(result):
    """
    Normalize the agent's tool results into the structure
    expected by the frontend and database.
    """

    raw_tools = (
        result.get("tool_results")
        or result.get("tools")
        or []
    )

    tools = []

    for item in raw_tools:
        if not isinstance(item, dict):
            continue

        tools.append({
            "tool": item.get(
                "tool",
                "unknown_tool"
            ),
            "query": item.get(
                "query",
                ""
            ),
            "result": item.get(
                "result",
                {}
            ),
        })

    return tools


def evidence_node_count(evidence_graph):
    """Return the number of evidence graph nodes."""

    if not isinstance(
        evidence_graph,
        dict
    ):
        return 0

    nodes = evidence_graph.get(
        "nodes",
        []
    )

    return (
        len(nodes)
        if isinstance(nodes, list)
        else 0
    )


def evidence_edge_count(evidence_graph):
    """Return the number of evidence graph edges."""

    if not isinstance(
        evidence_graph,
        dict
    ):
        return 0

    edges = evidence_graph.get(
        "edges",
        []
    )

    return (
        len(edges)
        if isinstance(edges, list)
        else 0
    )


def evidence_count_from_tools(tools):
    """
    Estimate the total evidence passages returned
    across all tools.
    """

    total = 0

    for item in tools:

        result = item.get(
            "result",
            {}
        )

        if not isinstance(
            result,
            dict
        ):
            continue

        count = result.get(
            "evidence_count"
        )

        if isinstance(
            count,
            int
        ):
            total += count

            continue

        results = result.get(
            "results",
            []
        )

        if isinstance(
            results,
            list
        ):
            total += len(results)

    return total


def investigation_summary(item):
    """
    Build a frontend-friendly investigation summary.

    This deliberately supports both the current database
    structure and older saved investigations.
    """

    tools = (
        item.get("tools")
        or item.get("tool_results")
        or []
    )

    graph = (
        item.get("evidence_graph")
        or empty_evidence_graph()
    )

    tool_count = (
        len(tools)
        if isinstance(
            tools,
            list
        )
        else 0
    )

    node_count = evidence_node_count(
        graph
    )

    edge_count = evidence_edge_count(
        graph
    )

    evidence_count = (
        evidence_count_from_tools(
            tools
        )
    )

    return {
        "id": item.get("id"),
        "created_at": item.get(
            "created_at"
        ),
        "request": item.get(
            "request",
            ""
        ),
        "tool_count": tool_count,
        "node_count": node_count,
        "edge_count": edge_count,
        "evidence_count": evidence_count,
    }


# ============================================================
# BASIC ROUTES
# ============================================================

@app.get("/")
def root():
    return {
        "name": "CivicLens",
        "status": "online",
        "message": (
            "Municipal Policy Impact "
            "Intelligence Agent"
        ),
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


# ============================================================
# DOCUMENT LIBRARY
# ============================================================

@app.get("/api/documents")
def documents():
    """
    Return the documents currently indexed
    by CivicLens.
    """

    inventory = get_document_inventory()

    try:
        index_info = get_index_info()
    except Exception:
        index_info = {}

    return {
        "success": True,
        "documents": inventory,
        "count": len(inventory),
        "index": index_info,
    }


@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...)
):
    """
    Upload a PDF and immediately rebuild
    the local TF-IDF RAG index.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail=(
                "A filename is required."
            ),
        )

    # Strip any path components supplied
    # by the client.
    original_name = Path(
        file.filename
    ).name

    extension = Path(
        original_name
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only PDF documents "
                "are supported."
            ),
        )

    DOCUMENTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    target_path = (
        DOCUMENTS_DIR
        / original_name
    )

    try:
        contents = await file.read()

        if not contents:
            raise HTTPException(
                status_code=400,
                detail=(
                    "The uploaded PDF "
                    "is empty."
                ),
            )

        # Basic PDF signature validation.
        if not contents.startswith(
            b"%PDF"
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "The uploaded file "
                    "does not appear to "
                    "be a valid PDF."
                ),
            )

        target_path.write_bytes(
            contents
        )

        # Immediately make the document
        # available to CivicLens retrieval.
        index_stats = rebuild_index()

    except HTTPException:
        raise

    except Exception as exc:

        # If indexing fails, remove the
        # newly uploaded document so the
        # evidence base stays consistent.
        if target_path.exists():
            try:
                target_path.unlink()
            except OSError:
                pass

        raise HTTPException(
            status_code=500,
            detail=(
                "Document upload/indexing "
                "failed: "
                f"{str(exc)}"
            ),
        ) from exc

    return {
        "success": True,
        "message": (
            "Document uploaded and added "
            "to the CivicLens evidence base."
        ),
        "document": {
            "filename": original_name,
            "size_bytes": len(contents),
        },
        "index": index_stats,
    }


# ============================================================
# INVESTIGATION HISTORY
# ============================================================

@app.get("/api/investigations")
def investigations():
    """
    Return recent saved investigations with
    useful summary statistics for the UI.
    """

    items = list_investigations(
        limit=10
    )

    summaries = [
        investigation_summary(item)
        for item in items
    ]

    return {
        "success": True,
        "investigations": summaries,
        "count": len(summaries),
    }


@app.get(
    "/api/investigations/{investigation_id}"
)
def investigation(
    investigation_id: str
):
    """
    Return a complete saved investigation.
    """

    item = get_investigation(
        investigation_id
    )

    if item is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "Investigation not found."
            ),
        )

    # Preserve the complete saved object,
    # while adding normalized summary metadata.
    summary = investigation_summary(
        item
    )

    return {
        "success": True,
        **item,
        **summary,
    }


# ============================================================
# POLICY ANALYSIS
# ============================================================

@app.post("/api/analyze")
def analyze(
    request: AnalysisRequest
):
    """
    Run a complete CivicLens investigation
    and persist the finished result.
    """

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail=(
                "Investigation question "
                "cannot be empty."
            ),
        )

    try:

        # ----------------------------------------------------
        # RUN AGENT
        # ----------------------------------------------------

        result = run_agent(
            question
        )

        # ----------------------------------------------------
        # NORMALIZE TOOL RESULTS
        # ----------------------------------------------------

        tools = normalize_tools(
            result
        )

        # ----------------------------------------------------
        # NORMALIZE EVIDENCE GRAPH
        # ----------------------------------------------------

        evidence_graph = (
            result.get(
                "evidence_graph"
            )
            or empty_evidence_graph()
        )

        # ----------------------------------------------------
        # NORMALIZE REPORT
        # ----------------------------------------------------

        report = result.get(
            "report",
            "",
        )

        # ----------------------------------------------------
        # SAVE INVESTIGATION
        # ----------------------------------------------------

        saved = save_investigation(
            request=question,
            plan=result.get(
                "plan",
                {
                    "steps": []
                }
            ),
            tools=tools,
            evidence_graph=evidence_graph,
            report=report,
        )

        # ----------------------------------------------------
        # SUMMARY METRICS
        # ----------------------------------------------------

        tool_count = len(
            tools
        )

        node_count = evidence_node_count(
            evidence_graph
        )

        edge_count = evidence_edge_count(
            evidence_graph
        )

        evidence_count = (
            evidence_count_from_tools(
                tools
            )
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Analysis failed: "
                f"{str(exc)}"
            ),
        ) from exc

    # --------------------------------------------------------
    # FINAL API RESPONSE
    # --------------------------------------------------------

    return {
        "success": True,

        "investigation_id": saved[
            "id"
        ],

        "request": question,

        "plan": result.get(
            "plan",
            {
                "steps": []
            },
        ),

        # Primary frontend structure.
        "tools": tools,

        # Compatibility alias for the
        # underlying agent structure.
        "tool_results": tools,

        "evidence_graph": (
            evidence_graph
        ),

        "report": report,

        # Useful UI metadata.
        "metrics": {
            "tool_count": tool_count,
            "node_count": node_count,
            "edge_count": edge_count,
            "evidence_count": evidence_count,
        },
    }