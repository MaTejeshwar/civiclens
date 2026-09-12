"""Simple local persistence layer for CivicLens investigations.

This intentionally uses a JSON file instead of a database.
The hackathon prototype only needs lightweight persistence for
recent investigations and does not need SQLite/Postgres/etc.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4


BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
INVESTIGATIONS_FILE = DATA_DIR / "investigations.json"

_lock = Lock()


def _ensure_storage():
    """Create the local persistence directory/file if needed."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not INVESTIGATIONS_FILE.exists():
        INVESTIGATIONS_FILE.write_text(
            "[]",
            encoding="utf-8"
        )


def _load_all():
    """Load all saved investigations."""

    _ensure_storage()

    try:
        data = json.loads(
            INVESTIGATIONS_FILE.read_text(
                encoding="utf-8"
            )
        )

        if isinstance(data, list):
            return data

    except (json.JSONDecodeError, OSError):
        pass

    return []


def _save_all(investigations):
    """Persist all investigations."""

    _ensure_storage()

    INVESTIGATIONS_FILE.write_text(
        json.dumps(
            investigations,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


def save_investigation(
    request,
    plan,
    tools,
    evidence_graph,
    report
):
    """Save a completed CivicLens investigation."""

    investigation = {
        "id": uuid4().hex[:12],
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "request": request,
        "plan": plan,
        "tools": tools,
        "evidence_graph": evidence_graph,
        "report": report,
    }

    with _lock:
        investigations = _load_all()

        # Newest investigations appear first.
        investigations.insert(
            0,
            investigation
        )

        # Keep storage intentionally small.
        investigations = investigations[:25]

        _save_all(investigations)

    return investigation


def list_investigations(limit=10):
    """Return recent investigations."""

    with _lock:
        investigations = _load_all()

    return investigations[:limit]


def get_investigation(investigation_id):
    """Return one saved investigation by ID."""

    with _lock:
        investigations = _load_all()

    for investigation in investigations:

        if investigation.get("id") == investigation_id:
            return investigation

    return None